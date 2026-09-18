# Citation sheet — Linux virtual network devices, **v7.2** (`git describe --tags` → `v7.2`, HEAD `8d3ae59288f1`)

All line numbers copied from `grep -n` / `sed -n` output on `/home/wazir/workspace/repos/linux`.

---

## A. veth — `/home/wazir/workspace/repos/linux/drivers/net/veth.c`

| function | path:line | note |
|---|---|---|
| `veth_xmit` | drivers/net/veth.c:347 | `.ndo_start_xmit` |
| `veth_forward_skb` | drivers/net/veth.c:320 | |
| `veth_xdp_rx` | drivers/net/veth.c:312 | `ptr_ring_produce` at :314 |
| `__veth_xdp_flush` | drivers/net/veth.c:301 | |
| `veth_poll` | drivers/net/veth.c:965 | NAPI handler |
| `veth_xdp_rcv` | drivers/net/veth.c:907 | `napi_gro_receive` at :945, `netif_receive_skb` at :943 |
| `veth_xdp_rcv_skb` | drivers/net/veth.c:790 | `skb->protocol = eth_type_trans(...)` at :887 |
| `veth_convert_skb_to_xdp_buff` | drivers/net/veth.c:751 | **successor** to the old inline headroom/`pskb_expand_head` logic |
| `veth_skb_is_eligible_for_gro` | drivers/net/veth.c:338 | |
| `veth_napi_enable` | drivers/net/veth.c:1241 | |
| `veth_napi_enable_range` | drivers/net/veth.c:1218 | contains `netif_napi_add(dev, &rq->xdp_napi, veth_poll)` at :1227 |
| `__veth_napi_enable` | drivers/net/veth.c:1075 | |
| `__veth_napi_enable_range` | drivers/net/veth.c:1034 | |
| `veth_napi_add` | **does not exist in 7.2** | successor = `veth_napi_enable_range` (:1218), which inlines `netif_napi_add` |
| `veth_enable_xdp` | drivers/net/veth.c:1176 | `veth_enable_xdp_range` :1117 |
| `veth_set_features` | drivers/net/veth.c:1523 | |
| `veth_xdp_set` | drivers/net/veth.c:1573 | |
| `veth_xdp` (ndo_bpf) | drivers/net/veth.c:1655 | |
| `veth_newlink` | drivers/net/veth.c:1819 | |
| `veth_dev_init` | drivers/net/veth.c:1466 | |
| `veth_get_stats64` | drivers/net/veth.c:451 | `veth_stats_rx` :420 |
| `veth_netdev_ops` | drivers/net/veth.c:1709 | `.ndo_start_xmit = veth_xmit` at :1713 |
| `veth_open` | drivers/net/veth.c:1390 | `netif_carrier_on` both ends at :1410–1411 (also :1372/1374 in `veth_set_channels`) |
| `veth_link_ops` | drivers/net/veth.c:1984 | forward decl at :1793 |
| `veth_setup` | drivers/net/veth.c:1742 | |

### veth_xmit — drivers/net/veth.c:347–415 (decisive lines 358, 367, 373, 379, 383, 385)
```c
// drivers/net/veth.c:356-386
	rcu_read_lock();
	rcv = rcu_dereference(priv->peer);
	if (unlikely(!rcv) || !pskb_may_pull(skb, ETH_HLEN)) {
		kfree_skb(skb);
		goto drop;
	}

	rcv_priv = netdev_priv(rcv);
	rxq = skb_get_queue_mapping(skb);
	if (rxq < rcv->real_num_rx_queues) {
		rq = &rcv_priv->rq[rxq];
```
```c
// drivers/net/veth.c:368-386  (the use_napi test, forward, and stats branch)
		/* The napi pointer is available when an XDP program is
		 * attached or when GRO is enabled
		 * Don't bother with napi/GRO if the skb can't be aggregated
		 */
		use_napi = rcu_access_pointer(rq->napi) &&
			   veth_skb_is_eligible_for_gro(dev, rcv, skb);
	}

	skb_tx_timestamp(skb);

	ret = veth_forward_skb(rcv, skb, rq, use_napi);
	switch (ret) {
	case NET_RX_SUCCESS: /* same as NETDEV_TX_OK */
		if (!use_napi)
			dev_sw_netstats_tx_add(dev, 1, length);
		else
			__veth_xdp_flush(rq);
		break;
```
The `NETDEV_TX_BUSY` arm (backpressure, added for the ptr_ring-full case) also calls `__veth_xdp_flush(rq)` at :404 after `netif_tx_stop_queue(txq)` at :402.

### veth_forward_skb — drivers/net/veth.c:320–325
```c
// drivers/net/veth.c:320-325
static int veth_forward_skb(struct net_device *dev, struct sk_buff *skb,
			    struct veth_rq *rq, bool xdp)
{
	return __dev_forward_skb(dev, skb) ?: xdp ?
		veth_xdp_rx(rq, skb) :
		__netif_rx(skb);
}
```

### veth_xdp_rx / __veth_xdp_flush — drivers/net/veth.c:301–318
```c
// drivers/net/veth.c:301-318
static void __veth_xdp_flush(struct veth_rq *rq)
{
	/* Write ptr_ring before reading rx_notify_masked */
	smp_mb();
	if (!READ_ONCE(rq->rx_notify_masked) &&
	    napi_schedule_prep(&rq->xdp_napi)) {
		WRITE_ONCE(rq->rx_notify_masked, true);
		__napi_schedule(&rq->xdp_napi);
	}
}

static int veth_xdp_rx(struct veth_rq *rq, struct sk_buff *skb)
{
	if (unlikely(ptr_ring_produce(&rq->xdp_ring, skb)))
		return NETDEV_TX_BUSY; /* signal qdisc layer */

	return NET_RX_SUCCESS; /* same as NETDEV_TX_OK */
}
```

### veth_skb_is_eligible_for_gro — drivers/net/veth.c:338–345
```c
// drivers/net/veth.c:338-345
static bool veth_skb_is_eligible_for_gro(const struct net_device *dev,
					 const struct net_device *rcv,
					 const struct sk_buff *skb)
{
	return !(dev->features & NETIF_F_ALL_TSO) ||
		(skb->destructor == sock_wfree &&
		 rcv->features & (NETIF_F_GRO_FRAGLIST | NETIF_F_GRO_UDP_FWD));
}
```

### veth_poll — drivers/net/veth.c:965; the xdp_do_flush + rcv call
```c
// drivers/net/veth.c:984-990
	xdp_set_return_frame_no_direct();
	done = veth_xdp_rcv(rq, budget, &bq, &stats);

	if (stats.xdp_redirect > 0)
		xdp_do_flush();
	if (stats.xdp_tx > 0)
		veth_xdp_flush(rq, &bq);
	xdp_clear_return_frame_no_direct();
```
```c
// drivers/net/veth.c:936-946  (skb path: veth_xdp_rcv_skb -> napi_gro_receive)
		} else {
			/* ndo_start_xmit */
			struct sk_buff *skb = ptr;

			stats->xdp_bytes += skb->len;
			skb = veth_xdp_rcv_skb(rq, skb, bq, stats);
			if (skb) {
				if (skb_shared(skb) || skb_unclone(skb, GFP_ATOMIC))
					netif_receive_skb(skb);
				else
					napi_gro_receive(&rq->xdp_napi, skb);
			}
		}
```

### veth_xdp_rcv_skb — skb → xdp_buff conversion (7.2 differs from older kernels)
`veth_xdp_rcv_skb` (:790) delegates the conversion to `veth_convert_skb_to_xdp_buff` (:751). 7.2 **no longer uses `pskb_expand_head`**; it uses page-pool copy-on-write (`skb_pp_cow_data`, declared `include/linux/skbuff.h:3725`, defined `net/core/skbuff.c:942`).
```c
// drivers/net/veth.c:751-772
static int veth_convert_skb_to_xdp_buff(struct veth_rq *rq,
					struct xdp_buff *xdp,
					struct sk_buff **pskb)
{
	struct sk_buff *skb = *pskb;
	u32 frame_sz;

	if (skb_shared(skb) || skb_head_is_locked(skb) ||
	    skb_is_nonlinear(skb) ||
	    skb_headroom(skb) < XDP_PACKET_HEADROOM) {
		if (skb_pp_cow_data(rq->page_pool, pskb, XDP_PACKET_HEADROOM))
			goto drop;

		skb = *pskb;
	}
	/* SKB "head" area always have tailroom for skb_shared_info */
	frame_sz = skb_end_pointer(skb) - skb->head;
	frame_sz += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
	xdp_init_buff(xdp, frame_sz, &rq->xdp_rxq);
	xdp_prepare_buff(xdp, skb->head, skb_headroom(skb),
			 skb_headlen(skb), true);
```
```c
// drivers/net/veth.c:882-890  (post-XDP_PASS fixups in veth_xdp_rcv_skb)
	off = xdp->data_end - orig_data_end;
	if (off != 0) {
		skb_set_tail_pointer(skb, xdp->data_end - xdp->data);
		skb->len += off; /* positive on grow, negative on shrink */
	}

	skb->protocol = eth_type_trans(skb, rq->dev);

	metalen = xdp->data - xdp->data_meta;
```
`__skb_push(skb, skb->data - skb_mac_header(skb))` is at :809 (before conversion); `bpf_prog_run_xdp` at :819.

