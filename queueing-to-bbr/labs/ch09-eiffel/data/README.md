# Eiffel chapter lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

Machine: AMD Ryzen 7 8845HS laptop, shared with other builders' runs during the measurements,
so treat differences under about 20% as noise. Nothing here needed sudo.

- `race-vs-packets.csv`: `./race.sh` (C, `cc -O2 -march=native`), 20,000 buckets (the paper's
  kernel queue, p. 26), 3 to 1,000,000 packets kept queued. Columns: N buckets, n packets,
  queue (heap, wheel, scan, cffs), ns per pop+push (fastest of three 0.2 s runs), and words,
  slots or comparisons touched per pop+push. The table view of Diagram 9.2.
- `race-vs-buckets.csv`: the same race with 1,000 and then 10 packets queued, 1,024 to
  4,194,304 buckets. Quoted in the chapter notes, not plotted.
- `ffsq-python.txt`: the Python lab's solution (`ffsq.py`, kept out of this folder; the code is
  in the page's solution toggle) at six sizes: words per push and pop against heapq comparisons,
  then time per push+pop.
- `bpf-fq-build.txt`: `./build-bpf-fq.sh ~/workspace/repos/linux` as a normal user (tree at v7.2),
  and the BPF listing clang 22 produces for one `__builtin_ctzll`.

Not here, because it needs sudo: registering `bpf_qdisc_fq.bpf.o` with `bpftool struct_ops
register` and attaching `bpf_fq` in the bench (the last step of the BPF qdisc lab, marked "not executed").
