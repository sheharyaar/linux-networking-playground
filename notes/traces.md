# Real pwru transcripts from the kind-worker bench (kernel 7.2, pwru 1.0.12), 2026-09-17. Columns: netns iface len func.

## veth pair, TCP SYN, curl in pp-a → http.server in pp-b (--kmods veth)
4026533305 (pp-a) : ip_local_out > __ip_local_out > ip_output > ip_finish_output > __ip_finish_output > ip_finish_output2 > neigh_resolve_output > __neigh_event_send > [skb_clone > ipv4_neigh_lookup > neigh_resolve_output on first ARP] > eth_header > skb_push(74) > __dev_queue_xmit > qdisc_pkt_len_segs_init > netdev_core_pick_tx > validate_xmit_skb > netif_skb_features > passthru_features_check > skb_network_protocol > skb_csum_hwoffload_help > validate_xmit_xfrm > dev_hard_start_xmit > veth_xmit[veth] > skb_clone_tx_timestamp > __dev_forward_skb > __dev_forward_skb2 > skb_scrub_packet > eth_type_trans
4026534700 (pp-b) vb: __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb > __netif_receive_skb_one_core > ip_rcv > ip_rcv_core > tcp_wfree (skb_orphan in ip_rcv_core :583 "Must drop socket now because of tproxy") > ip_rcv_finish_core > ip_route_input_noref > ip_route_input_slow > fib_validate_source > __fib_validate_source > ip_local_deliver > ip_local_deliver_finish > ip_protocol_deliver_rcu(40) > raw_local_deliver > tcp_v4_rcv > __inet_lookup_listener > inet_lhash2_lookup > sk_filter_trim_cap > security_sock_rcv_skb > bpf_lsm_socket_sock_rcv_skb > tcp_v4_fill_cb > tcp_v4_do_rcv > tcp_rcv_state_process > tcp_v4_conn_request > tcp_conn_request > tcp_v4_route_req > ... > tcp_try_fastopen > consume_skb > kfree_skbmem
Note: no veth_xmit without --kmods veth. No nf_hook_slow (fresh netns, no tables). pwru attached 1598 kprobes (vmlinux).

## same, with a packet socket tap + tc clsact matchall pass on vb (--kmods veth,cls_matchall,act_gact)
pp-b vb: __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb > __netif_receive_skb_one_core > deliver_skb > packet_rcv > skb_push > skb_clone(74) > consume_skb > qdisc_pkt_len_segs_init > tc_run > tcf_classify > mall_classify[cls_matchall] > tcf_action_exec > tcf_gact_act[act_gact] > ip_rcv > ...
/proc/net/ptype in pp-b: "ALL vb packet_rcv" while the tap is open; 0800 ip_rcv, 0806 arp_rcv, 86dd ipv6_rcv.

## native XDP (xdp_pass) on vb (--kmods veth --filter-trace-xdp)
skb1 pp-b vb: veth_xdp_rcv_skb[veth] > tcp_wfree > consume_skb > skb_release_head_state > skb_release_data > kfree_skbmem   (old skb dies: skb_pp_cow_data because TCP clone → head locked)
xdp_buff addr 0xfffff16e...: bpf_prog_8040a002a5caccda_xdp_pass_prog[bpf](xdp)
skb2 pp-b vb (new addr): eth_type_trans > gro_receive_skb > dev_gro_receive > skb_defer_rx_timestamp > qdisc_pkt_len_segs_init > tc_run > ip_rcv_core (no ip_rcv: list path ip_list_rcv) > ip_rcv_finish_core > ip_route_input_noref > ... > tcp_v4_rcv
## generic XDP on vb
pp-b vb: __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb > __netif_receive_skb_one_core > pskb_expand_head(74) > skb_release_data > bpf_prog_run_generic_xdp > qdisc_pkt_len_segs_init > tc_run > ip_rcv > ip_rcv_core > tcp_wfree > ip_rcv_finish_core ... (same skb throughout)

## router pp-rt (c0 10.5.1.2 → r0 | r1 → s0 10.5.2.2), nft table inet lab with rawpre(nftrace)/prerouting/forward(ct counters)/postrouting/input/output/natpost, --all-kmods, --filter-netns pp-rt
SYN in r0: __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb > __netif_receive_skb_one_core > ip_rcv > ip_rcv_core > tcp_wfree > nf_hook_slow > ipv4_conntrack_defrag[nf_defrag_ipv4] > nft_do_chain_inet[nf_tables] (raw -300) > ipv4_conntrack_in[nf_conntrack] > nf_conntrack_in > nf_conntrack_tcp_packet > nf_checksum > nf_ip_checksum > nf_nat_ipv4_pre_routing[nf_nat] > nf_nat_inet_fn > nft_do_chain_inet (filter 0) > ip_rcv_finish_core > ip_route_input_noref > ip_route_input_slow > fib_validate_source > __fib_validate_source > ip_forward > pskb_expand_head (skb_cow: cloned skb, TTL write) > skb_release_data > skb_headers_offset_update > nf_hook_slow (FORWARD) > nft_do_chain_inet > ip_forward_finish > ip_output
out r1: nf_hook_slow (POST_ROUTING) > nft_do_chain_inet (filter) > nf_nat_ipv4_out[nf_nat] > nf_nat_inet_fn > nft_nat_do_chain[nft_chain_nat] > nf_confirm[nf_conntrack] > __nf_conntrack_confirm > ip_finish_output > __ip_finish_output > ip_finish_output2 > neigh_resolve_output > __neigh_event_send > eth_header > skb_push > __dev_queue_xmit > ... > dev_hard_start_xmit > veth_xmit[veth] > skb_clone_tx_timestamp > __dev_forward_skb > __dev_forward_skb2 > skb_scrub_packet > eth_type_trans
nft monitor trace (stdbuf -oL needed): trace id X inet lab rawpre packet: iif "r0" ... ; rawpre rule ip saddr 10.5.1.2 meta nftrace set 1 (verdict continue); rawpre policy accept; prerouting packet/policy accept; forward packet iif "r0" oif "r1"; forward rule ct state new counter ... (verdict continue); forward policy accept; postrouting ...; natpost ... policy accept.
Counters after one curl: ct state new 1 packet/60 bytes; established,related 11 packets/1440 bytes. conntrack -L: tcp 6 114 TIME_WAIT src=10.5.1.2 dst=10.5.2.2 sport=51770 dport=8080 src=10.5.2.2 dst=10.5.1.2 sport=8080 dport=51770 [ASSURED]

