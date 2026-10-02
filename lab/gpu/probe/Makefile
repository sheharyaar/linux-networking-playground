# Builds the probe and its loader with the system's clang, bpftool and libbpf.
# bpftime's own examples build libbpf from bpftime's submodule instead; see
# notes in ../README or the dossier's chapter 14.
BPFTIME ?= $(HOME)/workspace/repos/bpftime
VMLINUX_DIR := $(BPFTIME)/third_party/vmlinux/x86

all: matvec_tail

matvec_tail.bpf.o: matvec_tail.bpf.c
	clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I$(VMLINUX_DIR) -c $< -o $@

matvec_tail.skel.h: matvec_tail.bpf.o
	bpftool gen skeleton $< > $@

matvec_tail: matvec_tail.c matvec_tail.skel.h
	cc -g -O2 -Wall $< -lbpf -o $@

clean:
	rm -f matvec_tail matvec_tail.bpf.o matvec_tail.skel.h

.PHONY: all clean
