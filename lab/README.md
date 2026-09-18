# lab/ — the bench for the packet-path dossier

Every lab here belongs to a chapter of `packet-path-dossier.html`. Each shell script takes
one argument:

    ./NN-name.sh up      build the topology and print what it built
    ./NN-name.sh down    remove everything it built
    ./NN-name.sh trace   print the tracer command lines to run while you generate traffic

All scripts source `lib.sh` and name every object they create with a `pp-` prefix, so
`ip link show | grep pp-` and `ip netns list | grep pp-` tell you whether anything was left
behind. They build on dummy and veth devices, never on your real network card, so they are
safe to run on a laptop with a live connection. The exception is `12-macvlan-ipvlan.sh`,
which accepts `LOWER=<ifname>` if you deliberately want a real interface.

## Where each lab runs

"Host" means your own machine, as root. "Node" means inside a kind node via `docker exec`,
which is how the traces in the dossier were captured. "Cluster" means it only reads an
existing Kubernetes cluster.

| Lab | Chapter | Runs on | What it builds |
|---|---|---|---|
| `00-check.sh` | 0 | host or node | Read-only: kernel version, BTF, tool availability. Start here. |
| `02-xdp/xdp_pass.c` | 2 | host or node | The smallest XDP program; build and attach lines are in the file header. |
| `05-router.sh` | 4, 5 | host or node | Three namespaces `pp-c`/`pp-rt`/`pp-s`, with nftables, conntrack and a masquerade rule to toggle. |
| `06-gateway.sh` | 6 | host or node | Reuses the router topology for ARP resolution and a real qdisc. |
| `07-sockets.sh` | 7 | host or node | The socket as a file, the three TCP queues, UDP overflow. Uses the veth topology. |
| `08-lo-unix.sh` + `unix_pair.py` | 8 | host | Dummy device `pp-dummy0`, a local listener, and a unix socket pair. |
| `09-veth.sh` | 9 | host or node | `pp-a`/`pp-b` with one veth pair; the `ethtool -K` toggles that move the receive door. |
| `10-bridge.sh` | 10 | host or node | `pp-l`/`pp-br0`/`pp-r`; optionally `modprobe br_netfilter` for the second half. |
| `11-bond-vrf.sh` | 11 | host or node | `pp-bond0` over two veth slaves, and `pp-vrf` with table 10. |
| `12-macvlan-ipvlan.sh` | 12 | host or node | A macvlan and an ipvlan on two separate veth lower devices. |
| `13-ipvs.sh` | 13 | host | A virtual service over two real servers. Needs `ipvsadm`. |
| `14-cilium.sh` | 14, 15 | cluster | Read-only wrapper over `kubectl`, `cilium-dbg` and `pwru`. Changes nothing. |
| `15-kind-vxlan.yaml` | 15 | cluster | A throwaway cluster with VXLAN instead of Geneve. Create it yourself. |
| `15-kind-native.yaml` | 15 | cluster | A throwaway cluster with native routing and no tunnel. Create it yourself. |

## Prerequisites

Install nothing you do not need; each row says which labs want it.

| Tool | Arch package | Debian/Ubuntu package | Needed by |
|---|---|---|---|
| `ip`, `bridge`, `tc` | `iproute2` | `iproute2` | all of them |
| `ethtool` | `ethtool` | `ethtool` | 09 (the GRO and TSO toggles), 12 |
| `curl` | `curl` | `curl` | 05, 06, 08, 09, 10, 11, 12, 13 |
| `python3` | `python` | `python3` | 05, 07, 08, 13 (the test servers) |
| `nft` | `nftables` | `nftables` | 05, 06, 11 (the doubled-hook counter) |
| `conntrack` | `conntrack-tools` | `conntrack` | 05 |
| `ss`, `nstat` | `iproute2` | `iproute2` | 07 |
| `tcpdump` | `tcpdump` | `tcpdump` | 08 (the `-Q inout` split on `lo`) |
| `ipvsadm` | `ipvsadm` | `ipvsadm` | 13 only. Absent on the dossier's bench, which is why chapter 13's output is labelled expected. |
| `bpftrace` | `bpftrace` | `bpftrace` | 07, 08. Absent on the bench; those blocks are labelled expected. |
| `pwru` | not packaged, see below | not packaged | every `trace` action |
| `clang`, `llvm` | `clang` `llvm` | `clang` `llvm` | 02 only, to build the XDP object |
| `kubectl`, `docker`, `kind` | `kubectl` `docker` `kind` | as available | 14, 15 |

