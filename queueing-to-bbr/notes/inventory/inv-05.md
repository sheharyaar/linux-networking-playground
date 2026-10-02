# Inventory 05: Aggarwal, Savage, Anderson, "Understanding the Performance of TCP Pacing" (INFOCOM 2000)

Source PDF: /home/wazir/Documents/Books/networking/routing-papers-bbr/05-tcp-pacing.pdf
Text: /tmp/qbbr/05-tcp-pacing.txt (layout), /tmp/qbbr/05-tcp-pacing.raw.txt

## 1. Facts

- **Citation:** Amit Aggarwal, Stefan Savage, Thomas Anderson. "Understanding the Performance of TCP Pacing." In *Proc. IEEE INFOCOM 2000*, Tel Aviv, March 2000, vol. 3, pp. 1157–1165. The venue, volume and page range are **not printed in this PDF**. They come from the standard bibliographic citation and I could not check them here. The DOI usually given is 10.1109/INFCOM.2000.832483 (unverified).
- **PDF:** 9 pages, US Letter, two-column. PDF metadata says "paper.dvi" (dvips, Acrobat Distiller 3.02), created 23 Nov 1999. It is the authors' camera-ready/preprint copy, not the IEEE-paginated version.
- **Printed page numbers:** **none.** I rendered all 9 pages and none has a folio, running header, or footer.
- **Printed range:** none in the PDF. If the proceedings citation is right (1157–1165, 9 pages), the offset would be printed = PDF + 1156. That mapping is **assumed, not verified**. Every page reference below is a **PDF page (p1–p9)**.
- **Offset check:** done by rendering. p1 (title, abstract, §I) and p9 (references 3–32 only) carry no numbers, so the only safe locator is the PDF page.

## 2. Sections (PDF pages)

| Section | PDF pages |
|---|---|
| Abstract, I. Introduction | p1 |
| II. Related Work | p1–p2 |
| III. Background | p2–p3 |
| III.A TCP Mechanisms (ack-clocking, slow start, CA, delayed ACK) | p2 |
| III.B Burstiness in TCP: B.1 Slow Start (p2), B.2 Losses (p2–p3), B.3 Ack Compression (p3), B.4 Multiplexing (p3) | p2–p3 |
| IV. Pacing (sender vs receiver pacing; hybrid of window and rate) | p3 |
| IV.A Implementation (ns, leaky bucket, timer every RTT/window) | p3 |
| IV.B Why Pacing (Should) Help (Fig. 1 queueing argument) | p3–p4 |
| V. Simulation Setup and Methodology (topology, MSS 576, Jain index, normalized fairness) | p4 |
| VI. Results (overview) | p4 |
| VI.A Single Flow (Figs 3–5, footnote 1 T_cycle) | p4–p5 |
| VI.B Multiple Flows: B.1 Synchronization Effect (p5–p6), B.2 De-synchronization Effect (p6) | p5–p6 |
| VI.C Multiple Flows – Variable RTT (Figs 9–11) | p6–p7 |
| VI.D Variable Length Flows (ideal latency, four phases; Figs 12–13) | p6–p7 |
| VI.E Interaction of Paced and non-Paced Flows (Figs 14–15) | p7–p8 |
| VI.F Effect of Queueing Discipline (RED, BLUE; Fig. 16) | p8 |
| VII. Conclusions | p8 |
| References [1]–[32] | p8–p9 |

Figure locations: Fig. 1 p3; Figs 2–4 p4; Figs 5–7 p5; Figs 8–10 p6; Figs 11–13 p7; Figs 14–16 p8.

## 3. Terms introduced

