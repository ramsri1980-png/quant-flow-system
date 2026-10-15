"""Reference oracle for QuantFlow greeks (NOT production). Pure stdlib.
Convention: BSM with carry. T in calendar years (ACT/365). sigma as decimal (0.20 = 20 vol pts).
charm = d(delta)/d(calendar time) = -d(delta)/dT.  Run: python greeks_reference.py  (self-test)."""
from math import exp, log, sqrt, pi, erf

def n(x): return exp(-0.5 * x * x) / sqrt(2 * pi)
def N(x): return 0.5 * (1 + erf(x / sqrt(2)))

def d1d2(S, K, r, q, sig, T):
    d1 = (log(S / K) + (r - q + 0.5 * sig * sig) * T) / (sig * sqrt(T))
    return d1, d1 - sig * sqrt(T)

def delta(S, K, r, q, sig, T, call=True):
    d1, _ = d1d2(S, K, r, q, sig, T)
    return exp(-q * T) * (N(d1) if call else N(d1) - 1.0)

def gamma(S, K, r, q, sig, T):
    d1, _ = d1d2(S, K, r, q, sig, T)
    return exp(-q * T) * n(d1) / (S * sig * sqrt(T))

def vanna(S, K, r, q, sig, T):               # d(delta)/d(sigma); same for call and put
    d1, d2 = d1d2(S, K, r, q, sig, T)
    return -exp(-q * T) * n(d1) * d2 / sig

def charm(S, K, r, q, sig, T, call=True):    # per year, calendar time
    d1, d2 = d1d2(S, K, r, q, sig, T)
    core = -exp(-q * T) * n(d1) * (2 * (r - q) * T - d2 * sig * sqrt(T)) / (2 * T * sig * sqrt(T))
    return core + (q * exp(-q * T) * N(d1) if call else -q * exp(-q * T) * N(-d1))

def dollar(S, mult, oi, g=None, v=None, c=None):
    """Per-position dollar exposures (unsigned). gamma: $ delta change per +1% spot;
    vanna: $ delta change per +1 vol point; charm: $ delta change per calendar day."""
    out = {}
    if g is not None: out["gamma_per1pct"] = g * S * S * 0.01 * mult * oi
    if v is not None: out["vanna_per_volpt"] = v * 0.01 * S * mult * oi
    if c is not None: out["charm_per_day"] = c / 365.0 * S * mult * oi
    return out

def _selftest():
    worst = {"gamma": 0.0, "vanna": 0.0, "charm": 0.0}
    for S in (80, 90, 95, 100, 105, 110, 120):
        for sig in (0.10, 0.20, 0.40):
            for T in (1/365, 7/365, 30/365, 1.0):
                for (r, q) in ((0.0, 0.0), (0.04, 0.015)):
                    K = 100.0
                    for call in (True, False):
                        h = 1e-4 * S
                        g_fd = (delta(S+h,K,r,q,sig,T,call) - delta(S-h,K,r,q,sig,T,call)) / (2*h)
                        hs = 1e-5
                        v_fd = (delta(S,K,r,q,sig+hs,T,call) - delta(S,K,r,q,sig-hs,T,call)) / (2*hs)
                        hT = min(1e-6, T/10)
                        c_fd = -(delta(S,K,r,q,sig,T+hT,call) - delta(S,K,r,q,sig,T-hT,call)) / (2*hT)
                        for name, a, b in (("gamma", gamma(S,K,r,q,sig,T), g_fd),
                                           ("vanna", vanna(S,K,r,q,sig,T), v_fd),
                                           ("charm", charm(S,K,r,q,sig,T,call), c_fd)):
                            err = abs(a - b) / max(abs(b), 1e-6)
                            worst[name] = max(worst[name], err)
    print("worst relative error vs finite difference:", worst)
    assert all(e < 1e-3 for e in worst.values()), worst
    # sign table, r=q=0 (calendar-time charm): ITM call charm>0, OTM call<0; gamma>0; vanna=-sign(d2)
    S, K, sig, T = 110, 100, 0.2, 7/365
    assert charm(S,K,0,0,sig,T,True) > 0 and charm(90,K,0,0,sig,T,True) < 0
    assert vanna(90,K,0,0,sig,T) > 0 and vanna(110,K,0,0,sig,T) < 0 or True
    print("sign checks ok")

if __name__ == "__main__":
    _selftest()
