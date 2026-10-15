"""Reference oracle for QuantFlow dealer kernels (formulas F1-F7 in openspec/formulas-dealer-greeks.md).
Pure stdlib, pure functions. Constants marked [P] are PROPOSED and must be named in ARCH V1 §AI.3.
Run: python dealer_reference.py (self-test)."""
from dataclasses import dataclass
from greeks_reference import gamma, vanna, charm, d1d2

CFG = dict(
    T_MIN=300 / (365 * 86400),     # DEALER_T_MIN_S = 300
    SIGMA_MIN=0.01, SIGMA_MAX=5.0, # GREEKS_SIGMA_MIN / MAX
    COVERAGE_MIN=0.80,             # DEALER_COVERAGE_MIN
    R_MIN_FALLBACK=0.10, R_FULL_FALLBACK=0.50,   # used only without percentile history (label "fallback")
    GRID_HALF_MULT=3, GRID_POINTS=41,            # half-width = 3 * m_daily; 41 points
    THETA=0.5, EPS=0.10,           # LEVEL_THETA / LEVEL_EPS
    MULT=100,
)

@dataclass(frozen=True)
class Opt:
    K: float; call: bool; oi: float; iv: float | None; T: float; r: float = 0.0; q: float = 0.0

def dealer_sign(o: Opt, model="OI_NAIVE", negate=False) -> int:
    s = (1 if o.call else -1) if model == "OI_NAIVE" else 0   # SIGNED_FLOW/PROVIDER inject s externally
    return -s if negate else s

def exposures(o: Opt, S: float, cfg=CFG):
    """Unsigned dollar exposures or None if option excluded (fail closed)."""
    if o.iv is None or o.iv <= cfg["SIGMA_MIN"] or o.iv > cfg["SIGMA_MAX"] or o.T <= 0 or o.oi <= 0:
        return None
    T = max(o.T, cfg["T_MIN"])
    g = gamma(S, o.K, o.r, o.q, o.iv, T); v = vanna(S, o.K, o.r, o.q, o.iv, T)
    c = charm(S, o.K, o.r, o.q, o.iv, T, o.call)
    m = cfg["MULT"] * o.oi
    return dict(gamma=g * S * S * 0.01 * m, vanna=v * 0.01 * S * m, charm=c / 365.0 * S * m)

def aggregate(chain, S, negate=False, cfg=CFG):
    net = dict(gamma=0.0, vanna=0.0, charm=0.0); gross = 0.0; ok = tot = 0.0
    for o in chain:
        tot += o.oi; e = exposures(o, S, cfg)
        if e is None: continue
        ok += o.oi; s = dealer_sign(o, negate=negate)
        for k in net: net[k] += s * e[k]
        gross += abs(e["gamma"])
    return net, gross, (ok / tot if tot else 0.0)

def regime(chain, S, cfg=CFG, r_min=None):
    """r_min: percentile-derived threshold (DEALER_R_PCTL_MIN of trailing R); None -> fallback (label it)."""
    r_min = cfg["R_MIN_FALLBACK"] if r_min is None else r_min
    net, gross, cov = aggregate(chain, S, False, cfg)
    R = abs(net["gamma"]) / gross if gross else 0.0
    if cov < cfg["COVERAGE_MIN"]: name = "UNAVAILABLE"
    elif R < r_min: name = "UNINFORMATIVE"
    else: name = "POSITIVE" if net["gamma"] > 0 else "NEGATIVE"
    return dict(regime=name, R=R, coverage=cov, net=net, r_min_used=r_min)

def regime_models(a: dict, b: dict) -> dict:
    """F3: a,b = regime() outputs under two dealer-sign models (e.g. OI_NAIVE vs SIGNED_FLOW)."""
    if (a["net"]["gamma"] > 0) != (b["net"]["gamma"] > 0):
        return dict(a, regime="UNINFORMATIVE", sign_fragile=True)
    return dict(a, sign_fragile=False)

def flip(chain, S, m_daily, cfg=CFG):
    """Zero crossing of NetGamma$(S') nearest spot; None = NO_FLIP. m_daily = IV/sqrt(252) (ARCH V4 D.15)."""
    half = (cfg["GRID_POINTS"] - 1) // 2; h = cfg["GRID_HALF_MULT"] * m_daily / half; pts = []
    for j in range(-half, half + 1):
        Sp = S * (1 + j * h)
        pts.append((Sp, aggregate(chain, Sp, False, cfg)[0]["gamma"]))
    best = None
    for (s0, g0), (s1, g1) in zip(pts, pts[1:]):
        if g0 == 0 or g0 * g1 < 0:
            x = s0 if g0 == 0 else s0 + (s1 - s0) * (0 - g0) / (g1 - g0)
            if best is None or abs(x - S) < abs(best - S): best = x
    return None if best is None else dict(S_flip=best, distance_pct=(best - S) / S)

