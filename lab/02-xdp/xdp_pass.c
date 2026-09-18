/* Lab 2 — the smallest XDP program that does something visible: count frames, pass them all.
 * Build:  clang -O2 -g -target bpf -c xdp_pass.c -o xdp_pass.o
 * Attach: ip link set dev DEV xdp obj xdp_pass.o sec xdp          (native, if the driver supports it)
 *         ip link set dev DEV xdpgeneric obj xdp_pass.o sec xdp   (generic, any device)
 * Detach: ip link set dev DEV xdp off
 * Count:  bpftool map dump name xdp_count
 */
#include <linux/bpf.h>
#include <linux/types.h>

#define SEC(name) __attribute__((section(name), used))
static void *(*bpf_map_lookup_elem)(void *map, const void *key) = (void *)BPF_FUNC_map_lookup_elem;

struct {
	int (*type)[BPF_MAP_TYPE_ARRAY];
	int (*max_entries)[1];
	__u32 *key;
	__u64 *value;
} xdp_count SEC(".maps");

SEC("xdp")
int xdp_pass_prog(struct xdp_md *ctx)
{
	__u32 k = 0;
	__u64 *v = bpf_map_lookup_elem(&xdp_count, &k);
	if (v)
		__sync_fetch_and_add(v, 1);
	return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
