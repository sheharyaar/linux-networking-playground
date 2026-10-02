#!/usr/bin/env python3
"""epochs.py: loss epochs, synchronization and fairness from chapter-6 flow.py CSVs.

  python3 epochs.py run-f.csv [--window 0.06] [--start 3] [--bin 1.0] [--agg agg.csv]
  python3 epochs.py --table none-*-f.csv fq-*-f.csv [--runs-csv runs.csv]
                                  (the mean per condition, and with --runs-csv one row per run)

A flow's loss event is a sample where its ca_state turns to recovery or loss (an RTO) after
being open, disorder or cwr. Loss events are grouped into congestion epochs: an epoch opens at
the first event not yet grouped and takes every event less than --window seconds after it
(default 60 ms: one RTT on the bench with a full 21-packet queue, 40 + 10 ms, plus 10 ms).
A flow counts once per epoch.

For one run it prints:
  first epoch       how many of the N flows lost in the first congestion epoch, and when
  peak              the largest sum of the N windows (packets) before 1.5 s, and the smallest
                    sum in the second after that peak
  sum after start   mean of the summed windows after --start, and its swing (standard deviation
                    over mean): flows in step make the sum swing more
  steady state      for epochs after --start seconds: number of epochs, mean flows per epoch,
                    and the share of epochs in which at least half of the flows lost together
  RTOs              loss events that were retransmit timeouts (ca_state loss)
  goodput           aggregate payload Mbit/s over the whole run, the first 2 s, and after --start
  Jain              Jain's index of per-flow bytes over the whole run, and the mean of the index
                    over --bin second windows after --start (short-term fairness)
With --agg it writes t_s, the sum of the windows and the number of flows in recovery or loss at
each sample, for plotting. --window is the only knob that changes the epoch counts; the run's
condition name is the file name up to the last "-N-f.csv".
"""
import argparse, collections, csv, re

def jain(x):
    s = sum(x); q = sum(v * v for v in x)
    return s * s / (len(x) * q) if q else float('nan')

def analyse(path, window, start, binw, agg=None):
    rows = list(csv.DictReader(open(path)))
    by = collections.defaultdict(list)
    for r in rows:
        by[int(r['flow'])].append(r)
    N = len(by)
    events = []
    for k, rs in by.items():
        prev = 'open'
        for r in rs:
            st = r['ca_state']
            if st in ('recovery', 'loss') and prev not in ('recovery', 'loss'):
                events.append((float(r['t_s']), k, st))
            prev = st
    events.sort()
    epochs = []
    for t, k, kind in events:
        if epochs and t - epochs[-1]['t'] < window:
            epochs[-1]['flows'].add(k); epochs[-1]['rto'] += kind == 'loss'
        else:
            epochs.append({'t': t, 'flows': {k}, 'rto': int(kind == 'loss')})
    tmax = max(float(r['t_s']) for r in rows)
    def acked_at(rs, t):
        v = 0
        for r in rs:
            if float(r['t_s']) > t: break
            v = int(r['bytes_acked'])
        return v
    ks = sorted(by)
    final = [int(by[k][-1]['bytes_acked']) for k in ks]
    first2 = [acked_at(by[k], 2.0) for k in ks]
    atstart = [acked_at(by[k], start) for k in ks]
    wins = []
    t = start
    while t + binw <= tmax:
        x = [acked_at(by[k], t + binw) - acked_at(by[k], t) for k in ks]
        if sum(x): wins.append(jain(x))
        t += binw
    ts = collections.OrderedDict()
    for r in rows:
        d = ts.setdefault(float(r['t_s']), [0, 0])
        d[0] += int(r['cwnd']); d[1] += r['ca_state'] in ('recovery', 'loss')
    early = [(t, c) for t, (c, n) in ts.items() if t < 1.5]
    tp, peak = max(early, key=lambda x: x[1])
    after = [c for t, (c, n) in ts.items() if tp < t <= tp + 1.0]
    st = [c for t, (c, n) in ts.items() if t >= start]
    smean = sum(st) / len(st); ssd = (sum((c - smean) ** 2 for c in st) / len(st)) ** 0.5
    late = [e for e in epochs if e['t'] >= start]
    res = dict(file=path, N=N, events=len(events), epochs=len(epochs),
               rtos=sum(e['rto'] for e in epochs),
               first_t=epochs[0]['t'] if epochs else float('nan'),
               first_n=len(epochs[0]['flows']) if epochs else 0,
               first_rto=epochs[0]['rto'] if epochs else 0,
               first_missed=sorted(set(ks) - epochs[0]['flows']) if epochs else ks,
               peak=peak, peak_t=tp, trough=min(after) if after else float('nan'),
               agg_mean=smean, agg_cv=ssd / smean,
               late_epochs=len(late),
               late_mean=sum(len(e['flows']) for e in late) / len(late) if late else float('nan'),
               late_half=100 * sum(len(e['flows']) * 2 >= N for e in late) / len(late) if late else float('nan'),
               gp_all=sum(final) * 8 / tmax / 1e6, gp_2s=sum(first2) * 8 / 2 / 1e6,
               gp_late=(sum(final) - sum(atstart)) * 8 / (tmax - start) / 1e6,
               jain=jain(final), jain_win=sum(wins) / len(wins) if wins else float('nan'),
               retrans=sum(int(by[k][-1]['total_retrans']) for k in ks))
    if agg:
        with open(agg, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['t_s', 'agg_cwnd', 'flows_in_recovery'])
            for t, (c, n) in ts.items(): w.writerow([f'{t:.3f}', c, n])
    return res

