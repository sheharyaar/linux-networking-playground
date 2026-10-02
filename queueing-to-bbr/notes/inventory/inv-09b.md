# Inventory 09b: Cardwell et al., "BBR: Congestion-Based Congestion Control" (CACM 2017)

## 1. Facts

- **Citation:** Neal Cardwell, Yuchung Cheng, C. Stephen Gunn, Soheil Hassas Yeganeh, Van Jacobson. "BBR: Congestion-Based Congestion Control." *Communications of the ACM* 60(2):58–66, February 2017. DOI 10.1145/3009824. It is a "practice" article ("Article development led by queue.acm.org", p.58), reprinted from *ACM Queue* 14(5), Sep–Oct 2016. The kernel header comment cites the Queue version (net/ipv4/tcp_bbr.c:48-51).
- **PDF:** 9 pages. Printed page numbers are in every footer.
- **Printed range:** 58–66.
- **Offset:** printed = PDF + 57. I checked this on rendered pages: PDF p1 shows "58", PDF p3 shows "60", PDF p9 shows "66".
- **Layout:** p59 is mostly a Shutterstock illustration with three short text columns at the bottom. p61 carries a large pull-quote in the middle column, which repeats p60 text. The pull-quote misspells "anomolies"; the body text spells it correctly.

## 2. Sections (headings are unnumbered; printed pages)

| Heading | Pages |
|---|---|
| Untitled introduction ("By all accounts…") | 58 |
| Congestion and Bottlenecks | 58–60 (Fig 1 on p60; covers Kleinrock/Jaffe and "three-year quest") |
| Characterizing the Bottleneck | 60–61 (RTT model, estimators, uncertainty principle) |
| Matching the Packet Flow to the Delivery Path | 61–62. Run-in heads: "When an ack is received" p61, "When data is sent" p61–62, "Steady-state behavior" p62 (includes the Max-plus aside) |
| Single BBR Flow Startup Behavior | 62–63 (Startup/Drain, Figs 6–7) |
| Behavior of Multiple BBR Flows Sharing a Bottleneck | 63–64 (ProbeRTT and synchronization, Fig 8) |
| Google B4 WAN Deployment Experience | 64–65 (Figs 9–10, loss tolerance) |
| YouTube Edge Deployment Experience | 65 (Fig 11, SGSN/2.5G, Fig 12) |
| Mobile Cellular Adaptive Bandwidth | 66. Run-in heads: "Delayed and stretched aks." [sic], "Token-bucket policers.", "Competition with loss-based congestion control." |
| Conclusion | 66 |
| Acknowledgments, Related articles, References (18) | 66 |

## 3. Terms introduced (as the paper defines them)

1. **bottleneck**: the single slowest link in each direction. It sets the maximum delivery rate and is where persistent queues form. p58
2. **RTprop**: round-trip propagation time, the pipe's "length". It changes only when the path changes. p58 (estimator p61)
3. **BtlBw**: bottleneck bandwidth, the pipe's "minimum diameter". p58 (estimator p61)
4. **inflight**: data sent but not yet acknowledged. p58
5. **BDP**: BtlBw × RTprop, the inflight value where the RTprop and BtlBw constraint lines intersect. p59 (restated p60)
6. **app-limited / bandwidth-limited / buffer-limited**: the three regions of Fig 1, separated by inflight = BDP and inflight = BDP + BtlneckBufSize. p59 (figure p60)
7. **congestion / congestion control**: congestion is "sustained operation to the right of the BDP line". Congestion control is "some scheme to bound how far to the right a connection operates on average". p59
8. **rate balance / full pipe**: the two optimality conditions. Rate balance means bottleneck arrival rate = BtlBw. Full pipe means inflight = BDP. Both must hold at once. p60
9. **η (noise)**: an RTT excess ≥ 0 caused by queues, delayed-ACK strategy and ACK aggregation. p60
10. **delivery rate**: Δdelivered/Δt between a packet's send and its ACK. It is always ≤ the bottleneck rate. p61
11. **uncertainty principle**: RTprop is visible only left of BDP and BtlBw only right of it, so whenever one can be measured the other cannot. p61
12. **application limited**: the application has run out of data to fill the network. Such samples are marked and kept out of the BtlBw filter unless they exceed it. p61
13. **pacing_rate / pacing_gain**: pacing_rate = pacing_gain × BtlBw. It is "BBR's primary control parameter". p61–62
14. **cwnd_gain**: the secondary parameter. It caps inflight at a small multiple of BDP for network and receiver pathologies. p61; set to 2 for delayed/stretched ACKs, p66
15. **Startup / Drain / ProbeBW / ProbeRTT**: states, each defined by "a table containing one or more fixed gains and exit criteria". p62 (ProbeBW), p63 (Startup, Drain), p63–64 (ProbeRTT)

## 4. Core claims (with page)

