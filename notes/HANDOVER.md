# HANDOVER — packet-path dossier, remaining work (written 2026-09-18)

You are taking over a half-finished commission. Chapters 0–7 of
`packet-path-dossier.html` are written, appended and audited. Your job is
chapters 8–16, the merged glossary, the master reference list, the remaining
lab scripts, the bench traces that back them, the final audit, and an honest
final report. Work chapter by chapter, in order. Do not re-plan.

## 0. Ground rules (non-negotiable)

1. **Install nothing, anywhere.** No pacman, yay, pip, go install, apt, not
   even inside kind nodes. If a tool is missing, write it as a prerequisite
   (package name) in the lab sidebar and move on. The one allowed exception:
   copying the already-installed static `/usr/bin/pwru` from the host into
   kind-worker (`docker cp /usr/bin/pwru kind-worker:/usr/local/bin/pwru`),
   which the user agreed to.
2. **Do not run sudo on the host.** It needs a password and the user is not
   watching. Host-side labs are written for the user to run later.
3. **Do not change the existing kind cluster** (Cilium config, resources,
   node sysctls). Read and trace only. Creating throwaway netns/devices
   inside `kind-worker` with the `pp-` prefix is fine; always clean up.
4. **Do not ask the user anything.** Make the judgment call, note it in the
   final report.
