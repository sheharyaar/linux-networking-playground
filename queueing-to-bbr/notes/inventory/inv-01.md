# Inventory 01 — Jacobson, "Congestion Avoidance and Control" (SIGCOMM '88, CCR reprint)

## 1. Facts

- **Citation (original):** Van Jacobson (ideas developed with Michael J. Karels, credited in fn 1, p.158). "Congestion Avoidance and Control." *Proc. ACM SIGCOMM '88*, Stanford, CA, August 1988; *Computer Communication Review* 18(4). The cover page of this PDF prints "Originally Published in: Proc. SIGCOMM '88, Vol 18 No. 4, August 1988" (p.157).
  - Original page range 314–329 is from memory, **not printed in this PDF**. It fits the kernel comment "SIGCOMM '88, p. 328" for Appendix B (`net/ipv4/tcp_cong.c:493-494`). Appendix B's code sits on reprint p.172, and 172 + 156 = 328. So the reprint appears to be a facsimile with renumbered folios: original page = reprint page + 156. That is inferred, not checked against the 1988 printing.
- **This PDF:** an ACM SIGCOMM *Computer Communication Review* reprint. Every folio reads "ACM SIGCOMM -NNN- Computer Communication Review". The pages don't print the reprint's volume or issue. CCR 25(1), Jan 1995 (25th-anniversary reprint issue) is a guess and is **unverified**.
- **PDF page count:** 17 (pdfinfo). Scanned and OCR'd (Ghostscript 9.53). The extracted text garbles equations and figures, so use the rendered pages.
- **Printed page numbers:** yes, centred in the footer as "-157-" … "-173-".
- **Printed range:** pp. 157–173. PDF p.1 is a cover sheet (p.157). The paper itself runs pp.158–173.
- **Offset:** printed = PDF + 156. Checked on the rendered pages: PDF 1 → "-157-", PDF 2 → "-158-", PDF 3 → "-159-", PDF 4 → "-160-", PDF 13 → "-169-", PDF 17 → "-173-".

## 2. Sections (printed pages)

| Section | Pages |
|---|---|
| Cover sheet ("Originally published in…") | 157 |
| Untitled intro: the Oct '86 collapse, algorithms (i)–(vii), conservation of packets, three ways it fails | 158 |
| 1 Getting to Equilibrium: Slow-start | 158–160 |
| 2 Conservation at equilibrium: round-trip timing | 160–162 |
| 3 Adapting to the path: congestion avoidance | 162–165 |
| 4 Future work: the gateway side of congestion control | 165–166 |
| Acknowledgements | 166–167 |
| Appendix A: A fast algorithm for rtt mean and variation (A.1 Theory 167–169; A.2 Practice 169–171) | 167–171 |
| Appendix B: The combined slow-start with congestion avoidance algorithm | 171–172 |
| Appendix C: Window Adjustment Policy | 172 |
| References (17 entries) | 173 |

Much of the content sits in footnotes. These matter: fn 8 (p.164), fn 9 (p.164), fn 10 (p.165), fn 11 (p.165), fn 13 (p.166), fn 15–17 (pp.169–170).

## 3. Terms introduced

1. **Congestion collapse**: throughput falls by orders of magnitude because the network is busy carrying useless retransmissions. Used on p.158. Fn 5 (p.162) credits the term to Nagle [Nag84] and describes it as "positive feedback instability due to poor retransmit timers".
2. **Conservation of packets / equilibrium**: with a full window in flight, a new packet enters the network only when an old one leaves. p.158.
3. **Self-clocking (ack clock)**: acks arrive at the bottleneck's packet spacing, so a sender that transmits only on acks automatically sends at the bottleneck rate. pp.158–159, Fig 1 (p.159).
4. **Bottleneck (P_b)**: the slowest link on the path. P_b is its minimum packet spacing. Fig 1 caption, p.159.
5. **Congestion window (cwnd)**: per-connection sender state. The sender transmits min(receiver window, cwnd). p.159.
6. **Slow-start**: start cwnd at 1 and add 1 per ack, which doubles the window every RTT. p.159. Its cost is given on p.160.
7. **Load ρ and RTT variation σ_R**: ρ is the arrival rate divided by the departure rate. Both R and σ_R scale like (1−ρ)^−1. pp.160–161.
8. **rto, β**: the retransmit timeout. RFC 793 sets rto = βR with β = 2. p.161.
9. **Exponential (retransmit timer) backoff**: double the timer on each retransmission of the same packet. p.162 (with a linear-system argument).
10. **Congestion avoidance**: an endpoint policy that cuts load when the network signals congestion and probes for more when it doesn't. p.163.
11. **Multiplicative decrease**: W_i = d·W_{i−1} with d < 1. p.164.
12. **Additive increase (AIMD)**: W_i = W_{i−1} + u with u ≪ W_max. In practice this is cwnd += 1/cwnd per ack. p.165.
13. **Pipesize (W_max)**: the path's delay-bandwidth product minus protocol overhead, i.e. the largest sensible window on an unloaded path. p.165 (also fn 9, p.164).
14. **Mean deviation (mdev, D)**: the average of |M − A|, used as a cheap substitute for the standard deviation. p.169.
15. **ssthresh**: the threshold that switches from slow-start to congestion avoidance. It is set to half the window on timeout. p.171.