1. Loss-based CC (even CUBIC) is the main cause of poor performance. With big buffers it keeps them full (bufferbloat). With small buffers it misreads loss as congestion and gets low throughput. pp58–59
2. The best operating point is the left edge of the bandwidth-limited region (inflight = BDP), not the right edge where loss-based CC sits. Kleinrock (1979) showed this point is optimal; Jaffe proved no distributed algorithm can converge to it. pp59–60
3. Jaffe's impossibility rests on measurement ambiguity, which disappears if BtlBw and RTprop are estimated *sequentially* over time. p60; restated in the Conclusion p66
4. A windowed min of RTT and a windowed max of delivery rate are "unbiased, efficient" estimators of RTprop and BtlBw. p61
5. Pacing is integral to the design and pacing_rate is the primary control. cwnd only bounds inflight. pp61–62
6. In steady state BBR keeps about one BDP in flight. It cycles pacing_gain (1.25 then 0.75) to detect BtlBw increases, so it converges to a new bottleneck rate "exponentially fast". p62
7. Startup uses gain 2/ln2 and finds BtlBw in log2(BDP) RTTs, creating up to 2 BDP of queue. Drain then removes that queue. p63
8. ProbeRTT dips synchronize flows "around the desirable event of an empty bottleneck queue". This drives fairness and stability. pp63–64
9. On B4, BBR throughput is 2–25× CUBIC's. On YouTube, median RTT drops 53% globally and by more than 80% in the developing world. pp64–65
10. CUBIC's loss tolerance is structural. BBR's loss tolerance is a configuration parameter (the ProbeBW peak gain): it meets link × (1 − loss) up to 5% loss and is close up to 15%. p65
11. Caveats: being too gentle starves cellular schedulers. Policers cause continuous losses, so a policer model was added. Router buffers larger than several BDPs let loss-based competitors take more than their fair share. p66

## 5. Figures worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| **1** | 60 | **RTT and delivery rate vs inflight**: two piecewise-linear panels, three regions, slopes 1/BtlBw and 1/RTprop, "optimum operating point is here" at BDP vs "loss-based CC operates here" at BDP + buffer | **Essential.** The chapter's anchor picture. Redraw it interactively (slider for buffer size) and overlay the Kleinrock power curve |
| 2 | 60 | onAck pseudocode | Maps 1:1 onto tcp_rate_skb_delivered / tcp_rate_gen / bbr_update_bw |
| 3 | 62 | send() pseudocode (cwnd cap, nextSendTime) | Maps onto tcp_update_skb_after_send (EDT) and the cwnd test |
| 4 | 62 | 700 ms detail of a 10 Mbps/40 ms flow: RTT, inflight and BW traces aligned with the 8-slot gain cycle (1.00×5, 1.25, 0.75, …) | Shows the one-RTT lag between applying a gain and seeing its effect. Shows that the 1.25 phase raises RTT, not delivery rate |
| 5 | 63 | BtlBw doubles at t=20 s ("BW estimate increases 1.95× (=1.25³) in 3 cycles"), then halves at t=40 s (inflight clamped by cwnd_gain until "20Mbps BtlBw times out of filter") | Asymmetric adaptation: fast up (1.25× per cycle), slow down (max-filter timeout of about 10 rounds at inflated RTT) |
| 6 | 63 | First second of a 10 Mbps/40 ms flow: time/sequence plot plus RTT, startup/drain/probe-BW markers, "cwnd_gain clamps BBR inflight at 3 BDP", CUBIC overlay | Startup/Drain dynamics, with numbers to reproduce |
| 7 | 64 | 8 s RTT: CUBIC fills the 250 ms buffer and cycles 70–100%; BBR flat at RTprop | Best bufferbloat contrast. Directly reproducible on the netns bench |
| 8 | 64 | Five BBR flows on a 100 Mbps/10 ms link converging to fair share, with ProbeRTT notches | Multi-flow convergence and ProbeRTT sync |
| 9 | 64 | B4: BBR/CUBIC throughput ratio vs CUBIC throughput (2× line), CDF inset | Deployment evidence. Skim |
| 10 | 65 | Goodput vs random loss (0.001–50%) on 100 Mbps/100 ms, plus the ideal-limit curve | Loss tolerance. Links to paper 10's cliff |
| 11 | 65 | YouTube CUBIC-RTT/BBR-RTT ratio vs CUBIC RTT | Skim |
| 12 | 65 | Median RTT vs buffer (150–9750 KB) on 128 Kbps/40 ms with 8 flows; SYN-timeout lines | CUBIC delay is linear in buffer size; BBR's is flat |

## 6. Maths

Background assumed: algebra only. The paper also uses the BDP/queue intuition, Mathis's 1/√p law (cited, not derived), Kleinrock's power metric (cited, never defined) and Max-plus algebra (a parenthetical pointer only).