1. **ack-clocking**: the sender waits for returning ACKs to time new transmissions, so the bottleneck's spacing is copied back onto the sender. Explained p2 (III.A); cites Jacobson [16].
2. **time unit**: the time to serialize one segment on the bottleneck, 1 time unit = TCP packet size / b. Defined p2 (III.B).
3. **delay-bandwidth product**: RTT × bottleneck bandwidth, the window at which the pipe is exactly full. Named p2 (III.B.1).
4. **slow-start burst (2× rate)**: each ACK releases two packets, so slow start transmits at twice the bottleneck rate and builds a queue. p2 (III.B.1).
5. **post-recovery burst**: the ACK of a retransmission fills a sequence hole and releases a window's worth of data at once. p2–p3 (III.B.2).
6. **ack compression**: on two-way traffic, ACKs queue behind data on the reverse path, lose their spacing, and arrive in a clump. p3 (III.B.3); cites [32].
7. **multiplexing clusters**: on a fast shared link each flow's window stays a tight cluster and the flow is idle for the rest of the RTT. Clusters that overlap form bigger bursts. p3 (III.B.4).
8. **pacing (sender-based)**: spread a window evenly across one RTT at rate window/RTT. The window decides *how much* to send and the rate decides *when*. Receiver-based pacing is rejected. p3 (IV).
9. **Paced Reno**: ns-2 Reno plus a per-packet timer firing every RTT/window, with a separate EWMA RTT from timestamps. Pacing applies for the whole connection. p3 (IV.A) and p4 (V).
10. **Jain's fairness index**: f = (Σxᵢ)² / (n·Σxᵢ²). It is 1 for equal shares and falls to 1/n when one flow takes everything. p4 (V).
11. **normalized fairness ratio**: Jain's index computed on xᵢ·RTTᵢ, because the fair share is taken as ∝ 1/RTT. p4 (V).
12. **synchronized drops / synchronization effect**: all flows lose packets in the same RTT and back off together, leaving the link oversubscribed then undersubscribed. Introduced p1 (§I), analysed p5–p6 (VI.B.1).
13. **late congestion signals**: paced traffic keeps the queue near zero until the link saturates, so the first loss arrives only after the network is already overloaded. p5–p6 (VI.B.1 item 1).
14. **mixing of flows**: paced packets from all flows interleave, so an overflow interval hits every flow, whereas bursty clusters hit only some. p6 (VI.B.1 item 2).
15. **de-synchronization effect**: in steady state, pacing randomizes which flows lose, which staggers their sawtooths and slightly raises utilization. p6 (VI.B.2).
16. **ideal latency / normalized latency**: ideal latency is a flow that slow-starts to its fair share and then holds a constant window. Normalized latency = actual / ideal. p7 (VI.D).

## 4. Core claims

1. Queueing theory says bursty arrivals give more delay, more loss, and lower throughput. Pacing should therefore help both the individual flow and the network (p1; formalized in Fig. 1, p3).
2. During slow start a window of W packets builds a queue of W/2 at the bottleneck. With a small buffer, Reno takes its first loss early at W ≈ 2× buffer, while paced Reno loses only after filling the pipe (p2, restated p5).
3. One flow with buffer ≈ BDP/4: pacing wins clearly during startup because Reno leaves slow start early and then crawls in congestion avoidance. In steady state both show the same sawtooth and the same throughput (p4–p5, Figs 3–4).
4. Pacing's single-flow gain grows with BDP when buffers are small, vanishes once buffer ≥ BDP/2, and turns slightly negative because pacing "lags behind by a round trip time" (p5, Fig. 5).
5. Fifty flows starting together at 57 Mbps / 100 ms with a 312-packet buffer: Reno beats pacing in the initial period, because paced flows overflow the buffer together and all back off together (p5–p6, Figs 6–8).
6. Two things cause this synchronization. The congestion signal arrives late, because pacing keeps the queue empty until saturation. And pacing mixes the flows, so every flow has a packet in the overflow (p5–p6).
7. In steady state pacing de-synchronizes losses. Throughput is slightly higher, short-term fairness is lower, and long-term fairness is about the same (p6, Fig. 8).
8. With mixed RTTs (100 ms and 280 ms), pacing gives much better RTT-normalized fairness and a lower drop rate at similar throughput (p6–p7, Figs 9–11).
9. With realistic arrivals (20 sources, think time ~ Exp(1 s)), paced flows suffer regular synchronized drops whenever new flows slow-start in (phase 3). This holds even with a buffer equal to BDP (p7, Figs 12–13).
10. Paced flows mixed with Reno flows get worse latency. A paced flow spreads its packets across the RTT, so it is more likely to have at least one packet hit a Reno burst (p1 §I; p7–p8, Figs 14–15). Probabilistic AQM (RED with a low min_th, high max_th and low max_p, or a utilization trigger like BLUE) reduces both problems, because "with pacing even a small queue size should be interpreted as congestion" (p8, Fig. 16).

