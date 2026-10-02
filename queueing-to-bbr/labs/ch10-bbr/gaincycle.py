#!/usr/bin/env python3
"""gaincycle.py: one BBR flow against one FIFO bottleneck, packet by packet (a model, not Linux).
STARTER for the BBR chapter's "build a tiny one" lab: write the four functions marked "yours"
(about 20 lines: the two filters of Fig. 2, the gain cycle, and the pacer of Fig. 3). Everything
else, the bottleneck, the event loop, the states and the control, is given.

  python3 gaincycle.py [--rate 10] [--rtt 40] [--limit 50] [--seconds 20]
                       [--step 8:20 --step 14:10] [--every 0.005] [--csv out.csv]

The path is the bench's: a drop-tail FIFO of --limit packets drained at --rate Mbit/s
(1514-byte frames on the wire, 1448 bytes of payload), then --rtt ms back to the sender.
--step T:R changes the bottleneck to R Mbit/s at T seconds (the paper's Fig. 5).
The sender is BBR as the paper writes it: Fig. 2 on every ack, Fig. 3 on every send, the gains
of p. 62-63, ProbeRTT of pp. 63-64. Every --every seconds one CSV row is written.
"""
import argparse, csv, heapq, math, sys
from collections import deque

WIRE, MSS = 1514, 1448
STARTUP_G = 2 / math.log(2)                      # 2.885 (p. 63)
CYCLE = [1.25, 0.75, 1, 1, 1, 1, 1, 1]           # Fig. 4, p. 62

class Bottleneck:
    def __init__(s, mbps, rtt, limit):
        s.rate, s.rtt, s.limit = mbps * 1e6, rtt, limit
        s.departs = deque(); s.last = 0.0
    def queue(s, now):
        while s.departs and s.departs[0] <= now: s.departs.popleft()
        return len(s.departs)
    def arrive(s, now):                          # returns the ack time, or None if dropped
        if s.queue(now) >= s.limit: return None
        s.last = max(now, s.last) + WIRE * 8 / s.rate
        s.departs.append(s.last)
        return s.last + s.rtt

class BBR:
    def __init__(s, now, rtt0):
        s.delivered, s.delivered_time = 0, now
        s.inflight, s.cwnd, s.prior_cwnd = 0, 10, 10
        s.rtprop, s.rtprop_stamp = rtt0, now      # the handshake's RTT
        s.samples = {}                            # round -> best delivery rate in it (pkt/s)
        s.round, s.next_round = 0, 0
        s.state, s.full_bw, s.full_cnt = 'startup', 0.0, 0
        s.idx, s.cycle_stamp = 0, now
        s.probe_rtt_done = None
        s.pacing_rate = STARTUP_G * 10 / rtt0     # Linux: high_gain * init_cwnd / RTT
        s.next_send = now
        s.last_rtt = s.last_rate = s.srtt = 0.0
    def bdp(s): return s.btlbw() * s.rtprop       # packets
    def gains(s):                                 # (pacing_gain, cwnd_gain) per state
        return {'startup': (STARTUP_G, STARTUP_G), 'drain': (1 / STARTUP_G, STARTUP_G),
                'probe_bw': (CYCLE[s.idx], 2.0), 'probe_rtt': (1.0, 1.0)}[s.state]

    def on_ack(s, now, p):
        s.inflight -= 1
        round_start, expired = s.update_model(now, p)
        s.srtt += (s.last_rtt - s.srtt) / 8 if s.srtt else s.last_rtt   # TCP's smoothed RTT, for the log
        s.update_state(now, round_start, expired)
        s.update_control()

    # ---- part 1 of yours: the two filters (Fig. 2, p. 60; estimators p. 61) ----------------
    def btlbw(s):
        """BtlBw: the largest delivery rate in s.samples from the last 10 rounds, in packets/s."""
        raise NotImplementedError('part 1: btlbw()')

    def update_model(s, now, p):
        """Feed this ack's RTT sample to the RTprop filter (a 10 s windowed min) and its
        delivery-rate sample to s.samples. Count packet-timed rounds. Return (round_start, expired)."""
        raise NotImplementedError('part 1: update_model()')

    # ---- part 2 of yours: the gain cycle (ProbeBW, p. 62) ----------------------------------
    def advance_cycle(s, now):
        """In ProbeBW, move to the next slot of CYCLE once the current one has lasted one RTprop."""
        raise NotImplementedError('part 2: advance_cycle()')

    # ---- part 3 of yours: the pacer (Fig. 3, p. 62) -----------------------------------------
    def on_send(s, now):
        """One packet leaves now. Set s.next_send from s.pacing_rate (packets/s) and return the
        per-packet record that on_ack() reads back: sendtime, delivered, delivered_time."""
        raise NotImplementedError('part 3: on_send()')

    # ---- given: the states (pp. 62-64) and the control (Fig. 3; cwnd_gain p. 61) ----------
    def update_state(s, now, round_start, expired):
        bw = s.btlbw()
        if s.state == 'startup' and round_start:  # leave after 3 rounds with under 25% growth
            if bw >= 1.25 * s.full_bw: s.full_bw, s.full_cnt = bw, 0
            else: s.full_cnt += 1
            if s.full_cnt >= 3: s.state = 'drain'
        if s.state == 'drain' and s.inflight <= s.bdp():
            s.state, s.idx, s.cycle_stamp = 'probe_bw', 2, now
        if s.state == 'probe_bw':
            s.advance_cycle(now)
        if expired and s.state != 'probe_rtt':    # RTprop not lowered for 10 s
            s.prior_cwnd, s.state, s.probe_rtt_done = s.cwnd, 'probe_rtt', None
        if s.state == 'probe_rtt':                # 4 packets for max(200 ms, one round)
            if s.probe_rtt_done is None and s.inflight <= 4:
                s.probe_rtt_done, s.probe_rtt_round = now + 0.2, s.round
            elif s.probe_rtt_done is not None and now > s.probe_rtt_done and s.round > s.probe_rtt_round:
                s.rtprop_stamp, s.cwnd = now, max(s.cwnd, s.prior_cwnd)
                s.state = 'probe_bw' if s.full_cnt >= 3 else 'startup'
                s.idx, s.cycle_stamp = 2, now

    def update_control(s):
        pg, cg = s.gains(); full = s.full_cnt >= 3
        rate = pg * s.btlbw() * 0.99              # Linux paces 1% under (tcp_bbr.c:148)
        if full or rate > s.pacing_rate: s.pacing_rate = rate   # Startup only speeds up
        target = max(cg * s.bdp(), 4)
        if full: s.cwnd = min(s.cwnd + 1, target)
        elif s.cwnd < target or s.delivered < 10: s.cwnd += 1
        if s.state == 'probe_rtt': s.cwnd = min(s.cwnd, 4)

    def on_loss(s):                               # Linux deducts lost packets from cwnd
        s.inflight -= 1; s.cwnd = max(s.cwnd - 1, 4)

    def can_send(s, now): return s.inflight < s.cwnd and now >= s.next_send