| # | Item | Page | Learner reproduces? |
|---|---|---|---|
| M1 | RTT_t = RTprop_t + η_t, with η ≥ 0 | 60 | Yes (state and use) |
| M2 | RTprop-hat = RTprop + min(η_t) = min(RTT_t) for t ∈ [T − W_R, T]; W_R is "tens of seconds to minutes" | 61 | Yes |
| M3 | deliveryRate = Δdelivered/Δt ≤ BtlBw. Δdelivered is exact and Δt ≥ the true arrival interval, so the ratio can only underestimate | 61 | Yes (toggle: the bias argument) |
| M4 | BtlBw-hat = max(deliveryRate_t) for t ∈ [T − W_B, T]; W_B is 6–10 RTTs | 61 | Yes |
| M5 | BDP = BtlBw × RTprop | 59, 60 | Yes |
| M6 | Fig 1 model: deliveryRate = min(inflight/RTprop, BtlBw); RTT = max(RTprop, inflight/BtlBw); loss when inflight > BDP + buffer. The slopes are labelled on the figure | 60 | Yes. **Toggle: Kleinrock's optimum.** Power = rate/RTT is x/RTprop² for x ≤ BDP (rising) and BtlBw²/x beyond (falling), so the maximum is at x = BDP with P* = BtlBw/RTprop. The M/M/1 version (not in the paper): P = λ(μ−λ) peaks at ρ = ½, where mean occupancy N = 1, i.e. "keep the pipe just full" |
| M7 | send(): stop if inflight ≥ cwnd_gain·bdp; nextSendTime = now + size/(pacing_gain·BtlBw) | 62 (Fig 3) | Yes |
| M8 | Two worked counterexamples: IW = 10 into a 5-packet BDP at exactly the bottleneck rate leaves a 5-packet standing queue; sending one BDP in BDP/2 bursts gives full utilization but an average queue of BDP/4 | 60 | Yes. The BDP/4 sawtooth is a nice pen exercise |
| M9 | Gain cycle 1.25 / 0.75 / 1.0 (8 slots, visible only in Fig 4). Convergence: 1.25³ = 1.95 in 3 cycles (Fig 5) | 62–63 | Yes. **Toggle: why 1.25/0.75 drains what it adds.** One RTprop at 1.25 sends 1.25 BDP while the bottleneck drains 1 BDP, so the queue grows by 0.25 BDP. The 0.75 phase removes 0.25 BDP. Mean gain over the 8 slots is 1. A 0.25-BDP queue adds 0.25·RTprop of RTT (10 ms on a 40 ms path, matching Fig 4) |
| M10 | Startup gain 2/ln2 ≈ 2.885; BtlBw found in log2(BDP) RTTs; "up to 2BDP excess queue"; Drain gain = 1/(2/ln2) | 63 | Partly. **Toggle:** with a smooth exponential send rate and BBR's ACK-lagged, interval-averaged sampler, the gain needed to keep doubling each round comes out to 4·ln2 ≈ 2.77. That is my derivation. The paper gives none; the code comment (tcp_bbr.c:150-154) gives an informal rationale. Later BBR drafts reportedly use 2.77 (unverified). Drain duration if the queue is (g−1)·BDP: (g−1)/(1−1/g)·RTprop = g·RTprop ≈ 115 ms at 40 ms |
| M11 | cwnd_gain = 2 lets BBR keep sending "even when ACKs are delayed by up to one RTT" | 66 | Yes. **Toggle: the 2×BDP cap.** If ACKs are withheld for D ≤ RTprop while pacing at BtlBw, inflight peaks at BDP + BtlBw·D ≤ 2·BDP. The cap binds only when BtlBw is overestimated (Fig 5 bottom; multi-flow) |
| M12 | ProbeRTT: inflight 4 packets for ≥ 1 round when the RTprop estimate is "many seconds" old | 63–64 | Duty-cycle arithmetic comes from the code: 200 ms / 10 s ≈ 2% |
| M13 | Mathis: full rate needs loss < 1/BDP². "e.g. < one loss per 30 million packets for a 10Gbps/100ms path" | 64 | **Check it.** With 1500 B packets, BDP = 83,333 packets and 1/BDP² ≈ 1 per 6.9 × 10⁹. With Mathis C = √1.5 it is about 1 per 4.9 × 10⁹. "30 million" fits a 1 Gbps/100 ms path better (1 per 46–69 M). This is my arithmetic; I checked no erratum |
| M14 | 8 MB / 200 ms ⇒ 335 Mbps (uses MiB: 8·2²⁰·8/0.2 = 335.5 Mbps); 2 Gbps vs 15 Mbps = 133× | 64 | Yes |
| M15 | Maximum possible throughput = link rate × (1 − lossRate) | 65 | Yes. Combine with paper 10's g(1−p) = 1 cliff |

