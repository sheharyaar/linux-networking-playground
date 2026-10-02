// SPDX-License-Identifier: GPL-2.0
/* edt_lab.bpf.c: Cilium's EDT rate limiter, cut down to one aggregate, for the bench's rtr:r1.
 *
 * The arithmetic is edt_sched_departure() from the reader's Cilium fork (v1.19.6-vpc,
 * bpf/lib/edt.h:64-115), line for line, minus three things this lab does not need:
 *   - the aggregate id (Cilium writes the pod's endpoint id into skb->queue_mapping in
 *     cil_from_container, bpf_lxc.c:2435/2442, and reads it back here; the bench has one pod),
 *   - the hash map of aggregates (cilium_throttle, edt.h:32-39); one array slot here,
 *   - the priority hack (edt.h:109-113).
 * Counters are added so `bpftool map dump name edt_state` shows what happened.
 *
 * Build (no sudo):  clang -O2 -g -target bpf -DRATE_BPS=1250000 -c edt_lab.bpf.c -o edt_lab.o
 * Load (sudo):      see load-edt.sh
 * RATE_BPS is bytes per second, as Cilium stores it (GetBytesPerSec(), bandwidth.go:158-164):
 * the annotation "10M" is 1,250,000.
 */
#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#ifndef RATE_BPS
#define RATE_BPS 1250000ULL                 /* "10M" */
#endif
#ifndef HORIZON_NS
#define HORIZON_NS 2000000000ULL            /* bwmap.DefaultDropHorizon, pkg/maps/bwmap/bwmap.go:28 */
#endif
#define NSEC_PER_SEC 1000000000ULL
#define READ_ONCE(x)     (*(volatile typeof(x) *)&(x))
#define WRITE_ONCE(x, v) (*(volatile typeof(x) *)&(x) = (v))

struct edt_state {
	__u64 t_last;                           /* edt.h:22 */
	__u64 passed;                           /* left with the stamp it came with (or none) */
	__u64 stamped;                          /* given a later departure time */
	__u64 horizon_drops;                    /* DROP_EDT_HORIZON */
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct edt_state);
} edt_state SEC(".maps");

SEC("tc")
int edt_sched_departure(struct __sk_buff *skb)
{
	__u64 delay, now, t, t_next;
	struct edt_state *info;
	__u32 key = 0;

	if (skb->protocol != bpf_htons(ETH_P_IP) && skb->protocol != bpf_htons(ETH_P_IPV6))
		return TC_ACT_OK;                   /* edt.h:71-75 */
	info = bpf_map_lookup_elem(&edt_state, &key);
	if (!info)
		return TC_ACT_OK;

	now = bpf_ktime_get_ns();               /* edt.h:89 */
	t = skb->tstamp;                        /* edt.h:90: TCP's own departure time, if any */
	if (t < now)
		t = now;
	delay = ((__u64)skb->wire_len) * NSEC_PER_SEC / RATE_BPS;   /* edt.h:93 */
	t_next = READ_ONCE(info->t_last) + delay;                   /* edt.h:94 */
	if (t_next <= t) {                      /* edt.h:95-98: under the rate, keep the packet's time */
		WRITE_ONCE(info->t_last, t);
		__sync_fetch_and_add(&info->passed, 1);
		return TC_ACT_OK;
	}
	if (t_next - now >= HORIZON_NS) {       /* edt.h:104-105 */
		__sync_fetch_and_add(&info->horizon_drops, 1);
		return TC_ACT_SHOT;
	}
	WRITE_ONCE(info->t_last, t_next);       /* edt.h:106 */
	skb->tstamp = t_next;                   /* edt.h:107: written without bpf_skb_set_tstamp() */
	__sync_fetch_and_add(&info->stamped, 1);
	return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
