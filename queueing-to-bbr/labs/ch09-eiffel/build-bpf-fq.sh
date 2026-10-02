#!/bin/bash
# build-bpf-fq.sh: compile the kernel's BPF fq qdisc (a selftest) without root.
#   ./build-bpf-fq.sh ~/workspace/repos/linux      # path to a kernel tree, v6.16 or later
# Writes vmlinux.h (from this kernel's BTF) and bpf_qdisc_fq.bpf.o into this folder,
# then lists the object's struct_ops sections. Loading it needs root: see the lab.
set -e
K=${1:?usage: $0 PATH_TO_KERNEL_TREE}
S=$K/tools/testing/selftests/bpf
cd "$(dirname "$0")"
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -Wno-missing-declarations \
      -I. -I"$S" -I"$S/libarena/include" -I"$S/progs" \
      -c "$S/progs/bpf_qdisc_fq.c" -o bpf_qdisc_fq.bpf.o
ls -l bpf_qdisc_fq.bpf.o
llvm-objdump -h bpf_qdisc_fq.bpf.o | grep -E 'struct_ops|\.maps|\.data'