## 7. Numbers worth reusing

- **10 Mbps, 40 ms** (Figs 4, 6, 7): BDP = 50 KB ≈ 34.5 MSS of 1448 B. A 1.25 phase adds 12.5 KB of queue, about +10 ms RTT. The Fig 7 buffer is 250 ms = 312.5 KB = 6.25 BDP; CUBIC's RTT reaches about 290 ms and cycles 70–100% full. Fig 6 RTT peaks near 120 ms = 3·RTprop, matching "cwnd_gain clamps inflight at 3 BDP" (≈2 BDP queue).
- **Fig 5:** after the 10 → 20 Mbps step, the estimate grows 1.25× per cycle of about 8·RTprop ≈ 0.32 s. It doubles in about 3 cycles (≈1 s; the figure shows 20 → about 21 s). After the 20 → 10 Mbps drop, inflight is clamped at 2·old BDP = 200 KB, so RTT is about 160–170 ms. The stale max ages out after 10 rounds × ~170 ms ≈ 1.7–1.8 s (the figure shows about 41.8 s).
- **Fig 8:** 100 Mbps / 10 ms, BDP 125 KB, 5 flows → 20 Mbps fair share.
- **B4:** 2–25× CUBIC. 75% of BBR connections were rwnd-limited by an 8 MB receive buffer (8 MB/200 ms ⇒ 335 Mbps). One US–Europe path: 2 Gbps BBR vs 15 Mbps CUBIC. The prober sends 8 MB per minute. B4 has been all-BBR since 2016.
- **Fig 10:** 100 Mbps/100 ms, 60 s flows, random loss 0.001–50%. CUBIC drops 10× at 0.1% loss and stalls above 1%. BBR is at the limit up to 5% and close up to 15%.
- **YouTube:** −53% median RTT globally, −80%+ in the developing world, more than 200 M playbacks on five continents over a week.
- **SGSN / 2.5G:** 8–114 kbps links serving more than half of 7 B mobile subscriptions. Fig 12 uses 128 Kbps/40 ms (BDP = 640 B, under one packet) with 8 flows and 150–9750 KB buffers. CUBIC delay at 9750 KB is 9.75 MB × 8 / 128 kbps ≈ 609 s, matching the plot's ~600 s.
- **Startup:** 12 orders of magnitude of link speeds, binary search in log2(BDP) rounds.

## 8. Linux mapping (v7.2 tree, `git describe` = v7.2; lines verified by grep)

**What upstream has:** upstream v7.2 `net/ipv4/tcp_bbr.c` (1200 lines) is **BBRv1**. Its header (lines 2–59) gives the v1 model, the 4-state diagram and the Queue 2016 citation. A grep finds no `inflight_hi`, `inflight_lo`, ECN or v2/v3 code. The only loss-related logic is packet conservation, the lost-packet deduction and the long-term (lt_) policer model. Recent changes are interface-only: `cwnd_event_tx_start` hook (v7.1-rc1, d1e59a469737) and the cong_control args (v6.10).