## 5. Figures and examples worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| 1 | p3 | Response time vs load. Worst case (batch arrivals) rises linearly from load 1. Best case (perfect spacing) stays flat until load N (capacity), then rises. Random traffic lies between. | The whole intuition for pacing. Redraw it, then annotate the paper's twist: the flat part of "best case" is exactly where a loss-based sender gets **no signal**. It is also BBR's operating point (Kleinrock's knee). |
| 2 | p4 | Dumbbell: S_i to BS at 4x Mbps/5 ms, BS to BR bottleneck at x Mbps/40 ms, BR to R_i at 4x/5 ms. | Reusable netns topology. RTT = 2(5+40+5) = 100 ms. |
| 3, 4 | p4 | One flow, 5 Mbps, 100 ms, BDP 108 pkts, buffer 25 pkts. Fig. 3 is cumulative throughput; Fig. 4 is cwnd vs time. | Pen-and-paper target. Values below are read from a 200-dpi crop of Fig. 4, so they are approximate. **Reno:** slow start peaks ≈62 (2B = 50 plus overshoot), the window collapses to ≈1 (a timeout after a multi-loss burst), then a linear CA ramp of ≈130 RTTs reaches ≈135. **Paced:** slow start overshoots to ≈213 (one RTT of feedback delay past BDP+B = 133), resumes at ≈77, and reaches the sawtooth by ≈90 RTT. **Steady state (both):** peak ≈135 = BDP+B, trough ≈67, period ≈75 RTTs. Fig. 3's slow convergence (~1000+ RTTs) comes from the cumulative-average metric. |
| 5 | p5 | Throughput difference (paced − Reno) vs BDP, one line per buffer/BDP ratio (0.1, 0.25, 0.5, 1.0, 2.0). | Shows when pacing helps: large BDP and small buffer. Ties directly to buffer-sizing arithmetic. |
| 8 | p6 | Aggregate window of 50 flows vs time. Paced spikes to ≈3300 then collapses to ≈200. Reno peaks ≈2400. Afterwards paced oscillates higher. (Values read off the plot, approximate.) | **The canonical picture of synchronization.** Use it as the chapter spine. |
| 12 | p7 | Normalized latency vs flow size (10–100k pkts), buffer 0.25 BDP, with four labelled phases. | Shows that the effect depends on workload, not only topology. Phase 3 (~1k–10k pkts) is where pacing hurts most (paced peak ≈2.4). |
| 14, 15 | p8 | Latency when a fraction of the flows is paced. The Reno/Paced latency ratio is < 1 for most mixes. In line B (5000-pkt flows) the ratio is ≈0.27 at 10% paced and rises above 1 only past ~80% paced. | The incentive problem: early adopters of pacing lose. |
| 16 | p8 | Normalized latency with RED variants vs drop-tail. | The paper's remedy. Maps to sch_red, sch_sfb, and CoDel. |

## 6. Maths