def run(a):
    path = Bottleneck(a.rate, a.rtt / 1000, a.limit)
    rtt0 = a.rtt / 1000 + WIRE * 8 / (a.rate * 1e6)
    bbr = BBR(0.0, rtt0)
    steps = sorted((float(t), float(r)) for t, r in (x.split(':') for x in a.step))
    ev = []; n = 0; rows = []; t_log = 0.0; drops = 0; timer = None
    def push(t, kind, p=None):
        nonlocal n; n += 1; heapq.heappush(ev, (t, n, kind, p))
    def try_send(now):                            # Fig. 3: one packet per pacing slot, under cwnd
        nonlocal timer, drops
        if bbr.inflight >= bbr.cwnd: return       # wait for an ack
        if now < bbr.next_send:
            if timer is None: timer = bbr.next_send; push(timer, 'send')
            return
        pkt = bbr.on_send(now); t_ack = path.arrive(now)
        if t_ack is None: drops += 1; push(now + path.rtt + 0.002, 'lost')
        else: push(t_ack, 'ack', pkt)
        if timer is None: timer = bbr.next_send; push(timer, 'send')
    push(0.0, 'send')
    while ev:
        now, _, kind, p = heapq.heappop(ev)
        if now > a.seconds: break
        while steps and steps[0][0] <= now: path.rate = steps.pop(0)[1] * 1e6
        while t_log <= now:
            pg, cg = bbr.gains()
            rows.append({'t_s': f'{t_log:.3f}', 'state': bbr.state, 'pacing_gain': round(pg, 3),
                         'cwnd_gain': round(cg, 3), 'link_mbps': path.rate / 1e6,
                         'btlbw_mbps': round(bbr.btlbw() * MSS * 8 / 1e6, 3),
                         'rtprop_ms': round(bbr.rtprop * 1e3, 2), 'cwnd': round(bbr.cwnd, 1),
                         'inflight': bbr.inflight, 'queue': path.queue(t_log),
                         'rtt_ms': round(bbr.last_rtt * 1e3, 2), 'srtt_ms': round(bbr.srtt * 1e3, 2),
                         'delivery_mbps': round(bbr.last_rate * MSS * 8 / 1e6, 3), 'drops': drops})
            t_log += a.every
        if kind == 'send': timer = None
        elif kind == 'ack': bbr.on_ack(now, p)
        elif kind == 'lost': bbr.on_loss()
        try_send(now)
    out = open(a.csv, 'w', newline='') if a.csv else sys.stdout
    w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'gaincycle: {a.seconds} s, {bbr.delivered} packets delivered = '
          f'{bbr.delivered * MSS * 8 / a.seconds / 1e6:.2f} Mbit/s, {drops} dropped, rows={len(rows)}',
          file=sys.stderr)

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--rate', type=float, default=10); p.add_argument('--rtt', type=float, default=40)
p.add_argument('--limit', type=int, default=50); p.add_argument('--seconds', type=float, default=20)
p.add_argument('--step', action='append', default=[]); p.add_argument('--every', type=float, default=0.005)
p.add_argument('--csv')
run(p.parse_args())
