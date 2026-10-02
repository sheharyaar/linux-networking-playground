# Chapter 2 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1)

Everything here comes from the rootless bench in `labs/common/qnet.sh` (bottleneck `netem rate 10mbit`
on `r1` in the rtr namespace, 20 ms delay each way, offloads off). No sudo was used.

## Poisson arrivals into the bottleneck (`md1-sweep.sh`, Diagram 2.2)

Built with `qnet.sh --limit 1000`, so nothing was dropped (the `lost` column is 0 everywhere).
Each load ran 30 s, except fixed 0.95, which ran 60 s.

    ./md1-sweep.sh --seconds 30 0.1 0.3 0.5 0.7 0.8 0.9
    ./md1-sweep.sh --seconds 60 0.95
    ./md1-sweep.sh --sizes exp --seconds 30 0.3 0.5 0.7 0.8 0.9
    ./md1-sweep.sh --batch 10 --seconds 30 0.5 0.8

- `sweep-fixed.csv`: 1514-byte frames (M/D/1), one row per load, written by `summarise.py`.
- `sweep-exp.csv`: frames of 62 bytes plus an exponential part (mean 400 B), capped at 1514
  (M/G/1, service-time c² about 0.64).
- `sweep-fixed-b10.csv`: 1514-byte frames sent ten at a time per Poisson arrival (Problem 3.43).
- `packets/<label>.csv.gz`: per-packet logs from `poisson.py recv` (seq, send_ns, recv_ns,
  frame_bytes; both clocks CLOCK_REALTIME). Kept for the fixed sweep and exp-0.9; the rest were
  dropped to keep the folder small. The scripts write these as `out/<label>.csv`.
- `backlog/<label>-q.csv`: `qwatch.py --dev r1 --every 0.02` during each run (written as
  `out/<label>-q.csv`).

Columns of the sweep files: `rho` is the measured load (lambda times mean service time);
`Wq_ms` is the mean wait before service, measured as one-way delay minus the frame's own
transmission time minus the smallest such value in the run (`base_ms`, the 20 ms path plus the
stack); `pk_Wq_ms` and `mm1_Wq_ms` are the P-K and M/M/1 predictions for single-packet arrivals
(for the batch runs, `pk_Wq_ms` is the single-packet value; the batch formula is on the page);
`T_ms` is `Wq_ms` plus the mean service time; `N_backlog` is the time-averaged backlog from
`qwatch.py` while packets were leaving, and `lambda_T` is Little's prediction for it. Every
column skips the run's first second.

## Window held fixed (`wsweep.sh`, Diagram 2.3)

`qnet.sh` defaults (limit 50), one fresh bench per window, `flow.py send --cc reno --seconds 8`,
summary over the last 5 s.

    ./wsweep.sh            # W = 5 10 15 20 25 30 33 36 40 50 60 70 80, then 0 (no cap)

- `wsweep.csv`: one row per window (`none` = uncapped Reno). `littles_inflight` is packets per
  second times the mean RTT.
- `window/w<W>.csv` and `window/w-uncapped.csv`: `flow.py`'s TCP_INFO samples for each run
  (written as `out/w<W>.csv`, and `out/w0.csv` for the uncapped run).

## netem try-it

- `netem-tryit.txt`: the output of the netem card's try-it block, as shown on the page.
