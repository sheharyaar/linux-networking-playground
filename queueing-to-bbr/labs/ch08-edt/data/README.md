# Chapter 8 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

All runs use `labs/common/qnet.sh` (rootless: `unshare --user --map-root-user --net --mount`, offloads
off) and this folder's tools: `txtime.py` (UDP with SO_TXTIME), `txgaps.py` (matches a capture with the
stamps), `flow.py` and `gaps.py` (unchanged copies of the chapter 5 tools). Captures are
`tcpdump -i r0 --time-stamp-precision nano` inside `rtr`, so each packet is timed as it arrives from
`snd:s0`. The machine was shared with other builders' runs; nothing here measures CPU.

## UDP with SO_TXTIME: fq, its horizon, then ETF (`udp-transcript.txt`)

Setup as collected: qnet's delay on `s0` removed, `rtr:r1` deleted and re-added as
`netem delay 20ms rate 10mbit limit 50`, `s0` root `fq`. That combined form shrinks r1's buffer to about 33
packets (netem counts its delay line, `sch_netem.c:552`), so the lab page now uses the bench's corrected
form instead: r1 left as qnet built it and the 20 ms moved to the ack path (`rcv:c0` root
`netem delay 40ms limit 100000`). No number here depends on it: captures are at `rtr:r0`, upstream of r1,
and 200 B datagrams 1 ms apart (1.6 Mbit/s) never queue at a 10 Mbit/s bottleneck. `rcv` runs `txtime.py --listen` on port 9000
so no ICMP port-unreachable comes back. Datagrams are 200 B on the wire, stamps 1 ms apart, each handed
to the kernel about 5 ms before its stamp unless noted.

| file | what |
|---|---|
| `udp-fq-inorder.csv` | fq, 1000 CLOCK_MONOTONIC stamps; one row per packet: stamp and capture time (µs from the first stamp), lateness |
| `udp-fq-reverse8.csv` | fq, 400 stamps, each group of 8 handed down in reverse order |
| `udp-etf-delta{500000,100000,50000,20000,10000}.csv` | `etf clockid CLOCK_TAI delta D` (ns), 1000 CLOCK_TAI stamps; delta 0 sent nothing to the wire |
| `udp-transcript.txt` | every command's output, including the host-side EPERM check, past stamps, the horizon (drop and cap), ETF's refusals, and the CAP_NET_ADMIN check with `setpriv` |

Headline: fq left every packet a median 13 µs after its stamp (p99 25 µs), in stamp order even when the
stamps were handed down reversed; stamps 45 ms in the past left at once; 20 stamps 11 s ahead were
dropped (`horizon_drops 20`); with `horizon 2s horizon_cap`, 20 stamps 5 s ahead were capped
(`horizon_caps 20`) and left together, 0.9 µs apart. ETF attached on the veth; software ETF released each
packet `delta` early plus about 3 µs (−497 µs at delta 500 µs, −17 µs at 20 µs); at delta 10 µs it dropped
30 of 1000 as `TXTIME_MISSED` (5 in an earlier run), at delta 0 all 1000 (`overlimits 1000`). Past stamps, a
CLOCK_MONOTONIC socket and ping were all dropped at enqueue (`ENOBUFS` to the sender; `TXTIME_INVALID_PARAM`
on the error queue for the SO_TXTIME sockets). ETF also dropped the kernel's own IPv6 packets on an idle
link (6 in 8 s; none with `disable_ipv6`), and ARP, hence the permanent neighbour entry. `tc qdisc replace`
on an etf root fails ("Change operation not supported"), and `clockid CLOCK_MONOTONIC` is refused
("Invalid clockid. CLOCK_TAI must be used.").

## TCP at 24 Mbit/s, three pacers (`tcp24-*`)

Short path: qnet's three netem qdiscs deleted (veth `noqueue` everywhere; ping RTT 0.032–0.044 ms).
`net.ipv4.tcp_tso_rtt_log=0` in `snd`, so TSO autosizing uses the 2018 rule (no RTT bonus). CUBIC, 10 s
each. `--max-pacing-rate` sets SO_MAX_PACING_RATE.

| name | `snd:s0` root | socket cap | who decides each departure time |
|---|---|---|---|
| `before` | `fq maxrate 24mbit` | 24 Mbit/s | fq, from the rate, at dequeue (the 2013 arithmetic: wire bytes from `now`) |
| `edt` | `fq` | 24 Mbit/s | TCP, `tcp_wstamp_ns` into `skb->tstamp`; fq holds the skb until then |
| `internal` | `fq_codel` | 24 Mbit/s | TCP, and TCP's own hrtimer holds the next skb |
| `maxrate-nocap` | `fq maxrate 24mbit` | none | fq, from the rate; TCP sizes skbs from its own 88 Mbit/s rate |

Files: `*-flow.csv` (`flow.py` TCP_INFO every 10 ms), `*-packets-5to6s.csv` (one second of the capture,
`gaps.py --csv`), and `tcp24-transcript.txt` (the `ss -tin` line at 6 s, `tc -s` after, `gaps.py` and medians).

Headline (seconds 2–10): before RTT 2.026 ms, pairs every 1008 µs, 22.955 Mbit/s of payload, unacked 4;
edt 0.028 ms, pairs every 964 µs, 24.001 Mbit/s, unacked 4; internal 0.016 ms, 964 µs, 24.001 Mbit/s,
unacked 0; maxrate-nocap 7.077 ms with 7-segment skbs every 3.52 ms.

`tcp24-wrongturn-rttlog9.txt`: the same before and edt runs with `tcp_tso_rtt_log` left at 9: 64 KB skbs
(45 segments) on this short path, before RTT 45.4 ms, edt 0.16 ms. It also shows that
`tc qdisc replace dev s0 root fq` on an existing fq keeps its `maxrate`.

## The rate-model sweep (`rate-model-sweep.csv`)

The before and edt setups above at 14 caps from 6 to 192 Mbit/s, 6 s each (median RTT over seconds 2–6,
burst size and gap from a 2 s capture). This is the table view of the chapter's Diagram 8.3. The model
line there is 2 × segs × 1514 × 8 / cap, with segs = max(2, floor((cap/8 >> 10) / 1448)) and no
path term: every measured median sits 4–18 µs above it.