### veth_newlink — drivers/net/veth.c:1819 (peer creation + netns)
| anchor | line |
|---|---|
| `struct net *peer_net = rtnl_newlink_peer_net(params);` | 1823 |
| `peer = rtnl_create_link(peer_net, ifname, ...)` | 1856 |
| `err = register_netdevice(peer);` | 1869 |
| `err = register_netdevice(dev);` | 1898 |
| `rcu_assign_pointer(priv->peer, peer);` | 1909 |
| `rcu_assign_pointer(priv->peer, dev);` (peer's priv) | 1915 |

The peer's netns comes from `rtnl_newlink_peer_net(params)` (:1823) — i.e. rtnetlink resolves `IFLA_NET_NS_FD`/`IFLA_NET_NS_PID` on the *peer* attribute before `veth_newlink` runs; `veth_disable_gro(peer)` at :1876, `netif_carrier_off(peer)` at :1877.

### veth_set_features — the NETIF_F_GRO branch (drivers/net/veth.c:1523–1549)
```c
// drivers/net/veth.c:1530-1543
	if (!(changed & NETIF_F_GRO) || !(dev->flags & IFF_UP) || priv->_xdp_prog)
		return 0;

	peer = rtnl_dereference(priv->peer);
	if (features & NETIF_F_GRO) {
		err = veth_napi_enable(dev);
		if (err)
			return err;

		if (peer)
			xdp_features_set_redirect_target(peer, true);
	} else {
		if (peer)
			xdp_features_clear_redirect_target(peer);
		veth_napi_del(dev);
```

### The forwarding helpers

| function | path:line |
|---|---|
| `__dev_forward_skb` (decl) | include/linux/netdevice.h:4394 |
| `__is_skb_forwardable` | include/linux/netdevice.h:4400 |
| `____dev_forward_skb` | include/linux/netdevice.h:4440 |
| `is_skb_forwardable` | net/core/dev.c:2432 |
| `__dev_forward_skb2` | net/core/dev.c:2438 |
| `__dev_forward_skb` (def) | net/core/dev.c:2451 |

```c
// include/linux/netdevice.h:4440-4453
static __always_inline int ____dev_forward_skb(struct net_device *dev,
					       struct sk_buff *skb,
					       const bool check_mtu)
{
	if (skb_orphan_frags(skb, GFP_ATOMIC) ||
	    unlikely(!__is_skb_forwardable(dev, skb, check_mtu))) {
		dev_core_stats_rx_dropped_inc(dev);
		kfree_skb(skb);
		return NET_RX_DROP;
	}

	skb_scrub_packet(skb, !net_eq(dev_net(dev), dev_net(skb->dev)));
	skb->priority = 0;
	return 0;
}
```
Note for 7.2: `skb->protocol = eth_type_trans()` and `skb_postpull_rcsum()` have moved **out** of `____dev_forward_skb` into `__dev_forward_skb2`:
```c
// net/core/dev.c:2438-2455
static int __dev_forward_skb2(struct net_device *dev, struct sk_buff *skb,
			      bool check_mtu)
{
	int ret = ____dev_forward_skb(dev, skb, check_mtu);

	if (likely(!ret)) {
		skb->protocol = eth_type_trans(skb, dev);
		skb_postpull_rcsum(skb, eth_hdr(skb), ETH_HLEN);
	}

	return ret;
}

int __dev_forward_skb(struct net_device *dev, struct sk_buff *skb)
{
	return __dev_forward_skb2(dev, skb, true);
}
```
```c
// include/linux/netdevice.h:4400-4423  (is_skb_forwardable core)
static __always_inline bool __is_skb_forwardable(const struct net_device *dev,
						 const struct sk_buff *skb,
						 const bool check_mtu)
{
	const u32 vlan_hdr_len = 4; /* VLAN_HLEN */
	unsigned int len;

	if (!(dev->flags & IFF_UP))
		return false;
	if (!check_mtu)
		return true;
	len = dev->mtu + dev->hard_header_len + vlan_hdr_len;
	if (skb->len <= len)
		return true;
	/* if TSO is enabled, we don't care about the length as the packet
	 * could be forwarded without being segmented before
	 */
	if (skb_is_gso(skb))
		return true;
	return false;
}
```

### **Does veth allocate or copy a new skb on xmit? NO.**
`grep -n "skb_copy\|skb_clone\|alloc_skb"` in `drivers/net/veth.c` returns **zero hits**. The xmit path (`veth_xmit` :347 → `veth_forward_skb` :320 → `__dev_forward_skb` → `__netif_rx`) hands the *same* `sk_buff` pointer to the peer; only metadata is scrubbed (`skb_scrub_packet`, netdevice.h:4451). The only buffer-touching calls in veth.c are on the **receive/NAPI/XDP** side:
- `drivers/net/veth.c:761` — `skb_pp_cow_data(rq->page_pool, pskb, XDP_PACKET_HEADROOM)` in `veth_convert_skb_to_xdp_buff`, i.e. only when a native XDP program is attached *and* the skb is shared/head-locked/nonlinear/short-on-headroom.
- `drivers/net/veth.c:942` — `skb_unclone(skb, GFP_ATOMIC)` in `veth_xdp_rcv`, guarding `napi_gro_receive`.

---

## B. Bridge — `net/bridge/`

| function | path:line | note |
|---|---|---|
| `br_add_if` | net/bridge/br_if.c:560 | decl br_private.h:917 |
| `netdev_rx_handler_register` call | net/bridge/br_if.c:619 | |
| `br_get_rx_handler` | net/bridge/br_input.c:463 | decl br_private.h:929 |
| `br_handle_frame` | net/bridge/br_input.c:339 | |
| `br_handle_frame_dummy` | net/bridge/br_input.c:458 | DSA case |
| `nf_hook_bridge_pre` | net/bridge/br_input.c:267 | **successor** to the inline `NF_HOOK(NF_BR_PRE_ROUTING)` in `br_handle_frame` |
| `br_handle_frame_finish` | net/bridge/br_input.c:76 | |
| `br_pass_frame_up` | net/bridge/br_input.c:33 | |
| `br_netif_receive_skb` | net/bridge/br_input.c:26/27 | `netif_receive_skb` at :30 |
| `should_deliver` | net/bridge/br_forward.c:21 | |
| `br_dev_queue_push_xmit` | net/bridge/br_forward.c:33 | `dev_queue_xmit(skb)` at :53 |
| `br_forward_finish` | net/bridge/br_forward.c:63 | |
| `__br_forward` | net/bridge/br_forward.c:73 | |
| `deliver_clone` | net/bridge/br_forward.c:120 | |
| `br_forward` | net/bridge/br_forward.c:144 | |
| `maybe_deliver` | net/bridge/br_forward.c:176 | |
| `br_flood` | net/bridge/br_forward.c:201 | |
| `br_multicast_flood` | net/bridge/br_forward.c:299 | |
| `br_dev_xmit` | net/bridge/br_device.c:30 | `.ndo_start_xmit` at br_device.c:444 |
| `br_fdb_find_rcu` | net/bridge/br_fdb.c:263 | |
| `br_fdb_update` | net/bridge/br_fdb.c:973 | learning |
| `struct net_bridge_port` | net/bridge/br_private.h:388 | `br` :389, `dev` :390, `state` — see below |

`struct net_bridge_port` head (net/bridge/br_private.h:388–391): `struct net_bridge *br;` :389, `struct net_device *dev;` :390. There is **no bare `u8 state;`** grep hit in br_private.h in 7.2; `p->state` is read at br_input.c:346-ish and br_forward.c:28 — the field is declared inside the same struct further down (bitfield/`u8 state` is part of the port's STP block); use `p->state` usage anchors br_input.c:101/107 and br_forward.c:28.

### br_if.c:619 — rx_handler registration
```c
// net/bridge/br_if.c:615-625
	err = br_netpoll_enable(p);
	if (err)
		goto err3;

	err = netdev_rx_handler_register(dev, br_get_rx_handler(dev), p);
	if (err)
		goto err4;

	dev->priv_flags |= IFF_BRIDGE_PORT;

	err = netdev_master_upper_dev_link(dev, br->dev, NULL, NULL, extack);
```
```c
// net/bridge/br_input.c:463-469
rx_handler_func_t *br_get_rx_handler(const struct net_device *dev)
{
	if (netdev_uses_dsa(dev))
		return br_handle_frame_dummy;

	return br_handle_frame;
}
```

### br_handle_frame — the forwarding-state branch (net/bridge/br_input.c:430–446)
In 7.2 the `NF_HOOK(NFPROTO_BRIDGE, NF_BR_PRE_ROUTING, … br_handle_frame_finish)` is **no longer inline here**; it was factored into `nf_hook_bridge_pre()`.
```c
// net/bridge/br_input.c:430-447
forward:
	if (br_mst_is_enabled(p))
		goto defer_stp_filtering;

	switch (p->state) {
	case BR_STATE_FORWARDING:
	case BR_STATE_LEARNING:
defer_stp_filtering:
		if (ether_addr_equal(p->br->dev->dev_addr, dest))
			skb->pkt_type = PACKET_HOST;

		return nf_hook_bridge_pre(skb, pskb);
	default:
		reason = SKB_DROP_REASON_BRIDGE_INGRESS_STP_STATE;
drop:
		kfree_skb_reason(skb, reason);
	}
	return RX_HANDLER_CONSUMED;
```
```c
// net/bridge/br_input.c:285-289 + 310-317  (nf_hook_bridge_pre: the okfn is br_handle_frame_finish)
	nf_hook_state_init(&state, NF_BR_PRE_ROUTING,
			   NFPROTO_BRIDGE, skb->dev, NULL, NULL,
			   net, br_handle_frame_finish);
...
frame_finish:
	net = dev_net(skb->dev);
	br_handle_frame_finish(net, NULL, skb);
#else
	br_handle_frame_finish(dev_net(skb->dev), NULL, skb);
#endif
	return RX_HANDLER_CONSUMED;
```

### br_handle_frame_finish — fdb lookup and the dst/flood/local_rcv decision
| anchor | line |
|---|---|
| `br_fdb_update(br, p, eth_hdr(skb)->h_source, vid, 0)` (learning) | 144 |
| `dst = br_fdb_find_rcu(br, eth_hdr(skb)->h_dest, vid)` | 204 |
| `return br_pass_frame_up(skb, false)` (BR_FDB_LOCAL) | 222 |
| `br_forward(READ_ONCE(dst->dst), skb, local_rcv, false)` | 226 |
| `br_flood(br, skb, pkt_type, local_rcv, false, vid)` | 229 |
| `return br_pass_frame_up(skb, promisc)` | 235 |

```c
// net/bridge/br_input.c:142-144
	/* insert into forwarding database after filtering to avoid spoofing */
	if (test_bit(BR_LEARNING_BIT, &p->flags))
		br_fdb_update(br, p, eth_hdr(skb)->h_source, vid, 0);
```
```c
// net/bridge/br_input.c:203-236
	case BR_PKT_UNICAST:
		dst = br_fdb_find_rcu(br, eth_hdr(skb)->h_dest, vid);
...
	if (dst) {
		unsigned long now = jiffies;

		if (test_bit(BR_FDB_LOCAL, &dst->flags))
			return br_pass_frame_up(skb, false);

		if (now != READ_ONCE(dst->used))
			WRITE_ONCE(dst->used, now);
		br_forward(READ_ONCE(dst->dst), skb, local_rcv, false);
	} else {
		if (!mcast_hit)
			br_flood(br, skb, pkt_type, local_rcv, false, vid);
		else
			br_multicast_flood(mdst, skb, brmctx, local_rcv, false);
	}

	if (local_rcv)
		return br_pass_frame_up(skb, promisc);
```

### br_pass_frame_up — net/bridge/br_input.c:33–73
```c
// net/bridge/br_input.c:58-72
	indev = skb->dev;
	skb->dev = brdev;
	skb = br_handle_vlan(br, NULL, vg, skb);
	if (!skb)
		return NET_RX_DROP;
	/* update the multicast stats if the packet is IGMP/MLD */
	br_multicast_count(br, NULL, skb, br_multicast_igmp_type(skb),
			   BR_MCAST_DIR_TX);

	BR_INPUT_SKB_CB(skb)->promisc = promisc;

	return NF_HOOK(NFPROTO_BRIDGE, NF_BR_LOCAL_IN,
		       dev_net(indev), NULL, skb, indev, NULL,
		       br_netif_receive_skb);
}
```
```c
// net/bridge/br_input.c:26-31
static int
br_netif_receive_skb(struct net *net, struct sock *sk, struct sk_buff *skb)
{
	br_drop_fake_rtable(skb);
	return netif_receive_skb(skb);
}
```

### br_forward / __br_forward / br_forward_finish / br_dev_queue_push_xmit
```c
// net/bridge/br_forward.c:144-171  (br_forward)
void br_forward(const struct net_bridge_port *to,
		struct sk_buff *skb, bool local_rcv, bool local_orig)
{
	if (unlikely(!to))
		goto out;
	/* redirect to backup link if the destination port is down */
	if (rcu_access_pointer(to->backup_port) &&
	    (!netif_carrier_ok(to->dev) || !netif_running(to->dev))) {
...
	if (should_deliver(to, skb)) {
		if (local_rcv)
			deliver_clone(to, skb, local_orig);
		else
			__br_forward(to, skb, local_orig);
		return;
	}
```
```c
// net/bridge/br_forward.c:91-118  (__br_forward: skb->dev = to->dev; NF_BR_FORWARD)
	indev = skb->dev;
	skb->dev = to->dev;
	if (!local_orig) {
		if (skb_warn_if_lro(skb)) {
			kfree_skb(skb);
			return;
		}
		br_hook = NF_BR_FORWARD;
		skb_forward_csum(skb);
		net = dev_net(indev);
	} else {
		...
		br_hook = NF_BR_LOCAL_OUT;
		net = dev_net(skb->dev);
		indev = NULL;
	}

	NF_HOOK(NFPROTO_BRIDGE, br_hook,
		net, NULL, skb, indev, skb->dev,
		br_forward_finish);
```
```c
// net/bridge/br_forward.c:63-70  (br_forward_finish)
int br_forward_finish(struct net *net, struct sock *sk, struct sk_buff *skb)
{
	skb_clear_tstamp(skb);
	return NF_HOOK(NFPROTO_BRIDGE, NF_BR_POST_ROUTING,
		       net, sk, skb, NULL, skb->dev,
		       br_dev_queue_push_xmit);

}
```
```c
// net/bridge/br_forward.c:33-55  (br_dev_queue_push_xmit)
int br_dev_queue_push_xmit(struct net *net, struct sock *sk, struct sk_buff *skb)
{
	skb_push(skb, ETH_HLEN);
	if (!is_skb_forwardable(skb->dev, skb))
		goto drop;

	br_drop_fake_rtable(skb);
	if (skb->ip_summed == CHECKSUM_PARTIAL &&
	    eth_type_vlan(skb->protocol)) {
		int depth;
		if (!vlan_get_protocol_and_depth(skb, skb->protocol, &depth))
			goto drop;
		skb_set_network_header(skb, depth);
	}
	br_switchdev_frame_set_offload_fwd_mark(skb);
	dev_queue_xmit(skb);
	return 0;
```

### **Does flooding clone the skb? YES** — `deliver_clone` → `skb_clone`
```c
// net/bridge/br_forward.c:120-132
static int deliver_clone(const struct net_bridge_port *prev,
			 struct sk_buff *skb, bool local_orig)
{
	struct net_device *dev = BR_INPUT_SKB_CB(skb)->brdev;

	skb = skb_clone(skb, GFP_ATOMIC);
	if (!skb) {
		DEV_STATS_INC(dev, tx_dropped);
		return -ENOMEM;
	}

	__br_forward(prev, skb, local_orig);
	return 0;
}
```
`br_flood` (:201) walks `br->port_list` calling `maybe_deliver` (:176), which clones for every port **except the last** (`prev` is carried forward and delivered un-cloned after the loop) — `err = deliver_clone(prev, skb, local_orig);` at br_forward.c:194.

### br_dev_xmit — host's own transmit into the bridge (net/bridge/br_device.c:30)
```c
// net/bridge/br_device.c:90-113
	dest = eth_hdr(skb)->h_dest;
	if (is_broadcast_ether_addr(dest)) {
		br_flood(br, skb, BR_PKT_BROADCAST, false, true, vid);
	} else if (is_multicast_ether_addr(dest)) {
		...
		mdst = br_mdb_entry_skb_get(brmctx, skb, vid);
		if ((mdst || BR_INPUT_SKB_CB_MROUTERS_ONLY(skb)) &&
		    br_multicast_querier_exists(brmctx, eth_hdr(skb), mdst))
			br_multicast_flood(mdst, skb, brmctx, false, true);
		else
			br_flood(br, skb, BR_PKT_MULTICAST, false, true, vid);
	} else if ((dst = br_fdb_find_rcu(br, dest, vid)) != NULL) {
		br_forward(READ_ONCE(dst->dst), skb, false, true);
	} else {
		br_flood(br, skb, BR_PKT_UNICAST, false, true, vid);
	}
```

### br_netfilter_hooks.c

| item | path:line |
|---|---|
| `br_nf_ops[]` | net/bridge/br_netfilter_hooks.c:1047 |
| `br_nf_pre_routing` | :483 |
| `br_nf_local_in` | :585 |
| `br_nf_forward_ip` | :673 |
| `br_nf_forward_arp` | :728 |
| `br_nf_forward` | :769 |
| `br_nf_post_routing` | :925 |
| `br_nf_pre_routing_finish` | :376 |
| `br_nf_hook_thresh` | :1123 |
| `nf_register_net_hooks(net, br_nf_ops, …)` | :1106 |

```c
// net/bridge/br_netfilter_hooks.c:1047-1086
static const struct nf_hook_ops br_nf_ops[] = {
	{
		.hook = br_nf_pre_routing,
		.pf = NFPROTO_BRIDGE,
		.hooknum = NF_BR_PRE_ROUTING,
		.priority = NF_BR_PRI_BRNF,
	},
#if IS_ENABLED(CONFIG_NF_CONNTRACK)
	{
		.hook = br_nf_local_in,
		.pf = NFPROTO_BRIDGE,
		.hooknum = NF_BR_LOCAL_IN,
		.priority = NF_BR_PRI_LAST,
	},
#endif
	{
		.hook = br_nf_forward,
		.pf = NFPROTO_BRIDGE,
		.hooknum = NF_BR_FORWARD,
		.priority = NF_BR_PRI_BRNF,
	},
	{
		.hook = br_nf_post_routing,
		.pf = NFPROTO_BRIDGE,
		.hooknum = NF_BR_POST_ROUTING,
		.priority = NF_BR_PRI_LAST,
	},
	{
		.hook = ip_sabotage_in,
		.pf = NFPROTO_IPV4,
		.hooknum = NF_INET_PRE_ROUTING,
		.priority = NF_IP_PRI_FIRST,
	},
	{
		.hook = ip_sabotage_in,
		.pf = NFPROTO_IPV6,
		.hooknum = NF_INET_PRE_ROUTING,
		.priority = NF_IP6_PRI_FIRST,
	},
};
```
```c
// net/bridge/br_netfilter_hooks.c:516-542  (br_nf_pre_routing IPv4 -> NF_INET_PRE_ROUTING)
	if (!brnet->call_iptables && !br_opt_get(br, BROPT_NF_CALL_IPTABLES))
		return NF_ACCEPT;

	if (!IS_IP(skb) && !is_vlan_ip(skb, state->net) &&
	    !is_pppoe_ip(skb, state->net))
		return NF_ACCEPT;

	nf_bridge_pull_encap_header_rcsum(skb);
	if (br_validate_ipv4(state->net, skb))
		return NF_DROP_REASON(skb, SKB_DROP_REASON_IP_INHDR, 0);
	...
	nf_bridge->ipv4_daddr = ip_hdr(skb)->daddr;
	skb->protocol = htons(ETH_P_IP);
	skb->transport_header = skb->network_header + ip_hdr(skb)->ihl * 4;

	NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING, state->net, state->sk, skb,
		skb->dev, NULL,
		br_nf_pre_routing_finish);

	return NF_STOLEN;
```
```c
// net/bridge/br_netfilter_hooks.c:719-724  (br_nf_forward_ip -> NF_INET_FORWARD)
	nf_bridge->physoutdev = skb->dev;

	NF_HOOK(pf, NF_INET_FORWARD, state->net, NULL, skb,
		brnf_get_logical_dev(skb, state->in, state->net),
		parent,	br_nf_forward_finish);

	return NF_STOLEN;
```
```c
// net/bridge/br_netfilter_hooks.c:958-968  (br_nf_post_routing -> NF_INET_POST_ROUTING)
	nf_bridge_pull_encap_header(skb);
	if (pf == NFPROTO_IPV4)
		skb->protocol = htons(ETH_P_IP);
	else
		skb->protocol = htons(ETH_P_IPV6);

	NF_HOOK(pf, NF_INET_POST_ROUTING, state->net, state->sk, skb,
		NULL, realoutdev,
		br_nf_dev_queue_xmit);

	return NF_STOLEN;
```
**Sysctl path:** `register_net_sysctl_sz(net, "net/bridge", table, …)` at net/bridge/br_netfilter_hooks.c:1254 → **`/proc/sys/net/bridge/bridge-nf-call-iptables`**, `.procname = "bridge-nf-call-iptables"` at :1192 in `brnf_table[]` (:1184); handler `brnf_sysctl_call_tables` at :1172; per-netns field `int call_iptables;` at :63, bound at :1246, defaulted to 1 at :1225. Siblings: `bridge-nf-call-arptables` :1186, `bridge-nf-call-ip6tables` :1198, `bridge-nf-filter-vlan-tagged` :1204, `bridge-nf-filter-pppoe-tagged` :1210, `bridge-nf-pass-vlan-input-dev` :1216.

---

## C. Bonding — `drivers/net/bonding/bond_main.c`

| function | path:line | note |
|---|---|---|
| `bond_dev_queue_xmit` | drivers/net/bonding/bond_main.c:297 | decl include/net/bonding.h:679 |
| `bond_should_deliver_exact_match` | :1589 | |
| `bond_handle_frame` | :1603 | |
| `bond_enslave` | :1888 | `netdev_rx_handler_register` at :2234 |
| `__bond_xmit_hash` | :4253 | |
| `bond_xmit_hash` | :4287 | |
| `bond_xmit_hash_xdp` | :4314 (call) | |
| `bond_xmit_roundrobin` | :5045 | slave get :4966 |
| `bond_xmit_activebackup_slave_get` | :5058 | |
| `bond_xmit_activebackup` | :5066 | |
| `bond_3ad_xor_xmit` | :5304 | |
| `bond_xmit_broadcast` | :5322 | |
| `__bond_start_xmit` | :5558 | |
| `bond_start_xmit` | :5596 | |
| `BOND_MODE(bond)` macro | include/net/bonding.h:51 | `((bond)->params.mode)` |
| `struct bonding` | include/net/bonding.h:216 | `curr_active_slave` :218, `slave_cnt` :225, `recv_probe` :226 |
| **`slave_list`** | **absent in 7.2** | successor: `#define bond_slave_list(bond) (&(bond)->dev->adj_list.lower)` at include/net/bonding.h:54 — slaves live in the netdev adjacency list, not a private list head |
| `BOND_MODE_*` | include/uapi/linux/if_bonding.h:67–73 | RR 67, AB 68, XOR 69, BCAST 70, 8023AD 71, TLB 72, ALB 73 |
| `BOND_XMIT_POLICY_*` | include/uapi/linux/if_bonding.h:92–97 | L2 92, L34 93, L23 94, ENCAP23 95, ENCAP34 96, VLAN_SRCMAC 97 |

### bond_enslave — rx_handler registration (drivers/net/bonding/bond_main.c:2234)
```c
// drivers/net/bonding/bond_main.c:2231-2242
	if (!(bond_dev->features & NETIF_F_LRO))
		dev_disable_lro(slave_dev);

	res = netdev_rx_handler_register(slave_dev, bond_handle_frame,
					 new_slave);
	if (res) {
		slave_dbg(bond_dev, slave_dev, "Error %d calling netdev_rx_handler_register\n", res);
		goto err_detach;
	}

	res = bond_master_upper_dev_link(bond, new_slave, extack);
```

### bond_handle_frame — drivers/net/bonding/bond_main.c:1603
```c
// drivers/net/bonding/bond_main.c:1610-1646
	int ret = RX_HANDLER_ANOTHER;

	skb = skb_share_check(skb, GFP_ATOMIC);
	if (unlikely(!skb))
		return RX_HANDLER_CONSUMED;

	*pskb = skb;

	slave = bond_slave_get_rcu(skb->dev);
	bond = slave->bond;

	recv_probe = READ_ONCE(bond->recv_probe);
	if (recv_probe) {
		ret = recv_probe(skb, bond, slave);
		if (ret == RX_HANDLER_CONSUMED) {
			consume_skb(skb);
			return ret;
		}
	}
	...
	if (bond_should_deliver_exact_match(skb, slave, bond)) {
		if (is_link_local_ether_addr(eth_hdr(skb)->h_dest))
			return RX_HANDLER_PASS;
		return RX_HANDLER_EXACT;
	}

	skb->dev = bond->dev;
```
`recv_probe` is set to `bond_rcv_validate` (ARP/NS monitor) at :4388 and `bond_3ad_lacpdu_recv` (LACPDU) at :4394; cleared at :4417. Function returns `RX_HANDLER_ANOTHER` at :3231/:3419/:3442/:3450 (helper paths) and via `ret` initialised at :1610.

### __bond_start_xmit — mode dispatch (drivers/net/bonding/bond_main.c:5558)
```c
// drivers/net/bonding/bond_main.c:5571-5593
	switch (BOND_MODE(bond)) {
	case BOND_MODE_ROUNDROBIN:
		return bond_xmit_roundrobin(skb, dev);
	case BOND_MODE_ACTIVEBACKUP:
		return bond_xmit_activebackup(skb, dev);
	case BOND_MODE_8023AD:
		if (bond_should_broadcast_neighbor(skb, dev))
			return bond_xmit_broadcast(skb, dev, false);
		fallthrough;
	case BOND_MODE_XOR:
		return bond_3ad_xor_xmit(skb, dev);
	case BOND_MODE_BROADCAST:
		return bond_xmit_broadcast(skb, dev, true);
	case BOND_MODE_ALB:
		return bond_alb_xmit(skb, dev);
	case BOND_MODE_TLB:
		return bond_tlb_xmit(skb, dev);
	default:
		/* Should never happen, mode already checked */
		netdev_err(dev, "Unknown bonding mode %d\n", BOND_MODE(bond));
		WARN_ON_ONCE(1);
		return bond_tx_drop(dev, skb);
	}
```

### __bond_xmit_hash — which fields each policy hashes (drivers/net/bonding/bond_main.c:4253)
```c
// drivers/net/bonding/bond_main.c:4253-4277
static u32 __bond_xmit_hash(struct bonding *bond, struct sk_buff *skb, const void *data,
			    __be16 l2_proto, int mhoff, int nhoff, int hlen)
{
	struct flow_keys flow;
	u32 hash;

	if (bond->params.xmit_policy == BOND_XMIT_POLICY_VLAN_SRCMAC)
		return bond_vlan_srcmac_hash(skb, data, mhoff, hlen);

	if (bond->params.xmit_policy == BOND_XMIT_POLICY_LAYER2 ||
	    !bond_flow_dissect(bond, skb, data, l2_proto, nhoff, hlen, &flow))
		return bond_eth_hash(skb, data, mhoff, hlen);

	if (bond->params.xmit_policy == BOND_XMIT_POLICY_LAYER23 ||
	    bond->params.xmit_policy == BOND_XMIT_POLICY_ENCAP23) {
		hash = bond_eth_hash(skb, data, mhoff, hlen);
	} else {
		if (flow.icmp.id)
			memcpy(&hash, &flow.icmp, sizeof(hash));
		else
			memcpy(&hash, &flow.ports.ports, sizeof(hash));
	}

	return bond_ip_hash(hash, &flow, bond->params.xmit_policy);
}
```
`bond_xmit_hash` (:4287) short-circuits to `skb->hash` for `ENCAP34` when `skb->l4_hash`, else calls `__bond_xmit_hash` at :4293.

### bond_dev_queue_xmit — drivers/net/bonding/bond_main.c:297
```c
// drivers/net/bonding/bond_main.c:297-310
netdev_tx_t bond_dev_queue_xmit(struct bonding *bond, struct sk_buff *skb,
			struct net_device *slave_dev)
{
	skb->dev = slave_dev;

	BUILD_BUG_ON(sizeof(skb->queue_mapping) !=
		     sizeof(qdisc_skb_cb(skb)->slave_dev_queue_mapping));
	skb_set_queue_mapping(skb, qdisc_skb_cb(skb)->slave_dev_queue_mapping);

	if (unlikely(netpoll_tx_running(bond->dev)))
		return bond_netpoll_send_skb(bond_get_slave_by_dev(bond, slave_dev), skb);

	return dev_queue_xmit(skb);
}
```
```c
// drivers/net/bonding/bond_main.c:5058-5077  (activebackup: the curr_active_slave read)
static struct slave *bond_xmit_activebackup_slave_get(struct bonding *bond)
{
	return rcu_dereference(bond->curr_active_slave);
}
...
	slave = bond_xmit_activebackup_slave_get(bond);
	if (slave)
		return bond_dev_queue_xmit(bond, skb, slave->dev);

	return bond_tx_drop(bond_dev, skb);
```
```c
// drivers/net/bonding/bond_main.c:5304-5316  (3ad/xor)
static netdev_tx_t bond_3ad_xor_xmit(struct sk_buff *skb,
				     struct net_device *dev)
{
	struct bonding *bond = netdev_priv(dev);
	struct bond_up_slave *slaves;
	struct slave *slave;

	slaves = rcu_dereference(bond->usable_slaves);
	slave = bond_xmit_3ad_xor_slave_get(bond, skb, slaves);
	if (likely(slave))
		return bond_dev_queue_xmit(bond, skb, slave->dev);

	return bond_tx_drop(dev, skb);
}
```
Note: `bond_xmit_broadcast` (:5322) is the only bonding tx path that copies — `bond_dev_queue_xmit(bond, skb2, slave->dev)` at :5357 (with `skb_clone`/`pskb_copy` upstream in that function).

---

## D. VRF — `drivers/net/vrf.c`, `net/l3mdev/l3mdev.c`, `include/net/l3mdev.h`

| function | path:line | note |
|---|---|---|
| `vrf_local_xmit` | drivers/net/vrf.c:358 | |
| `vrf_ip_local_out` | drivers/net/vrf.c:475 | |
| `vrf_process_v4_outbound` | drivers/net/vrf.c:490 | |
| `is_ip_tx_frame` | drivers/net/vrf.c:550 | |
| `vrf_xmit` | drivers/net/vrf.c:563 | |
| `vrf_output` | drivers/net/vrf.c:834 | |
| `vrf_ip_out_redirect` | drivers/net/vrf.c:853 | |
| `vrf_output_direct` | drivers/net/vrf.c:876 | |
| `vrf_ip_out_direct` | drivers/net/vrf.c:905 | |
| `vrf_ip_out` | drivers/net/vrf.c:926 | |
| `vrf_l3_out` | drivers/net/vrf.c:945 | |
| `do_vrf_add_slave` | drivers/net/vrf.c:1012 | |
| `vrf_add_slave` | drivers/net/vrf.c:1041 | |
| `vrf_dev_init` | drivers/net/vrf.c:1086 | |
| `vrf_netdev_ops` | drivers/net/vrf.c:1110 | `.ndo_start_xmit = vrf_xmit` :1113, `.ndo_add_slave = vrf_add_slave` :1115 |
| `vrf_fib_table` | drivers/net/vrf.c:1119 | returns `vrf->tb_id` |
| `vrf_rcv_finish` | drivers/net/vrf.c:1126 | |
| `vrf_rcv_nfhook` | drivers/net/vrf.c:1132 | |
| `vrf_ip6_input_dst` | drivers/net/vrf.c:1247 | **no IPv4 equivalent in 7.2** |
| `vrf_ip6_rcv` | drivers/net/vrf.c:1275 | |
| `vrf_ip_rcv` | drivers/net/vrf.c:1340 | |
| `vrf_l3_rcv` | drivers/net/vrf.c:1380 | |
| `vrf_link_scope_lookup` | drivers/net/vrf.c:1400 | |
| `vrf_l3mdev_ops` | drivers/net/vrf.c:1428 | |
| `vrf_newlink` | drivers/net/vrf.c:1636 | |
| `vrf_link_ops` | drivers/net/vrf.c:1730 | |
| **`vrf_rx_stats`** | **absent in 7.2** | successor: `dev_dstats_rx_add(vrf_dev, skb->len)` at drivers/net/vrf.c:1360 |

### vrf_ip_rcv — drivers/net/vrf.c:1340–1376
```c
// drivers/net/vrf.c:1340-1376
static struct sk_buff *vrf_ip_rcv(struct net_device *vrf_dev,
				  struct sk_buff *skb)
{
	struct net_device *orig_dev = skb->dev;

	skb->dev = vrf_dev;
	skb->skb_iif = vrf_dev->ifindex;
	IPCB(skb)->flags |= IPSKB_L3SLAVE;

	if (ipv4_is_multicast(ip_hdr(skb)->daddr))
		goto out;

	/* loopback traffic; do not push through packet taps again.
	 * Reset pkt_type for upper layers to process skb
	 */
	if (skb->pkt_type == PACKET_LOOPBACK) {
		skb->pkt_type = PACKET_HOST;
		goto out;
	}

	dev_dstats_rx_add(vrf_dev, skb->len);

	if (!list_empty(&vrf_dev->ptype_all)) {
		int err;

		err = vrf_add_mac_header_if_unset(skb, vrf_dev, ETH_P_IP,
						  orig_dev);
		if (likely(!err)) {
			skb_push(skb, skb->mac_len);
			dev_queue_xmit_nit(skb, vrf_dev);
			skb_pull(skb, skb->mac_len);
		}
	}

	skb = vrf_rcv_nfhook(NFPROTO_IPV4, NF_INET_PRE_ROUTING, skb, vrf_dev);
out:
	return skb;
}
```
Differences from the description you gave: 7.2 uses `dev_dstats_rx_add` (not `vrf_rx_stats`); the "loopback" test is on `skb->pkt_type == PACKET_LOOPBACK` (there is **no** `IFF_LOOPBACK`/`orig_dev` check for IPv4 — `orig_dev` is only used for the tap MAC header at :1366); there is **no** `vrf_ip_input_dst` call in the v4 path (only IPv6 has `vrf_ip6_input_dst`, :1247, called from `vrf_ip6_rcv`); and there is no `vrf_ip_local_out` on the receive side.

### vrf_l3_rcv / vrf_rcv_nfhook
```c
// drivers/net/vrf.c:1379-1392
/* called with rcu lock held */
static struct sk_buff *vrf_l3_rcv(struct net_device *vrf_dev,
				  struct sk_buff *skb,
				  u16 proto)
{
	switch (proto) {
	case AF_INET:
		return vrf_ip_rcv(vrf_dev, skb);
	case AF_INET6:
		return vrf_ip6_rcv(vrf_dev, skb);
	}

	return skb;
}
```
```c
// drivers/net/vrf.c:1132-1142
static struct sk_buff *vrf_rcv_nfhook(u8 pf, unsigned int hook,
				      struct sk_buff *skb,
				      struct net_device *dev)
{
	struct net *net = dev_net(dev);

	if (nf_hook(pf, hook, net, NULL, skb, dev, NULL, vrf_rcv_finish) != 1)
		skb = NULL;    /* kfree_skb(skb) handled by nf code */

	return skb;
}
```

### vrf_xmit / vrf_process_v4_outbound / vrf_ip_local_out
```c
// drivers/net/vrf.c:563-575
static netdev_tx_t vrf_xmit(struct sk_buff *skb, struct net_device *dev)
{
	unsigned int len = skb->len;
	netdev_tx_t ret;

	ret = is_ip_tx_frame(skb, dev);
	if (likely(ret == NET_XMIT_SUCCESS || ret == NET_XMIT_CN))
		dev_dstats_tx_add(dev, len);
	else
		dev_dstats_tx_dropped(dev);

	return ret;
}
```
```c
// drivers/net/vrf.c:504-540  (vrf_process_v4_outbound: flow, route, dst, local_out)
	memset(&fl4, 0, sizeof(fl4));
	/* needed to match OIF rule */
	fl4.flowi4_l3mdev = vrf_dev->ifindex;
	fl4.flowi4_iif = LOOPBACK_IFINDEX;
	fl4.flowi4_dscp = ip4h_dscp(ip4h);
	fl4.flowi4_flags = FLOWI_FLAG_ANYSRC;
	fl4.flowi4_proto = ip4h->protocol;
	fl4.daddr = ip4h->daddr;
	fl4.saddr = ip4h->saddr;

	rt = ip_route_output_flow(net, &fl4, NULL);
	if (IS_ERR(rt))
		goto err;

	skb_dst_drop(skb);

	/* if dst.dev is the VRF device again this is locally originated traffic
	 * destined to a local address. Short circuit to Rx path.
	 */
	if (rt->dst.dev == vrf_dev)
		return vrf_local_xmit(skb, vrf_dev, &rt->dst);

	skb_dst_set(skb, &rt->dst);
```
```c
// drivers/net/vrf.c:538-543
	memset(IPCB(skb), 0, sizeof(*IPCB(skb)));
	ret = vrf_ip_local_out(dev_net(skb_dst(skb)->dev), skb->sk, skb);
	if (unlikely(net_xmit_eval(ret)))
		vrf_dev->stats.tx_errors++;
	else
		ret = NET_XMIT_SUCCESS;
```
```c
// drivers/net/vrf.c:475-488
static int vrf_ip_local_out(struct net *net, struct sock *sk,
			    struct sk_buff *skb)
{
	int err;

	vrf_nf_reset_ct(skb);

	err = nf_hook(NFPROTO_IPV4, NF_INET_LOCAL_OUT, net, sk,
		      skb, NULL, skb_dst(skb)->dev, dst_output);
	if (likely(err == 1))
		err = dst_output(net, sk, skb);

	return err;
}
```
Note: `fl4.flowi4_l3mdev = vrf_dev->ifindex` (:506) has **replaced** the old `FLOWI_FLAG_L3MDEV_SRC`/oif-based trick; `FLOWI_FLAG_ANYSRC` remains at :509.

### vrf_ip_out / vrf_ip_out_direct — locally generated packets (l3mdev_l3_out path)
```c
// drivers/net/vrf.c:926-942
static struct sk_buff *vrf_ip_out(struct net_device *vrf_dev,
				  struct sock *sk,
				  struct sk_buff *skb)
{
	/* don't divert multicast or local broadcast */
	if (ipv4_is_multicast(ip_hdr(skb)->daddr) ||
	    ipv4_is_lbcast(ip_hdr(skb)->daddr))
		return skb;

	vrf_nf_set_untracked(skb);

	if (qdisc_tx_is_default(vrf_dev) ||
	    IPCB(skb)->flags & IPSKB_XFRM_TRANSFORMED)
		return vrf_ip_out_direct(vrf_dev, sk, skb);

	return vrf_ip_out_redirect(vrf_dev, skb);
}
```
```c
// drivers/net/vrf.c:905-924  (vrf_ip_out_direct)
	skb->dev = vrf_dev;

	err = nf_hook(NFPROTO_IPV4, NF_INET_LOCAL_OUT, net, sk,
		      skb, NULL, vrf_dev, vrf_ip_out_direct_finish);

	if (likely(err == 1))
		err = vrf_output_direct(net, sk, skb);
```

### vrf_l3mdev_ops — drivers/net/vrf.c:1428–1436
```c
// drivers/net/vrf.c:1428-1436
static const struct l3mdev_ops vrf_l3mdev_ops = {
	.l3mdev_fib_table	= vrf_fib_table,
	.l3mdev_l3_rcv		= vrf_l3_rcv,
	.l3mdev_l3_out		= vrf_l3_out,
#if IS_ENABLED(CONFIG_IPV6)
	.l3mdev_link_scope_lookup = vrf_link_scope_lookup,
#endif
};
```

### do_vrf_add_slave + table-id storage
```c
// drivers/net/vrf.c:1026-1033
	port_dev->priv_flags |= IFF_L3MDEV_SLAVE;
	ret = netdev_master_upper_dev_link(port_dev, dev, NULL, NULL, extack);
	if (ret < 0)
		goto err;

	cycle_netdev(port_dev, extack);

	return 0;
```
The table id is stored on the **master** in `struct net_vrf.tb_id` (`drivers/net/vrf.c:114` struct, `vrf_fib_table` :1119 returns it). It is parsed in `vrf_newlink`:
```c
// drivers/net/vrf.c:1647-1660
	vrf->tb_id = nla_get_u32(data[IFLA_VRF_TABLE]);
	if (vrf->tb_id == RT_TABLE_UNSPEC) {
		NL_SET_ERR_MSG_ATTR(extack, data[IFLA_VRF_TABLE],
				    "Invalid VRF table id");
		return -EINVAL;
	}

	dev->priv_flags |= IFF_L3MDEV_MASTER;

	err = register_netdevice(dev);
```
`vrf_dev_init` (:1086) creates the self-referential default dst (`vrf_rtable_create` :1091, `vrf_rt6_create` :1094) and sets `dev->flags = IFF_MASTER | IFF_NOARP` at :1098.

### l3mdev

| item | path:line |
|---|---|
| `struct l3mdev_ops` fields | include/net/l3mdev.h:36 (`l3mdev_fib_table`), :37 (`l3mdev_l3_rcv`), :39 (`l3mdev_l3_out`) |
| `l3mdev_master_ifindex_rcu` (decl) | include/net/l3mdev.h:78 |
| `l3mdev_master_ifindex` | include/net/l3mdev.h:79 |
| `l3mdev_fib_table_rcu` (decl) | include/net/l3mdev.h:144 |
| `l3mdev_fib_table` | include/net/l3mdev.h:146 |
| `l3mdev_l3_rcv` | include/net/l3mdev.h:179 |
| `l3mdev_ip_rcv` | include/net/l3mdev.h:196 |
| `l3mdev_l3_out` | include/net/l3mdev.h:208 |
| `l3mdev_ip_out` | include/net/l3mdev.h:228 |
| (stubs when !CONFIG_NET_L3_MASTER_DEV) | include/net/l3mdev.h:296 / :308 |
| `l3mdev_master_ifindex_rcu` (def) | net/l3mdev/l3mdev.c:110 |
| `l3mdev_fib_table_rcu` (def) | net/l3mdev/l3mdev.c:162 |
| `l3mdev_fib_table_by_index` | net/l3mdev/l3mdev.c:189 |
| `l3mdev_link_scope_lookup` | net/l3mdev/l3mdev.c:218 |
| `l3mdev_fib_rule_match` | net/l3mdev/l3mdev.c:247 |
| `l3mdev_update_flow` | net/l3mdev/l3mdev.c:271 |

```c
// include/net/l3mdev.h:178-199
static inline
struct sk_buff *l3mdev_l3_rcv(struct sk_buff *skb, u16 proto)
{
	struct net_device *master = NULL;

	if (netif_is_l3_slave(skb->dev))
		master = netdev_master_upper_dev_get_rcu(skb->dev);
	else if (netif_is_l3_master(skb->dev) ||
		 netif_has_l3_rx_handler(skb->dev))
		master = skb->dev;

	if (master && master->l3mdev_ops->l3mdev_l3_rcv)
		skb = master->l3mdev_ops->l3mdev_l3_rcv(master, skb, proto);

	return skb;
}

static inline
struct sk_buff *l3mdev_ip_rcv(struct sk_buff *skb)
{
	return l3mdev_l3_rcv(skb, AF_INET);
}
```
(`netif_is_l3_slave()` is the `IFF_L3MDEV_SLAVE` test; it lives in include/linux/netdevice.h.)

```c
// net/l3mdev/l3mdev.c:247-269  (l3mdev_fib_rule_match)
int l3mdev_fib_rule_match(struct net *net, struct flowi *fl,
			  struct fib_lookup_arg *arg)
{
	struct net_device *dev;
	int rc = 0;

	/* update flow ensures flowi_l3mdev is set when relevant */
	if (!fl->flowi_l3mdev)
		return 0;

	rcu_read_lock();

	dev = dev_get_by_index_rcu(net, fl->flowi_l3mdev);
	if (dev && netif_is_l3_master(dev) &&
	    dev->l3mdev_ops->l3mdev_fib_table) {
		arg->table = dev->l3mdev_ops->l3mdev_fib_table(dev);
		rc = 1;
	}

	rcu_read_unlock();

	return rc;
}
```

**Where l3mdev_ip_rcv is called:** `ip_rcv_finish()` — `net/ipv4/ip_input.c:486` (also `ip_list_rcv_finish()` at :655).
```c
// net/ipv4/ip_input.c:480-490
static int ip_rcv_finish(struct net *net, struct sock *sk, struct sk_buff *skb)
{
	struct net_device *dev = skb->dev;
	int ret;

	/* if ingress device is enslaved to an L3 master device pass the
	 * skb to its handler for processing
	 */
	skb = l3mdev_ip_rcv(skb);
	if (!skb)
		return NET_RX_SUCCESS;
```
**Where l3mdev_ip_out is called:** `__ip_local_out()` (defined net/ipv4/ip_output.c:102) — call at `net/ipv4/ip_output.c:114`.
```c
// net/ipv4/ip_output.c:111-118
	/* if egress device is enslaved to an L3 master device pass the
	 * skb to its handler for processing
	 */
	skb = l3mdev_ip_out(sk, skb);
	if (unlikely(!skb))
		return 0;

	skb->protocol = htons(ETH_P_IP);
```

**FRA_L3MDEV / rule->l3mdev matching:** the generic rule matcher does it, not `fib4_rule_match`:
```c
// net/core/fib_rules.c:298-299
	if (rule->l3mdev && !l3mdev_fib_rule_match(rule->fr_net, fl, arg))
		goto out;
```
Related anchors: `[FRA_L3MDEV] = { .type = NLA_U8 }` net/core/fib_rules.c:863; parse `nlrule->l3mdev = nla_get_u8(nla)` :529; `fib_nl2rule_l3mdev` call :641; dump :1207. IPv4 side: `fib4_rule_match` is at net/ipv4/fib_rules.c:180 (registered `.match` at :469) and calls `l3mdev_update_flow(net, flowi4_to_flowi(flp))` at :94 (in `fib4_rule_action`/lookup prep); `fib4_rule_default` rejects l3mdev rules at :64.

### `ip vrf exec` kernel side
- `BPF_CGROUP_INET_SOCK_CREATE` — `include/uapi/linux/bpf.h:1102`.
- `struct bpf_sock.bound_dev_if` writability gate — `__sock_filter_check_attach_type()` at `net/core/filter.c:9080`, the field case at `:9085`:
```c
// net/core/filter.c:9080-9094
static bool __sock_filter_check_attach_type(int off,
					    enum bpf_access_type access_type,
					    enum bpf_attach_type attach_type)
{
	switch (off) {
	case offsetof(struct bpf_sock, bound_dev_if):
	case offsetof(struct bpf_sock, mark):
	case offsetof(struct bpf_sock, priority):
		switch (attach_type) {
		case BPF_CGROUP_INET_SOCK_CREATE:
		case BPF_CGROUP_INET_SOCK_RELEASE:
			goto full_access;
		default:
			return false;
		}
```
- The actual load/store conversion to `sk->sk_bound_dev_if`: `net/core/filter.c:10254–10262` (`BUILD_BUG_ON(sizeof_field(struct sock, sk_bound_dev_if) != 4)` at :10255).

---

## E. macvlan — `drivers/net/macvlan.c`

| function | path:line | note |
|---|---|---|
| `macvlan_hash_lookup` | drivers/net/macvlan.c:125 | |
| `macvlan_hash_lookup_source` | :139 | |
| `macvlan_broadcast_one` | (called :291, :493) | |
| `macvlan_broadcast` | :264 | |
| `macvlan_forward_source_one` | :408 | |
| `macvlan_forward_source` | :434 | |
| `macvlan_handle_frame` | :460 | |
| `macvlan_queue_xmit` | :545 | |
| `macvlan_start_xmit` | :585 | |
| `macvlan_port_create` | :1250 | `netdev_rx_handler_register` at :1279 |
| `macvlan_common_newlink` | :1460 | mode parse at :1522–1523; validate switch at :1345–1349 |
| `enum macvlan_mode` | include/uapi/linux/if_link.h:1229 | PRIVATE 1230, VEPA 1231, BRIDGE 1232, PASSTHRU 1233, SOURCE 1234 |
| `struct macvlan_dev` | include/linux/if_macvlan.h:18 | `port` :22, `lowerdev` :23, `mode` :31 |

### macvlan_port_create registration (drivers/net/macvlan.c:1279)
```c
// drivers/net/macvlan.c:1279
	err = netdev_rx_handler_register(dev, macvlan_handle_frame, port);
```

### macvlan_handle_frame — drivers/net/macvlan.c:460–542
```c
// drivers/net/macvlan.c:472-506  (multicast/broadcast branch)
	/* Packets from dev_loopback_xmit() do not have L2 header, bail out */
	if (unlikely(skb->pkt_type == PACKET_LOOPBACK))
		return RX_HANDLER_PASS;

	port = macvlan_port_get_rcu(skb->dev);
	if (is_multicast_ether_addr(eth->h_dest)) {
		unsigned int hash;

		skb = ip_check_defrag(dev_net(skb->dev), skb, IP_DEFRAG_MACVLAN);
		if (!skb)
			return RX_HANDLER_CONSUMED;
		*pskb = skb;
		eth = eth_hdr(skb);
		if (macvlan_forward_source(skb, port, eth->h_source)) {
			kfree_skb(skb);
			return RX_HANDLER_CONSUMED;
		}
		src = macvlan_hash_lookup(port, eth->h_source);
		if (src && src->mode != MACVLAN_MODE_VEPA &&
		    src->mode != MACVLAN_MODE_BRIDGE) {
			/* forward to original port. */
			vlan = src;
			ret = macvlan_broadcast_one(skb, vlan, eth, 0) ?:
			      __netif_rx(skb);
			handle_res = RX_HANDLER_CONSUMED;
			goto out;
		}

		hash = mc_hash(NULL, eth->h_dest);
		if (test_bit(hash, port->bc_filter))
			macvlan_broadcast_enqueue(port, src, skb);
		else if (test_bit(hash, port->mc_filter))
			macvlan_multicast_rx(port, src, skb);

		return RX_HANDLER_PASS;
	}
```
```c
// drivers/net/macvlan.c:508-541  (unicast: source filter, passthru, hash lookup, PACKET_HOST, RX_HANDLER_ANOTHER)
	if (macvlan_forward_source(skb, port, eth->h_source)) {
		kfree_skb(skb);
		return RX_HANDLER_CONSUMED;
	}
	if (macvlan_passthru(port))
		vlan = list_first_or_null_rcu(&port->vlans,
					      struct macvlan_dev, list);
	else
		vlan = macvlan_hash_lookup(port, eth->h_dest);
	if (!vlan || vlan->mode == MACVLAN_MODE_SOURCE)
		return RX_HANDLER_PASS;

	dev = vlan->dev;
	if (unlikely(!(dev->flags & IFF_UP))) {
		kfree_skb(skb);
		return RX_HANDLER_CONSUMED;
	}
	len = skb->len + ETH_HLEN;
	skb = skb_share_check(skb, GFP_ATOMIC);
	if (!skb) {
		ret = NET_RX_DROP;
		handle_res = RX_HANDLER_CONSUMED;
		goto out;
	}

	*pskb = skb;
	skb->dev = dev;
	skb->pkt_type = PACKET_HOST;

	ret = NET_RX_SUCCESS;
	handle_res = RX_HANDLER_ANOTHER;
out:
	macvlan_count_rx(vlan, len, ret == NET_RX_SUCCESS, false);
	return handle_res;
```

### macvlan_queue_xmit — drivers/net/macvlan.c:545–573
```c
// drivers/net/macvlan.c:545-573
static int macvlan_queue_xmit(struct sk_buff *skb, struct net_device *dev)
{
	const struct macvlan_dev *vlan = netdev_priv(dev);
	const struct macvlan_port *port = vlan->port;
	const struct macvlan_dev *dest;

	if (vlan->mode == MACVLAN_MODE_BRIDGE) {
		const struct ethhdr *eth = skb_eth_hdr(skb);

		/* send to other bridge ports directly */
		if (is_multicast_ether_addr(eth->h_dest)) {
			skb_reset_mac_header(skb);
			macvlan_broadcast(skb, port, dev, MACVLAN_MODE_BRIDGE);
			goto xmit_world;
		}

		dest = macvlan_hash_lookup(port, eth->h_dest);
		if (dest && dest->mode == MACVLAN_MODE_BRIDGE) {
			/* send to lowerdev first for its network taps */
			dev_forward_skb(vlan->lowerdev, skb);

			return NET_XMIT_SUCCESS;
		}
	}
xmit_world:
	skb->dev = vlan->lowerdev;
	return dev_queue_xmit_accel(skb,
				    netdev_get_sb_channel(dev) ? dev : NULL);
}
```
Note the 7.2 tail is `dev_queue_xmit_accel(skb, …)` (accel/sb-channel aware), not plain `dev_queue_xmit`.
```c
// drivers/net/macvlan.c:585-595  (macvlan_start_xmit)
static netdev_tx_t macvlan_start_xmit(struct sk_buff *skb,
				      struct net_device *dev)
{
	struct macvlan_dev *vlan = netdev_priv(dev);
	unsigned int len = skb->len;
	int ret;

	if (unlikely(netpoll_tx_running(dev)))
		return macvlan_netpoll_send_skb(vlan, skb);

	ret = macvlan_queue_xmit(skb, dev);
```
```c
// drivers/net/macvlan.c:125-137  (macvlan_hash_lookup)
static struct macvlan_dev *macvlan_hash_lookup(const struct macvlan_port *port,
					       const unsigned char *addr)
{
	struct macvlan_dev *vlan;
	u32 idx = macvlan_eth_hash(addr);

	hlist_for_each_entry_rcu(vlan, &port->vlan_hash[idx], hlist,
				 lockdep_rtnl_is_held()) {
		if (ether_addr_equal_64bits(vlan->dev->dev_addr, addr))
			return vlan;
	}
	return NULL;
}
```
Mode parsing in `macvlan_common_newlink`: `vlan->mode = nla_get_u32(data[IFLA_MACVLAN_MODE]);` at drivers/net/macvlan.c:1523 (guarded at :1522); the validate-side switch is at :1345–1349; `macvlan_changelink` re-parse at :1625–1627.

---

## F. ipvlan — `drivers/net/ipvlan/`

| function | path:line | note |
|---|---|---|
| `ipvlan_get_L3_hdr` | ipvlan_core.c:149 | |
| `ipvlan_skb_crossing_ns` | ipvlan_core.c:312 | |
| `ipvlan_rcv_frame` | ipvlan_core.c:324 | |
| `ipvlan_addr_lookup` | ipvlan_core.c:366 | |
| `ipvlan_process_v4_outbound` | ipvlan_core.c:428 | |
| `ipvlan_process_outbound` | ipvlan_core.c:536 | |
| `ipvlan_multicast_enqueue` | ipvlan_core.c:575 | |
| `ipvlan_xmit_mode_l3` | ipvlan_core.c:603 | |
| `ipvlan_xmit_mode_l2` | ipvlan_core.c:630 | |
| `ipvlan_queue_xmit` | ipvlan_core.c:675 | |
| `ipvlan_external_frame` | ipvlan_core.c:703 | |
| `ipvlan_handle_mode_l3` | ipvlan_core.c:723 | |
| `ipvlan_handle_mode_l2` | ipvlan_core.c:744 | |
| `ipvlan_handle_frame` | ipvlan_core.c:781 | |
| `ipvlan_l3_rcv` | ipvlan_l3s.c:39 | l3mdev-based (L3S) |
| `ipvl_l3mdev_ops` | ipvlan_l3s.c:91 (`.l3mdev_l3_rcv` :92) | |
| `ipvlan_nf_input` | ipvlan_l3s.c:95 | |
| `ipvl_nfops[]` | ipvlan_l3s.c:117 | |
| `ipvlan_register_nf_hook` | ipvlan_l3s.c:134 | `nf_register_net_hooks` :140 |
| `ipvlan_unregister_nf_hook` | ipvlan_l3s.c:151 | |
| `ipvlan_l3s_register` (called) | ipvlan_main.c:34 | |
| `ipvlan_set_port_mode` | ipvlan_main.c:10 | |
| `ipvlan_port_create` | ipvlan_main.c:62 | `netdev_rx_handler_register(dev, ipvlan_handle_frame, port)` at :84 |
| **`ipvlan_init_port`** | **absent in 7.2** | successor = `ipvlan_port_create` (ipvlan_main.c:62), called from `ipvlan_link_new` path at :159 |
| `ipvlan_link_new` | ipvlan_main.c:540 | flags parse :635, mode parse :638 |
| `enum ipvlan_mode` | include/uapi/linux/if_link.h:1324 | L2 1325, L3 1326, L3S 1327, MAX 1328 |
| `IPVLAN_F_PRIVATE` / `IPVLAN_F_VEPA` | include/uapi/linux/if_link.h:1331 / :1332 | |

### ipvlan_handle_frame — drivers/net/ipvlan/ipvlan_core.c:781–803
```c
// drivers/net/ipvlan/ipvlan_core.c:781-803
rx_handler_result_t ipvlan_handle_frame(struct sk_buff **pskb)
{
	struct sk_buff *skb = *pskb;
	struct ipvl_port *port = ipvlan_port_get_rcu(skb->dev);

	if (!port)
		return RX_HANDLER_PASS;

	switch (port->mode) {
	case IPVLAN_MODE_L2:
		return ipvlan_handle_mode_l2(pskb, port);
	case IPVLAN_MODE_L3:
		return ipvlan_handle_mode_l3(pskb, port);
#ifdef CONFIG_IPVLAN_L3S
	case IPVLAN_MODE_L3S:
		return RX_HANDLER_PASS;
#endif
	}

	/* Should not reach here */
	WARN_ONCE(true, "%s called for mode = [%x]\n", __func__, port->mode);
	kfree_skb(skb);
	return RX_HANDLER_CONSUMED;
}
```
Note: L3S returns `RX_HANDLER_PASS` here — the work happens in the netfilter `NF_INET_LOCAL_IN` hook and the l3mdev `l3mdev_l3_rcv` callback instead.

### ipvlan_handle_mode_l3 / l2
```c
// drivers/net/ipvlan/ipvlan_core.c:723-742
static rx_handler_result_t ipvlan_handle_mode_l3(struct sk_buff **pskb,
						 struct ipvl_port *port)
{
	void *lyr3h;
	int addr_type;
	struct ipvl_addr *addr;
	struct sk_buff *skb = *pskb;
	rx_handler_result_t ret = RX_HANDLER_PASS;

	lyr3h = ipvlan_get_L3_hdr(port, skb, &addr_type);
	if (!lyr3h)
		goto out;

	addr = ipvlan_addr_lookup(port, lyr3h, addr_type, true);
	if (addr)
		ret = ipvlan_rcv_frame(addr, pskb, false);

out:
	return ret;
}
```
```c
// drivers/net/ipvlan/ipvlan_core.c:744-779  (l2: unicast delegates to l3; multicast clones + enqueues)
	if (unlikely(skb->pkt_type == PACKET_LOOPBACK))
		return RX_HANDLER_PASS;

	/* Perform like l3 mode for non-multicast packet */
	if (likely(!is_multicast_ether_addr(eth->h_dest)))
		return ipvlan_handle_mode_l3(pskb, port);
	...
	if (!ipvlan_external_frame(skb, port))
		return RX_HANDLER_PASS;

	if (skb_queue_len_lockless(&port->backlog) >= IPVLAN_QBACKLOG_LIMIT)
		nskb = NULL;
	else
		nskb = skb_clone(skb, GFP_ATOMIC);

	if (nskb) {
		ipvlan_skb_crossing_ns(nskb, NULL);
		ipvlan_multicast_enqueue(port, nskb, false);
	} else {
		dev_core_stats_rx_dropped_inc(skb->dev);
	}

	return RX_HANDLER_PASS;
```

### ipvlan_rcv_frame — the `local` fork (drivers/net/ipvlan/ipvlan_core.c:324–364)
```c
// drivers/net/ipvlan/ipvlan_core.c:337-363
	if (local) {
		if (unlikely(!(dev->flags & IFF_UP))) {
			kfree_skb_reason(skb, SKB_DROP_REASON_DEV_READY);
			goto out;
		}

		skb = skb_share_check(skb, GFP_ATOMIC);
		if (!skb)
			goto out;

		*pskb = skb;
	}

	if (local) {
		skb->pkt_type = PACKET_HOST;
		if (dev_forward_skb(ipvlan->dev, skb) == NET_RX_SUCCESS)
			success = true;
	} else {
		skb->dev = dev;
		ret = RX_HANDLER_ANOTHER;
		success = true;
	}

out:
	ipvlan_count_rx(ipvlan, len, success, false);
	return ret;
```
(`skb->dev = dev` is at :356 for the non-local case; `PACKET_HOST` at :351 for the local case.)

### ipvlan_addr_lookup — hash on IP address (drivers/net/ipvlan/ipvlan_core.c:366)
```c
// drivers/net/ipvlan/ipvlan_core.c:366-386
struct ipvl_addr *ipvlan_addr_lookup(struct ipvl_port *port, void *lyr3h,
				     int addr_type, bool use_dest)
{
	struct ipvl_addr *addr = NULL;
#if IS_ENABLED(CONFIG_IPV6)
	struct in6_addr *i6addr;
#endif
	__be32 addr4;

	switch (addr_type) {
#if IS_ENABLED(CONFIG_IPV6)
	case IPVL_IPV6: {
		struct ipv6hdr *ip6h;

		ip6h = (struct ipv6hdr *)lyr3h;
		i6addr = use_dest ? &ip6h->daddr : &ip6h->saddr;
lookup6:
		addr = ipvlan_ht_addr_lookup6(port, i6addr);
		break;
	}
```
Hash helpers: `ipvlan_get_v4_hash` :51, `ipvlan_get_v6_hash` :37/:45, `ipvlan_ht_addr_lookup6` :75, `ipvlan_ht_addr_lookup4` :89.

### ipvlan_queue_xmit — mode dispatch (drivers/net/ipvlan/ipvlan_core.c:675)
```c
// drivers/net/ipvlan/ipvlan_core.c:684-695
	switch(port->mode) {
	case IPVLAN_MODE_L2:
		return ipvlan_xmit_mode_l2(skb, dev);
	case IPVLAN_MODE_L3:
#ifdef CONFIG_IPVLAN_L3S
	case IPVLAN_MODE_L3S:
#endif
		return ipvlan_xmit_mode_l3(skb, dev);
	}
```

### ipvlan_xmit_mode_l2 — sibling delivery, host-loop test, fallthrough
```c
// drivers/net/ipvlan/ipvlan_core.c:636-672
	if (!ipvlan_is_vepa(ipvlan->port) &&
	    ether_addr_equal(eth->h_dest, eth->h_source)) {
		lyr3h = ipvlan_get_L3_hdr(ipvlan->port, skb, &addr_type);
		if (lyr3h) {
			addr = ipvlan_addr_lookup(ipvlan->port, lyr3h, addr_type, true);
			if (addr) {
				if (ipvlan_is_private(ipvlan->port)) {
					consume_skb(skb);
					return NET_XMIT_DROP;
				}
				ipvlan_rcv_frame(addr, &skb, true);
				return NET_XMIT_SUCCESS;
			}
		}
		skb = skb_share_check(skb, GFP_ATOMIC);
		if (!skb)
			return NET_XMIT_DROP;
		/* Packet definitely does not belong to any of the
		 * virtual devices, but the dest is local. So forward
		 * the skb for the main-dev. At the RX side we just return
		 * RX_PASS for it to be processed further on the stack.
		 */
		dev_forward_skb(ipvlan->phy_dev, skb);
		return NET_XMIT_SUCCESS;

	} else if (is_multicast_ether_addr(eth->h_dest)) {
		skb_reset_mac_header(skb);
		ipvlan_skb_crossing_ns(skb, NULL);
		ipvlan_multicast_enqueue(ipvlan->port, skb, true);
		return NET_XMIT_SUCCESS;
	}

	skb->dev = ipvlan->phy_dev;
	return dev_queue_xmit(skb);
```

### ipvlan_xmit_mode_l3 (:603) and ipvlan_process_v4_outbound (:428)
```c
// drivers/net/ipvlan/ipvlan_core.c:613-627
	if (!ipvlan_is_vepa(ipvlan->port)) {
		addr = ipvlan_addr_lookup(ipvlan->port, lyr3h, addr_type, true);
		if (addr) {
			if (ipvlan_is_private(ipvlan->port)) {
				consume_skb(skb);
				return NET_XMIT_DROP;
			}
			ipvlan_rcv_frame(addr, &skb, true);
			return NET_XMIT_SUCCESS;
		}
	}
out:
	ipvlan_skb_crossing_ns(skb, ipvlan->phy_dev);
	return ipvlan_process_outbound(skb);
```
```c
// drivers/net/ipvlan/ipvlan_core.c:435-459
	struct flowi4 fl4 = {
		.flowi4_oif = dev->ifindex,
		.flowi4_flags = FLOWI_FLAG_ANYSRC,
		.flowi4_mark = skb->mark,
	};

	if (!pskb_network_may_pull(skb, sizeof(struct iphdr)))
		goto err;

	ip4h = ip_hdr(skb);
	fl4.daddr = ip4h->daddr;
	fl4.saddr = ip4h->saddr;
	fl4.flowi4_dscp = ip4h_dscp(ip4h);

	rt = ip_route_output_flow(net, &fl4, NULL);
	if (IS_ERR(rt))
		goto err;

	if (rt->rt_type != RTN_UNICAST && rt->rt_type != RTN_LOCAL) {
		ip_rt_put(rt);
		goto err;
	}
	skb_dst_set(skb, &rt->dst);
	memset(IPCB(skb), 0, sizeof(*IPCB(skb)));
```
(`ip_local_out(...)` follows immediately after the excerpt, around :461.)

### L3S: ipvlan_l3_rcv and the NF_INET_LOCAL_IN hook
```c
// drivers/net/ipvlan/ipvlan_l3s.c:39-61
static struct sk_buff *ipvlan_l3_rcv(struct net_device *dev,
				     struct sk_buff *skb, u16 proto)
{
	struct ipvl_addr *addr;
	struct net_device *sdev;

	addr = ipvlan_skb_to_addr(skb, dev);
	if (!addr)
		goto out;

	sdev = addr->master->dev;
	switch (proto) {
	case AF_INET:
	{
		const struct iphdr *ip4h = ip_hdr(skb);
		int err;

		err = ip_route_input_noref(skb, ip4h->daddr, ip4h->saddr,
					   ip4h_dscp(ip4h), sdev);
		if (unlikely(err))
			goto out;
		break;
	}
```
```c
// drivers/net/ipvlan/ipvlan_l3s.c:95-131
static unsigned int ipvlan_nf_input(void *priv, struct sk_buff *skb,
				    const struct nf_hook_state *state)
{
	struct ipvl_addr *addr;
	unsigned int len;

	addr = ipvlan_skb_to_addr(skb, skb->dev);
	if (!addr)
		goto out;

	skb->dev = addr->master->dev;
	skb->skb_iif = skb->dev->ifindex;
#if IS_ENABLED(CONFIG_IPV6)
	if (addr->atype == IPVL_IPV6)
		IP6CB(skb)->iif = skb->dev->ifindex;
#endif
	len = skb->len + ETH_HLEN;
	ipvlan_count_rx(addr->master, len, true, false);
out:
	return NF_ACCEPT;
}

static const struct nf_hook_ops ipvl_nfops[] = {
	{
		.hook     = ipvlan_nf_input,
		.pf       = NFPROTO_IPV4,
		.hooknum  = NF_INET_LOCAL_IN,
		.priority = INT_MAX,
	},
#if IS_ENABLED(CONFIG_IPV6)
	{
		.hook     = ipvlan_nf_input,
		.pf       = NFPROTO_IPV6,
		.hooknum  = NF_INET_LOCAL_IN,
		.priority = INT_MAX,
	},
#endif
};
```
### ipvlan_set_port_mode — L3S registration (drivers/net/ipvlan/ipvlan_main.c:10)
```c
// drivers/net/ipvlan/ipvlan_main.c:21-42
	if (port->mode != nval) {
		list_for_each_entry(ipvlan, &port->ipvlans, pnode) {
			flags = ipvlan->dev->flags;
			if (nval == IPVLAN_MODE_L3 || nval == IPVLAN_MODE_L3S) {
				err = dev_change_flags(ipvlan->dev,
						       flags | IFF_NOARP,
						       extack);
			} else {
				err = dev_change_flags(ipvlan->dev,
						       flags & ~IFF_NOARP,
						       extack);
			}
			if (unlikely(err))
				goto fail;
		}
		if (nval == IPVLAN_MODE_L3S) {
			/* New mode is L3S */
			err = ipvlan_l3s_register(port);
			if (err)
				goto fail;
		} else if (port->mode == IPVLAN_MODE_L3S) {
			/* Old mode was L3S */
			ipvlan_l3s_unregister(port);
		}
		port->mode = nval;
	}
```
`ipvlan_l3s_register` (ipvlan_l3s.c:~205) does both jobs: `ipvlan_register_nf_hook(read_pnet(&port->pnet))` at ipvlan_l3s.c:212 and sets the dev's `l3mdev_ops`/`IFF_L3MDEV_RX_HANDLER`; `ipvlan_l3s_unregister` calls `ipvlan_unregister_nf_hook` at :228.
`ipvlan_link_new` (ipvlan_main.c:540) parses: `port->flags = nla_get_u16(data[IFLA_IPVLAN_FLAGS])` at :635, `mode = nla_get_u16(data[IFLA_IPVLAN_MODE])` at :638; `ipvlan_changelink` re-parses at :460–467.

---

## G. IPVS — `net/netfilter/ipvs/`

| function | path:line | note |
|---|---|---|
| **`ip_vs_ops[]`** | **absent in 7.2** | split into `ip_vs_ops4[]` at ip_vs_core.c:2325 and `ip_vs_ops6[]` at :2374 |
| **`ip_vs_remote_request4` / `ip_vs_reply4` / `ip_vs_local_request4` / `ip_vs_local_reply4`** | **absent in 7.2** | all four collapsed into two family-agnostic hooks: `ip_vs_in_hook` (ip_vs_core.c:2097) and `ip_vs_out_hook` (ip_vs_core.c:1510); the `af` comes from `state->pf` |
| `ip_vs_forward_icmp` | ip_vs_core.c:2296 | |
| `ip_vs_in_hook` | ip_vs_core.c:2097 | (successor of `ip_vs_in`) |
| `ip_vs_out_hook` | ip_vs_core.c:1510 | (successor of `ip_vs_out`) |
| `handle_response` | ip_vs_core.c:1439 | |
| `handle_response_icmp` | ip_vs_core.c:1028 | |
| `__ip_vs_rs_conn_out` | ip_vs_core.c:1401 | |
| `ip_vs_schedule` | ip_vs_core.c:619 | `sched->schedule` :706, `ip_vs_conn_new` :727 |
| `ip_vs_sched_persist` (persistent path) | contains `sched->schedule` :531, `ip_vs_conn_new` :549/:578 | |
| `ip_vs_try_to_schedule` | ip_vs_core.c:1648 | `pp->conn_schedule(...)` at :1661 |
| `__ip_vs_service_find` | ip_vs_ctl.c:495 | |
| `ip_vs_service_find` | ip_vs_ctl.c:562 | calls `__ip_vs_service_find` at :584 |
| `ip_vs_nat_send_or_cont` | ip_vs_xmit.c:666 | |
| `ip_vs_send_or_cont` | ip_vs_xmit.c:696 | |
| `ip_vs_bypass_xmit` | ip_vs_xmit.c:736 | v6 at :759 |
| `ip_vs_nat_xmit` | ip_vs_xmit.c:787 | v6 at :871 |
| `ip_vs_tunnel_xmit` | ip_vs_xmit.c:1147 | v6 at :1292 |
| `ip_vs_dr_xmit` | ip_vs_xmit.c:1439 | v6 at :1469 |
| `ip_vs_drop_early_demux_sk` | ip_vs_xmit.c:650 | |
| `ip_vs_conn_in_get` | ip_vs_conn.c:413 | `ip_vs_conn_in_get_proto` :461 |
| `ip_vs_conn_out_get` | ip_vs_conn.c:543 | `ip_vs_conn_out_get_proto` :604 |
| `ip_vs_conn_new` | ip_vs_conn.c:1444 | `EXPORT_SYMBOL` ip_vs_core.c:58 |
| `struct ip_vs_conn` | include/net/ip_vs.h:813 | `cport` :818, `dport` :821, `caddr` :839, `vaddr` :840, `daddr` :843, `vport` :845, `packet_xmit` :877 |
| `struct ip_vs_service` | include/net/ip_vs.h:933 | `scheduler` :953, `vport` :1010, `vaddr` :1011 |
| `ip_vs_rr` ops `.name = "rr"` | ip_vs_rr.c:101 | |
| `ip_vs_wrr` ops `.name = "wrr"` | ip_vs_wrr.c:239 | |
| `ip_vs_notrack` | include/net/ip_vs.h:2127 | |
| `ip_vs_update_conntrack` | net/netfilter/ipvs/ip_vs_nfct.c:70 | decl include/net/ip_vs.h:2153, no-op stub :2168 |

### ip_vs_ops4[] — full (net/netfilter/ipvs/ip_vs_core.c:2325–2372)
```c
// net/netfilter/ipvs/ip_vs_core.c:2325-2372
static const struct nf_hook_ops ip_vs_ops4[] = {
	/* After packet filtering, change source only for VS/NAT */
	{
		.hook		= ip_vs_out_hook,
		.pf		= NFPROTO_IPV4,
		.hooknum	= NF_INET_LOCAL_IN,
		.priority	= NF_IP_PRI_NAT_SRC - 2,
	},
	/* After packet filtering, forward packet through VS/DR, VS/TUN,
	 * or VS/NAT(change destination), so that filtering rules can be
	 * applied to IPVS. */
	{
		.hook		= ip_vs_in_hook,
		.pf		= NFPROTO_IPV4,
		.hooknum	= NF_INET_LOCAL_IN,
		.priority	= NF_IP_PRI_NAT_SRC - 1,
	},
	/* Before ip_vs_in, change source only for VS/NAT */
	{
		.hook		= ip_vs_out_hook,
		.pf		= NFPROTO_IPV4,
		.hooknum	= NF_INET_LOCAL_OUT,
		.priority	= NF_IP_PRI_NAT_DST + 1,
	},
	/* After mangle, schedule and forward local requests */
	{
		.hook		= ip_vs_in_hook,
		.pf		= NFPROTO_IPV4,
		.hooknum	= NF_INET_LOCAL_OUT,
		.priority	= NF_IP_PRI_NAT_DST + 2,
	},
	/* After packet filtering (but before ip_vs_out_icmp), catch icmp
	 * destined for 0.0.0.0/0, which is for incoming IPVS connections */
	{
		.hook		= ip_vs_forward_icmp,
		.pf		= NFPROTO_IPV4,
		.hooknum	= NF_INET_FORWARD,
		.priority	= 99,
	},
	/* After packet filtering, change source only for VS/NAT */
	{
		.hook		= ip_vs_out_hook,
		.pf		= NFPROTO_IPV4,
		.hooknum	= NF_INET_FORWARD,
		.priority	= 100,
	},
};
```
Priorities relative to NAT: the *reply/SNAT* hook sits at `NF_IP_PRI_NAT_SRC - 2` (:2331), just **before** the in-hook at `NF_IP_PRI_NAT_SRC - 1` (:2340), so both run ahead of conntrack's SNAT at `NAT_SRC` in LOCAL_IN. On LOCAL_OUT, IPVS runs **after** conntrack DNAT: `NF_IP_PRI_NAT_DST + 1` (:2347) for out/SNAT and `+ 2` (:2354) for in/schedule. `ip_vs_ops6[]` (:2374) mirrors this with `NF_IP6_PRI_NAT_SRC`/`NF_IP6_PRI_NAT_DST` at :2380, :2389, :2396, :2403 and FORWARD 99/100 at :2411/:2418.

### ip_vs_in_hook — lookup / schedule / packet_xmit
```c
// net/netfilter/ipvs/ip_vs_core.c:2176-2183
	/*
	 * Check if the packet belongs to an existing connection entry
	 */
	cp = INDIRECT_CALL_1(pp->conn_in_get, ip_vs_conn_in_get_proto,
			     ipvs, af, skb, &iph);

	if (!iph.fragoffs && is_new_conn(skb, &iph) && cp) {
		int conn_reuse_mode = sysctl_conn_reuse_mode(ipvs);
```
```c
// net/netfilter/ipvs/ip_vs_core.c:2243-2260
	if (unlikely(!cp)) {
		int v;

		if (!ip_vs_try_to_schedule(ipvs, af, skb, pd, &v, &cp, &iph))
			return v;
	}

	IP_VS_DBG_PKT(11, af, pp, skb, iph.off, "Incoming packet");

	ip_vs_in_stats(cp, skb);
	ip_vs_set_state(cp, IP_VS_DIR_INPUT, skb, pd, iph.len);
	if (cp->packet_xmit)
		ret = cp->packet_xmit(skb, cp, pp, &iph);
		/* do not touch skb anymore */
	else {
		IP_VS_DBG_RL("warning: packet_xmit is null");
		ret = NF_ACCEPT;
	}
```
`ip_vs_try_to_schedule` is the `pp->conn_schedule` indirection:
```c
// net/netfilter/ipvs/ip_vs_core.c:1658-1663
	if (!cp) {
		...
		if (!pp->conn_schedule(ipvs, af, skb, pd, verdict, cpp, iph))
```

### ip_vs_out_hook — reply direction / SNAT back
```c
// net/netfilter/ipvs/ip_vs_core.c:1579-1597
	cp = INDIRECT_CALL_1(pp->conn_out_get, ip_vs_conn_out_get_proto,
			     ipvs, af, skb, &iph);

	if (likely(cp))
		return handle_response(af, skb, pd, cp, &iph, hooknum);

	/* Check for real-server-started requests */
	if (atomic_read(&ipvs->conn_out_counter)) {
		...
			cp = __ip_vs_rs_conn_out(hooknum, ipvs, af, skb, &iph);
			if (cp)
				return handle_response(af, skb, pd, cp, &iph,
						       hooknum);
```
`handle_response` is at ip_vs_core.c:1439; it does the reverse mangle (`pp->snat_handler`) and `ip_vs_route_me_harder(cp->ipvs, af, skb, hooknum)` at :1483.

### ip_vs_schedule — sched->schedule + ip_vs_conn_new (net/netfilter/ipvs/ip_vs_core.c:619)
```c
// net/netfilter/ipvs/ip_vs_core.c:703-728
	sched = rcu_dereference(svc->scheduler);
	if (sched) {
		/* read svc->sched_data after svc->scheduler */
		smp_rmb();
		dest = sched->schedule(svc, skb, iph);
	} else {
		dest = NULL;
	}
	if (dest == NULL) {
		IP_VS_DBG(1, "Schedule: no dest found.\n");
		return NULL;
	}
	...
	{
		struct ip_vs_conn_param p;

		ip_vs_conn_fill_param(svc->ipvs, svc->af, iph->protocol,
				      caddr, cport, vaddr, vport, &p);
		cp = ip_vs_conn_new(&p, dest->af, &dest->addr,
				    dest->port ? dest->port : vport,
				    flags, dest, skb->mark);
```

### ip_vs_nat_xmit — the DNAT (net/netfilter/ipvs/ip_vs_xmit.c:787)
```c
// net/netfilter/ipvs/ip_vs_xmit.c:839-860
	/* copy-on-write the packet before mangling it */
	if (skb_ensure_writable(skb, sizeof(struct iphdr)))
		goto tx_error;

	if (skb_cow(skb, rt->dst.dev->hard_header_len))
		goto tx_error;

	/* mangle the packet */
	if (pp->dnat_handler && !pp->dnat_handler(skb, pp, cp, ipvsh))
		goto tx_error;
	ip_hdr(skb)->daddr = cp->daddr.ip;
	ip_send_check(ip_hdr(skb));

	IP_VS_DBG_PKT(10, AF_INET, pp, skb, ipvsh->off, "After DNAT");
	...
	/* Another hack: avoid icmp_send in ip_fragment */
	skb->ignore_df = 1;

	rc = ip_vs_nat_send_or_cont(NFPROTO_IPV4, skb, cp, local);
```

### ip_vs_nat_send_or_cont / ip_vs_send_or_cont
```c
// net/netfilter/ipvs/ip_vs_xmit.c:665-693
/* return NF_STOLEN (sent) or NF_ACCEPT if local=1 (not sent) */
static inline int ip_vs_nat_send_or_cont(int pf, struct sk_buff *skb,
					 struct ip_vs_conn *cp, int local)
{
	int ret = NF_STOLEN;

	skb->ipvs_property = 1;
	if (likely(!(cp->flags & IP_VS_CONN_F_NFCT)))
		ip_vs_notrack(skb);
	else
		ip_vs_update_conntrack(skb, cp, 1);
	...
	if (!local) {
		skb_forward_csum(skb);
		if (skb->dev)
			skb_clear_tstamp(skb);
		NF_HOOK(pf, NF_INET_LOCAL_OUT, cp->ipvs->net, NULL, skb,
			NULL, skb_dst(skb)->dev, dst_output);
	} else
		ret = NF_ACCEPT;

	return ret;
}
```
```c
// net/netfilter/ipvs/ip_vs_xmit.c:695-714
/* return NF_STOLEN (sent) or NF_ACCEPT if local=1 (not sent) */
static inline int ip_vs_send_or_cont(int pf, struct sk_buff *skb,
				     struct ip_vs_conn *cp, int local)
{
	int ret = NF_STOLEN;

	skb->ipvs_property = 1;
	if (likely(!(cp->flags & IP_VS_CONN_F_NFCT)))
		ip_vs_notrack(skb);
	if (!local) {
		ip_vs_drop_early_demux_sk(skb);
		skb_forward_csum(skb);
		if (skb->dev)
			skb_clear_tstamp(skb);
		NF_HOOK(pf, NF_INET_LOCAL_OUT, cp->ipvs->net, NULL, skb,
			NULL, skb_dst(skb)->dev, dst_output);
	} else
		ret = NF_ACCEPT;
	return ret;
}
```

### ip_vs_dr_xmit — no DNAT, just route out (net/netfilter/ipvs/ip_vs_xmit.c:1439)
```c
// net/netfilter/ipvs/ip_vs_xmit.c:1439-1460
ip_vs_dr_xmit(struct sk_buff *skb, struct ip_vs_conn *cp,
	      struct ip_vs_protocol *pp, struct ip_vs_iphdr *ipvsh)
{
	int local;

	local = __ip_vs_get_out_rt(cp->ipvs, cp->af, skb, cp->dest, cp->daddr.ip,
				   IP_VS_RT_MODE_LOCAL |
				   IP_VS_RT_MODE_NON_LOCAL |
				   IP_VS_RT_MODE_KNOWN_NH, NULL, ipvsh);
	if (local < 0)
		goto tx_error;
	if (local)
		return ip_vs_send_or_cont(NFPROTO_IPV4, skb, cp, 1);

	ip_send_check(ip_hdr(skb));

	/* Another hack: avoid icmp_send in ip_fragment */
	skb->ignore_df = 1;

	ip_vs_send_or_cont(NFPROTO_IPV4, skb, cp, 0);

	return NF_STOLEN;
```
No IP-header rewrite at all — the destination IP stays the VIP and only the L2 next hop changes (`IP_VS_RT_MODE_KNOWN_NH`, :1447).

### ip_vs_tunnel_xmit — IPIP/GUE/GRE encap (one anchor)
```c
// net/netfilter/ipvs/ip_vs_xmit.c:1147-1152
ip_vs_tunnel_xmit(struct sk_buff *skb, struct ip_vs_conn *cp,
		  struct ip_vs_protocol *pp, struct ip_vs_iphdr *ipvsh)
{
	struct netns_ipvs *ipvs = cp->ipvs;
	struct net *net = ipvs->net;
	struct rtable *rt;			/* Route to the other host */
```

### IPVS ↔ conntrack
- `ip_vs_notrack()` — `include/net/ip_vs.h:2127`: attaches the untracked conntrack template so IPVS-handled packets bypass nf_conntrack; called from `ip_vs_nat_send_or_cont` (ip_vs_xmit.c:673) and `ip_vs_send_or_cont` (ip_vs_xmit.c:704), i.e. whenever the conn does **not** carry `IP_VS_CONN_F_NFCT`.
- `ip_vs_update_conntrack()` — `net/netfilter/ipvs/ip_vs_nfct.c:70`: for `IP_VS_CONN_F_NFCT` connections it rewrites the conntrack tuple so the real-server address/port is visible to conntrack/NAT instead of the VIP; called from `ip_vs_nat_send_or_cont` (ip_vs_xmit.c:675) with `outin=1`.

---

### Summary of names that changed between the reader's expectations and v7.2
1. `veth_napi_add` → `veth_napi_enable_range` (drivers/net/veth.c:1218).
2. veth's skb→xdp_buff conversion no longer uses `pskb_expand_head`; it is `veth_convert_skb_to_xdp_buff` (:751) using `skb_pp_cow_data` (:761 / net/core/skbuff.c:942).
3. `br_handle_frame`'s inline `NF_HOOK(NF_BR_PRE_ROUTING, …)` → `nf_hook_bridge_pre()` (net/bridge/br_input.c:267), called at :441.
4. `skb->protocol = eth_type_trans()` + `skb_postpull_rcsum()` moved from `____dev_forward_skb` to `__dev_forward_skb2` (net/core/dev.c:2438).
5. bonding has no `slave_list`; slaves are `bond_slave_list(bond)` = `&bond->dev->adj_list.lower` (include/net/bonding.h:54).
6. VRF: `vrf_rx_stats` → `dev_dstats_rx_add` (drivers/net/vrf.c:1360); v4 receive uses `PACKET_LOOPBACK` (not `IFF_LOOPBACK`) and has no `vrf_ip_input_dst`; outbound flow uses `fl4.flowi4_l3mdev` (:506).
7. ipvlan has no `ipvlan_init_port`; it is `ipvlan_port_create` (drivers/net/ipvlan/ipvlan_main.c:62).
8. IPVS: single `ip_vs_ops[]` → `ip_vs_ops4[]`/`ip_vs_ops6[]` (ip_vs_core.c:2325/:2374); the four `*4` hook wrappers → `ip_vs_in_hook` (:2097) / `ip_vs_out_hook` (:1510).
9. macvlan's xmit tail is `dev_queue_xmit_accel` (drivers/net/macvlan.c:571), not `dev_queue_xmit`.