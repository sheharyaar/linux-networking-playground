# Chapter 5 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

All runs use `labs/common/qnet.sh` (rootless, offloads off, 20 ms delay each way by default) and this
folder's tools: `flow.py` (TCP_INFO plus SO_MEMINFO every 10 ms; `--max-pacing-rate` sets
SO_MAX_PACING_RATE), `qwatch.py` (`tc -s -j qdisc` every 20 ms) and `gaps.py` (reads a pcap).
Reno everywhere. The machine was shared with other builders' runs; nothing here measures CPU.

## TSQ: the bottleneck on the sender's own interface (20 s each)

Common setup: `rtr:r1` deleted and re-added as `netem delay 20ms limit 100000` (data delay, no rate);
`rcv:c0` keeps qnet's 20 ms (ack delay), so the empty-path RTT is 40 ms.

| files | `s0` root | `net.ipv4.tcp_limit_output_bytes` in `snd` |
|---|---|---|
| `tsq-tbf-default-{qdisc,flow}.csv` | `tbf rate 10mbit burst 1540 latency 2s`, child `pfifo limit 10000` | 4194304 (default) |
| `tsq-tbf-lob64k-{qdisc,flow}.csv` | same | 65536 |
| `tsq-tbf-lob4k-{qdisc,flow}.csv` | same | 4096 |
| `orphan-netem-{qdisc,flow}.csv` | `netem rate 10mbit limit 10000` (orphans each skb at enqueue) | 4194304 |

`tsq-runs-transcript.txt` has the qdisc lines and the flow summaries; `ss-tmi-tsq-tbf.txt` is one
`ss -tmi` line taken 5 s into a separate 8 s run of the default case.

Headline (seconds 3–20): tbf default and 64 KB: backlog 4–7 packets (median 9,084 B), wmem_alloc median
14,448 B, RTT 48 ms, 9.52 Mbit/s, 0 retransmissions. 4 KB: backlog median 4,542 B, RTT 44 ms, same
goodput. netem: backlog 2.3–14.9 MB (median 6.5 MB), wmem_alloc 0 throughout, RTT 1.5–8.1 s.

## Pacing and fq spacing (10 s each), captured with tcpdump at `rtr:r0`

Setup: `rtr:r1` = `netem delay 20ms rate 10mbit limit 50`; `s0` = `fq` or `pfifo` (qnet's delay on
`s0` removed); `ip netns exec rtr tcpdump -i r0 -n -s 128 -w X.pcap --time-stamp-precision nano`.

| files | `s0` | cap |
|---|---|---|
| `pace-fq-cap5-{packets.csv,gaps.txt,qdisc.csv,flow.csv}` | fq | 5 Mbit/s |
| `pace-pfifo-cap5-{packets.csv,gaps.txt}` | pfifo | 5 Mbit/s |
| `pace-fq-nocap-{packets.csv,gaps.txt}` | fq | none |
| `pace-pfifo-nocap-{packets.csv,gaps.txt}` | pfifo | none |

`*-packets.csv` is `gaps.py --skip 0 --csv`: one row per data packet (time from the first data packet,
frame bytes, payload bytes, gap). `*-gaps.txt` is `gaps.py --skip 2`. fq-cap5: pairs every 4,632 us,
5.001 Mbit/s of payload; fq counters `throttled 2303` for 4,628 packets. pfifo-cap5 gives the same
spacing (TCP's internal pacing). Uncapped: pairs 2.42 ms apart after slow start in both; fq showed
`fastpath 4453 throttled 282`.

## TSO autosizing (8 s each, capture seconds 4–8)

`tso-autosize-bursts.txt`: no rate on `rtr:r1` (`netem delay 20ms limit 100000`), fq on `s0`,
`--max-pacing-rate` 20, 50, 100, 200, 500 Mbit/s. Bursts of 2, 4, 8, 16, 42 segments; median gaps
1157, 923, 920, 913, 938 us.

## fq system card (6 s, two flows)

`fq-two-flows-tc.txt`: `s0` = fq, `rtr:r1` = `netem delay 20ms rate 10mbit limit 50`, flows capped at
2 and 5 Mbit/s on ports 5001 and 5002; `tc -s qdisc` at 3 s and at the end.
`fq-two-flows-flowlimit2-tc.txt`: the same with `fq flow_limit 2` (no drops).

These files are the table view for the chapter's plots (`notes/plots/ch05_plots.py`) and the
reference output for the labs.
