// Loader for matvec_tail.bpf.c. Run it under bpftime's syscall server, run
// ../out/matvec_shared under bpftime's agent, then press Ctrl-C here. It reads
// the last launch of matvec_warp back and prints its waves and its tail.
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "matvec_tail.skel.h"

#define ROWS 4096
#define BUCKETS 20

struct row_times {
	__u64 start_ns;
	__u64 end_ns;
	__u32 start_sm;
	__u32 end_sm;
};

static volatile sig_atomic_t stop;
static void on_sigint(int sig) { stop = 1; }

static int cmp_u64(const void *a, const void *b)
{
	__u64 x = *(const __u64 *)a, y = *(const __u64 *)b;
	return x < y ? -1 : x > y;
}

int main(void)
{
	static struct row_times t[ROWS];
	static __u64 ends[ROWS];
	struct matvec_tail_bpf *skel;
	__u64 t0 = ~0ULL, t1 = 0;
	int n = 0, moved = 0, rows_on_sm[256] = { 0 };

	skel = matvec_tail_bpf__open_and_load();
	if (!skel || matvec_tail_bpf__attach(skel)) {
		fprintf(stderr, "failed to load or attach\n");
		return 1;
	}
	signal(SIGINT, on_sigint);
	printf("attached; run the target, then press Ctrl-C\n");
	while (!stop)
		sleep(1);

	int fd = bpf_map__fd(skel->maps.rows);
	for (__u32 r = 0; r < ROWS; r++) {
		if (bpf_map_lookup_elem(fd, &r, &t[r]) || !t[r].end_ns)
			continue;
		if (t[r].start_ns < t0)
			t0 = t[r].start_ns;
		if (t[r].end_ns > t1)
			t1 = t[r].end_ns;
		ends[n++] = t[r].end_ns;
		moved += t[r].start_sm != t[r].end_sm;
		rows_on_sm[t[r].end_sm & 255]++;
	}
	if (!n) {
		printf("no rows recorded\n");
		return 1;
	}
	qsort(ends, n, sizeof(ends[0]), cmp_u64);
	double span = (t1 - t0) / 1e3;
	printf("rows recorded: %d, kernel span %.1f us\n", n, span);
	printf("90%% of rows done at %.1f us; the last 10%% took %.1f us more\n",
	       (ends[n * 9 / 10] - t0) / 1e3, (t1 - ends[n * 9 / 10]) / 1e3);
	printf("rows whose warp ended on a different SM: %d\n", moved);

	// Waves show up as clusters of start times.
	int hist[BUCKETS] = { 0 };
	for (__u32 r = 0; r < ROWS; r++)
		if (t[r].end_ns) {
			int b = (int)((t[r].start_ns - t0) * BUCKETS / (t1 - t0 + 1));
			hist[b < BUCKETS ? b : BUCKETS - 1]++;
		}
	printf("row start times, %d buckets of %.1f us:\n", BUCKETS, span / BUCKETS);
	for (int b = 0; b < BUCKETS; b++) {
		printf("%6.1f us %5d ", b * span / BUCKETS, hist[b]);
		for (int i = 0; i < hist[b] / 16; i++)
			putchar('#');
		putchar('\n');
	}
	printf("rows per SM:");
	for (int s = 0; s < 256; s++)
		if (rows_on_sm[s])
			printf(" %d:%d", s, rows_on_sm[s]);
	putchar('\n');
	matvec_tail_bpf__destroy(skel);
	return 0;
}
