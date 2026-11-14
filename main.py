"""Quantile forecaster for polymarket-faa-attribution-02.

Reads every case file (*.in) in the input directory, in name order, and
writes one forecast file (*.out) per case to the output directory. Each
forecast gives, for every market and every one of the 240 minutes after
the checkpoint, five quantiles of that minute's price.

Method: the median stays at the market's last price. The spread around
it comes from the market's own recent minute-to-minute moves, widens
with the horizon as a power law, and carries heavier tails than a bell
curve. Standard library only; deterministic; no network, no clock.
"""

import json
import math
import os

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
# Standard normal quantiles at the five levels.
Z = (-1.6448536269514722, -0.6744897501960817, 0.0,
     0.6744897501960817, 1.6448536269514722)

# Tuned constants. The local scorer sweeps overrides of these; the values
# here are the ones that scored best on the six practice cases.
PARAMS = {
    "lookback": 360,     # minutes of recent moves the spread is measured on
    "estimator": "mad",  # "rms" or "mad": how moves become a per-minute scale
    "scale": 1.0,        # multiplier on the measured per-minute scale
    "floor": 0.0005,     # smallest per-minute scale, for markets that sat still
    "alpha": 0.35,       # horizon widening: spread grows like h ** alpha
    "mid_mult": 1.2,     # extra width on the 0.25 / 0.75 quantiles
    "tail_mult": 1.75,   # extra width on the 0.05 / 0.95 quantiles
}


def _measure(prices, lookback, estimator):
    """Per-minute move scale from the recent history of one market."""
    diffs = []
    start = max(1, len(prices) - lookback)
    for i in range(start, len(prices)):
        diffs.append(prices[i] - prices[i - 1])
    if not diffs:
        return 0.0
    if estimator == "mad":
        mean_abs = sum(abs(d) for d in diffs) / len(diffs)
        return mean_abs * 1.2533141373155001
    total = 0.0
    for d in diffs:
        total += d * d
    return math.sqrt(total / len(diffs))


def market_rows(prices, horizon, params):
    """The 240 forecast rows for one market, each five quantiles."""
    x = prices[-1]
    sigma = params["scale"] * _measure(prices, params["lookback"],
                                       params["estimator"])
    if sigma < params["floor"]:
        sigma = params["floor"]
    alpha = params["alpha"]
    mults = (params["tail_mult"], params["mid_mult"], 1.0,
             params["mid_mult"], params["tail_mult"])
    rows = []
    for h in range(1, horizon + 1):
        width = sigma * (h ** alpha)
        row = []
        for k in range(5):
            q = x + Z[k] * mults[k] * width
            if q < 0.0:
                q = 0.0
            elif q > 1.0:
                q = 1.0
            row.append(round(q, 6) + 0.0)
        rows.append(row)
    return rows


def forecast_case(case, params=None):
    """Build the forecast document for one parsed case object."""
    if params is None:
        params = PARAMS
    horizon = int(case["horizon_minutes"])
    forecasts = []
    for market in case["markets"]:
        forecasts.append({
            "id": market["id"],
            "q": market_rows(market["prices"], horizon, params),
        })
    return {"forecasts": forecasts}


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(in_dir) if n.endswith(".in"))
    for name in names:
        with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        doc = forecast_case(case)
        out_name = name[:-3] + ".out"
        with open(os.path.join(out_dir, out_name), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"))


if __name__ == "__main__":
    main()
