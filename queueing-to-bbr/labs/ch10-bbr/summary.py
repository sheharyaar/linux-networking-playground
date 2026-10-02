#!/usr/bin/env python3
"""summary.py: summarise bench.sh runs (or a gaincycle.py CSV) for the BBR chapter.

  python3 summary.py data/cubic data/bbr        (prefixes written by bench.sh --out)
  python3 summary.py --sim sim.csv              (a gaincycle.py CSV)

For each run: goodput, retransmissions, RTT and bottleneck queue after the first 2 s, and for BBR
the state timeline (from the gains in TCP_CC_INFO), the ProbeRTT episodes, the pacing_gain
sequence over one second, and pacing_rate against 0.99 x pacing_gain x bw (tcp_bbr.c:245-262).
"""
import csv, statistics as st, sys

def pct(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p / 100 * len(xs)))]

def runs(f, key):
    out, prev = [], None
    for r in f:
        if r[key] != prev: out.append((float(r['t_s']), r[key])); prev = r[key]
    return out

def bench(prefix):
    f = list(csv.DictReader(open(prefix + '-f.csv')))
    q = list(csv.DictReader(open(prefix + '-q.csv')))
    late = [r for r in f if float(r['t_s']) > 2]
    ql = [int(r['backlog_pkts']) for r in q if float(r['t_s']) > 2]
    t_end = float(f[-1]['t_s'])
    rtt = [float(r['rtt_ms']) for r in late]; infl = [int(r['inflight']) for r in late]
    print(f'== {prefix}  cc={f[0]["cc"]}')
    print(f'goodput {int(f[-1]["bytes_acked"]) * 8 / t_end / 1e6:.2f} Mbit/s over {t_end:.1f} s, '
          f'retransmitted {f[-1]["total_retrans"]} segments')
    print(f'after 2 s: srtt median {st.median(rtt):.1f} ms (p95 {pct(rtt, 95):.1f}), minrtt {f[-1]["minrtt_ms"]} ms, '
          f'inflight median {st.median(infl):.0f}, bottleneck queue median {st.median(ql):.0f} max {max(ql)} packets')
    if not f[0]['state']:
        return
    tl = runs(f, 'state')
    print('states:', ' '.join(f'{t:.2f}s {s}' for t, s in tl if s != 'probe_bw' or True)[:400])
    prt = [(t, s) for t, s in tl if s == 'probe_rtt']
    for t, _ in prt:
        nxt = next((t2 for t2, s2 in tl if t2 > t), t_end)
        dip = [int(r['backlog_pkts']) for r in q if t <= float(r['t_s']) <= nxt + 0.05]
        print(f'  probe_rtt at {t:.2f} s for {(nxt - t) * 1000:.0f} ms; queue min during it {min(dip) if dip else "?"}')
    w = [r for r in f if 5.0 <= float(r['t_s']) < 6.0 and r['state'] == 'probe_bw']
    seq = runs(w, 'pacing_gain')
    print('pacing_gain from 5.0 s:', ' '.join(f'{float(g):g}@{t:.3f}' for t, g in seq))
    ratio = [float(r['pacing_mbps']) / (float(r['pacing_gain']) * float(r['bbr_bw_mbps']))
             for r in late if r['bbr_bw_mbps'] and float(r['bbr_bw_mbps']) > 0 and r['state'] == 'probe_bw']
    if ratio: print(f'pacing_rate / (pacing_gain x bw): median {st.median(ratio):.4f}')
    bws = [float(r['bbr_bw_mbps']) for r in late]; mr = [float(r['bbr_mrtt_ms']) for r in late]
    print(f'model: bw median {st.median(bws):.2f} Mbit/s, mrtt median {st.median(mr):.2f} ms, '
          f'BDP {st.median(bws) * 1e6 / 8 * st.median(mr) / 1e3 / 1448:.1f} segments; cwnd median '
          f'{st.median(int(r["cwnd"]) for r in late if r["state"] == "probe_bw"):.0f} in probe_bw')

def sim(path):
    f = list(csv.DictReader(open(path)))
    late = [r for r in f if float(r['t_s']) > 2]
    print(f'== {path} (model)')
    print('states:', ' '.join(f'{t:.2f}s {s}' for t, s in runs(f, 'state')))
    steady = [r for r in late if r['state'] == 'probe_bw']
    print(f'probe_bw: queue max {max(int(r["queue"]) for r in steady)}, RTT max '
          f'{max(float(r["rtt_ms"]) for r in steady):.1f} ms, btlbw {steady[-1]["btlbw_mbps"]} Mbit/s, '
          f'drops {f[-1]["drops"]}')
    links = runs(f, 'link_mbps')
    for t0, mbps in links[1:]:                    # a --step: btlbw at the end of each 0.75 slot after it
        ends = [r for prev, r in zip(f, f[1:]) if float(r['t_s']) > t0 and
                prev['pacing_gain'] == '0.75' and r['pacing_gain'] != '0.75'][:4]
        print(f'step to {float(mbps):g} Mbit/s at {t0:g} s: btlbw ' + ' -> '.join(
            f'{float(r["btlbw_mbps"]):.2f} ({float(r["t_s"]):.2f} s)' for r in ends))

args = sys.argv[1:]
if args[:1] == ['--sim']: sim(args[1])
else:
    for a in args: bench(a)
