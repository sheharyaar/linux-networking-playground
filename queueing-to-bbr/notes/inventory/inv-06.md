# Inventory 06: Saeed et al., "Carousel: Scalable Traffic Shaping at End Hosts" (SIGCOMM 2017)

Source PDF: /home/wazir/Documents/Books/networking/routing-papers-bbr/06-carousel.pdf
Text: /tmp/qbbr/06-carousel.txt (layout), /tmp/qbbr/06-carousel.raw.txt

## 1. Facts

- **Citation:** Ahmed Saeed, Nandita Dukkipati, Vytautas Valancius, Vinh The Lam, Carlo Contavalli, Amin Vahdat. "Carousel: Scalable Traffic Shaping at End Hosts." In *Proc. ACM SIGCOMM 2017*, Los Angeles, CA, USA, August 21–25, 2017, pp. 404–417. https://doi.org/10.1145/3098822.3098852. The DOI, ISBN 978-1-4503-4653-5/17/08 and "14 pages" are all printed on p. 404. Saeed is at Georgia Tech (work done at Google); the other authors are at Google.
- **PDF:** 14 pages, US Letter, ACM sigconf two-column layout.
- **Printed page numbers:** yes. Each page has a centred footer folio, plus running heads "SIGCOMM '17, …" and "A. Saeed et al." / "Carousel: …".
- **Printed range:** 404–417.
- **Offset:** printed = PDF + 403. Verified on rendered pages: PDF p1 → 404, p2 → 405, p7 → 410, p11 → 414, p14 → 417 (and on every page in between). **Pages below are printed page numbers.**

## 2. Sections (printed pages)

| Section | Pages |
|---|---|
| Abstract; 1 Introduction | 404–405 |
| 2 Traffic Shapers in Practice (Fig. 1) | 405–406 |
| 2.1 Policers | 405–406 |
| 2.2 Hierarchical Token Bucket (HTB), with footnote 2 on the TSQ 128 KB default | 406 |
| 2.3 FQ/pacing (Fig. 2b) | 406 |
| 3 The Cost of Shaping: Policers, Pacing, HTB, Memory, Summary (Figs 3–9) | 406–408 |
| 4 Carousel Design Principles: requirements and three tenets (Fig. 10 on 409) | 408–409 |
| 5 The Carousel System (software NIC, busy polling) | 409 |
| 5.1 Single Queue Shaping | 409–411 |
| 5.1.1 Timestamp Calculation (LTS formula, max-consolidation, ERT) | 409–410 |
| 5.1.2 Single Time-indexed Queue (Timing Wheel, Algorithm 1 on 410, horizon/granularity, global pool) | 410–411 |
| 5.2 Deferred Completions (Fig. 11), and delay-based CC as an alternative | 411–412 |
| 5.3 Scaling Carousel with multiple cores (NBA water-filling, lazy ~100 ms updates) | 412 |
| 6 Carousel at the Receiver (ACK-sequence shaping on top of DCTCP) | 412 |
| 7 Evaluation | 412–416 |
| 7.1 Microbenchmark: setup on 412–413; 7.1.1 Rate Conformance 413; 7.1.2 Memory Efficiency 413–414; 7.1.3 Timing Wheel Parameters 414; 7.1.4 Receiver 414–415 | 412–415 |
| 7.2 Production Experience (Figs 20–23) | 415–416 |
| 8 Discussion (hardware NICs, limitations) | 416 |
| 9 Related Work | 416 |
| 10 Conclusion | 416–417 |
| 11 Acknowledgments; References [1]–[44] | 417 |

Figure locations: Fig. 1 on 405; Figs 2–3 on 406; Figs 4–6 on 407; Figs 7–9 on 408; Fig. 10 on 409; Algorithm 1 on 410; Fig. 11 on 411; Figs 12–14 on 413; Figs 15–18 and Table 1 on 414; Figs 19–23 on 415.

## 3. Terms introduced

