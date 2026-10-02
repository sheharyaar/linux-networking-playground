// ch13_lab_test.go: the Maglev chapter's probe into Cilium's own table builder.
//
// It is never copied into the fork. run-go.sh hands it to `go test -overlay`, which
// compiles it as if it sat in pkg/maglev/ next to maglev.go, so it can call the same
// GetLookupTable the agent calls (pkg/loadbalancer/reconciler/bpf_reconciler.go,
// computeMaglevTable) and reuse the package's own test helpers.
//
// It prints, for Cilium's default M = 16381 and the default seed:
//   - entries per backend (the paper's floor/ceiling of M/N),
//   - the share of the table that changes owner when k backends leave, counting only
//     slots that did NOT belong to a removed backend (the "extra" moves),
//   - the time GetLookupTable takes (the machine is shared: treat it as a rough number).
package maglev

import (
	"fmt"
	"math/rand/v2"
	"net"
	"slices"
	"sort"
	"testing"
	"time"

	"github.com/cilium/hive/hivetest"
	"github.com/stretchr/testify/require"

	cmtypes "github.com/cilium/cilium/pkg/clustermesh/types"
	"github.com/cilium/cilium/pkg/loadbalancer"
)

// podBackends returns n backends that look like pods: 10.244.x.y:8080/TCP, weight 100
// (loadbalancer.DefaultBackendWeight, what the reconciler passes for a plain Service).
func podBackends(n int) []BackendInfo {
	out := make([]BackendInfo, n)
	for i := range out {
		ip := net.IPv4(10, 244, byte(i/200), byte(i%200+2)).To4()
		ac, _ := cmtypes.AddrClusterFromIP(ip)
		out[i] = BackendInfo{
			ID:     loadbalancer.BackendID(i + 1),
			Addr:   loadbalancer.NewL3n4Addr(loadbalancer.TCP, ac, 8080, 0),
			Weight: loadbalancer.DefaultBackendWeight,
		}
	}
	return out
}

func counts(table []loadbalancer.BackendID) (int, int) {
	c := map[loadbalancer.BackendID]int{}
	for _, id := range table {
		c[id]++
	}
	lo, hi := len(table), 0
	for _, v := range c {
		lo, hi = min(lo, v), max(hi, v)
	}
	return lo, hi
}

func TestCh13MaglevLab(t *testing.T) {
	const m = DefaultTableSize // 16381
	cfg, err := UserConfig{TableSize: m, HashSeed: DefaultHashSeed}.ToConfig()
	require.NoError(t, err)
	ml := New(cfg, hivetest.Lifecycle(t))

	fmt.Printf("Cilium pkg/maglev, M = %d, seed %s\n", m, DefaultHashSeed)

	// Equal weights of 100 take the weighted branch of computeLookupTable; it must give
	// exactly the table that weight 1 gives.
	w100 := podBackends(160)
	w1 := slices.Clone(w100)
	for i := range w1 {
		w1[i].Weight = 1
	}
	require.Equal(t, ml.GetLookupTable(slices.Values(w1)), ml.GetLookupTable(slices.Values(w100)))
	fmt.Println("weights 1 and 100 give the same table: yes")

	fmt.Println("N,M_over_N,min_entries,max_entries,k_removed,trials,extra_moved_pct_mean,extra_moved_pct_max")
	rng := rand.New(rand.NewPCG(13, 13))
	for _, n := range []int{3, 100, 160} {
		all := podBackends(n)
		before := ml.GetLookupTable(slices.Values(all))
		lo, hi := counts(before)
		for _, k := range []int{1, 2, 3, 5} {
			if k >= n {
				continue
			}
			trials := 20
			if n == 3 {
				trials = 3
			}
			sum, worst := 0.0, 0.0
			for range trials {
				dead := map[loadbalancer.BackendID]bool{}
				for _, i := range rng.Perm(n)[:k] {
					dead[all[i].ID] = true
				}
				var alive []BackendInfo
				for _, b := range all {
					if !dead[b.ID] {
						alive = append(alive, b)
					}
				}
				after := ml.GetLookupTable(slices.Values(alive))
				moved := 0
				for j := range before {
					if !dead[before[j]] && after[j] != before[j] {
						moved++
					}
				}
				pct := 100 * float64(moved) / float64(m)
				sum += pct
				worst = max(worst, pct)
			}
			fmt.Printf("%d,%.1f,%d,%d,%d,%d,%.3f,%.3f\n", n, float64(m)/float64(n), lo, hi, k, trials, sum/float64(trials), worst)
		}
	}

	// How long one table takes to build (median of 7). Shared machine: rough numbers.
	for _, c := range []struct{ n, m int }{{160, 16381}, {1000, 65521}} {
		cfg2, err := UserConfig{TableSize: uint(c.m), HashSeed: DefaultHashSeed}.ToConfig()
		require.NoError(t, err)
		ml2 := New(cfg2, hivetest.Lifecycle(t))
		bs := podBackends(c.n)
		var ds []time.Duration
		for range 7 {
			t0 := time.Now()
			ml2.GetLookupTable(slices.Values(bs))
			ds = append(ds, time.Since(t0))
		}
		sort.Slice(ds, func(i, j int) bool { return ds[i] < ds[j] })
		fmt.Printf("build time N=%d M=%d: median %v; permutation scratch %.1f MB; table %d bytes\n",
			c.n, c.m, ds[3].Round(10*time.Microsecond), float64(len(ml2.permutations)*8)/1e6, c.m*4)
	}
}
