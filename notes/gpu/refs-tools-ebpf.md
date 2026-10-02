# Verified references — TOOLS and EBPF layers (agent fetch, 2026-10-02)

## Tools
- https://docs.nvidia.com/nsight-systems/UserGuide/index.html — Nsight Systems User Guide (2026.5). --cuda-graph-trace=graph (default, whole graphs) vs node (per-node, overhead). --trace=cuda is HW trace by default on Blackwell+.
- https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html — Nsight Compute Profiling Guide (2026.3.1). Anchors: #metrics-structure, #sections-and-rules (Speed Of Light, Occupancy, Roofline charts), #statistical-sampler (warp scheduler states / stall reasons).
- https://developer.nvidia.com/tools-overview/nsight-compute/get-started-2026_1 — supported archs: Turing, Ampere, Ada, Hopper, Blackwell. Volta dropped.
- https://docs.nvidia.com/nsight-compute/ReleaseNotes/index.html — 2020.1 "Removed support for the Pascal SM 6.x GPU architecture".
- https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html — CUDA 13.0: nvprof + Visual Profiler removed; offline compilation and library support for Maxwell, Pascal, Volta removed.
- https://docs.nvidia.com/cuda/profiler-users-guide/index.html — nvprof (12.9 doc): Volta last fully supported; no cc 8.0+.
- https://forums.developer.nvidia.com/t/announcement-cuda-nvprof-and-visual-profiler-are-deprecated/358159
- https://docs.nvidia.com/cupti/index.html — CUPTI (Activity, Callback, PC sampling, PM sampling, Range profiler). Pascal PC-sampling support UNVERIFIED.
- https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html — memcheck, racecheck, initcheck, synccheck.
- https://docs.nvidia.com/cuda/cuda-gdb/index.html — CUDA-GDB 13.4; sm_75 floor.
- https://github.com/NVIDIA/NVTX
- https://docs.nvidia.com/deploy/nvml-api/index.html
- https://docs.nvidia.com/datacenter/dcgm/latest/index.html
- https://github.com/NVlabs/NVBit — SM 3.5–12.1, CUDA >= 12.0; release 1.8.1.
- NVBit paper: Villa, Stephenson, Nellans, Keckler, MICRO-52 2019, https://doi.org/10.1145/3352460.3358307 ; PDF https://d1qx31qr3h6wln.cloudfront.net/publications/MICRO_2019_NVBit.pdf — "dynamic recompilation at the SASS level".

## bpftime / eBPF
- https://eunomia.dev/bpftime/documents/gpu/ — Write and Run eBPF on GPU with bpftime. Docs list helpers 501–506 only; source at a900f85 has 507–511 (threadscheduling README documents 509 sm_id, 510 warp_id, 511 lane_id).
- https://github.com/eunomia-bpf/bpftime — bpftime: Userspace eBPF Runtime (MIT).
- https://www.usenix.org/conference/osdi25/presentation/zheng-yusheng — "Extending Applications Safely and Efficiently" (Zheng, Yu, Yang, Hu, Lai, Williams, Quinn; OSDI '25). PDF https://www.usenix.org/system/files/osdi25-zheng-yusheng.pdf. Table 3: uprobe ~2561 ns kernel vs ~190 ns bpftime (re-check in PDF).
- https://arxiv.org/abs/2311.07923 — bpftime: userspace eBPF Runtime for Uprobe, Syscall and Kernel-User Interactions (2023).
- eGPU: Extending eBPF Programmability and Observability to GPUs (Yang, Yu, Zheng, Quinn; HCDS '25) — DOI 10.1145/3723851.3726984 (UNVERIFIED by fetch; name only).
- https://github.com/eunomia-bpf/llvmbpf — Userspace eBPF VM with LLVM JIT/AOT Compiler; documents PTX + SPIR-V output.
- https://frida.re/docs/javascript-api/ — Interceptor attach (onEnter/onLeave) vs replace.
- https://github.com/frida/frida-gum
- https://github.com/vbpf/ebpf-verifier — PREVAIL.
- https://pldi19.sigplan.org/details/pldi-2019-papers/44/Simple-and-Precise-Static-Analysis-of-Untrusted-Linux-Kernel-Extensions — PREVAIL paper (PLDI 2019).
- https://eunomia.dev/tutorials/47-cuda-events/ — eBPF Tutorial: Tracing CUDA GPU Operations (uprobes on libcudart).
- https://eunomia.dev/tutorials/xpu/flamegraph/ — GPU flamegraph with CUPTI + eBPF.
- https://www.yunwei37.com/blog/gpu-observability-challenges — The GPU Observability Gap (Oct 2025).
- https://arxiv.org/abs/2512.12615 — gpu_ext: Extensible OS Policies for GPUs via eBPF (Dec 2025).
- https://lpc.events/event/19/contributions/2168/ — Extending eBPF to GPU Device and Driver Contexts (LPC 2025).

## Added while writing ch10 (2026-10-02)
- NVML utilization: /opt/cuda/targets/x86_64-linux/include/nvml.h:241–247 — gpu = "Percent of time over the past sample period during which one or more kernels was executing on the GPU"; sample period 1 s to 1/6 s by product.
- ncu CLI https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html — --clock-control default **boost** (values base/boost/force-boost/none/reset); --cache-control default **all** (flush before each replay pass).
- Profiling Guide #kernel-replay: all memory the kernel can access saved before pass 1; written subset restored before each later pass; caches not restored. Range replay avoids per-kernel serialisation.
- Nsight Systems release notes https://docs.nvidia.com/nsight-systems/ReleaseNotes/index.html — "versions, starting with 2025.4 do not provide support for Pascal or Volta architectures"; use an older version. GPU Metrics need Turing+ (User Guide #gpu-metrics).
- DCGM field IDs (latest names): 1002 DCGM_FI_PROF_SM_UTIL_RATIO (cycles an SM has ≥1 warp), 1003 DCGM_FI_PROF_SM_OCCUPANCY_RATIO, 1005 DCGM_FI_PROF_DRAM_UTIL_RATIO. https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html (older releases: DCGM_FI_PROF_SM_ACTIVE etc.)
- nvidia.ko 615.71.09 has local symbol nvidia_unlocked_ioctl (nm on the dkms module).
