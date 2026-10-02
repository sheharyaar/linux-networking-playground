# Chapter 1 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

All three come from `labs/common/qnet.sh` with its defaults (bottleneck netem rate 10mbit limit 50,
20 ms delay each way, offloads off) and `flow.py send --cc reno`.

- `reno-sawtooth.csv`: 30 s Reno transfer, TCP_INFO every 10 ms (flow.py columns).
- `reno-bottleneck-queue.csv`: the same run, `qwatch.py --dev r1 --every 0.02` in the rtr namespace.
- `reno-blackhole-backoff.csv`: 18 s Reno transfer; the bottleneck switched to `loss 100%` from 5.0 s to 13.0 s.

They are the table view for the chapter's plots, and the reference output for the labs.
