# FAA attribution quantile forecaster

A forecaster for the make.fun competition polymarket-faa-attribution-02.
It reads one case file per run: several markets, each with minute-by-minute
Yes prices up to a checkpoint. For every market and every one of the 240
minutes after the checkpoint it writes five quantiles of where that
minute's price will fall: the low tail, the low quarter, the middle, the
high quarter and the high tail.

How it works, in plain language: the middle forecast stays at the
market's last price, because these prices move in steps and mostly sit
still. The spread around it comes from each market's own recent
minute-to-minute moves, measured from the history inside the case
itself, so a jumpy market gets a wider forecast than a quiet one. The
spread widens as the forecast minute gets further from the checkpoint,
and the tails are heavier than a bell curve would give, because these
prices jump now and then. Every number stays between zero and one, the
five stay in order, and two runs on the same case write byte-for-byte
identical output. Only the Python standard library is used: no network,
no wall clock, no randomness.
