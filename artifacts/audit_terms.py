# term -> section id where it is introduced. Filled chapter by chapter.
TERMS = {
    # ch0
    'struct sk_buff': 'ch0', 'net_device': 'ch0', 'receive handler': 'ch0', 'network namespace': 'ch0',
    'netfilter hook': 'ch0', 'nf_hook_slow': 'ch0', 'kprobe': 'ch0', 'pwru': 'ch0', 'bpftrace': 'ch0',
    'nft monitor trace': 'ch0', 'function_graph': 'ch0',
    # ch1
    'receive ring': 'ch1', 'descriptor': 'ch1', 'DMA': 'ch1', 'page pool': 'ch1', 'hardirq': 'ch1',
    'softirq': 'ch1', 'NAPI': 'ch1', 'net_rx_action': 'ch1', 'netdev_budget': 'ch1', 'time squeeze': 'ch1',
    'GRO': 'ch1', 'gro_receive_skb': 'ch1', 'backlog': 'ch1', 'softnet_data': 'ch1', 'enqueue_to_backlog': 'ch1',
    'process_backlog': 'ch1', 'netif_rx': 'ch1', 'RSS': 'ch1', 'RPS': 'ch1',
}
TERMS.update({
    # ch2
    'XDP': 'ch2', 'xdp_buff': 'ch2', 'XDP_PASS': 'ch2', 'XDP_REDIRECT': 'ch2', 'generic XDP': 'ch2',
    'XDP_PACKET_HEADROOM': 'ch2', 'xdp_frame': 'ch2', 'devmap': 'ch2', 'cpumap': 'ch2', 'AF_XDP': 'ch2',
    'skb_pp_cow_data': 'ch2', 'do_xdp_generic': 'ch2',
    # ch3
    '__netif_receive_skb_core': 'ch3', 'packet socket': 'ch3', 'ptype_all': 'ch3', 'packet_rcv': 'ch3',
    'deliver_skb': 'ch3', 'promiscuous': 'ch3', 'PACKET_OTHERHOST': 'ch3', 'dev_queue_xmit_nit': 'ch3',
    'tc ingress': 'ch3', 'clsact': 'ch3', 'tcx': 'ch3', 'tcf_classify': 'ch3', 'TC_ACT_': 'ch3',
    'vlan_do_receive': 'ch3', 'rx_handler': 'ch3', 'RX_HANDLER_': 'ch3', 'ptype_base': 'ch3', 'pt_prev': 'ch3',
    'another_round': 'ch3',
})
TERMS.update({
    # ch4
    'skb_orphan': 'ch4', 'early demux': 'ch4', 'ip_route_input_slow': 'ch4', 'fib_lookup': 'ch4',
    'RTN_LOCAL': 'ch4', 'RTN_UNICAST': 'ch4', 'dst_entry': 'ch4', 'skb_dst': 'ch4', 'dst_input': 'ch4', 'dst_output': 'ch4',
    'fib_validate_source': 'ch4', 'ip_local_deliver': 'ch4', 'ip_protocol_deliver_rcu': 'ch4', 'ip_forward': 'ch4',
    'skb_cow': 'ch4', 'ip_error': 'ch4',
    # ch5
    'hook entry': 'ch5', 'base chain': 'ch5', 'nf_conn': 'ch5', 'reply tuple': 'ch5', 'IP_CT_NEW': 'ch5',
    'nf_confirm': 'ch5', 'unconfirmed': 'ch5', 'nf_nat_inet_fn': 'ch5', 'nf_nat_setup_info': 'ch5',
    'nf_nat_manip_pkt': 'ch5', 'nft_do_chain': 'ch5', 'nf_conntrack_in': 'ch5', 'resolve_normal_ct': 'ch5',
})
TERMS.update({
    # ch6
    'write queue': 'ch6', 'ip_queue_xmit': 'ch6', '__ip_local_out': 'ch6', 'ip_finish_output2': 'ch6',
    'neighbour entry': 'ch6', 'arp_queue': 'ch6', 'neigh_probe': 'ch6', 'arp_solicit': 'ch6',
    '__dev_queue_xmit': 'ch6', 'netdev_core_pick_tx': 'ch6', 'queueing discipline': 'ch6', 'qdisc': 'ch6',
    'noqueue': 'ch6', '__qdisc_run': 'ch6', 'sch_direct_xmit': 'ch6', 'GSO': 'ch6', 'TSO': 'ch6',
    'ndo_start_xmit': 'ch0', 'transmit completion': 'ch6',
    # ch7
    'struct socket': 'ch7', 'struct sock': 'ch7', 'sockfs': 'ch7', 'socket_file_ops': 'ch7', 'private_data': 'ch7',
    'sock_recvmsg': 'ch7', 'inet_recvmsg': 'ch7', 'tcp_recvmsg': 'ch7', 'request socket': 'ch7', 'accept queue': 'ch7',
    'sk_receive_queue': 'ch7', 'out_of_order_queue': 'ch7', 'socket backlog': 'ch7', 'sk_backlog': 'ch7',
    'sock_owned_by_user': 'ch7', 'sk_rcvbuf': 'ch7', 'sk_rmem_alloc': 'ch7', 'truesize': 'ch7',
    'sk_data_ready': 'ch7', 'sock_def_readable': 'ch7', 'sock_rfree': 'ch7', 'tcp_add_backlog': 'ch7',
})
TERMS.update({
    # ch8
    'loopback_xmit': 'ch8', 'skb_dst_force': 'ch8', 'skb_valid_dst': 'ch8',
    'PACKET_OUTGOING': 'ch8', 'PACKET_LOOPBACK': 'ch8', 'dev_loopback_xmit': 'ch8',
    'ip_route_output_key_hash_rcu': 'ch8',
    'unix_stream_read_generic': 'ch8', 'abstract socket': 'ch8', 'SCM_RIGHTS': 'ch8',
    'SOCK_SEQPACKET': 'ch8', 'unix_find_other': 'ch8', 'UNIXCB': 'ch8',
})
TERMS.update({
    # introduced earlier than the chapter that expands them
    'RTCF_LOCAL': 'ch4', 'rt_dst_alloc': 'ch4',
    'unix_stream_sendmsg': 'ch0', 'unix_dgram_sendmsg': 'ch0', 'sock_alloc_send_pskb': 'ch0',
})
TERMS.update({
    # ch9
    'veth_forward_skb': 'ch9', 'veth_skb_is_eligible_for_gro': 'ch9',
    'veth_xdp_rx': 'ch9',
    '____dev_forward_skb': 'ch9', '__is_skb_forwardable': 'ch9', 'skb_scrub_packet': 'ch9',
    'xnet': 'ch9', 'veth_xdp_set': 'ch9', 'NETIF_F_ALL_TSO': 'ch9', 'nf_reset_ct': 'ch9',
})
TERMS.update({
    # named earlier than the chapter that expands them
    'veth_xmit': 'ch0', '__dev_forward_skb': 'ch0', 'veth_xdp_rcv_skb': 'ch2',
})
TERMS.update({
    # ch10
    'br_handle_frame': 'ch10', 'br_handle_frame_finish': 'ch10', 'forwarding database': 'ch10',
    'br_fdb_find_rcu': 'ch10', 'br_fdb_update': 'ch10', 'br_forward': 'ch10', '__br_forward': 'ch10',
    'br_flood': 'ch10', 'deliver_clone': 'ch10', 'br_dev_queue_push_xmit': 'ch10',
    'br_pass_frame_up': 'ch10', 'NF_BR_': 'ch10', 'br_netfilter': 'ch10',
    'br_nf_pre_routing': 'ch10', 'br_nf_forward_ip': 'ch10', 'br_nf_post_routing': 'ch10',
    'bridge-nf-call-iptables': 'ch10', 'ip_sabotage_in': 'ch10', 'DOCKER-USER': 'ch10',
    'nf_hook_bridge_pre': 'ch10', 'NF_STOLEN': 'ch10',
})
TERMS.update({
    # named earlier than the chapter that expands them
    'br_handle_frame': 'ch3', 'br_netfilter': 'ch3',
})
TERMS.update({
    # ch11
    'bond_handle_frame': 'ch11', 'recv_probe': 'ch11', 'bond_should_deliver_exact_match': 'ch11',
    'bond_start_xmit': 'ch11', '__bond_start_xmit': 'ch11', 'bond_dev_queue_xmit': 'ch11',
    'bond_xmit_hash': 'ch11', 'transmit hash policy': 'ch11', 'l3mdev': 'ch11',
    'l3mdev_ip_rcv': 'ch11', 'vrf_ip_rcv': 'ch11', 'vrf_l3_rcv': 'ch11', 'IPSKB_L3SLAVE': 'ch11',
    'vrf_rcv_nfhook': 'ch11', 'vrf_l3_out': 'ch11', 'vrf_ip_out_direct': 'ch11',
    'vrf_fib_table': 'ch11', 'tcp_l3mdev_accept': 'ch11', 'SO_BINDTODEVICE': 'ch11',
    'RX_HANDLER_EXACT': 'ch11', 'ip vrf exec': 'ch11',
})
TERMS.update({
    # named earlier than the chapter that expands them
    'bond_handle_frame': 'ch3', 'RX_HANDLER_EXACT': 'ch3',
    'l3mdev': 'ch4', 'l3mdev_ip_rcv': 'ch4',
})
TERMS.update({
    # ch12
    'lower device': 'ch12', 'macvlan_handle_frame': 'ch12', 'macvlan_hash_lookup': 'ch12',
    'macvlan_forward_source': 'ch12', 'macvlan_start_xmit': 'ch12', 'promiscuity': 'ch12',
    'ipvlan_handle_frame': 'ch12', 'ipvlan_addr_lookup': 'ch12', 'ipvlan_get_L3_hdr': 'ch12',
    'ipvlan_process_v4_outbound': 'ch12', 'ipvlan_nf_input': 'ch12',
    'ipvlan_skb_crossing_ns': 'ch12', 'netdev_rx_handler_register': 'ch12',
    'passthru': 'ch12', 'vepa': 'ch12', 'l3s': 'ch12',
})
TERMS.update({'netdev_rx_handler_register': 'ch3'})
TERMS.update({
    # ch13
    'virtual service': 'ch13', 'real server': 'ch13',
    'ip_vs_in_hook': 'ch13', 'ip_vs_out_hook': 'ch13', 'ip_vs_ops4': 'ch13',
    'the director': 'ch13',
    'ip_vs_schedule': 'ch13', 'ip_vs_conn': 'ch13', 'packet_xmit': 'ch13',
    'ip_vs_nat_xmit': 'ch13', 'ip_vs_nat_send_or_cont': 'ch13', 'ip_vs_notrack': 'ch13',
    'handle_response': 'ch13', 'ip_vs_dr_xmit': 'ch13', 'ip_vs_tunnel_xmit': 'ch13',
    'kube-ipvs0': 'ch13', 'ip_vs_conn_new': 'ch13',
})
TERMS.update({
    # ch14
    'cil_from_container': 'ch14', 'ipcache': 'ch14', 'security identity': 'ch14',
    'policy_can_egress4': 'ch14', 'ipv4_local_delivery': 'ch14', 'redirect_ep': 'ch14',
    'ctx_redirect_peer': 'ch14', 'bpf_redirect_peer': 'ch14', 'skb_do_redirect': 'ch14',
    'ndo_get_peer_dev': 'ch14', 'cilium_host': 'ch14', 'cilium_net': 'ch14',
    'cil_from_host': 'ch14', 'cil_to_host': 'ch14', 'endpoint routes': 'ch14',
    'cil_to_container': 'ch14', 'SKB_DROP_REASON_TC_INGRESS': 'ch14',
    'handle_ipv4_from_lxc': 'ch14', 'ipv4_forward_to_destination': 'ch14',
})
TERMS.update({
    # ch15
    'encap_and_redirect_lxc': 'ch15', 'ctx_set_encap_info4': 'ch15', 'tunnel key': 'ch15',
    'tunnel identifier': 'ch15', 'cilium_geneve': 'ch15', 'cil_to_overlay': 'ch15',
    'cil_from_overlay': 'ch15', 'outer packet': 'ch15',
    'geneve_udp_encap_recv': 'ch15', 'gro_cells_receive': 'ch15', 'cil_from_netdev': 'ch15',
    'cil_to_netdev': 'ch15', 'fib_redirect_v4': 'ch15', 'pass_to_stack': 'ch15',
    'handle_nat_fwd': 'ch15', 'snat_v4_nat': 'ch15', 'iptunnel_xmit': 'ch15',
    'geneve_xmit': 'ch15', 'BPF masquerade': 'ch15',
})
TERMS.update({
    # ch16
    'flowtable': 'ch16', 'netkit': 'ch16', 'BIG TCP': 'ch16', 'NF_INET_INGRESS': 'ch16',
    'nf_flow_offload_ip_hook': 'ch16', 'netkit_xmit': 'ch16', 'gso_ipv4_max_size': 'ch16',
})