## masquerade on the router (natpost: oifname r1 masquerade)
SYN at POST_ROUTING (r1): nf_hook_slow > nft_do_chain_inet (filter 0) > nf_nat_ipv4_out[nf_nat] (100) > nf_nat_inet_fn > nft_nat_do_chain[nft_chain_nat] > nf_nat_masquerade_ipv4 > nf_nat_manip_pkt > nf_nat_ipv4_manip_pkt > skb_ensure_writable > l4proto_manip_pkt > skb_ensure_writable > nf_csum_update > inet_proto_csum_replace4 x2 | tuple flips 10.5.1.2:57158 → 10.5.2.1:57158 | nf_xfrm_me_harder > __xfrm_decode_session > nf_confirm > __nf_conntrack_confirm > ip_finish_output ...
SYN-ACK at PRE_ROUTING (r1): ip_rcv > ip_rcv_core > sock_edemux (destructor of a request-sock-built skb) > nf_hook_slow > ipv4_conntrack_defrag > nft_do_chain_inet (raw) > ipv4_conntrack_in > nf_conntrack_in > nf_conntrack_tcp_packet > nf_checksum > nf_ip_checksum > nf_nat_ipv4_pre_routing > nf_nat_inet_fn > nf_nat_manip_pkt (no chain walk: mapping stored) > ... inet_proto_csum_replace4 x2 | tuple flips dst 10.5.2.1 → 10.5.1.2 | nft_do_chain_inet (filter) > ip_rcv_finish_core > ip_route_input_noref > ip_route_input_slow > fib_validate_source > ip_forward
conntrack -L: tcp 6 112 TIME_WAIT src=10.5.1.2 dst=10.5.2.2 sport=57158 dport=8080 src=10.5.2.2 dst=10.5.2.1 sport=8080 dport=57158 [ASSURED]
nft trace: forward rule ct state new counter (verdict continue); natpost rule oifname "r1" masquerade (verdict accept). Server log shows client 10.5.1.2? No: server saw "10.5.1.2"?? (log line printed 10.5.1.2 from an earlier non-NAT run; with NAT the server sees 10.5.2.1.)

## lo: kind-worker root netns, curl --interface 10.128.0.75 http://172.18.0.4:8081 (server bound 0.0.0.0)
ip route get 172.18.0.4 from 10.128.0.75 → "local 172.18.0.4 from 10.128.0.75 dev lo table local"
SYN: ip_local_out > __ip_local_out > nf_hook_slow (LOCAL_OUT) > ip_output > nf_hook_slow[lo] (POST_ROUTING) > ip_finish_output > __ip_finish_output > ip_finish_output2 > __dev_queue_xmit[lo] > qdisc_pkt_len_segs_init > netdev_core_pick_tx > validate_xmit_skb > netif_skb_features > skb_network_protocol > skb_csum_hwoffload_help > validate_xmit_xfrm > dev_hard_start_xmit > loopback_xmit > skb_clone_tx_timestamp > tcp_wfree (skb_orphan in loopback_xmit :80) > eth_type_trans > __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb > __netif_receive_skb_one_core > ip_rcv > ip_rcv_core > nf_hook_slow (PRE_ROUTING) > __inet_lookup_listener > inet_lhash2_lookup x2 (early demux) > ip_rcv_finish_core > ip_local_deliver > nf_hook_slow (LOCAL_IN) > ip_local_deliver_finish > ip_protocol_deliver_rcu > raw_local_deliver > tcp_v4_rcv > __inet_lookup_listener > ... > tcp_v4_do_rcv > tcp_rcv_state_process > tcp_v4_conn_request > tcp_conn_request > ... > consume_skb
Interface column: "0" before the route is attached, then lo:1 for everything. Node root netns has nft tables → nf_hook_slow at all four hooks.

## TCP data segment (HTTP response, 400 bytes) arriving on the client side of the veth pair
tcp_v4_rcv > sk_filter_trim_cap > security_sock_rcv_skb > bpf_lsm_socket_sock_rcv_skb > tcp_v4_fill_cb > tcp_v4_do_rcv > tcp_rcv_established > tcp_urg > tcp_data_queue > tcp_queue_rcv > tcp_event_data_recv > [later, process context] sock_rfree > skb_attempt_defer_free > napi_consume_skb > skb_release_head_state > skb_release_data > kfree_skbmem

## veth: the two receive doors (kind-worker, pwru 1.0.12 --kmods veth, 2026-09-18)

Setup: lab/09-veth.sh (pp-a va 10.9.0.1 — vb 10.9.0.2 pp-b), curl from pp-a to a python http.server in pp-b.
The /tmp copies of these transcripts were lost at reboot; the function order below is what pwru printed, condensed to the receive half, one skb address throughout.

Door 1 (default; also with `ethtool -K vb gro on` alone, because the sender still has TSO so the skb is not eligible):

    veth_xmit[veth] > __netif_rx > netif_rx_internal > enqueue_to_backlog > … (softirq) … > __netif_receive_skb_core > tc_run > ip_rcv > ip_rcv_core > ip_rcv_finish_core

Door 2 (`ethtool -K vb gro on` in pp-b AND `ethtool -K va tso off gso off` in pp-a; the sender now segments, every skb is eligible, veth_xmit takes the NAPI branch):

    veth_xmit[veth] > veth_xdp_rcv_skb[veth] > tcp_wfree > pskb_expand_head > skb_release_data > skb_headers_offset_update > gro_receive_skb > dev_gro_receive > inet_gro_receive > tcp4_gro_receive > tcp_gro_receive > skb_defer_rx_timestamp > qdisc_pkt_len_segs_init > tc_run > ip_rcv_core > ip_rcv_finish_core

