# Chapter 12 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

All runs use `labs/common/qnet.sh`, which is rootless (`unshare --user --map-root-user --net --mount`) with offloads off. Each script removes the qdiscs it does not want. Neither script touches `rcv:c0`, so qnet's 20 ms netem stays on the return path.

The tools are in the folder above:
- `txtime.py`: UDP with SO_TXTIME. It is chapter 8's tool plus `--clock real` and `--no-stamp`.
- `txgaps.py`: chapter 8's tool, unchanged. It matches a capture with the stamps.
- `podedt.py`: a UDP sender that applies Cilium's `edt.h` arithmetic itself.
- `rxcount.py`: 100 ms bins of arrivals.
- `eyeq_loop.py`: EyeQ's rate rule, iterated.

Nothing here needed sudo. The machine was shared with other builders' runs, so nothing here measures CPU. The pcaps were not kept; the CSVs carry every packet.

## Stamps across the router (`cross-*`, `./run-stamps.sh`)

Setup:
- `snd:s0` is set to `noqueue`, so nothing on the sender reads a stamp.
- `rtr:r1` gets plain `fq`, with its defaults (horizon 10 s).
- `rcv` runs `txtime.py --listen`.
- Datagrams are 200 B on the wire, stamps are 1 ms apart, and each is handed down about 5 ms before its stamp.
- Two captures in `rtr` (`tcpdump --time-stamp-precision nano`): `r0` times each packet as it arrives from `snd`, and `r1` times it as fq lets it go.

| file | what |
|---|---|
| `cross-{none,mono,tai,real,burst}-stamps.csv` | the sender's planned stamps; the first line records the clock and REALTIME minus that clock |
| `cross-*-r0.csv`, `cross-*-r1.csv` | `txgaps.py --csv`: one row per captured packet with its stamp, capture time (µs from the first stamp) and lateness |
| `cross-transcript.txt` | every command's output, both medians per run, and `tc -s` on r1 at the end |

The runs:
- `none`: no SO_TXTIME at all. The planned times still go into the payload.
- `mono`, `tai`, `real`: the socket's SO_TXTIME clock.
- `burst`: 50 monotonic stamps 1 ms apart, all handed down at once.

Headline, median lateness (capture minus stamp):

| run | at r0 | at r1 (after fq) |
|---|---|---|
| none | −4,939 µs | −4,935 µs |
| mono | −4,939 µs | +12.4 µs |
| tai | −4,937 µs | +12.7 µs |
| real | −4,935 µs | −4,931 µs |

A monotonic or TAI stamp reaches the router's fq and is honoured. A realtime stamp is cleared at the first hop like a receive time. The burst arrived 4.5 µs apart at r0 and left 1,000.1 µs apart at r1. fq on r1 ended with `throttled 2050`, which is 1000 (mono) + 1000 (tai) + 50 (burst).

In `none`, r1's p99 (+6.1 ms) and max (+15.1 ms) come from the first ~16 packets. They waited about 20 ms for ARP, because the reply crosses `rcv:c0`'s netem. The lab page calls this its common wrong turn.

## A pod over its limit (`edt-*`, `./run-overload.sh`)

The sender is `podedt.py --limit 10M`: 1,250,000 B/s, or 1,211.2 µs per 1,514-byte datagram on the wire. It runs for 8 s.

The sender is the pod. The router takes the socket away at `ip_rcv`, as the host stack does without BPF host routing. fq uses Cilium's settings: `horizon 2s buckets 32768`, with `flow_limit` 100 unless noted. qnet's netem on `s0` and `r1` is removed, so the limiter is the only thing that sets the rate.

`rxcount.py` in `rcv` takes the one-way delay from the send time in each payload. Both namespaces read the same CLOCK_MONOTONIC.

| name | fq on | flow_limit | horizon | SO_SNDBUF | offered |
|---|---|---|---|---|---|
| `under` | r1 | 100 | 2 s | default | 8 Mbit/s |
| `over` | r1 | 100 | 2 s | default | 20 Mbit/s |
| `bigfq` | r1 | 2000 | 2 s | default | 20 Mbit/s |
| `short` | r1 | 100 | 100 ms | default | 20 Mbit/s |
| `kept` | s0 (socket still attached) | 100 | 2 s | 212,992 | 20 Mbit/s |
| `keptbig` | s0 | 100 | 2 s | 8,388,608 (`--sndbuf 4194304`, doubled) | 20 Mbit/s |

Files:
- `edt-NAME-rx.csv`: `t_s, pkts, mbit_wire, owd_ms_median` per 100 ms bin.
- `edt-NAME-tx.csv`: the sender's log every 100 ms: `ahead_ms`, which is t_last minus now, plus the offered, passed, stamped and horizon-drop counters.
- `edt-transcript.txt`: podedt's summary, rxcount's per-second table, and `tc -s` after each run. The two `kept` runs are a second invocation of the same script.

Headline (seconds 4–7):

| run | delivered | delay | other |
|---|---|---|---|
| under | 8.0 Mbit/s | 0 ms | |
| over | 0.59–0.62 Mbit/s | 1,999.7 ms | flows_plimit 7,354; podedt offered 13,211, stamped 8,256, horizon drops 4,954; 903 delivered |
| bigfq | 10.0 Mbit/s | 2 s | |
| short | 10.0 Mbit/s | 100 ms | |
| kept | 10.0 Mbit/s | 85.8 ms | the sender blocked and offered only 6,673 |
| keptbig | 0.58–0.63 Mbit/s | 2 s | flows_plimit 7,354 |

`over` is Little's law: 100 packets held for 2 s is 50 pkt/s, about 0.6 Mbit/s. The limiter never learns that fq dropped a packet it stamped, so its clock runs to the horizon.

`notes/plots/ch12_plots.py` draws `over`, `bigfq`, `short` and `kept` as Diagram 12.4.

## The rate loop (`eyeq-loop.txt`, `python3 eyeq_loop.py`)

EyeQ's rule R ← R(1 − α(y − C)/C) on one link, in 200 µs steps, with a floor of 1 Mb/s on 10 Gb/s. A run ends within 0.01% of C/N.

From line rate at α = 0.5:
- N = 14 takes 31 steps, 6.2 ms. The paper says "about 30 iterations", "6ms".
- The linear part alone takes 13.3 steps.

From 1.5 R* the step counts for α = 0.25 to 1.9 are 28, 11, 4, 12 and 45. α = 2.1 never settles.

## System card (`system-card-try-it.txt`)

The output of the card's Try-it:
- `default_qdisc` on the host: `fq_codel`.
- In a fresh `unshare -Urn` namespace: "No such file or directory".
- The congestion control copied into it: `cubic`.
- The fork's `bandwidth.go` probe lines: 172–173 and 261.

## Not here

Part (b) of the overload lab is `edt_lab.bpf.c` on r1, loaded with `sudo ./load-edt.sh`. It needs sudo and was not run. With the object built, the load fails with EPERM.