(The paper also uses "knee" and "cliff" from [JRC87] on p.172, and "recursive prediction error / stochastic gradient" estimators on p.167.)

## 4. Core claims

1. In October '86, LBL→UC Berkeley throughput fell from 32 kbps to 40 bps, about a factor of a thousand. p.158.
2. Packet conservation can fail in only three ways: the connection never reaches equilibrium, the sender injects before a packet leaves, or path resource limits prevent equilibrium. p.158.
3. An ack-clocked sender's packet spacing exactly matches the packet time on the slowest link, because ack spacing preserves the bottleneck spacing. Fig 1, p.159.
4. Slow-start opens the window in R·log₂W. It needs W/2 packets of bottleneck buffer and never sources data faster than twice the path's maximum. pp.159–160 (Fig 2 caption, p.160).
5. A good RTT estimator is "the single most important feature" of a protocol that must survive heavy load. RFC 793's fixed β = 2 copes only with loads up to about 30%, and above that it retransmits packets that were merely delayed. pp.160–161.
6. Exponential backoff is the only retransmit spacing that works. The paper argues this by analogy: the network is roughly a linear system, and linear systems are stabilised by exponential damping. p.162.
7. Damage loss is rare (≪1%) on most paths, so a timeout signals congestion, and every existing network delivers that signal for free. p.163.
8. Under congestion, queues grow geometrically (L_n = γⁿL₀), so sources must back off at least that fast: multiplicative decrease. p.164.
9. Increase should be small and additive (+1 packet per RTT). Multiplicative increase oscillates because "it is easy to drive the net into saturation but hard for the net to recover". pp.164–165.
10. A window larger than the pipesize builds a standing queue at the bottleneck that cannot shrink, however carefully the sender clocks. Fn 9, p.164. This is the seed of CoDel (paper 02).
11. Endpoints can keep network capacity from being exceeded, but they can't make sharing fair. Only gateways have the information to do that, so gateway congestion detection is "the next big step". pp.165–166.

## 5. Figures and examples worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| 1 Window Flow Control 'Self-clocking' | 159 | The pipe/funnel diagram: packets stretch in time at the bottleneck (P_b). The ack spacing A_r = A_b = A_s = P_b is preserved on the return path. | The single most reused picture in the field. CoDel's Figs 1–2 (paper 02, p.44) redraw it. It underlies pacing and BBR (BtlBw = 1/P_b). **Redraw it.** |
| 2 Chronology of a Slow-start | 160 | Time in one-RTT rows (0R–3R). Each ack releases two packets, which stack at the bottleneck. | Shows exponential growth and the W/2 burst buffer demand. Pacing and TSQ later fix this burstiness. **Redraw it** (animate per RTT). |
| 3 / 4 Startup without / with slow-start | 161 / 162 | Sequence-vs-time traces over a 230.4 kbps link. Without slow-start, 35% of 20 KBps is used and some data is sent 5×. With slow-start the slope is 20 KBps and the 2 s ramp averages 16 KBps. | Before/after evidence. Worth a schematic, not a re-plot. |
| 5 / 6 RFC 793 vs Mean+Variance timer | 163 / 164 | Per-packet RTT on the Arpanet (2–10 s) against the timer line. The RFC 793 timer cuts through the samples (spurious retransmits); the A+2D timer tracks them. | Motivates estimating variance. Easy to reproduce from synthetic data in numpy. |
| 7 Multiple-conversation test setup | 166 | 4 LBL Suns → 4 UCB hosts via csam–cartan, a 230.4 kbps microwave link, with a 50-packet queue and 16 KB (32-packet) windows. | **The paper's canonical topology. Use it as the spine.** It maps onto a 3-netns veth lab. |
| 8 / 9 Four TCPs without / with congestion avoidance | 167 / 168 | Without CA: 4000 of 11000 packets retransmitted, shares of 8/5/5/0.5 KBps. With CA: 89 of 8281 retransmitted (1%), 8/8/4.5/4.5 KBps. The gap comes from delayed-ack receivers (bursts of 5–7). | Fairness, and burstiness from ack policy. The fig 9 caption is an early argument against bursty acks. |
| 10 / 11 Total / effective bandwidth | 169 / 170 | Old TCPs offer 125% of link capacity but deliver only 75% goodput. New TCPs show ~20 s of damped oscillation, then run at link rate. | Offered load versus goodput, which is the essence of collapse. |
| 12 Window adjustment detail | 171 | Throughput in 3 s bins. Loss spikes give the window size, which decays exponentially with a fitted τ = 28 s ("~4 s with a gateway drop algorithm"). | Lets you read the window off loss events, like reading cwnd from `ss -ti`. |

