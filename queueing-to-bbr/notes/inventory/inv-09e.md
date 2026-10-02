# Inventory 09e — EyeQ (Jeyakumar et al., NSDI 2013)

## 1. Facts

- **Citation:** Vimalkumar Jeyakumar, Mohammad Alizadeh, David Mazières, Balaji Prabhakar, Changhoon Kim, Albert Greenberg. "EyeQ: Practical Network Performance Isolation at the Edge." *10th USENIX Symposium on Networked Systems Design and Implementation (NSDI '13)*, Lombard, IL, April 2013, pp. 297–311. (The venue city and month are not printed in this PDF; they come from my memory. The footer reads only "10th USENIX Symposium on Networked Systems Design and Implementation (NSDI '13)".) Affiliations: Stanford, Insieme Networks, Windows Azure. Code at http://jvimal.github.com/eyeq (p.298). The earlier HotCloud 2012 version is ref [26].
- **PDF pages:** 15 (pdfinfo).
- **Printed page numbers:** yes, in the USENIX footers.
- **Printed range:** 297–311.
- **Offset:** **this PDF has NO USENIX cover page.** PDF page 1 is the title/abstract page, footer 297. **printed = PDF + 296.** Checked on rendered pages: PDF 1 = p.297, PDF 2 = p.298, PDF 3 = p.299, PDF 6 = p.302, PDF 7 = p.303, PDF 9 = p.305, PDF 12 = p.308.
- **Two text-extraction traps:**
  - The text layer carries a second, invisible page sequence, centred numbers "2"…"15" left over from the preprint. They do not render, so ignore them and cite 297–311.
  - **PDF page 9 (p.305) has no extractable body text.** Only its footer is in the .txt files. §5.1's start (testbed, convergence test, CPU and latency vs htb) and Figs 6–7 must be read from the rendered page.

## 2. Sections (printed pages)

| Section | Pages |
|---|---|
| Abstract, §1 Introduction (the EyeQ model, the arbitration mechanism, Fig 1) | 297–298 |
| §2 Predictable Bandwidth Partitioning | 298–300 |
| §2.1 EyeQ's bandwidth guarantees (hose constraint fn.1) | 299 |
| §2.2 Rate guarantees at short timescales (Fig 2) | 299–300 |
| §2.3 The Fat and Flat Datacenter Network (Figs 3–4) | 300 |
| §3 EyeQ Design | 300–303 |
| §3.1 Detecting and Resolving Contention (Fig 5) | 301 |
| §3.2 Receiver EyeQ Module | 301–302 |
| §3.3 Sender EyeQ Module | 302 |
| §3.4 Rate Control Loop (control law, logistic-map stability, ECN term, DCTCP/QCN comparison) | 302–303 |
| §3.5 EyeQ on a network (admission constraints, best-effort class) | 303 |
| §4 Implementation; §4.1 REM (pp.303–304); §4.2 SEM (multi-queue rate limiter, rate-limiter accuracy/LSO) (p.304) | 303–304 |
| §5 Evaluation (overview p.304) | 304–308 |
| §5.1 Micro Benchmarks (testbed, convergence Fig 6, CPU and latency vs htb Fig 7, 20k flows) | 305–306 |
| §5.2 Macro Benchmarks; §5.2.1 all-to-all shuffle (Fig 8, p.306); §5.2.2 memcached (Table 1, pp.306–307) | 306–307 |
| §5.3 Congestion in the Fabric (ns2, Fig 9) | 307–308 |
| §6 Related work; §7 Concluding Remarks; Acknowledgments | 308 |
| References [1]–[45] | 309–311 |

## 3. Terms introduced