5. **Cite kernel code only from `~/workspace/repos/linux` (checked out at
   v7.2)** as `file:line`, and verify every line with grep/sed before you
   write it. Never cite from memory. Cilium code is cited from the fork at
   `~/workspace/neverinstall/cilium` (bpf/*.c, bpf/lib/*.h,
   pkg/datapath/loader/*.go).
6. **Style = `~/workspace/learning/agent-directory/BLOG_STYLE_LEARNING.md`.**
   Read it first, fully. Then read `build/ch07.html` and `build/ch05.html`
   end to end and copy their structure exactly. Key rules from the spec that
   the audit enforces: no term used before the section that introduces it
   (forward references in plain words instead), answers behind toggles and
   at least 35 words each, every diagram captioned `Diagram N.M — …`, every
   reference verified, banned-word list, vocabulary `dl` per chapter.
7. Keep the spine: **the life of one skb**. Every chapter's `chmeta` line
   ends with `Spine:` and one sentence saying where the skb is now.
8. Tone: the reader knows the netfilter chart cold. Function names plus the
   deciding struct fields with short code excerpts (≤ 12 lines each), "not
   too verbose". No metaphors, no marketing verbs, no em dashes in prose
   (figcaptions use the `Diagram N.M — …` convention, that is fine).

## 1. Files and their contracts

- `packet-path-dossier.html` — the deliverable (~177 KB now). Skeleton, hero,
  sticky TOC (with `RT0`…`RT16` reading-time placeholders), how-to-read card
  (scenario→chapter table), chapters ch0–ch7, then a line `<!--APPEND-->`
  before `</main>`, footer, Mermaid ESM import, answer-toggle, beforeprint
  and filter scripts. Glossary and references do not exist yet.
- `build/ch00.html` … `build/ch07.html` — chapter sources already appended.
  Write `build/ch08.html` … `build/ch16.html`, `build/glossary.html`,
  `build/references.html` the same way.
- `artifacts/append.py` — `python3 artifacts/append.py build/chNN.html` inserts the fragment
  before `<!--APPEND-->`. Run it exactly once per fragment (it asserts one
  marker). If you must re-append a fixed chapter, remove the old
  `<section id="chNN"…>…</section>` from the dossier first with a small
  Python script, never by hand.
- `artifacts/audit.py` + `artifacts/audit_terms.py` — `python3 artifacts/audit.py` prints: Mermaid header
  check per diagram, HTML nesting, "early uses: N of M terms", per-chapter
  words → minutes, BANNED hits, em-dash count in prose. Read both files to
  learn the contract; `TERMS = {term: section_id}` maps a vocabulary term to
  the id of the section that introduces it. Extend TERMS for each new
  chapter (all `.words dt` terms plus the key function names). Current
  state: 0 early uses of 131 terms, all diagrams OK, one BANNED hit on
  "unlock" in ch7 (reword to "release" or similar) and 12 em dashes in prose
  (check what the spec says; if it limits them, reduce; figcaptions are
  excluded already).
- `notes/anchors-rx-tx.md`, `notes/anchors-l3-sock.md` — verified anchors
  for ch0–ch7 (reuse when a later chapter needs to point back).
- `notes/anchors-devices.md` (2112 lines) — verified anchors for the device
  chapters. Read it BY SECTION with sed -n, not whole: A veth line 7, B bridge
  306, C bonding 694, D VRF 878, E macvlan 1267, F ipvlan 1437, G IPVS 1811.
- `notes/anchors-cilium.md` — verified Cilium anchors (see §3, ch14/15).
- `notes/refs-verified.md` — every external URL already verified with title.
  Add to it before citing anything new; verify with WebFetch (elixir links
  pinned to v7.2; netkit/tcx have no kernel docs, use LWN 949960 / commits;
  ipvsadm(8) via manpages.debian.org; nft(8) via netfilter.org).
- `notes/traces.md` — real pwru transcripts already captured (veth default
  door, taps+tc, native/generic XDP, router hooks, masquerade flips, lo, data
  segment). The two veth receive-door sequences (GRO on the receiving end
  only → still backlog door; GRO on receiver + TSO/GSO off on sender → NAPI
  door) are recorded at the end of notes/traces.md; the /tmp originals were
  lost at reboot, re-capture on the bench if you want the raw lines.
- `lab/` — `lib.sh` (need_root, need, ns_add, ns_del, link_del, veth_pair,
  move_to, addr, banner), `00-check.sh`, `02-xdp/xdp_pass.c`, `05-router.sh`,
  `06-gateway.sh`, `07-sockets.sh`, `08-lo-unix.sh`, `09-veth.sh`,
  `10-bridge.sh`, `unix_pair.py`. Missing: `11-bond-vrf.sh`,
  `12-macvlan-ipvlan.sh`, `13-ipvs.sh`, `14-cilium.sh`, `15-kind-vxlan.yaml`,
  `15-kind-native.yaml` (+ the helm/cilium-cli install commands as comments
  for the user to run, using image `localhost:5000/cilium/cilium-dev:local`),
  `README.md`. Match the existing scripts' style and the `pp-` prefix.
- Full earlier transcript, if you need a detail not written down:
  `/home/wazir/.claude/projects/-home-wazir-workspace-repos-linux-networking-playground/d47028a0-23bf-4cda-83d4-2828b50ba47f.jsonl`
  (grep it, do not read it whole).
- Keep `notes/PROGRESS.md` updated after each chapter (one line: what is
  appended, what is traced, what is pending) so another agent can resume.

## 2. Chapter markup contract (mirror build/ch07.html)

```
<section id="chN" class="chapter">
  <div class="chnum">N</div>
  <h2>TITLE EXACTLY AS IN THE TOC</h2>
  <p class="chmeta">~RTN min · <span class="tag X">X</span> · Spine: …</p>
  <h3 id="…">…</h3> … 4–6 h3 sections
  ≥1 <figure class="dia"><pre class="mermaid">…</pre><figcaption>Diagram N.M — …</figcaption></figure>
  <aside class="tryit">… lab, prerequisites, commands in <pre>, expected output …</aside>
  <div class="recap">…</div>
  <dl class="words">…</dl>
  <div class="check"> 3 questions, each with <details class="ans"> ≥35-word answer </div>
  <ul class="refs"> <li class="ref" data-layer="…"> … </ul>
</section>
```
Titles for ch8–ch16 (must match the TOC verbatim):
8 "Two programs on one host: lo, same pod, unix sockets" (SOCK) ·
9 "veth: the mystery, resolved" (L2) · 10 "The bridge, and Docker on it" (L2) ·
11 "Master devices: bond and VRF" (L2 L3) · 12 "macvlan and ipvlan" (L2) ·
13 "IPVS: the NAT that hides in INPUT" (L3) ·
14 "Cilium on one node: the tc hook takes over" (BPF) ·
15 "Cilium across nodes and to the world" (BPF) ·
16 "Epilogue: traps, fast paths, what came next" (LAB).
Layer tag classes: HW L2 L3 SOCK BPF LAB.

Length budget: ch0–ch7 average ~2500 words (20k total). The plan promised
~28–30k total, so the remaining chapters must be leaner: 1700–2200 words
each, Cilium chapters up to 2600, epilogue ≤ 1500. Do not pad. Report the
final total honestly.

## 3. Content briefs (facts below were verified in the earlier session unless marked "verify")

### ch8 — lo, same pod, unix sockets (scenarios 1, 2, 3, 8)
- Scenarios 1 and 2 collapse to one: the output route lookup returns
  RTN_LOCAL for any local address, so `dev_out` becomes `net->loopback_dev`
  (verify in net/ipv4/route.c, `ip_route_output_key_hash_rcu`, the
  `res->type == RTN_LOCAL` branch). Show `ip route get 172.18.0.4 from
  10.128.0.75` → `dev lo` (transcript in notes/traces.md).
- Transmit half: `__ip_local_out` → LOCAL_OUT → `ip_output` → POST_ROUTING →
  `ip_finish_output2` (lo neighbour is NUD_NOARP) → `__dev_queue_xmit` (lo is
  noqueue → direct) → `loopback_xmit` drivers/net/loopback.c:70–94:
  skb_orphan, skb_dst_force, eth_type_trans, `__netif_rx` → backlog →
  `__netif_receive_skb_core` → taps → `ip_rcv` → PRE_ROUTING → routing
  (`rt_dst_alloc` route.c:1693 sets input = ip_local_deliver) → LOCAL_IN →
  `tcp_v4_rcv`. Point: the skb walks the full netfilter chart twice
  (OUTPUT/POSTROUTING then PREROUTING/INPUT), both in the same netns.
- Research and settle: does a tap on lo see each packet once or twice
  (`dev_queue_xmit_nit` on xmit plus ptype_all on receive)? Grep
  net/packet/af_packet.c for PACKET_LOOPBACK / IFF_LOOPBACK / pkt_type and
  net/core/dev.c; cite the deciding line. Do not assert without the line.
- Scenario 8, same pod: containers share the netns, so this is scenario 1
  inside the pod; Cilium's `cil_from_container` (attached on the host side of
  the lxc veth) never sees it. Demonstrate with `kubectl exec` into two
  containers of one pod (create a throwaway two-container pod in a
  throwaway namespace on the existing cluster if none exists; delete it
  afterwards) showing `ip route get` and `ss` from both.
- Unix sockets: `unix_stream_sendmsg` af_unix.c:2377 → `sock_alloc_send_pskb`
  :2423 (charges sender's wmem) → `skb_copy_datagram_from_iter` →
  `__skb_queue_tail(&other->sk_receive_queue)` :2488 → `sk_data_ready` :2493;
  `unix_dgram_sendmsg` :2083 (queue at :2291, peer wake / backpressure via
  unix_dgram_peer_wake_*); `unix_stream_read_generic` :2907. There is still
  an skb, but the "absence list" is the teaching point: no dev, no route, no
  dst, no netfilter, no qdisc, no checksum, no MTU, no taps (tcpdump cannot
  see it). Mention SCM_RIGHTS (fd passing rides in UNIXCB(skb).fp) and
  SOCK_SEQPACKET briefly. abstract vs filesystem path names (verify
  `unix_find_other`/`unix_find_bsd`/`unix_find_abstract`).
- Bench status: pwru cannot match unix skbs (no IP header) and ftrace inside
  the node failed. Lab `08-lo-unix.sh` + `unix_pair.py` exist; give bpftrace
  one-liners (kprobe:unix_stream_sendmsg, kprobe:sock_def_readable) and
  label their output "expected" not "observed". Try once more with
  `bpftrace` on the host? No, host needs sudo. Leave labelled.

### ch9 — veth (scenario 5; the user's named pain point, give it the most diagrams)
- Payoff sentence, first paragraph: a veth does not create a new skb; it
  swaps skb->dev to the peer, scrubs it if the netns changes, and hands the
  same skb to `__netif_rx` (or to its own NAPI poll), so the receive half of
  the flow runs again in the peer's namespace while the transmit half ran
  once in the origin namespace.
- `veth_xmit` drivers/net/veth.c:347: `rcv = rcu_dereference(priv->peer)`;
  `use_napi = rcu_access_pointer(rq->napi) && veth_skb_is_eligible_for_gro(dev, rcv, skb)`;
  eligibility :338–345 = `!(dev->features & NETIF_F_ALL_TSO) ||
  (skb->destructor == sock_wfree && rcv->features & (GRO_FRAGLIST|GRO_UDP_FWD))`.
  `veth_forward_skb` :320 = `__dev_forward_skb(dev, skb) ?: xdp ?
  veth_xdp_rx(rq, skb) : __netif_rx(skb)`.
- `__dev_forward_skb2` net/core/dev.c:2438 → `____dev_forward_skb`
  include/linux/netdevice.h:4440: `__is_skb_forwardable` :4400 (MTU check,
  GSO exempt) → `skb_scrub_packet(skb, !net_eq(dev_net(dev), dev_net(skb->dev)))`
  → `skb->priority = 0`; then eth_type_trans. Read `skb_scrub_packet` in
  net/core/skbuff.c and list exactly what it clears (dst, nf/ct, tc index,
  ipvs_property, mark only if xnet, skb->dev? verify each). This answers
  "does routing/conntrack run again": yes, because dst is dropped and ct is
  reset; skb->mark survives only inside one netns.
- Two doors, with the two transcripts: default door `__netif_rx →
  netif_rx_internal → enqueue_to_backlog → … → tc_run → ip_rcv` ; NAPI door
  `veth_xdp_rcv_skb → tcp_wfree → pskb_expand_head → … → gro_receive_skb →
  dev_gro_receive → inet_gro_receive → tcp4_gro_receive → tcp_gro_receive →
  tc_run → ip_rcv_core`. Subtle point to state: GRO on the receiving end
  alone does not flip the pair into NAPI mode; eligibility also needs the
  sender's TSO off (or a sock_wfree destructor plus fraglist/UDP-fwd GRO),
  which is exactly what attaching an XDP program does to the peer
  (`veth_xdp_set` clears peer GSO_SOFTWARE, veth.c:1622). `veth_set_features`
  GRO branch :1530–1543 → `veth_napi_enable`.
- The only copy: native XDP path `veth_xdp_rcv_skb` → `skb_pp_cow_data`
  veth.c:761 / skbuff.c:942 when the skb is shared, head-locked, nonlinear
  or short on headroom (TCP clones → always copied). Everywhere else the skb
  identity is preserved; prove it with pwru: the skb address column stays
  constant across `veth_xmit` and `__netif_rx`.
- pwru needs `--kmods veth` to show `veth_xmit`/`veth_xdp_rcv_skb` (module).
- Diagrams: (9.1) sequence va→vb naming every function and the netns
  boundary; (9.2) the two-doors decision flowchart with the eligibility
  rule; (9.3) what skb_scrub_packet clears vs keeps.
- Lab `09-veth.sh` exists (pp-a va 10.9.0.1 — vb 10.9.0.2 pp-b). Add the
  `ethtool -K` toggles as steps and the restore step.

### ch10 — bridge, Docker (scenario 6)
- Anchors: notes/anchors-devices.md §B (line 306). rx_handler block
  dev.c:6097–6116: bridge returns RX_HANDLER_CONSUMED (frame stolen), bond/
  macvlan/ipvlan return RX_HANDLER_ANOTHER (`goto another_round` with the new
  dev). `br_handle_frame` → `br_handle_frame_finish` → `br_fdb_find_rcu` →
  `br_forward`/`br_flood` → `__br_forward` → `br_forward_finish` →
  `br_dev_queue_push_xmit` → `dev_queue_xmit` on the port (skb->dev = port);
  local delivery `br_pass_frame_up` (skb->dev = bridge dev → `netif_receive_skb`
  → the core runs again for the bridge device). NF_BR_* hooks; br_netfilter:
  `br_nf_pre_routing` calls the IPv4 PRE_ROUTING hooks with the bridge as
  in-device, `br_nf_forward_ip`, `br_nf_post_routing`;
  `bridge-nf-call-iptables`. Then Docker: docker0, veth pairs, the DOCKER and
  DOCKER-USER chains, MASQUERADE; why Kubernetes/Docker load br_netfilter and
  what breaks when it is off (verify claims against the nf_bridge code, not
  folklore).
- Lab `10-bridge.sh` exists (pp-l vl 10.10.0.1 — pp-br0 — vr 10.10.0.2 pp-r).
  Capture a bench trace in kind-worker: `pwru --kmods bridge,br_netfilter,veth
  --filter-dst-ip 10.10.0.2 --output-meta` and show br_handle_frame …
  br_dev_queue_push_xmit … veth_xmit; then `modprobe br_netfilter` (module
  should autoload from the host; if not, label the trace expected) and show
  the ip hooks appearing between br functions. Save the transcript to
  notes/traces.md.

### ch11 — bond and VRF (scenarios 10, 11)
- Anchors §C (694) bonding: `bond_handle_frame` rx_handler sets skb->dev =
  bond dev, returns RX_HANDLER_ANOTHER; inactive-slave handling
  (`bond_should_deliver_exact_match`), `recv_probe` for LACPDU/ARP monitor;
  xmit `bond_start_xmit` → `__bond_start_xmit` → mode function → `bond_dev_queue_xmit`
  sets skb->dev = slave → `dev_queue_xmit` again (bond is noqueue, slave
  may have a qdisc: two passes through `__dev_queue_xmit`); `bond_xmit_hash`
  and xmit_hash_policy. State clearly: same skb, device swapped twice.
- Anchors §D (878) VRF: `l3mdev_ip_rcv` from `ip_rcv_finish_core` →
  `vrf_ip_rcv`: skb->dev = vrf dev, IPSKB_L3SLAVE, the PRE_ROUTING hooks run
  a second time with the VRF device (the "hooks twice" phenomenon; verify in
  drivers/net/vrf.c `vrf_rcv_nfhook`); table selection via the l3mdev fib
  rule (`fib_rule` l3mdev → `l3mdev_fib_table`); output: `vrf_xmit` →
  `vrf_process_v4_outbound` → route lookup in the VRF table → `ip_local_out`
  (OUTPUT/POSTROUTING run again with the VRF dev; `vrf_l3_out`/`vrf_ip_out`
  for locally generated packets; verify). Sockets: `ip vrf exec`,
  SO_BINDTODEVICE, `net.ipv4.tcp_l3mdev_accept`.
- Write `lab/11-bond-vrf.sh`: bond0 (mode active-backup or balance-rr) over
  two veth ends whose peers sit in one netns bridged or bonded; a VRF `pp-vrf`
  table 10 enslaving a veth. Bench: both create in kind-worker (verified
  earlier). Trace with `pwru --kmods bonding,vrf,veth` (module names: check
  `lsmod` on the host; vrf may be built in → then omit).

### ch12 — macvlan vs ipvlan (scenario 12)
- Anchors §E (1267), §F (1437). `macvlan_handle_frame` keyed by dest MAC
  (`macvlan_hash_lookup`), modes private/vepa/bridge/passthru/source,
  bridge-mode local forwarding without touching the lower device, unicast
  filter on the lower dev (`dev_uc_add`) vs promisc; `ipvlan_handle_frame`
  keyed by IP (`ipvlan_addr_lookup`), modes l2/l3/l3s; l3 mode transmit does
  the route lookup in the parent's namespace (`ipvlan_process_v4_outbound` →
  `ip_route_output_flow` → `ip_local_out`), so the skb runs the parent's
  OUTPUT/POSTROUTING; l3s adds a LOCAL_IN nf hook (`ipvlan_nf_input`) so the
  parent's INPUT chain sees it too. Use cases: macvlan when each endpoint
  needs its own MAC (DHCP, switch port security allows several MACs); ipvlan
  when the NIC or fabric allows one MAC (Wi-Fi, most cloud NICs, the user's
  laptop has only Wi-Fi: say so). One comparison table.
- Write `lab/12-macvlan-ipvlan.sh` (on a dummy or veth end; note that on the
  laptop the Wi-Fi NIC will refuse macvlan, that is itself the lesson).
  Bench trace in kind-worker with `pwru --kmods macvlan,ipvlan,veth`.

### ch13 — IPVS (scenario 9)
- Anchors §G (1811): `ip_vs_ops` hook registrations and priorities
  (net/netfilter/ipvs/ip_vs_core.c), `ip_vs_in` from LOCAL_IN (the VIP is a
  local address on kube-ipvs0, so routing said "local"), `ip_vs_schedule`,
  `ip_vs_nat_xmit` rewriting daddr and re-routing, re-injection through
  `ip_local_out`/`NF_HOOK(LOCAL_OUT)` guarded by `skb->ipvs_property`
  (skbuff.h), reply direction `ip_vs_reply4` at LOCAL_IN and FORWARD,
  `net.ipv4.vs.conntrack` interaction, DR/TUN briefly, kube-proxy ipvs mode
  (ipset + a few iptables rules). Diagram: the netfilter chart with the
  INPUT→OUTPUT jump drawn on it.
- `ip_vs` is not loadable in the kind node and ipvsadm is not installed:
  write `lab/13-ipvs.sh` for the host (prerequisite: ipvsadm, package
  `ipvsadm`) and label its output expected. Trace hint:
  `pwru --kmods ip_vs --filter-dst-ip VIP`.

### ch14 — Cilium same node (scenario 7, first half)
- Bench facts: cluster `kind` (kind-control-plane 172.18.0.2, kind-worker2
  172.18.0.3, kind-worker 172.18.0.4); Cilium fork image
  `localhost:5000/cilium/cilium-dev:local` (v1.19.6-vpc.18); routing-mode
  tunnel, Geneve port 6081, ENCAP_IFINDEX 5 = cilium_geneve; KPR on; BPF
  masquerade on eth0; BPF host routing (EnableHostLegacyRouting=false);
  EnableTCX=true (all programs tcx); EnableEndpointRoutes=false (no
  cil_to_container). Test pods (re-check with `kubectl get pod -A -o wide`):
  acme/far-client 10.64.1.13 and acme/server 10.64.1.10 on kind-worker;
  acme/client on kind-worker2; default/masq-client → masq-witness
  (hostNetwork).
- Anchors notes/anchors-cilium.md: cil_from_container bpf_lxc.c:2211 →
  tail_handle_ipv4 :2156 → handle_ipv4_from_lxc :1591 (ipcache :1715,
  policy_can_egress4 :1899) → ipv4_forward_to_destination :1187 (local
  endpoint 1346–1424 → ipv4_local_delivery lib/local_delivery.h:229 →
  tail_call_policy :43 on the destination endpoint's program, or
  redirect_ep :82–96 → `ctx_redirect_peer`). Kernel side: `bpf_redirect_peer`
  → `skb_do_redirect` (net/core/filter.c: `ndo_get_peer_dev`, skb->dev =
  peer, `skb_scrub_packet(skb, false)`, return -EAGAIN) → in
  `__netif_receive_skb_core` the TC_ACT_REDIRECT case does `goto
  another_round` (verify the exact lines around dev.c:6062–6090). So the skb
  never leaves the softirq, never touches `veth_xmit`, the backlog, or any
  host-namespace netfilter hook; it re-enters the core with dev = the pod's
  eth0 and runs the pod netns' own (empty) hooks. Overlay the netfilter chart
  and grey out what is skipped. Host → pod and pod → host paths via
  cilium_host/cilium_net (`cil_from_host`, `cil_to_host`, attachment table
  in pkg/datapath/loader host.go:249/255/105/110/165). Reply direction is
  symmetric. Mention what changes with EnableEndpointRoutes (cil_to_container
  on the lxc egress) in one paragraph.
- Bench: in kind-worker run `pwru --filter-trace-tc --filter-dst-ip
  10.64.1.10 --output-meta` (server pod IP; use the pod's real port) while
  `kubectl exec -n acme far-client -- curl -s http://10.64.1.10:PORT/`. Show
  program names (`cil_from_container`) in the transcript and the missing
  `veth_xmit`/`nf_hook_slow`. Write `lab/14-cilium.sh` (kubectl + docker exec
  wrapper; no cluster changes).

### ch15 — Cilium cross node, tunnel modes, world (scenario 7, second half)
- Tunnel egress: ipv4_forward_to_destination tunnel branch 1460–1545 →
  encap_and_redirect_lxc :1532 → lib/encap.h `__encap_and_redirect_with_nodeid`
  :254–279 → ctx_set_encap_info4 lib/overloadable_skb.h:189–222 (tunnel_id =
  source identity, remote = node IP) → `ctx_redirect(ENCAP_IFINDEX)` →
  kernel `bpf_redirect` → `skb_do_redirect` → `__bpf_tx_skb` → `dev_queue_xmit`
  on cilium_geneve → tcx egress cil_to_overlay bpf_overlay.c:781 →
  `geneve_xmit` → `udp_tunnel_xmit_skb` → `iptunnel_xmit` → `ip_local_out` in
  the host netns: LOCAL_OUT and POST_ROUTING run for the OUTER UDP packet →
  route → eth0 tcx egress cil_to_netdev bpf_host.c:1501 (handle_nat_fwd
  :1707; overlay traffic is not masqueraded, find the check) → NIC.
- Tunnel ingress on the far node: eth0 tcx ingress cil_from_netdev
  bpf_host.c:1290 (no TUNNEL_PORT handling: passes to stack) → `ip_rcv` →
  PRE_ROUTING/LOCAL_IN on the outer → `udp_rcv` → `geneve_udp_encap_recv` →
  `geneve_rx` → `gro_cells_receive` → `netif_receive_skb` on cilium_geneve →
  tcx ingress cil_from_overlay bpf_overlay.c:650 (get_tunnel_key :718 →
  identity) → ipv4_local_delivery → redirect_peer into the pod. Netfilter
  sees the outer packet on both hosts and never the inner one. VXLAN: same
  shape with `vxlan_xmit`/`vxlan_rcv`, UDP 8472, VNI = identity; Geneve adds
  TLV options. Native routing: fib_redirect_v4 :1550 → `bpf_fib_lookup` →
  `ctx_redirect(ifindex)` to eth0 → cil_to_netdev → wire; far node eth0
  cil_from_netdev → ipcache → local endpoint → redirect_peer: with BPF host
  routing the stack is never entered; with legacy host routing the skb is
  passed to the stack and routed to the lxc device (endpoint routes).
- World: pod → cil_from_container → destination not in ipcache as an
  endpoint → pass_to_stack :1565–1583 → `ip_rcv` on the lxc device in the
  host netns → PRE_ROUTING → route → FORWARD → POST_ROUTING → eth0 tcx egress
  cil_to_netdev → handle_nat_fwd → snat_v4_nat lib/nodeport_egress.h:407
  (BPF masquerade to the node IP, state in cilium_snat_v4_external; iptables
  MASQUERADE not involved). Return: eth0 ingress cil_from_netdev →
  rev-SNAT → ipcache → redirect to the pod. Say explicitly where the skb
  re-enters the netfilter chart (host FORWARD path for world traffic) and
  where it never enters it (pod-to-pod).
- Bench: pwru in kind-worker with `--filter-trace-tc --kmods geneve,veth`
  for acme/client (worker2) → acme/server (worker), showing cil_from_netdev,
  udp_rcv, geneve_rx, cil_from_overlay, and the redirect. Also a world flow
  from a pod on kind-worker to 172.18.0.1 or 1.1.1.1 showing pass to stack,
  nf_hook_slow on FORWARD, cil_to_netdev. Save both to notes/traces.md.
- Labs: `lab/15-kind-vxlan.yaml` and `lab/15-kind-native.yaml` (kind
  configs for NEW throwaway clusters named pp-vxlan / pp-native, never the
  existing one) with the cilium install commands as comments for the user.
  Do not create these clusters yourself.

### ch16 — epilogue
- Master table: all 12 scenarios × the ordered list of functions/hooks the
  skb visits (this is finish line #1; make it dense and correct, link each
  row to its chapter).
- Traps and fast paths: nf_flow_table (FORWARD conntrack offload,
  `nf_flow_offload_ip_hook` at the netdev ingress hook, so the FORWARD chain
  is skipped after the first packet), netkit (Cilium 1.16+ replacement for
  veth: BPF runs in `netkit_xmit`, delivers with `__netif_rx` to the peer;
  LWN 949960), tcx vs clsact (`tcx_run` dev.c:4484–4491 runs before legacy
  `tc_run`), BIG TCP (gso_ipv4_max_size), NF_INET_INGRESS hook. Limitations
  of this dossier (what was not traced on the bench: unix sockets, IPVS,
  host-only labs; diagrams not visually rendered). Keep ≤ 1500 words.

## 4. Closing tasks, in order

1. `build/glossary.html` → `<section id="glossary">` merging every `.words`
   dl, grouped by chapter with a heading per chapter and anchors back.
2. `build/references.html` → `<section id="references">` grouped by layer
   (HW, L2, L3, SOCK, BPF, LAB) from notes/refs-verified.md; each entry title
   + URL + one line why it matters; no unverified URL.
3. Append both, then delete the `<!--APPEND-->` line.
4. Reading times: run artifacts/audit.py, take its per-chapter minutes, replace `RTn`
   in the TOC `<span class="rt">RTn · TAG</span>` and `~RTn min` in each
   chmeta by line-oriented Python (not by hand). Hero meta placeholders
   `~WORDS words · ~MINUTES minutes · DIAGRAMS diagrams` → real totals.
5. Final `python3 artifacts/audit.py`: 0 early uses, all diagrams OK, no nesting
   errors, BANNED empty, em dashes per the spec.
6. `lab/README.md`: prerequisites table (tool → package → which lab), the
   kind-worker copy commands (`docker exec kind-worker rm -rf /root/lab;
   docker cp lab/. kind-worker:/root/lab/`; `docker cp /usr/bin/pwru
   kind-worker:/usr/local/bin/pwru`), the host-vs-node column per lab.
7. Update the repo `README.md` with two lines pointing at the dossier and
   lab/ (it is otherwise empty).
8. Append a dated status line to
   `/home/wazir/.claude/projects/-home-wazir-workspace-repos-linux-networking-playground/memory/packet-path-dossier.md`
   (what is delivered, what remains unverified).

## 5. Bench facts and pitfalls

- Root shell: `docker exec kind-worker bash -c '…'`. Node shares the host
  kernel 7.2.3; device modules autoload from the host; node lacks ping,
  tcpdump, bpftool (use curl + `python3 -m http.server`); init-netns-only
  sysctls (netdev_budget, netdev_max_backlog, gro_normal_batch) are invisible
  in the node.
- pwru 1.0.12 at kind-worker:/usr/local/bin/pwru (re-copy if the node was
  restarted). Probes vmlinux skb functions only unless `--kmods a,b` (real
  module names only; built-in names like nft_counter or sch_fq_codel fail
  with "failed to open /sys/kernel/btf/…") or `--all-kmods`.
  `--filter-netns /run/netns/NAME`, `--filter-trace-tc`, `--filter-trace-xdp`,
  `--output-meta`, `--output-tuple`. Shows drop reasons
  (`sk_skb_reason_drop(SKB_DROP_REASON_…)`). Cannot match unix-socket skbs.
  Run it in the background with a timeout, e.g.
  `timeout 20 pwru … > /tmp/x.txt 2>&1 &`, generate traffic, wait, read.
- nft tracing: `stdbuf -oL nft monitor trace` and `pkill -TERM nft`; do not
  name an nft chain `in`.
- Labs are copied with `docker exec kind-worker rm -rf /root/lab; docker cp
  lab/. kind-worker:/root/lab/` (plain `docker cp lab …` nests the dir).
- Cilium reading: fork at ~/workspace/neverinstall/cilium; agent config via
  `kubectl -n kube-system exec ds/cilium -- cilium-dbg status --verbose` and
  `cilium-dbg bpf …` commands (read-only).
- Earlier verified kernel anchors you will point back to: generic XDP inside
  `__netif_receive_skb_core` dev.c:6023–6035, taps 6048–6057, tc ingress
  6062–6070, rx_handler 6097–6116, ptype demux 6160–6177; `__dev_queue_xmit`
  :4771 (egress tc :4812, `q->enqueue` :4834, noqueue direct :4878);
  routing `ip_route_input_slow` route.c:2286, RTN_LOCAL :2397, forwarding
  check :2405–2407, `ip_error` :990; `nf_hook` netfilter.h:227–275,
  `nf_hook_slow` core.c:612; conntrack `nf_conntrack_in` nf_conntrack_core.c:2004,
  `nf_confirm` nf_conntrack_proto.c:240–265; NAT `nf_nat_inet_fn`
  nf_nat_core.c:898; `ip_rcv_core` skb_orphan ip_input.c:581–583;
  `tcp_v4_rcv` tcp_ipv4.c:2070; `sock_alloc_file` socket.c:525.

## 6. Final report (to the parent agent, who relays it to the user)

Structured, plain, no hedging:
1. What is delivered: file, size, chapters, diagram count, word total and
   reading time, final audit output verbatim.
2. What was traced on the bench (list) and what is labelled "expected" only.
3. Judgment calls you made and anything left out, with the reason.
4. Three or four post-delivery probing questions for the reader per the spec
   §8.1 (they will be quizzed later with the Alvar `probe` skill), written
   verbatim so they can be relayed.
5. Files touched.
