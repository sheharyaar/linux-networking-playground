# NOTES — From a full buffer to BBR (a reading list as a book)

Spec: `~/workspace/learning/agent-directory/BOOK_GUIDED_BLOG_STYLE_LEARNING.md`.
The "book" is the numbered reading list in `~/Documents/Books/networking/routing-papers-bbr/`
(PDFs at the top level, fetched web copies in `web/`, approved additions in `extra/`).
Full per-paper inventories (13 headings each) live in `notes/inventory/inv-NN.md`.

## Reader contract

2026-10-02, Phase 0 answers through the question tool:

- **Finish line** (all four, plus "use your judgement"):
  1. Explain the chain: AIMD → CoDel → TSQ/fq → pacing → timing wheels/EDT → BBR. For each step, say what failure the step before it left behind.
  2. Diagnose a live host: from `ss -ti`, `tc -s qdisc` and a symptom, name the mechanism and prove it with a trace on kernel 7.2.
  3. Do the arithmetic by hand: BDP, queueing delay, buffer size, pacing rate, CoDel spacing, Maglev disruption.
  4. Own the Cilium knobs: Bandwidth Manager, BBR for pods, Maglev, BIG TCP.
- **Maths:** "Use it, derive in toggles". Each result is stated, explained in words and used on numbers in the page. The derivation sits in a `details.deriv` toggle.
- **Reading mode:** sandwich (default budgets: 10 min before, 20 min after).
- **Location:** this repo, `linux-networking-playground/queueing-to-bbr/`.
- **Starting point** (from the user-profile memory and `.alvar/LEARNER.md`, not re-asked):
  - Strong Linux networking; knows the netfilter chart cold; develops a Cilium fork (`~/workspace/neverinstall/cilium`, v1.19.6-vpc).
  - Bootstrap vocabulary, usable without ceremony: skb, qdisc as a word, veth, netns, tc as a command, TCP handshake and sequence numbers, sockets, eBPF/tc hooks, kube-proxy, Service, ECMP as a routing idea, MTU, GSO/GRO as names.
  - LEARNER.md: compact, simple English, mechanism plus code path. Banned words: leak, hurt, bites, substrate. Wants probing questions. Weak spot: symptom-driven diagnosis; over-applying a correct fact past its boundary.
- **Style:** compact, plain, with examples (learner profile). Mermaid is preferred over prose for structure.
- **2026-10-02, plan approval:**
  - "If possible add a zoom button in the mermaid part/svg part." Done in `assets/dossier.js`: zoom bar on every `figure.dia`, plus a full-screen view.
  - "I approve the changes."
  - The three open decisions were not answered, so the recommendations apply: KaTeX via CDN; chapter 2 at full length; the merges as planned.
- **Never install anything** (memory `no-installs-by-agent`). The user runs sudo.
- **2026-10-02, after reading chapter 1:**
  - "It would be good if standard deviation and other can be latex … Rest is fine, you can generate all the chapters."
  - Rule from now on: every formula, variable, Greek letter, sub/superscript and worked equation in prose (body text, captions, answers, hints, solutions, word lists) is KaTeX inline \( \). Code, Mermaid labels, SVG text and quiz prompts stay plain.
  - The user approved building chapters 2–14 and the capstone without per-chapter approval.
  - The three after-first-chapter calibration questions are answered by "rest is fine", so the primer depth, lab size and voice stay as in chapter 1.

## Book facts

