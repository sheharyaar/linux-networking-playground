# Chapter 10 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1, iproute2 7.2.0)

Bench runs come from `../bench.sh` through `labs/common/qnet.sh`: qnet's bottleneck kept as built
(`rtr:r1` netem rate 10mbit limit 50), fq on the sender's `s0`, and the whole 40 ms on the ack path
(`rcv:c0` netem delay 40ms). One ping first resolves ARP, so the handshake RTT is the path's.

- `cubic-f.csv`: 25 s CUBIC flow, `bbrflow.py` columns, TCP_INFO every 5 ms (the BBR columns are
  empty: CUBIC has no `get_info`). `inflight` is unacked - sacked - lost + retrans.
- `cubic-q.csv`: the same run, `qwatch.py --dev r1 --every 0.02` in rtr.
- `cubic-ss.txt`: `ss -tin` at 5 s and 15 s. `cubic-tc.txt`: `tc -s` on s0 (fq) and r1 at the end.
- `bbr-*`: the same four files for `--cc bbr`. **Not recorded yet**: `tcp_bbr` was not loaded
  (`/proc/sys/net/ipv4/tcp_available_congestion_control` read `reno cubic`); it needs
  `sudo modprobe tcp_bbr` once. `notes/plots/ch10_plots.py` adds the BBR series when `bbr-f.csv` exists.

Model runs come from `../gaincycle.py` with the four functions from the page's lab solution filled in
(the starter on disk raises NotImplementedError until you write them):

- `sim-bench.csv`: `--seconds 22` on the bench path (10 Mbit/s, 40 ms, 50-packet buffer).
- `sim-step-up.csv`: `--seconds 12 --step 8:20`, the bottleneck doubled at 8 s (Fig. 5, top).
- `sim-steps-limit1000.csv`: `--seconds 20 --limit 1000 --step 8:20 --step 14:10` (Fig. 5, both halves).

`python3 ../summary.py cubic` and `python3 ../summary.py --sim sim-bench.csv` (from this folder, with
paths adjusted) print the numbers quoted in the page. They are the table view for the chapter's plots.