## 6. Maths

Background assumed across the paper: EWMA/low-pass filters, basic queueing (ρ, M/M/1-style 1/(1−ρ)), difference equations, and linear-system stability (asserted, not used).

| # | Item | Page | Reproduce? |
|---|---|---|---|
| M1 | Slow-start time **R·log₂W**. Bottleneck burst demand **W/2** packets. Rate ≤ 2× path max. | 160 (+Fig 2) | **Yes, core.** Example: W = 32 gives 5 RTTs and 16 buffers. |
| M2 | Without slow-start: a 10 Mbps Ethernet into a 56 kbps Arpanet gives a burst of 8 packets at "200×" the path rate (10e6/56e3 ≈ 179). | 160 | Yes (one line). |
| M3 | R and σ_R scale like **(1−ρ)^−1**. At ρ = 0.75 the RTT varies "by a factor of sixteen (±2σ)". | 161 | State and use. The ×16 is **asserted**; the arithmetic isn't shown. |
| M4 | RFC 793: **R ← αR + (1−α)M** (α = 0.9), **rto = βR** (β = 2). "β = 2 adapts to loads ≤ 30%". | 161 | Reproduce the filter. The 30% figure is asserted. |
| M5 | Load model: **L_i = N** (uncongested), **L_i = N + γL_{i−1}**, then L_n = γⁿL₀ (fn 8). Explodes for γ > 1. | 163–164 | **Yes.** Two-line difference equation. It motivates MD. |
| M6 | **W_i = dW_{i−1}** (d < 1, MD). MI candidate W_i = bW_{i−1}, 1 < b ≤ 1/d, is rejected. **W_i = W_{i−1} + u** (u ≪ W_max). d = 0.5, u = 1. | 164–165 | **Yes.** |
| M7 | Queue clearing time scales like **(1−ρ)^−2** (fn 9, citing Kleinrock ch. 2). Regeneration time (1−ρ)^−1 with variance (1−ρ)^−3 (fn 13). | 164, 166 | State only. |
| M8 | Per-ack AI increment **1/cwnd** (packets), which is **maxseg·maxseg/cwnd** in bytes. A window of cwnd packets yields ≤ cwnd acks per R, so the window grows ≤ 1 packet per R (fn 10). | 165 | **Yes, core.** Maps to `tcp_cong_avoid_ai`. |
| M9 | Rate-based variant (fn 11): decrementing the interval, 1/I → 1/(I−c), is non-linear and destabilising. A linear rate increase uses **I_i = αI_{i−1}/(α + I_{i−1})**. | 165 | **Good toggle.** Show that 1/I_i = 1/I_{i−1} + 1/α, so the rate rises by a constant 1/α per packet. This is the bridge to pacing. |
| M10 | Estimator: **A ← (1−g)A + gM ⇔ A ← A + g(M−A)**. Split the error into random and estimation parts, E_r + E_e. sdev(A) = g·sdev(M). Converges with time constant 1/g. Typical g = 0.1–0.2. | 167–168 | **Yes.** |
| M11 | **mdev² = (Σ\|M−A\|)² ≥ Σ\|M−A\|² = σ²**, claimed to show "mdev is the more conservative (larger) estimate". For normal errors the paper writes "mdev = √(π/2)·sdev (≈1.25)". | 169 | **Use as an error-spotting exercise.** With proper 1/n normalisation, Cauchy–Schwarz gives mdev ≤ sdev (fn 15 says eliding n "makes no difference", but it does). For normal errors mdev = √(2/π)·sdev ≈ 0.80·sdev, so the 1.25 is sdev/mdev. Hence rto = A+2D ≈ A+1.6σ, one reason the later A+4D is safer. (Standard result; this note is mine, not the paper's.) |
| M12 | **Err = M−A; A ← A + g·Err; D ← D + g(\|Err\|−D)**. Scaled by 2ⁿ: 2ⁿA ← 2ⁿA + Err, 2ⁿD ← 2ⁿD + (\|Err\|−D). C code with SA = 8A and SD = 4D (gains 1/8 and 1/4). | 169–171 | **Yes, core.** Then show that `rto = ((SA>>2)+SD)>>1` equals A + 2D, because (2A + 4D)/2 = A + 2D. |
| M13 | Rounding: a ½-tick bias each in SA and SD gives a 1.5-tick bias = ½-tick rounding + 1-tick phase correction. | 171 | Skim. |
| M14 | Appendix B: `if (cwnd < ssthresh) cwnd += 1; else cwnd += 1/cwnd;`. On timeout, ssthresh = W/2 and cwnd = 1. | 171–172 | **Yes, core.** |
| M15 | Appendix C: halve because you now probably share with one new conversation (ρ ≤ 0.5). With AI there are **O(w²) packets between drops**. Arpanet windows of 8–12 packets mean 1-packet increments give ~1% drops. | 172 | **Toggle derivation.** The sawtooth runs w/2 → w over w/2 RTTs and sends ≈ 3w²/8 packets per drop, so p ≈ 8/(3w²). That gives w = 8 → 4.2%, w = 12 → 1.9%, w = 16 → 1.0%, the same order as the paper's claim. Rearranged: rate ≈ (MSS/RTT)·√(3/(2p)), i.e. Mathis et al. 1997 (cited by paper 02 [16]). |
| M16 | Fig 7 arithmetic: 4 × 32 = 128 packets offered against a 50-packet queue gives "+160%" (actually 156%). | 166 | Yes (warm-up). |

A learner should be able to reproduce **M1, M5, M6, M8, M9, M12, M14 and M15**.

## 7. Numbers worth reusing

- **Collapse:** 32 kbps → 40 bps, LBL–UCB, 400 yards, 3 IMP hops (p.158).
- **TCP's dynamic range:** 800 Mbps Cray channels to 1200 bps packet radio (p.159).
- **Burst:** 10 Mbps Ethernet → 56 kbps Arpanet gives 8 packets at ~200× (p.160).
- **Timers:** ρ = 0.75 → RTT varies ×16; α = 0.9, β = 2; β = 2 copes only up to ~30% load (p.161). Gains g = 1/8 (A) and 1/4 (D); rto = A + 2D (pp.170–171).
- **Damage loss:** ≪ 1%. The scheme is insensitive up to ~1 packet per window (12–15% for an 8-packet window). 12% loss costs about 60% of throughput (fn 6, p.163).
- **Fig 1 standing-queue example (fn 9, p.164):** pipesize 16 packets (8 each way), window 22, so 6 packets queue permanently.
- **Constants:** d = 0.5, u = 1 (p.165). [JRC87] used d = 7/8 (p.172).
- **Era limits:** Arpanet IMP allows ≤ 8 packets in transit per gateway pair. The 4.3BSD default window is 8 packets (4 KB) (p.165).
- **Fig 3/4 testbed:** Sun 3/50s, 230.4 kbps point-to-point link, 512-byte data packets. 20 KBps available; 35% used without slow-start; 16 KBps for the first 2 s with slow-start (19 KBps over a minute); 7 KBps without (pp.161–162).
- **Fig 7:** 4 pairs, 1 MB transfers (2048 × 512 B) started 3 s apart, 50-packet microwave-link queue, 16 KB windows (p.166). Derived (mine): a 552-byte packet takes ≈ 19.2 ms at 230.4 kbps, so a full 50-packet queue holds ≈ 0.96 s.
- **Fig 8/9:** 25 KBps link data rate, fair share ≈ 6 KBps each. Delayed-ack receivers waited for 35% of the window or 200 ms, producing bursts of 5–7 packets and a loss rate of 1.8% versus 0.5% (pp.167–168).
- **Fig 12:** window decay τ = 28 s, against ~4 s expected with a gateway drop algorithm (p.171).
- **Appendix C:** windows converged to 8–12 packets; unloaded Arpanet pipe is 4–5 packets; the increment should be ~4× smaller (p.172).
- **Modern companions (Linux v7.2):**
  - TCP_INIT_CWND = 10 (`include/net/tcp.h:269`).
  - TCP_RTO_MIN = HZ/5 = 200 ms (`tcp.h:162`); TCP_TIMEOUT_INIT = 1 s (`tcp.h:167`); TCP_RTO_MAX = 120 s (`tcp.h:160-161`).
  - Delayed ACK between 40 ms (`tcp.h:154`) and 200 ms (`tcp.h:150`).
  - CUBIC β = 717/1024 ≈ 0.7 (`net/ipv4/tcp_cubic.c:50`).
  - Live host: HZ = 1000; `ss -ti` showed `rto:203 rtt:2.625/0.593` and `rto:206 rtt:5.795/1.237`. Both match rto = srtt + 200 ms, because 4·rttvar is below the floor.
- **Worked-example seeds:**
  - 100 Mbps × 50 ms with 1448-byte MSS: BDP ≈ 432 packets. Slow-start from 1 takes log₂432 ≈ 8.75 RTTs; from IW10 it takes ≈ 5.4 RTTs.
  - 10 Mbps × 40 ms: BDP ≈ 34.5 packets.
  - Mathis: 1448 B, 50 ms, p = 10⁻⁴ gives ≈ 28.4 Mbps.

## 8. Linux mapping (v7.2 tree, grep-verified)

**Slow-start and AIMD (Reno)**

- `net/ipv4/tcp_cong.c:456`: `tcp_slow_start()`. Adds `acked` to cwnd up to ssthresh. The comment at :447–455 explains stretch ACKs and ABC, which differ from the paper's per-ack +1.
- `net/ipv4/tcp_cong.c:467-487`: `tcp_cong_avoid_ai()`. Comment at :467: "In theory this is tp->snd_cwnd += 1 / tp->snd_cwnd". Implemented as an integer counter, `snd_cwnd_cnt`.
- `net/ipv4/tcp_cong.c:493-510`: `tcp_reno_cong_avoid()`. Comment: "This is Jacobson's slow start and congestion avoidance. SIGCOMM '88, p. 328." It returns early if not cwnd-limited.
- `net/ipv4/tcp_cong.c:514-520`: `tcp_reno_ssthresh()` = max(cwnd>>1, 2). This is d = 0.5.
- `net/ipv4/tcp_cong.c:531`: `struct tcp_congestion_ops tcp_reno`.
- `include/net/tcp.h:1529`: `tcp_in_slow_start()` = cwnd < ssthresh. Same test as Appendix B.
- `net/ipv4/tcp_input.c:3858`: `tcp_cong_control()`. Dispatches to the `cong_control` hook if the CA module has one (BBR does). Otherwise it runs PRR reduction or `tcp_cong_avoid()` (:3513). **This is the fork point between AIMD and BBR in the learner's chain.**
- `net/ipv4/tcp_cubic.c:50`: β = 717/1024 (today's default CC; the live host confirms `cubic`).

**Timeout and loss**

- `net/ipv4/tcp_input.c:2554`: `tcp_enter_loss()`. Sets ssthresh via `ca_ops->ssthresh` (:2570) and cwnd = in_flight + 1 (:2574). This is the paper's "on timeout: ssthresh = W/2, cwnd = 1".
- `net/ipv4/tcp_input.c:2971, 2985`: `tcp_init_cwnd_reduction()` / `tcp_cwnd_reduction()`. Proportional Rate Reduction (RFC 6937), the modern packet-conservation-during-recovery rule. The tracepoint `trace_tcp_cwnd_reduction_tp` (:2994) is declared at `include/trace/events/tcp.h:359`.
- Fast retransmit, the paper's (vii): `tcp_fastretrans_alert()` (`tcp_input.c:3328`). In v7.2, `tcp_time_to_recover()` (:2717) only checks `lost_out`, so loss marking is done by RACK (`net/ipv4/tcp_recovery.c:95` `tcp_rack_mark_lost()`).

**RTT estimation and RTO (Appendix A)**

- `net/ipv4/tcp_input.c:1070-1136`: `tcp_rtt_estimator()`. Comments cite "Jacobson's article in SIGCOMM '88" and "On a 1990 paper the rto value is changed to: RTO = rtt + 4 * mdev" (:1082-1083). It is the same shift code as p.171: `m -= (srtt>>3); srtt += m` ("rtt = 7/8 rtt + 1/8 new", :1094) and `mdev += m - mdev>>2` ("3/4 … 1/4", :1111).
- The Linux additions to that function:
  - An Eifel-like smaller gain when RTT falls (:1095-1107).
  - A per-RTT `mdev_max`/`rttvar_us` envelope floored at `tcp_rto_min_us` (:1112-1123).
  - First-sample init `mdev = 2M` ("make sure rto = 3*rtt", :1128-1129).
- `include/net/tcp.h:880-883`: `__tcp_set_rto()` = (srtt_us>>3) + rttvar_us. `tcp_set_rto()` is at `tcp_input.c:1175` and `tcp_bound_rto()` at `tcp.h:875`.
- `net/ipv4/tcp_input.c:3459-3497`: `tcp_ack_update_rtt()`. Karn's rule (paper item vi, [KP87]): no sample when retransmitted data is acked, unless timestamps provide one. It resets `icsk_backoff` only on a valid sample.
- `net/ipv4/tcp_timer.c:537`: `tcp_retransmit_timer()`. Exponential backoff `icsk_backoff++; icsk_rto = min(icsk_rto << 1, tcp_rto_max(sk))` at :683-684, with a linear-timeout exception for thin streams at :669-677. Helper: `include/net/inet_connection_sock.h:254` `inet_csk_rto_backoff()`.

**What `ss -ti` exports**

- `net/ipv4/tcp.c:4297-4298`: `tcpi_rtt = srtt_us>>3`, `tcpi_rttvar = mdev_us>>2`. So `ss` "rtt:A/D" are the paper's A and D.
- `tcp.c:4278` `tcpi_rto`; `:4255` `tcpi_backoff`; `:4238` cwnd; `:4299` ssthresh.

**Other paper items**

- Restart after idle: `net/ipv4/tcp_output.c:160` `tcp_cwnd_restart()` (RFC 2861; halves per idle RTO). Delayed ACK, the paper's (iv): `tcp_output.c:4413` `tcp_send_delayed_ack()` and `tcp_input.c:336` `tcp_in_quickack_mode()`.
- Pacing, the descendant of fn 11: `net/ipv4/tcp_input.c:1138` `tcp_update_pacing_rate()`. Rate = cwnd·mss/srtt × 200% in slow-start or ×120% in CA, with sysctl defaults at `tcp_ipv4.c:3501-3502`.
- Observability: `tracepoint:tcp:tcp_probe` (`include/trace/events/tcp.h:367`, fired at `tcp_input.c:6508`) carries `snd_cwnd`, `ssthresh`, `srtt`, `snd_una`/`snd_nxt`.

## 9. Prerequisites and forward references

**Assumed without definition:**
- Sliding-window flow control and the receiver's advertised window; cumulative ACKs and sequence numbers.
- MSS (`maxseg`) and silly-window avoidance (cites [Cla82]).
- Gateway (router) output queues; IMPs, the Arpanet and Milnet.
- EWMA/low-pass filters, variance, standard deviation.
- Queueing load ρ, "regeneration points", the "rush-hour effect" [Kle76].
- Linear-system stability; Taylor series; ARMAX models.
- Ethernet exponential backoff (fn 4, p.162).
- Delayed acks; ISO TP-4 / Xerox NS SPP; DECbit "congestion experienced" [ISO86, JRC87]; "knee" and "cliff" [JRC87].

**Forward references inside the paper:**
- (vii) fast retransmit, "described in a soon-to-be-published RFC" (p.158).
- "In-progress paper" proofs for backoff (fn 4, p.162), AIMD (p.165) and damage loss (fn 6, p.163).
- A rate-based variant tried with Sun on NFS (fn 11, p.165).
- Gateway congestion detection (§4, pp.165–166), which leads to RED in 1993 and CoDel in 2012 (paper 02).
- A second-order control loop for the increment (p.172).

**Forward links to the learner's chain:**
- Fn 9 (standing queue = window − pipe) → CoDel.
- Fig 2's W/2 burst and Fig 9's delayed-ack bursts → TSQ, fq, pacing.
- Fn 11's rate-based control → pacing, EDT, the BBR pacing rate.
- Pipesize W_max → BDP → BBR's BtlBw × RTprop.
- "Loss ≈ congestion" (p.163) → the assumption BBR abandons.

## 10. References worth reading

1. **[JRC87] Jain, Ramakrishnan, Chiu, DEC-TR-506 (1987).** The source of AIMD, knee/cliff, and the DECbit network signal. Jacobson "copied Jain's scheme" (fn 7). Beyond the list, Chiu & Jain 1989 has the AIMD convergence/fairness proof the paper waves at.
2. **[KP87] Karn & Partridge, SIGCOMM '87.** RTT sampling ambiguity under retransmission (Karn's algorithm). Implemented today in `tcp_ack_update_rtt`.
3. **[Nag84] RFC 896.** Coins "congestion collapse". Short, and still the clearest description of the failure mode.
4. Optional: **[Kle76] Kleinrock vol. II, ch. 2.** The (1−ρ)^−k scalings and the rush-hour effect behind fn 9 and fn 13. Heavy going; read only for the maths toggles.

## 11. Suggested spine and strands

**Spine:** the csam→cartan **230.4 kbps microwave bottleneck with a 50-packet queue** (Fig 7, p.166).
- First one Sun 3/50 connection starts across it (Figs 3–4: collapse without slow-start, clean ramp with it).
- Then four 16 KB-window connections share it (Figs 8–12: collapse vs AIMD convergence).
- Every mechanism in the paper (ack clock, slow-start, RTO, MD/AI) can be narrated as something that happens to packets in that one queue. A 3-netns veth + netem lab reproduces it at modern rates.

**Strands (quizzable claims):**
1. `ack-clock`: in equilibrium an ack-clocked sender transmits at exactly the bottleneck packet rate, because ack spacing preserves P_b (Fig 1, p.159).
2. `slowstart-cost`: slow-start reaches window W in R·log₂W, but each RTT's burst needs up to W/2 bottleneck buffers (p.160).
3. `rto-needs-variance`: a fixed rto = 2R spuriously retransmits once load exceeds ~30%, because RTT variance grows like (1−ρ)^−1. Use rto = A + 2D (paper) or A + 4D with a 200 ms floor (Linux) (pp.161, 170–171).
4. `loss-is-the-signal`: because damage loss is ≪1%, a timeout means congestion, so loss is a free, universal congestion signal (p.163).
5. `md-because-geometric`: congested queues grow like γⁿ, so a stable sender must cut its window multiplicatively (p.164).
6. `ai-not-mi`: probe with +1 packet per RTT (cwnd += 1/cwnd per ack). Multiplicative increase overshoots and oscillates (pp.164–165, fn 10).
7. `window-minus-pipe-queue`: any window above the pipesize sits as a standing queue that the ack clock can never drain (fn 9, p.164). This is the hand-off to CoDel.

## 12. Exercise ideas

1. **Pen and paper, 35 min: the estimator by hand, then check `ss`.**
   - Feed RTT samples (e.g. 100, 100, 100, 300, 100, 100 ms) through A ← A + (M−A)/8 and D ← D + (|Err|−D)/4.
   - Tabulate rto three ways: the paper's A+2D, RFC 6298's A+4D, and Linux's srtt + max(4D, 200 ms) with first-sample init D = M/2.
   - Prove that `((SA>>2)+SD)>>1` = A + 2D.
   - Fix the paper's mdev ≥ sdev claim (M11).
   - Finally take `rtt:x/y` from a live `ss -ti` and predict `rto:` (this host: 2.625 + 200 → 203 ✓). No tools needed beyond `ss`.
2. **Pen and paper, 30 min: Fig 7 and Appendix C arithmetic.**
   - Packet time at 230.4 kbps; the 50-packet queue in seconds; the "+160%"; slow-start time and buffer demand for W = 32.
   - The AIMD packets-per-drop result 3w²/8, and from it p for w = 8, 12, 16 compared with the paper's 1% claim. Then derive the Mathis formula.
   - Redo it for a modern path: 100 Mbps, 50 ms, IW10.
3. **Bench, 50–60 min, no iperf3: draw the sawtooth.**
   - Topology: 3 netns (snd — rtr — rcv) over veth. On rtr's egress to rcv: `netem delay 20ms rate 10mbit limit 60`, or htb 10mbit + pfifo plus a separate netem delay. Turn off TSO/GSO on snd's veth with `ethtool`.
   - Sender: a python3 bulk socket with `setsockopt(IPPROTO_TCP, TCP_CONGESTION, b"reno")`.
   - Logging: bpftrace on `tracepoint:tcp:tcp_probe` (snd_cwnd, ssthresh, srtt) filtered by port, plotted with matplotlib.
   - Predict before running: peak cwnd ≈ BDP + buffer, sawtooth period ≈ (W/2)·RTT, ssthresh = W/2. Repeat with `cubic` and compare the 0.7 decrease and cubic regrowth.
   - Put the bottleneck in the rtr namespace on purpose. A shaper on the sender's own interface is softened by TSQ, a later fix in the chain. (netem with delay/rate orphans skbs, see `sch_netem.c:496-500`, so a netem-only local setup also works. Not run on the bench yet.)
4. **Bench, 20 min: exponential backoff live.**
   - During the exercise 3 transfer, black-hole the path (`ip -n rtr link set <dev> down` or `netem loss 100%`).
   - Poll `ss -ti` every 0.5 s: `backoff:` should increment, `rto:` should double from ~200 ms (`tcp_timer.c:683-684`), and cwnd should fall to 1 (`tcp_enter_loss`).
   - Restore the link and watch slow-start resume.

None of these need iperf3. A python3 socket pair is the traffic source; `nc` exists but its flag dialect is unchecked.

## 13. Honest assessment for this learner

**Read closely:**
- The intro and §1 (pp.158–160), especially Figs 1 and 2.
- §3 (pp.162–165) including fn 8, fn 9, fn 10 and fn 11. Fn 9 is CoDel's thesis 24 years early; fn 11 is pacing's.
- Appendices B and C (pp.171–172).
- These are short and are the conceptual root of everything downstream.

**Read for the method, not the constants:**
- §2 and Appendix A (pp.160–162, 167–171). The estimator structure survives in `tcp_rtt_estimator` almost line for line, but the constants and RTO formula changed.

**Skim:**
- The trace figures 3–12. Read the captions for the numbers; the plots are low-resolution scans.
- §4 (pp.165–166) is one idea: fairness and early detection need the gateway.
- The Acknowledgements.

**Outdated, with "since the paper" notes:**
- **RTO.** Now A + 4D (Jacobson's 1990 revision, cited in the kernel comment at `tcp_input.c:1082`; RFC 6298, K = 4). The initial RTO is 1 s (RFC 6298). Linux adds a 200 ms min-RTO floor on rttvar, so on a LAN `rto ≈ srtt + 200 ms`. The paper's "mdev ≥ sdev" is backwards (M11).
- **Initial window.** 1 → 10 segments (RFC 6928; `TCP_INIT_CWND`).
- **Per-ack increase.** "+1 per ack" became per-segment-acked accounting (ABC, RFC 3465). Linux handles stretch ACKs (`tcp_cong.c:447-455`).
- **Loss detection.** Timeout-only became fast retransmit/recovery (RFC 5681), SACK, PRR (RFC 6937), then RACK-TLP (RFC 8985). In v7.2, loss marking is RACK-based (`tcp_time_to_recover` only checks `lost_out`).
- **Default CC.** Reno's d = 0.5 / u = 1 gave way to CUBIC (RFC 9438; β ≈ 0.7). The paper itself says u = 1 is "almost certainly too large" (p.172).
- **Congestion signal.** The "congestion experienced bit" the paper sidesteps became ECN (RFC 3168), now L4S (RFC 9330–9332; `sch_dualpi2.c` exists in v7.2).
- **Gateway side.** "Future work" became RED (1993), then CoDel and fq_codel (paper 02; RFC 8289/8290), PIE and CAKE.
- **Loss as the signal.** "Loss ≈ congestion" and "ack clock = bottleneck clock" both fail with deep buffers, Wi-Fi/GRO ack aggregation and stretch ACKs. That is why the chain moves to pacing and BBR.
- **Delayed acks.** The author's doubts about delayed acks (Fig 9 caption) remain relevant. Linux delays ACKs by 40–200 ms with quickack heuristics.