1. **Dedicated-switch abstraction**: each tenant should see its endpoints as if a private switch connected them, limited only by endpoint capacities. p.297.
2. **Hose constraint / hose model**: guarantees are per endpoint (ingress and egress capacity), not per pair, as with a dedicated switch. p.299, footnote 1 (contrasted with the "pipe" model on p.308).
3. **Minimum/maximum bandwidth guarantee (per vNIC)**: what the administrator configures. The minimum is what allows work-conserving sharing among co-located VMs. p.298. EyeQ aims at an *average-rate* guarantee over an interval "as short as possible". p.299.
4. **Admissible traffic**: sources never send more, in aggregate, to a sink than the bottleneck capacity. TCP keeps traffic admissible, and EyeQ enforces it. p.299 (enforced), defined p.300.
5. **High bisection bandwidth / "fat and flat" network**: Clos-like fabrics oversubscribed (<3:1) only at the ToR, with uniform capacity between racks. pp.297, 300.
6. **Edge vs core congestion**: the paper's terms are "first point of contention" (p.301) and "bottleneck port (the receiver)" (p.299). It never says "congestion point". Its claim is that persistent congestion appears only at access links. p.300.
7. **SEM (Sender EyeQ Module)**: a WRR/WFQ root scheduler with per-endpoint aggregate rate limiters and leaf per-destination rate limiters. pp.298 (Fig 1), 301 (Fig 5), 302.
8. **REM (Receiver EyeQ Module)**: rate meters plus an RX scheduler plus a feedback generator. pp.298, 301–302.
9. **Rate meter**: a per-endpoint byte counter read every 200 µs. The paper also calls these "congestion detectors" (p.306). p.302.
10. **RX scheduler / per-VM virtual link capacity**: splits the receive link among *active* VMs, C_i = B_i·C/Σ_{j∈A}B_j. p.302.
11. **Per-destination rate limiter**: a sender-side token bucket created only when a destination sends congestion feedback, so uncongested destinations are not head-of-line blocked. pp.301–302, 304.
12. **HACK (host-ACK)**: a 64 B feedback packet on IP protocol 143 carrying a 16-bit rate in the IPID field, sampled once per 10 kB received. p.302.
13. **Receiver-side detection, sender-side reaction**: the core design rule, because rate limiting at the receiver only works against transports that back off. p.301.
14. **RCP (Rate Control Protocol)**: an explicit-rate congestion control. EyeQ runs a variant per virtual link instead of per network link. First mentioned p.300, variant on p.302.
15. **Logistic map**: the 1-D nonlinear recurrence z[n+1] = b·z[n](1−z[n]) that EyeQ's update reduces to. p.302, footnote 2.
16. **Bandwidth headroom (10%)**: capacity kept unused so queues stay short, needed because the testbed switch has no ECN. pp.299, 305, 306.
17. **TX-context / multi-queue (per-CPU) rate limiter**: per-endpoint sender state, with token buckets whose FIFO is split per CPU and tokens borrowed from a shared pool. p.304.

## 4. Core claims

1. TCP shares bandwidth per flow and knows nothing about tenants. EyeQ gives each endpoint min/max guarantees, as if it had a dedicated switch, without changing applications or switches (pp.297–298).
2. Guarantees must hold over milliseconds. A UDP tenant that averages 2.5 Gb/s (10 Gb/s on for 5 ms, off for 15 ms) raises a co-located TCP tenant's median and 99th-percentile latency by more than 10x, even though it stays under its 3 Gb/s share. With EyeQ, latency is about 55 µs (pp.299–300, Fig 2).
3. With high bisection bandwidth, randomized routing and admissible traffic, persistent congestion occurs only at access links. Azure storage data (5-minute averages, 20 racks, one week) shows higher peak and variance on edge links than core links (p.300, Fig 4). ns2 shows per-packet ECMP keeps core queues under 50 kB at 90% load (pp.307–308, Fig 9).
4. Contention at the receiver happens inside the switch, invisible to both hosts, and a 1 MB shared buffer fills in 800 µs. So EyeQ meters at the receiver every 200 µs and enforces at the sender, because a receiver cannot slow UDP (p.301).
5. The rate update R ← R(1 − α(y−C)/C) needs no estimate of the number of senders or their demands. Run per virtual link, it avoids RCP's per-flow max-min unfairness (p.302).
6. For N long-lived flows on one link, the update is a logistic map whose fixed point R* = C/N is stable when 0 < α < 2. Near R* the error shrinks by a factor (1−α) per step. With α = 0.5 it reaches 0.01% in about 30 iterations, at most 6 ms at 200 µs per step. DCTCP- and QCN-style loops took 100–150 ms and 20–30 ms (pp.302–303).
7. Feedback traffic is bounded at 64 Mb/s on a 10 Gb/s link no matter how many senders there are (p.302).
8. Per-CPU token-bucket queues with a single 50 µs per-CPU timer use 1.5x less CPU than Linux htb. htb's single lock raises median latency 2.2x at low load (pp.304–305, Fig 7).
9. Against 14 UDP senders starting at full rate (a 14x incast), EyeQ converges within 5 ms and protects the TCP tenant's guarantee (p.305, Fig 6).
10. With a bursty UDP tenant, memcached's 99.9th-percentile latency is 1.1 s without EyeQ and 750 µs with it (666 µs on a dedicated cluster). The price is the 10% headroom (Table 1, p.307; takeaways pp.307).