Notes: without `--kmods veth` neither veth_xmit nor veth_xdp_rcv_skb is printed (module functions are not probed by default). pskb_expand_head in door 2 is the headroom fix-up before GRO, not a new skb: the address column is unchanged. Features were restored afterwards (`ethtool -K va tso on gso on`, `ethtool -K vb gro off`).

## ch8 bench, 2026-09-18 (kind-worker, pwru 1.0.12)

IMPORTANT pwru correction: this build has NO `--filter-dst-ip` / `--filter-dst-port`.
Filtering is by pcap expression as a positional argument, e.g.
`pwru --output-meta "tcp and host 172.18.0.4 and port 4240"`.
Flags that do exist: --filter-netns, --filter-ifname, --filter-func, --filter-mark,
--filter-skb-expr, --filter-trace-tc, --filter-trace-xdp, --filter-track-skb, --kmods,
--all-kmods, --output-meta (default true), --output-tuple (default true), --output-caller,
--output-stack, --output-tcp-flags, --output-limit-lines, --timestamp.

### lo in the node root netns: `curl --interface 10.128.0.75 http://172.18.0.4:4240/healthz`
(4240 = cilium health listener, already running; nothing was started for this trace.)

Route lookup, live:
    # ip route show table local
    local 172.18.0.4 dev eth0 proto kernel scope host src 172.18.0.4
    # ip route get 172.18.0.4 from 10.128.0.75
    local 172.18.0.4 from 10.128.0.75 dev lo table local
The local-table entry names eth0; the lookup answers dev lo. That is the RTN_LOCAL
override at net/ipv4/route.c:2881-2882 (`dev_out = l3mdev_master_dev_rcu(...) ? : net->loopback_dev`).

SYN, one skb address 0xffff88df0dbcfee8 from first line to last:
    ip_local_out > __ip_local_out > nf_hook_slow (LOCAL_OUT) > ip_output >
    nf_hook_slow (POST_ROUTING, iface lo:1) > ip_finish_output > __ip_finish_output >
    ip_finish_output2 > __dev_queue_xmit > qdisc_pkt_len_segs_init > netdev_core_pick_tx >
    validate_xmit_skb > netif_skb_features > skb_network_protocol > skb_csum_hwoffload_help >
    validate_xmit_xfrm > dev_hard_start_xmit > loopback_xmit > skb_clone_tx_timestamp >
    tcp_wfree > eth_type_trans > __netif_rx > netif_rx_internal > enqueue_to_backlog >
    __netif_receive_skb > __netif_receive_skb_one_core > ip_rcv > ip_rcv_core >
    nf_hook_slow (PRE_ROUTING) > __inet_lookup_listener > inet_lhash2_lookup >
    ip_rcv_finish_core > ip_local_deliver > nf_hook_slow (LOCAL_IN) > ip_local_deliver_finish >
    ip_protocol_deliver_rcu > raw_local_deliver > tcp_v4_rcv > __inet_lookup_listener >
    inet_lhash2_lookup > sk_filter_trim_cap > security_sock_rcv_skb >
    bpf_lsm_socket_sock_rcv_skb > tcp_v4_fill_cb > tcp_v4_do_rcv > tcp_rcv_state_process >
    tcp_conn_request > tcp_v4_route_req > security_inet_conn_request > tcp_try_fastopen

Four nf_hook_slow calls = the chart twice (LOCAL_OUT, POST_ROUTING, PRE_ROUTING, LOCAL_IN).
IFACE column: 0 at ip_local_out, lo:1 from ip_output onward.
NO ip_route_input_noref / ip_route_input_slow anywhere in the 1631-line capture.
Mechanism (source-verified): loopback_xmit calls skb_dst_force (drivers/net/loopback.c:85),
so the OUTPUT route survives into the receive half; that route was built with RTCF_LOCAL so
rt_dst_alloc already set rt->dst.input = ip_local_deliver (net/ipv4/route.c:1693); and
ip_rcv_finish_core only does an input lookup when `!skb_valid_dst(skb)`
(net/ipv4/ip_input.c:406, skb_valid_dst at include/net/dst_metadata.h:93).
This is the exact opposite of veth, where skb_scrub_packet drops the dst.

### tap on lo: once or twice? — TWICE, measured
Throwaway AF_PACKET SOCK_RAW tap bound to lo in kind-worker (/tmp/pp-tap.py, python3, deleted after).
Every frame of the connection appeared exactly twice with identical TCP sequence numbers:
    ('OUTGOING', 35726, 4240, 1415493697)
    ('HOST',     35726, 4240, 1415493697)
    ('OUTGOING', 4240, 35726, 1308798598)
    ('HOST',     4240, 35726, 1308798598)
    ... TOTAL frames seen by the tap: 24  (12 packets x 2)
Mechanism: xmit_one calls dev_queue_xmit_nit when a tap is active (net/core/dev.c:3883-3884);
dev_queue_xmit_nit clones and sets skb2->pkt_type = PACKET_OUTGOING (dev.c:2597); then the
same skb is delivered to ptype_all again on the receive side as PACKET_HOST.
The PACKET_LOOPBACK suppression in af_packet.c (:1893 packet_rcv_spkt, :2144 packet_rcv,
:2273 tpacket_rcv) does NOT apply here: PACKET_LOOPBACK is set only by dev_loopback_xmit
(dev.c:4345), the multicast/broadcast loopback helper, not by loopback_xmit.

### same pod, two containers (throwaway ns pp-demo, pod pp-twins, deleted after)
Containers alpha and beta, both nicolaka/netshoot:v0.13, pod IP 10.128.0.82 on kind-worker.
    alpha: ip -br a -> lo, eth0@if19 10.128.0.82/32 ; readlink /proc/self/ns/net -> net:[4026532689]
    beta : ip -br a -> lo, eth0@if19 10.128.0.82/32 ; readlink /proc/self/ns/net -> net:[4026532689]
    beta : ip route get 10.128.0.82 from 10.128.0.82 -> local 10.128.0.82 from 10.128.0.82 dev lo
