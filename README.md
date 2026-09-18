# linux-networking-playground

Visual dossiers and a reproducible lab bench for the Linux network stack.

- **[`packet-path-dossier.html`](packet-path-dossier.html)** — the life of one `sk_buff`, from a
  NIC ring to a socket and back out, through `lo`, unix sockets, veth, bridges, bonds, VRFs,
  macvlan, ipvlan, IPVS and Cilium. 17 chapters, ~41,000 words, 27 diagrams, every claim
  anchored to a `file:line` in Linux 7.2 and most of them to a real `pwru` transcript.
  Open it in a browser; it is a single self-contained file.
- **[`lab/`](lab/)** — the scripts that build every topology the dossier traces, with an `up`,
  `down` and `trace` action each, plus prerequisites and the commands for running them inside
  a kind node. Start with [`lab/README.md`](lab/README.md).

Two earlier dossiers in the same format live here as well: `sr-iov-dossier.html` and
`gpu-sharing-dossier.html`.
