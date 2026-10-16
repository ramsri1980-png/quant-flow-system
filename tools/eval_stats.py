"""Evaluation statistics (pure stdlib): day-clustered bootstrap difference + Holm correction.
Alerts on the same day are NOT independent: resample whole DAYS, never single alerts.
Usage: from eval_stats import day_cluster_bootstrap_diff, holm"""
import random
from collections import defaultdict

def _by_day(rows):
    d = defaultdict(list)
    for day, v in rows: d[day].append(v)
    return d

def _resample_mean(days, rng):
    keys = list(days); tot = n = 0.0
    for _ in keys:
        vals = days[keys[rng.randrange(len(keys))]]
        tot += sum(vals); n += len(vals)
    return tot / n if n else float("nan")

def day_cluster_bootstrap_diff(a, b, B=5000, seed=7, alpha=0.05):
    """a, b: lists of (day, value). Returns mean(a)-mean(b) with day-clustered bootstrap CI and two-sided p."""
    da, db = _by_day(a), _by_day(b)
    if not da or not db: raise ValueError("empty group")
    mean = lambda rows: sum(v for _, v in rows) / len(rows)
    diff = mean(a) - mean(b); rng = random.Random(seed); sims = []
    for _ in range(B): sims.append(_resample_mean(da, rng) - _resample_mean(db, rng))
    sims.sort(); lo = sims[int(B * alpha / 2)]; hi = sims[int(B * (1 - alpha / 2)) - 1]
    # centred bootstrap p-value (null: diff = 0)
    centred = [s - diff for s in sims]
    p = (sum(1 for c in centred if abs(c) >= abs(diff)) + 1) / (B + 1)
    return dict(diff=diff, lo=lo, hi=hi, p=p, n_a=len(a), n_b=len(b), days_a=len(da), days_b=len(db))

def holm(pvals, alpha=0.05):
    """Holm-Bonferroni. pvals: dict name->p. Returns dict name->(adjusted_p, reject)."""
    items = sorted(pvals.items(), key=lambda kv: kv[1]); m = len(items); out = {}; run = 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p)); out[k] = (run, run < alpha)
    return out

def _selftest():
    rng = random.Random(1)
    def make(mu, days=80, per=4):
        return [(d, rng.gauss(mu, 1.0) + rng.gauss(0, 0.5) * 0) for d in range(days) for _ in range(per)]
    real = day_cluster_bootstrap_diff(make(0.5), make(0.0))
    null = day_cluster_bootstrap_diff(make(0.0), make(0.0))
    assert real["lo"] > 0 and real["p"] < 0.01, real
    assert null["lo"] < 0 < null["hi"], null
    h = holm({"H1": 0.001, "H2": 0.04, "H3": 0.03})
    assert h["H1"][1] and not h["H2"][1], h
    print("eval_stats self-test ok", {k: round(v, 3) if isinstance(v, float) else v for k, v in real.items()})

if __name__ == "__main__": _selftest()