| Ch | Resource | File | Edition / venue | Printed pages | PDF→printed |
|---|---|---|---|---|---|
| 01 | Jacobson, Congestion Avoidance and Control | 01-congestion-avoidance-and-control.pdf | SIGCOMM '88, CCR reprint | 158–173 (cover 157) | +156 |
| 02 | Bertsekas & Gallager, Data Networks 2e, ch. 3 | extra/bertsekas-gallager-data-networks-ch3-queueing.pdf | Prentice Hall 1992, author-hosted | §3.2 152–161, §3.3.1 164–171, §3.5 186–189; problems from 242 | +148 |
| 02 | Mathis, Semke, Mahdavi, Ott, Macroscopic Behavior of TCP | extra/mathis-…-1997-macroscopic-tcp.pdf | CCR 27(3) 1997 | 67–82 (no folios printed) | +66 |
| 02 | Appenzeller, Keslassy, McKeown, Sizing Router Buffers | extra/appenzeller-…-2004-…pdf | SIGCOMM '04 | 281–292 (no folios printed) | +280 |
| 03 | Nichols & Jacobson, Controlling Queue Delay | 02-controlling-queueing-delay.pdf | CACM 55(7) July 2012 | 42–50 | +41 |
| 04 | tc-tbf(8), tc-htb(8) | web/03a, 03b (+ .local.txt, iproute2 7.2.0) | man pages | sections | n/a |
| 04 | Shreedhar & Varghese, DRR | extra/shreedhar-varghese-1995-drr-sigcomm.pdf | SIGCOMM '95 | 231–242 (scan; read as images) | +230 |
| 05 | LWN TSQ (2012), LWN TSO sizing + FQ (2013), tc-fq(8) | web/04a, 04b, 03c | articles | sections | n/a |
| 06 | Aggarwal, Savage, Anderson, TCP Pacing | 05-tcp-pacing.pdf | INFOCOM 2000 preprint | none printed: use PDF p1–p9 | n/a |
| 07 | Saeed et al., Carousel | 06-carousel.pdf | SIGCOMM '17 | 404–417 | +403 |
| 08 | Jacobson, Evolving from AFAP (slides); Dumazet EDT cover letter | web/07a-…slides.pdf, web/07b-* | netdev 0x12 (2018); net-next 2018 | slide numbers 1–19 | n/a |
| 09 | Saeed et al., Eiffel | 08-eiffel.pdf | NSDI '19 | 17–31 | +15 |
| 10 | Cardwell et al., BBR | 09-bbr.pdf | CACM 60(2) Feb 2017 | 58–66 | +57 |
| 11 | Cao et al., When to use BBR | 10-when-to-use-bbr.pdf | IMC '19 | 130–136 | +129 |
| 11 | Ware et al., Modeling BBR's interactions | extra/ware-2019-bbr-interactions-imc.pdf | IMC '19 | 137–143 (no folios printed; Crossref) | +136 |
| 12 | Jeyakumar et al., EyeQ | 09-eyeq.pdf | NSDI '13 | 297–311 (PDF p9 has no text layer) | +296 |
| 12 | Lau, Preserve mono delivery time | web/11-* | net-next 2022 (v5.18) | email | n/a |
| 13 | Eisenbud et al., Maglev | 12-maglev.pdf | NSDI '16, Google author version (corrected Table 1) | 1–13 | 0 |
| 14 | LWN Going big with TCP packets; Isovalent BIG TCP on Cilium | web/13a, 13b | articles | sections | n/a |

**Exercises in the sources:** only Bertsekas & Gallager has problems (ch. 3, p. 242 on). That puts chapter 2 on the "book has questions" branch (`.bookq`). Every other chapter uses the `.check` branch.