1. **traffic shaping**, with two kinds. *Pacing* injects inter-packet gaps within one connection. *Rate limiting* enforces a rate on a flow aggregate. p. 404.
2. **flow / traffic aggregate**: a set of TCP flows grouped under one shaping policy. p. 404, footnote 1 on p. 405.
3. **pre-filtering with multiple token bucket queues**: the classifier → per-aggregate queue + token bucket → scheduler architecture that Carousel argues against. p. 405 (Fig. 1).
4. **policer**: a token bucket with zero buffering that drops non-conformant packets. Rate is the long-run average; burst is the jitter tolerance. pp. 405–406.
5. **HTB**: a tree of token-bucket shapers in a Linux qdisc. Leaves shape, and inner nodes let leaves borrow from each other. p. 406.
6. **FQ/pacing**: Linux sch_fq. Per-flow state lives in hashed RB-trees, DRR runs over active flows, and a second RB-tree holds flows keyed by next-send time. Pacing happens at TSO-segment granularity. p. 406.
7. **TSO autosizing**: sizing TSO packets from the pacing rate so that at least one goes out per ~1 ms. p. 406.
8. **backpressure**: a signal from the shaper that slows the source. Drops are the coarse form; TSQ is the fine one. pp. 406, 408.
9. **head-of-line (HoL) blocking**: a delayed packet holds up unrelated packets queued behind it. pp. 405, 409.
10. **release time / Earliest Release Time (ERT)**: a packet's absolute earliest wire time, the final consolidated timestamp. pp. 409–410.
11. **timestamp policy (LTS_i, R_i)**: each policy i keeps its last timestamp and advances it by len/R_i per packet. Several policies combine by taking the max. p. 410.
12. **Timing Wheel**: a circular array of slots, each covering g_min of time, out to a horizon. O(1) insert and extract, FIFO within a slot. It is a special case of the **Calendar Queue**. p. 410.
13. **slot granularity g_min / horizon**: g_min ≥ 1/f_max, where f_max is the polling frequency. Slots = horizon/g_min. Beyond-horizon packets are either clamped into the last slot or dropped. pp. 410–411.
14. **Deferred Completions**: the shaper returns the TX completion to the guest stack only when the packet actually leaves. This bounds per-flow occupancy (a generalized TSQ). Delivery has to be out-of-order. pp. 409, 411–412.
15. **NBA (NIC-level bandwidth allocator)**: periodically redistributes an aggregate's rate across per-core timestampers using water-filling (max-min). It reserves 1% for idle cores and updates every ≈100 ms. p. 412.
16. **Gbps/CPU and Gbps/SoftNIC**: efficiency metrics. Egress Gbps ÷ (CPUs × utilization), and Gbps ÷ the software NIC's self-reported busy fraction. pp. 415–416.

## 4. Core claims

1. Shaping is moving to end hosts. Middleboxes lack state, buffer expensively, and cannot see edge bottlenecks, and the host is the cheapest place to buffer (p. 405).
2. On production video servers, FQ/pacing cuts the retransmission rate by **40%** but costs **10% of machine CPU** at the median and the tail, i.e. up to ~6 of 64 cores (p. 407, Fig. 4). QUIC's user-space pacing behaves the same way. The p99 process CPU rises 0.15 → 0.20 (+30%) and retransmissions fall from 2.6% to 1.6% (p. 407, Fig. 5).
3. Policers are cheap but conform badly to the target rate: up to 10× off, and 5× below target even with a 1 s burst at 100 ms RTT under CUBIC (pp. 406–407, Fig. 3).
4. HTB conforms within ~5% but serializes on the global qdisc lock. TCP_RR saturates at 600K vs 800K transactions/s without HTB (p. 407, Fig. 6), and production lock-acquire time reaches ~1 s at p99 (pp. 407–408, Fig. 7).
5. Without backpressure, one 2 Gbps, 50 ms-RTT VM flow piles **21K MTU packets** (≈32 MB, +120 ms) into a hypervisor shaper. With backpressure the bound is about 2 TSO segments ≈ 85 MTU packets ≈ 128 KB (p. 408, Fig. 8).
6. The CPU cost of HTB and FQ is *intrinsic*. They need one queue per rate limit, which has to be polled, plus per-packet cross-core locking (p. 408).
7. One time-indexed queue can emulate many token buckets. Each policy stamps LTS'_i = LTS_i + len/R_i, and the final release time is the **max** across policies, which is equivalent to a chain of token buckets (p. 410).
8. A timing wheel gives O(1) insert and extract with a smaller constant than a calendar queue (which degrades to O(N) on skew), at the price of FIFO order within a slot (p. 410).
9. Deferred completions keep shaper occupancy at ≈2 × active flows regardless of rate or CC. Delay-based CC (Vegas) shows about twice DC's p99 occupancy in the rate sweep (Fig. 14) and a less predictable p99 as flows increase (Fig. 15). Without DC the shaper fills its 70K-entry memory (pp. 413–414).
10. Carousel tracks target rates more tightly than HTB (5% deviation) and FQ (6%). FQ's conformance collapses beyond ~200 flows because of its packet limits (p. 413, Figs 12–13). A slot granularity of 8–16 µs suffices at 5 Gbps, while 4 ms slots deviate by ~300 Mbps (p. 414, Fig. 16). In production Carousel delivers 6.4% / 8.2% more Gbps/CPU at p50 / p90, about 4.6 CPUs saved per 72-CPU host or 16–20% of networking CPU (p. 415). It also lifts software-NIC efficiency 12% via bigger batches, 2.1 → 3.3 packets (p. 416).
11. Limitations: enqueued timestamps cannot be changed, so preemptive schedules such as strict priority are unsupported; timestamps must share a clock base across sources (p. 416).

