# Maglev chapter lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

Machine: AMD Ryzen 7 8845HS laptop, shared with other builders' runs, so the two build times
below are rough. Nothing here needed sudo, Docker or the network.

- `maglev-sweep-n100.csv`: Maglev against a plain mod-N table, N = 100 backends, Cilium's ten
  table sizes M = 251 ... 131071, k = 1 or 3 backends removed, 20 random tables per row
  (random offset and skip per backend, `random.Random(13)`). Columns: slots per backend
  (min, max), the percent of the table that changed owner among backends that stayed
  (`maglev_extra_pct`), the percent that changed at all (`maglev_total_pct`), and the same
  "extra" measure for the mod-N table. The table view of Diagram 13.4's lines.
- `maglev-fig12.csv`: the paper's Fig. 12 setting (p. 11): N = 1000, M = 65537 with k = 1 ... 30
  removed (20 tables each) and M = 655373 with k = 1, 10, 20, 30 (3 tables each). Both counts,
  so you can see that only `maglev_extra_pct` matches the figure. The table in the chapter's
  learning on what moves.
  Both CSVs come from `maglev_lab.py`, a longer version of the Python lab's solution; its code is
  in `notes/chapters/ch13.md` (solutions stay off this folder).
- `python-lab-run.txt`: `maglev_starter.py` with the two TODOs filled as in the page's solution,
  then the one-line Fig. 12 point (1% of 1000 backends removed, M = 65537, 5 tables): 2.36%.
- `cilium-go-test.txt`: `go/run-go.sh`, the fork's own `go test ./pkg/maglev/` (fork
  v1.19.6-vpc.25, HEAD 8ab00248bc), offline from its vendor/ directory.
- `cilium-go-lab.txt`: `go/run-go.sh lab`, the chapter's probe `go/ch13_lab_test.go` compiled into
  the fork's `pkg/maglev` through `go test -overlay` (nothing copied into the fork; the script
  checks `git status` afterwards). Cilium's own `GetLookupTable` at M = 16381 and the default
  seed, pod-like backends 10.244.x.y:8080/TCP with weight 100; percent of the table that moved
  among backends that stayed, mean and max over 20 random removals; build time (median of 7)
  and the builder's permutation scratch size. The crosses in Diagram 13.4.

Not here, because it was not run: the throwaway kind cluster in `cluster/` (needs Docker and
creates a cluster; the page marks it "not executed"). `cluster/compare.py` was checked only on
synthetic dumps built from random 3-backend tables of 251 slots.
