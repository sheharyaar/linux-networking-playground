# Chapter 7 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1, HZ = 1000)

The machine was shared with other builders' runs. Only the build lab and `wheelwait.py` time anything,
and both say so. Everything here ran without sudo.

## The kernel's timer wheel: `wheelwait.py`

| file | what |
|---|---|
| `wheelwait.csv` | one row per wait: `kind` (`wheel` = blocking `recv()` with `SO_RCVTIMEO`, which sleeps in `schedule_timeout()` on a `timer_list`; `hrtimer` = `time.sleep()`), `requested_ms`, `elapsed_ms`, `late_ms`. 10 timeouts from 20 ms to 10 s, 3–20 repeats each, each pair started at a random point inside one wheel slot. Diagram 7.3. |
| `wheelwait-transcript.txt` | the summary table of that run |
| `wheelwait-quick.txt` | `python3 wheelwait.py --quick`, the output quoted in the timer-wheel system card |

Headline: every wheel wait came back less than one slot width late (1, 8, 64, 512 ms by level), plus
up to about 3 ms of scheduling noise in the quick run; hrtimer sleeps were about 0.1 ms late.

## Timing wheel against a heap: `wheel_starter.py`

| file | what |
|---|---|
| `wheel-vs-heap.txt` | the starter's driver with the page's solution wheel, 100 to 100,000 flows, 300,000 releases per run. Heap comparisons per packet 8.8 / 12.1 / 15.4 / 18.8; wheel operations 4.1 / 4.0 / 4.0 / 4.0; ns per packet heap 528 → 2,522, wheel 529 → 1,275 (shared CPU). |
| `starter-literal-poll3.txt` | `--literal --poll 3`: the printed Algorithm 1 released 53 of 20,000 packets before the driver's stop guard |
| `alg1-check.txt` | Algorithm 1 as printed, with slip (b) fixed (front += 1), and with both fixed (sweep `TW[front]`), polling every slot and every third slot |

## Sixteen rate limits on the bench: `run-bench.sh`

Each run builds a fresh `labs/common/qnet.sh` bench (rootless, offloads off), applies `shapers.sh`,
starts 16 Reno flows with `mflow.py` for 30 s (one process, ports 5001–5016), and samples the shaper's
qdisc every 50 ms with `qwatch.py`. The empty-path RTT is 40 ms in all three.

| prefix | shaper | where |
|---|---|---|
| `htb-snd-*` | 16 HTB classes, `rate 500kbit ceil 500kbit`, `pfifo limit 100` leaves, u32 filters on dport | `snd:s0`; `rtr:r1` = `netem delay 20ms limit 10000` |
| `fq-snd-*` | `fq maxrate 500kbit` | `snd:s0`; `rtr:r1` as above |
| `htb-rtr-*` | the same 16 HTB classes | `rtr:r1`; `snd:s0` keeps qnet's `netem delay 20ms`, which orphans each skb |

In the two `s0` runs `rtr:r1` carries only the 20 ms data delay, with no rate: at 8 Mbit/s its delay line
holds about 14 packets, far below `limit 10000` (netem counts its delay line against `limit`,
`sch_netem.c:552`), so the shaper on `s0` is the only queue on the path and the router never drops.

`ackpath/` holds the same three runs with the bench recipe in BUILD-BRIEF §10 instead (`ROUTER=qnet`:
`r1` left as qnet's `netem rate 10mbit limit 50`, `s0`'s delay moved to the acks as `rcv:c0 netem delay
40ms`). Held bytes, drops and output rates are the same; the `s0` runs' RTT rises from 137 ms to a
median 155 ms (130–174), because the 16 equal-rate classes release their two-frame skbs in step and the
10 Mbit/s hop queues those bursts at 80% load. The page uses the runs at the top level, where the shaper
is the only queue.

Files per run: `*-flows.csv` (per flow every 0.1 s: bytes_acked, cwnd, rtt_ms, total_retrans,
wmem_alloc), `*-qdisc.csv` (root qdisc backlog and sent bytes every 50 ms), `*-summary.txt`
(`mflow.py`'s goodput line), `*-tc-at20s.txt` (`tc -s qdisc` and, for HTB, `tc -s class`, 20 s in).
`bench-summary.txt` is the table below; `bench-transcript.txt` the console; `bench-date.txt` the start.

| shaper | held median / max | out | RTT median (min–max) | resent | wmem_alloc |
|---|---|---|---|---|---|
| htb on s0 | 96,896 / 96,896 B (32 skbs) | 8.007 Mbit/s | 137 ms (132–138) | 0 | 7,712 B |
| fq on s0 | 96,896 / 96,896 B (32 skbs) | 7.990 Mbit/s | 137 ms (126–137) | 0 | 7,712 B |
| htb on r1 | 1,401,964 / 2,422,400 B (926 / 1,600 pkts) | 8.002 Mbit/s | 1,743 ms (1,236–2,471) | 1,614 | 0 B |

Note: `mflow.py`'s per-flow goodput for `htb-rtr` reads 0.485 Mbit/s, above the 0.478 a 500 kbit/s class
leaves for payload, because the RTT fell from 2.4 s at 5 s to 1.4 s at 30 s. Rate is read at the
shaper's output (`sent_bytes` in `*-qdisc.csv`).
