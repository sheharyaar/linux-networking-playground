# Inventory 02 — Nichols & Jacobson, "Controlling Queue Delay" (CACM, July 2012)

## 1. Facts

- **Citation:** Kathleen Nichols and Van Jacobson. "Controlling Queue Delay." *Communications of the ACM* 55(7):42–50, July 2012. doi:10.1145/2209249.2209264. A CACM "practice" article, "development led by queue.acm.org". The same text appeared in ACM Queue in 2012; `include/net/codel_impl.h:47` cites http://queue.acm.org/detail.cfm?id=2209336.
- **Title note:** the filename says "controlling-queueing-delay", but the printed title is "Controlling Queue Delay".
- **PDF page count:** 9 (pdfinfo). Born-digital InDesign PDF with a good text layer. The figures are vector graphics, so their axes extract as number soup.
- **Printed page numbers:** yes, as footer folios "42 COMMUNICATIONS OF THE ACM | JULY 2012 | VOL. 55 | NO. 7" (even pages left, odd pages right).
- **Printed range:** pp. 42–50. PDF p.2 (printed 43) is a full-page illustration. Its folio appears in the text layer but is not visible in the render.
- **Offset:** printed = PDF + 41. Checked on the rendered pages: PDF 1 → "42", PDF 3 → "44", PDF 4 → "45", PDF 6 → "47", PDF 9 → "50".
- **Missing from the article:** the CoDel pseudocode. It lives in an online appendix, "http://queue.acm.org/appendices/codel.html" (p.47). The control law is described only in words (p.46). There are no numbered sections and no mention of ECN or flow queueing (grep-confirmed).

## 2. Sections (headed, unnumbered; printed pages)

| Section | Pages |
|---|---|
| Untitled intro: bufferbloat, AQM history, RED | 42, 44 (43 = illustration) |
| Understanding Queues | 44–45 |
| Controlled Delay Management | 45–46 |
| One Code Module, No Knobs, Any Link Rate | 46–47 |
| Simulation Experiments (run-in heads: Simulator Configuration, Metrics) | 47 |
| Performance Across a Range of Static Link Rates | 47–48 |
| Performance on Dynamic Links | 48–49 |
| Dropping the Right Packets | 49 |
| Consumer Edge (with the unnumbered table "Consumer edge example") | 49 |
| Manage the Right Queue | 49–50 |
| Next Steps | 50 |
| References (22), author bios, related articles | 50 |

## 3. Terms introduced

