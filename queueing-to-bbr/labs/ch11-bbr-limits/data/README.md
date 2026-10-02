# Chapter 11 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1, rootless)

Every bench run builds `../../common/qnet.sh`'s three namespaces, then the chapter's scripts change it:

- `snd:s0` egress: `fq` (qnet's `netem delay 20ms` removed; BUILD-BRIEF section 10);
- `rcv:c0` egress: `netem delay 40ms limit 100000` (the whole RTT on the ack path);
- `rtr:r1` egress, the bottleneck: `netem rate 10mbit limit L [loss P%]`, no delay. One BDP is
  33.0 full-size packets (825.6 packets/s x 40 ms), so L = 17 is half a BDP and L = 330 is ten.

`tcp_bbr` was **not loaded** on the host (`/proc/sys/net/ipv4/tcp_available_congestion_control`
printed `reno cubic` at 13:30 and again at 16:15), so no BBR run exists yet. Every file below is
CUBIC or Reno. Rerun the BBR commands from the page after `sudo modprobe tcp_bbr`; the plot script
draws `duel-bbr-summary.csv` (columns `bdp,bbr_share_pct`) and `sweep-bbr.csv` (losssweep.sh's
format) automatically when they exist.

The machine was shared with other builders' runs; at 10 Mbit/s that does not change the results.

## One CUBIC flow alone, 60 s, per buffer depth (`../losssweep.sh --loss 0 --limit L`)

- `solo-cubic.csv`: one row per depth (cc, limit, loss, goodput over the last 40 s, mean RTT,
  retransmissions, segments). L = 4, 17, 33, 330 (and 333, a first try at ten BDPs).
- `run-solo-cubic-L*-p0.csv`: the `flow.py` samples (every 50 ms) behind each row.

## Two flows on one bottleneck, 120 s, share over 60-120 s (`../duel.sh`)

- `duel-cc-shallow-{a,b,q}.csv`, `duel-cc-shallow-r1.txt`: CUBIC against CUBIC, L = 17.
  Jain 0.993 (54.2% / 45.8%), RTT 56 ms, 290 router drops.
- `duel-cc-deep-{a,b,q}.csv`, `duel-cc-deep-r1.txt`, `duel-cc-deep-transcript.txt`: CUBIC against
  CUBIC, L = 330. Jain 0.989 (44.8% / 55.2%), RTT 380 ms, 228 drops.
- `duel-cc-deep333-*`: the same at L = 333 (Jain 1.000, RTT 387 ms); transcript of both first runs
  in `duel-cc-shallow-and-deep333-transcript.txt`.
- `-a.csv`/`-b.csv` are `flow.py` samples, `-q.csv` is `qwatch.py` on `rtr:r1` every 100 ms,
  `-r1.txt` is `tc -s qdisc show dev r1` at the end.

## Random loss on the bottleneck, one flow at a time, 30 s per point (`../losssweep.sh`, L = 300)

- `sweep-cubic-reno.csv`: one row per (cc, loss %): goodput over the last 20 s, mean RTT,
  retransmissions, segments, retransmitted %. Diagram 11.3's top panel.
- `run-sweep-{cubic,reno}-P.csv`: the `flow.py` samples behind each row.
- `wrongturn-ackloss10.{csv,txt}`: the loss lab's wrong turn, `loss 10%` on `rcv:c0` (the acks)
  instead of the bottleneck: CUBIC still 9.54 Mbit/s.

## Model output (no bench)

- `ware-model-bench.txt`: `python3 ../ware_model.py` (the spine path), the paper lab's solution.
- `ware-model-cao-fig8.txt`: the same model on Cao et al.'s Fig. 8 path (1 Gbit/s, 20 ms).