`pwru` is a single static binary from <https://github.com/cilium/pwru>. The dossier used
version 1.0.12. **That build has no `--filter-dst-ip` or `--filter-dst-port`**: filtering is a
pcap expression given as a positional argument, for example
`pwru --output-meta 'tcp and host 10.9.0.2 and port 80'`.

Kernel requirements: 5.3 or newer for `pwru`, 5.18 or newer for its faster multi-kprobe
backend, and `CONFIG_DEBUG_INFO_BTF=y`. `00-check.sh` tests all of this.

## Running the labs inside a kind node

This is how every trace in the dossier was captured. The node shares the host kernel, so
device modules autoload from the host and the traces are real.

    # copy the labs in (plain `docker cp lab ...` nests the directory, so copy lab/. instead)
    docker exec kind-worker rm -rf /root/lab
    docker cp lab/. kind-worker:/root/lab/

    # copy the tracer in (re-copy if the node was restarted)
    docker cp /usr/bin/pwru kind-worker:/usr/local/bin/pwru

    # then work inside the node, which is already root
    docker exec -it kind-worker bash -c 'cd /root/lab && ./09-veth.sh up'

Two things the node cannot do. It has no `ping`, `tcpdump`, `bpftool`, `bpftrace` or
`ipvsadm`, so use `curl` plus `python3 -m http.server`, or simply aim a `curl` at a closed
port: the SYN still crosses every device and is answered with a reset, which is enough to
trace the whole path. And sysctls that exist only in the initial namespace
(`netdev_budget`, `netdev_max_backlog`, `gro_normal_batch`) are invisible from inside it.

## Capturing a trace

`pwru` needs to be running before the traffic and to stop by itself, so the usual shape is:

    docker exec -d kind-worker timeout 40 /usr/local/bin/pwru \
        --kmods veth --output-meta 'tcp and host 10.9.0.2' > /tmp/t.txt
    sleep 18
    docker exec kind-worker ip netns exec pp-a curl -s --max-time 2 http://10.9.0.2:9099/
    sleep 20
    docker exec kind-worker cat /tmp/t.txt

Useful flags: `--kmods a,b` to probe module functions (`veth`, `bridge`, `bonding`, `vrf`,
`macvlan`, `ipvlan`, `geneve`, `ip_vs`) which are otherwise not probed at all;
`--filter-netns /run/netns/NAME`; `--filter-trace-tc` and `--filter-trace-xdp` to show BPF
program names; `--output-meta` and `--output-tuple`, both on by default.

Two traps worth knowing before you read output:

* Receive handlers are never printed. `br_handle_frame`, `bond_handle_frame`,
  `macvlan_handle_frame` and `ipvlan_handle_frame` all take `struct sk_buff **pskb`, so
  `pwru` has no skb argument to read. You see the function each one calls next instead.
* `pwru` run inside one kind node sees the **whole host kernel**, so the `NETNS` column
  contains every node and every pod, not just the one you ran it in. That is a feature: it
  is how chapter 15 follows one skb across two nodes.

## Cleaning up

    ./NN-name.sh down
    ip link show | grep pp-        # should print nothing
    ip netns list | grep pp-       # should print nothing

`11-bond-vrf.sh down` also flushes routing table 10. If you interrupted a lab midway, the
`down` action is safe to run on its own.
