# Chapter 14 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

All runs use this folder's `bigpair.sh`: a rootless (`unshare --user --map-root-user --net --mount`)
pair of namespaces, `snd` (10.0.14.1, fd14::1) and `rcv` (10.0.14.2, fd14::2), joined by one veth
pair `s0`–`c0`, MTU 1500, **offloads on** (veth's defaults: TSO and GSO on, GRO off), no qdisc, no
delay. Tools: `bulk.py` (one bulk flow, IPv4 or IPv6, 1 MiB writes and reads), `skblen.py` (skb
lengths from a pcap), `matrix.sh`, `capture.sh`, `grocap.sh`, `summarise.py`. Python 3.14, tcpdump
4.99.6, iproute2 7.2.0. Arch's kernel has `CONFIG_MAX_SKB_FRAGS=17` and `CONFIG_IRQ_TIME_ACCOUNTING=y`.

**Shared machine.** The laptop (Ryzen 7 8845HS, 8 cores, 16 threads) was running other builders'
labs at the same time. Load average 1.9–3.0 during the matrix; the whole machine was 11–21% busy
(`host_busy_frac`), and the two pinned CPUs were already 0.14–0.28 CPU-seconds per second busy
before each repetition (`role: idle` rows). The CPU numbers are therefore upper bounds, and the
comparison holds because the four cases were interleaved five times and every repetition agrees.

## Rootless knob behaviour (`rootless-knobs.txt`)

Inside the user namespace, `ip link set DEV gso_max_size|gro_max_size|gso_ipv4_max_size|gro_ipv4_max_size N`
succeeds for any N up to the ceiling: veth's `tso_max_size` is 524280 (= `GSO_MAX_SIZE` = 8 × 65535)
and `GRO_MAX_SIZE` is 524280. 524281 or 600000 fails with `Error: too big gso_max_size.` (or
`gro_max_size`), exit status 2. A `dummy` device (tso_max_size 65536) refuses 185000 the same way.
Setting `gso_max_size 32000` also set `gso_ipv4_max_size` to 32000 (the legacy coupling).
`net.core.max_skb_frags` does not exist inside the new netns (host value 17).

## Bulk flows, 64 KB against 185,000 (`veth-matrix.jsonl`, `veth-summary.csv`)

`./bigpair.sh -- ./matrix.sh 5 8 data/veth-matrix.jsonl`: five repetitions × {IPv6, IPv4} ×
{65536, 185000}, 8 s each, sender pinned to CPU 5 and sink to CPU 6 (`taskset`), all four knobs set
on both ends before each flow. `cpus_busy_s` is the busy time of CPUs 5 and 6 from `/proc/stat`
(user + nice + system + irq + softirq + steal), which includes both ends' softirq work.
`python3 summarise.py data/veth-matrix.jsonl --csv data/veth-summary.csv`:

| family | knobs | Gbit/s median (range) | CPU-s per GB median (range) |
|---|---|---|---|
| IPv6 | 65536 | 55.8 (53.8–56.6) | 0.2175 (0.2122–0.2265) |
| IPv6 | 185000 | 69.1 (68.0–71.2) | 0.1552 (0.1497–0.1574) |
| IPv4 | 65536 | 54.6 (52.2–57.9) | 0.2212 (0.2120–0.2342) |
| IPv4 | 185000 | 69.2 (66.6–74.1) | 0.1558 (0.1426–0.1666) |

Throughput ×1.24 (IPv6) and ×1.27 (IPv4); CPU per byte ×0.71 and ×0.70.
Two-term fit, CPU per skb = F + b × payload bytes, through the two medians: IPv6 F = 6.15 µs,
b = 0.122 ns/byte; IPv4 F = 6.60 µs, b = 0.120 ns/byte (the page's model plot).

## What the receiver sees (`capture-transcript.txt`, `skb-lengths.csv`, `tcpdump-text.txt`)

`./bigpair.sh -- ./capture.sh /tmp/x`: 2 s flows, `tcpdump -i c0 -s 128 -c 20000` in `rcv`.
`skb-lengths.csv` keeps the first 2,000 data skbs of each capture (frame = pcap original length = skb->len).

| capture | largest frame | segments × MSS | IP length field 0 |
|---|---|---|---|
| IPv6, 65536 | 64,346 B | 45 × 1428 | 0 of 20,000 |
| IPv4, 65536 | 65,226 B | 45 × 1448 | 0 of 20,000 |
| IPv6, 185000 | 184,298 B | 129 × 1428 | 19,963 of 20,000 |
| IPv4, 185000 | 183,962 B | 127 × 1448 | 19,963 of 20,000 |

No IPv6 skb carried a hop-by-hop header (kernel ≥ 7.0). tcpdump prints IPv4 BIG skbs as
`length 183948 [was 0, presumed TSO]` and IPv6 ones as `payload length 0) fd14::1 > fd14::2: [|tcp]`.

## MSG_ZEROCOPY at 185,000 (`zerocopy-transcript.txt`)

`bulk.py send --zerocopy`: the largest skbs were 69,698 B (IPv4) and 69,718 B (IPv6), i.e.
17 frags × 4096 B = 69,632 B of payload, although the knobs allowed 185,000.

## GRO on the far end (`gro-path-transcript.txt`, `gro-lengths.csv`)

`./bigpair.sh --gro-path [--size 185000] [--rate 10mbit] -- ./grocap.sh SECONDS PREFIX`: `s0` has
TSO off (the sender segments in software, so 1,514-byte frames cross the veth) and `c0` has GRO on
(veth runs NAPI GRO). Single runs; `gro-lengths.csv` keeps the first 1,000 skbs of each capture.
- default knobs: GRO handed up 64,346 / 65,226 B skbs (21.4 Gbit/s).
- 185000: 184,298 / 183,962 B (22.9 Gbit/s); 93% / 88% above 65,535 B.
- 185000 with `tbf rate 10mbit` on `s0`: median 1,514 B (one frame), largest 14,366 / 14,546 B
  (ten frames after an idle gap); 4,858 of 5,000 IPv4 skbs were single frames, 1.21 ms apart.

## ss and a knob raised mid-flow (`ss-and-live-raise.txt`)

`ss -tmi` during an IPv4 flow: segs_out / segs_in ≈ 43 at 65536 and ≈ 119 at 185000, about one
ack per skb in both. Raising the IPv4 knobs on both ends 1 s into a flow left that connection at
65,226 B skbs; the next connection got 183,962 B.
