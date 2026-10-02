# Verified references — CUDA / ISA layers (agent fetch, 2026-10-02). CUDA 13.4 U1, PTX ISA 9.4, Programming Guide v13.4.2.

PG = https://docs.nvidia.com/cuda/cuda-programming-guide/  (old cuda-c-programming-guide/ redirects only from index.html)
- PG 02-basics/writing-cuda-kernels.html#thread-hierarchy — Writing SIMT Kernels; #basics-of-simt; #thread-block-synchronization; #gpu-device-memory-spaces; #distributed-shared-memory
- PG 01-introduction/programming-model.html#thread-blocks-and-grids; #warps-and-simt; #gpu-memory; #thread-block-clusters
- PG 03-advanced/advanced-kernel-programming.html#simt-execution-model; #hardware-multithreading; #independent-thread-scheduling
- PG 02-basics/asynchronous-execution.html#cuda-streams; #cuda-events; #introduction-to-cuda-graphs-with-stream-capture
- PG 04-special-topics/cuda-graphs.html (#stream-capture, #graph-instantiation)
- PG 04-special-topics/unified-memory.html
- PG 04-special-topics/lazy-loading.html#lazy-loading
- PG 05-appendices/compute-capabilities.html#features-and-technical-specifications
- PG 05-appendices/cpp-language-extensions.html#warp-shuffle-functions; #warp-vote-functions; #thread-block-cluster
- PG 05-appendices/device-callable-apis.html#sm-id-and-warp-id — "%smid and %warpid are defined as volatile values"
- PG 01-introduction/cuda-platform.html#ptx-compatibility; #cubins-and-fatbins; #binary-compatibility — JIT + compute cache quotes
- PG 03-advanced/driver-api.html#module; #context
- PG 05-appendices/environment-variables.html#jit-compilation (#cuda-cache-path, #cuda-cache-maxsize, #cuda-force-ptx-jit-and-cuda-force-jit)
- Best Practices: https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html #coalesced-access-to-global-memory #shared-memory-and-memory-banks #occupancy #pinned-memory
- NVCC: https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html #the-cuda-compilation-trajectory #virtual-architectures #fatbinaries #gpu-code-generation-in-cuda #keep-keep
- Binary utilities: https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html #cuobjdump #nvdisasm #instruction-set-reference #nvidia-ampere-gpu-and-ada-instruction-set #hopper-instruction-set (no Volta/Pascal anchors in 13.x)
- PTX ISA 9.4: https://docs.nvidia.com/cuda/parallel-thread-execution/index.html #state-spaces #special-registers #special-registers-globaltimer #special-registers-smid #special-registers-warpid #memory-consistency-model #scope #parallel-synchronization-and-communication-instructions-membar #parallel-synchronization-and-communication-instructions-atom #asynchronous-warpgroup-level-matrix-instructions #data-movement-and-conversion-instructions-cp-async-bulk #parallel-synchronization-and-communication-instructions-mbarrier
  - %globaltimer: "A predefined, 64-bit global nanosecond timer." + tools-oriented, "may change or be removed", unspecified under JIT to other targets.
  - %smid: "may change during execution, e.g. due to rescheduling of threads following preemption".
- Inline PTX: https://docs.nvidia.com/cuda/inline-ptx-assembly/
- Runtime API: https://docs.nvidia.com/cuda/cuda-runtime-api/index.html (group__CUDART__STREAM.html, group__CUDART__GRAPH.html, group__CUDART__MEMORY.html)
- Driver API: https://docs.nvidia.com/cuda/cuda-driver-api/index.html ; group__CUDA__MODULE.html ; group__CUDA__LIBRARY.html
- Compatibility: https://docs.nvidia.com/deploy/cuda-compatibility/latest/
- Release notes current: https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/ ; 13.0: https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html#deprecated-architectures — "Offline compilation and library support for these architectures have been removed in CUDA Toolkit 13.0 … Toolkits through the 12.x series … will continue to be supported"
- PTX Compiler API: https://docs.nvidia.com/cuda/ptx-compiler-api/index.html
- cuBLAS: https://docs.nvidia.com/cuda/cublas/index.html
- Hopper tuning: https://docs.nvidia.com/cuda/hopper-tuning-guide/index.html (#tensor-memory-accelerator #thread-block-clusters); Ada tuning: https://docs.nvidia.com/cuda/ada-tuning-guide/index.html

Blogs (developer.nvidia.com/blog/…): even-easier-introduction-cuda ("An Even Easier Introduction to CUDA (Updated)"); using-cuda-warp-level-primitives; how-access-global-memory-efficiently-cuda-c-kernels; using-shared-memory-cuda-cc; how-overlap-data-transfers-cuda-cc; how-optimize-data-transfers-cuda-cc; cuda-graphs ("Getting Started with CUDA Graphs"); unified-memory-cuda-beginners; cuda-pro-tip-write-flexible-kernels-grid-stride-loops; cooperative-groups; cuda-refresher-cuda-programming-model; cuda-pro-tip-understand-fat-binaries-jit-caching; nvidia-hopper-architecture-in-depth; cutlass-3-x-orthogonal-reusable-and-composable-abstractions-for-gemm-kernel-design
- Volta whitepaper: https://images.nvidia.com/content/volta-architecture/pdf/volta-architecture-whitepaper.pdf ("Inside Volta" blog not verifiable)
- https://research.colfax-intl.com/tutorial-hopper-tma/ — CUTLASS Tutorial: Mastering the NVIDIA® Tensor Memory Accelerator (TMA)
- https://pytorch.org/blog/hopper-tma-unit/ — Deep Dive on the Hopper TMA Unit for FP8 GEMMs
- Legacy warp intrinsics: deprecated in CUDA 9 (archive 9.0 PG #warp-shuffle-functions); absent from current docs.

LLVM: https://llvm.org/docs/CompileCudaWithLLVM.html (--offload-arch=sm_XX, best-effort with newer CUDA + warning); https://llvm.org/docs/NVPTXUsage.html. Clang 22: CUDA 12.8 full, 12.9 partial, newer = warn and proceed.
