# Citation sheet — RX/TX core (kernel v7.2, ~/workspace/repos/linux, HEAD 8d3ae59288f1)

## net/core/dev.c
| function | path:line | note |
|---|---|---|
| netif_rx | net/core/dev.c:5778 | wraps netif_rx_internal :5786 with local_bh_disable |
| __netif_rx | net/core/dev.c:5746 | netif_rx_internal :5753; caller already in BH |
| netif_rx_internal | net/core/dev.c:5706 | no generic XDP here; RPS get_rps_cpu :5721 → enqueue_to_backlog :5725 / :5733 |
| enqueue_to_backlog | net/core/dev.c:5381 | sd->input_pkt_queue __skb_queue_tail :5414; limit net_hotdata.max_backlog :5396; napi_schedule_rps(sd) :5413 |
| napi_schedule_rps | net/core/dev.c:5292 | raises the backlog NAPI |
| process_backlog | net/core/dev.c:6658 | drains sd->process_queue :6678 → __netif_receive_skb :6680; splice input_pkt_queue→process_queue :6704 |
| net_rx_action | net/core/dev.c:7920 | time_limit :7923 (netdev_budget_usecs), budget :7926 (netdev_budget); napi_poll :7958; squeeze :7964-7970 |
| napi_poll / __napi_poll | :7792 / :7725 | n->poll(n, weight) :7739 |
| napi_schedule | include/linux/netdevice.h:560 | inline |
| __napi_schedule / ____napi_schedule | :6724 / :4965 | |
| netif_receive_skb | :6468 | → netif_receive_skb_internal :6474 |
| netif_receive_skb_internal | :6393 | RPS :6406→enqueue_to_backlog :6409; else __netif_receive_skb :6415 |
| netif_receive_skb_list_internal | :6420 | RPS :6438/:6444; __netif_receive_skb_list :6453 |
| __netif_receive_skb / _one_core | :6309 / :6208 | core call :6214 |
| __netif_receive_skb_core | :5986 | ORDER: another_round 6017; generic XDP 6023-6026; skip_classify 6043; skip_taps 6046; ptype_all netns loop 6048 (deliver_skb 6051); dev->ptype_all 6055; skip_taps: 6061; CONFIG_NET_INGRESS 6062; sch_handle_ingress 6067 (another_round 6070); skip_classify: 6080; vlan_do_receive 6091; rx_handler 6097; CONSUMED/ANOTHER/EXACT/PASS 6104/6107/6109/6112; 2nd vlan 6135; deliver_ptype_list_skb 6160,6169,6173,6177 |
| deliver_skb | :2486 | refcount_inc(&skb->users) :2490, pt_prev->func :2491 — no clone |
| deliver_ptype_list_skb | :2496 | |
| dev_queue_xmit_nit | :2549 | TX tap; skb_clone :2575 |
| sch_handle_ingress / egress | :4465 / :4529 | tcx first (4484-4491), legacy tc_run only if TC_ACT_UNSPEC; egress 4543-4549 |
| tcx_run | :4444 | bpf_mprog_foreach_prog |
| do_xdp_generic | :5670 | verdict switch 5678-5695 (REDIRECT→xdp_do_generic_redirect, TX→generic_xdp_tx) |
| netif_receive_generic_xdp | :5590 | mac push 5604; clone/nonlinear/headroom check 5607-5610; bpf_prog_run_generic_xdp 5617 |
| netif_skb_check_for_xdp | :5565 | pskb_expand_head + skb_linearize 5575-5588 |
| generic_xdp_tx | :5645 | netdev_start_xmit :5657 (bypasses qdisc + taps) |
| dev_queue_xmit | include/linux/netdevice.h:3446 | inline |
| __dev_queue_xmit | :4771 | sch_handle_egress :4812; netdev_core_pick_tx :4830; `if (q->enqueue)` :4834 → __dev_xmit_skb :4836; noqueue direct :4839-4890, dev_hard_start_xmit :4878 |
| __dev_xmit_skb | :4185 | |
| dev_hard_start_xmit | :3895 | xmit_one :3905 |
| xmit_one | :3878 | dev_nit_active_rcu :3884 → dev_queue_xmit_nit :3885; netdev_start_xmit :3890 |
| netdev_core_pick_tx | :4722 | |
| is_skb_forwardable | :2432 | real check __is_skb_forwardable include/linux/netdevice.h:4400 |
| ____dev_forward_skb | include/linux/netdevice.h:4440 | skb_scrub_packet(skb, !net_eq(dev_net(dev), dev_net(skb->dev))); skb->priority = 0 |
| __dev_forward_skb2 | :2438 | ____dev_forward_skb :2441; skb->protocol = eth_type_trans :2444; skb_postpull_rcsum |
| __dev_forward_skb | :2451 | check_mtu = true |
| dev_forward_skb | :2475 | __dev_forward_skb ?: netif_rx_internal :2477 |
| softnet_data | include/linux/netdevice.h:3576 | process_queue :3578, input_pkt_queue :3622, backlog (napi_struct) :3624 |

