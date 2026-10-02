# Chapter 6 lab data (the author's runs, 2026-10-02, kernel 7.2.6-arch2-1, rootless)

Every run comes from `../run.sh` through `../../common/qnet.sh`, with its defaults unless the
name says otherwise:

- bottleneck `netem rate 10mbit limit 21` on `rtr:r1`, no delay (a 21-packet drop-tail buffer,
  a quarter of the 85-packet pipe);
- `netem delay 20ms` on `rtr:r0` and on `rcv:c0` (both on the ack path; RTT 40 ms);
- `s0` qdisc: `pfifo limit 10000` (nothing paces) or `fq` (fq paces every flow);
- sender route `initcwnd 1`, TCP MSS 536 (576-byte IP packets, 590-byte frames), Reno, SACK on,
  `tcp_pacing_ss_ratio=200`, `tcp_pacing_ca_ratio=120`;
- eight flows started together by `flow.py --flows 8`.

The machine was shared with other builders' runs; at 10 Mbit/s that does not change the results.

## Eight flows started together, 15 s each (five runs per condition)

- `bulk-summary-b21.txt`: `epochs.py --table` over the five runs of each condition at the
  21-packet buffer: means, with the range in brackets. Conditions: `none` (pfifo), `fq`,
  `timer` (pfifo, all flows set `SO_MAX_PACING_RATE` 1 Gbit/s, so TCP's own timer paces),
  `fq100` (fq with both pacing ratios at 100, the paper's rate), `none-nosack` and `fq-nosack`
  (`net.ipv4.tcp_sack=0`).
- `bulk-summary-b85.txt`: the same for `none-b85` and `fq-b85` (buffer of one pipe, 85 packets;
  epoch window 90 ms).
- `bulk-runs-b21.csv`, `bulk-runs-b85.csv`: one row per run (first_n = flows lost in the first
  congestion epoch, first_t = its time, peak = largest sum of windows before 1.5 s, agg_mean and
  agg_cv = mean and std/mean of the summed windows after 3 s, late_half = % of epochs after 3 s in
  which half or more of the flows lost together, gp_2s and gp_all = goodput in Mbit/s).
- `none-1-f.csv`, `fq-1-f.csv`: the per-flow `TCP_INFO` samples (every 10 ms) of run 1 of each,
  the source of Diagram 6.2. `none-1-agg.csv`, `fq-1-agg.csv`: their summed windows and the number
  of flows in recovery per sample. `none-1-q.csv`, `fq-1-q.csv`: `qwatch.py` on `rtr:r1`.
  `none-1-r1.txt`, `fq-1-s0.txt`: `tc -s` at the end (router drops; fq's throttled counters).

## One flow (10 s)

- `one-none-1-f.csv`, `one-fq-1-f.csv` and their `-q.csv`: one Reno flow, pfifo and fq. First drop
  in the round 32→64 unpaced (34 drops in slow start, ssthresh 51) and 64→128 paced (74 drops,
  ssthresh 86); both later peak at 106 = pipe + buffer.

## Paced and unpaced flows in the same run (pfifo, so only flows with SO_MAX_PACING_RATE pace)

- `mixed-300-runs.csv`, `mixed-300-summary.txt`: eight flows of 300 packets (157,200 bytes, the
  paper's Fig. 14 size) started together, with 0, 1, 2, 4, 6, 7 or 8 of them paced by TCP's own
  timer; 24 runs per point; `mix300r100-k4` is 4 of 8 with both ratios at 100.
- `mixed-bulk-runs.csv`, `mixed-bulk-summary.txt`: the same mixes with 15 s bulk flows, 4 runs per
  point; goodput per flow.

## Other transcripts

- `ss-tin-pfifo-8flows.txt`: `ss -tin` six seconds into an eight-flow pfifo run: every unpaced
  socket prints a `pacing_rate`. The `tc -s` of pfifo follows it.
- `wrongturn-netem-delay-limit21.txt`, `wrongturn-f.csv`: the lab's common wrong turn, the buffer
  built as `netem delay 20ms rate 10mbit limit 21` on `rtr:r1`: one flow ran at 2.49 Mbit/s.
- `runs-transcript.txt`: the one-line summary `flow.py send` printed at the end of every run in
  the batches above (bytes acked, goodput, Jain's index, retransmissions).