**Errata found while inventorying.** Each one is re-verified before it ships as a `p.erratum` note.
- Jacobson p.169: "mdev ≥ sdev" is backwards. With 1/n normalisation mdev ≤ sdev, and for normal errors mdev ≈ 0.80·sdev.
- BBR p.64: "one loss per 30 million packets at 10 Gbps/100 ms" does not follow from 1/BDP². The figure fits about 1 Gbps.
- Carousel: the "1.5 Mbps minimum" contradicts "one packet per horizon". Algorithm 1 has indexing/unit slips; the units on Fig. 17's axis don't reconcile.
- Eiffel: a factor-2 slip in the gradient queue (p.22); BSR mislabelled "Bit-Scan-Forward" (p.21); "non-work conserving" written where work-conserving is meant (p.19).
- Maglev: the default M = 65537 for N = 1000 breaks the paper's own M > 100N rule. Cilium's docs read the 1% rule as a disruption bound; it is a balance bound.
- Pacing footnote 1 (p5): the sawtooth period formula is about 2× off from Fig. 4 (the inventory agent's derivation).
- Cao et al.: the 20% cliff can't be told apart from the BBRv1 policer threshold (50/256).

**Errata shipped in wave 1** (each verified on the rendered page by the chapter's builder; details in `notes/chapters/chNN.md`):
- ch02: Appenzeller p. 283 "times-out" where the argument needs a fast-retransmit halving; Appenzeller p. 286 table 99.99988% where Eq. 3 gives 99.988%; B&G solutions manual Problem 3.4 drops the ½; B&G Problem 3.9's printed answers are totals, the stem asks per session.
- ch03: CoDel p. 48 "250 seconds" is 200 s; p. 49 "512KB and 1.5MB" are kbit/s and Mbit/s. Reference slip (go-deeper only): ref 7's CACM volume/date.
- ch04: DRR p. 237 "Figure 1" means Table 1; tc-tbf(8) `latency` is not the maximum wait (limit = rate × latency + burst, so latency + burst/rate: 76 ms measured as 75).
- ch05: none shipped. Held: tc-fq(8) NAME calls fq "traffic policing".

**Errata shipped in wave 2:**
- ch06: pacing footnote 1 (PDF p. 5) gives 108.5 round trips for Fig. 4's sawtooth; the figure repeats every 75, and Mathis's derivation with an ack per packet gives 72 (off by 3/2, correcting the inventory's "about 2×"). Fig. 15's 0.26 curve is line C, not B (inventory slip).
- ch08: AFAP slide 9 is labelled M/D/1 but plots ρ/(1−ρ), the M/M/1 wait (1 packet time at 50%, 3 at 75%; coordinator checked the render). ch02's reference to slides 9–10 now says so.
- ch07: Carousel Algorithm 1 as printed strands packets (a direct transcription released 11,627 of 20,000; 53 when polling every third slot); the 1.5 Mbps minimum is 500× the paper's own one-packet-per-horizon rule, and Fig. 17's axis unit is wrong. Held: Fig. 6 and Fig. 13 caption issues.
- ch09: Eiffel p. 21 "Bit-Scan-Forward (BSR)" (BSR is reverse); p. 19 the second "non-work conserving" means work-conserving; p. 22 gradient queue: with b = Σ i·2^i the critical point is b/a, not b/2a, and the two slips cancel so ceil(b/a) is right.

**Errata shipped in wave 3:**
- ch10: BBR p. 64 "one loss per 30 million packets" at 10 Gbps/100 ms: the 1/BDP² rule gives about 1 in 6.9×10⁹ (RFC 3649 §1 independently says 5×10⁹); 30 million fits about 1 Gbit/s.
- ch11: Cao's 20% cliff is BBRv1's policer detector (lost/delivered ≥ 50/256, `tcp_bbr.c:188, 740–744`), which the paper never names for BBR_1.1: a missing explanation. Also Cao's "3×" at 10 MB is about 6× in Fig. 8a; Table 1's header prints 1e6 for 1e7.
- ch13: Cilium docs read the paper's 1% rule as a reassignment bound (it bounds balance; confirmed by running Cilium's own GetLookupTable); the first USENIX printing's Table 1 lists each slot's rank, fixed in the 8 March update (Google's copy, cited, is correct). Not an erratum: M = 65537 for N = 1000 (N = 1000 is only the test size).
- ch12: LPC 2021 (Cilium BWM talk) slide 24 says ingress stamps are CLOCK_TAI; the receive stamp is CLOCK_REALTIME (`skbuff.h:4448–4451`). Held: three EyeQ candidates (notes/chapters/ch12.md).
- ch14: Isovalent §1 calls a 1,538-byte frame an "MTU"; §5.2 reports "packets per seconds" and "50%" where its own output shows transactions per second and +45%.

**Since the sources (verified 2026-10-02):**
- Upstream v7.2 `tcp_bbr.c` is BBRv1. BBRv3 is out of tree; google/bbr branch `bbr-v3-2026-09-16-01` has `tcp_bbr3.c`; draft-ietf-ccwg-bbr-06 is dated 2026-07-06.
- `tcp_rate.c` was removed in v7.0; the rate sampler now lives in `tcp_output.c` and `tcp_input.c`.
- `skb->mono_delivery_time` became `skb->tstamp_type` in v6.11.
- BIG TCP over IPv6 stopped inserting the hop-by-hop jumbogram header in v7.0 (merge 1fdad81d8803).
- Linux IPVS gained a Maglev scheduler, `mh`, in v4.18 (039f32e8cdea, 2018; ch13).
- draft-ietf-ccwg-bbr-06 renames inflight_hi/lo to inflight_longterm/shortterm, specifies no ECN response (§3.7), and gives PROBE_DOWN gain 0.90 where the v3 code uses 91/100 (ch11).
- Since v7.0 (merge 1fdad81d8803, Feb 2026) IPv6 BIG TCP writes payload length 0 and takes the real length from the skb, as IPv4 BIG TCP has since v6.3; no hop-by-hop jumbogram header. Cilium's 1.20 docs still describe the HBH header. tcpdump prints such IPv6 skbs as `[|tcp]` (ch14).
- Cilium 1.20 docs: the Bandwidth Manager does not work in kind (no global `net.core` sysctls). BBR for pods needs kernel ≥ 5.18 and BPF host routing. BIG TCP needs tunnelling off. Maglev's default M is 16381.

## Layer tags

`MATH` (purple, --t1) · `CC` end-to-end congestion control (blue, --t2) · `AQM` the bottleneck queue (green, --t3) · `HOST` qdiscs, pacing, EDT, offloads, the Cilium datapath (amber, --t4) · `LB` load balancing (red, --t5)

## Connecting spine

One 100 MB upload from a Cilium pod to a service VIP over a 10 Mbit/s, 40 ms path (BDP = 50 KB ≈ 34.5 × 1448 B).

| Ch | What happens to the upload |
|---|---|
| 01 | Slow start and AIMD grow its cwnd; the ack clock spaces it; a loss halves it |
| 02 | Little's law turns its bottleneck queue into delay; Mathis predicts its loss-driven rate |
| 03 | CoDel drains the standing queue it builds at the bottleneck |
| 04 | HTB holds its tenant to a rate; DRR shares that rate among flows |
| 05 | TSQ caps its bytes in the host qdisc; TSO autosizing sizes its skbs; fq paces it |
| 06 | Pacing alone, under loss-driven control, would hide its loss signal |
| 07 | Carousel replaces its shaping queue with a timing wheel |
| 08 | TCP writes its departure time into skb->tstamp; fq honours it |
| 09 | A find-first-set bitmap finds its next packet among many flows |
| 10 | BBR models its path (BtlBw 10 Mbit/s, RTprop 40 ms) and paces by gain |
| 11 | A shallow buffer or a CUBIC neighbour breaks that model |
| 12 | Cilium's BPF stamps it per pod; the stamp survives the veth hop (mono delivery time) |
| 13 | Entering the cluster at a LoadBalancer VIP, Maglev hashes its 5-tuple to one backend and conntrack keeps it there; from a pod, Cilium's socket LB picks the backend once at connect() with a random slot (`bpf/bpf_sock.c:124–128, 408`; docs: "Maglev hashing is applied only to external (N-S) traffic") |
| 14 | Across the 10 Mbit/s bottleneck GRO gets one 1,514-byte frame per poll, so BIG TCP changes nothing for this upload; between pods on a fast link GRO hands the receiver 184 KB skbs (measured on a veth pair: 55.8 → 69.1 Gbit/s, −30% CPU per GB) |

Payoff sentence (to place in the capstone): the upload's speed is set by a model of the path that BBR keeps. That speed is enforced by a departure time that TCP or Cilium's BPF writes into each skb and fq honours. So the bottleneck queue stays near empty while the pipe stays full, which is the operating point the queueing maths calls optimal.

## Chapter status

| chapter | built | pre-read probe | lock-in | open edges |
|---|---|---|---|---|
| ch01 Congestion avoidance and control | 2026-10-02 (5 · 23 min) | | | |
| ch02 Queues in numbers | built (7 · 22 min) | | | |
| ch03 Controlling queue delay | built (6 · 23 min) | | | |
| ch04 Shapers and fair schedulers | built (5 · 22 min) | | | |
| ch05 Small queues on the host | built (6 · 23 min) | | | |
| ch06 TCP pacing | built (6 · 22 min) | | | |
| ch07 Carousel | built (6 · 22 min) | | | |
| ch08 Teaching NICs about time | built (6 · 22 min) | | | |
| ch09 Eiffel | built (7 · 22 min) | | | |
| ch10 BBR | built (6 · 23 min) | | | |
| ch11 Where BBR loses | built (6 · 22 min) | | | |
| ch12 Pods with a speed limit | built (7 · 22 min) | | | |
| ch13 Maglev | built (6 · 22 min) | | | |
| ch14 BIG TCP | built (6 · 22 min) | | | |
| capstone One upload from a pod | built 2026-10-02 (~13 min) | | | |

## Systems index

| system | full card | back cards |
|---|---|---|
| linux-tcp (Linux TCP via ss -ti) | ch01 | ch02, ch05, ch06, ch08, ch10, ch14 |
| netem (network emulator) | ch02 | ch06, ch11 |
| fq-codel (qdisc layer, fq_codel, mac80211) | ch03 | |
| htb (HTB and TBF via tc classes) | ch04 | ch07 |
| sch-fq (fair queue and pacing qdisc) | ch05 | ch06, ch07, ch08, ch09, ch10, ch12 |
| bpftrace | ch05 | |
| linux-timer-wheel (kernel/time/timer.c) | ch07 (new slug) | |
| so-txtime (SO_TXTIME and ETF) | ch08 | ch12 |
| linux-bpf-qdisc (Qdisc_ops in BPF, v6.16) | ch09 (new slug) | |
| tcp-bbr (Linux tcp_bbr via ss -ti) | ch10 | ch11, ch12 |
| cilium-bwm (Bandwidth Manager, EDT in BPF, BBR for pods) | ch12 | |
| cilium-maglev (Maglev in kube-proxy replacement) | ch13 | |
| linux-gso (GSO/GRO size knobs, BIG TCP) | ch14 | |

## Bench

- Rootless: `unshare -Urn` gives a user namespace that owns its own netns. veth, `ip link set … netns <pid>`, netem, tbf, htb, fq and codel all work without sudo (tested 2026-10-02). Shared helpers live in `labs/common/` and build everything from scratch, so no lab depends on another lab's state.
- Needs the user's sudo:
  - `modprobe tcp_bbr` (not loaded; the setsockopt fails with ENOENT).
  - bpftrace.
  - tc BPF program loading (`kernel.unprivileged_bpf_disabled = 2`).
- Missing tools, which the user installs if wanted: iperf3, netperf, flent, tshark, ipvsadm. Present: tc and ss (iproute2 7.2.0), bpftrace, pwru, tcpdump, ethtool, nstat, clang, bpftool, python3 (numpy 2.5, scipy 1.18, matplotlib 3.11), gnuplot, docker, kind, kubectl, cilium.
- Commands in pages must be fish-safe: no bare `VAR=value`, `for … end` loops, `$HOME` in `VAR=` prefixes.
- Wi-Fi: `wlan0` (mt7921e) shows `qdisc noqueue`, because mac80211 runs its own fq_codel (target 20 ms, interval 100 ms, ECN on; `net/mac80211/tx.c:1618-1621`).
- Wave 1 lessons (2026-10-02):
  - netem as the root qdisc on the **sender's own** egress (qnet's default on `s0`) orphans each skb at enqueue, so TSQ never sees the queue and nothing paces: the sender queue grew to 14.9 MB and RTT to 8 s (ch05). For sender-side TSQ, fq, pacing or departure-time work, put fq (or tbf) on `s0` and move its 20 ms to the ack path: `tc -n rcv qdisc del dev c0 root` then `tc -n rcv qdisc add dev c0 root netem delay 40ms limit 100000`. The bottleneck on `r1` stays qnet's.
  - netem's `limit` counts packets in its delay line (`sch_netem.c:552`), so `netem delay 20ms rate 10mbit limit 50` on `r1` has room for only about 33 queued packets at 10 Mbit/s (ch06 found this; ch05 lab 3 uses that form and is noted).
  - qnet's root on `r1` is netem with handle 1:, so `qdisc replace … root handle 1: tbf` fails ("must match existing qdisc"). Delete the root first (ch03).
  - `tc qdisc replace` on an existing netem keeps the parameters you did not name (rate stays); delete and add (ch05).
  - `tc qdisc change … tbf` resets a pfifo child's limit to tbf's byte limit counted as packets (`sch_tbf.c:443–444`); re-set the child after any change (ch03).
  - netem with a child qdisc keeps packets in its own tfifo, so it cannot host codel; ch03 uses tbf as "a plain rate limiter".
  - TCP falls back to its internal pacing timer when `SO_MAX_PACING_RATE` is set and no fq is present, so pfifo and fq spaced packets the same under a cap (ch05).

## Chapter inventories

Full inventories: `notes/inventory/inv-NN.md`. The condensed per-chapter inventory and strands go here as each chapter is built.

### ch01 — Congestion avoidance and control (built 2026-10-02)
- Read in full from the PDF (text plus rendered pp. 159, 160, 166, 169). Printed = PDF + 156; the original SIGCOMM pages are 314–329 (Crossref), and the kernel's "p. 328" is reprint p. 172.
- Spine: the csam–cartan 230.4 kbit/s link with a 50-packet queue (Fig. 7, p. 166). The bench copy is qnet.sh defaults (10 Mbit/s, 20 ms each way, limit 50).
- Strands: ack-clock, slowstart-cost, rto-needs-variance, loss-is-the-signal, aimd, window-minus-pipe-queue. The approved mini-plan merged md-because-geometric and ai-not-mi into aimd.
- Measured on the bench (rootless, kernel 7.2.6), data in labs/ch01-aimd/data/:
  - Reno: cwnd 42–85; peak 83 = pipe 33 + queue 50; period 3.4 s; queue never below 8; slow start overshot to 166 with 86 retransmissions; 9.54 Mbit/s goodput.
  - Black hole 5–13 s: RTO 530 → 1060 → 2120 → 4240 → 8480 ms; first successful retransmission at 13.45 s, against path back at 13.02 s.
  - With offloads on, the queue held 224 KB in 50 "packets" and cwnd peaked at 131.
- Decision: plot 2 is an analytic model. A synthetic-sample version showed A+2D late more often than 2R, which is true for exponential noise and confusing as a figure. The model gives 2R late = e^(-2-b/m), A+kD late = e^(-(1+2k/e)). Derivation in a toggle.
- Erratum shipped: p.169 mdev ≥ sdev and the √(π/2) factor are inverted (verified on the rendered page).
- Budget: after half 4,657 words (~23 min, over the 20-min default and inside the 25% tolerance), stated honestly.
- Mermaid: all three blocks parse with mmdc 11.17.0 (found in the npx cache; nothing installed). Headless Chrome render checked: KaTeX, both plots, zoom bars.

## Budget
```json budget
{"before": 10, "after": 20}
```

## Terms
```json terms
{
"congestion collapse": "ch01",
"conservation of packets": "ch01",
"bottleneck": "ch01",
"ack clock": "ch01",
"congestion window": "ch01",
"cwnd": "ch01",
"slow start": "ch01",
"ssthresh": "ch01",
"retransmit timeout": "ch01",
"mean deviation": "ch01",
"exponential backoff": "ch01",
"congestion avoidance": "ch01",
"aimd": "ch01",
"pipe size": "ch01",
"bandwidth-delay product": "ch01",
"bdp": "ch01",
"little's law": "ch02",
"m/m/1": "ch02",
"m/d/1": "ch02",
"utilisation": "ch02",
"utilization": "ch02",
"pollaczek": "ch02",
"kleinrock's power": "ch02",
"bufferbloat": "ch03",
"standing queue": "ch03",
"sojourn time": "ch03",
"codel": "ch03",
"fq_codel": "ch03",
"active queue management": "ch03",
"token bucket": "ch04",
"htb": "ch04",
"deficit round robin": "ch04",
"max-min fairness": "ch04",
"tcp small queues": "ch05",
"tsq": "ch05",
"pacing": "ch05",
"tso autosizing": "ch05",
"sch_fq": "ch05",
"timing wheel": "ch07",
"carousel": "ch07",
"earliest departure time": "ch08",
"edt": "ch08",
"so_txtime": "ch08",
"find first set": "ch09",
"pifo": "ch09",
"eiffel": "ch09",
"bbr": "ch10",
"btlbw": "ch10",
"rtprop": "ch10",
"pacing_gain": "ch10",
"bandwidth manager": "ch12",
"eyeq": "ch12",
"tstamp_type": "ch12",
"mono delivery time": "ch12",
"maglev": "ch13",
"consistent hashing": "ch13",
"big tcp": "ch14",
"jumbogram": "ch14",
"operating point": "ch02",
"poisson arrivals": "ch02",
"mathis formula": "ch02",
"buffer-sizing rule": "ch02",
"jain's fairness index": "ch02",
"random early detection": "ch03",
"good queue": "ch03",
"bad queue": "ch03",
"control law": "ch03",
"flow queueing": "ch03",
"arrival curve": "ch04",
"work-conserving": "ch04",
"generalized processor sharing": "ch04",
"pacing rate": "ch05",
"fq flow": "ch05",
"new and old lists": "ch05",
"throttled tree": "ch05",
"byte queue limits": "ch05",
"bql": "ch05",
"slow-start burst": "ch06",
"ack compression": "ch06",
"paced reno": "ch06",
"late congestion signal": "ch06",
"mixing of flows": "ch06",
"congestion epoch": "ch06",
"synchronized drops": "ch06",
"desynchronization": "ch06",
"traffic shaping": "ch07",
"flow aggregate": "ch07",
"earliest release time": "ch07",
"slot granularity": "ch07",
"horizon": "ch07",
"calendar queue": "ch07",
"deferred completion": "ch07",
"backpressure": "ch07",
"head-of-line blocking": "ch07",
"afap": "ch08",
"as fast as possible": "ch08",
"skb->tstamp": "ch08",
"clock_tai": "ch08",
"etf": "ch08",
"earliest txtime first": "ch08",
"integer priority queue": "ch09",
"bucketed queue": "ch09",
"hierarchical ffs": "ch09",
"cffs": "ch09",
"gradient queue": "ch09",
"single shaper": "ch09",
"bottleneck bandwidth": "ch10",
"round-trip propagation time": "ch10",
"inflight": "ch10",
"rate balance": "ch10",
"delivery rate": "ch10",
"app-limited": "ch10",
"application-limited": "ch10",
"windowed filter": "ch10",
"windowed max": "ch10",
"windowed min": "ch10",
"pacing gain": "ch10",
"cwnd gain": "ch10",
"cwnd_gain": "ch10",
"probebw": "ch10",
"probertt": "ch10",
"bbr states": "ch10",
"loss cliff": "ch11",
"cliff point": "ch11",
"policer mode": "ch11",
"inflight cap": "ch11",
"in-flight cap": "ch11",
"goodput gain": "ch11",
"gpgain": "ch11",
"probe time": "ch11",
"bbrv3": "ch11",
"tenant": "ch12",
"hose model": "ch12",
"admissible traffic": "ch12",
"rcp": "ch12",
"rate control protocol": "ch12",
"edt rate limiter": "ch12",
"bbr for pods": "ch12",
"maglev lookup table": "ch13",
"virtual ip": "ch13",
"equal-cost multipath": "ch13",
"generic routing encapsulation": "ch13",
"direct server return": "ch13",
"connection tracking table": "ch13",
"offset and skip": "ch13",
"minimal disruption": "ch13",
"overprovision factor": "ch13",
"gso max size": "ch14",
"gro max size": "ch14",
"hop-by-hop header": "ch14",
"max_skb_frags": "ch14",
"packet budget": "ch14"
}
```

## Decisions log

- 2026-10-02: Paper 10 gets its own chapter, paired with Ware et al. (the user approved; the inventory agent had suggested a merge).
- 2026-10-02: EyeQ (09e) is merged with mono delivery time (11) as chapter 12, "Pods with a speed limit".
- 2026-10-02: Eiffel keeps its own chapter with a fenced reading guide (pp. 18–19, 21–22, 24, 26, 28).
- 2026-10-02: Added chapter 2 (queueing maths) and the DRR paper in chapter 4, Ware in chapter 11; Chiu–Jain, Kleinrock, Varghese–Lauck and the BBR draft are go-deeper references.
- 2026-10-02: Inline maths in prose is always KaTeX (user request after chapter 1). `notes/katexify.py` converts plain-text maths outside protected regions.
- 2026-10-02: KaTeX 0.19 via jsDelivr (`\( \)` and `\[ \]` only, never `$`). It's a second CDN beyond Mermaid's, a deviation from the spec, recorded here.
- 2026-10-02: Zoom bar on every figure (`.mermaid` or `.plot` holder), plus a full-screen view. The audit checks that every `figure.dia` starts with a holder.
- 2026-10-02: Curves are inline SVG in `<div class="plot">`, generated by Python scripts in `notes/plots/`. Structure stays in Mermaid.
- 2026-10-02: Page references: printed pages for papers; PDF pages for the pacing paper (none printed); section names, slide numbers or message names for man pages, LWN, slides and cover letters. The audit accepts `p.`, `§` or `slide N`.
- 2026-10-02: Chapters 2–14 are built by parallel subagents in three waves (2–5, 6–9, 10–14) from `notes/BUILD-BRIEF.md`; each writes `notes/chapters/chNN.md` with its terms JSON, which `audit.py` merges. The coordinator integrates the hub, glossary and NOTES after each wave.
- 2026-10-02: "tbf" is not a reserved term, so lab commands before the shapers chapter may use `tbf` as a plain rate limiter. "token bucket" stays reserved for chapter 4. "operating point" moves to chapter 2 (Kleinrock).
- 2026-10-02: Labs in chapters 1–3 use netem's `rate` as the bottleneck, so the word "token bucket" stays out until chapter 4.
- 2026-10-02: Wave 1 (ch02–ch05) integrated: audit 0 problems over six pages. ch01's three nested KaTeX spans (a katexify side effect) fixed; audit.py now flags nested maths and checks `../` anchors in the sibling file.
- 2026-10-02: ch04 says "customers A and B" (as the HTB user guide does), because "tenant" is the pods chapter's term. The capstone's ch04 stop follows that wording until the pods chapter.
- 2026-10-02: "shaper", "policer" and "quantum" are defined in ch04's word list but not mapped as reserved terms (ch01 says "policers", ch03 "shaper", fq_codel has a quantum parameter).
- 2026-10-02: ch05 avoids bare "horizon" (a ch07 term), using only `horizon_drops`.
- 2026-10-02: Wave 2 (ch06–ch09) integrated: audit 0 problems over ten pages; 87 glossary terms, 9 systems. Two new system slugs: linux-timer-wheel (ch07) and linux-bpf-qdisc (ch09). integrate.py keeps acronym-led titles ("TCP pacing") and takes hand-written index lines for htb and so-txtime.
- 2026-10-02: ch07 maps "earliest release time" (ch02 already says "release time" in plain prose). ch09 maps "bucketed queue", "gradient queue" and "eiffel"; ch07 never uses "bucketed queue".
- 2026-10-02: ch07's sender-side runs put only `netem delay 20ms limit 10000` on r1 (no rate) so the shaper is the only queue; the brief's ack-path recipe was also run (data/ackpath/): same memory and rates, RTT 155 ms against 137.
- 2026-10-02: fq horizon is v5.8 (39d010504e6b); ch05's "v5.7" is the watchdog timer slack (583396f4ca4d), which is right.
- 2026-10-02: ch09's chnav right was written as "The next chapter" so "BBR" never appears before chapter 10; audit.py now leaves `.chnav` out of the vocabulary scan.
- 2026-10-02: Wave 3 (ch10–ch14) launched before ch07 finished; tcp_bbr still not loaded, so ch10/ch11 builders re-check before finishing and mark BBR runs "not executed" if needed (resume them once the reader loads it).
- 2026-10-02: Wave 3 (ch10–ch14) integrated; capstone built by the coordinator. Full audit: 0 problems over 16 pages; 133 glossary terms, 13 systems.
- 2026-10-02: **Not executed, needs the reader's sudo:** every Linux BBR run in ch10 (bench.sh --cc bbr, the ss -ti line in the tcp-bbr card is illustrative and labelled) and ch11 (the two duels, the BBR loss sweep), because `tcp_bbr` was never loaded; BPF loads in ch09 (bpf_fq qdisc) and ch12 (EDT limiter); bpftrace probes in ch05. Resume the ch10 and ch11 builders after `sudo modprobe tcp_bbr`: their notes hold resume checklists and the plots pick up data automatically.
- 2026-10-02: Spine corrections from builders, verified in code: ch13 (a pod's connection to a service is balanced by the socket LB at connect() with a random slot; Maglev is N-S only) and ch14 (GRO gets single frames behind 10 Mbit/s; BIG TCP changes nothing for the upload). The capstone states both.
- 2026-10-02: Capstone stop 12 reads `bpf/lib/edt.h:88–106`: the limiter starts from the stamp TCP wrote, \(\max(\text{stamp}, \text{now})\), sends at max(t, t_last + wire_len/rate), drops beyond the 2 s horizon (`pkg/maps/bwmap/bwmap.go:28`).
- 2026-10-02: ch11 does not map "shallow buffer"/"deep buffer" (ch01 uses them); ch13 adds "overprovision factor"; ch12 owns "tenant" and "EyeQ".
