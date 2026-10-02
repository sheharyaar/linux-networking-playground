#!/bin/bash
# race.sh: build race.c and run the two sweeps of the Eiffel chapter's rootless lab.
#   ./race.sh     writes race-vs-packets.csv and race-vs-buckets.csv here (the author's run is in data/)
# race-vs-packets: 20,000 buckets (the paper's kernel queue, p. 26), 3 to 1,000,000 packets queued.
# race-vs-buckets: 1,000 and then 10 packets queued, 1,024 to 4,194,304 buckets.
# Each point is the fastest of three 0.2 s runs per queue. The CPU is shared with whatever
# else runs on the machine, so treat differences under about 20% as noise.
set -e
cd "$(dirname "$0")"
cc -O2 -march=native -o race race.c
echo "N,n,queue,ns_per_op,touched_per_op" > race-vs-packets.csv
for n in 3 10 30 100 300 1000 3000 10000 30000 100000 300000 1000000; do ./race 20000 $n >> race-vs-packets.csv; done
echo "N,n,queue,ns_per_op,touched_per_op" > race-vs-buckets.csv
for n in 1000 10; do
  for N in 1024 4096 20000 65536 262144 1048576 4194304; do ./race $N $n >> race-vs-buckets.csv; done
done
column -s, -t race-vs-packets.csv; echo; column -s, -t race-vs-buckets.csv