## 5. Figures and examples worth redrawing

| Fig | Page | Shows | Why it matters |
|---|---|---|---|
| 1 | 298 | Flows F1, F2, F3 across SEMs and REMs. Guarantees A=2 and B=8 Gb/s; F1 gets 10, then 2; F2 gets 8, then 5 when F3 starts; spare 3 goes back to F1 | The best worked example of distributed, work-conserving min-guarantees. Redraw it as a timeline |
| 2 | 299 | (a) TCP and UDP VMs sharing a 10G receiver link split 6:3; (b) UDP on/off at 5 ms/15 ms; (c) latency CDF with and without EyeQ | The "averages hide bursts" argument, and the most transferable lesson for `tc -s` diagnosis |
| 3–4 | 300 | Spine/ToR fabric; CDF of 5-minute link utilization, core vs edge | The edge-congestion premise |
| 5 | 301 | SEM (rate limiters 3 and 7 Gb/s under WFQ) and REM (rate meters 3 and 6 Gb/s), with feedback forming end-to-end flow control | The architecture. Redraw next to Cilium's datapath (§8) |
| 6 | 305 | TCP vs UDP rate sampled every 1 ms over 0–50 ms. TCP runs at about 9G, then UDP starts at about 15 ms on the plot (the text says "t=30s", an inconsistency), and both settle near 4.5G within about 5 ms | Shows convergence speed and the 10% headroom (9G, not 10G) |
| 7 | 305 | (a) CPU% EyeQ vs htb across packet sizes; (b) latency CDF, htb vs EyeQ limiter | The cost of a global qdisc lock, which still matters for HTB today |
| Table 1 | 307 | memcached p50/p99/p99.9 in four scenarios | Tail-latency numbers to reuse |
| 9 | 307 | Queue-occupancy CDFs, edge vs core, per-flow vs per-packet ECMP | Packet-level support for §2.3 |

## 6. Maths

| # | Item | Page | Background | Reproduce? |
|---|---|---|---|---|
| E1 | On/off average: 10 Gb/s × 5/(5+15) = 2.5 Gb/s (25%) | 299 | — | **Yes** |
| E2 | Buffer fill: two 10G ports into one, with 1 MB shared buffer, gives 10 Gb/s of excess, so 8·10^6 bit / 10^10 bit/s = **800 µs** | 301, 304 | — | **Yes** |
| E3 | RX scheduler: **C_i = B_i·C / Σ_{j∈A} B_j** (A = VMs receiving at non-zero rate) | 302 | Weighted proportional share | **Yes** |
| E4 | Feedback budget: one 64 B HACK per 10 kB gives 10 Gb/s ÷ 80 kbit = 125k HACK/s; × 512 bit = **64 Mb/s** | 302 | — | **Yes** |
| E5 | Ideal rate for N long-lived senders: R_i = C_i/N | 302 | Max-min | Yes |
| E6 | **Control law: R_i ← R_i·(1 − α·(y_i − C_i)/C_i)**, keeping R_i positive | 302 | Multiplicative update, RCP | **Yes** |
| E7 | **Stability:** with N flows on unit capacity, R[n+1] = R[n](1 + α − αN·R[n]). Substituting z[n] = ((b−1)/b)·R[n]/R*, R* = 1/N, b = 1+α gives **z[n+1] = b·z[n](1−z[n])**. R* is the unique stable fixed point iff **1 < b < 3, i.e. 0 < α < 2** | 302–303 | Fixed points, \|f′\| < 1, logistic map | **Yes, in a toggle**. Derive the substitution, then f′(R*) = 1 + α − 2αN·R* = 1 − α, so \|1−α\| < 1 ⇔ 0 < α < 2 |
| E8 | **Linearization: R[n] ≈ R* + (R[0]−R*)(1−α)^n**, linear convergence. With α = 0.5, within 0.01% "in about 30 iterations, irrespective of R[0]". Worst case 30 × 200 µs = **6 ms** | 303 | Geometric decay | **Yes**. The linear part alone gives n = ln(10⁻⁴)/ln(0.5) ≈ 13.3. The rest of the ~30 is the nonlinear transient: from far below R*, R grows at most 1.5× per step; from far above, the factor 1 − α(y−C)/C goes **negative** once y > C(1+1/α) = 3C, hence the "keep R positive" clamp. My simulation (α = 0.5, N = 1…100, R[0] from 10⁻³ to 1, floor clamp) gives 20–32 iterations, matching "about 30". α = 1 is fastest in the delay-free model (1−α = 0); α ≥ 2.1 diverges. The paper's observation that high α oscillates in practice comes from feedback delay and noise, which the model leaves out |
| E9 | ECN degradation: **R_i ← R_i(1 − β/2)**, β = fraction of marked packets | 303 | DCTCP | Yes. Same form as DCTCP's cwnd·(1 − α/2) (§8) |
| E10 | Admission: Σ guarantees on a server < 10 Gb/s; Σ guarantees under a ToR < ToR uplink capacity | 303 | Hose model | Yes |
| E11 | Timer and tokens: 50 µs at 10 Gb/s is 62.5 kB ("at most 64kB"). A 64 kB TSO chunk at 10 Gb/s takes **51.2 µs** (using 64 kB = 64,000 B; 65,536 B would take 52.4 µs). Limited to 1 Gb/s, that is one chunk per **512 µs**. Capping LSO at 32 kB gives 256 µs | 304 | — | **Yes** |
| E12 | Convergence scenario: N = 14 senders at 10 Gb/s make a 10N Gb/s incast; each settles to 5/N Gb/s | 305 | — | Yes |
| E13 | Shuffle: S TB over N nodes moves S/(N(N−1)) TB per ordered pair | 306 | — | Yes |