| Item | Page | Background | Reproduce? |
|---|---|---|---|
| 1 time unit = packet size / b | p2 | none | yes. At 5 Mbps and 576 B it is 0.92 ms. The pacing interval RTT/W at W = BDP equals exactly one time unit. |
| **Slow-start queue = W/2.** At window W/2 the sender receives W/2 ACKs spaced 1 unit apart and sends 2 packets per ACK: W packets in W/2 units. The bottleneck drains only W/2 in that time, so W/2 queue. Corollary: the first loss comes at W ≈ 2B (p5) unless BDP is smaller. | p2 (p5) | ack-clocking | **yes, the key derivation** |
| Delayed ACKs: slow-start growth 2× becomes 1.5× per RTT, and CA growth 1 becomes 0.5 pkt per RTT | p2 | delayed ACK | yes (one line) |
| Pacing interval = RTT/window; rate = window/RTT | p3 | none | yes |
| Fig. 1 delay bounds (qualitative, cites Kleinrock [19]) | p3 | M/D/1 vs batch-arrival intuition | sketch only |
| Jain index f = (Σxᵢ)²/(n Σxᵢ²) | p4 | none | yes. Check [1,1,1,1] gives 1 and [4,0,0,0] gives 0.25. |
| Normalized fairness f = (Σ xᵢ·RTTᵢ)² / (n·Σ(xᵢ·RTTᵢ)²) | p4 | fair share ∝ 1/RTT | yes |
| Footnote 1: T_cycle = RTT²·BW/packet_size (from Mathis et al. [21]) | p5 | AIMD sawtooth | **yes, and critique it.** With Fig. 3/4 numbers it gives 0.01·5e6/4608 ≈ 10.9 s ≈ 108 RTTs. A W/2→W sawtooth with W_max = BDP+B = 133 gives W_max/2 ≈ 67 base RTTs; queueing stretches the RTT by up to 23 ms, which brings this toward the ≈75 RTTs observed in Fig. 4. The footnote is the period for W_max = 2·BDP and drops the ½ that applies when W_max ≈ BDP. *(This is my derivation, not the paper's.)* |
| Fair-share BDP: 57 Mbps × 100 ms / 576 B ≈ 1237 pkts (the paper says 1250), about 25 per flow over 50 flows; buffer 312 = ¼·1250 | p5 | BDP | yes |
| Implicit overshoot: Fig. 8's paced peak ≈ 3300 ≈ 2·(BDP+B) = 2·1562. Slow start keeps doubling for one RTT after the buffer overflows, until the loss is detected. | p6 (figure) | slow start | **yes, good derived exercise** *(my reading of the figure)* |
| Implicit probability argument (§I p1, VI.E p7). A paced flow with k packets spread over the RTT, facing a congested fraction q of the RTT, gets P(≥1 loss) ≈ 1−(1−q)^k. A clustered flow gets ≈ q. AIMD reacts to loss *events*, not counts. | p1, p7 | Bernoulli | yes. The paper argues this in words. The formalization is mine. |
| Ideal latency (slow start to fair share, then constant window) | p7 | slow-start arithmetic | optional |

Background assumed: Reno AIMD and slow-start arithmetic, BDP, basic queueing intuition (no formulas from Kleinrock are used). There is no control theory and no stochastic model beyond the words.

## 7. Numbers worth reusing

- MSS = **576 B** (4608 bits); ACK every packet; delayed ACK disabled (p3–p4).
- Topology: side links 4× bottleneck at 5 ms; bottleneck 40 ms; **RTT 100 ms**. The 280-ms flows get extra side-link delay (p4, p6).
- Single flow: **5 Mbps, BDP 108 pkts, buffer 25 pkts** (≈BDP/4). Time unit 0.92 ms (p4).
- 50 flows: **57 Mbps, BDP ≈1250 pkts, buffer 312**, fair share ≈25 pkts/flow (p5).
- 50 flows, 20 Mbps, buffer 312, RTT 100 vs 280 ms (BDP ≈ 434 vs 1215 pkts by my arithmetic) (p6).
- 20 sources, **25 Mbps, 100 ms** (BDP ≈ 542 pkts), buffer 0.25 or 1.0 BDP, think time Exp(mean 1 s), flow sizes 10–100,000 pkts (p6–p7).
- Mixed experiment: 20 flows of **300 packets** (≈173 KB at 576 B), also 5000 packets (p7–p8).
- RED settings (Fig. 16 legend, p8): (min_th = 0.25·B, max_th = 0.5·B, max_p = 0.1) and (min_th = 5, max_th = 0.9·B, max_p = 0.02). The second one works best.
- Single flow: Reno's first loss at W ≈ 2B = 50. Paced near BDP + B ≈ 133 (p5 statement plus arithmetic).
- Values read from Fig. 4 (approximate): Reno slow-start peak ≈62; paced peak ≈213; sawtooth 67↔135; period ≈75 RTTs.
- Values read from Fig. 8 (approximate): paced peak ≈3300 at ~8 RTT, trough ≈200 at ~14 RTT; Reno peak ≈2400, trough ≈500–700; steady-state peaks ≈1600 ≈ BDP + B = 1562.

## 8. Linux mapping (kernel v7.2, ~/workspace/repos/linux, `git describe` = v7.2; all lines grepped)

The paper's per-packet "timer fires every RTT/window" became, in Linux, a **rate** (`sk_pacing_rate`) plus an **earliest-departure timestamp** per skb. The timestamp is enforced either by sch_fq or by one hrtimer per socket.

**Rate computation ("window/RTT")**
- `tcp_update_pacing_rate()` in net/ipv4/tcp_input.c:1138. It computes rate = mss × max(cwnd, packets_out) / srtt × ratio (line 1159). The ratio is `tcp_pacing_ss_ratio` (200%) if cwnd < ssthresh/2 (line 1154), otherwise `tcp_pacing_ca_ratio` (120%). The result is capped by `sk_max_pacing_rate` (line 1169). Defaults are set at net/ipv4/tcp_ipv4.c:3501–3502, and both sysctls are **per-netns**. It is called from `tcp_cong_control()` (tcp_input.c:3858, call at 3875). Commit 43e122b014c9 (v4.3, 2015) introduced the 200/120 split.
  - Contrast with the paper: Linux deliberately paces **faster** than cwnd/RTT. Pacing becomes a ceiling that smooths microbursts while ACKs still clock the flow. This sidesteps the paper's "lags behind by an RTT" penalty (p5).
  - Small discrepancy: Documentation/networking/ip-sysctl.rst:1131 says the ss ratio applies "in slow start", but the code uses cwnd < ssthresh/2.
- Fields: `sk_pacing_rate` (bytes/s) at include/net/sock.h:498; `sk_pacing_status` at 506; `sk_max_pacing_rate` at 507; `sk_pacing_shift` at 527. The enum `SK_PACING_NONE/NEEDED/FQ` is at sock.h:613–615. Defaults are ~0UL and shift 10 (net/core/sock.c:3798–3800).
- `SO_MAX_PACING_RATE`: net/core/sock.c:1253. It sets SK_PACING_NEEDED at 1264–1266.

**Who actually paces (this is the diagnosis trap)**
- `tcp_needs_internal_pacing()` at include/net/tcp.h:1614 is true only when the status is SK_PACING_NEEDED. BBR sets that (net/ipv4/tcp_bbr.c:1079), and so does SO_MAX_PACING_RATE.
- sch_fq flips a socket to SK_PACING_FQ in `fq_classify()` (net/sched/sch_fq.c:356, flip at 399–401). From then on fq enforces the timestamps and TCP's own timer stays idle.
- CUBIC/Reno under fq_codel or pfifo_fast (status NONE) is **not paced at all**. `ss -ti` still prints `pacing_rate`, because `tcp_get_info()` copies `sk_pacing_rate` unconditionally (net/ipv4/tcp.c:4210, field at 4231). So a "pacing_rate" in ss does not prove the flow is paced.

**Enforcement: EDT model (v4.20, commits d3edd06ea8ea and ab408b6dc744)**
- `__tcp_transmit_skb()` at net/ipv4/tcp_output.c:1536 sets tcp_wstamp_ns = max(tcp_wstamp_ns, now) and writes it to skb->tstamp (lines 1553–1555).
- `tcp_update_skb_after_send()` at tcp_output.c:1446–1468 advances tcp_wstamp_ns by len/sk_pacing_rate. It skips this for the first 10 segments (line 1458) and subtracts up to half the gap as jitter credit (lines 1463–1464; commit a7a2563064e9). This is the modern form of the paper's "duration of the current and subsequent intervals is suitably altered" (p3).
- Internal pacing (no fq): `tcp_pacing_check()` at tcp_output.c:2815 arms **one hrtimer per socket** (`pacing_timer`, set up at net/ipv4/tcp_timer.c:902) at tcp_wstamp_ns. The callback is `tcp_pace_kick()` (tcp_output.c:1435), which calls `tcp_tsq_handler` (1289). It is invoked from `tcp_write_xmit()` (2964; check at 3006). It dates from v4.13 (218af599fa63, 2017). The paper's "extra overhead of using a timer for each packet" (p3) is what Linux avoids: there is one timer per socket, re-armed, and with fq there is one watchdog per qdisc.
- sch_fq: `fq_dequeue()` at sch_fq.c:705 computes time_next_packet = max(skb time_to_send, f->time_next_packet) (761–762) and throttles the flow if it is in the future (764–766). Throttled flows go into the `q->delayed` rbtree (138, 222–238). `fq_check_throttled()` (664) releases them, and one qdisc watchdog hrtimer is armed at `time_next_delayed_flow` with `timer_slack` (744–747; net/sched/sch_api.c:644–667). For non-EDT skbs, fq computes spacing from sk_pacing_rate itself (798–834).

**TSO/TSQ coupling (burst size at the pacing point)**
- `tcp_tso_autosize()` at tcp_output.c:2256 sizes bursts to about 1 ms of pacing rate (pacing_rate >> sk_pacing_shift, line 2262).
- `tcp_small_queue_check()` at 2857 limits a flow to max(2·truesize, pacing_rate>>shift), capped by `tcp_limit_output_bytes` (4 MB, tcp_ipv4.c:3491). Real pacing is therefore at **TSO-burst granularity**, not per MSS as in the paper.
- The Wi-Fi laptop matters here. mac80211 sets `tx_sk_pacing_shift = 7` (~7.8 ms of data) at net/mac80211/main.c:951 and applies it in tx.c:4358.

**The paper's remedies**
- RED: net/sched/sch_red.c (`red_enqueue` at 70; helpers in include/net/red.h).
- BLUE: net/sched/sch_sfb.c (Stochastic Fair Blue). Its header cites the same Feng et al. TR as the paper's [9]. `sfb_enqueue` is at 282.
- Delay-based AQM and per-flow isolation, which remove the "mixing" fate-sharing: net/sched/sch_codel.c and net/sched/sch_fq_codel.c.

**BBR, which paces but is not loss-driven**
- net/ipv4/tcp_bbr.c. Pacing gain cycle at 163–168; **random starting phase** `bbr_cycle_rand = 7` at 170, used at 623, which explicitly de-synchronizes flows. `bbr_set_pacing_rate` at 287. The comment at 56–58 says BBR wants fq and otherwise falls back to internal pacing.

**Bench emulation**
- net/sched/sch_netem.c: rate at 379, `netem_enqueue` at 459.
- net/sched/sch_tbf.c: enqueue 251, dequeue 281.

**Tracing hooks (exist in the running kernel)**
- `tracepoint:tcp:tcp_probe` gives snd_cwnd, ssthresh and srtt (include/trace/events/tcp.h:367).
- `tracepoint:qdisc:qdisc_dequeue` (include/trace/events/qdisc.h:14).
- kprobes: `__tcp_transmit_skb`, `tcp_update_pacing_rate`, `tcp_pace_kick` (all present in /proc/kallsyms).

## 9. Prerequisites assumed, and forward references

**Used without definition:**
- Reno fast retransmit and fast recovery, duplicate ACKs (p2, p4)
- drop-tail FIFO
- RED and its min_th/max_th/max_p (p1, p8)
- BLUE (p8)
- the ns simulator; EWMA RTT and the TCP timestamp option (p3)
- leaky bucket (p3; cites Turner [29])
- "sawtooth", and Mathis's macroscopic model (footnote 1, p5)
- Kleinrock's queueing curves (p3)
- exponential think-time model (p7)

**Forward references inside the paper:**
- §I (p1) promises "approaches for eliminating this effect". Only VI.F (p8) delivers, with RED tuning and a pointer to BLUE.
- VI.B (p5) defers to VI.D (p6); VI.D (p7) defers to VI.F.

**Forward references for the study guide:**
- **CoDel** (inv-02): a sojourn-time signal is exactly the paper's wish that "even a small queue size should be interpreted as congestion" (p8).
- **fq_codel/sch_fq**: per-flow queues end the "mixing" lottery.
- **TSQ/fq and EDT** (Carousel, inv-06): how Linux actually paces.
- **BBR** (inv-09/10): pacing as the primary control rather than an add-on to loss-based AIMD.

## 10. References worth reading (2–4)

- **[21] Mathis, Semke, Mahdavi, Ott 1997, "The Macroscopic Behavior of the TCP Congestion Avoidance Algorithm."** Source of the sawtooth cycle in footnote 1 and of the throughput ∝ 1/(RTT·√p) law. You need it to reason about why loss events, not loss counts, set a Reno flow's rate.
- **[32] Zhang, Shenker, Clark 1991, "Observations on the Dynamics of a Congestion Control Algorithm: The Effects of Two-Way Traffic."** The origin of ack compression and of pacing-for-TCP (p1–p3). It also documents synchronization in window flow control.
- **[12] Floyd & Jacobson 1993, RED.** The remedy the paper tests (p8). Its motivation section explains global synchronization in drop-tail gateways, the same phenomenon pacing amplifies.
- (Optional) **[9] Feng et al., BLUE.** A utilization- and loss-triggered AQM, available in Linux as sch_sfb.

## 11. Suggested per-chapter spine

**Spine event:** the synchronized collapse in **Fig. 8 (PDF p6)**. Setup: 50 flows start together over a 57 Mbps, 100 ms, 312-packet drop-tail bottleneck (BDP ≈1250 pkts, buffer ≈ BDP/4). The paced aggregate window climbs to ≈3300 packets and falls to ≈200 within a couple of RTTs. Reno peaks ≈2400 and falls less far. Every strand can be asked about this one moment: why the paced curve overshoots more, why it falls together, why Reno's falls are staggered, and what a CoDel, fq_codel or BBR bottleneck would change. Use Figs 3–4 (single flow, p4) as the warm-up arithmetic object.

**Candidate strands**
1. `ss-queue-half-window`: In slow start a window of W builds a W/2 queue at the bottleneck. So unpaced Reno first loses near W ≈ 2·buffer, while paced Reno loses only near BDP + buffer (p2, p5).
2. `pacing-late-signal`: Pacing keeps the bottleneck queue near zero until the link is saturated. A loss-based sender therefore gets its first congestion signal only after it is already oversubscribed (p3–p6).
3. `mixing-synchronizes`: Through a shared drop-tail FIFO, paced flows have packets in every overflow interval, so they all lose and halve in the same RTT. Bursty flows share fate less (p5–p6, Fig. 8).
4. `loss-event-lottery`: Against bursty competitors, a paced flow is more likely to see at least one loss per RTT. AIMD reacts to loss *events*, so the paced flow backs off more often and finishes later (p1, p7–p8, Figs 14–15).
5. `where-pacing-wins`: Pacing wins for a single flow with large BDP and buffer < BDP/2, and in RTT-fairness and drop rate when RTTs differ. It loses for simultaneous slow starts and for mixed populations (p5–p7).
6. `aqm-for-paced`: For paced traffic even a small standing queue means congestion. RED with a very low min_th, high max_th and low max_p works best, which anticipates CoDel's sojourn-time signal (p8, Fig. 16).
7. `bbr-inverts-the-result` (external): BBR turns "no queue until saturation" into its operating point. Its signal is a delivery-rate plateau or a min-RTT rise, not loss, and it randomizes its probe phase (tcp_bbr.c:170, 623).

## 12. Exercise ideas

1. **Pen-and-paper: the Fig. 3/4 single flow (30 min).**
   - Derive the W/2 queue.
   - Compute BDP = 5 Mbps × 100 ms / 576 B ≈ 108 pkts.
   - Find Reno's first loss (W ≈ 2B = 50). In the ideal case (halve to 25), count CA RTTs to reach the BDP: ≈83 RTTs ≈ 8.3 s.
   - Then explain Fig. 4's real behaviour: a collapse to ≈1 and a ≈130-RTT ramp. Multiple slow-start losses without SACK force a timeout.
   - Compare paced Reno: the first loss appears near BDP+B = 133 and the window overshoots to ≈213 during the one RTT the loss signal takes to return.
   - Compute the sawtooth period two ways (the footnote vs (BDP+B)/2) and check against Fig. 4 (≈75 RTTs).
   - Then predict Fig. 8's paced overshoot ≈ 2(BDP+B) ≈ 3100, against ≈3300 observed.
   - Jain-index warm-ups.
2. **Python simulation of synchronization (45–60 min; numpy/matplotlib, no iperf3).**
   - Model N AIMD flows in discrete RTT rounds through a drop-tail buffer of B packets. Per-RTT arrival patterns are either *clustered* (each flow's window lands in a random contiguous slot) or *paced* (spread uniformly).
   - Drop packets that exceed capacity plus B within each sub-slot. Each flow halves at most once per RTT.
   - Plot aggregate window vs time and the per-RTT fraction of flows with a loss. Reproduce the qualitative shape of Fig. 8, then add a RED-like early-drop probability with a low min_th.
3. **netns bench: pacing on/off through a FIFO bottleneck (60 min, no iperf3; python sockets).**
   - Topology: three netns (snd, rtr, rcv) joined by veth pairs. Bottleneck: `tbf rate 20mbit burst 3k limit <≈BDP/4 bytes>` on rtr's egress toward rcv. RTT: `netem delay 100ms` on rcv's egress, i.e. the ACK path. Do not put netem with a small `limit` on the data path, because netem's limit counts packets still in the delay line.
   - Run 20 python TCP senders started together, each sending 300 × MSS. Use `net.ipv4.tcp_congestion_control=reno` inside the snd netns.
   - Condition A: snd egress noqueue or fq_codel, which means unpaced.
   - Condition B: `tc qdisc add dev snd0 root fq` plus `sysctl net.ipv4.tcp_pacing_ss_ratio=100 net.ipv4.tcp_pacing_ca_ratio=100` in snd. This emulates the paper's exact cwnd/RTT pacing; the sysctls are per-netns.
   - Condition C: the same as B but with the stock 200/120 ratios.
   - Condition D: replace tbf's inner qdisc with fq_codel.
   - Record flow completion times, `tc -s qdisc` drops at rtr, and cwnd traces. Get cwnd from `bpftrace -e 'tracepoint:tcp:tcp_probe { ... }'` or by sampling `ss -tin`.
   - Disable veth GSO/TSO (`ethtool -K` if present, or `ip link set dev X gso_max_size 1500`) so bursts are per-packet as in the paper.
4. **bpftrace: see EDT spacing (20–30 min).**
   - Kprobe `__tcp_transmit_skb` and print per-socket deltas of `((struct tcp_sock *)arg0)->tcp_wstamp_ns` alongside `sk_pacing_rate`.
   - Check that Δ ≈ skb->len / rate, minus the jitter credit, when fq is attached. Check that it stays flat (no pacing) under fq_codel with CUBIC.
   - This confirms the "ss pacing_rate ≠ paced" trap.

None of the exercises needs iperf3. Exercise 3 is the one that would be quicker with it, and python senders replace it.

## 13. Honest assessment

**Read closely:**
- III.B (p2–p3): the four sources of burstiness and the W/2 derivation.
- IV.B (p3–p4): Fig. 1 and the "too good" argument.
- VI.A (p4–p5): the single-flow numbers, which give the arithmetic exercise.
- VI.B.1–B.2 (p5–p6): the synchronization mechanism.
- VI.E (p7–p8): the mixed-population incentive problem.
- VI.F (p8): the AQM conclusion.

**Skim:**
- II Related Work (p1–p2) and III.A (p2): Reno basics the learner knows.
- VI.C and VI.D details (p6–p7): read the figures, skip the prose.
- The reference list.

**Outdated or limited:**
- ns-2 Reno with no SACK, MSS 576 B, delayed ACK disabled, and packet-counted drop-tail FIFO bottlenecks.
- Bandwidths of 5–57 Mbps.
- Pacing at exactly cwnd/RTT, per packet. There is no TSO, and no qdisc between the socket and the wire.

**Since the paper:**
- Linux has paced by default whenever sch_fq is the qdisc: sch_fq since v3.12 (2013), the 200/120% ratios since v4.3 (2015), internal hrtimer pacing since v4.13 (2017), EDT since v4.20 (2018); commits verified in the tree.
- Google's production measurements show pacing *reducing* retransmissions by 40% on video servers (Carousel, inv-06, printed p. 407). Those are host-limited senders on diverse Internet paths, not simultaneous slow starts through one FIFO.
- Later re-evaluations exist, such as Wei, Cao & Low, "TCP Pacing Revisited" (2006), and Ghobadi & Ganjali on pacing in datacenters (2012/13). Both report that pacing's benefit depends on flow count and buffer size. These are **unverified here; check before citing.**

**How the negative result relates to BBR**

Both of the paper's failure mechanisms need a **loss-driven window controller** behind a **shared drop-tail FIFO**:
- late signal: the sender grows until the buffer overflows;
- mixing: overflow intervals hit every flow, and every flow halves.

BBR breaks both premises:
1. Its congestion signal is model-based. Delivery rate stops increasing (`bbr_full_bw_thresh`, 25%, tcp_bbr.c:180) and min-RTT rises. These become visible exactly at the knee where pacing keeps the queue empty. What the paper treats as a bug, "no queue until saturation", is BBR's target operating point. Pacing is also what makes BBR's delivery-rate samples clean, since bursts and ACK compression would corrupt the bandwidth estimate.
2. BBRv1 does not multiplicatively decrease on loss, so synchronized losses do not cause a synchronized collapse.
3. BBR randomizes its PROBE_BW phase (tcp_bbr.c:170, 623) to avoid lock-step probing.

But the paper's lessons do not vanish:
- BBR's STARTUP (gain 2.885, tcp_bbr.c:155) still overshoots like slow start.
- PROBE_RTT is deliberately synchronized across flows.
- Paced BBRv1 against bursty loss-based CUBIC in shallow drop-tail buffers reproduces a version of the mixed-population problem, in reverse: BBR causes high loss for CUBIC (reported in later literature such as Hock et al. 2017 and Ware et al. IMC 2019; **unverified details**).
- BBRv2/v3 re-add loss/ECN response (inflight_hi), and with it partial exposure to the paper's mechanism.
- Mainline v7.2 `tcp_bbr.c` is still BBRv1 (the header and constants match the 2016 design), so v2/v3 experiments need out-of-tree code.

**One-line takeaway for the learner:** pacing hurts *loss-based AIMD at a shared FIFO*. Fix the signal (CoDel/ECN), the isolation (fq/fq_codel), or the controller (BBR), and pacing's downside mostly disappears.