## 5. Figures and examples worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| 1 | 405 | Classifier → N token-bucket queues → scheduler → NIC | The "before" picture. Map it onto HTB classes and `tc filter`. |
| 2a / 2b | 406 | HTB tree; FQ/pacing internals (hashtable of RB-trees on flow ids, and a "flow delays" RB-tree on time_next_packet) | Redraw 2b against **v7.2 sch_fq**, which keeps the same structure (`fq_root[]`, `q->delayed`) and adds EDT, bands and a fastpath. |
| 8 | 408 | CDF of packets buffered at a hypervisor shaper with no backpressure (10K–22K packets) | The motivating disaster. Easy to recompute: 21K × 1.5 KB at 2 Gbps ≈ 126 ms. |
| 10 | 409 | Carousel architecture: socket buffers → Timestamper → circular time-indexed queue → NIC, with "report completion to source" | **Chapter spine diagram.** |
| Alg. 1 | 410 | Timing-wheel Insert and Extract pseudo-code | Implement it in Python. See the errata in §6. |
| 11a / 11b | 411 | Immediate vs deferred completions between guest TCP, virtio driver and software NIC | The same idea as TSQ's `tcp_wfree` destructor. Redraw it with veth, host fq and Cilium. |
| 12–13 | 413 | Absolute rate deviation vs set rate (1 flow), and achieved rate vs number of flows at a 5 Gbps target | Benchmark shape for a netns re-run at lower rates. |
| 14–15 | 413–414 | Packets held in the shaper: DC vs Vegas, vs rate and vs flows | Occupancy ≈ 2 × flows under DC. |
| 16 | 414 | Deviation vs slot granularity (2 µs – 4 ms) at 5 Gbps. Flat ≈0 up to ~256 µs, ≈200 Mbps at 500 µs, ≈300 Mbps at 4 ms (read from figure). | Granularity arithmetic. The flat region is wider than the "8–16 µs" the text recommends. |
| 17 | 414 | Analytical minimum rate and #slots vs horizon (2 µs slots) | See the unit caveat in §6. |
| 18 | 414 | CDF of \|timestamp − actual tx\|, from 64 ns to 14 µs. >90% are below 2 µs. | Accuracy is bounded by slot rounding. |

## 6. Maths

| Item | Page | Background | Reproduce? |
|---|---|---|---|
| **Per-policy timestamp:** LTS'_i = LTS_i + len(P_j^i)/R_i. Unpaced packets carry timestamp 0. | 410 | leaky bucket | **yes, core.** Gap in the paper: as written, an idle policy accumulates credit. A flow idle for T can then burst R·T bytes at once. Real implementations clamp with max(now, LTS) first: Linux `tcp_wstamp_ns = max(tcp_wstamp_ns, tcp_clock_cache)` at tcp_output.c:1554, and Cilium-style EDT does max(now, t_last + len/R). *(This critique is mine.)* |
| **Consolidation:** final timestamp = max_i(timestamp_i), equivalent to a series of token buckets | 410 | none | yes. Show that max of release times means the slowest bucket dominates. |
| slots = horizon / g_min; horizon = l_max / r_min; g_min = 1/f_max | 410 | none | **yes** |
| Example: g = 8 µs, horizon 4 s → 500K slots. Max per-flow rate = 1500 B / 8 µs = 1.5 Gbps; with 4 KB per slot ≈ 4 Gbps. | 410 | none | **yes.** **Inconsistency to catch:** the paper says the minimum rate is "one packet sent per time horizon, which is 1.5 Mbps for 1500 B". But 1500 B per 4 s = 3 kb/s. 1.5 Mbps follows only from horizon = l_max/r_min with l_max = 500 packets (500 × 12 kbit / 4 s). *(My check.)* |
| Burst emulation: put a burst's worth of packets in one slot | 411 | none | yes |
| Memory: 21K × 1.5 KB ≈ 32 MB; +120 ms at 2 Gbps; 2 × 64 KB / 1.5 KB ≈ 85 packets (footnote 3: TSO 64 KB, MTU 1.5 KB) | 408 | none | yes (the arithmetic gives ≈126 ms) |
| References, not packets: 1M outstanding × 8 B pointers ≈ 8 MB | 412 | none | yes |
| **Receiver ACK shaping:** NewAck = min((now − T_a)·Rate + SN_a, SN_r); a synthetic ACK every MTU/Rate | 412 | TCP sequence numbers | yes (optional; niche) |
| Gbps/CPU = 18 Gbps / (72 × 0.5) = 0.5 | 415 | none | yes |
| CPU arithmetic: 10% of 64 cores ≈ 6 (407); 6.4% of 72 ≈ 4.6 CPUs, and ÷ 0.40 networking share gives 16% / 20% (415) | 407, 415 | none | yes |
| HTB TCP_RR: 800K/600K means "33% higher" without HTB. The Fig. 6 caption says "HTB is 30% lower", but 600/800 is 25% lower. | 407 | none | quick sanity check |
| Algorithm 1 as printed | 410 | ring buffers | **yes, with errata.** (a) Extract tests and pops `TW[now % N]` inside the loop; to sweep the overdue slots it should use `TW[FrontTimestamp % N]`. (b) Ts and now are divided by Granularity, i.e. in slot units, yet the code does `FrontTimestamp += Granularity`; in slot units that should be += 1. *(My reading; verify by implementing.)* |
| Fig. 17 units | 414 | none | **caveat:** the x-axis says "nanoseconds", but 8000 slots at 16000 on the axis implies µs for 2 µs slots. The min-rate curve does not fit one 1500 B packet per horizon (that would be ≈12 Mbps at 1 ms). It roughly fits 2 × 64 KB per horizon (≈1 Gbps at 1 ms). Treat it as qualitative: min rate ∝ 1/horizon and slots ∝ horizon. *(My reconstruction; unverified.)* |

