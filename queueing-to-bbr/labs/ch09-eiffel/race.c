// race.c: the timing harness of the Eiffel chapter's rootless lab.
//
//   cc -O2 -march=native -o race race.c
//   ./race N n            # N buckets in the window, n packets kept queued
//
// It runs the "hold" model of a pacer: pop the packet with the smallest rank (its send
// time, in buckets), then push one new packet a random 1..N-1 buckets later, so the queue
// always holds n packets inside a window of N buckets that moves forward.
// Four queues race on the same random stream:
//   heap   a binary heap keyed by rank: O(log n) comparisons per operation
//   wheel  a timing wheel: N slots, scanned slot by slot from the cursor (no bitmap)
//   scan   the same wheel plus one bit per slot, scanned a 64-bit word at a time
//   cffs   two hierarchical find-first-set bitmaps, primary and secondary (Eiffel, pp. 21-22)
// It prints one CSV row per queue: N, n, queue, ns per pop+push, words or slots or
// comparisons touched per pop+push. It contains a reference FFS queue: write your own
// Python one first (ffsq_starter.py), then read this.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NIL 0xffffffffu
static uint64_t rs;
static inline uint64_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static uint64_t N, n;
static uint32_t *nxt;                 /* per packet: next packet in the same bucket */
static uint64_t *rk;                  /* per packet: its rank */
static uint64_t touch;                /* words, slots or comparisons touched */
static double now_ns(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1e9 + t.tv_nsec; }

/* ---- per-bucket FIFO lists, shared by wheel, scan and cffs ---- */
typedef struct { uint32_t *head, *tail; } fifo;
static void fifo_init(fifo *f, uint64_t nb) {
	f->head = malloc(nb * 4); f->tail = malloc(nb * 4);
	memset(f->head, 0xff, nb * 4);
}
static inline int fifo_push(fifo *f, uint64_t b, uint32_t id) {   /* returns 1 if the bucket was empty */
	nxt[id] = NIL;
	if (f->head[b] == NIL) { f->head[b] = f->tail[b] = id; return 1; }
	nxt[f->tail[b]] = id; f->tail[b] = id; return 0;
}
static inline uint32_t fifo_pop(fifo *f, uint64_t b, int *now_empty) {
	uint32_t id = f->head[b];
	f->head[b] = nxt[id];
	*now_empty = (f->head[b] == NIL);
	return id;
}

/* ---- heap ---- */
static uint64_t *hp; static uint64_t hn;
static void heap_push(uint32_t id) {
	uint64_t key = (rk[id] << 24) | id, i = hn++;
	while (i) { uint64_t p = (i - 1) / 2; touch++; if (hp[p] <= key) break; hp[i] = hp[p]; i = p; }
	hp[i] = key;
}
static uint32_t heap_pop(void) {
	uint64_t top = hp[0], key = hp[--hn], i = 0;
	for (;;) {
		uint64_t c = 2 * i + 1;
		if (c >= hn) break;
		if (c + 1 < hn) { touch++; if (hp[c + 1] < hp[c]) c++; }
		touch++; if (key <= hp[c]) break;
		hp[i] = hp[c]; i = c;
	}
	hp[i] = key;
	return (uint32_t)(top & 0xffffff);
}

/* ---- wheel: slot-by-slot scan from a cursor (a timing wheel with no bitmap) ---- */
static fifo wh; static uint64_t wcur;
static void wheel_push(uint32_t id) { fifo_push(&wh, rk[id] % N, id); }
static uint32_t wheel_pop(void) {
	int e;
	while (wh.head[wcur % N] == NIL) { wcur++; touch++; }
	touch++;
	return fifo_pop(&wh, wcur % N, &e);
}

/* ---- scan: the wheel plus one bit per slot, 64 slots per word read ---- */
static fifo sc; static uint64_t *sbits, swords, scur;
static void scan_push(uint32_t id) {
	uint64_t b = rk[id] % N;
	if (fifo_push(&sc, b, id)) sbits[b >> 6] |= 1ull << (b & 63);
	touch++;
}
static uint32_t scan_pop(void) {
	uint64_t p = scur % N, wi = p >> 6, w = sbits[wi] & (~0ull << (p & 63)), b;
	touch++;
	while (!w) { wi = (wi + 1 == swords) ? 0 : wi + 1; w = sbits[wi]; touch++; }
	b = (wi << 6) | __builtin_ctzll(w);
	scur += (b + N - p) % N;                         /* the cursor moves to the bucket found */
	int e; uint32_t id = fifo_pop(&sc, b, &e);
	if (e) { sbits[b >> 6] &= ~(1ull << (b & 63)); touch++; }
	return id;
}