## net/core/gro.c + include/net/gro.h
| napi_gro_receive | include/linux/netdevice.h:4311 | inline → gro_receive_skb |
| gro_receive_skb | net/core/gro.c:638 | gro_skb_finish(gro, skb, dev_gro_receive(gro, skb)) :647 |
| dev_gro_receive | net/core/gro.c:476 | |
| gro_skb_finish | net/core/gro.c:612 | GRO_NORMAL → gro_normal_one :617 (napi_skb_finish renamed) |
| gro_complete tail | net/core/gro.c:301 | flushed skb → gro_normal_one |
| gro_normal_one | include/net/gro.h:537 | batch on gro->rx_list; flush at net_hotdata.gro_normal_batch :543 |
| gro_normal_list | include/net/gro.h:519 | netif_receive_skb_list_internal(&gro->rx_list) :521 |

## skbuff
__alloc_skb net/core/skbuff.c:674; build_skb :508; napi_build_skb :576; skb_clone :2097; skb_scrub_packet :6278-6299 (pkt_type=PACKET_HOST, skb_iif=0, ignore_df=0, skb_dst_drop, skb_ext_reset, nf_reset_ct, nf_reset_trace, ipvs_reset; if xnet: mark=0, skb_clear_tstamp); skb_orphan include/linux/skbuff.h:3389; skb_reset_network_header :3134; __skb_pull :2836.
struct sk_buff include/linux/skbuff.h:886 — dev 894, sk 907, cb 919, _nfct 933, len 935, data_len 936, pkt_type 975, mark 1069, protocol 1082, transport_header 1083, network_header 1084, mac_header 1085, tail 1092, end 1093, head 1094, data 1095, users 1097.

## XDP
xdp_do_redirect net/core/filter.c:4593 (→ __xdp_do_redirect_frame :4523 via xdp_convert_buff_to_frame :4602); xdp_do_generic_redirect :4679; bpf_xdp_redirect :4717; struct xdp_buff include/net/xdp.h:86; struct xdp_frame :294; enum xdp_action include/uapi/linux/bpf.h:6576 (ABORTED 6577, DROP 6578, PASS 6579, TX 6580, REDIRECT 6581); dev_map_enqueue kernel/bpf/devmap.c:552; cpu_map_enqueue kernel/bpf/cpumap.c:793; dev_xdp_install net/core/dev.c:10327; bpf_xdp_link_attach :10678; xdp_convert_buff_to_frame include/net/xdp.h:430; xdp_build_skb_from_frame net/core/xdp.c:849.

## Drivers
loopback_xmit drivers/net/loopback.c:70-94 (skb_orphan :80, eth_type_trans :87, __netif_rx :90; ndo_start_xmit :156).
igb: igb_msix_ring igb_main.c:7153 (napi_schedule_irqoff :7160); igb_poll :8278 (igb_clean_rx_irq :8300); igb_clean_rx_irq :9016 (loop head 9035, desc size check 9049-9052, dma_rmb 9058, igb_build_skb :9100, igb_construct_skb :9103, igb_process_skb_fields :9131, napi_gro_receive :9133, refill :9045/:9151); igb_construct_skb :8612; igb_build_skb :8664; igb_alloc_rx_buffers :9205; struct igb_ring igb.h:319 (desc 329, count 335, next_to_clean 346, next_to_use 347).
mt76: mt76_dma_rx_process dma.c:974; mt76_dma_rx_poll :1073 (:1084); mt76_rx_complete mac80211.c:1514 → ieee80211_rx_list :1529/:1538 → netif_receive_skb_list :1544 or napi_gro_receive :1550.

## Qdisc + neighbour
__qdisc_run sch_generic.c:440 (quota net_hotdata.dev_tx_weight :442; qdisc_restart loop :445); qdisc_restart :418 (dequeue_skb :427, sch_direct_xmit :437); sch_direct_xmit :344; dequeue_skb :258; qdisc_run include/net/pkt_sched.h:120; noop_qdisc :712; noqueue_qdisc_ops :744; fq_codel_qdisc_ops sch_fq_codel.c:760.
neigh_resolve_output net/core/neighbour.c:1596; neigh_output include/net/neighbour.h:547 (neigh_hh_output :507 used :558); __neigh_event_send :1202 (NUD_INCOMPLETE set :1224; arp_queue tail :1265; neigh_probe :1273); neigh_probe :1084; arp_solicit net/ipv4/arp.c:333; arp_rcv :967; arp_process :702; NUD_* include/uapi/linux/neighbour.h:63+; ip_finish_output2 net/ipv4/ip_output.c:199 (ip_neigh_for_gw :230, neigh_output :236).

## Renames in 7.2
napi_skb_finish→gro_skb_finish; napi_gro_receive is an inline over gro_receive_skb; netdev_max_backlog→net_hotdata.max_backlog; tap loop iterates dev_net_rcu(skb->dev)->ptype_all + dev->ptype_all; noqueue detected by !q->enqueue.