Background assumed: token and leaky buckets, DRR, big-O for priority queues, TCP Small Queues and completion semantics, max-min fairness / water-filling. There is no queueing theory and no control theory.

Must reproduce: the LTS formula plus max-consolidation; wheel sizing (slots, max and min rate); the memory arithmetic with and without backpressure; Algorithm 1.

## 7. Numbers worth reusing

- Production video server: **37 Gbps** peak per server, tens of thousands of flows (p. 407). 25 servers in 5 sites; up to **38 Gbps** and **50,000 sessions** per server (p. 415).
- Pacing on: −40% retransmissions, +10% machine CPU (p. 407). QUIC at ~8 Gbps: CPU p99 0.15 → 0.20; retransmissions 2.6% → 1.6% (p. 407).
- Policer at a 1 Gbps target: up to 5× below target at 100 ms RTT even with a 1 s burst (pp. 406–407, Fig. 3).
- HTB: up to tens of thousands of classes at p90, 1000–2000 actively rate limited (p. 408). HTB queue limit 16K packets. FQ (paper's config) 10K global, 1000 per flow (p. 408, setup on p. 413).
- Hypervisor shaper: 2 Gbps, 50 ms RTT, 21K packets ≈ 32 MB, +120 ms. TSQ bound 128 KB ≈ 85 packets (p. 408).
- TSQ default "128KB = two 64 KB TSO" (footnote 2, p. 406).
- Wheel example: 8 µs × 500K = 4 s; 1.5 Gbps max per flow at 1500 B (p. 410). Evaluation wheel: **2 µs granularity, 2 s horizon** (1M slots) (p. 413). netem RTT **35 ms**; samples every 100 ms; neper load generator (p. 413).
- Timing-wheel CPU per packet: ~21–22 ns with std::list vs ~11–12 ns with the global pool, independent of 1K–20M packets (Table 1, p. 414).
- Receiver test: 100:1 incast (10 machines × 10 connections), base RTT ≈10 µs, within 1% of target (pp. 414–415).
- NBA update period ≈100 ms; 1% reserve (p. 412).
- Example from p. 405: 500 VMs × 50 endpoints = 25K VM-to-endpoint flows to isolate.

## 8. Linux mapping (kernel v7.2 at ~/workspace/repos/linux; lines grepped; commit tags from `git describe --contains`)

**What Linux adopted:** the *timestamp* half of Carousel (EDT) and its *backpressure* half (TSQ, which predates the paper). It did **not** adopt the *timing wheel* for host software queues. sch_fq still uses rbtrees and one hrtimer. A wheel appears only as an optional NIC offload that the kernel explicitly credits to Carousel.

| Carousel idea (page) | Linux v7.2 | Where |
|---|---|---|
| TCP stamps each packet with a release time (409–410) | **EDT**. TCP keeps `tcp_wstamp_ns`, writes it to skb->tstamp, and advances it by len/sk_pacing_rate after each send. Commits d3edd06ea8ea ("tcp: provide earliest departure time in skb->tstamp") and ab408b6dc744 ("switch tcp and sch_fq to new earliest departure time model"), both in **v4.20 (Sep 2018)**. | net/ipv4/tcp_output.c:1536 (`__tcp_transmit_skb`), 1553–1555 (stamp); 1446–1468 (`tcp_update_skb_after_send`, jitter credit 1463–1464) |
| "Delay-based CC should discount pacing delay" (412) | ab408b6dc744's message: with EDT "TCP can get more accurate RTT samples, since pacing no longer inflates them". The send timestamp is the intended departure time, so time spent waiting in fq is not counted in the RTT sample. | commit message (git show ab408b6dc744) |
| Pacing rate "2 × cwnd/RTT" (406, 410) | In 2017 this was already 200% if cwnd < ssthresh/2 and **120%** otherwise (43e122b014c9, v4.3, 2015). The paper simplifies. | net/ipv4/tcp_input.c:1138–1170; defaults at net/ipv4/tcp_ipv4.c:3501–3502 |
| Rate-limit module re-stamps packets; consolidation by max (410) | tc-BPF can write skb->tstamp (f11216b24219, **v5.0**). sch_fq dequeue uses max(skb time_to_send, f->time_next_packet), and applies its own `flow_max_rate` on top of EDT skbs. | net/sched/sch_fq.c:761–766; EDT/rate path 798–834 |
| Single time-indexed queue (410) | **Not a wheel.** sch_fq keeps per-flow FIFOs, or a per-flow rbtree `t_root` when timestamps are non-monotonic (comment at 66–67; insert at 476). Throttled *flows* (not packets) sit in the `q->delayed` rbtree keyed by `time_next_packet` (138, 222–238). One qdisc watchdog hrtimer is armed at `time_next_delayed_flow` (744–747) with `timer_slack` = 10 µs default (1248). The slack plays the role of Carousel's g_min. The cost is O(log #throttled flows), not O(1). | net/sched/sch_fq.c; watchdog in net/sched/sch_api.c:644–667 |
| Horizon: clamp to last slot or drop (410–411) | sch_fq `horizon` defaults to 10 s, `horizon_drop` = 1. Beyond the horizon fq either drops (`horizon_drops`) or caps tstamp to now+horizon (`horizon_caps`). These are exactly Carousel's two options. Commit 39d010504e6b (**v5.8**, 2020). | net/sched/sch_fq.c:540–543, 615–623, 1250–1251; stats 1366–1367 |
| Timing-wheel NIC offload (416, "designed for hardware offload") | `TCA_FQ_OFFLOAD_HORIZON` / `q->offload_horizon` lets fq hand packets due within the device's wheel horizon straight to the NIC. Commits f858cc9eed5b and f26080d47007 (**v6.13**, 2024), whose messages **cite the Carousel PDF by URL**. In v7.2 **no in-tree driver** sets `dev->max_pacing_offload_horizon` (grep found only include/linux/netdevice.h:2552, net/core/rtnetlink.c:2127, net/sched/sch_fq.c:1182). | net/sched/sch_fq.c:114, 320, 341, 669, 1182 |
| Deferred Completions (409, 411–412) | **TSQ** (46d3ceabd8d9, v3.6, 2012). The skb destructor `tcp_wfree` releases socket wmem only at TX completion. `tcp_small_queue_check` throttles a flow once sk_wmem_alloc exceeds max(2·truesize, pacing_rate >> sk_pacing_shift), capped at `tcp_limit_output_bytes`. TX completion goes through `tcp_wfree` → `tcp_tsq_handler`; paced sockets are re-kicked by `tcp_pace_kick`. | net/ipv4/tcp_output.c:1387 (`tcp_wfree`), 2857–2900 (check; THROTTLED at 2891), 1289 (`tcp_tsq_handler`), 1435 (`tcp_pace_kick`) |
| TSQ default "128 KB" (406, fn. 2) | History in the tree: 128 KB (v3.6), 256 KB (c39c4c6abb89, **v4.2, 2015**, i.e. already stale when the paper appeared), 1 MB (c73e5807e4f6, v5.0, 2018), **4 MB** (9ea3bfa61b09, **v6.16**, 2025). The effective per-flow limit is still ~1 ms of pacing rate (`sk_pacing_shift` = 10, net/core/sock.c:3800). Wi-Fi uses shift 7 (net/mac80211/main.c:951). | net/ipv4/tcp_ipv4.c:3491 |
| Completions across a VM/container boundary (411–412) | For veth/netns, skb->sk is preserved through `skb_scrub_packet` since 9c4c325252c5 (**v4.19**). Its message says losing it "breaks TSQ", so host-side qdisc delay backpressures the pod's socket. The EDT stamp also survives netns crossing when it is a mono delivery time (a1ac9c8acec1, **v5.18**; `skb_clear_tstamp` keeps it if `tstamp_type` is set). | net/core/skbuff.c:6278–6299; include/linux/skbuff.h:4507–4513; include/linux/netdevice.h:4440–4453 (`____dev_forward_skb`) |
| TSO autosizing, one TSO per ~1 ms (406) | `tcp_tso_autosize` = pacing_rate >> sk_pacing_shift, plus a min_rtt-based allowance (`tcp_tso_rtt_log` = 9, since v5.18), capped at `sk_gso_max_size`. **BIG TCP** raises that cap, so EDT release points carry larger bursts. | net/ipv4/tcp_output.c:2256–2271; net/ipv4/tcp_ipv4.c:3497 |
| SO_MAX_PACING_RATE, used for the FQ baseline (413) | sets `sk_max_pacing_rate` and marks the socket SK_PACING_NEEDED | net/core/sock.c:1253–1266 |
| FQ/pacing internals (406) | Hashed rbtrees: `fq_root[hash_ptr(sk, fq_trees_log)]` with 1024 buckets (405, 1244); DRR quantum 2×MTU, initial quantum 10×MTU (1229–1230); `fq_gc` (260). Defaults: limit 10000, **flow_limit 100** (1227–1228), whereas the paper configured 1000 per flow. The socket is flipped to SK_PACING_FQ at 399–401. | net/sched/sch_fq.c |
| One shaper per core, lock-free (412) | Partial analogue only. `mq` builds one child qdisc per TX queue (net/sched/sch_mq.c:91–92), and XPS maps CPUs to TX queues (net/core/dev.c:4621), so mq+fq gives one fq and one lock per queue. Each enqueue still takes the root lock (dev.c:4252); only pfifo_fast is `TCQ_F_NOLOCK` (net/sched/sch_generic.c:976). There is **no kernel NBA**: an aggregate rate spanning TX queues is not rebalanced. | as listed |
| HTB baseline (406–407) | `htb_enqueue` 620, `htb_dequeue` 942, `htb_do_events` 749, tokens via `psched_l2t_ns` 665/678. The watchdog hrtimer is armed at the next class event (993; default lookahead now+5 s at 964). The paper's "HTB's timer fires once every 10ms" (413) is **not** what v7.2's code structure does; it probably reflects their kernel or config (unverified). Hardware offload of HTB exists (`q->offload`, 1151). | net/sched/sch_htb.c |
| Policer (405–406) | `tcf_police_act` | net/sched/act_police.c:252 |
| Timestamp-ordered launch-time qdisc | sch_etf (rbtree by txtime) with SO_TXTIME: the device or qdisc honours an absolute launch time | net/sched/sch_etf.c:162, 253; net/core/sock.c:1613 |
| Varghese–Lauck timing wheel inside Linux | The **kernel timer wheel**: a hierarchical, non-cascading wheel of 64-bucket levels with granularity 8^level jiffies. It is used for coarse timeouts, **not** for packet pacing (pacing uses hrtimers). | kernel/time/timer.c:64–145 (design comment, HZ=1000 table at 104), 153–187 (LVL_* constants), 524 (`calc_index`), 541 (`calc_wheel_index`) |

**Cilium (not in the kernel tree; no Cilium checkout on this machine, so everything here is unverified against source):**
- Bandwidth Manager is Carousel's *rate-limit timestamper* moved into BPF. A tc BPF program on the host's native device computes a per-endpoint (pod) EDT. Roughly: t_next = max(now, t_last + len/rate), and drop if t_next − now exceeds a drop horizon. The rate comes from the `kubernetes.io/egress-bandwidth` annotation.
- It writes skb->tstamp and relies on **mq + fq** on the native device to enforce it. That is Carousel's "single time-indexed queue" replaced by fq.
- It enforces a **flow aggregate** (all of a pod's flows), which plain fq cannot do (paper p. 406: "FQ/pacing … does not support flow aggregates").
- "BBR for Pods" is documented by Cilium as needing kernel ≥ 5.18, which lines up with the v5.18 mono-delivery-time change above. *(The causal link is my inference.)*
- To check in the learner's fork: `bpf/lib/edt.h` (`edt_sched_departure`), the throttle map, and the bandwidth-manager Go package that sets fq and its horizon. Confirm the default drop horizon (I recall ~2 s; unverified).

## 9. Prerequisites assumed, and forward references

**Assumed, not defined:**
- token bucket and leaky bucket ([8] is a Wikipedia link)
- DRR [41]; RB-trees; the Linux qdisc architecture [10]
- TSO/GRO [20, 3]; TSQ [4]; virtio completions [40]
- SoftNIC/FlexNIC busy-polling NICs [24, 31]
- BwE [32], SWAN [25], EyeQ [30] as rate sources
- DCTCP (§6), TCP Vegas (§7.1.2), CUBIC; incast [12]
- water-filling and max-min fairness (§5.3)
- calendar queues [16], PIFO [42], VirtualClock [44]
- neper [7] and netem as tools

**Internal forward references:** §1 → §3 (costs), §4 → §5.1–5.3, §5.1.1 → §8 (consolidation limits), §5.1.2 → §7 (Table 1), §5.2 → §7 (backpressure comparison).

**Forward references for the guide:**
- **Eiffel** (NSDI 2019, same first author; inv-08). It generalizes Carousel's queue to programmable schedulers using integer priority queues (bucketed queues with bitmap find-first-set) and addresses the "not a generic scheduler" limitation on p. 416.
- **EDT in Linux** (v4.20), **sch_fq horizon** (v5.8), **fq pacing offload** (v6.13, citing Carousel).
- **Cilium Bandwidth Manager / BBR for pods.**
- **BBR** (inv-09/10), the main consumer of cheap pacing (cited as [17] on pp. 404, 405, 416).
- **EyeQ** (inv-09-eyeq): receiver-side and edge isolation, related to §6.

## 10. References worth reading (2–4)

- **[43] Varghese & Lauck, SOSP '87, "Hashed and Hierarchical Timing Wheels."** The data structure itself: simple, hashed and hierarchical schemes and their costs. It also explains the Linux kernel timer wheel (kernel/time/timer.c) and pins down the arithmetic for granularity vs horizon vs memory.
- **[44] L. Zhang, SIGCOMM '90, "Virtual Clock."** The ancestor of "schedule by computed transmission time". Carousel's LTS'_i = LTS_i + len/R_i is VirtualClock's auxVC update without the max(now, ·). Reading it explains the idle-credit gap noted in §6.
- **[5] and [4] LWN: "pkt_sched: fq: Fair Queue packet scheduler" (2013) and "TCP Small Queues" (2012).** The primary sources for the two Linux mechanisms Carousel benchmarks against and generalizes. Read them next to sch_fq.c and tcp_output.c in v7.2.
- (Optional) **[17] Cardwell et al., BBR (ACM Queue 2016)**, the consumer that makes per-flow pacing mandatory.

## 11. Suggested per-chapter spine

**Spine object:** one 1500-byte (or one 64 KB TSO) packet from a VM or pod's TCP flow travelling through **Fig. 10 / Fig. 11b (pp. 409, 411)**:
1. TCP stamps a pacing release time (LTS += len/(2·cwnd/RTT)).
2. The aggregate rate limiter pushes the stamp later (max).
3. The packet drops into a timing-wheel slot ⌊ts/g⌋.
4. It is extracted once now ≥ slot.
5. **Only then** does the completion return, letting TSQ release the flow's next packet.

Counterexample to set beside it: **Fig. 8 (p. 408)**. The same 2 Gbps, 50 ms flow *without* deferred completions piles up 21K packets (32 MB, +120 ms).

Linux re-run of the same path: TCP EDT (tcp_output.c:1553) → [veth: skb->sk and the mono tstamp preserved] → Cilium BPF re-stamp → host mq/fq (`time_next_packet`, `q->delayed`, watchdog) → `tcp_wfree` at TX completion → TSQ unthrottle.

**Candidate strands**
1. `timestamp-not-queue`: a rate limit can be expressed as a per-packet release time LTS' = LTS + len/R, and several policies compose by taking the **max** timestamp, which equals a chain of token buckets (p. 410).
2. `wheel-sizing`: a timing wheel needs horizon/g slots. Its maximum per-flow rate is ≈ (bytes per slot)/g and its minimum is ≈ packet/horizon. g cannot usefully be finer than the dequeue polling period (pp. 410, 414).
3. `deferred-completion-bounds-memory`: if the completion is withheld until the packet leaves the shaper, per-flow occupancy is bounded by TSQ (~2 packets), so shaper memory scales with flows rather than flows × cwnd (pp. 408, 411, 413).
4. `multiqueue-cost-is-intrinsic`: token-bucket shapers need one queue per rate limit (polled) and take a global lock per packet. That, not timer resolution, is why HTB and FQ cost CPU at high packets per second (pp. 407–408).
5. `horizon-policy`: a packet stamped beyond the horizon is either clamped into the last slot (good for pacing, causes rate overshoot) or dropped (hard rate limit). Linux sch_fq's horizon_caps vs horizon_drops is the same choice (p. 411; sch_fq.c:615–623).
6. `per-core-shaper`: one wheel per core removes locking. An aggregate spanning cores then needs a periodic water-filling reallocator (NBA, ~100 ms, 1% reserve) (p. 412).
7. `edt-in-linux`: Linux adopted Carousel's timestamps (EDT, v4.20) and backpressure (TSQ), but sch_fq keeps throttled *flows* in an rbtree with one hrtimer. A real timing wheel exists only as a NIC offload (fq offload_horizon, v6.13).

## 12. Exercise ideas

1. **Pen-and-paper wheel and EDT arithmetic (30 min).**
   - (a) Recompute the paper's example (8 µs, 4 s → 500K slots, 1.5 Gbps max) and reconcile the "1.5 Mbps minimum" claim with one packet per horizon (= 3 kb/s).
   - (b) The evaluation wheel (2 µs, 2 s): slot count, max rate for 1500 B and for 64 KB per slot.
   - (c) Linux sch_fq with timer_slack 10 µs: if one 64 KB GSO skb is released per slack window, what aggregate rate does it support (≈52 Gbps)? What about BIG TCP-sized skbs?
   - (d) A Cilium pod at 100 Mbit/s: inter-release gap of a 64 KB GSO skb (≈5.2 ms), and worst-case queued bytes under a 2 s horizon with no backpressure (≈25 MB).
   - (e) Show the idle-credit burst in the bare LTS formula: idle 1 s at 10 Mbit/s releases a 1.25 MB burst. Then fix it with max(now, ·).
2. **Python timing wheel vs heap (45–60 min; numpy/matplotlib).**
   - Implement Algorithm 1 and find and fix the two slips noted in §6.
   - Generate 1K–10K paced flows with random rates. Measure (i) the |release − scheduled| CDF vs granularity (2, 8, 32, 500, 4000 µs; compare Figs 16 and 18) and (ii) ns/packet vs heapq (an rbtree stand-in) as queued packets grow from 1K to 1M (compare Table 1).
   - Add the clamp-vs-drop horizon options.
3. **netns rate conformance, fq vs htb vs tbf (45–60 min; no iperf3, python sockets).**
   - Topology: veth pair between two netns. A python receiver counts bytes per 100 ms; python senders set `SO_MAX_PACING_RATE` (option 47) under `tc qdisc add dev v0 root fq`. Compare `htb` with one class at the same rate, and `tbf`.
   - Sweep 50/200/800 Mbit/s and 1/10/100/1000 flows. Plot absolute deviation (Fig. 12/13 style).
   - Watch `tc -s qdisc show dev v0` fq counters: `throttled`, `flows_plimit`, `horizon_drops`/`horizon_caps`, `latency` (unthrottle_latency_ns).
   - Watch `ss -tin` pacing_rate and notsent. Raise flow_limit to see the "FQ drops beyond 200 flows" effect turn into a parameter rather than a law.
   - Optional: bpftrace on `tracepoint:qdisc:qdisc_dequeue`, casting skbaddr to read `skb->tstamp`, to histogram dequeue lateness.
4. **kind + Cilium Bandwidth Manager as Carousel-in-BPF (45–60 min; no iperf3).**
   - Enable bandwidthManager, then annotate a pod `kubernetes.io/egress-bandwidth: 50M`.
   - On the kind node container: `tc qdisc show dev eth0` (expect mq/fq) and `cilium-dbg bpf bandwidth list` (or the equivalent in the learner's fork).
   - From the pod run python senders with 1, 10 and 100 flows to a receiver pod. Confirm the *aggregate* holds at ≈50 Mbit/s (the flow-aggregate case fq alone cannot do), and look at `ss -ti` inside the pod.
   - Then enable BBR for pods and repeat. Watch fq `horizon_drops` and pod-side retransmits.
   - Caveat: kind nodes share the host kernel (7.2.6), so the BPF and fq run in the host kernel inside the node's netns.

## 13. Honest assessment

**Read closely:**
- §2.3 FQ/pacing (p. 406), checked against v7.2 sch_fq. The structure survives; EDT, bands, fastpath and horizon were added.
- §3 cost numbers (pp. 406–408), especially the memory paragraph and Fig. 8.
- §4 tenets (pp. 408–409).
- §5.1 timestamps and timing wheel, with Algorithm 1 (pp. 409–411).
- §5.2 Deferred Completions (pp. 411–412), which is TSQ generalized; know it cold for the Cilium story.
- §7.1.3 granularity and horizon (p. 414).

**Skim:**
- §1 motivation (p. 404–405, beyond the definitions).
- §6 receiver ACK shaping (p. 412): niche, DCTCP-specific, and not what Linux or Cilium do.
- §7.2 production CPU numbers (pp. 415–416): Google-internal and not reproducible; remember only "~8% machine CPU, 12% SoftNIC".
- §8–9 (p. 416), except the Limitations paragraph.

**Outdated or caveated:**
- (1) The evaluated Carousel is in a **busy-polling software NIC**, not the kernel. The authors say a kernel version "would require re-engineering the kernel's Qdisc path" (p. 409), and Linux never did that.
- (2) "TSQ default 128 KB" (p. 406) was already 256 KB upstream in 2015. It is 4 MB in v7.2, with the real per-flow limit ~1 ms of pacing rate.
- (3) "Linux sets pacing rate to 2 × cwnd/RTT" (pp. 406, 410) has been 200/120% since v4.3.
- (4) FQ's "10K global / 1000 per flow" was their configuration; the v7.2 default per-flow limit is 100.
- (5) The claim that HTB's timer fires every 10 ms (p. 413) does not match v7.2's hrtimer watchdog.
- (6) The figure and arithmetic slips in Algorithm 1, the 1.5 Mbps example and the Fig. 17 units (see §6).

**Since the paper:**
- Linux EDT (v4.20, 2018, by Google's Eric Dumazet, who is thanked in the acknowledgments on p. 417).
- sch_fq horizon (v5.8).
- tc-BPF writable skb->tstamp (v5.0), which enabled Cilium's Bandwidth Manager.
- netns-preserved mono tstamps (v5.18).
- fq pacing offload with explicit Carousel credit (v6.13).
- Eiffel (NSDI 2019) generalizes the queue.
- Hardware timing-wheel NICs are what the offload hook targets. No mainline driver uses it in v7.2.

**Takeaway for this learner:** Carousel is the design rationale for what Cilium's Bandwidth Manager does: stamp per packet, enforce with one time-ordered structure, and backpressure through completions. sch_fq is the pragmatic kernel compromise. The timing wheel is the part the kernel left to hardware.