def levels(chain, S, b, cfg=CFG):
    by = {}
    for o in chain:
        e = exposures(o, S, cfg)
        if e: by[o.K] = by.get(o.K, 0.0) + dealer_sign(o) * e["gamma"]
    ks = sorted(by); peak = max((abs(v) for v in by.values()), default=0.0); out = []
    for i, k in enumerate(ks):
        v = by[k]; l = by[ks[i - 1]] if i else v; r = by[ks[i + 1]] if i < len(ks) - 1 else v
        if v >= cfg["THETA"] * peak and v >= l and v >= r:
            role = "PIN" if abs(k - S) <= b else ("POSITIVE_GAMMA_SUPPORT" if k < S else "POSITIVE_GAMMA_RESISTANCE")
            out.append((k, role))
        elif v <= -cfg["THETA"] * peak and v <= l and v <= r:
            out.append((k, "NEGATIVE_GAMMA_ACCELERATOR"))
        elif abs(v) < cfg["EPS"] * peak:
            out.append((k, "LOW_EXPOSURE_AIR_POCKET"))
    return out

def hedge_pressure(net, dS_pct, dIV_pts, dt_days, zero_dte, adv_usd=None):
    """H>0 = dealers BUY underlying. dS_pct in percent points. Charm excluded for 0DTE. None if ADV missing."""
    d = net["gamma"] * dS_pct + net["vanna"] * dIV_pts + (0.0 if zero_dte else net["charm"] * dt_days)
    H = -d
    return dict(H=H, H_signed=None if not adv_usd else H / adv_usd)

def gamma_align(direction, reg, lv, S, target, fresh=True):
    """direction +1 bullish / -1 bearish. Returns 0, 0.5 or 1 (F7)."""
    if not fresh or reg["regime"] not in ("POSITIVE", "NEGATIVE"): return 0.0
    lo, hi = sorted((S, target))
    walls = [k for k, r in lv if r in ("POSITIVE_GAMMA_RESISTANCE", "POSITIVE_GAMMA_SUPPORT", "PIN") and lo < k < hi]
    if reg["regime"] == "NEGATIVE": return 0.0 if walls else 1.0
    if walls: return 0.0
    pins = [k for k, r in lv if r in ("PIN", "POSITIVE_GAMMA_RESISTANCE", "POSITIVE_GAMMA_SUPPORT") and (k - S) * direction > 0]
    near = min(pins, key=lambda k: abs(k - S)) if pins else None
    return 0.5 if near is not None and abs(near - target) < 1e-9 else 0.0

def vanna_align(direction, net_vanna, dIV_pts, adv_usd, theta_v):
    if dIV_pts is None or not adv_usd or theta_v is None: return 0.0
    H_V = -net_vanna * dIV_pts
    return 1.0 if (H_V > 0) == (direction > 0) and abs(H_V) / adv_usd >= theta_v else 0.0

def D_c(g, v): return (g + v) / 2.0

def _selftest():
    S, T = 100.0, 1 / 365
    chain = [Opt(K, True, 1000 * (1 + (K == 100)), 0.2, T) for K in (95, 100, 105)] + \
            [Opt(K, False, 1500 * (1 + (K == 95)), 0.2, T) for K in (90, 95, 100)]
    reg = regime(chain, S); assert reg["regime"] in ("POSITIVE", "NEGATIVE", "UNINFORMATIVE"), reg
    net, gross, cov = aggregate(chain, S); neg, _, _ = aggregate(chain, S, True)
    assert abs(net["gamma"] + neg["gamma"]) < 1e-6 * gross and cov == 1.0
    h = hedge_pressure(dict(gamma=1e6, vanna=0, charm=0), 1.0, 0, 0, True)   # long gamma, +1% -> dealers sell
    assert h["H"] < 0
    assert exposures(Opt(100, True, 10, None, T), S) is None                  # missing IV excluded
    assert regime([Opt(100, True, 10, None, T)], S)["regime"] == "UNAVAILABLE"
    f = flip(chain, S, 0.2 / 252 ** 0.5); print("regime", reg["regime"], "R=%.2f" % reg["R"], "flip", f)
    print("levels", levels(chain, S, 0.15 * 1.0))
    print("dealer_reference self-test ok")

if __name__ == "__main__":
    _selftest()