/* ---- cffs: hierarchical FFS bitmaps, two of them (Eiffel's cFFS, pp. 21-22) ---- */
typedef struct { int L; uint64_t *lv[6]; fifo f; } hbm;
static void hbm_init(hbm *h, uint64_t nb) {
	uint64_t bits = nb; h->L = 0;
	for (;;) {
		uint64_t words = (bits + 63) / 64;
		h->lv[h->L++] = calloc(words, 8);
		if (words == 1) break;
		bits = words;
	}
	fifo_init(&h->f, nb);
}
static inline void hbm_set(hbm *h, uint64_t b) {         /* set the bit, then parents, until one was set */
	for (int k = 0; k < h->L; k++) {
		uint64_t i = b >> 6, old = h->lv[k][i];
		touch++;
		h->lv[k][i] = old | (1ull << (b & 63));
		if (old) break;
		b = i;
	}
}
static inline void hbm_clear(hbm *h, uint64_t b) {       /* clear the bit, then parents that empty */
	for (int k = 0; k < h->L; k++) {
		uint64_t i = b >> 6;
		touch++;
		if ((h->lv[k][i] &= ~(1ull << (b & 63)))) break;
		b = i;
	}
}
static inline int hbm_empty(hbm *h) { return h->lv[h->L - 1][0] == 0; }
static inline uint64_t hbm_min(hbm *h) {                 /* one word and one ctz per level, root first */
	uint64_t b = 0;
	for (int k = h->L - 1; k >= 0; k--) { touch++; b = (b << 6) | __builtin_ctzll(h->lv[k][b]); }
	return b;
}
static hbm qa, qb, *pri = &qa, *sec = &qb; static uint64_t hidx;   /* primary covers [hidx, hidx+N) */
static void cffs_push(uint32_t id) {
	uint64_t off = rk[id] - hidx; hbm *q = pri;
	if (off >= N) { q = sec; off -= N; if (off >= N) off = N - 1; }  /* beyond both: last bucket, unsorted */
	if (fifo_push(&q->f, off, id)) hbm_set(q, off);
}
static uint32_t cffs_pop(void) {
	touch++;
	if (hbm_empty(pri)) { hbm *t = pri; pri = sec; sec = t; hidx += N; touch++; }  /* swap the two pointers */
	uint64_t b = hbm_min(pri);
	int e; uint32_t id = fifo_pop(&pri->f, b, &e);
	if (e) hbm_clear(pri, b);
	return id;
}

/* ---- the race ---- */
typedef struct { const char *name; void (*push)(uint32_t); uint32_t (*pop)(void); } queue;
static void reset(void) {
	rs = 0x9e3779b97f4a7c15ull; hn = 0; wcur = scur = hidx = 0; touch = 0;
	memset(wh.head, 0xff, N * 4); memset(sc.head, 0xff, N * 4); memset(sbits, 0, swords * 8);
	hbm *hs[2] = { &qa, &qb };
	for (int j = 0; j < 2; j++) {
		uint64_t bits = N;
		for (int k = 0; k < hs[j]->L; k++) { uint64_t w = (bits + 63) / 64; memset(hs[j]->lv[k], 0, w * 8); bits = w; }
		memset(hs[j]->f.head, 0xff, N * 4);
	}
	pri = &qa; sec = &qb;
}
static void run(queue *q, double budget_ns) {
	double best = 1e18, tpo = 0;
	for (int rep = 0; rep < 3; rep++) {
		reset();
		for (uint64_t i = 0; i < n; i++) { rk[i] = rnd() % N; q->push((uint32_t)i); }
		for (uint64_t i = 0; i < 20000; i++) { uint32_t id = q->pop(); rk[id] += 1 + rnd() % (N - 1); q->push(id); }
		uint64_t ops = 0; touch = 0;
		double t0 = now_ns(), t1;
		do {
			for (int i = 0; i < 4096; i++) {
				uint32_t id = q->pop();
#ifdef CHECK
				static uint64_t last; if (ops == 0 && i == 0) last = 0;
				if (rk[id] < last) { fprintf(stderr, "%s: order broken\n", q->name); exit(2); }
				last = rk[id];
#endif
				rk[id] += 1 + rnd() % (N - 1); q->push(id);
			}
			ops += 4096; t1 = now_ns();
		} while (t1 - t0 < budget_ns);
		double ns = (t1 - t0) / ops;
		if (ns < best) { best = ns; tpo = (double)touch / ops; }
	}
	printf("%llu,%llu,%s,%.2f,%.2f\n", (unsigned long long)N, (unsigned long long)n, q->name, best, tpo);
}
int main(int argc, char **argv) {
	if (argc < 3) { fprintf(stderr, "usage: %s N n [only]\n", argv[0]); return 1; }
	N = strtoull(argv[1], 0, 10); n = strtoull(argv[2], 0, 10);
	if (N < 2 || n < 1 || n >= (1u << 24)) { fprintf(stderr, "need N >= 2 and 1 <= n < 2^24\n"); return 1; }
	nxt = malloc(n * 4); rk = malloc(n * 8); hp = malloc(n * 8);
	fifo_init(&wh, N); fifo_init(&sc, N);
	swords = (N + 63) / 64; sbits = calloc(swords, 8);
	hbm_init(&qa, N); hbm_init(&qb, N);
	queue qs[] = { { "heap", heap_push, heap_pop }, { "wheel", wheel_push, wheel_pop },
		       { "scan", scan_push, scan_pop }, { "cffs", cffs_push, cffs_pop } };
	for (unsigned i = 0; i < sizeof qs / sizeof qs[0]; i++)
		if (argc < 4 || !strcmp(argv[3], qs[i].name)) run(&qs[i], 2e8);
	return 0;
}