1. **Bufferbloat**: buffers that stay full and add delay with no throughput benefit. Named on p.42; its "essence" is the standing queue (p.44).
2. **AQM (active queue management)**: the router decides when to drop or signal packets before its buffer is full. p.42.
3. **RED**: Random Early Detection, the AQM the IRTF recommended in 1998. Hard to configure and seldom deployed. p.42.
4. **BDP / pipe size**: bandwidth × delay. "Pipe size" is the BDP measured in packets. p.44.
5. **Standing queue**: the queue left over when the window exceeds the pipe size. It never dissipates however steadily the sender transmits. p.44.
6. **Good queue / bad queue**: good queue absorbs bursts and drains within about one RTT; bad queue persists for several RTTs and only adds delay. p.45.
7. **Occupancy time**: how long the buffer is non-empty. The paper rejects it as an indicator, citing the ack-per-window example in Fig 4. p.45.
8. **Ack-per-window receiver**: a receiver that sends one ACK per window, so the sender emits full-window bursts every RTT. p.45 (Fig 4).
9. **Packet sojourn time**: the time a packet spends in the queue (dequeue time − enqueue timestamp). It is independent of link rate. p.46.
10. **Local minimum queue delay**: the minimum sojourn over a sliding window. A minimum above zero means a standing queue. p.46 (credited to Jacobson's 2006 "rant on queues" [11]).
11. **Target**: the acceptable standing-queue delay, 5 ms. Defined p.46; value on p.47.
12. **Interval**: the window over which the minimum must stay above target before dropping, about a worst-case RTT, 100 ms. Defined p.46; value on p.47.
13. **Dropping state / control law**: once in the dropping state, the next drop time shrinks in inverse proportion to √(drops so far). The state is left when delay < target. p.46.
14. **Jain fairness index**: (Σxᵢ)² / (n·Σxᵢ²). Used here on per-source drop share. p.47.
15. **Concatenated / hidden queues**: the bottleneck buffer may sit in a device you can't manage, such as a cable modem. p.50 (Fig 10).

## 4. Core claims

1. A window larger than the pipe creates a standing queue that "has nothing to do with the sender's rate". Window 25 into a 20-packet pipe leaves 5 packets (±1) queued forever. This "is the essence of bufferbloat". It is not congestion, though it is almost universally misclassified as such. pp.44–45.
2. Queue *magnitude* carries no information about excess queue, because startup needs a big queue. Queue *occupancy time* carries none either, because an ack-per-window flow keeps the buffer always occupied with zero excess. p.45.
3. Good queue goes away in about one RTT and bad queue persists. The robust separator is the minimum queue over a window longer than the nominal RTT. p.45.
4. CoDel's three innovations are the *local minimum* as the measure of standing queue, a *single state variable* (how long the minimum has been above or below target) instead of a window of samples, and *packet sojourn time* instead of bytes or packets. p.46.
5. Because the minimum sojourn can only decrease at dequeue, all of CoDel's work happens at dequeue with no locks. The only enqueue-side cost is a timestamp. p.46.
6. Mechanism:
   - Drop when the queue delay has exceeded target for at least interval.
   - After that, schedule drops at intervals shrinking as 1/√count.
   - Stop when the delay falls below target.
   - Never drop with less than one MTU buffered.
   - Re-enter the dropping state "at a recent control level". p.46
7. Target = 5 ms: utilisation suffers below it and barely improves above it. Interval = 100 ms works for RTTs of 10 ms–1 s, and best for 10–300 ms. p.47.
8. On a simulated Wi-Fi-like link whose rate jumps 100 → 10 → 1 → 50 → 1 → 100 Mbps, tail drop holds up to ~10 s of queue. CoDel finds a new control point within 100 ms and moves almost the same total bytes. pp.48–49.
9. Undersized buffers are not the answer: 10-packet buffers lose about 75% of throughput. A large CoDel-managed buffer gets a 2.7 ms median delay. pp.48–49.
10. AQM only helps where the queue actually builds. Concatenated queues (a cable modem behind a home router) hide the bottleneck, and AQM is no substitute for differentiated queueing for latency-sensitive traffic. pp.49–50.

## 5. Figures and examples worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| 1 TCP connection startup | 44 | A redraw of Jacobson's 1988 Fig 1 funnel: a 25-packet back-to-back window squeezed at the bottleneck. | Links the two papers directly. **Redraw both side by side.** |
| 2 TCP connection after one RTT | 44 | Ack-clocked steady state with 5 packets still queued at the bottleneck. | **The spine picture.** The standing queue equals window − pipe. |
| 3 Queue size vs. time | 45 | A startup spike that drains in ~1 RTT, then a flat ±1 sawtooth at 5 packets. | Good queue and bad queue in one plot. **Redraw it** and annotate the min-over-interval. |
| 4 Queue vs. time, ack-per-window receiver, 20-packet window | 45 | A 20-packet sawtooth every RTT that returns to zero. | Shows why occupancy time fails: the buffer is always busy, yet there is no excess queue. **Redraw.** |
| 5 CoDel vs RED vs link bandwidth (3/10/45/100 Mbps) | 46 | Median delay and utilisation box plots. RED over-controls, with low utilisation at ≥10 Mbps. | Evidence for "no knobs". Skim. |
| 6 CoDel at low bandwidths (128 kbps–1.5 Mbps; 500 B vs 1500 B MTU) | 46 | Medians far above 5 ms at 128 kbps (≈0.07–0.15 s for 1500 B). | Shows the MTU floor: one 1500 B packet at 128 kbps takes 94 ms. Good arithmetic check. |
| 7 Wireless example (a/b/c) | 48 | Per-packet delay over 300 s as the rate steps every 50 s. Tail drop reaches ~10 s and CoDel stays tiny. Panel (c) is cumulative KB, including 10-packet-buffer curves. | **The best "why adapt" picture.** Re-plot schematically. |
| 8 CoDel and RED by RTT (10–500 ms) | 48 | 95th percentile and median delays, plus utilisation. | Shows interval = 100 ms tolerating any RTT. Skim. |
| 9 Jain fairness of drop share | 49 | CoDel ≈ 0.8–0.95 against RED ≈ 0.4. | "Dropping the right packets". Skim. |
| Table "Consumer edge example" | 49 | C vs T at 512 kbps and 1.5 Mbps, by direction: drop %, median delay, MB, fairness. | Concrete numbers for worked examples. |
| 10 Rate mismatch in a cable modem | 50 | CPE router (scheduler) → 100 Mbps–1 Gbps Ethernet → modem buffer → 2 Mbps upstream. | "Manage the right queue". Maps to BQL, Wi-Fi firmware queues, and shaping to just below the bottleneck. **Redraw** with a Linux-host analogue. |

## 6. Maths

The article has only one typeset equation. Everything else is quantitative argument in prose.

| # | Item | Page | Reproduce? |
|---|---|---|---|
| Q1 | Bottleneck squeeze: 1 ms packets go from 100 Mbps into 10 Mbps. The 2nd packet arrives 1 ms after the 1st but waits 9 ms more; the 3rd waits 18 ms. In general the k-th packet of a back-to-back burst waits (k−1)·(t_out − t_in). | 44 | **Yes.** For a 25-packet burst the last packet waits 216 ms. |
| Q2 | Pipe: 10 bottleneck packet times one way (100 ms at 10 ms spacing), so 20 packets in flight fill it. Window 25 → **standing queue = W − BDP = 5 (±1)**. | 44 | **Yes, core.** Extra delay = 5 × 10 ms = 50 ms, with zero throughput gain. |
| Q3 | Control law: "next drop time is decreased in inverse proportion to the square root of the number of drops…using the well-known relationship of drop rate to throughput to get a linear change in throughput" [12, 16]. No formula is printed. | 46 | **Yes, via the Linux form** `drop_next = t + interval/√count` (`codel_impl.h:93`). With I = 100 ms the drops fall at 0, 100, 170.7, 228.4, 278.4, 323.2, 364.0, 401.8, 437.1, 470.5 ms. Closed form: t_k ≈ 2I√k, so the drop *rate* rises **linearly in time**, r(t) ≈ t/(2I²). After 1 s of continuous above-target delay there have been ≈ 33 drops, now 17 ms apart. The "linear change in throughput" claim is **asserted, not derived**. Treat it as a derivation toggle: with Mathis X ∝ 1/(RTT√p) and one drop every δ seconds, a single Reno flow gets X ∝ δ. |
| Q4 | Min-over-interval as the statistic. min{sojourn over the last I} > target ⇔ every packet dequeued in the last I was above target. That is why one variable suffices (`first_above_time`). | 46 | **Yes.** A two-line logical argument. |
| Q5 | Target choice: utilisation drops below 5 ms and is flat above it (empirical). | 47 | State. |
| Q6 | **Jain index J = (Σxᵢ)² / (n·Σxᵢ²)**, with 1/n ≤ J ≤ 1. | 47 | Yes (easy). |
| Q7 | Serialisation checks: 1500 B at 100 Mbps "0.1 ms" (exact: 0.12 ms); 1500 B at 3 Mbps = 4 ms. | 47 | **Yes.** Extend: at 128 kbps a 1500 B packet takes 94 ms and a 500 B packet 31 ms, which explains Fig 6. |
| Q8 | Buffer = 1 BDP = 830 packets at nominal 100 Mbps (implies RTT ≈ 100 ms). At 1 Mbps that buffer means "as much as 10 seconds" of delay. | 48 | **Yes.** 830 × 12000 bit / 1 Mbps = 9.96 s. |
| Q9 | A 10-packet buffer at 1 Mbps gives a 120 ms worst case, with ~25% of the throughput of a large CoDel buffer. | 48 | **Yes.** 10 × 12000 / 1e6 = 0.12 s. |
| Q10 | CoDel buffer ~8×BDP in the sims, to show buffer size doesn't matter. | 47 | State. |

Background assumed: BDP, serialisation time, basic TCP AIMD, and the Mathis 1/√p law (cited, not stated).

A learner should reproduce **Q1, Q2, Q3 (the drop schedule and t_k ≈ 2I√k), Q4, Q7, Q8 and Q9**.

## 7. Numbers worth reusing

- **Standing-queue example (p.44):** window 25, pipe 20 (RTT = 20 packet times, e.g. 10 ms per packet and 200 ms RTT), standing queue 5 ±1.
- **Squeeze example (p.44):** 1 ms packets, 100 → 10 Mbps, waits of 9 and 18 ms.
- **Parameters:** target 5 ms; interval 100 ms; interval works for RTT 10 ms–1 s (best 10–300 ms); no drop below 1 MTU buffered (pp.46–47).
- **Simulation sweep (p.47):** 64 kbps–100 Mbps; 5 ms–1 s delay; 0–50 bulk flows; PackMime web 0–80; CBR 64 kbps in 100 B packets; buffer ~8×BDP; CUBIC (and New Reno) with SACK.
- **Low-rate runs (pp.46–47):** 128/256/512 kbps and 1.5 Mbps; MTU 500 vs 1500 B; RTT 30–100 ms. RED's median delays were 100–200 ms there.
- **Web-only traffic:** more than 10% drops needed for over 60% utilisation (p.48).
- **Dynamic link (p.48):** nominal 100 Mbps; 4 FTPs + 5 web connections; rate changes every 50 s over 300 s (100 → 10 → 1 → 50 → 1 → 100 Mbps); 830-packet buffer; tail drop up to ~10 s; CoDel re-converges within 100 ms.
- **10-packet buffers (pp.48–49):** throughput ~75% less, 120 ms worst case. Large CoDel buffer: median 2.7 ms, 75th percentile 5 ms, under 90 ms for 95% of the time.
- **RTT sweep:** 10–500 ms (p.49).
- **Consumer edge table (p.49):** symmetric 512 kbps and 1.5 Mbps links. The text says "512KB and 1.5MB", a typo for kbps/Mbps.

  | Link | Direction | Median delay C / T (ms) | Drop % C / T |
  |---|---|---|---|
  | 512 kbps | download | 18 / 73 | 8 / 8 |
  | 512 kbps | upload | 9 / 37 | 1.5 / 5.8 |
  | 1.5 Mbps | download | 8 / 49 | 3.5 / 4.7 |

- **Cable modem (p.50):** upstream typically 2 Mbps, Ethernet from the home side 100 Mbps–1 Gbps.
- **Linux defaults (v7.2):**

  | Setting | Value | Source |
  |---|---|---|
  | codel limit | 1000 packets | `sch_codel.c:26` |
  | fq_codel limit | 10240 packets | `sch_fq_codel.c:515` |
  | fq_codel flows | 1024 | `sch_fq_codel.c:516` |
  | fq_codel memory_limit | 32 MB | `sch_fq_codel.c:517` |
  | fq_codel quantum / CoDel mtu | `psched_mtu()` = MTU + L2 header = 1514 on Ethernet | `sch_fq_codel.c:519`, `include/net/pkt_sched.h:131-133` |
  | mac80211 CoDel | target 20 ms, interval 100 ms, ECN on | `net/mac80211/tx.c:1618-1621` |
  | CoDel clock | 1024 ns units (`CODEL_SHIFT` 10) | `include/net/codel.h:60-63` |

- **This host (observed 2026-10-02):** `net.core.default_qdisc = fq_codel`, `tcp_congestion_control = cubic`, `wlan0` (mt7921e) shows `qdisc noqueue`. The kernel's built-in default is pfifo_fast (`net/sched/sch_generic.c:37`), so fq_codel comes from a sysctl, most likely systemd's.
- **Worked-example seeds:**
  - 10 Mbps bottleneck, 1514 B frames: 1.21 ms per packet. 5 ms target ≈ 4 packets. A 1000-packet pfifo ≈ 1.21 s of queue. BDP at 40 ms ≈ 34.5 packets.

## 8. Linux mapping (v7.2 tree, grep-verified)

**Core algorithm: `include/net/codel_impl.h`**

The header comment (:44-49) names the source as Nichols & Jacobson and the Linux implementers as Dave Taht and Eric Dumazet.

- `:54-62` `codel_params_init()`: interval = MS2TIME(100), target = MS2TIME(5), ECN off, ce_threshold disabled.
- `:80-90` `codel_Newton_step()`: maintains 1/√count in Q0.16 by Newton iteration, avoiding sqrt and divide.
- `:92-102` `codel_control_law()`: comment "CoDel control_law is t + interval/sqrt(count)". **This is the formula the article never prints.**
- `:104-144` `codel_should_drop()`:
  - sojourn `ldelay = now − enqueue_time` (:123);
  - resets if sojourn < target **or backlog ≤ mtu** (:128-133), the paper's one-MTU rule;
  - `first_above_time = now + interval` (:139) is **the paper's "single state variable"**;
  - drops once now passes it (:140-141).
- `:146-271` `codel_dequeue()`, the dropping-state machine:
  - all work at dequeue, as the paper says;
  - the while loop drops and reschedules (:181-215);
  - ECN mark instead of drop (:188, :220), which is not in the paper;
  - "resume at a recent control level" (:233-250): reuse `count − lastcount` if re-entering within 16 intervals;
  - ce_threshold CE marking (:257-269), for DCTCP/L4S-style use; not in the paper.

**Data structures: `include/net/codel.h`**

- `:60-63` time base (`codel_time_t`, `CODEL_SHIFT` 10, `MS2TIME`).
- `:107` `struct codel_params` (target, ce_threshold, interval, mtu, ecn).
- `:129` `struct codel_vars` (count, lastcount, dropping, rec_inv_sqrt, first_above_time, drop_next, ldelay).
- `:151` `struct codel_stats` (maxpacket, drop_count, ecn_mark, ce_mark).

**Enqueue timestamp: `include/net/codel_qdisc.h`**

- `:67` `codel_get_enqueue_time()` and `:72` `codel_set_enqueue_time()`. This is the only work at enqueue, exactly as p.46 claims.

**The codel qdisc: `net/sched/sch_codel.c`**

- `:116-127` `codel_qdisc_enqueue()`: timestamp, or tail-drop when over `limit`, with reason `QDISC_DROP_OVERLIMIT`.
- `:85` `codel_qdisc_dequeue()` → `codel_dequeue()` (:64).
- `:198-208` `codel_init()`: limit 1000, `params.mtu = psched_mtu(dev)`.
- `:258-282` `codel_dump_stats()`: the source of `tc -s qdisc` fields `count`, `lastcount`, `ldelay`, `dropping`, `drop_next`, plus `maxpacket`, `ecn_mark`, `drop_overlimit`.
- CoDel's own drops use reason `QDISC_DROP_CONGESTED` (`include/net/dropreason-qdisc.h:58-63`). They are visible on `tracepoint:qdisc:qdisc_drop` (`include/trace/events/qdisc.h:88`) with fields `kind` and `reason`.

**fq_codel: `net/sched/sch_fq_codel.c`**

- `:185` `fq_codel_enqueue()`, with the timestamp at :204.
- `:284-322` `__fq_codel_dequeue()`: DRR over new_flows/old_flows with a per-flow `codel_dequeue()` at :306. The MTU check uses the **whole-qdisc** backlog `&sch->qstats.backlog`, not the flow's.
- `:515-525` defaults.
- This is the "mitigation for ack/data mixing" the paper hints at (p.49). It is not part of this article (RFC 8290).

**Wi-Fi: the learner's only NIC (`net/mac80211/`)**

- `iface.c:1621` sets `IFF_NO_QUEUE`, which is why `wlan0` shows `noqueue`.
- `tx.c:1402-1432` `fq_tin_dequeue_func()` calls `codel_dequeue()` per flow.
- `tx.c:1618-1621` sets target 20 ms, interval 100 ms, ECN on. So on this laptop, CoDel already runs inside mac80211, not in tc.
- `debugfs.c:74-111` `aqm_read()` shows the fq counters (root only). In v7.2 the arguments for the `fq_overlimit` and `fq_overmemory` labels appear swapped (:89-100). Read from source, not tested.

**Relatives**

- `net/sched/sch_cake.c:503` `cobalt_should_drop()` (CoDel + BLUE).
- `sch_pie.c`, `sch_fq_pie.c`, `sch_dualpi2.c` (L4S) are all present in v7.2.
- "Manage the right queue" at the NIC: BQL in `lib/dynamic_queue_limits.c:83` `dql_completed()` keeps the driver ring short so the queue builds in the qdisc, where CoDel can see it. That is the Linux analogue of Fig 10.

## 9. Prerequisites and forward references

**Assumed without definition:**
- TCP window and ack clock (deferred to Jacobson '88 [8]); slow-start.
- RED and its parameters; earlier AQM literature (BLUE [22]).
- ns-2, CUBIC, New Reno, SACK, PackMime-HTTP, CBR over UDP.
- Box plots and percentiles.
- MTU; Ethernet flow control (PAUSE frames); DiffServ and per-hop behaviours ("Delay Bound PHB").
- "Ack compression" and "data pendulum" (named on p.49, never defined).
- DOCSIS cable upstream; CeroWrt/OpenWrt.
- Poisson versus correlated (closed-loop) arrivals (p.45).

**Forward references inside the article:**
- The online pseudocode appendix (p.47).
- CeroWrt implementation and real-world tests; the ns-2 code release (p.50).
- An open question: whether to speed re-convergence after rate changes of ≥10× several times a minute (p.48).
- "Known mitigations" for ack/data mixing in the home-router implementation (p.49). These became fq_codel.

**Forward links to the learner's chain:**
- "Manage the right queue" → BQL and TSQ. TSQ keeps the *sending host's* qdisc short, so a local shaper plus CoDel won't see a standing queue from a local TCP.
- fq → pacing → EDT, where the queue becomes a timestamp and fq's horizon drop replaces queue-length drops.
- The "standing queue = window − pipe" framing → BBR's goal of keeping inflight ≈ BDP so the standing queue is ~0.
- "Min over a window ≥ RTT" → BBR's windowed min-RTT filter (RTprop; `tcp_update_rtt_min` at `tcp_input.c:3443` keeps a minmax windowed min).

## 10. References worth reading

1. **[16] Mathis, Semke, Mahdavi, "The macroscopic behavior of the TCP congestion avoidance algorithm," CCR 27(3), 1997.** The 1/√p law the control law leans on. Also closes the AIMD maths from paper 01.
2. **[12] Jacobson, Nichols, Poduri, "RED in a different light" (1999, unpublished).** Why RED is unconfigurable, and the earlier rate-based thinking behind the control law.
3. **[11] Jacobson, "A rant on queues" (MIT Lincoln Labs talk, 2006).** The origin of the min-queue insight, good-vs-bad queue, and "queues are shock absorbers". Slides.
4. Optional: **[7] Gettys & Nichols, "Bufferbloat: Dark buffers in the Internet," CACM 2011.** The motivating measurements.
5. Beyond the list:
   - **RFC 8289 (CoDel)**: the normative pseudocode this article omits.
   - **RFC 8290 (FQ-CoDel)**: what Linux and this laptop actually run.

## 11. Suggested spine and strands

**Spine:** **the 25-packet window pushed into a 20-packet pipe** (Figs 1–3, pp.44–45).
- The startup burst forms good queue that drains in one RTT. Then 5 packets sit at the bottleneck forever.
- CoDel's three ideas act on exactly that queue: minimum sojourn, one state variable, and the 1/√count drop schedule. The schedule makes the sender shrink its window until W ≈ pipe.
- Second act: the same link's rate collapses 100 → 1 Mbps (Fig 7, p.48), and the "reasonable" 830-packet buffer becomes 10 s of bad queue.

**Strands (quizzable claims):**
1. `standing-queue-is-window-minus-pipe`: steady-state queue = window − BDP (in packets). It adds delay with zero throughput gain and does not depend on the sender's rate (p.44).
2. `length-and-occupancy-are-blind`: neither queue length nor busy time separates good queue from bad (Figs 3–4, p.45).
3. `min-sojourn-over-interval`: CoDel's signal is the minimum per-packet sojourn over a window ≥ worst-case RTT. It is computable at dequeue with one variable and no locks (p.46).
4. `target-and-interval`: target 5 ms is the acceptable standing delay and interval 100 ms is about the worst-case RTT. One setting covers 10 ms–1 s RTTs and 64 kbps–100 Mbps (pp.46–47).
5. `inv-sqrt-drop-schedule`: in the dropping state the k-th gap is interval/√k (100, 70.7, 57.7, 50 ms…). The drop rate ramps linearly in time until delay < target (p.46; `codel_impl.h:93`).
6. `mtu-floor`: CoDel never drops with ≤ 1 MTU queued, so at low rates (128 kbps: 94 ms per 1500 B packet) delay sits far above target by design (p.46, Fig 6).
7. `manage-the-right-queue`: AQM is useless unless it sits at the queue that actually fills, such as a cable modem, NIC ring or Wi-Fi firmware (p.50, Fig 10). In Linux that means BQL, mac80211 TXQs and shaping just below the bottleneck rate.

## 12. Exercise ideas

1. **Pen and paper, 30–40 min: CoDel by hand.**
   - Compute the drop times for count 1…10 with I = 100 ms.
   - Derive t_k ≈ 2I√k and r(t) ≈ t/(2I²). How many drops in 1 s?
   - Explain why min-over-interval > target ⇔ continuously above target (Q4).
   - Redo the article's arithmetic: Q1 (216 ms for the 25th packet), Q2 (5 packets = 50 ms), Q8 (830 packets, 9.96 s at 1 Mbps), Q9 (120 ms), and the Fig 6 MTU floor (94 ms at 128 kbps).
2. **Bench, 50–60 min, no iperf3: pfifo vs codel vs fq_codel under load.**
   - Topology: 3 netns (snd — rtr — rcv). On rtr's egress to rcv: `htb` root, a 10 mbit class, child `pfifo limit 1000`, later swapped for `codel` then `fq_codel`. Put `netem delay 40ms` on rtr's egress back toward snd (the ACK path). Disable TSO/GSO on snd's veth.
   - Load: a python3 bulk TCP sender (cubic) for 60 s, with `ping -i 0.2` snd→rcv alongside.
   - Predict before running:

     | Qdisc | Predicted ping RTT |
     |---|---|
     | pfifo | ≈ 40 ms + up to 1000 × 1.21 ms ≈ 1.25 s |
     | codel | ≈ 40 + 5–10 ms |
     | fq_codel | ≈ 40 ms (ping gets its own flow) |

   - Read `tc -s qdisc show` (`count`, `lastcount`, `ldelay`, `drop_next`, `drop_overlimit`).
   - Count drops with bpftrace on `tracepoint:qdisc:qdisc_drop`, keyed by kind and reason (CONGESTED vs OVERLIMIT). Optionally timestamp the CoDel drops to see the 1/√count spacing.
   - Put the bottleneck in rtr deliberately; see the TSQ note in §9.
   - The bpftrace field syntax (`args.kind` vs `str(args->kind)`) depends on the installed version and is unverified.
3. **Bench, 30–40 min: reproduce Fig 2's standing queue exactly.**
   - Same topology, plain `pfifo`. On the receiver socket, set `TCP_WINDOW_CLAMP` (Python `socket.TCP_WINDOW_CLAMP` = 10) so the window ≈ BDP + 5 packets: (34.5 + 5) × 1448 ≈ 57 KB at 10 Mbit / 40 ms.
   - Expect: `tc -s` backlog ≈ 5 packets, ping inflated by ≈ 6 ms, throughput ≈ link rate. Clamp below the BDP and the queue goes to 0 while throughput drops.
   - Switch the queue to `codel`:
     - +5 packets (~6 ms > target) should trigger drops after 100 ms;
     - +3 packets (~3.6 ms < target) should never trigger a drop. This makes target = "acceptable standing queue" tangible.
   - Rounding of the clamp under window scaling is unverified.
4. **Observation, 15–20 min (root needed for debugfs): your own Wi-Fi.**
   - Run `tc -s qdisc show dev wlan0` (shows noqueue) and explain it from `iface.c:1621`.
   - Read `/sys/kernel/debug/ieee80211/phy0/aqm` and relate it to mac80211's 20 ms / 100 ms CoDel (`tx.c:1618-1621`).
   - Ping the AP while a large download runs and compare with Fig 7's behaviour. Mind the swapped debugfs labels.

## 13. Honest assessment for this learner

**What kind of paper this is:**
- A magazine "practice" article, not a full paper.
- No pseudocode (it is in an online appendix). The control law is never written as an equation.
- Every result is ns-2 simulation. No ECN, no flow queueing.
- The ideas are excellent. The specification lives in RFC 8289 and in `include/net/codel_impl.h` (271 lines), which the learner can read in 20 minutes alongside it.

**Read closely:**
- "Understanding Queues" and "Controlled Delay Management" (pp.44–46). The standing-queue argument and the good/bad split are the conceptual core.
- The paragraph on the three innovations and the target/interval paragraph (pp.46–47).
- "Manage the Right Queue" (pp.49–50). It maps directly onto BQL, TSQ, mac80211 and Cilium-era host queueing.

**Skim:**
- The simulation sections (pp.47–49). Pull out the numbers in §7 and ignore the box-plot detail.
- Figs 5, 8 and 9 are comparative evidence against RED, which matters little now.

**Since the paper:**
- **Linux and standards.**
  - CoDel and fq_codel were merged into Linux (implemented by Taht and Dumazet, per `codel_impl.h:49`; mainline in 3.5, 2012, from memory, unverified).
  - fq_codel became the de facto distro default through `net.core.default_qdisc` (this host). The kernel's own default is still pfifo_fast.
  - Standardised as **RFC 8289 (CoDel) and RFC 8290 (FQ-CoDel), both 2018**. RFC 7567 (2015) replaced the RFC 2309 RED recommendation the article cites, and recommends AQM without mandating an algorithm.
- **Linux additions the article lacks.** ECN marking (`codel_impl.h:188, 220`) and `ce_threshold` for DCTCP/L4S-style shallow marking (`:257`).
- **Successors.** PIE (RFC 8033), CAKE/COBALT, and L4S DualPI2 (RFC 9332; `sch_dualpi2.c`) build on or compete with it.
- **"No knobs" softened.**
  - At low rates, target must be at least about one MTU's serialisation time. RFC 8289 discusses setting target to 5–10% of interval (recalled, check the RFC section).
  - mac80211 uses 20 ms.
  - In data centres, 5 ms / 100 ms are orders of magnitude too large, so people use `ce_threshold` or fq's own marking.
- **Hosts and Cilium.** TSQ (Linux 3.6), fq + pacing (3.12) and EDT (4.20) moved host-side queue control out of AQM (version numbers from memory, unverified). Cilium's Bandwidth Manager runs mq + fq with EDT timestamps on the egress device, not CoDel (per Cilium docs; check in your fork). CoDel remains the right model for the *bottleneck router* and *Wi-Fi* cases, and for reading `tc -s` on edge boxes.
- **Typos in the article.** Ref [8] dates SIGCOMM '88 as "(Stanford, CA, 1998)", and the consumer-edge text says "512KB and 1.5MB" for kbps/Mbps. Neither matters.
