# Chapter 4 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1, iproute2 7.2.0)

Every run starts from a fresh `labs/common/qnet.sh` bench (20 ms delay each way, offloads off).
The netem bottleneck on `rtr:r1` was deleted and replaced as listed below. Flows are Reno bulk
transfers from `../flow.py` (the chapter copy, which adds a `wall_s` column), sampled every 10 ms.
The machine was shared with other builds; at 10 Mbit/s that does not change the numbers.

## Two customers on one 10 Mbit/s uplink (HTB)
Tree: root qdisc `1:` htb (`default 20`), root class `1:1` rate = ceil = 10 Mbit/s, two leaf classes
`1:10` (customer A, port 5001) and `1:20` (customer B, port 5002), each with a `pfifo limit 50` leaf
queue, classified by `flower ip_proto tcp dst_port`. Run with `../phases.sh`.

| files | leaf rates (ceil 10 Mbit/s) | quantum | phases | goodput |
|---|---|---|---|---|
| `eq-*` | 5 / 5 Mbit/s | default (62500) | A 0–40 s, B 10–30 s | A alone 9.56; both 4.78 / 4.78; A alone again 9.56 |
| `split31-*` | 7.5 / 2.5 Mbit/s | default | A 0–30 s, B 5–25 s | both 7.17 / 2.44 |
| `spare31-*` | 3 / 1 Mbit/s | default (37500 / 12500) | same | both 7.17 / 2.39 |
| `spare31q-*` | 3 / 1 Mbit/s | 1514 / 1514 | same | both 5.74 / 3.82 |

- `eq-a.csv`, `eq-b.csv`: flow.py rows. `eq-goodput.csv`: 1 s bins on a shared axis (goodput.py).
- `eq-classes.csv`: cwatch.py, every class every 0.25 s (bytes, lended, borrowed, tokens, ctokens).
- `eq-class-at8.txt`, `eq-class-at20.txt`, `eq-class-end.txt`, `eq-qdisc-at20.txt`: `tc -s` snapshots.
- `*-goodput.csv`, `*-class-at18.txt`, `*-class-config.txt` (`tc -d class show`) for the other three.

## A shaper is a queue (one flow, HTB class rate = ceil = 5 Mbit/s)
| files | leaf queue | goodput | RTT median / max |
|---|---|---|---|
| `q-default-*` | none given, so HTB's default pfifo, limit 1000 (the veth txqueuelen) | 4.77 Mbit/s | 2459 / 2461 ms |
| `q-pfifo50-*` | `pfifo limit 50` | 4.77 Mbit/s | 123 / 160 ms |
| `q-fqcodel-*` | `fq_codel` (defaults) | 4.29 Mbit/s | 44 / 52 ms |

RTT statistics use rows after t = 8 s (q-default, q-fqcodel) or t = 5 s.

## TBF as the uplink cap
`tbf50-*`: `tbf rate 10mbit burst 32kb latency 50ms` on rtr:r1, one 20 s flow. tc computed the inner
bfifo limit as 95268 bytes (`tbf50-qdisc-config.txt`, from `tc qdisc show dev r1 invisible`).
`tbf50-root-q.csv` is qwatch.py every 20 ms: the backlog peaked at 93868 bytes (62 packets), 75 ms
of sending at 10 Mbit/s. Goodput 9.56 Mbit/s; RTT median 88 ms, max 115.5 ms.

## A policer instead of a shaper
`pol-16k-*`, `pol-64k-*`, `pol-256k-*`: no shaper on rtr:r1; an ingress `police rate 5mbit burst B
conform-exceed drop` on rtr:r0 for the flow's packets. Goodput 2.33 / 4.80 / 4.82 Mbit/s, total
retransmissions 86 / 348 / 551, RTT median 40.3–40.6 ms (no queue anywhere).
`*-police-end.txt` is `tc -s filter show dev r0 ingress` at the end.

## The direct-queue trap
`direct-*`: htb with `default 30` (a class that does not exist) and a filter for the wrong port
(5011). Every packet went to HTB's direct queue: `direct_packets_stat 246585`, 353 Mbit/s unshaped.

These files are the table view for the chapter's plots and the reference output for its labs.
