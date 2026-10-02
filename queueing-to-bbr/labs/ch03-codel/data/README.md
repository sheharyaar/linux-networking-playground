# Chapter 3 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1, iproute2 7.2.0)

All runs use `../run.sh`, which builds `labs/common/qnet.sh` (snd -> rtr -> rcv, 20 ms delay each way,
offloads off) and replaces the bottleneck on rtr:r1 with `tbf rate 10mbit burst 1540 latency 2s`
(a plain rate limiter) whose child qdisc, handle 2:, holds the queue. The sender is
`flow.py send --cc reno`; a `ping -i 0.1` runs alongside as a second flow; `qstat.py` samples the
child qdisc every 10 ms (5 ms for the UDP run). The machine was shared with other builders; at
10 Mbit/s that does not matter.

Columns: `*-tcp.csv` are flow.py's TCP_INFO samples (`t_s` from connect, `rtt_ms` is the smoothed RTT).
`*-q.csv` are qstat.py's samples of the child qdisc (`ldelay` in microseconds, `drop_next` in
microseconds from the sample time, `dropping` 0/1). `*-ping.txt` is raw `ping -D` output; the plots
place each ping at `icmp_seq x 0.1 s`, which lines up with the TCP clock to within about 0.3 s.

| files | command | headline |
|---|---|---|
| `pfifo-*` | `./run.sh pfifo --seconds 40 --out data/pfifo` | 9.54 Mbit/s; TCP RTT median 655 ms (p95 1237); backlog median 513 packets; ping median 653 ms |
| `codel-*` | `./run.sh codel --seconds 40 --out data/codel` | 8.35 Mbit/s; TCP RTT median 42.2 ms (p95 49.8); backlog median 1 (p95 8); ping median 41.1, max 52; 36 CoDel drops from 5 s to 40 s |
| `fq_codel-*` | `./run.sh fq_codel --seconds 40 --out data/fq_codel` | 8.34 Mbit/s; TCP RTT median 42.2 ms; ping median 40.4, max 41.3 |
| `codel-4flows-*` | `./run.sh codel --flows 4 --seconds 40 --out data/codel-4flows` | four Reno flows: 2.33 + 2.30 + 2.42 + 2.35 = 9.40 Mbit/s; Jain index 0.9996 |
| `fq_codel-ecn-*` | `./run.sh fq_codel --ecn --seconds 20 --out data/fq_codel-ecn` | sender asks for ECN: 26 marks, 0 drops, 0 retransmissions, RTT median 42.2 ms |
| `step-pfifo-*` | `./run.sh pfifo --seconds 60 --step-at 20 --out data/step-pfifo` | 10 -> 1 Mbit/s at 20 s: the ~530 queued packets become 6.4 s; TCP RTT 6.5 s from 26 s on |
| `step-codel-*` | `./run.sh codel --seconds 60 --step-at 20 --out data/step-codel` | sojourn spike 360 ms; count reaches 29; RTT under 100 ms within 2 s; afterwards ldelay about 45 ms, ping about 65 ms (one frame is 12.1 ms at 1 Mbit/s) |
| `udp-codel-*` | `./run.sh codel --udp 11 --seconds 10 --every 0.005 --out data/udp-codel` | open-loop UDP at 11 Mbit/s: first dropping episode 0.143 -> 3.350 s, count 286 at exit; 836 drops in 10 s (84/s against an 83/s excess) |
| `snap-*-snap.txt` | `./run.sh codel --seconds 16 --step-at 10 --snap "8 10.3 10.6 11 13"`, `./run.sh fq_codel --seconds 12 --snap "6 9"` | real `tc -s qdisc show dev r1` text at those moments (the system card quotes 10.3 s and 9 s) |

Notes.

- The step runs: `tc qdisc change ... tbf` also resets a pfifo child's limit to tbf's byte limit
  (tbf_change() calls fifo_set_limit(), net/sched/sch_tbf.c:443-444; 251540 "packets" here), so
  run.sh sets `pfifo limit 1000` again straight after the change.
- In two of three pfifo step runs the sender processed no acks for about 3.4 s at 46-50 s (26 s after
  the step), with no retransmission and no timeout; a third run with `ss` sampling instead of ping
  and qstat did not show it. The cause was not found. The page's plot stops at 45 s.
- The 1.0-1.2 s ack gaps at 3-8 s in the pfifo runs are loss recovery after slow start, when the RTT
  is 1.2 s.
