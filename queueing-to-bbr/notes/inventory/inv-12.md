# Inventory 12: Maglev (Eisenbud et al., NSDI 2016)

Source PDF: `/home/wazir/Documents/Books/networking/routing-papers-bbr/12-maglev.pdf`
Text: `/tmp/qbbr/12-maglev.txt` (layout), `/tmp/qbbr/12-maglev.raw.txt`
Check scripts written for this inventory: `/tmp/qbbr/maglev_table1.py` (Table 1 and removal variants), `/tmp/qbbr/maglev_check.py`, `/tmp/qbbr/maglev_check2.py` (Figure 12 reproduction)

## 1. Facts

- **Citation:** Daniel E. Eisenbud, Cheng Yi, Carlo Contavalli, Cody Smith, Roman Kononov, Eric Mann-Hielscher, Ardas Cilingiroglu, Bin Cheyney, Wentao Shang, Jinnah Dylan Hosein. "Maglev: A Fast and Reliable Software Network Load Balancer." 13th USENIX Symposium on Networked Systems Design and Implementation (NSDI '16), Santa Clara, CA, March 2016. Google Inc. (Shang: UCLA; Hosein: SpaceX; both did the work at Google.)
  - The venue is **not printed** in this PDF. It has no USENIX banner or footer. It is the Google-hosted author version. The cited Cilium docs link to `research.google.com/pubs/archive/44824.pdf`. The local kernel source names the venue: `net/netfilter/ipvs/ip_vs_mh.c:16` links `usenix.org/.../nsdi16/nsdi16-paper-eisenbud.pdf`.
  - From memory, not verifiable from this PDF: the USENIX proceedings pagination is pp. 523–535. Use local page numbers when citing this file.
- **PDF page count:** 13 (US Letter; pdfinfo).
- **Printed page numbers:** yes. Page 1 has no printed number. Pages 2–13 print "2"…"13" at bottom centre.
- **Printed page range:** 1–13 (1 implied).
- **PDF→printed offset:** 0. Checked on the rendered pages: PDF p6 prints "6" (Pseudocode 1 / Table 1 page) and PDF p11 prints "11" (Figures 11–12 page). PDF p2 prints "2", and so on.
- **Extraction gotchas:** `6553733` in the text is "655373" followed by footnote marker 3 (p11). The summation and floor/ceiling on p6 come out mangled; use the rendered page. "DKPK" on p12 is the paper's own typo for DPDK.

## 2. Sections (printed pages)

| § | Title | Pages |
|---|---|---|
| — | Abstract | 1 |
| 1 | Introduction | 1–2 |
| 2 | System Overview | 2–3 |
| 2.1 | Frontend Serving Architecture (Fig 2) | 2–3 |
| 2.2 | Maglev Configuration (Fig 3) | 3 |
| 3 | Forwarder Design and Implementation | 3–7 |
| 3.1 | Overall Structure (Fig 4) | 3–4 |
| 3.2 | Fast Packet Processing (Fig 5) | 4–5 |
| 3.3 | Backend Selection | 5 |
| 3.4 | Consistent Hashing (Pseudocode 1, Table 1) | 5–7 |
| 4 | Operational Experience | 7–9 |
| 4.1 | Evolution of Maglev: 4.1.1 Failover, 4.1.2 Packet Processing | 7 |
| 4.2 | VIP Matching (Fig 6) | 7–8 |
| 4.3 | Fragment Handling | 8 |
| 4.4 | Monitoring and Debugging | 8–9 |
| 5 | Evaluation | 9–11 |
| 5.1 | Load Balancing (Fig 7) | 9 |
| 5.2 | Single Machine Throughput: 5.2.1 Kernel Bypass (Fig 8) p9–10; 5.2.2 Traffic Type (Fig 9) p10; 5.2.3 NIC Speed (Fig 10) p10–11 | 9–11 |
| 5.3 | Consistent Hashing (Figs 11, 12) | 11 |
| 6 | Related Work | 11–12 |
| 7 | Conclusion; Acknowledgements | 12 |
| — | References [1]–[41] | 13 |

Figure and table locations: Fig 1 p1; Fig 2 p2; Figs 3 and 4 p3; Fig 5 p4; Pseudocode 1 and Table 1 p6; Fig 6 p7; Figs 7 and 8 p9; Figs 9 and 10 p10; Figs 11 and 12 p11.

## 3. Terms introduced (as the paper defines them)

1. **VIP (Virtual IP address)**: an address assigned to no specific interface. Multiple service endpoints behind Maglev serve it, and Maglev announces it to the router over BGP. (p2)
2. **ECMP (Equal Cost Multipath)**: every Maglev announces the VIP at the same cost, so the router spreads VIP packets across the Maglev machines. This is how the system scales out. (p1 abstract, p2)
3. **GRE encapsulation**: Maglev wraps the chosen packet in a GRE/IP header whose outer destination is the selected endpoint. The endpoint decapsulates it. (p2)
4. **Direct Server Return (DSR)**: the endpoint sends the reply (source = VIP) straight to the router, so Maglev never handles the larger return packets. The implementation is "out of scope". (p3)
5. **Backend pool**: the set of endpoints configured for a VIP. A pool can nest other pools and is health-checked. Packets go only to healthy backends. (p3)
6. **Shard**: a group of Maglevs in the same cluster that serves its own set of VIPs, used for performance isolation and feature testing. (p3)
7. **Steering module**: hashes each packet's 5-tuple to pick a receive queue (one per packet thread). It falls back to round-robin only when that queue is full. (p4)
8. **5-tuple**: source IP, source port, destination IP, destination port, IP protocol number. (p4, footnote 1)
9. **Connection tracking table**: a fixed-size hash table per packet thread that maps a packet's 5-tuple hash to the backend chosen for it. On a hit with a healthy backend the choice is reused. (p4–5)
10. **Consistent hashing**: generate a large lookup table in which each backend owns some entries. It should give (a) *load balancing*: each backend gets an almost equal number of connections; and (b) *minimal disruption*: when the backend set changes, a connection likely goes to the same backend as before. (p5)
11. **Maglev hashing**: the paper's own consistent hash. Each backend gets a *preference list* (a permutation of all table positions), and backends take turns filling their most-preferred empty position until the table is full. (p6)
12. **Lookup table (`entry[]`, size M)**: the per-VIP array mapping a hash bucket to a backend. M must be prime. (p6)
13. **offset / skip**: two hashes of the backend's unique name, giving `permutation[i][j] = (offset + j·skip) mod M`. (p6)
14. **Overprovision factor**: maximum load divided by average load across endpoints at a point in time. (p9)
15. **Packet-tracer**: specially marked probe packets. Each Maglev forwards them normally and also reports its machine name and chosen backend to a receiver. (p8)

## 4. Core claims

1. A software LB scales out: capacity is N×T, with N+1 redundancy and ECMP spreading the load. That needs a high per-machine throughput T and *connection persistence*, meaning every packet of a connection reaches the same endpoint. (p2)
2. The steering module hashes the 5-tuple instead of using round-robin. This lowers the chance of reordering packets within a connection, and it lets backend selection run once per connection without races against health updates. (p4)
3. Kernel bypass with a shared packet pool and pointer rings (no copies, batching, one thread pinned per core) gives about 350 ns per packet and line rate with small packets. Moving to bypass raised throughput more than 5×. The Linux-stack version reaches under 30% of bypass throughput. (p4–5, p7, p10)
4. Per-Maglev connection tracking alone is not enough. When the set of Maglevs changes, ECMP reshuffles flows onto Maglevs that hold no entry for them, and the CT table can fill under heavy load or a SYN flood. Local consistent hashing, not shared state such as a DHT, covers both cases. (p5)
5. Maglev hashing puts balance ahead of minimal disruption, the opposite of Karger and rendezvous hashing. Imbalance forces overprovisioning. A few disruptions are tolerable because resets only happen when a connection's Maglev affinity changes at the same moment. (p6)
6. Each backend gets ⌊M/N⌋ or ⌈M/N⌉ entries. Choosing M > 100×N keeps the difference in hash space between backends under 1%. (p6)
7. Building the table costs O(M log M) on average and O(M²) in the worst case, so M ≫ N. (p6)
8. At M=65537 and N=1000, Karger and rendezvous hashing need 29.7% and 49.5% overprovisioning; at M=655373 they need 10.3% and 12.3%. Maglev is nearly perfect at both sizes. (p11)
9. A larger M means less disruption. Google still defaults to M=65537 because concurrent failures are rare, CT is the primary protection, and table generation grows from 1.8 ms to 22.9 ms going from 65537 to 655373. (p11)
10. In production (458 endpoints, Europe), the coefficient of variation of per-endpoint load is 6–7%, and the overprovision factor is below 1.2 more than 60% of the time. It is higher off-peak. (p9)

## 5. Figures and examples worth redrawing

- **Figure 2, Maglev packet flow (p2).** Redraw as a numbered sequence:
  1. Client→DNS returns a VIP.
  2. Unencapsulated inbound: Internet→router.
  3. Router→Maglev by ECMP.
  4. Encapsulated inbound: Maglev→endpoint over GRE.
  5. Unencapsulated outbound: endpoint→router→client (DSR).
  6. Dashed: BGP announcements from Maglev to router.

  This is the one picture of the whole system.
- **Figure 4, forwarder structure (p3).** NIC → steering (5-tuple hash) → RX queues → packet threads (VIP match → miss: drop; connection tracking → hit: reuse; miss: consistent hashing then add entry → encap) → TX queues → muxing → NIC. Pair it with §3.1 text (p4).
- **Table 1, sample lookup table (p6).** M=7, three backends, (offset, skip) = B0 (3,4), B1 (0,2), B2 (3,1).
  - Permutations: B0 = 3,0,4,1,5,2,6; B1 = 0,2,4,6,1,3,5; B2 = 3,4,5,6,0,1,2.
  - Before: B1,B0,B1,B0,B2,B2,B0.
  - After B1 is removed: B0,B0,B0,B0,B2,B2,B2. Row 6 is the one extra change (B0→B2).
  - Re-verified by script `/tmp/qbbr/maglev_table1.py`.
- **Figure 11 (p11).** Min and max percent of entries per backend for M/K/R at "small" (65537) and "large" (655373), N=1000; the ideal is 0.1%. Approximate readings:
  - M ≈ 0.10 / 0.10 at both sizes.
  - K-small ≈ 0.075 / 0.13; R-small ≈ 0.065 / 0.15.
  - K-large ≈ 0.092 / 0.11; R-large ≈ 0.09 / 0.112.
- **Figure 12 (p11).** Percent of changed entries against percent of failed backends (0.1–3%), N=1000, 200 trials per k. Readings: M=65537 rises from about 0.6% to about 2.3% at 1% failed and peaks near 2.8%. M=655373 stays around 0.4–0.8%.
  - Redraw it from a Python reproduction. My reproduction, one trial per point: 0.54% at k=1, 2.38% at k=10 (M=65537); 0.58% at k=10 (M=655373).
  - Inference, flagged: those values match the plot only if the metric counts entries that changed **but did not belong to a removed backend**. Counting all changed entries gives 3.38% at k=10, which does not match.
- Optional: **Figure 7 (p9)** (diurnal load, stdev, overprovision factor) and **Figures 8–10 (p9–10)** (throughput against packet threads). Skimmable.

## 6. Maths

| Item | Page | Content |
|---|---|---|
| Permutation | p6 | `offset ← h1(name[i]) mod M`; `skip ← h2(name[i]) mod (M−1) + 1`; `permutation[i][j] ← (offset + j × skip) mod M`. The paper says only "two different hashing functions"; it does not name them. |
| Why M prime | p6 | "M must be a prime number so that all values of skip are relatively prime to it." skip ∈ {1..M−1}. The map j ↦ offset + j·skip (mod M) is a bijection on Z_M iff gcd(skip, M) = 1, and that holds for every skip only when M is prime. Counterexample for the learner: M=8, skip=2 visits {0,2,4,6}; skip=4 visits {0,4}. Once those slots are full, the populate loop runs off the end of the permutation. |
| Pseudocode 1, POPULATE | p6 | `next[i]←0`; `entry[j]←−1`; n←0. Outer `while true` loop; `for each i<N`: c ← `permutation[i][next[i]]`; while `entry[c]≥0` advance `next[i]`; `entry[c]←i`; `next[i]++`; n++; return when n=M. Each pass of the for loop is one round in which every backend claims one slot. |
| Balance claim | p6 | Each backend gets ⌊M/N⌋ or ⌈M/N⌉ entries, a difference of at most 1. Why: every full round fills exactly N slots, and the loop stops partway through the last round. So the **first M mod N backends in iteration order get the extra slot**, which is why order matters (Cilium sorts backends; see §8). |
| M > 100N ⇒ ≤ 1% | p6 | (⌈M/N⌉ − ⌊M/N⌋)/⌊M/N⌋ ≤ 1/⌊M/N⌋ ≤ 1/100. This is a **balance** bound, not a disruption bound. Note that the paper's own evaluation (M=65537, N=1000) gives M/N ≈ 65.5, which breaks the rule: entries are 65 or 66, so max/mean ≈ 1.007. |
| Expected cost | p6 | At step n the expected number of tries is M/(M−n), so the total is ∑_{n=1}^{M} M/n = M·H_M ≈ M(ln M + 0.577) = O(M log M) (coupon collector). The worst case is O(M²), when N = M and every backend has the same permutation. M=7 gives 18.15 expected probes; the actual Table 1 run takes 12. M=65537 gives about 7.6×10⁵. |
| Line-rate pps | p4 | 10 Gb/s gives 813 Kpps at 1500 B IP and 9.06 Mpps at 100 B IP. Both match 10e9 / ((L + 38) × 8), where 38 B = Ethernet header 14 + FCS 4 + preamble/SFD 8 + IFG 12. The 38 B is my derivation; the paper does not state it. |
| Worst-case delay | p5 | Pool of 3000 packets ÷ 10 Mpps = 300 µs. Batch timer 50 µs. Both are Little's-law style. |
| bps from pps | p9, footnote 2 | bps = min(pps × packet_size, line_rate_bps). |
| Overprovision | p9, p11 | max/avg − 1: Karger 29.7%, rendezvous 49.5% at 65537. |

**By hand (pen and paper):**
- Rebuild Table 1. Then remove each backend in turn:
  - Remove B0: 0 extra changes.
  - Remove B1: 1 extra (row 6), as in the paper.
  - Remove B2: 1 extra (row 6).
- Add B3 with (1,3): new table B1,B3,B1,B0,B2,B0,B2. Rows 5 and 6 are extra changes beyond row 1.
- Show that M=8 breaks the permutation.
- Compute M·H_M for M=7.
- Compute the ⌊M/N⌋/⌈M/N⌉ split for:
  - Cilium's default M=16381 with N=160: 102 or 103 entries.
  - M=251 with N=3: 84, 84, 83.

## 7. Numbers worth reusing

- In service since 2008 (p1); "over six years" (p7).
- 10 Gbps line rate = 813 Kpps at 1500 B and 9.06 Mpps at 100 B average (p4).
- About 350 ns per packet. 50 µs batch timer. 3000-packet pool, so at most about 300 µs added delay under overload (p5).
- Kernel bypass more than 5× faster (p7). Linux stack under 30% of bypass (p10).
- Testbed: two 8-core CPUs with one used for Maglev, 128 GB, 10G NIC. One core for steering and muxing, so at most 7 packet threads (p9–10). Minimum packets: 52 B UDP, 64 B TCP (p10).
- NIC saturates at 5 threads for non-SYN and constant-5-tuple traffic; SYN needs 6 (p10). 40G NIC: a bit over 15 Mpps, limited by the steering module (p11).
- Production load: 458 endpoints, 5-minute granularity, CV 6–7%, overprovision factor below 1.2 more than 60% of the time (p9).
- Hashing evaluation: N=1000; M=65537 and 655373 ("no special significance… need to be prime", footnote 3); Karger with 1000 views (p11).
- Overprovisioning: K/R 29.7% / 49.5% at 65537; 10.3% / 12.3% at 655373 (p11).
- Default M=65537. Generation time 1.8 ms at 65537 and 22.9 ms at 655373 (p11). Figure 12: 200 repetitions per k (p11).
- M > 100·N (p6).
- Cilium: allowed M ∈ {251, 509, 1021, 2039, 4093, 8191, 16381, 32749, 65521, 131071}, default 16381. The table stores one 4-byte backend ID per slot, so 16381 is about 64 KiB per service and 65521 about 256 KiB. The Go permutation scratch is N×M×8 B.
- IPVS `mh` uses the same 10 primes. Its default index is 12, giving 4093. The learner's running kernel has `CONFIG_IP_VS_MH=m` and `CONFIG_IP_VS_MH_TAB_INDEX=12`, and `ip_vs_mh.ko.zst` is present.

## 8. Real-system mapping

### (a) Cilium fork (`~/workspace/neverinstall/cilium`, tag v1.19.6-vpc.24): all paths verified by grep and read

**Control plane (Go): building the table**
- `pkg/maglev/maglev.go`:
  - `:38` sets `DefaultTableSize = 16381`. `:41` sets `DefaultHashSeed`. `:43–44` define the flag names `bpf-lb-maglev-table-size` and `bpf-lb-maglev-hash-seed`.
  - `:48` lists the supported sizes. `:53–57` is a comment quoting the paper's "M > 100×N… (page 6)".
  - `:68–89`, `ToConfig`: rejects sizes outside the list and requires a 12-byte base64 seed. Bytes 0–3 seed murmur, 4–7 `SeedJhash0` (v4), 8–11 `SeedJhash1` (v6).
  - `:203–208`, `getOffsetAndSkip`: `h1, h2 := murmur3.Hash128(addr, seed)`; `offset = h1 % m`; `skip = h2 % (m−1) + 1`. This is the paper's formula, but **h1 and h2 are the two 64-bit halves of one seeded MurmurHash3-128** (`pkg/murmur3/murmur3.go:15`), not two separate functions.
  - `:150–201`, `getPermutation`: parallel over backends on a workerpool. The permutation is built incrementally at `:190–193`: `perm[start]=offset; perm[j] = (perm[j−1] + skip) % m`.
  - `:229–253`, `setHashString`: the backend "unique name" is a string such as `[10.0.0.1:80/TCP,State:active]` (with `/i` for internal scope). A comment at `:225–228` says it must never change, or tables would differ across nodes during upgrades.
  - `:272–290`, `GetLookupTable`: **sorts backends by hashString** (`:283–287`) so every node builds an identical table. The paper is silent on ordering, yet ordering decides which backends get ⌈M/N⌉ entries.
  - `:292–338`, `computeLookupTable`: Pseudocode 1 written as `for n := range m { i := n % l; … }` with sentinel `0xffff_ffff` (`:310–313`).
    - **Weights**, which the paper omits ("implementation details are not described", p6): `:296–303` and `:320–326`. The scheme is Envoy-inspired (comment `:263–271`). A backend's turn is skipped while `(n+1)*weight < weightCntr[i]`, and each turn taken adds `weightSum`.
  - `:358–360`, `derivePermutationSliceLen`: the scratch slice size; the comment table at `:344–353` says about 1.3 GB at 131071.
- `pkg/maglev/maglev_test.go`: `:128–163` `TestBackendRemoval` (N=3, M=1021, asserts under 1% of surviving entries change); `:165–214` weighted removal (expected counts 16/98/832/75).
- `pkg/datapath/linux/config/config.go:443–445` emits `LB_MAGLEV_LUT_SIZE`, `HASH_INIT4_SEED`, `HASH_INIT6_SEED` into the BPF build. `bpf/node_config.h:112` (32749) is only the deprecated test/dev default.

**Maps**
- `bpf/lib/lb.h`:
  - `:317–332` defines `cilium_lb4_maglev` and `:245–260` `cilium_lb6_maglev`.
  - Type: `BPF_MAP_TYPE_HASH_OF_MAPS`, key = `__u16` rev-NAT/service ID. The inner map is an ARRAY with 1 entry whose value is `__u32[LB_MAGLEV_LUT_SIZE]`.
- `pkg/loadbalancer/maps/lbmaps.go`:
  - `:625–645`, `UpdateMaglev`: **creates a fresh inner map per update and swaps its FD into the outer map**, an atomic per-service table replacement.
  - `:647–658` is `DeleteMaglev`. `:1111–1114` holds the map names.

**Datapath (BPF): lookup**
- `bpf/lib/lb.h:1847–1874`, `lb4_select_backend_id_maglev`: outer lookup by `svc->rev_nat_index`, then `index = __hash_from_tuple_v4(tuple, sport, dport) % LB_MAGLEV_LUT_SIZE` (`:1872`), then `map_array_get_32` (`:1873`). The v6 version is at `:1092–1116`.
- `bpf/lib/hash.h:12–17`: `jhash_3words(saddr, (dport<<16)|sport, nexthdr, HASH_INIT4_SEED)`. **daddr is excluded** on purpose (comment `:9–11`), because the table is already per service. With session affinity, `sport` is forced to 0 (`lb.h:1858`), so the hash depends only on the client IP (docs `kubeproxy-free.rst:1405–1409`).

**Conntrack first, then Maglev: the paper's two-part strategy (§3.1/§3.3)**
- `bpf/lib/lb.h:2083–2206`, `lb4_local`:
  - `ct_lazy_lookup4(... CT_SERVICE ...)` at `:2104`.
  - `CT_NEW`: select via Maglev and `ct_create4` (`:2133–2166`).
  - `CT_REPLY`, an existing entry: reuse `state->backend_id` (`:2168`). If the backend is gone or not active, a non-SYN packet keeps draining to it and a SYN or missing backend is re-selected (`:2183–2200`).
  - This mirrors p4: "If a match is found and the selected backend is still healthy, the result is simply reused. Otherwise… consistent hashing."

**How backends leave the table**
- `pkg/loadbalancer/reconciler/bpf_reconciler.go`:
  - `:979–981`: maintenance backends are skipped.
  - `:1032–1051`: only active backends count; terminating ones are used only when no backend is active (KEP-1669); quarantined and unhealthy ones are excluded.
  - `:1053–1058`: `updateMaglev(fe, feID, orderedBackends[:activeCount])`.
  - `:1348–1363`: with an empty active set the table is deleted; otherwise it is recomputed in full and swapped in.
  - `:1545–1564` is `computeMaglevTable`. `:1165–1199` is `useMaglev`: only N-S-reachable frontend types, ClusterIP only with `bpf-lb-external-clusterip`, wildcard frontends never, and a per-service annotation overrides the default.

**Knobs**
- Agent flags: `bpf-lb-algorithm` (`pkg/loadbalancer/config.go:57`; value `"maglev"` at `:112`; default `random` at `:483`), `bpf-lb-maglev-table-size`, `bpf-lb-maglev-hash-seed`, `bpf-lb-external-clusterip` (`config.go:79`), `bpf-lb-algorithm-annotation` (`config.go:83`).
- Service annotation `service.cilium.io/lb-algorithm` (`pkg/annotation/k8s.go:147`).
- Helm (`install/kubernetes/cilium/values.yaml`):
  - **`maglev.tableSize` / `maglev.hashSeed` are top-level keys** (`:2519–2525`), **not** `loadBalancer.maglev.*`.
  - `loadBalancer.algorithm` (`:2596`); `bpf.lbExternalClusterIP` (`:801`); `bpf.lbAlgorithmAnnotation` (`:814`).
  - Configmap rendering: `templates/cilium-configmap.yaml:904` (`bpf-lb-algorithm`) and `:917–921` (maglev keys).
  - **Fork-specific:** `:486–493` forces `bpf-lb-algorithm-annotation: "true"` when `vpc.enabled`.

**CLI**
- `cilium-dbg bpf lb maglev list` (alias `ls`, supports `-o json`): `cilium-dbg/cmd/bpf_lb_maglev.go:11–18` and `cilium-dbg/cmd/bpf_lb_maglev_list.go:24–45, 124–126`.
- It prints `[revNAT-ID]/v4 → [M backend IDs]` (`lbmaps.go:779–788`).
- Map IDs to addresses with `cilium-dbg bpf lb list --backends` (`bpf_lb_list.go:174`) and `cilium-dbg service list`.

**Docs**
- `Documentation/network/kubernetes/kubeproxy-free.rst:488–582`:
  - Maglev applies only to N-S traffic, because E-W goes through socket LB at connect time (`:511–515`).
  - 16381 suits about 160 backends and 65521 about 650.
  - **The docs misstate the paper:** they say M > 100N guarantees "at most 1% difference in the reassignments", but the paper's 1% bounds the *balance* of hash space (p6). Figure 12 shows about 2–3% extra disruption at M/N ≈ 65. The Cilium test (`maglev_test.go:160–162`) carries the same conflation.

**Fork-specific connection worth teaching**
- `bpf/lib/vpc_dsr.h:30–33` and `:498–503`: the VPC public-LB entry node keeps **no per-flow state** and relies on Maglev, so that whichever node receives the address picks the same backend. This is §3.3–3.4's argument (ECMP and ownership changes defeat local CT) in the learner's own code.
- `:244–254` `vpc_lb4_is_maglev`; `:353–354` ICMP errors toward a public frontend are dropped unless the frontend uses Maglev, because the quoted tuple must re-hash to the same backend.

**Differences from the paper, at a glance**
- Hash: seeded murmur3-128 halves (control plane) and seeded jhash of saddr, ports and proto (datapath), against unspecified h1/h2 and a 5-tuple hash.
- Default M: 16381 from a fixed list of 10 primes, against 65537.
- Weights: implemented, against undescribed.
- Ordering: deterministic sort.
- Removal: recompute from scratch and swap, against "regenerate".
- Scope: per-node tables instead of per-Maglev machine; there is no ECMP layer in front unless the user adds one (BGP/LB-IPAM).

### (b) Linux kernel v7.2 (`~/workspace/repos/linux`): IPVS `mh` scheduler, `net/netfilter/ipvs/ip_vs_mh.c`

- `:8–16` is the header comment citing §3.4 and the NSDI'16 URL. `:49–50` lists the same 10 primes. `:53–58`: `CONFIG_IP_VS_MH_TAB_INDEX` defaults to 12, giving 4093. Kconfig `net/netfilter/ipvs/Kconfig:230–244, 303–317`.
- `:69–77`: two **fixed** hsiphash keys `hash1` and `hash2` (no per-host secret). `:87–101`: the hash input is `offset + port + folded addr`.
- `:121–156`, `ip_vs_mh_permutate`: `offset = hash1 % M`, `skip = hash2 % (M−1) + 1` (`:142–147`). `turns = (weight/gcd) >> rshift` (`:151`).
- `:158–230`, `ip_vs_mh_populate`: a bitmap marks used slots. The probe `perm += skip` wraps mod M (`:196–203`). **Weights work by consecutive turns** (`:219–223`), unlike Cilium's skip-a-turn counters. The lookup is updated in place under RCU (`:207–214`).
- `:233–242`, `ip_vs_mh_get`: hashes the **source address** (plus the source port only with the `MH_PORT` flag, `:35`, `:483–484`), not the 5-tuple. `:244–284` is the optional fallback (flag `:34`): when the chosen dest is unavailable, it re-hashes with increasing offsets instead of rebuilding.
- `:287` `ip_vs_mh_reassign`, `:428` `ip_vs_mh_dest_changed`, `:508–519` scheduler ops: add, del and upd of a dest each rebuild the table.

### (c) Katran

Only a mention was found: kernel selftests `tools/testing/selftests/bpf/progs/test_parse_tcp_hdr_opt.c:3–8` call Katran "a layer 4 load balancer". Nothing local verifies a Katran–Maglev relation, so it is **skipped**.

## 9. Prerequisites and forward references

**Prerequisites**
- Modular arithmetic: gcd, why a prime modulus makes every step a generator of Z_M.
- Harmonic numbers and coupon collector.
- Per-flow ECMP hashing: Linux `fib_multipath_hash`, `net/ipv4/route.c:2090`, `fib_multipath_hash_policy`.
- Conntrack basics (Cilium `CT_SERVICE` entries).
- BGP announcement of an anycast or VIP prefix.
- GRE and DSR (the learner's packet-path dossier covers encap).
- RSS-style queue steering.

**Forward references**
- In the paper: §3.3–3.4 depend on the ECMP behaviour from §2.1. §5.3 evaluates §3.4. Fragment handling (§4.3) reuses "same backend selection algorithm" with a 3-tuple Maglev pool.
- Outside it:
  - Cilium docs `kubeproxy-free.rst:488` and the session-affinity note at `:1405`.
  - The Envoy weighted-Maglev PR cited in `maglev.go:263` (envoyproxy/envoy#2982).
  - IPVS `mh`.
  - Main-line papers: fq/pacing (per-flow hashing to queues, `net/sched/sch_fq.c:356` `fq_classify`) and TCP congestion control (reordering → dupACKs, the reason every layer here keeps flows together).

## 10. References worth reading (from the paper's list)

1. [28] Karger et al., "Consistent hashing and random trees", STOC 1997: the ring baseline in Fig 11.
2. [38] Thaler & Ravishankar, "Using name-based mappings to increase hit rates", IEEE/ACM ToN 6(1), 1998: rendezvous (HRW) hashing, the other baseline.
3. [34] Patel et al., "Ananta: Cloud scale load balancing", SIGCOMM 2013: ECMP plus a flow table, no graceful pool-change mechanism (p11–12).
4. [22] Gandhi et al., "Duet", SIGCOMM 2014: the hybrid hardware/software LB that Maglev argues is unnecessary (p12).

## 11. Suggested spine and strands

**Spine:**
1. The problem: scale-out L4 LB, N×T capacity, connection persistence (p1–2).
2. Packet flow: VIP, BGP, ECMP, GRE, DSR (Fig 2, p2–3).
3. Forwarder pipeline: steering hash, per-thread CT, consistent-hash on miss (Fig 4, p3–4).
4. Why CT alone fails: ECMP set changes and a full CT table (p5).
5. Consistent-hash desiderata and Maglev's "balance first" choice (p5–6).
6. offset/skip permutation and why M is prime (p6).
7. POPULATE and Table 1 by hand (p6–7).
8. Costs: ⌊M/N⌋/⌈M/N⌉, M > 100N, O(M log M) (p6).
9. Evidence: Fig 11 balance, Fig 12 disruption, 65537 default and build time (p11).
10. Cilium mapping (maglev.go → lb.h; CT then Maglev; the fork's stateless VPC entry) and IPVS `mh`.
11. The bridge back to flow hashing in fq/ECMP.

**Candidate strands (quizzable claims):**
1. `ct-then-hash`: Maglev reuses a CT entry when its backend is healthy and falls back to Maglev hashing otherwise. The hash exists for flows that land on a Maglev without their CT entry (ECMP changes) or when the table is full. (p4–5; Cilium `lb.h:2133–2200`)
2. `prime-m-permutation`: With skip ∈ [1, M−1] and M prime, `(offset + j·skip) mod M` visits all M slots. A composite M (8, skip 2) visits only M/gcd slots and breaks POPULATE. (p6)
3. `populate-balance`: Round-robin turns give every backend ⌊M/N⌋ or ⌈M/N⌉ slots; M > 100N bounds the **hash-space** imbalance to ≤1%, a balance bound and not a disruption bound. (p6)
4. `balance-over-disruption`: Unlike Karger and rendezvous, removing a backend in Maglev can move surviving backends' entries (Table 1 row 6; about 2.3% at 1% failures, M=65537, N=1000), traded for near-perfect balance (Karger and rendezvous overprovision 29.7% and 49.5%). (p6–7, p11)
5. `table-build-cost`: POPULATE costs about M·H_M probes on average (O(M log M)) and O(M²) in the worst case. Generation time (1.8 → 22.9 ms) and per-VIP memory cap M, so the default is 65537. (p6, p11)
6. `cilium-same-table-everywhere`: Every Cilium node derives an identical table (sorted backend strings, seeded murmur3-128 halves for offset/skip, M from 10 primes, default 16381). The datapath indexes it with `jhash(saddr, ports, proto) % M` from a per-service hash-of-maps. (`maglev.go:203–208, 283–287`; `lb.h:1872`; `hash.h:15`)
7. `steering-hash-not-rr` (optional, links to the main line): the forwarder hashes the 5-tuple to RX queues instead of round-robin, avoiding intra-connection reordering and repeated backend selection, with round-robin fallback only when a queue fills. (p4)

## 12. Exercise ideas

1. **Pen and paper, about 30 min: Table 1 and its variants (p6).** Given (3,4), (0,2), (3,1) and M=7:
   - Write the three permutations and run POPULATE, counting probes.
   - Remove B0, B1 and B2 one at a time and mark the extra-disrupted rows. Answer key: B0 → none; B1 → row 6; B2 → row 6.
   - Add B3 (1,3). Answer: B1,B3,B1,B0,B2,B0,B2, with rows 5 and 6 as extra changes.
   - Show that M=8 with skip 2 or 4 fails.
   - Compute 7·H_7 = 18.15 against the 12 probes actually taken.
   - Compute the split for M=251, N=3 (84/84/83) and M=16381, N=160 (102/103).
   - Derive 813 Kpps and 9.06 Mpps from 10 Gb/s.
2. **Python (numpy), 45–60 min: Figures 11 and 12, plus rendezvous and ring.**
   - Implement POPULATE with **lazy permutations**. A full N×M int64 array at M=655373, N=1000 is about 5 GB; Cilium's own comment warns of 1.3 GB at 131071.
   - Use random (offset, skip) per backend.
   - Measure max/mean entries and extra disruption against M ∈ {251, 1021, 4093, 16381, 65537} and N ∈ {100, 1000}.
   - Add rendezvous (argmax over hashes per slot) and a Karger ring (1000 virtual points per backend via `searchsorted`).
   - Calibration targets: Maglev extra disruption ≈ 0.54% at k=1 and ≈ 2.4% at k=10 (M=65537); ≈ 0.58% at k=10 (M=655373). Karger and rendezvous max/mean ≈ 1.30 and 1.50 at 65537.
   - Plot extra disruption against M/N and mark where the "100×N" rule sits.
   - Starting code: `/tmp/qbbr/maglev_check2.py`.
3. **kind and Cilium, 45–60 min: read a real table.**
   - Enable Maglev: Helm `loadBalancer.algorithm=maglev`, `maglev.tableSize=251` (small enough to read), `maglev.hashSeed=$(head -c12 /dev/urandom | base64 -w0)`. Alternatively set `bpf.lbAlgorithmAnnotation=true` and annotate one Service with `service.cilium.io/lb-algorithm: maglev`.
   - Use a **NodePort** Service with 3 replicas. ClusterIP gets no table unless `bpf.lbExternalClusterIP=true` (`bpf_reconciler.go:1183`).
   - On each node run `kubectl -n kube-system exec <cilium-pod> -- cilium-dbg bpf lb maglev list -o json`, plus `cilium-dbg service list` and `cilium-dbg bpf lb list --backends` to map IDs to pods.
   - Count slots per backend ID (expect 84/84/83).
   - Confirm the tables are identical across nodes after mapping IDs to addresses. Backend IDs are node-local (comment `maglev.go:258–261`).
   - Scale to 2 replicas, dump again, and count changed slots that were not owned by the removed pod.
   - Stretch: `pwru`/`bpftrace` on a NodePort SYN to watch the CT_NEW → Maglev path.
   - Prerequisites:
     - The lab scripts don't set an algorithm, so the cluster is currently on `random` (default, `config.go:483`).
     - The command source is verified in the fork; confirm the in-cluster image is the fork or upstream 1.19.
     - Docker was not running at inventory time.
4. Optional, host netns: IPVS `ipvsadm -s mh`. **`ipvsadm` is not installed**, so list it as a prerequisite and don't install it. The module `ip_vs_mh` is present in the running kernel. The ipvsadm flag spelling for `mh-port`/`mh-fallback` must be checked in its man page; it was not verified locally.

## 13. Honest assessment

- **Read closely:** §3.3–3.4 (p5–7): the CT limitations, the balance-against-disruption argument, the offset/skip formulas, Pseudocode 1, the complexity paragraph and Table 1. Also §5.3 (p11) with Figs 11–12, and §3.1 (p3–4) for the steering/CT/hash split. About 1.5 hours total.
- **Skim:**
  - §3.2 (p4–5): grab the numbers (350 ns, 50 µs, 300 µs, 9.06 Mpps) and skip the ring-pointer mechanics of Fig 5.
  - §4.1 (p7): only the "active-passive → ECMP" lesson.
  - §4.2 VIP matching (p7–8): Google-specific.
  - §4.3 fragments (p8): one idea, a 3-tuple hash to a Maglev pool plus GRE recursion control.
  - §4.4 (p8–9).
  - §5.1–5.2 (p9–11): look at the plots and take away "NIC-bound at 5 threads, steering-bound at 15 Mpps".
  - §6 (p11–12): for references only.
- **Gaps in the paper:** h1/h2 are never named. The weights implementation is withheld (p6). DSR is out of scope (p3). Figure 12's y-metric is ambiguous; the reproduction suggests it excludes the removed backends' own entries. The default M=65537 with N=1000 violates the paper's own M > 100N rule.
- **Link to the main line:**
  - The shared primitive is **flow hashing that keeps a flow together**, applied by ECMP at the router, the steering module (RSS-like), the Maglev table, and `sch_fq`'s per-flow classification for pacing. All of them protect TCP from reordering, which congestion control reads as loss (dupACKs, cwnd cuts).
  - **DSR** means the large, paced, congestion-controlled response direction (where BBR and EDT live on the backend) never passes through the LB, which sees only small request packets. That is why the paper reports pps rather than bps.
  - The latency paragraph (batch timer, pool drain time) is a small queueing exercise.
- Keep it a side path: about 3 hours including exercise 1, with exercise 2 or 3 chosen according to the "own the Cilium knobs" goal.
