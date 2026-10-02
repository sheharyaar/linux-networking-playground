# Inventory 08 — Eiffel (Saeed et al., NSDI 2019)

## 1. Facts

- **Citation:** Ahmed Saeed, Yimeng Zhao, Nandita Dukkipati, Mostafa Ammar, Ellen Zegura, Khaled Harras, Amin Vahdat. "Eiffel: Efficient and Flexible Software Packet Scheduling." *16th USENIX Symposium on Networked Systems Design and Implementation (NSDI '19)*, Boston, MA, Feb 26–28 2019, pp. 17–31. ISBN 978-1-931971-49-2. Extended version: arXiv:1810.03060 (ref [48]; it also has the hClock-in-userspace use case, footnote 2, p.25).
- **PDF pages:** 16 (pdfinfo).
- **Printed page numbers:** yes, in the USENIX footers.
- **Printed range:** 17–31.
- **Offset:** PDF page 1 is the USENIX cover (red, unnumbered). **printed = PDF + 15.** Checked on rendered pages: PDF 2 = p.17 (title/abstract), PDF 6 = p.21 (Figs 2–4), PDF 7 = p.22, PDF 8 = p.23, PDF 9 = p.24, PDF 11 = p.26, PDF 16 = p.31 (Appendix A/B).
- Text extraction works on every page. Equations on p.22, p.23 and p.31 come out garbled in the .txt, so read those from the rendered PDF.

## 2. Sections (printed pages)

| Section | Pages |
|---|---|
| Abstract, §1 Introduction | 17–18 |
| §2 Background and Objectives (efficient PQs, rank properties, Table 1, Objective 1, flexibility, Objective 2, landscape) | 18–20 |
| §3 Eiffel Design (Fig 1) | 20–25 |
| §3.1 Priority Queueing in Eiffel | 20–23 |
| §3.1.1 Circular FFS-based Queue (cFFS) | 21–22 |
| §3.1.2 Approximate Priority Queuing (Gradient Queue) | 22–23 |
| §3.2 Flexibility in Eiffel | 23–25 |
| §3.2.1 PIFO Model Extensions | 23–24 |
| §3.2.2 Arbitrary Shaping | 24–25 |
| §4 Eiffel Implementation (policy creation, kernel qdisc, BESS) | 25 |
| §5 Evaluation | 25–29 |
| §5.1 Use cases; §5.1.1 Shaping in Kernel (p.26); §5.1.2 L(X)F in Userspace (pp.26–27) | 25–27 |
| §5.2 Microbenchmark (incl. ns2 network-wide impact and the queue-selection guide) | 27–29 |
| §6 Conclusion | 29 |
| References [1]–[56] | 29–31 |
| Appendix A Gradient Queue Correctness (Theorem 1); Appendix B Examples of Errors | 31 |

## 3. Terms introduced

1. **Packet scheduling / ranking function / rank**: ordering packets in a queue by a number (the rank) that a policy computes. Ranking happens on enqueue and sometimes again on dequeue. p.17 (properties of ranks on p.18).
2. **Integer priority queue**: a priority queue whose keys are bounded integers, so it can index instead of compare. p.18 (§1), developed on p.19.
3. **Bucketed integer priority queue**: the range [0,C] is split into N buckets of width C/N; packets in one bucket leave FIFO and are treated as equal rank. p.19.
4. **Granularity**: the rank interval one bucket covers (C/N). Finer granularity means more accurate ordering, more empty buckets and more memory. pp.19, 27–28.
5. **Timing wheel**: a time-indexed bucket array (Varghese & Lauck) that Carousel uses. O(1), but only for non-work-conserving, time-based schedules. p.19.
6. **Unit of scheduling / work conservation / ranking trigger**: the three axes the paper uses to judge flexibility: packets vs flows, work-conserving vs shaping, rank on enqueue, dequeue or both. p.19.
7. **PIFO (Push-In-First-Out)**: the hardware building block from Sivaraman 2016. Elements are inserted by rank and always removed from the head. Its programming model has scheduling transactions, scheduling trees and shaping transactions. Explained on p.20 and in more detail on p.23.
8. **FFS (Find First Set)**: a CPU instruction that returns the index of the first set bit in a word in a few cycles. With one bit per bucket, it finds the minimum non-empty bucket. p.21 (first mentioned in the abstract, p.17).
9. **Hierarchical FFS-based queue** (and **PIQ**, Priority Index Queue): a tree of bitmaps where each bit says whether a child is non-empty. Finding the minimum takes O(log_w N). p.21, Fig 3.
10. **cFFS (Circular Hierarchical FFS-based queue)**: two hierarchical FFS queues, a primary covering [h_index, h_index+q_size) and a secondary covering the range just after it. The pointers swap when the primary drains, so the window moves without rebuilding bitmaps. pp.21–22, Fig 4.
11. **Gradient Queue (GQ), curvature function, weight function**: an algebraic stand-in for FFS. Each non-empty bucket i adds 2^i(x−i)^2 to a quadratic, and the critical point gives the maximum non-empty index, ceil(b/a). A "proper" weight function makes the curvature unique per occupancy pattern. p.22, Fig 5.
12. **Approximate Gradient Queue**: uses the weight 2^(i/α)(x−i)^2 so that a and b cover far more buckets in one word. Lookup takes one step but can miss when buckets are empty, and a linear search then fixes it. pp.22–23.
13. **Per-flow ranking and on-dequeue ranking**: Eiffel's two additions to PIFO. A flow's rank is a function of all its queued packets, and dequeues can re-rank a flow (needed for pfabric). p.24, Fig 10 (p.26).
14. **Arbitrary shaping / single shaper**: every rate limit in a hierarchy is turned into per-packet timestamps in one time-ordered queue, instead of one queue per limiter. p.24, Figs 6–7.
15. **L(X)F**: the "least/largest X first" family (LSTF, LQF, SRTF). p.26.

The terms are **not in the paper**: "calendar queue" appears nowhere, and Brown 1988 is not cited. Eiffel's closest analogues are the timing wheel [54] and the bucketed queues of Carousel [47].

## 4. Core claims

1. Software schedulers built on comparison priority queues (rb-trees in qdiscs, binary heaps in C++) pay O(log n) per operation. A policy with m ranking functions pays O(m log n) per packet, and Eiffel cuts this to O(m) (p.18).
2. Packet ranks are integers, sit inside a bounded window that moves over time, and many packets share a rank. Together these make bucketed integer priority queues the right structure (pp.18–19).
3. A hierarchical FFS queue costs O(log_w N). N is fixed when the policy is configured, so the cost per packet is constant and does not depend on how many packets are queued (p.21).
4. A plain mod-N circular bitmap gives the wrong order once the range wraps. cFFS keeps correct order over a moving range by using two FFS queues whose pointers swap. Elements beyond the secondary range land, unsorted, in its last bucket (pp.21–22).
5. The approximate gradient queue finds a near-minimum in one step. It beats cFFS by up to 9% when the queue is densely occupied, and it degrades as the fraction of empty buckets grows. The authors recommend changing granularity once more than 30% of buckets are empty (pp.20, 22–23, 27–28).
6. Converting every rate limit into timestamps lets one shaper queue enforce all the limits in a scheduling hierarchy. This decouples shaping from work-conserving scheduling, which PIFO cannot do (p.24).
7. In the kernel (20k flows, 24 Gbps aggregate, EC2), the Eiffel qdisc used a median of 14x fewer cores than FQ/pacing and 3x fewer than Carousel. Most of the gap to Carousel came from Carousel firing timers at fixed intervals, while Eiffel arms its timer for the soonest deadline (p.26, Figs 8–9).
8. pFabric on cFFS in BESS sustains line rate with 5x as many flows as a binary-heap version, because moving a flow between buckets is O(1) (p.27, Fig 11). The intro also claims 40x for hClock (p.18).
9. In ns2 pFabric simulations, using the approximate queue in every switch barely changes flow completion times (p.28, Fig 15).
10. Below roughly 1k priority levels the choice of queue hardly matters. Above that, use FFS for a fixed range, cFFS for a moving range with uneven occupancy, and the approximate queue for a moving range with dense occupancy (pp.28–29, Fig 16).

## 5. Figures and examples worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| Table 1 | 19 | FQ/pacing, hClock, Carousel, OpenQueue and PIFO compared with Eiffel on complexity, HW/SW, scheduling unit, work-conserving, shaping, programmability | A one-glance map of the design space. FQ/pacing is listed as O(log n) |
| 2 | 21 | Six-bucket queue with bitmap 000011, where one FFS finds bucket 4 | The base idea. Redraw it with real bit order (Linux __ffs is least-significant-first) |
| 3 | 21 | Three-level bitmap hierarchy with w=2 | Shows why the cost is O(log_w N). Redraw with w=64 to show that 3 levels cover 262k buckets |
| 4 | 21 | cFFS: primary buckets 242–247 and secondary 248–253, each with its bitmap tree | Shows the moving-window problem and the fix. Pair it with QFQ's shifted bitmap and the timer wheel's two-part search (§8) |
| 5 | 22 | Curvature sketches for three occupancy states of a max-queue | Intuition for the gradient queue. Put it in a toggle |
| 6–7 | 24 | A hierarchical policy (0.7/0.3 and 0.1/0.9 shares, 10 and 7 Mbps limits, paced root) and how it maps to PQ1–PQ3 plus one shaper, with steps 1, 2.1/2.2, 3.1/3.2 | The "every rate limit becomes a timestamp" idea, the conceptual link to EDT and Cilium's Bandwidth Manager. Well worth redrawing as a packet journey |
| 8–9 | 26 | CDFs of cores used: FQ vs Carousel vs Eiffel, split into system vs softirq | Evidence that timer policy (fixed tick vs soonest deadline) dominates |
| 10 | 26 | The two-line pFabric policy with on-enqueue and on-dequeue rank updates | The simplest example of per-flow, re-ranking scheduling |
| 16 | 28 | Decision tree for choosing a PQ | A good summary slide |

(Figs 11–15, pp.26–28, are benchmark and simulation plots: worth citing, not redrawing. The paper itself mislabels a reference, see §6 errata.)

## 6. Maths

| # | Item | Page | Background | Reproduce? |
|---|---|---|---|---|
| M1 | A policy with m ranking functions needs m PQ ops per packet, so O(m log n) with comparison PQs and O(m) with Eiffel | 18 | Big-O | **Yes** |
| M2 | Comparison PQs need O(log n) for insert or extract (cites Thorup [52]) | 18 | Comparison lower bound | State and use |
| M3 | Bucketed PQ over [0,C] with N buckets of width C/N. Cost is constant per op ("logarithmic in the number of buckets", because the search is over buckets, not elements). Memory is tens to hundreds of KB | 19 | — | **Yes** (granularity arithmetic) |
| M4 | One word: O(1) when N ≤ w. M words scanned in sequence: O(M), the Linux RT example with 100 priorities in 2×64-bit or 4×32-bit words. Hierarchical: O(log_w N) | 21 | Logs, bitmaps | **Yes**: ⌈log_64 20000⌉ = 3; ⌈log_32 10^9⌉ = 6 (the paper's "six bit operations" for a billion buckets, p.29); ⌈log_64 10^9⌉ = 5 |
| M5 | Why naive mod indexing breaks: priority 6 in a 6-slot queue lands in slot 0 and its bit claims the minimum | 21 | Modular arithmetic | **Yes** (draw it) |
| M6 | Gradient queue: weight 2^i(x−i)^2. The paper writes the curvature as ax²−bx+c with critical point x=b/2a, a=Σ2^i, b=Σi·2^i, and max index = ceil(b/a) | 22 | Derivative of a quadratic | **Yes, in a toggle**. Expanding Σ2^i(x−i)² gives a·x² − 2(Σi2^i)·x + c, so with b := Σi2^i the critical point is b/a. The paper's "b/2a" treats b as the whole linear coefficient. Its final ceil(b/a) is correct |
| M7 | Theorem 1 (App. A): a = 2^{N+1}−2; b = N·2^{N+1} − (2^{N+1}−2); x = N/(1−2^{−N}) − 1 ∈ (N−1, N], so ceil(x) = N; clearing a lower bit j raises the critical point: (b−j2^j)/(a−2^j) − b/a > 0 | 31 | Geometric and arithmetic-geometric series | **Yes**: closed forms plus a numeric check. Checked: N=1..7 gives ceil = N |
| M8 | Approximate GQ: f(i)=i/α; b/a = M/(1−g(α,M)) + u(α), g = (2^{1/α})^{−M−1}, u = 1/(1−2^{1/α}). Example α=16: g≈0 at M=124, shift u "=22", I0=124, Imax=647, so 523 buckets | 23 | Series, asymptotics | **State only**. My numeric check: the formula matches Σ over buckets 0..M (b/a at M=124 is 101.97 exact vs 101.97 by formula). **u(16) ≈ −22.59 is negative**, so the critical point trails the true max by about 22.6 and the correction adds about 22.6; the paper gives only the magnitude. The text does not derive Imax=647. At 647, b ≈ 2^54, roughly a 64-bit or double-mantissa budget (my inference) |
| M9 | Exact GQ is O(log_w N), like FFS but with division in place of bit ops. BSR is 8–32x faster than DIV | 22–23 | — | State |
| M10 | Soft heap: error bound ε gives O(log 1/ε) insertion | 23 | — | Skip (background) |
| M11 | A rate limit becomes a per-packet timestamp (the Carousel result) | 24 | — | **Yes**, as the EDT rule t_next = max(now, t_last) + len/rate. The paper states the idea without writing the formula; the formula is the one in Carousel, Cilium edt.h and tcp_output.c (§8) |
| M12 | Granularity limit: with 100 µs buckets you cannot create gaps under 100 µs. Size buckets so each holds at least one packet | 28 | — | **Yes** |
| M13 | Binary-heap pFabric is described as needing "O(n)" re-heapify per move | 27 | Heaps | Critique it: with an index map, decrease-key is O(log n). The baseline is weak |

**Errata a learner will trip on** (worth a "read carefully" box):
- p.19: "Timing Wheel does not support operations needed for non-work conserving schedules (i.e., ExtractMin…)" should say *work-conserving*.
- p.21: "Bit-Scan-Forward (BSR)": BSF is forward and BSR is reverse. "Leftmost set bit" is a drawing convention. On x86 Linux, `__ffs` is `tzcnt`, the least-significant set bit.
- p.23 has a garbled sentence ("While BSR instruction is 8-32x faster than DIV…").
- p.28 says "Figure 12 shows throughput … for different ratios of non-empty buckets"; that is Figure 13.
- The line rate is 20 Gbps in the intro (p.18) but 25 Gbps instances and a 24 Gbps aggregate in §5.1.1 (p.26).
- App. A uses N both for the number of buckets and for the maximum index.

## 7. Numbers worth reusing

- Kernel pacing costs up to 10% CPU (from Carousel); hierarchical WFQ in VMware NetIOC up to 12% (pp.17–18).
- Networks need tens of thousands of rate limiters; NICs offered 10–128 queues (p.17).
- Rank ranges: 8 levels (802.1Q); 50k for per-flow fairness (50k flows on a video server); up to 1 million for time-indexed queues (p.18).
- Bucket counts run from a few thousand to hundreds of thousands, using tens to hundreds of KB (p.19).
- BSR takes 3 cycles (p.21). Linux RT uses 100 priorities, 2 words at 64-bit (p.21). QFQ has fewer than 64 groups (p.21). PIFO handles at most 2048 flows (pp.19–20).
- Approximate GQ example: α=16, I0=124, Imax=647, 523 buckets, shift about 22 (p.23).
- Kernel use case (p.26): **20k buckets, 2 s horizon, so 100 µs per bucket**; kernel v4.10; only sock.h modified; 2× m4.16xlarge (64 cores, 25 Gbps); neper; **20k flows paced with SO_MAX_PACING_RATE to a 24 Gbps aggregate**; 100 s runs sampled with dstat every 1 s. Results: **FQ 14x and Carousel 3x more cores** (median).
- Userspace: pFabric with 1500 B packets on one core, 10 runs of 20 s, 5x flows (p.27). BESS caps flows at 32 packets with 10 KB output batches (p.25).
- Bucketed vs comparison PQs: about 6x (p.27). Approx vs cFFS: up to +9% (10k buckets). Regranularize when more than 30% of buckets are empty (p.28).
- The PQ choice starts to matter at about 1k priority levels. A billion buckets need about 6 bit operations in cFFS (pp.28–29).
- ns2: 144-node leaf-spine, queues of 1000k elements, load 10–80% (p.28).
- Derived (mine): 24 Gbps × 100 µs = 300 kB, about 200 MTU packets per bucket in aggregate. 24 Gbps over 20k flows is 1.2 Mb/s per flow, one 1500 B packet every 10 ms, so per-flow pacing is far coarser than the bucket. A single 10 Gb/s flow sends a packet every 1.2 µs, about 83 per 100 µs bucket, released together. An rb-tree over 20k throttled flows needs about log2(20000) ≈ 14.3 levels (red-black height ≤ 2·log2(n+1) ≈ 28.6).

## 8. Linux mapping (v7.2 tree, `~/workspace/repos/linux`, grep-verified)

**Is Eiffel upstream? No.** Grepping the tree for `eiffel`, `cffs` and `gradient queue` finds only unrelated hits (a comment in sound/pci/ad1889.c and the AFFS `FS_DCFFS` constant). Linux kept rb-trees in sch_fq and took a different path: an O(1) list for in-order EDT packets plus a fast path.

**sch_fq, the pacer Eiffel benchmarked against (net/sched/sch_fq.c):**
- `:66`: comment: "If packets have monotically increasing time_to_send, they are placed in O(1) in linear list (head,tail), otherwise are placed in a rbtree (t_root)". The per-flow `struct rb_root t_root` is at `:71`, and `flow_queue_add()` at `:508` implements this. Git: `eeb84aa0d0af` (2019-05-04) "do not assume EDT packets are ordered" added it after Eiffel's v4.10 baseline.
- `:138` `struct rb_root delayed; /* for rate limited flows */` and `:139` `time_next_delayed_flow`: the rb-tree of throttled flows keyed by `time_next_packet`. This is the O(log n) structure Eiffel replaces. Insert is `fq_flow_rb_insert()` at `:220` (called by `fq_flow_set_throttled()` at `:241`), and drain is `fq_check_throttled()` at `:664` (an `rb_first()` loop plus an EWMA of unthrottle latency).
- `fq_dequeue()` at `:705` arms one hrtimer for the soonest deadline via `qdisc_watchdog_schedule_range_ns()` (`:745`, defined at net/sched/sch_api.c:644) with `timer_slack`. That is the "timer exactly when needed" behaviour Eiffel credits for beating Carousel.
- Per-flow pacing: `:796–833`, where `len = plen*NSEC_PER_SEC / rate` and `f->time_next_packet = now + len`.
- Horizon: `fq_packet_beyond_horizon()` at `:540`; drop or cap in `fq_enqueue()` at `:615–622`; defaults `horizon = 10 s` (`:1250`), `horizon_drop = 1` (`:1251`), `timer_slack = 10 µs` (`:1248`), `fq_trees_log = ilog2(1024)` (`:1244`).
- Post-Eiffel changes (git log): `076433bd78d7` (2023-09-20) fast path for mostly idle qdisc (`fq_fastpath_check()` at `:314`); `29f834aa326e` (2023-10-02) 3 bands with WRR (`FQ_BANDS` 3, include/uapi/linux/pkt_sched.h:856); `39d010504e6b` (2020-05-01) horizon attribute; `f26080d47007` (2024-10-03) pacing offload (`offload_horizon`). **No in-tree driver sets `dev->max_pacing_offload_horizon`**: it appears only in include/linux/netdevice.h:2552, net/core/rtnetlink.c:2127 and sch_fq.c:1182.
- `tc -s` fields to teach: `struct tc_fq_qd_stats` at include/uapi/linux/pkt_sched.h:859 (`throttled`, `flows`, `inactive_flows`, `throttled_flows`, `unthrottle_latency_ns`, `time_next_delayed_flow`, `horizon_drops/caps`, `fastpath_packets`, `band_pkt_count`).
- Probeable on the running 7.2.6 kernel (checked /proc/kallsyms): `fq_enqueue`, `fq_dequeue` and `fq_flow_rb_insert` exist as symbols. `fq_check_throttled`, `fq_flow_set_throttled` and `flow_queue_add` are inlined and cannot be kprobed.

**Other rb-tree qdiscs (the "O(log n) in qdiscs" claim, p.18):** sch_etf.c:35 (`rb_root_cached head`, by txtime); sch_hfsc.c:128/130/172 (vt_tree, cf_tree, eligible); sch_netem.c:95 (`t_root` tfifo); sch_htb.c:78–79 (`row`, `feed`) and `:146` (`wait_pq`).

**FFS and bitmaps in the kernel, real analogues of Eiffel's structures:**
- **Linux RT run-queue (cited by Eiffel as [11]):** `struct rt_prio_array { DECLARE_BITMAP(bitmap, MAX_RT_PRIO+1); struct list_head queue[MAX_RT_PRIO]; }` at kernel/sched/sched.h:311. `sched_find_first_bit()` at include/asm-generic/bitops/sched.h:13 is literally two `__ffs` calls on 64-bit and four on 32-bit, as the paper says. Used at kernel/sched/rt.c:1689; x86 pulls it in at arch/x86/include/asm/bitops.h:417.
- **`__ffs` on x86:** `variable__ffs()` uses `tzcnt` (arch/x86/include/asm/bitops.h:245); `bsfl` is used for `ffs()` (`:312`). Generic version: include/asm-generic/bitops/__ffs.h:13; `__ffs64` at include/linux/bitops.h:276; `find_next_bit()` at include/linux/find.h:58 → `_find_next_bit()` at lib/find_bit.c:155.
- **QFQ (Eiffel ref [22]), an in-kernel circular FFS bucket queue:** group bitmaps `q->bitmaps[QFQ_MAX_STATE]` at net/sched/sch_qfq.c:188, `qfq_ffs()` at `:747`. Each group's bucket list has `QFQ_MAX_SLOTS 32` (`:94`), `front` (`:171`), `full_slots` bitmap (`:172`) and `slots[]` (`:175`). `qfq_slot_scan()` (`:939`, `__ffs` at `:949`) and `qfq_slot_rotate()` (`:967`) keep the bitmap **relative to `front` by shifting it**, which avoids exactly the wrap bug Eiffel describes on p.21 without needing a second queue. Best contrast for teaching cFFS.
- **Kernel timer wheel, a hierarchical, circular, approximate bucketed queue:** kernel/time/timer.c design comment at `:65`; `LVL_CLK_SHIFT 3` (`:153`), `LVL_BITS 6` / `LVL_SIZE 64` (`:167–168`; one 64-bit word per level), `LVL_DEPTH 9/8` (`:174/176`), `WHEEL_SIZE` (`:187`), `DECLARE_BITMAP(pending_map, WHEEL_SIZE)` (`:263`), `calc_index()`/`calc_wheel_index()` (`:524/541`), `enqueue_timer()` sets the bit (`:612/617`). `next_pending_bucket()` (`:1837`) does the wrap-aware search as two `find_next_bit()` calls (`:1843`, `:1847`). Coarser granularity at higher levels with no recascading is an approximate-ordering tradeoff, the same spirit as Eiffel's granularity discussion.
- **HTB:** `row_mask[TC_HTB_MAXDEPTH]` (net/sched/sch_htb.c:176) plus `ffz(~mask)` (`:370`, `:404`, `:435`, `:476`) pick the highest active priority per level. A bitmap sits over rb-trees.
- **Linear scans where FFS would fit:** sch_prio.c:102/116 loops over at most 16 bands; sch_skbprio.c:44/57 loops over `SKBPRIO_MAX_PRIORITY 64` (pkt_sched.h:137), where one 64-bit FFS would do (an exercise hook). **sch_prio and mqprio do not use ffs or bitmaps**, which contradicts the brief's guess.

**EDT, the timestamp half of "arbitrary shaping" (p.24):** TCP sets `skb->tstamp` from `tp->tcp_wstamp_ns` in `tcp_update_skb_after_send()` (net/ipv4/tcp_output.c:1446; `len_ns = skb->len*NSEC_PER_SEC/rate` at :1459, `tcp_wstamp_ns += len_ns` at :1464). `SO_MAX_PACING_RATE` (value 47, include/uapi/asm-generic/socket.h:76) is handled at net/core/sock.c:1253. Eiffel's kernel test paced its 20k flows with this option.

**Programmable scheduling upstream today (forward link):** BPF qdisc via struct_ops, net/sched/bpf_qdisc.c (kfuncs `bpf_qdisc_skb_drop` `:215`, `bpf_qdisc_watchdog_schedule` `:226`, …). tools/testing/selftests/bpf/progs/bpf_qdisc_fq.c reimplements fq with `bpf_rbtree_add` (`:373`) and a `time_next_packet` comparator (`:155`). An Eiffel-style bitmap bucket queue would be a BPF qdisc today; nobody has upstreamed one.

**Cilium (user's fork, `~/workspace/neverinstall/cilium`, v1.19.6-vpc.24):** the Bandwidth Manager is Eiffel's single-shaper idea run on stock sch_fq. bpf/lib/edt.h:65 `edt_sched_departure()`: `delay = wire_len*NSEC_PER_SEC/bps` (`:93`), `t_next = t_last + delay` (`:94`), its own horizon drop (`:104–105`), `ctx->tstamp = t_next` (`:107`); called at bpf/bpf_host.c:1666. Its fq setup is mq with fq leaves and `Pacing:1` (pkg/datapath/linux/bandwidth/ops.go:113–145), `FqDefaultBuckets = 15` (2^15 flow-hash buckets, bandwidth.go:43), and **`DefaultDropHorizon = 2 s`** (pkg/maps/bwmap/bwmap.go:28), the same 2 s horizon Eiffel configured (p.26). The data structure under it is still sch_fq's rb-tree.

## 9. Prerequisites and forward references

**Assumed:** big-O and the O(log n) costs of heaps and rb-trees; bit tricks (FFS, `x & -x`); the qdisc model (enqueue, dequeue, watchdog timer, the global qdisc lock, p.25); pacing and rate limiting as timestamps (Carousel, read before this; 06 in this set); the PIFO model; scheduling policies by name (WFQ/STFQ, HPFQ, hClock, pFabric/SRTF, LSTF, EDF); BESS and busy-polling userspace; geometric series (for the toggles).

**Forward references:** BBR and TIMELY need per-flow pacing (p.26, [20], [43]); Linux's own route (EDT TCP 2018, sch_fq bands and fast path 2023, offload_horizon 2024); BPF qdisc; Cilium Bandwidth Manager (EDT + fq, 2 s horizon). Later hardware and approximate-PIFO work (PIEO, SP-PIFO, Gearbox) is **outside this paper, from my memory, and must be verified before it is taught**.

## 10. References worth reading

1. **[50] Sivaraman et al., "Programmable Packet Scheduling at Line Rate" (PIFO), SIGCOMM 2016.** Eiffel's whole flexibility section extends this. Rank, PIFO trees and the scheduling/shaping transaction split come from here.
2. **[47] Saeed et al., "Carousel: Scalable Traffic Shaping at End Hosts," SIGCOMM 2017.** The direct predecessor: timing wheel, timestamps instead of token buckets, the FQ CPU numbers. Already in the set (06); Eiffel reads as Carousel part 2.
3. **[54] Varghese & Lauck, "Hashed and Hierarchical Timing Wheels," SOSP 1987.** The structure behind Carousel and kernel/time/timer.c. Short and classic.
4. **[22] Checconi, Rizzo, Valente, "QFQ," IEEE/ACM ToN 2013.** FFS-based fair queueing that actually shipped in Linux (sch_qfq.c), with a front-relative circular bitmap.

(Brown's 1988 calendar queues are **not** in the reference list. Cite them separately if the guide wants them.)

## 11. Suggested spine and strands

**Spine** (one section in a "timing wheels / EDT" chapter):
1. Where the CPU goes: a scheduler is a priority queue, and rb-trees cost log n per packet per ranking function (pp.17–18).
2. Three facts about ranks lead to bucketing with granularity C/N (pp.18–19).
3. FFS on a word, then bitmap trees: O(log_w N), with Linux RT as the precedent (p.21).
4. The moving window: why mod breaks the bitmap, and three fixes (cFFS swap p.21–22; QFQ shift; the timer wheel's two-part search).
5. (Toggle) The gradient queue as an algebraic FFS and its approximation (pp.22–23, 31).
6. Every rate limit becomes a timestamp, so one shaper is enough (p.24), leading into EDT and Cilium.
7. Evidence: timer policy and data structure vs FQ and Carousel (p.26); the granularity tradeoff (p.28); decision tree (p.28).
8. What Linux did instead: sch_fq rb-trees plus an in-order list plus a fast path. Not upstream; BPF qdisc is the open door.

**Strands:**
- `eiffel-rank-properties`: packet ranks are integers in a bounded moving window, and many share a value, so sorting can become bucketing (p.18).
- `eiffel-ffs-bound`: a w-bit hierarchical bitmap finds the minimum non-empty bucket in ⌈log_w N⌉ word ops, independent of queued packets n (p.21). Example: N=20k, w=64 gives 3.
- `eiffel-circular-bitmap`: mod-N indexing corrupts the bitmap's ordering on wrap. cFFS fixes it with a primary and a secondary queue whose pointers swap (pp.21–22).
- `eiffel-granularity`: bucket width = horizon/N, and packets in one bucket leave FIFO, so 2 s/20k = 100 µs buckets cannot create gaps under 100 µs (pp.26, 28).
- `eiffel-timer-policy`: most of Eiffel's win over Carousel came from arming the timer for the soonest deadline instead of ticking at fixed intervals (p.26, Fig 9).
- `eiffel-single-shaper`: any rate limit is a per-packet timestamp, so one time-ordered queue can enforce all limits in a hierarchy (p.24). This is the EDT idea under Cilium's Bandwidth Manager.
- `eiffel-not-upstream`: v7.2 sch_fq keeps an rb-tree of throttled flows (`q->delayed`) and per-flow `t_root`, with an O(1) list for in-order EDT. No cFFS upstream.

## 12. Exercise ideas

1. **Pen and paper (25 min), bucket and complexity arithmetic.** (a) 20k buckets over 2 s: bucket width? At 24 Gbps with 1500 B packets, packets per bucket? For one 10 Gb/s flow, burst size per bucket? (100 µs; about 200; about 83.) (b) ⌈log_w N⌉ for N = 20k, 10^6, 10^9 and w = 32, 64; reconcile with "six bit operations" (p.29). (c) rb-tree depth for 20k throttled flows vs 3 FFS levels: what does each step cost in cache misses? (d) Gradient queue by hand: buckets {1,3,4} non-empty gives a=26, b=90, b/a=3.46, ceil 4. Then derive Theorem 1's closed forms.
2. **Python (45 min), build the queues.** Implement a 2-level FFS bucket queue (`(x & -x).bit_length()-1`), a cFFS with primary/secondary swap, and a `heapq` baseline. Replay synthetic EDT timestamps (20k flows, Poisson starts, 2 s horizon) and count word ops per pop vs heap comparisons. Plot ordering error against bucket width. Optional: an approximate GQ with α=16, reproducing the error-vs-empty-ratio shape of Fig 14.
3. **Lab (45 min), watch sch_fq's delayed rb-tree.** netns + veth with `tc qdisc replace dev veth0 root fq`. A python client opens 500–2000 TCP connections, each `setsockopt(SOL_SOCKET, 47 /*SO_MAX_PACING_RATE*/, rate)`. Read `tc -s qdisc show dev veth0` (flows, throttled_flows, throttled, unthrottle_latency, time_next_delayed_flow) while running `bpftrace -e 'kprobe:fq_flow_rb_insert { @ins = count(); } kprobe:fq_dequeue { @deq = count(); }'` (these two symbols exist on 7.2.6; the throttle helpers are inlined). Relate inserts per second to the rb-tree cost. No iperf3 needed.
4. **Code reading (30 min), three ways to wrap a bitmap.** Compare QFQ `qfq_slot_scan/rotate` (sch_qfq.c:939/967), the timer wheel's `next_pending_bucket` (timer.c:1837) and Eiffel's cFFS (p.22). For each, explain what happens when the minimum passes the end of the array. Bonus: sketch replacing sch_skbprio's 64-way linear scan (`:44`, `:57`) with one `__ffs`.

## 13. Honest assessment

- **Finish line 1 (the chain):** marginal. Eiffel is the data-structure footnote to the "timing wheels/EDT" step. It explains why bucketed and time-indexed queues beat rb-trees, but Linux did not adopt it, so it fixed nothing in the shipping chain. Its useful contribution to the story is the single-shaper/timestamp argument (p.24) and the timer-policy finding (p.26).
- **Finish line 2 (diagnosis):** low direct value. It helps the learner interpret sch_fq's `throttled_flows`, `unthrottle_latency` and `time_next_delayed_flow`, and that is about it.
- **Finish line 3 (arithmetic):** good. It is the best source in the set for priority-queue complexity (log2 n vs log_w N), granularity and burst arithmetic. The Appendix A series derivation is a fair "some maths" toggle.
- **Finish line 4 (Cilium):** moderate. The Bandwidth Manager is EDT on stock sch_fq, and the 2 s horizon matches. Owning the BW manager does not require knowing cFFS.
- **Read closely:** pp.18–19 (rank properties, bucketed PQ), p.21 to the top of p.22 (FFS, hierarchy, cFFS), p.24 (single shaper, Figs 6–7), p.26 (kernel use case, Figs 8–9), p.28 (granularity paragraph, Fig 16).
- **Skim:** §3.1.2 gradient queue (pp.22–23). The maths is pretty but sloppy (the factor-2 slip, the sign of u, an underived Imax) and the payoff is at most 9%; keep it to a toggle. Also skim Table 1.
- **Skip:** §3.2.1 PIFO extensions (pp.23–24) unless programmable scheduling is in scope; §4 BESS details; §5.1.2 pFabric; §5.2 microbenchmarks except the granularity text; the ns2 FCT plots.
- **Recommendation: MERGE** into the Carousel / timing-wheel / EDT chapter as one "the priority queue under the pacer" section of about one session. It should not be a standalone chapter.