def report(r, start, binw):
    print(f'{r["file"]}: {r["N"]} flows, {r["events"]} loss events in {r["epochs"]} epochs '
          f'({r["rtos"]} of the events were RTOs)')
    print(f'  first epoch at {r["first_t"]:.3f} s: {r["first_n"]} of {r["N"]} flows lost '
          f'({r["first_rto"]} RTOs); flows that lost later: {r["first_missed"]}')
    print(f'  peak: windows summed to {r["peak"]} packets at {r["peak_t"]:.2f} s, '
          f'lowest sum in the next second {r["trough"]}')
    print(f'  sum of windows after {start:g} s: mean {r["agg_mean"]:.1f} packets, swing (std/mean) {r["agg_cv"]:.3f}')
    print(f'  after {start:g} s: {r["late_epochs"]} epochs, mean {r["late_mean"]:.2f} flows per epoch, '
          f'{r["late_half"]:.0f}% of epochs with half or more of the flows')
    print(f'  goodput: all {r["gp_all"]:.2f} Mbit/s, first 2 s {r["gp_2s"]:.2f}, after {start:g} s {r["gp_late"]:.2f}')
    print(f'  Jain: whole run {r["jain"]:.3f}, mean over {binw:g} s windows after {start:g} s {r["jain_win"]:.3f}')

COLS = [('first_n', 'first epoch: flows', '{:.1f}'), ('peak', 'peak sum', '{:.0f}'), ('trough', 'trough', '{:.0f}'), ('agg_mean', 'sum after 3 s', '{:.1f}'), ('agg_cv', 'swing', '{:.3f}'),
        ('rtos', 'RTOs', '{:.1f}'), ('gp_2s', 'Mbit/s 0-2 s', '{:.2f}'), ('gp_all', 'Mbit/s all', '{:.2f}'),
        ('late_mean', 'flows/epoch', '{:.2f}'), ('late_half', '% epochs half+', '{:.0f}'),
        ('jain', 'Jain', '{:.3f}'), ('jain_win', 'Jain 1 s', '{:.3f}'), ('retrans', 'retrans', '{:.0f}')]

def table(results):
    groups = collections.OrderedDict()
    for r in results:
        groups.setdefault(re.sub(r'-\d+-f\.csv$', '', r['file'].split('/')[-1]), []).append(r)
    head = ['condition', 'runs'] + [c[1] for c in COLS]
    print(' | '.join(head))
    for g, rs in groups.items():
        cells = [g, str(len(rs))]
        for k, _, fmt in COLS:
            v = [r[k] for r in rs]
            cells.append(fmt.format(sum(v) / len(v)) + (f' ({fmt.format(min(v))}-{fmt.format(max(v))})' if len(rs) > 1 else ''))
        print(' | '.join(cells))

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('csv', nargs='+'); p.add_argument('--window', type=float, default=0.06)
p.add_argument('--start', type=float, default=3.0); p.add_argument('--bin', type=float, default=1.0)
p.add_argument('--agg'); p.add_argument('--table', action='store_true')
p.add_argument('--runs-csv', help='with several files: also write one row per run to this CSV')
a = p.parse_args()
res = [analyse(f, a.window, a.start, a.bin, a.agg if len(a.csv) == 1 else None) for f in a.csv]
if a.table or len(res) > 1:
    table(res)
    if a.runs_csv:
        keys = ['file'] + [k for k, _, _ in COLS] + ['epochs', 'late_epochs', 'first_t', 'peak_t']
        with open(a.runs_csv, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['run'] + keys[1:])
            for r in res:
                w.writerow([r['file'].split('/')[-1].replace('-f.csv', '')] +
                           [round(r[k], 3) if isinstance(r[k], float) else r[k] for k in keys[1:]])
else:
    report(res[0], a.start, a.bin)