`nc -l -p 9099 -s 10.128.0.82` in alpha; `echo hello | nc 10.128.0.82 9099` from beta.
ss -tlnp in alpha: LISTEN 10.128.0.82:9099 users:(("nc",pid=27,fd=3))
ss -tlnp in beta : LISTEN 10.128.0.82:9099   <-- same socket, Process column EMPTY
  (shared network namespace, separate PID namespace: ss finds the socket in the shared
   netns table but cannot map its inode to a process in its own /proc)

pwru --output-meta --filter-trace-tc "tcp and port 9099": 390 event lines.
    distinct NETNS column values: 4026532689 and 0 (0 = skb->dev NULL after delivery)
    distinct IFACE column values: lo:1 and 0
    grep -c 'cil_|veth_xmit|nf_hook_slow|tc_run|lxc'  ->  0
So: never the host netns, never an lxc device, no Cilium tc program, no veth_xmit, and no
nf_hook_slow at all (the pod netns has no registered hook entries; the four hook points are
still traversed, the inline nf_hook fast path just returns immediately).
Path is identical to the root-netns lo trace minus the nf_hook_slow lines.

## ch9 bench, 2026-09-18: veth, both doors, real skb addresses (kind-worker, pwru --kmods veth)

Topology built with docker exec in kind-worker: pp-a(va 10.9.0.1) <-veth-> pp-b(vb 10.9.0.2).
netns inodes: pp-a = 4026534764, pp-b = 4026534837. ifindex: va = 21, vb = 20.
Traffic: `ip netns exec pp-a curl -s --max-time 2 http://10.9.0.2:9099/` (no listener; the SYN
still crosses and is answered with a RST, which is enough to trace the whole path).

### Door 1 — default (TSO on at the sender, GRO off at the receiver)
One skb address 0xffff88dee6a8b8e8 on EVERY line below. Columns shown: skb, netns, ifindex, func.

    0xffff88dee6a8b8e8  4026534764   0   ip_local_out
    0xffff88dee6a8b8e8  4026534764   0   __ip_local_out
    0xffff88dee6a8b8e8  4026534764   0   ip_output
    0xffff88dee6a8b8e8  4026534764  21   ip_finish_output2
    0xffff88dee6a8b8e8  4026534764  21   neigh_resolve_output
    0xffff88dee6a8b8e8  4026534764  21   __neigh_event_send
    0xffff88dee6a8b8e8  4026534764  21   skb_clone
    0xffff88e0ff246f00  4026534764  21   arp_solicit          <-- a DIFFERENT skb: the ARP request
    0xffff88e0ff246f00  4026534764  21   consume_skb ... kfree_skbmem
    0xffff88dee6a8b8e8  4026534764  21   ipv4_neigh_lookup / neigh_resolve_output / eth_header / skb_push
    0xffff88dee6a8b8e8  4026534764  21   __dev_queue_xmit ... dev_hard_start_xmit
    0xffff88dee6a8b8e8  4026534764  21   veth_xmit[veth]
    0xffff88dee6a8b8e8  4026534764  21   skb_clone_tx_timestamp
    0xffff88dee6a8b8e8  4026534764  21   __dev_forward_skb
    0xffff88dee6a8b8e8  4026534764  21   __dev_forward_skb2
    0xffff88dee6a8b8e8  4026534764  21   skb_scrub_packet
    0xffff88dee6a8b8e8  4026534764  21   eth_type_trans
    0xffff88dee6a8b8e8  4026534837  20   __netif_rx           <-- netns AND ifindex flip here
    0xffff88dee6a8b8e8  4026534837  20   netif_rx_internal
    0xffff88dee6a8b8e8  4026534837  20   enqueue_to_backlog
    0xffff88dee6a8b8e8  4026534837  20   __netif_receive_skb / __netif_receive_skb_one_core
    0xffff88dee6a8b8e8  4026534837  20   ip_rcv > ip_rcv_core > tcp_wfree
    0xffff88dee6a8b8e8  4026534837  20   ip_rcv_finish_core
    0xffff88dee6a8b8e8  4026534837  20   ip_route_input_noref   <-- ROUTE LOOKUP RUNS (contrast with lo)
    0xffff88dee6a8b8e8  4026534837  20   ip_route_input_slow
    0xffff88dee6a8b8e8  4026534837  20   fib_validate_source / __fib_validate_source
    0xffff88dee6a8b8e8  4026534837  20   ip_local_deliver ... tcp_v4_rcv > tcp_v4_send_reset

Two facts this proves: (1) the skb identity is preserved across the namespace boundary, only
skb->dev and the namespace change; (2) unlike the loopback path of chapter 8, the receive half
DOES run ip_route_input_slow, because skb_scrub_packet dropped the dst.

### GRO on the receiver ONLY — still the backlog door
`ip netns exec pp-b ethtool -K vb gro on` (sender keeps TSO on):
    veth_xmit[veth] > __netif_rx > enqueue_to_backlog     (unchanged)
Confirms veth_skb_is_eligible_for_gro: the napi pointer exists but eligibility fails because
the transmitting device still has NETIF_F_ALL_TSO.

### Door 2 — GRO on the receiver AND `ethtool -K va tso off gso off` on the sender
One skb address 0xffff88dee6a8b2e8 throughout; no __netif_rx, no enqueue_to_backlog:

    0xffff88dee6a8b2e8  4026534764  21   eth_type_trans
    0xffff88dee6a8b2e8  4026534837  20   veth_xdp_rcv_skb[veth]
    0xffff88dee6a8b2e8  4026534837  20   tcp_wfree
    0xffff88dee6a8b2e8  4026534837  20   pskb_expand_head      <-- headroom fix-up, SAME skb struct
    0xffff88dee6a8b2e8  4026534837  20   skb_release_data / skb_headers_offset_update
    0xffff88dee6a8b2e8  4026534837  20   gro_receive_skb
    0xffff88dee6a8b2e8  4026534837  20   dev_gro_receive
    0xffff88dee6a8b2e8  4026534837  20   inet_gro_receive
    0xffff88dee6a8b2e8  4026534837  20   tcp4_gro_receive
    0xffff88dee6a8b2e8  4026534837  20   tcp_gro_receive
    0xffff88dee6a8b2e8  4026534837  20   skb_defer_rx_timestamp
    0xffff88dee6a8b2e8  4026534837  20   ip_rcv_core (list path, no ip_rcv)
    0xffff88dee6a8b2e8  4026534837  20   ip_rcv_finish_core > ip_route_input_noref > ip_route_input_slow
    0xffff88dee6a8b2e8  4026534837  20   fib_validate_source ... ip_local_deliver