**Background assumed for the maths:** discrete-time dynamical systems (fixed points, linearization, stability when \|f′\| < 1), the logistic map, max-min and weighted proportional fairness, token buckets.

**Caveats to teach:**
- The stability result assumes N identical long-lived flows, no feedback delay and noiseless meters.
- Units for the 16-bit rate field are not specified (p.302).
- §3.1 calls the sender scheduler WFQ (p.301), while Fig 5's caption and §3.3 say WRR (pp.301–302).

## 7. Numbers worth reusing

- 8–32 services or VMs per server (p.301). Oversubscription below 3:1, only at the ToR (p.300). Azure data covers 20 racks for one week at 5-minute averages (p.300).
- A 1 MB shared buffer fills in 800 µs (2→1 at 10G). Rate meter every **200 µs**. Feedback sampled per **10 kB**. HACK is 64 B, so feedback is at most **64 Mb/s** on 10G. 16-bit rate in IPID. IP protocol **143** (p.302; pp.301, 304).
- Without feedback for **100 ms**, a limiter halves its rate, down to a **1 Mb/s** floor (p.302).
- **α = 0.5**, about 30 iterations to 0.01%, **6 ms** worst case. DCTCP-style 100–150 ms, QCN 20–30 ms (p.303).
- Per-CPU timer every **50 µs** (64 kB per tick at 10G). Per-CPU FIFO capped at **128 kB**. LSO 64 kB takes 51.2 µs; LSO capped at **32 kB**; below 1 Gb/s, packets are split to MTU (1500 B) (p.304).
- Linux qdisc module: about 1900 lines of C plus 700 header lines. RX hook via `netdev_rx_handler_register` (p.303).
- Testbed (p.305): 16 servers, quad-core 2.4 GHz Xeon, **Linux 3.4**, 10GbE, one 24-port switch with **20 kB dedicated per port + 2 MB shared**, no ECN so **10% headroom**, LSO on, RSS with 4 queues.
- Convergence within **5 ms** for N = 14 (Fig 6). CPU: **1.5x** lower than htb, about equal at 32 kB packets. htb raises median latency **2.2x** (512 netperf processes, about 10 Mb/s, limiter at 5 Gb/s) (p.305). 20,000 flows on 1 to 10,000 limiters at a 5 Gb/s root use the same CPU (p.306).
- Shuffle: jobs P1/P2/P4 open 1/2/4 connections per pair; guarantees B1:B2:B4 = 4:2:1; last job finishes in 210 s instead of 180 s (p.306).
- memcached (pp.306–307): 288k req/s (6000/s per client per instance), 6 kB values, 32 B keys, 4 servers plus 12 clients with 10 connections per thread. With UDP (0.5 s bursts, about 5 Gb/s average) it manages only **269k req/s**. **Table 1 (144k req/s), p50/p99/p99.9 in µs:** Bare 98/370/666; Bare+EyeQ 100/333/630; Bare+UDP 4127/0.89×10⁶/1.1×10⁶; Bare+UDP+EyeQ 102/437/750.
- Servers are over 60% of datacenter cost; the network is 10–15% (p.307).
- ns2 (p.307): 144×10GbE hosts, 9 ToRs, 16 spines, λ = 0.9. Flow sizes: median 19 kB, mean 2.4 MB, p90 133 kB. Queues of 150 packets (225 kB) sampled every 1 ms. Per-packet ECMP keeps core queues under 50 kB.
- Related work: Oktopus reacts in about 2 s; NetShare is limited to 8–64 queues per port (p.308).
- Derived (mine): 200 µs at 10G is 250 kB, about 25 HACK samples per window at line rate. The 800 µs fill time is 4 meter windows. The Linux rate estimator (gen_estimator) has a 250 ms minimum interval, 1250x coarser than EyeQ's meter.

