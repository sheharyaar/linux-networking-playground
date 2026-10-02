# Inventory 10: Cao, Jain, Sharma, Balasubramanian, Gandhi, "When to use and when not to use BBR" (IMC 2019)

## 1. Facts

- **Citation:** Yi Cao, Arpit Jain, Kriti Sharma, Aruna Balasubramanian, Anshul Gandhi (all Stony Brook University). "When to use and when not to use BBR: An empirical analysis and evaluation study." In *Proceedings of the Internet Measurement Conference (IMC '19)*, October 21–23, 2019, Amsterdam, Netherlands. ACM, pp. 130–136 (a 7-page short paper). DOI 10.1145/3355369.3355579. ISBN 978-1-4503-6948-0/19/10.
  - Sources: the ACM Reference Format block and footer on p130, and the running header "IMC '19, October 21–23, 2019, Amsterdam, Netherlands" on every page.
- **PDF:** 7 pages. Printed page numbers are centred at the bottom of each page.
- **Printed range:** 130–136.
- **Offset:** printed = PDF + 129. I checked this on rendered pages: PDF p1 shows "130", PDF p4 shows "133", PDF p7 shows "136".
- **Experiments ran on Linux 4.15** (p132) with Ubuntu 18.10 TCP memory settings (p132). Traffic came from iPerf3.

## 2. Sections (printed pages)

| Section | Pages |
|---|---|
| Abstract, CCS, ACM ref | 130 |
| 1 Introduction | 130–131 |
| 2 Background on BBR (Fig 1) | 131 |
| 3 Experimental Setup / 3.1 Testbeds | 131–132 |
| 3.2 Setting the network parameters (TC-tbf, Fig 3) | 132 |
| 4 Evaluation | 132–135 |
| 4.1 BBR versus Cubic (Fig 4 tree) | 132–134 |
| 4.1.1 Decision Tree | 132–133 |
| 4.1.2 Deconstructing the decision tree results (Goodput Eq 1, Loss, Latency Eq 2; Figs 5–6) | 133–134 |
| 4.2 BBR's goodput vs packet losses (Eq 3, Fig 7) | 134 |
| 4.3 Analyzing BBR's fairness (Fig 8, Table 1; Mininet results, WAN results, Reason for using Mininet) | 134–135 |
| 5 Related Work | 135 |
| 6 Limitations and Future Work | 135 |
| 7 Conclusion; Acknowledgment | 135 |
| References [1]–[39] | 136 |

The text extraction scrambles the numbering of sections 5–7. The rendered p135 shows 5 Related Work, 6 Limitations, 7 Conclusion.

## 3. Terms introduced (as the paper defines them)

1. **BtlBw**: a max filter, "the maximum value of the observed bandwidth in the last few RTTs". p131
2. **RTprop**: the min-filtered network delay. p131
3. **pacing_gain**: "a dynamic gain factor used to scale BtlBw". It yields pacing_rate, which "controls the inter-packet spacing". p131
4. **cwnd_gain**: "a dynamic gain factor used to scale BDP". It yields cwnd. p131
5. **ProbeBW range**: "BBR then regulates the pacing_rate between 1.25 × BtlBw and 0.75 × BtlBw". p131
6. **ProbeRTT**: periodically entered "to reduce its cwnd and drain the queue to reset itself". p131
7. **2× BDP in flight**: "One BDP is budgeted for the network capacity, and the other is to deal with delayed/aggregated ACKs". p131
8. **shallow / deep buffer**: 100 KB vs 10 MB. 10 MB counts as "deep" because it exceeds most BDPs in the grid (e.g. 500 Mbps × 100 ms = 6.25 MB). p133
9. **GpGain^bbr_cubic**: percentage goodput gain of BBR over Cubic, Eq (1). p133
10. **LatDec^bbr_cubic**: percentage reduction in *completion time* of 10 MB/100 MB flows, Eq (2). p133
11. **cliff point**: the loss rate beyond which BBR's goodput drops abruptly; p = 1 − 1/pacing_gain. Introduced p131, defined p134
12. **BBR_1.1 / BBR_1.5**: BBR rebuilt with the maximum pacing_gain set to 1.1 or 1.5. p134
13. **TC-tbf**: token bucket. `rate` tokens are added per second, 1 token = 1 byte, and a packet of L bytes needs L tokens. The qdisc length sets the buffer. p132
14. **TC-NetEm**: delay and random-loss emulator. p132, p134
15. **policing signal**: "BBR considers a > 20% loss rate a signal of policing [8], and so uses the long-term average bandwidth". p134

## 4. Core claims (with page)

1. When the bottleneck buffer is much smaller than BDP, BBR gets up to 200% more goodput than Cubic. Example: 100 KB buffer, 200 ms, 500 Mbps gives Cubic 179.6 vs BBR 386.0 Mbps (+115%). In deep buffers Cubic wins, by at most +34% (p133); the intro rounds this to "30%" (p131). pp131, 133
2. In shallow buffers BBR's losses are several orders of magnitude higher than Cubic's. It often has 10× more retransmissions. Average loss at 100 KB is 10.1% for BBR vs 0.9% for Cubic; at 10 MB it is 0.8% vs 1.3%. p131, p133
3. The authors attribute the shallow-buffer loss to cwnd_gain = 2: the 2×BDP inflight "requires a buffer size of at least BDP". They also say "decreasing the 2× multiplier … significantly lowers the packet losses". pp131, 133. *No data for the reduced multiplier is shown.*
4. Contrary to BBR's design goal, BBR "often exhibits large queue sizes". p130. *This is inferred, not measured. No RTT or queue-occupancy data appears.*
5. A loss-rate **cliff** exists at p = 1 − 1/max pacing_gain: 20% for 1.25. BBR_1.1 drops near 9%. BBR_1.5 drops before its predicted 33% because of the >20% policing logic. p134
6. Retransmissions peak at the cliff. Before it goodput holds while loss grows; after it the sending rate collapses. p134
7. Sharing with Cubic depends on bottleneck buffer size (1 Gbps, 20 ms). With a 10 KB buffer BBR takes 94%. With 10 MB, Cubic gets 3× BBR. Around 5 MB the split is even. With a 100 KB buffer BBR has more than 200× Cubic's retransmits (Table 1). p134–135
8. On the real WAN path (Stony Brook → Rutgers) the in-the-wild bottleneck buffer is about 20 KB. BBR therefore dominates Cubic at every router buffer setting, and its retransmits settle near 500 packets/min. p135
9. A decision tree over 640 LAN configurations picks BBR vs Cubic with 81.9% median / 81.3% mean accuracy (5-fold CV); with default TCP memory it reaches 90.2% / 90.0%. The Mininet tree reaches about 90%. pp132–133
10. The issues (cliff, retransmits, unfairness) are "inherent in the current version of BBR". It is "not entirely obvious" whether they will persist. p135

## 5. Figures worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| 1 | 131 | (a) model-based design (path model → state machine → rate/quantum/cwnd); (b) Startup → Drain → ProbeBW ↔ ProbeRTT | Duplicates paper 09. Skip |
| 2 | 132 | Dumbbell (h1, h2 → router TBF/NetEm → h3) and the WAN variant | **Testbed template.** Shaping goes on a middle router, not the end host |
| 3 | 132 | Packet path IP stack → qdisc → TBF token bucket → NIC | Useful little tbf picture for `tc -s qdisc` readers |
| **4** | 132 | Decision tree. The root splits on BW ≤ 875 (samples = 222, value = [97, 125], class cubic). Right: RTT ≤ 37.5 → both leaves BBR. Left: BW ≤ 375 → (RTT ≤ 17.5 → both leaves cubic) / (BufSize ≤ 5.5 MB → bbr, else cubic) | Worth critiquing rather than redrawing (see §13) |
| **5** | 133 | Heatmaps of GpGain over 8 BW × 8 RTT at 100 KB (a) and 10 MB (b); BBR (c) and Cubic (d) retransmits at 100 KB | **The key evidence.** Redraw with a buffer/BDP axis instead of BW × RTT; the paper's thesis then becomes a single monotone picture |
| 6 | 134 | LatDec heatmaps (100 MB flows) at 100 KB and 10 MB | Same story for completion time. Note that "latency" means FCT here |
| **7** | 134 | Mininet 100 Mbps/25 ms/10 MB: (a) goodput vs loss 0–50% for Cubic, Reno, BBR, BBR_1.1, BBR_1.5; (b) retransmits vs loss | **The cliff.** Overlay vertical lines at 1 − 1/g and at the 19.5% lt_bw threshold |
| **8** | 134 | BBR vs Cubic share vs buffer (10⁴–10⁷ B) at 1 Gbps/20 ms: (a) Mininet crossover near 5 MB; (b) WAN flat, BBR ≈ 720 vs Cubic ≈ 60 Mbps | Coexistence depends on buffer/BDP. The crossover is at about 2 × BDP (BDP = 2.5 MB), which is my arithmetic, not the paper's |
| Table 1 | 135 | BBR vs Cubic retransmits vs buffer | The header prints "1e6" twice; the second is probably 1e7 |

## 6. Maths

Background: percentages, BDP, the token bucket. All maths here is reproducible by the learner.

| # | Item | Page | Notes |
|---|---|---|---|
| E1 | GpGain = (goodput_BBR − goodput_Cubic)/goodput_Cubic × 100 | 133 | Trivial. Note the asymmetry: +115% and −34% are not mirror images |
| E2 | LatDec = (latency_Cubic − latency_BBR)/latency_Cubic × 100 | 133 | Latency means flow completion time |
| E3 | **pacing_gain × BW × (1 − p) = BW ⇒ p* = 1 − 1/pacing_gain**; 1.1 → 9.1%, 1.25 → 20%, 1.5 → 33.3% | 134 | **The one to reproduce.** Fixed-point reading: with random loss, the max-filter sample during the probe phase is g(1−p)·BW. If g(1−p) < 1, every cycle's maximum falls below the current estimate, the filter ages out, and the estimate decays geometrically. The CACM paper says the same thing qualitatively (09b p65). The text writes "pacing_rate × BW" where it means pacing_gain |
| E4 | BDP examples: 500 Mbps × 100 ms = 6.25 MB | 133 | Extend it: 500 Mbps × 200 ms = 12.5 MB (a 100 KB buffer is 0.8% of BDP); 1 Gbps × 20 ms = 2.5 MB (the Fig 8 crossover at about 5 MB ≈ 2·BDP) |
| E5 | Argument: "BBR maintains 2 × BDP in flight, so BDP is queued" | 133 | **Critique it.** 2×BDP is the cwnd *cap*. A single BBRv1 flow pacing at gain 1 holds about 1 BDP. The cap binds when BtlBw is overestimated (several flows, ACK aggregation): see Hock et al. [30] and 09b Fig 5. In shallow buffers, losses also come from Startup (2.89× gain) and from every 1.25 phase, whose +0.25 BDP excess (3.1 MB at 12.5 MB BDP) dwarfs a 100 KB buffer. That is my analysis |
| E6 | Decision-tree statistics: Gini impurity, 75/25 split, 5-fold CV | 132–133 | Background only. Root samples = 222 does not equal 75% of 640 = 480, and the paper does not explain the gap |

## 7. Numbers worth reusing

- **Grid** (p132): 8 RTTs {5, 10, 25, 50, 75, 100, 150, 200 ms} × 8 BWs {10, 20, 50, 100, 250, 500, 750, 1000 Mbps} × 5 buffers {0.1, 1, 10, 20, 50 MB} = 640 configurations, each run 5 times × 60 s with iPerf3.
- **Testbeds:** Mininet/LAN minimum RTT 40 µs (p131). WAN Stony Brook → Rutgers minimum RTT 7 ms with 1 Gbps NICs (p132). The router is a Linksys WRT1900ACS running OpenWRT (p132). TCP rmem/wmem were set to 2³¹−1 (p132).
- **Fig 5(a), 100 KB buffer:** +115 (500 Mbps/200 ms), +90 (500/150), +91 (250/200), +60 (250/150). Near 0 at ≤ 50 Mbps.
- **Fig 5(b), 10 MB buffer:** Cubic wins up to −34 (10 Mbps/200 ms) and −33 (20/150). BBR still wins at 1 Gbps (+13…+24).
- **Retransmits** (25 ms, 500 Mbps, 100 KB → 10 MB): BBR 235,798 → 0; Cubic 1,649 → 471 (p133). Average loss: 10.1% vs 0.9% (100 KB); 0.8% vs 1.3% (10 MB).
- **Fig 7** (100 Mbps/25 ms/10 MB): Reno and Cubic are already down to about 20 Mbps or less at the first non-zero loss points (about 1%). BBR holds about 93–95 Mbps to roughly 18% and collapses by about 25%. BBR_1.1 still shows about 84 Mbps near 11% and has collapsed by about 18%. The sample points are coarse, so the "≈ 9%" in the text is not directly resolved by the plot. BBR_1.5 tracks BBR.
- **Fig 8 / Table 1** (1 Gbps/20 ms): 10 KB → BBR 94%. About 5 MB → even. 10 MB → Cubic 3×. At 100 KB: BBR 305,029 vs Cubic 1,398 retransmits (218×, quoted as "200×"). WAN bottleneck buffer about 20 KB; BBR retransmits about 500 packets/min.
- **Policer threshold in code:** 50/256 = 19.53%, almost exactly the predicted 20% cliff for gain 1.25.

## 8. Linux mapping (v7.2 tree; lines verified by grep; v4.15 compared with `git show v4.15:net/ipv4/tcp_bbr.c`)

| Paper knob/claim | Code | Location |
|---|---|---|
| "maximum pacing_gain 1.25" (BBR_1.1 / 1.5 edit this) | `bbr_pacing_gain[0] = BBR_UNIT * 5 / 4` | net/ipv4/tcp_bbr.c:164 (v4.15: :147) |
| 0.75 drain slot | `BBR_UNIT * 3 / 4` | :165 |
| "2× multiplier" | `bbr_cwnd_gain = BBR_UNIT * 2` | :161 |
| "> 20% loss = policing" | `bbr_lt_loss_thresh = 50` (out of 256, so 19.5%); test `(lost << BBR_SCALE) < bbr_lt_loss_thresh * delivered` at :743. Policing also requires 2 consecutive intervals of 4–16 rounds with consistent bw (≤ 1/8 or ≤ 4 kbit/s apart; :186-192). When it triggers, `lt_use_bw = 1` and `pacing_gain = BBR_UNIT` (:672-673; also :1002-1004) for 48 rounds (:194) | :188, `bbr_lt_bw_sampling` :689, `bbr_lt_bw_interval_done` :659 |
| "BBR does not actively react to packet losses" | Mostly true of the *model*, not of cwnd. Losses are subtracted from cwnd (`if (rs->losses > 0)` :493). The first recovery round uses packet conservation (`bbr_set_cwnd_to_recover_or_restore` :481). The 1.25 phase ends early on loss (:581) | |
| Startup aggressiveness behind shallow-buffer loss | `bbr_high_gain` 2.885 for pacing and cwnd | :155, `bbr_update_gains` :988 |
| Cliff mechanism (max-filter decay) | `bbr_update_bw` :762 → `minmax_running_max` over `bbr_bw_rtts` = 10 rounds (:134, :801) | |
| "Linux 4.15 … TCP layer can handle the pacing … fq is not needed" | Internal pacing since v4.13 (218af599fa63). `bbr_init` sets SK_PACING_NEEDED (:1079); `tcp_pacing_check` net/ipv4/tcp_output.c:2815 | |
| "do not set network parameters on end hosts … negative interaction with TCP Small Queues" | TSQ `tcp_small_queue_check` tcp_output.c:2857 (limit derived from `sk_pacing_rate >> sk_pacing_shift`) | |
| TC-tbf buffer = "qdisc length" | `struct tbf_sched_data.limit` "Maximal length of backlog: bytes" | net/sched/sch_tbf.c:100 |

**v4.15 vs v7.2.** The constants match: pacing_gain[], cwnd_gain 2, high_gain 2885, bw_rtts 10, min_rtt 10 s, ProbeRTT 200 ms, lt_loss_thresh 50. Later fixes and features are **not** in the paper's kernel:
- the lt_bw unity-pacing-gain fix (3aff3b4b986e, v4.16)
- skipping delayed-ACK RTTs for min_rtt (e42866031ff0, v4.16)
- ssthresh = BDP at Startup exit (53794570049d, v4.17)
- EDT pacing (v4.20)
- the 1% pacing margin (v4.20 era)
- ACK-aggregation cwnd (78dc70ebaa38, v5.1)
- the quantization fix (6b3656a60f20, v5.4)
- the PROBE_RTT postponement fix (1b9e2a8c99a5, v5.10)

So the qualitative v1 findings should carry over to the learner's 7.2.6 kernel, but exact numbers may differ (unverified). Upstream v7.2 is still BBRv1: no inflight_hi/lo and no ECN in tcp_bbr.c.

**ss/tc correlates for this paper's symptoms:**
- Shallow-buffer BBR shows high `retrans:` / `bytes_retrans` in `ss -ti` and `dropped` on the bottleneck in `tc -s qdisc`, while `bbr:(bw:…)` stays near link rate.
- Policer mode shows `pacing_gain:1`, `cwnd_gain:2` held with no 1.25/0.75 alternation, with `bw` ≈ the long-term average.
- Past the cliff, `bw` decays while `retrans` falls.

## 9. Prerequisites and forward references

**Assumed:**
- BBR basics (it summarizes paper 09 in one page)
- Reno/Cubic/Vegas/DCTCP at a sentence level
- tc tbf/netem, TSQ (cited via LWN), Mininet
- decision trees and Gini impurity
- iPerf3

**Forward references:**
- the "Limitations" section's "ongoing work" on BBR's design flaws (p135)
- BBRv2 IETF 104/105 slides [9, 10] as "online discussion about addressing unfairness"
- the delivery-rate estimation draft [3]

**Not covered:** RTT/queue measurements, more than 2 flows, RTT-unfairness (it cites Ma et al. [34]), ECN, fq-based AQM at the bottleneck.

## 10. References worth reading (from its list)

1. **[30] Hock, Bless, Zitterbart, "Experimental evaluation of BBR congestion control," ICNP 2017.** The mechanistic explanation this paper lacks. Multiple BBR flows overestimate bandwidth, become cwnd-limited at 2×BDP and keep about 1 BDP of standing queue; it also covers shallow vs deep buffer sharing with Cubic.
2. **[3] Cheng et al., "Delivery Rate Estimation," draft-cheng-iccrg-delivery-rate-estimation (2017).** The spec of the rate sampler (send/ACK phase, app-limited marking), now in tcp_input.c / tcp_output.c.
3. **[9]/[10] "BBR v2: A Model-based Congestion Control," IETF 104 and 105 ICCRG slides (2019).** What Google changed in response to exactly these issues (loss/ECN response, coexistence). This is the bridge to v2/v3.
4. **[37] Scholz et al., "Towards a deeper understanding of TCP BBR congestion control," IFIP Networking 2018.** An independent measurement of BBR's loss, fairness and RTT behavior, useful as a cross-check.

## 11. Spine and strands

**Recommendation: merge.** Make this paper a final section of the BBR chapter, "Where BBRv1 loses", about 25–35% of the chapter. It should not be its own chapter.

**Section spine:**
1. Claim map: winner = f(buffer/BDP). Redraw Fig 5 with buffer/BDP on the x-axis.
2. Shallow buffers: BBR gains goodput and pays in retransmits. Their 2×BDP argument, then the better account: Startup, the 1.25 probe excess vs buffer, the cwnd cap only under overestimation.
3. The loss cliff: Eq (3), validated by BBR_1.1, plus the policer confound (19.5% threshold).
4. Coexistence with Cubic: crossover near 2×BDP in Mininet; a shallow 20 KB buffer in the wild.
5. Method lessons: shape on a middle router (TSQ), kernel version matters (4.15), "latency" means FCT, the decision tree is weak.
6. What changed after (v2/v3): unverified pointer only.

**Strands:**
- `buffer-over-bdp-decides`: Whether BBRv1 or Cubic gets more goodput, and who wins when they share, is governed mainly by bottleneck buffer relative to BDP: BBR wins when buffer ≪ BDP, Cubic when buffer ≫ BDP. (pp131, 133–135)
- `loss-cliff-1-minus-1-over-g`: BBRv1's goodput collapses near random loss p* = 1 − 1/g_max (20% for g = 1.25), because the probe phase can no longer deliver ≥ BtlBw. (p134)
- `cliff-policer-confound`: The default 20% cliff coincides with tcp_bbr's policer threshold 50/256 ≈ 19.5%, so Eq (3) alone does not prove the mechanism; BBR_1.1 is the cleaner evidence. (p134 + code)
- `shallow-buffer-retransmits`: In shallow buffers BBRv1 keeps losing, often 10× to over 200× Cubic's retransmits, because its model ignores loss while Cubic backs off. (pp133, 135)
- `cwnd-cap-not-operating-point`: cwnd_gain = 2 is a cap; a single BBRv1 flow pacing at 1.0 × BtlBw holds about 1 BDP. A ≈1 BDP standing queue appears only when BtlBw is overestimated. (critique of p133; 09b p66)
- `shape-on-the-router`: Emulating a bottleneck with tc on the sending host interacts with TSQ/pacing; put tbf/netem on a separate router hop. (p132)

## 12. Exercise ideas (none needs iperf3; the paper used iPerf3, and Python sockets replace it)

1. **Pen and paper, 30 min: cliffs and buffer/BDP.**
   - Compute p* for g = 1.1, 1.25, 1.5 and set each against the 19.5% lt_bw threshold. Predict which mechanism fires first for each gain and explain the BBR_1.5 curve in Fig 7(a).
   - For the Fig 5 grid, compute BDP per cell and buffer/BDP for 100 KB and 10 MB, then shade cells by log(buffer/BDP). Does the sign of GpGain follow it? Where are the exceptions (10 MB at 1 Gbps)?
   - Size the probe excess 0.25·BDP against 100 KB for 500 Mbps/200 ms.
   - Critique the decision tree: RTT splits that don't change class, root n = 222.
2. **Lab, 45–60 min: loss sweep (Fig 7 at laptop scale).**
   - Three netns `snd—rtr—rcv`.
   - rtr egress toward rcv: root `netem loss P%` with a child `tbf rate 100mbit burst 32k limit 1mb`. Check the tree with `tc -s qdisc`.
   - rcv egress (ACK path): `netem delay 25ms`.
   - Run `sudo modprobe tcp_bbr` once.
   - Python sender with `TCP_CONGESTION` = bbr or cubic, 20 s per point, P ∈ {0, 1, 2, 5, 10, 15, 18, 19, 20, 21, 22, 25, 30}. The receiver counts bytes.
   - Sample `TCP_CC_INFO` every 5 ms. Above about 19.5%, look for pacing_gain pinned at 1.0 for long stretches (lt_bw mode) vs the 1.25/0.75 alternation. This is how the learner separates the two cliff mechanisms without rebuilding the module.
3. **Lab, 60 min: coexistence vs buffer (Fig 8a, scaled).**
   - 100 mbit / 20 ms (BDP 250 KB). One BBR and one Cubic Python flow for 30 s per point.
   - tbf `limit` ∈ {10 KB, 50 KB, 125 KB, 250 KB, 500 KB, 1 MB, 2.5 MB}.
   - Predict the crossover (paper's Mininet: about 2·BDP) before running.
   - Log per-flow goodput, `tcpi_total_retrans`, and `tc -s qdisc` drops/backlog. Compare retransmit ratios with Table 1.
4. **Optional, 30 min:** repeat exercise 3 with `fq` vs `fq_codel` vs `codel` as the *bottleneck* qdisc (tbf child) to see how AQM/FQ at the bottleneck changes Cubic's deep-buffer advantage. This is beyond the paper and connects to the CoDel/fq links of the chain.

## 13. Honest assessment

**Read closely:**
- §4.2 (p134), the cliff equation and its validation
- §4.1.2 (p133), the shallow/deep heatmaps and retransmit numbers
- §4.3 (pp134–135), coexistence vs buffer, including the WAN 20 KB observation
- §3.2 (p132), testbed hygiene

**Skim:**
- Abstract/Intro/Background (they restate paper 09, with errors: "Bandwidth Bottleneck and Round-trip…" on p130)
- the decision tree §4.1.1
- Related work and limitations

**Weaknesses to teach explicitly:**
1. Queue size is never measured, yet the abstract claims "large queue sizes".
2. The 2×BDP explanation treats a cap as an operating point.
3. "Decreasing the 2× multiplier lowers losses" (p131) is asserted with no data.
4. The default-gain cliff is confounded with the 19.5% policer detector.
5. The tree is weak: its RTT splits don't change the class, it effectively reduces to "1 Gbps → BBR; ≤ 250 Mbps → Cubic; 500–750 Mbps → BBR iff buffer ≤ 5.5 MB", and the sample counts are unexplained.
6. "Latency" means FCT.
7. There are at most 2 flows and a dumbbell topology.
8. It ran Linux 4.15, before several BBRv1 fixes.

**Likely BBRv1-specific findings.** All of these are unverified; I have no source in hand for v2/v3 behavior.
- The high shallow-buffer retransmission rate. BBRv2/v3 reportedly bound inflight using a loss-rate threshold (~2%) and ECN.
- The 20% random-loss cliff. A loss-responsive v2/v3 would likely back off at much lower loss, trading the cliff for a smoother decline.
- The lt_bw policer mode, reportedly replaced in v2.
- Strong shallow-buffer unfairness to Cubic.

**Likely durable:**
- buffer/BDP as the governing variable for model-based vs loss-based coexistence
- loss-based flows dominating very deep unmanaged buffers (09b p66 already concedes this)
- the testbed-hygiene lessons

**Keep or merge:** merge into the BBR chapter as its closing "limits" section. As a full chapter it would be thin: one equation, one mechanism, several soft conclusions. Its best value is the cliff equation, the buffer/BDP framing and a ready-made lab design.
