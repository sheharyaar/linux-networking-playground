// GPU probe for ../matvec.cu: when did each row of matvec_warp start and
// finish, and on which SM? One warp computes one row, so lane 0 of each warp
// records for its row. Loaded by matvec_tail.c under bpftime.
#define BPF_NO_GLOBAL_DATA
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#define BPF_MAP_TYPE_GPU_ARRAY_MAP 1503 // bpftime: one copy, in device memory
#define ROWS 4096			// d in ../matvec.cu

static const u64 (*bpf_get_globaltimer)(void) = (void *)502;
static const u64 (*bpf_get_block_idx)(u64 *x, u64 *y, u64 *z) = (void *)503;
static const u64 (*bpf_get_block_dim)(u64 *x, u64 *y, u64 *z) = (void *)504;
static const u64 (*bpf_get_thread_idx)(u64 *x, u64 *y, u64 *z) = (void *)505;
static const u64 (*bpf_get_sm_id)(void) = (void *)509;

struct row_times {
	u64 start_ns;
	u64 end_ns;
	u32 start_sm;
	u32 end_sm;
};

// A GPU array map: a lookup is address arithmetic on the GPU, with no request
// to the host, so the probe stays cheap.
struct {
	__uint(type, BPF_MAP_TYPE_GPU_ARRAY_MAP);   // 1503: one copy, in device memory
	__uint(max_entries, ROWS);
	__type(key, u32);
	__type(value, struct row_times);
} rows SEC(".maps");

// Row of this thread's warp, as matvec_warp computes it. Only lane 0 of each
// warp gets a row; the other 31 lanes return -1 and do nothing.
static __always_inline int lane0_row(u32 *row)
{
	u64 bx, by, bz, dx, dy, dz, tx, ty, tz;

	bpf_get_thread_idx(&tx, &ty, &tz);
	if (tx & 31)
		return -1;
	bpf_get_block_idx(&bx, &by, &bz);
	bpf_get_block_dim(&dx, &dy, &dz);
	u64 r = (bx * dx + tx) / 32;
	if (r >= ROWS)
		return -1;
	*row = r;
	return 0;
}

SEC("kprobe/_Z11matvec_warpPKfS0_Pfii")
int matvec_warp_entry()
{
	u32 row;
	struct row_times *t;

	if (lane0_row(&row))         // lanes 1 to 31 stop here
		return 0;
	t = bpf_map_lookup_elem(&rows, &row);
	if (!t)
		return 0;
	t->start_ns = bpf_get_globaltimer();   // helper 502
	t->start_sm = bpf_get_sm_id();         // helper 509
	return 0;
}

SEC("kretprobe/_Z11matvec_warpPKfS0_Pfii")
int matvec_warp_exit()
{
	u32 row;
	struct row_times *t;

	if (lane0_row(&row))
		return 0;
	t = bpf_map_lookup_elem(&rows, &row);
	if (!t)
		return 0;
	t->end_ns = bpf_get_globaltimer();
	t->end_sm = bpf_get_sm_id();
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