## 8. Linux and Cilium mapping (kernel v7.2 at `~/workspace/repos/linux`; user's Cilium fork at `~/workspace/neverinstall/cilium`, v1.19.6-vpc.24; all grep-verified)

**Receiver-side enforcement exists today, but without feedback, which is the design EyeQ argues against (p.301):**
- **Cilium `kubernetes.io/ingress-bandwidth`** is a **token-bucket policer that drops at local delivery**. `accept()` is at bpf/lib/token_bucket.h:16 and is called for `METRIC_INGRESS && !from_host` at bpf/lib/local_delivery.h:149–158. Refill and cap at token_bucket.h:42–44 (**bucket depth = `bps` bytes, one second's worth**), drop at `:46–49`, and the comment "For now the map is not thread safe" at `:13`. Docs: Documentation/network/kubernetes/bandwidth-manager.rst:33–37 ("ingress-bandwidth is enforced using an eBPF-based token bucket implementation"). The annotation is in pkg/datapath/linux/bandwidth/bandwidth.go:32, with `UpdateIngressBandwidthLimit()` at `:133`. Units: `GetBytesPerSec()` divides bits by 8.
  - Through EyeQ's lens: it detects *and* enforces at the receiver, so a UDP sender is not slowed. Its packets still crossed the bottleneck queue upstream, and only TCP backs off. Its 1 s burst allowance is the opposite of EyeQ's sub-ms timescale argument (pp.299–300). Example: "20M" means 2.5 MB/s, so a 2.5 MB bucket, so **about 2 ms of 10 Gb/s line-rate burst passes unpoliced**. Nothing sends rate feedback to the sending node.
- Kernel tools in the same category (receiver-side, no cross-host feedback): tc ingress policing `tcf_police_act()` at net/sched/act_police.c:252 (token refill at `:283`); ingress shaping through `drivers/net/ifb.c`. In-band receiver-to-sender signals are only the TCP receive window and ECN echo. **No receiver-driven transport upstream:** no `IPPROTO_HOMA` or `net/homa` in v7.2.
- **Nothing in v7.2 or this Cilium tree implements EyeQ-style receiver metering with sender-side, per-destination enforcement.** As far as I know this lives only in proprietary vSwitches. PicNIC (SIGCOMM 2019) is the published descendant; it is outside this paper, from my memory, and must be verified before it is taught.

**Sender-side enforcement maps to the SEM:**
- **Cilium egress EDT**, bpf/lib/edt.h:65 `edt_sched_departure()`: `delay = wire_len·NSEC_PER_SEC/bps` (`:93`), `t_next = t_last + delay` (`:94`), horizon drop (`:104–105`), `ctx->tstamp = t_next` (`:107`), called on host egress at bpf/bpf_host.c:1666 (overlay at bpf/bpf_overlay.c:836). This is EyeQ's per-endpoint *root* limiter done with timestamps instead of tokens. There are no feedback-driven per-destination leaf limiters, so it enforces a static egress cap, not a hose guarantee.
- **Parallel with EyeQ's multi-queue limiter (p.304).** EyeQ splits the FIFO per CPU and borrows tokens from a shared, locked pool. Cilium puts one fq per TX queue (mq root, pkg/datapath/linux/bandwidth/ops.go:113–145) and keeps one shared `t_last` per endpoint in a BPF hash map updated with `READ_ONCE`/`WRITE_ONCE` and no lock (edt.h:94–107). Same idea of per-queue queues with global rate state; Cilium accepts benign races where EyeQ took a lock. This makes a good strand.
- Per-flow and per-socket caps: sch_fq `flow_max_rate` (net/sched/sch_fq.c:119; applied at `:796–833`); `SO_MAX_PACING_RATE` (net/core/sock.c:1253, value 47).
- htb's single lock (Fig 7) remains the contention point. HTB offload (`bool offload` at net/sched/sch_htb.c:183, set at `:1151`) and mq+fq per queue are today's ways around it.

**Implementation details that Linux later solved differently:**
- **LSO burstiness (p.304) is solved by TSO autosizing.** `tcp_tso_autosize()` at net/ipv4/tcp_output.c:2256 sizes each TSO skb to `sk_pacing_rate >> sk_pacing_shift` (`:2262`), with `sk_pacing_shift = 10` by default (net/core/sock.c:3800), i.e. about 1 ms of data, plus a small-RTT term. At a 1 Gb/s pacing rate that is about 122 kB, capped by gso_max_size. At 100 Mb/s it is about 12 kB. EyeQ's hand-tuned "32 kB, and MTU below 1 Gb/s" is now automatic.
  - **BIG TCP tie-in:** Cilium's `bigTCPMaxSize = 196608` (pkg/datapath/linux/bigtcp/bigtcp.go:27). A 192 KiB skb takes 157 µs at 10 Gb/s and 1.57 ms at 1 Gb/s, but autosizing only produces skbs that large once pacing_rate × 2⁻¹⁰ ≥ 192 KiB, i.e. at about 1.6 Gb/s.
- **The rate meter** compares to `gen_estimator` (net/core/gen_estimator.c:76 `est_timer`, `:132` `gen_new_estimator`). Its minimum period is 250 ms (`:148–167`), so `tc -s` rates cannot see EyeQ-scale bursts. This is a direct diagnosis lesson from Fig 2.
- **The ECN term** R(1−β/2) has the same form as DCTCP's `dctcp_ssthresh()`: `cwnd − (cwnd·alpha)>>11` with alpha scaled to 1024 (net/ipv4/tcp_dctcp.c:118–124).
- **The RX hook** `netdev_rx_handler_register()` still exists (net/core/dev.c:5909).
- **The HACK protocol number:** 143 was "the first unused IP protocol number" in 2013. Linux now defines `IPPROTO_ETHERNET = 143 /* Ethernet-within-IPv6 Encapsulation */` (include/uapi/linux/in.h:80). (That IANA assigned it for SRv6, RFC 8986, is from my memory.) A reimplementation today would need a different number.

## 9. Prerequisites and forward references

**Assumed:** TCP congestion control and per-flow fairness; max-min and weighted fairness; WFQ/WRR; token buckets; datacenter fabrics (Clos, ECMP, ToR oversubscription); shallow-buffer switches; ECN, DCTCP, QCN, RCP; hose vs pipe models; the hypervisor vSwitch / Dom0 placement; NIC offloads (LSO/TSO, RSS, interrupt coalescing); the logistic map (only for §3.4).

**Forward references:**
- **Within this guide:** Carousel and Eiffel replace token buckets with timestamps (Eiffel p.24 claims timestamps adhere to rates better than token buckets); EDT and fq; TSO autosizing; Cilium Bandwidth Manager egress EDT and ingress token bucket; BIG TCP; BBR as another rate-based control loop.
- **Outside the paper, from my memory, to verify before teaching:** BwE (Kumar et al. 2015, cited by Eiffel [40]); PicNIC (2019); receiver-driven transports (pHost, NDP, Homa; none upstream in v7.2).

## 10. References worth reading

1. **[27] Dukkipati & McKeown, "Why flow-completion time is the right metric for congestion control" (RCP), CCR 2006, together with [29] Kelly, Raina, Voice, "Stability and fairness of explicit congestion control with small buffers," CCR 2008.** These are the source of the control law and its proper stability analysis, including feedback delay, which EyeQ's analysis leaves out.
2. **[18] Shieh et al., "Sharing the Data Center Network" (Seawall), NSDI 2011.** Per-source-VM weighted sharing, the foil EyeQ positions against: a tenant can grab more bandwidth by launching more VMs (p.308).
3. **[3] Ballani et al., "Towards Predictable Datacenter Networks" (Oktopus), SIGCOMM 2011.** The origin of the hose model and a static, centralized rate computation that takes about 2 s to react (p.308). Read it to see why EyeQ insists on milliseconds.
4. **[22] Alizadeh et al., "Less is More" (HULL), NSDI 2012.** Where the 10% headroom comes from (phantom queues). This links to the CoDel and latency-vs-throughput thread of the main chain. ([21] DCTCP is the other natural companion.)

## 11. Suggested spine and strands

**Spine** (a case study inside a "rate limiting at the edge / Cilium Bandwidth Manager" chapter):
1. The tenant problem: per-flow TCP fairness is not per-tenant fairness; the dedicated-switch and hose abstraction (pp.297–299).
2. Averages lie: the on/off UDP experiment, and why 100 ms or 250 ms meters miss 5 ms bursts (pp.299–300). Tie to `tc -s` and gen_estimator.
3. Where congestion lives: fat fabrics push it to the access links, so per-tenant state can stay in hosts (p.300; §5.3 pp.307–308).
4. Detect at the receiver, enforce at the sender: SEM, REM, HACK, and the reason receivers cannot police UDP (pp.301–302).
5. The control loop: the update law, the logistic-map stability argument, the convergence rate, the choice α = 0.5 (pp.302–303). Maths in a toggle.
6. Making it run at 10G: per-CPU token buckets, a 50 µs timer, and LSO burstiness (p.304). Then Linux's answers: TSO autosizing, EDT and fq, mq.
7. Evidence: 5 ms convergence, CPU vs htb, memcached tail (pp.305–307).
8. Today: Cilium egress EDT matches the SEM root limiter; Cilium ingress token bucket is receiver-side policing with a 1 s burst and no feedback. What a modern EyeQ would need.

**Strands:**
- `eyeq-short-timescale`: a 10 Gb/s on 5 ms / off 15 ms sender averages 2.5 Gb/s yet inflates a co-located TCP tenant's latency by more than 10x. Isolation must act at ms or finer (p.299).
- `eyeq-edge-congestion`: with high bisection bandwidth, randomized routing and admissible traffic, persistent congestion appears only at access links, so per-tenant state can live at the edge (p.300).
- `eyeq-detect-recv-enforce-send`: a receiver can detect contention but cannot slow UDP. EyeQ meters at the receiver and rate-limits per destination at the sender (p.301).
- `eyeq-rcp-stability`: R ← R(1 − α(y−C)/C) maps to the logistic map with b = 1+α. It is stable for 0 < α < 2, and near R* the error shrinks by (1−α) per 200 µs step (pp.302–303).
- `eyeq-capacity-split`: C_i = B_i·C/Σ_{active}B_j gives weighted, work-conserving shares among active receivers (p.302).
- `eyeq-lso-burst`: 64 kB of TSO at 10 Gb/s is 51.2 µs, so a 1 Gb/s limit releases one burst every 512 µs and breaks a 200 µs meter. Linux's TSO autosizing (pacing_rate >> 10) is the general fix (p.304; tcp_output.c:2256).
- `eyeq-cilium-ingress`: Cilium's ingress-bandwidth is a receiver-side token-bucket policer with a 1 s bucket and no feedback, the design EyeQ argues fails for non-responsive senders (token_bucket.h:16; EyeQ p.301).

## 12. Exercise ideas

1. **Pen and paper (30 min).** (a) Buffer fill time for 2→1 and 3→1 at 10G with 1 MB (800 µs, 400 µs). (b) HACK budget at 10G and 100G (64 and 640 Mb/s). (c) Derive the logistic map from the update, find R*, show f′(R*) = 1−α, and count iterations to 0.01% for α = 0.5 (13.3 from linearization), then explain the paper's 30. (d) TSO arithmetic: 64 kB and 192 KiB skbs at 1 and 10 Gb/s, then `tcp_tso_autosize` at 100 Mb/s, 1 Gb/s and 10 Gb/s. (e) Cilium ingress "20M": bucket size and how long a line-rate burst passes unpoliced at 10G.
2. **Python (40 min), the control loop.** Simulate N senders under the EyeQ update with a meter interval, a feedback delay of d steps, meter noise and the positivity clamp. Sweep α to show the stability edge at α = 2 with d = 0, and show it shrinking as d grows, which explains the conservative choice of 0.5. Add the ECN term. Plot with matplotlib.
3. **Lab (60 min), reproduce Fig 2 on veth.** Namespaces `tcpA`, `udpB`, `sw` and `rx`. On the `sw→rx` port put `tbf rate 100mbit burst 16k limit 64k`, a shallow "switch" buffer. Run a python TCP 1-byte ping-pong (timing with perf_counter_ns) and a python UDP on/off blaster (5 ms on as fast as possible, 15 ms off). Measure p50/p99.
   - (i) Baseline. Watch `tc -s qdisc` backlog and drops, and note that the 1 s averages look harmless.
   - (ii) Receiver-side policer: `tc qdisc add dev rx-eth ingress` plus a u32 match on ip protocol 17 with `action police rate 30mbit burst 1m drop`, emulating Cilium ingress-bandwidth. Latency stays bad because the queue is upstream.
   - (iii) Sender-side: `fq maxrate 30mbit` or tbf on the UDP sender's egress. Latency recovers.
   This reproduces EyeQ's core claim with no iperf3. Optional (kind + Cilium with bandwidthManager.enabled): annotate a pod with egress and ingress bandwidth, then inspect `cilium-dbg bpf bandwidth list` and `tc -s qdisc show dev eth0` in the node container (mq/fq leaves, horizon 2 s).
4. **Code reading (20 min).** Compare EyeQ's per-CPU token bucket (p.304) with Cilium's `edt_sched_departure` (edt.h:65) and `accept()` (token_bucket.h:16). For each, write down where the rate state lives, whether it is locked, what burst it allows, and what happens to a non-responsive UDP sender.

## 13. Honest assessment

- **This is a detour from the main chain.** EyeQ is not a step in AIMD → CoDel → TSQ/fq → pacing → EDT → BBR. It is about multi-tenant isolation and receiver-driven rate allocation, and its fabric premise (§2.3, §5.3) is datacenter-specific and dated (Linux 3.4, 10G, no ECN).
- **What it adds if kept:**
  - **The edge-enforcement argument.** It says why per-tenant rate state belongs on the host, which is exactly where Cilium's Bandwidth Manager lives.
  - **"Detect at the receiver, enforce at the sender".** This explains a real, checkable limitation of Cilium 1.19's ingress-bandwidth: a receiver-side token-bucket policer with a 1 s burst and no feedback. That is directly useful for finish line 4.
  - **A clean, small control loop with real maths:** the logistic-map stability condition 0 < α < 2 and the (1−α)^n convergence. It is good "some maths" practice and a warm-up for rate-based thinking before BBR (finish line 3).
  - **Two diagnosis lessons for finish line 2:** "averages hide bursts", i.e. ms-scale contention invisible to 250 ms `tc` estimators (Fig 2), and LSO/TSO burstiness against rate meters, which Linux fixed with TSO autosizing and EDT and which ties into BIG TCP knobs.
- **Read closely:** pp.299–300 (§2.2 and Fig 2); pp.301–303 (§3.1–3.4, control law and stability); p.304 (§4.2, multi-queue limiter and LSO accuracy); p.305 (Figs 6–7, from the rendered page, since the text layer is empty).
- **Skim:** §1 (pp.297–298, but redraw Fig 1); §2.3 and §5.3 (the fabric argument: take the conclusion, skip the data); §3.5 (p.303).
- **Skip:** §5.2 macro benchmarks except Table 1; §6 related work except the Seawall and Oktopus paragraph; the references to the Windows VMSwitch driver.
- **Recommendation: KEEP, but MERGE** as a one-session case study inside the Cilium Bandwidth Manager / edge rate-limiting chapter, with the control-loop maths in a toggle. It should not be a standalone chapter, and it should not sit in the main BBR chain.