Features restored and the whole topology deleted afterwards.

### skb_scrub_packet, what it actually clears (net/core/skbuff.c:6278-6299, verified in v7.2)
Always: pkt_type = PACKET_HOST (:6280), skb_iif = 0 (:6281), ignore_df = 0 (:6282),
skb_dst_drop (:6283), skb_ext_reset (:6284), nf_reset_ct (:6285), nf_reset_trace (:6286),
offload_fwd_mark and offload_l3_fwd_mark = 0 under CONFIG_NET_SWITCHDEV (:6289-6290),
ipvs_reset (:6292, clears skb->ipvs_property, include/linux/skbuff.h:5151).
Only when xnet (the two devices are in different netns): skb->mark = 0 (:6296),
skb_clear_tstamp (:6297).
CORRECTION to the handover brief: skb->tc_index is NOT cleared by skb_scrub_packet in v7.2
(tc_index appears in skbuff.c only at :1598, inside skb_copy's CHECK_SKB_FIELD list).
skb->dev is NOT changed by skb_scrub_packet either; the device swap happens in eth_type_trans,
whose first statement is `skb->dev = dev` (net/ethernet/eth.c).

## ch10 bench, 2026-09-18: Linux bridge, plain (kind-worker, pwru --kmods bridge,veth)

Topology: pp-l(vl 10.10.0.1) <-veth-> vl-br | pp-br0 | vr-br <-veth-> pp-r(vr 10.10.0.2).
netns: pp-l = 4026534754, node root = 4026533157, pp-r = 4026534834.
ifindex: vl = 24, vl-br = 23, pp-br0 = 22, vr-br = 25, vr = 26.
Traffic: `ip netns exec pp-l curl -s --max-time 2 http://10.10.0.2:9099/` (no listener needed).

ONE skb address 0xffff88df46234ae8 across all three namespaces:

    netns 4026534754 (pp-l), dev 24 (vl):
      ip_local_out > __ip_local_out > ip_output > ip_finish_output > __ip_finish_output >
      ip_finish_output2 > neigh_resolve_output > __neigh_event_send > skb_clone >
      [ARP on a separate skb 0xffff88dec2a77f00: arp_solicit > consume_skb > kfree_skbmem] >
      ipv4_neigh_lookup > neigh_resolve_output > eth_header > skb_push > __dev_queue_xmit >
      ... > dev_hard_start_xmit > veth_xmit[veth] > __dev_forward_skb > __dev_forward_skb2 >
      skb_scrub_packet > eth_type_trans
    netns 4026533157 (node root), dev vl-br:23:
      __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb >
      __netif_receive_skb_one_core > br_handle_frame_finish[bridge] > br_allowed_ingress[bridge] >
      nbp_switchdev_frame_mark[bridge] > br_forward[bridge] > __br_forward[bridge] >
      nbp_switchdev_frame_mark_tx_fwd_offload[bridge] > br_handle_vlan[bridge]
    dev flips to vr-br:25 here (that is __br_forward doing skb->dev = to->dev):
      br_forward_finish[bridge] > br_dev_queue_push_xmit[bridge] > skb_push >
      br_switchdev_frame_set_offload_fwd_mark[bridge] > __dev_queue_xmit > ... >
      dev_hard_start_xmit > veth_xmit[veth] > __dev_forward_skb2 > skb_scrub_packet > eth_type_trans
    netns 4026534834 (pp-r), dev 26 (vr):
      __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb > ...

HEADLINE: `grep -c nf_hook_slow` over the whole capture = **0**. With br_netfilter not loaded,
an IP packet forwarded by a bridge visits no netfilter hook at all, in any namespace.
(The NF_BR_* hook points are traversed but have no registered entries, and the IPv4 hooks are
never reached because nothing bridges the frame into them.)

`br_handle_frame` itself never appears: its signature is `(struct sk_buff **pskb)`, a double
pointer, so pwru cannot treat it as an skb-carrying function. The first bridge function you see
is its continuation `br_handle_frame_finish`.

Learned fdb after the run:
    4e:14:de:4c:fb:93 dev vl-br master pp-br0
    f6:16:0e:c9:08:a7 dev vr-br master pp-br0

### br_netfilter: NOT traced, labelled expected. Reason recorded.
br_netfilter is not loaded on this host and /proc/sys/net/bridge does not exist. Loading it is
NOT a neutral act: it registers br_nf_ops globally (net/bridge/br_netfilter_hooks.c:1047) and
bridge-nf-call-iptables defaults to 1 (:1225), which would change packet handling for the
docker0 and kind bridges carrying the live cluster. Left unloaded deliberately; the
br_netfilter half of chapter 10 is derived from verified source and labelled expected.

## ch11 bench, 2026-09-18: bond and VRF (kind-worker)

### Bond — active-backup, pp-bond0 10.11.0.1 over slaves pp-s1/pp-s2,
peers bridged together inside netns pp-peer at 10.11.0.2.
pwru --kmods bonding,veth,bridge "tcp and host 10.11.0.2".

EGRESS, one skb 0xffff88ded90e34e8, TWO passes through __dev_queue_xmit:
    dev 0            ip_local_out > __ip_local_out > nf_hook_slow > ip_output
    dev pp-bond0:31  nf_hook_slow > ip_finish_output > __ip_finish_output > ip_finish_output2 >
                     __dev_queue_xmit > qdisc_pkt_len_segs_init > netdev_core_pick_tx >
                     bond_select_queue[bonding] > validate_xmit_skb > ... > dev_hard_start_xmit >
                     bond_start_xmit[bonding] > bond_dev_queue_xmit[bonding]
    dev pp-s1:28     __dev_queue_xmit  <-- SECOND pass, on the slave, with the slave's own qdisc
                     ... > dev_hard_start_xmit > veth_xmit[veth] > ...

INGRESS (the RST coming back), showing RX_HANDLER_ANOTHER:
    dev pp-s1:28     __netif_rx > netif_rx_internal > enqueue_to_backlog >
                     __netif_receive_skb > __netif_receive_skb_one_core
    dev pp-bond0:31  qdisc_pkt_len_segs_init > skb_ensure_writable > ip_rcv > ip_rcv_core >
                     sock_wfree > nf_hook_slow > ...
The device column changes between __netif_receive_skb_one_core and the next line: that is
bond_handle_frame setting skb->dev = bond->dev and returning RX_HANDLER_ANOTHER, so the core
restarts (goto another_round) and ip_rcv sees the bond, never the slave.

bond_handle_frame itself is NOT printed, same reason as br_handle_frame: rx_handlers take
`struct sk_buff **pskb`, so pwru cannot read an skb argument out of them. Bonding functions
actually seen: bond_start_xmit, bond_dev_queue_xmit, bond_select_queue.

### VRF — pp-vrf table 10, enslaving pp-ve 10.12.0.1, peer pp-vp 10.12.0.2 in netns pp-vpeer.
`ip rule show` includes the l3mdev rule:  1000: from all lookup [l3mdev-table]
`ip route show table 10` holds the connected route AND `local 10.12.0.1 dev pp-ve` (the local
entry moved out of the global local table into the VRF table).
Traffic: `ip vrf exec pp-vrf curl -s --max-time 2 http://10.12.0.2:9099/`.
pwru --kmods vrf,veth "tcp and host 10.12.0.2".

EGRESS, one skb, FOUR nf_hook_slow calls:
    dev 0          ip_local_out > __ip_local_out > vrf_l3_out[vrf]
    dev pp-vrf:32  nf_hook_slow    <-- (1) LOCAL_OUT with the VRF device
    dev pp-vrf:32  nf_hook_slow    <-- (2) POST_ROUTING with the VRF device
    dev pp-vrf:32  vrf_finish_direct[vrf]
    dev pp-vrf:32  nf_hook_slow    <-- (3) the normal __ip_local_out LOCAL_OUT
    dev pp-vrf:32  ip_output
    dev pp-ve:34   nf_hook_slow    <-- (4) POST_ROUTING with the real device
    dev pp-ve:34   ip_finish_output > ... > veth_xmit[veth]
Source for (1) and (2): vrf_ip_out (drivers/net/vrf.c:926) takes the direct path
vrf_ip_out_direct (:905) because the VRF has the default qdisc; :911 sets skb->dev = vrf_dev,
:913 runs nf_hook(NF_INET_LOCAL_OUT, ..., vrf_dev), then vrf_output_direct (:876) runs
nf_hook(NF_INET_POST_ROUTING, ...) at :884. vrf_ip_out also calls vrf_nf_set_untracked.

INGRESS, PRE_ROUTING runs TWICE:
    dev pp-ve:34   __netif_rx > ... > ip_rcv > ip_rcv_core > nf_hook_slow  <-- PRE_ROUTING #1, slave dev
    dev pp-ve:34   __inet_lookup_listener > inet_lhash2_lookup
    dev pp-ve:34   vrf_l3_rcv[vrf]          <-- called from ip_rcv_finish via l3mdev_ip_rcv
    dev pp-vrf:32  nf_hook_slow             <-- PRE_ROUTING #2, now with the VRF device
    dev pp-vrf:32  ip_rcv_finish_core > ip_route_input_noref > ip_route_input_slow >
                   fib_validate_source > __fib_validate_source > ip_local_deliver >
                   nf_hook_slow (LOCAL_IN) > ip_local_deliver_finish > ip_protocol_deliver_rcu >
                   raw_local_deliver > tcp_v4_rcv > ... > tcp_add_backlog (curl held the lock)
Call site: net/ipv4/ip_input.c:486, `skb = l3mdev_ip_rcv(skb)` inside ip_rcv_finish (:478),
before ip_rcv_finish_core (:490). vrf_ip_rcv (drivers/net/vrf.c:1340) sets skb->dev = vrf_dev,
skb_iif, IPSKB_L3SLAVE, and calls vrf_rcv_nfhook (:1132) which is the second PRE_ROUTING.
vrf functions actually printed: vrf_l3_out, vrf_finish_direct, vrf_l3_rcv.
All devices and namespaces deleted afterwards.

## ch12 bench, 2026-09-18: macvlan vs ipvlan (kind-worker)

Setup: two lower veth devices in the root netns, peers in netns pp-sw.
  pp-lo0 <-> pp-lo1(pp-sw, 10.13.0.9)   with macvlan pp-mv0 10.13.0.1 mode bridge
  pp-lo2 <-> pp-lo3(pp-sw, 10.14.0.9)   with ipvlan  pp-iv0 10.14.0.2 mode l2

FINDING 1 — two lowers were needed. Creating an ipvlan on the SAME lower device that already
had a macvlan fails with "RTNETLINK answers: Device or resource busy".
netdev_rx_handler_register (net/core/dev.c:5909) returns -EBUSY at :5913-5914 when a handler
is already registered. A device can be exactly one of: bridge port, bond slave, macvlan lower,
ipvlan lower. Never two at once.

FINDING 2 — the MAC and promiscuity, measured:
    lower pp-lo0 a2:b7:4b:50:89:6a     promiscuity 1     <-- macvlan lower
    macvlan      12:19:80:52:7e:cc                       <-- its OWN address
    lower pp-lo2 d2:61:13:ff:1b:54     promiscuity 0     <-- ipvlan lower
    ipvlan       d2:61:13:ff:1b:54                       <-- the SAME address as the lower

FINDING 3 — the receive handoff. Identical except for one function, and that function names
the key each driver uses. pwru --kmods macvlan,ipvlan,veth.

macvlan, one skb 0xffff88dec276f6e8:
    dev 35        ... veth_xmit[veth] > __dev_forward_skb2 > skb_scrub_packet > eth_type_trans
    dev pp-lo0:36 __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb >
                  __netif_receive_skb_one_core
    dev pp-lo0:36 macvlan_forward_source[macvlan]        <-- keyed by MAC
    dev pp-mv0:40 qdisc_pkt_len_segs_init > skb_ensure_writable > ...

ipvlan, one skb 0xffff88df5058bee8:
    dev 38        ... veth_xmit[veth] > __dev_forward_skb2 > skb_scrub_packet > eth_type_trans
    dev pp-lo2:39 __netif_rx > netif_rx_internal > enqueue_to_backlog > __netif_receive_skb >
                  __netif_receive_skb_one_core
    dev pp-lo2:39 ipvlan_get_L3_hdr[ipvlan]              <-- keyed by the L3 header
    dev pp-iv0:41 qdisc_pkt_len_segs_init > skb_ensure_writable > ...

macvlan_handle_frame and ipvlan_handle_frame themselves are not printed (double-pointer
rx_handler signature), but the helper each calls first IS, and it is the one that differs.

### Source confirmations for ch12 (v7.2)
ipvlan L3 transmit: ipvlan_xmit_mode_l3 (ipvlan_core.c:603) first tries a sibling ipvlan
address via ipvlan_addr_lookup (:615) and delivers locally with ipvlan_rcv_frame (:621);
otherwise ipvlan_skb_crossing_ns(skb, ipvlan->phy_dev) at :627 moves the skb onto the PARENT
device, and ipvlan_process_outbound (:536) strips the Ethernet header (:558-560) before
ipvlan_process_v4_outbound (:428) does ip_route_output_flow (:449) and ip_local_out (:460) with
net = dev_net(parent). The comment at :539-541 states this in words. So an L3-mode ipvlan's
egress runs the PARENT namespace's OUTPUT and POSTROUTING.
ipvlan L3S: ipvlan_handle_frame returns RX_HANDLER_PASS for L3S (ipvlan_core.c:793); the device
swap happens instead in ipvlan_nf_input (ipvlan_l3s.c:95), registered at NF_INET_LOCAL_IN with
priority INT_MAX (ipvl_nfops, :117-131), which sets skb->dev = addr->master->dev (:104). So in
L3S the parent's PRE_ROUTING, routing and INPUT chains all run with the LOWER device, and the
skb only becomes the ipvlan device's at the very end of LOCAL_IN.

## ch14/ch15 bench, 2026-09-18: Cilium (kind cluster, fork v1.19.6-vpc.18, tunnel/geneve, TCX, BPF host routing, BPF masquerade)

### CORRECTIONS to the handover brief's bench facts
- Node IPs have CHANGED: kind-worker2 = 172.18.0.2, kind-control-plane = 172.18.0.3,
  kind-worker = 172.18.0.4 (worker unchanged; the other two are swapped versus the brief).
- acme/far-client CANNOT reach acme/server: the fork's CiliumNetworkPolicy
  cilium-vpc-sg-acme-server admits only security group "acme-client", and far-client is in
  "acme-far-client". The drop is visible and is itself a good trace (see below).
- Throwaway namespace pp-demo with pods pp-cli (kind-worker 10.128.0.66), pp-srv
  (kind-worker 10.128.0.82, nginx :80) and pp-cli-far (kind-worker2 10.128.0.57) was used
  instead. No VPC labels, so no policy selects them. Deleted afterwards.
- pwru run inside kind-worker sees the WHOLE host kernel, so one capture contains every kind
  node's netns. netns map: 4026533157 = kind-worker, 4026533092 = kind-worker2,
  4026531833 = the laptop's init netns (br-kind-cilium side), 4026534894 = pp-cli,
  4026534754 = pp-srv, 4026534692 = pp-cli-far.

### ch14 — same node, pp-cli -> pp-srv. pwru --filter-trace-tc --kmods veth "tcp and host 10.128.0.82 and port 80"
One skb 0xffff88df0dbcc2e8:
    netns 4026534894 eth0:42          ip_local_out > __ip_local_out > ip_output >
                                      ip_finish_output2 > __dev_queue_xmit > dev_hard_start_xmit >
                                      veth_xmit[veth] > __dev_forward_skb2 > skb_scrub_packet >
                                      eth_type_trans
    netns 4026533157 ~09ac2395bb83:43 __netif_rx > netif_rx_internal > enqueue_to_backlog >
                                      __netif_receive_skb > __netif_receive_skb_one_core >
                                      bpf_prog_7aa41f27b2ed9b54_cil_from_container[bpf](tc) >
                                      skb_ensure_writable x7 > skb_do_redirect
    netns 4026534754 eth0:44          skb_scrub_packet > ip_rcv > ip_rcv_core > ...
Whole-capture counts for 12 packets: nf_hook_slow 0, veth_xmit 12, enqueue_to_backlog 12,
skb_do_redirect 12, cil_from_container 12, and NO other bpf program.
So per packet exactly ONE veth crossing (pod -> lxc) and then a direct jump into the
destination pod. The second veth pair is never used; the backlog is used once, not twice;
netfilter is never entered at all.

Kernel side, verified in v7.2:
  sch_handle_ingress: tcx_run at net/core/dev.c:4486, case TC_ACT_REDIRECT :4493,
    __skb_push(skb, skb->mac_len) :4498, `if (skb_do_redirect(skb) == -EAGAIN) {
    __skb_pull(...); *another = true; break; }` :4499-4502.
  __netif_receive_skb_core: sch_handle_ingress(..., &another) :6067, `if (another)
    goto another_round;` :6069-6070; the another_round label is at :6017.
  skb_do_redirect net/core/filter.c:2519; BPF_F_PEER branch :2531; requires
    skb_at_tc_ingress :2532; dev = skb_get_peer_dev(dev) :2534 (which calls
    ndo_get_peer_dev, filter.c:2509-2517); REQUIRES the peer to be in a DIFFERENT netns,
    `net_eq(net, dev_net(dev))` is a drop condition :2537; skb->dev = dev :2539;
    skb_scrub_packet(skb, false) :2541  <-- false, so skb->mark is KEPT; return -EAGAIN :2542.
Cilium side (fork v1.19.6-vpc.18): cil_from_container bpf/bpf_lxc.c:2212 (__section_entry
  :2211); tail_handle_ipv4 :2157; handle_ipv4_from_lxc :1591; ipv4_forward_to_destination :1187;
  ipv4_local_delivery bpf/lib/local_delivery.h:229 (ipv4_l3 rewrites the MACs :242,
  local_delivery :247); redirect_ep :82-97 (ctx_redirect :88 when not fast,
  ctx_change_type(PACKET_HOST) :95 when from_tunnel, ctx_redirect_peer :97).

### ch14 bonus — a POLICY DROP, same shape, different ending (acme/far-client -> acme/server)
    netns 4026533157 ~96ba345865a7:13 bpf_prog_7aa41f27b2ed9b54_cil_from_container[bpf](tc) >
                                      skb_ensure_writable x7 >
                                      sk_skb_reason_drop(SKB_DROP_REASON_TC_INGRESS)
curl reports 000 / exit 28. The denial happens in the same program that would otherwise
redirect, before the packet has touched anything else.

### ch15 — cross node, pp-cli-far (kind-worker2) -> pp-srv (kind-worker), Geneve
pwru --filter-trace-tc --kmods geneve,veth "(udp and port 6081) or (tcp and host 10.128.0.82 and port 80)"
ONE skb 0xffff88dfec7e0ae8 for the entire two-node path:
    netns 4026534692 eth0:28   ip_local_out ... veth_xmit > skb_scrub_packet > eth_type_trans
    netns 4026533092 dev 29    __netif_rx > enqueue_to_backlog > __netif_receive_skb_one_core >
                               cil_from_container > skb_do_redirect > __bpf_redirect
    netns 4026533092 dev 27    __dev_queue_xmit > cil_to_overlay > dev_hard_start_xmit >
      (cilium_geneve)          geneve_xmit[geneve] > geneve_build_gro_hint_opt >
                               skb_tunnel_check_pmtu > geneve_build_skb > skb_scrub_packet >
                               iptunnel_handle_offloads > udp_set_csum > iptunnel_xmit >
                               skb_scrub_packet > skb_push
    ---- the TUPLE COLUMN FLIPS HERE from 10.128.0.57:33200->10.128.0.82:80(tcp)
         to 172.18.0.2:62469->172.18.0.4:6081(udp) ----
    netns 4026533092 dev 27    ip_local_out > __ip_local_out > nf_hook_slow (LOCAL_OUT) > ip_output
    netns 4026533092 eth0:2    nf_hook_slow (POST_ROUTING) > ip_finish_output2 >
                               __dev_queue_xmit > cil_to_netdev > dev_hard_start_xmit >
                               veth_xmit[veth] > skb_scrub_packet > eth_type_trans
    netns 4026531833 dev 7     (the laptop's bridge) __netif_rx > ... > veth_xmit[veth] > ...
    netns 4026533157 eth0:2    __netif_rx > enqueue_to_backlog > __netif_receive_skb_one_core >
                               cil_from_netdev > ip_rcv > ip_rcv_core > nf_hook_slow (PRE_ROUTING) >
                               ip_rcv_finish_core > udp_v4_early_demux > ip_route_input_noref >
                               ip_route_input_slow > ip_local_deliver > nf_hook_slow (LOCAL_IN) >
                               ip_protocol_deliver_rcu > udp_rcv > udp_queue_rcv_one_skb >
                               geneve_udp_encap_recv[geneve] > __iptunnel_pull_header >
                               skb_pull_rcsum > skb_scrub_packet > eth_type_trans
    ---- the TUPLE COLUMN FLIPS BACK to the inner TCP tuple here ----
    netns 4026533157 cilium_geneve:7  gro_cells_receive > netif_rx > netif_rx_internal >
                               enqueue_to_backlog > __netif_receive_skb_one_core >
                               cil_from_overlay > skb_ensure_writable x9 > skb_do_redirect
    netns 4026534754 eth0:44   skb_scrub_packet > ip_rcv > ip_rcv_core > ip_rcv_finish_core >
                               ip_route_input_slow > ip_local_deliver > ip_protocol_deliver_rcu >
                               tcp_v4_rcv > __inet_lookup_listener
MEASURED: of the 116 nf_hook_slow calls in kind-worker's netns in that capture, 116 carry the
OUTER udp 6081 tuple and 0 carry the inner tcp tuple. Netfilter sees only the outer packet.
Programs seen in the capture: cil_to_netdev 68, cil_from_netdev 68, cil_to_overlay 37,
cil_from_overlay 37, cil_to_host 25, cil_from_host 25, cil_from_container 12.

### ch15 — pod to world, pp-cli (10.128.0.66) -> 172.18.0.1:9099
pwru --filter-trace-tc --kmods veth "tcp and host 172.18.0.1 and port 9099"
    netns 4026534894 eth0:42          ip_local_out ... veth_xmit > skb_scrub_packet > eth_type_trans
    netns 4026533157 ~09ac2395bb83:43 __netif_rx > enqueue_to_backlog > cil_from_container >
                                      skb_ensure_writable x4 > skb_do_redirect > skb_pull
    netns 4026533157 eth0:2           qdisc_pkt_len_segs_init > cil_to_netdev > skb_ensure_writable
    ---- SOURCE FLIPS 10.128.0.66 -> 172.18.0.4 right here, with
         inet_proto_csum_replace_by_diff. That is the BPF masquerade, inside cil_to_netdev. ----
    netns 4026533157 eth0:2           netdev_core_pick_tx > ... > veth_xmit[veth] > eth_type_trans
    netns 4026531833 dev 7            (leaves the node onto the laptop's bridge)

CORRECTION to the brief: the brief expected world traffic to "pass to stack" and traverse the
host's ip_rcv / PRE_ROUTING / FORWARD / POST_ROUTING. It does NOT, on this cluster.
MEASURED: nf_hook_slow inside kind-worker's netns for this flow = 0. All 4 nf_hook_slow in the
capture are in the laptop's init netns (4026531833), where the masqueraded packet is received
and answered with a RST. The reason is ENABLE_HOST_ROUTING (EnableHostLegacyRouting=false):
ipv4_forward_to_destination takes the fib_redirect_v4 branch rather than pass_to_stack, so the
skb is redirected to eth0 and never enters the node's stack. pass_to_stack (bpf_lxc.c:1565-1583)
is what a cluster WITHOUT BPF host routing would use, and that is the case the brief described.