| Paper concept | Code symbol | Location |
|---|---|---|
| Model summary (BtlBw = windowed_max over 10 rounds, min_rtt over 10 s, pacing = gain × bw, cwnd = max(gain × bw × min_rtt, 4)) | header comment | tcp_bbr.c:7-11 |
| States Startup/Drain/ProbeBW/ProbeRTT | `enum bbr_mode` BBR_STARTUP … BBR_PROBE_RTT | tcp_bbr.c:82 |
| Per-flow state | `struct bbr` (min_rtt_us:91, `struct minmax bw`:94, rtt_cnt:95, next_rtt_delivered:96, lt_*:105-111, pacing_gain:10 bits:112, cwnd_gain:113, full_bw_reached:114, full_bw_cnt:115, cycle_idx:116, extra_acked[2]:124) | tcp_bbr.c:90-129 |
| 8-slot ProbeBW cycle | `CYCLE_LEN 8` | :131 |
| W_B "6–10 RTTs" | `bbr_bw_rtts = CYCLE_LEN + 2` (10 *packet-timed rounds*, not wall time) | :134 |
| W_R "tens of s to minutes" | `bbr_min_rtt_win_sec = 10` | :136 |
| ProbeRTT "at least one round trip" | `bbr_probe_rtt_mode_ms = 200`, so max(200 ms, 1 round) | :138; logic :942-985 |
| (not in paper) pace 1% under bw | `bbr_pacing_margin_percent = 1` | :148, applied :252 |
| Startup gain 2/ln2 | `bbr_high_gain = BBR_UNIT*2885/1000+1` = 739/256 = 2.88672 | :155 |
| Drain = inverse gain | `bbr_drain_gain = BBR_UNIT*1000/2885` = 88/256 = 0.34375 | :159 |
| cwnd_gain = 2 | `bbr_cwnd_gain = BBR_UNIT*2` | :161 |
| 1.25 / 0.75 / 1×6 | `bbr_pacing_gain[]` | :163-169 |
| (not in paper) random start phase | `bbr_cycle_rand = 7`, used at :623. The start index is never the 0.75 slot | :170 |
| ProbeRTT "four packets" | `bbr_cwnd_min_target = 4` | :176 |
| Startup exit "while delivery rate is increasing" | `bbr_full_bw_thresh = 5/4`, `bbr_full_bw_cnt = 3`, so exit after 3 rounds with < 25% growth | :180, :182; `bbr_check_full_bw_reached` :874 |
| Policer model (p66) | lt_ params (`bbr_lt_loss_thresh = 50` ⇒ 50/256 ≈ 19.5% loss), `bbr_lt_bw_sampling` :689, `bbr_lt_bw_interval_done` :659; uses lt_bw for 48 rounds (:194) and forces pacing_gain = 1 (:1002-1004) | :186-194 |
| BtlBw estimate | `bbr_max_bw` :216 (minmax_get); `bbr_bw` :224 (lt_bw if policed) | |
| pacing_rate = gain × BtlBw | `bbr_rate_bytes_per_sec` :245, `bbr_bw_to_pacing_rate` :257 (capped by SO_MAX_PACING_RATE), **`bbr_set_pacing_rate`** :287. Before full_bw_reached the rate only rises (:295) | |
| BDP | `bbr_bdp` :361 (ceil(bw × min_rtt × gain), :381) | |
| (not in paper) TSO/delayed-ACK quantization | `bbr_quantization_budget` :396 (+3 TSO goals, round to even, +2 in phase 0) | |
| (not in paper, EDT era v4.20) | `bbr_packets_in_net_at_edt` :438 | |
| Delayed/stretched ACKs (p66) | cwnd_gain 2 plus `bbr_update_ack_aggregation` :818 and `bbr_ack_aggregation_cwnd` :458 (added v5.1, 78dc70ebaa38) | |
| (not in paper) loss recovery | `bbr_set_cwnd_to_recover_or_restore` :481 (packet conservation for the first round) | |
| inflight cap cwnd_gain × bdp | `bbr_set_cwnd` :520 (min(cwnd+acked, target) :543; ProbeRTT cap :551) | |
| Gain-cycle phase timing | `bbr_is_next_cycle_phase` :555. A phase lasts min_rtt; 1.25 also needs inflight ≥ 1.25 BDP or a loss (:582); 0.75 ends early once inflight ≤ BDP (:589). Then `bbr_advance_cycle_phase` :592, `bbr_update_cycle_phase` :602 | |
| BtlBw filter update with the app-limited rule (Fig 2's `if`) | **`bbr_update_bw`** :762. The round counter uses `next_rtt_delivered`; filter :799-801 is `if (!rs->is_app_limited \|\| bw >= bbr_max_bw(sk)) minmax_running_max(...)` (paper: `>`, code: `>=`) | |
| Startup → Drain → ProbeBW | **`bbr_check_drain`** :894 (sets ssthresh :900; exits when in-network-at-EDT ≤ BDP, :903-906) | |
| RTprop filter + ProbeRTT | **`bbr_update_min_rtt`** :942 (expiry :949; skips delayed ACKs; enters PROBE_RTT :960; done-stamp :973); `bbr_check_probe_rtt_done` :909. This is a simple min with timestamp expiry, *not* the minmax lib | |
| Gain table per state | `bbr_update_gains` :988 (STARTUP: both high_gain; DRAIN: drain/high; PROBE_BW: cycle/2; PROBE_RTT: 1/1) | |
| onAck | `bbr_update_model` :1017 → **`bbr_main`** :1028 (`.cong_control`, :1149) | |
| Requires pacing | `bbr_init` :1040 sets `SK_PACING_NEEDED` (:1079), so TCP paces internally if there is no fq (header comment :56-59) | |
| ss output | `bbr_get_info` :1108 (bw = bbr_bw × mss × 1e6 >> 24 bytes/s; min_rtt_us; gains <<8) → `.get_info` :1155 | |
| Unprivileged use | `.flags = TCP_CONG_NON_RESTRICTED` :1145. Once loaded it is setsockopt-able by any user | |

**Delivery-rate sampling.** `net/ipv4/tcp_rate.c` **no longer exists in v7.2.** It was dissolved in v7.0-rc1 (commits f10ab9d3a7ea, 670ade3bfae6, b814bdcecd79, bc1f0b1c98f5). Current locations:
- `tcp_rate_skb_sent` is at net/ipv4/tcp_output.c:1473. It snapshots `tx.delivered` (:1500), `tx.delivered_mstamp`, `first_tx_mstamp` and `tx.is_app_limited` (:1502). These are Fig 3's `packet.delivered` / `packet.delivered_time` / `packet.app_limited`.
- The estimator's design comment starts at net/ipv4/tcp_input.c:1690.
- `tcp_rate_gen` is at :1724. It clears the app-limited bubble at :1730, uses interval = max(send-phase, ack-phase) at :1767 (the paper uses the ACK phase only), discards samples with interval < min_rtt at :1780, and records `rate_delivered`/`rate_interval_us` for tcp_info at :1790.
- `tcp_rate_skb_delivered` is at :1808. It is called from tcp_ack, which calls `tcp_rate_gen` at :4439 and then `tcp_cong_control` at :4440 (def :3858 → `cong_control` = bbr_main).
- `tcp_rate_check_app_limited` is at net/ipv4/tcp.c:1099. It is Fig 3's `app_limited_until = inflight`, setting `tp->app_limited = delivered + inflight`.
- `struct rate_sample` is at include/net/tcp.h:1306.
- Delivery rate in BBR is in **packets**/µs << 24 (BW_SCALE). The paper uses bytes.

**Pacing / EDT (Fig 3's nextSendTime):**
- `tcp_update_skb_after_send` (tcp_output.c:1446) advances `tp->tcp_wstamp_ns` by len × 1e9 / sk_pacing_rate. The first 10 segments are not paced (:1458).
- `__tcp_transmit_skb` (:1536) stamps `skb_set_delivery_time(skb, tcp_wstamp_ns)` at :1555 for sch_fq.
- `tcp_pacing_check` (:2815) is the internal-pacing hrtimer path. `tcp_needs_internal_pacing` is at include/net/tcp.h:1614.
- The TSQ / TSO-size coupling to pacing rate is `tcp_tso_autosize` (:2256) and `tcp_small_queue_check` (:2857), both using `sk_pacing_rate >> sk_pacing_shift`.
- sch_fq's pacing header comment is at net/sched/sch_fq.c:14-20.
- Windowed max is `minmax_running_max` (lib/win_minmax.c:67; Kathleen Nichols' 3-sample algorithm).
- History: TCP internal pacing landed in v4.13 (218af599fa63). The EDT model landed in v4.20 (ab408b6dc744; BBR adapted in a87c83d5ee25).

**How `ss -ti` prints BBR:**
- inet_diag calls `ca_ops->get_info` (net/ipv4/inet_diag.c:343-344) and emits `INET_DIAG_BBRINFO`. The layout is `struct tcp_bbr_info` (include/uapi/linux/inet_diag.h:234): bw_lo/hi in bytes/s, min_rtt in µs, gains as fixed-point << 8.
- The same struct is available through `getsockopt(TCP_CC_INFO=26)` (net/ipv4/tcp.c:4555). Python exposes `socket.TCP_CC_INFO`; unpack with `struct.unpack('<5I', ...)`.
- `/usr/bin/ss` (iproute2 7.2.0) contains the format `bbr:(bw:%sbps,mrtt:%g,pacing_gain:%g,cwnd_gain:%g)`, which I confirmed with `strings`. I infer that mrtt is in ms and the gains are /256; I did not read the iproute2 source.
- **State decoder for ss:**
  - pacing_gain 2.88672 + cwnd_gain 2.88672 → STARTUP
  - 0.34375 + 2.88672 → DRAIN
  - 1.25, 0.75 or 1 + cwnd_gain 2 → PROBE_BW
  - 1 + 1 → PROBE_RTT
  - 1 + 2 held for many rounds → probably lt_bw policer mode
- ss's `pacing_rate` ≈ 0.99 × pacing_gain × bw.
- ss's `minrtt` (tcp_min_rtt, 300 s window, `tcp_min_rtt_wlen`, tcp_input.c:3443) differs from `mrtt` (BBR's 10 s window).
- ss's `delivery_rate` is the last non-app-limited sample (tcp.c:388, :4321-4324).

**Paper name → code name:** BtlBw → `bbr->bw` / `bbr_max_bw()` / ss `bw`; RTprop → `min_rtt_us` / ss `mrtt`; deliveryRate → `rs->delivered / rs->interval_us`; app_limited_until → `tp->app_limited`; nextSendTime → `tp->tcp_wstamp_ns`; ProbeBW → `BBR_PROBE_BW`; "policer model" → `lt_bw` / `lt_use_bw`; "2/ln2" → `bbr_high_gain`.

**Paper vs code:**

| Paper | Code |
|---|---|
| W_B "6–10 RTTs" | 10 rounds |
| W_R "tens of s–min" | 10 s |
| ProbeRTT "≥ 1 round" | max(200 ms, 1 round) |
| Startup exit not quantified | 25% growth / 3 rounds |

**Lab note:** this host shows `tcp_available_congestion_control = reno cubic`. tcp_bbr.ko.zst is present but not loaded, so it needs `sudo modprobe tcp_bbr` (no install). Default qdisc is fq_codel, so BBR will use internal pacing unless fq is set.

**Cilium tie-ins (kernel side only):**
- Pod BBR depends on EDT timestamps surviving the veth netns hop. Kernel commit a1ac9c8acec1 "net: Add skb->mono_delivery_time…" (v5.18-rc1) states exactly this case (`tcp-sender => veth@netns => veth@hostns => fq@eth0`).
- Cilium's own ≥5.18 requirement and knob names are from memory, unverified here.

## 9. Prerequisites and forward references

**Assumed:**
- TCP sliding window, ACK clocking, cwnd, slow start, rwnd, RTO, delayed ACKs
- loss-based AIMD/CUBIC
- bufferbloat (cites Gettys & Nichols)
- token-bucket policers
- the Mathis 1/√p law
- the idea of pacing and the Linux FQ qdisc (cited via the LWN article)
- BDP

Not assumed but alluded to: Kleinrock's power metric, Max-plus algebra.

**Not mentioned at all:** CoDel/AQM, TSQ, EDT, timing wheels, ECN. The chapter must supply these links from the code: EDT `tcp_wstamp_ns`, fq `time_to_send`, TSQ `tcp_small_queue_check`.

**Forward references inside the paper:**
- "explicit policer model" (p66; details only in code)
- "actively researching" competition with loss-based flows in deep buffers (p66; this is BBRv2's motivation)
- Max-plus control (p62, ref 12)

## 10. References worth reading (from its list)

1. **[16] Kleinrock 1979, "Power and deterministic rules of thumb…"** (and [8] Gail & Kleinrock 1981). The source of the optimal-operating-point argument behind Fig 1. Good for the derivation toggle.
2. **[17] Mathis, Semke, Mahdavi, Ott 1997, "The macroscopic behavior of the TCP congestion avoidance algorithm."** The 1/√p law behind the B4 and loss-tolerance claims, and the AIMD end of the chain.
3. **[4] Corbet, "TSO sizing and the FQ scheduler," LWN 2013.** The fq/pacing and TSO-autosizing link in the chain, and the qdisc BBR relies on.
4. **[7] Flach et al., "An Internet-wide analysis of traffic policing," SIGCOMM 2016.** Why `lt_bw` exists. It explains the 20% loss threshold confound in paper 10.

## 11. Chapter spine and strands

**Spine:**
1. Hook: Fig 7, CUBIC's 290 ms vs BBR's flat 40 ms on the same 10 Mbps path.
2. Two constraints and Fig 1: three regions, where loss-based CC lives, why bufferbloat follows. Toggle: Kleinrock power peaks at BDP.
3. Rate balance + full pipe; the two counterexamples (IW into a small BDP; BDP/2 bursts).
4. Estimation: RTT = RTprop + η; windowed min/max; why each is one-sided; uncertainty principle. Linux: rate sampler (now in tcp_output.c / tcp_input.c), minmax.
5. Control: onAck/send → `bbr_main`, `sk_pacing_rate`, EDT `tcp_wstamp_ns`, fq or internal pacing; cwnd as cap. Toggle: 2×BDP cap.
6. Steady state: ProbeBW gain cycle (Fig 4), up/down adaptation (Fig 5). Toggle: zero-sum cycle; 1.25ⁿ growth; filter timeout arithmetic.
7. Startup/Drain (Fig 6), ProbeRTT and synchronization (Fig 8). Arithmetic: log2 BDP rounds, g·RTprop drain, 2% duty.
8. Evidence and limits: B4, loss tolerance (Fig 10), YouTube, SGSN; policers, cellular, competition (p66).
9. Diagnose a live host: decode `ss -ti` bbr fields and `tc -s qdisc` (fq throttled counts, backlog).
10. Bridge to paper 10: where v1 breaks (shallow buffers, loss cliff, CUBIC coexistence) and what upstream still runs (v1).

**Strands:**
- `bdp-knee-is-optimal`: The optimal operating point is inflight = BtlBw × RTprop; loss-based CC operates at BDP + buffer. (p59–60, Fig 1)
- `one-sided-estimators`: Delivery-rate samples can only underestimate BtlBw and RTT samples can only overestimate RTprop, hence windowed max and windowed min. (p60–61)
- `uncertainty-forces-probing`: RTprop is observable only left of BDP and BtlBw only right of it, so BBR must alternate (gain > 1 vs ProbeRTT). (p61)
- `pacing-primary-cwnd-cap`: pacing_rate = gain × BtlBw is the control; cwnd = 2 × BDP is a cap sized for ACKs delayed up to one RTT. (p61, p66)
- `gain-cycle-zero-sum`: 1.25 for one RTprop adds 0.25 BDP of queue, 0.75 removes it; bandwidth increases are found at 1.25× per 8-RTprop cycle. (p62–63)
- `startup-drain-probertt-numbers`: Startup 2/ln2 ≈ 2.89 (code 739/256), Drain 0.344, ProbeRTT 4 packets for max(200 ms, 1 round) every 10 s ≈ 2% duty. (p63–64 + code)
- `ss-gains-decode-state`: In `ss -ti`, pacing_gain/cwnd_gain identify the state: 2.89/2.89 STARTUP, 0.34/2.89 DRAIN, {1.25, 0.75, 1}/2 PROBE_BW, 1/1 PROBE_RTT. (code)

## 12. Exercise ideas (none needs iperf3)

1. **Pen and paper, 40 min: "BBR by hand on 10 Mbps / 40 ms."**
   - Compute BDP in bytes and packets.
   - Compute the queue and RTT bump from a 1.25 phase (compare Fig 4).
   - Compute Startup rounds from IW10, and the DRAIN time if the queue is 2 BDP (g·RTprop).
   - Compute throughput during ProbeRTT (4 × 1448 B / 40 ms ≈ 1.16 Mbps) and the duty-cycle cost.
   - Fig 5 timings: 1.25ⁿ ≥ 2 → n = 4 cycles to be sure (1.95 after 3), and the stale-max timeout 10 rounds × ~170 ms.
   - Check the B4 numbers (8 MiB/200 ms, 133×). Re-derive the "1 per 30 M packets" example and find that it does not match 10 Gbps.
   - Decode five given `ss` lines into states.
2. **Lab, 50–60 min: reproduce Figs 6/7 on netns.**
   - Topology: three netns `snd—rtr—rcv` with two veth pairs.
   - On rtr's egress toward rcv: `tbf rate 10mbit burst 3000 limit 312500` (a 250 ms buffer).
   - On rcv's egress (the ACK path): `netem delay 40ms`. This keeps shaping off the sender, as paper 10 p132 advises because of TSQ.
   - Run `sudo modprobe tcp_bbr` once.
   - Python sender: `setsockopt(IPPROTO_TCP, TCP_CONGESTION, b"bbr")`, `sendall` for 10 s. A sampler thread reads `TCP_INFO` and `TCP_CC_INFO` every 5 ms into CSV. Python receiver drains the socket.
   - Plot RTT, bw, pacing_gain and cwnd for bbr vs cubic.
   - Also watch `ip netns exec rtr tc -s qdisc` (backlog, drops) and `ss -tin` in snd.
   - Variant: set `ip route … congctl bbr` in snd instead of setsockopt.
   - Variant: sender qdisc fq vs fq_codel (internal pacing).
   - With iperf3 you could use `iperf3 -C bbr`; the Python pair replaces it.
3. **Lab, 40 min: bandwidth step (Fig 5).**
   - Same bench. Use `tc qdisc change … tbf rate 20mbit` at t = 10 s and back to 10mbit at t = 20 s.
   - Predict when bw reaches 20 Mbps (≈3–4 cycles of 8·RTprop) and when the stale 20 Mbps max ages out (10 rounds at inflated RTT). Compare with the TCP_CC_INFO trace.
4. **Lab, 30–40 min: five flows and ProbeRTT sync (Fig 8).**
   - 100 mbit / 10 ms, 5 Python BBR flows started 2 s apart.
   - Plot per-flow throughput and mark samples where gains = 1/1 (PROBE_RTT). Check that the ProbeRTT dips align.
   - Optional Cilium tie-in (unverified knob names): inspect `tc qdisc show` inside a kind node container for fq when the Bandwidth Manager is on, and the pod netns `net.ipv4.tcp_congestion_control`.

## 13. Honest assessment

**Read closely:**
- pp59–63, the whole argument from Fig 1 through Startup/Drain, especially the p60 counterexamples, the p61 estimator bias argument and the Fig 2/3 pseudocode
- the ProbeRTT paragraph (pp63–64)
- the p65 loss-tolerance paragraph
- the four p66 "lessons" paragraphs (they explain 1.25, cwnd_gain = 2 and lt_bw)

**Skim:**
- the Kleinrock/Jaffe history (p59–60), keeping only the claim
- the Max-plus aside (p62), which is an unexplained pointer
- B4/YouTube/SGSN (pp64–65): take the numbers and Figs 9/11/12 only

**Caveats:**
- The paper describes the 2016 design. Several important code behaviors are absent from it: pacing margin, quantization budget, ack-aggregation cwnd, packet conservation, full-bw thresholds, the randomized cycle phase, the 200 ms ProbeRTT floor. Teach from code for those.
- The paper never shows the 8-slot cycle length in text, only in Fig 4.
- The "30 million packets" example looks arithmetically off (see M13).
- Upstream v7.2 is still BBRv1, so everything the paper says still describes the shipping Linux CC, modulo the additions listed above.
