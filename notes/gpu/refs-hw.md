# Verified references and facts — HW layer (agent fetch, 2026-10-02)

## References
- Ada whitepaper: https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf — "NVIDIA ADA GPU ARCHITECTURE" v2.02 (AD102/103 only, not AD107)
- H100 whitepaper landing: https://resources.nvidia.com/en-us-hopper-architecture/nvidia-h100-tensor-c — "NVIDIA H100 Tensor Core GPU Architecture" V1.04; PDF https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf
- H100 datasheet: https://dam-cdn.nvd.orangelogic.com/AssetLink/mfj81tsm68n0ne632upmuvirso3ta3g3.pdf
- Hopper blog: https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/ (Andersch et al., 22 Mar 2022)
- P100 whitepaper: https://images.nvidia.com/content/pdf/tesla/whitepaper/pascal-architecture-whitepaper-v1.2.pdf
- GTX 1080 (GP104) whitepaper: https://international.download.nvidia.com/geforce-com/international/pdfs/GeForce_GTX_1080_Whitepaper_FINAL.pdf
- Volta whitepaper: https://images.nvidia.com/content/volta-architecture/pdf/volta-architecture-whitepaper.pdf (WP-08608-001_v1.1, Aug 2017)
- Fatahalian slides: no stable copy. Fallback: https://cs184.eecs.berkeley.edu/public/sp19/lectures/lec-23-how-gpus-work/lec-23-how-gpus-work.pdf ("slides by Kayvon Fatahalian")
- Roofline CACM 2009: https://cacm.acm.org/magazines/2009/4/22959-roofline-an-insightful-visual-performance-model-for-multicore-architectures ; tech report https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.html
- Jia et al. Volta: https://arxiv.org/abs/1804.06826 ; Turing T4 (compares Pascal P4/GP104): https://arxiv.org/abs/1903.07486 ; Luo et al. Hopper: https://arxiv.org/abs/2402.13499
- Flynn 1972: https://doi.org/10.1109/TC.1972.5009071
- Tuning guides: https://docs.nvidia.com/cuda/pascal-tuning-guide/index.html (still live), ada-tuning-guide, hopper-tuning-guide
- P5000 datasheet: https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/productspage/quadro/quadro-desktop/quadro-pascal-p5000-data-sheet-us-nv-704386-r1.pdf
- Laptop GPU compare: https://www.nvidia.com/en-us/geforce/laptops/compare/
- ASUS FA401UU spec: https://www.asus.com/laptops/for-gaming/tuf-gaming/asus-tuf-gaming-a14-2024/techspec/ — RTX 4050 Laptop GPU, 2345 MHz at 100 W, 6 GB GDDR6
- CC table (current, from 7.5): https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html ; CC 6.1 from archive: https://docs.nvidia.com/cuda/archive/12.9.0/cuda-c-programming-guide/index.html
- Open kernel modules (Turing or later): https://github.com/NVIDIA/open-gpu-kernel-modules
- R580 last branch for Maxwell/Pascal/Volta: secondary only (Phoronix https://www.phoronix.com/news/NVIDIA-580-Linux-Driver-Last-HW, 403 to fetch). Name, do not link as verified.

## Facts
| | P5000 (GP104, 6.1) | RTX 4050 Laptop (AD107, 8.9) | H100 SXM5 (PCIe) |
|---|---|---|---|
| SMs | 20 | 20 (derived 2560/128) | 132 (114) |
| FP32 lanes | 2560 (128/SM) | 2560 (128/SM) | 16896 (14592), 128/SM |
| boost | 1733 MHz (GP104 full, GTX1080 WP; P5000 DS silent) | 2345 MHz @100 W (ASUS) | 1980 MHz (1755) |
| memory | 16 GB GDDR5X, 256-bit, 288 GB/s | 6 GB GDDR6, 96-bit, ~216 GB/s derived (confirm on device) | 80 GB HBM3, 5120-bit, 3352 GB/s (PCIe HBM2e 2039) |
| L2 | 2 MB | UNVERIFIED (read from device) | 50 MB |
| FP32 TFLOPS | ~8.9 derived | ~12 derived | 66.9 WP (DS says 60) |
| FP16 non-tensor | 1/64 FP32 (Pascal tuning guide) | ? | 133.8 |
| tensor cores | none | 4th gen | 4th gen, 528 |
| power | 180 W | 35–115 W TGP | 700 W (350) |

CC limits: 6.1 → 64 warps, 2048 thr, 32 blocks, 64K regs, 255 regs/thr, 96 KB smem/SM, 48 KB/block.
8.9 → 48 warps, 1536 thr, 24 blocks, 64K regs, 255, 100 KB/SM, 99 KB/block, 128 KB L1+smem.
9.0 → 64 warps, 2048 thr, 32 blocks, 64K regs, 255, 228 KB/SM, 227 KB/block, 256 KB L1+smem.

Lifecycle: CUDA 13.0 removed Maxwell/Pascal/Volta offline compilation and library support (12.x still supported for them); nvprof removed in 13.0; Nsight Compute dropped Pascal in 2020.1 and Volta later (2026.1 = Turing+); cuda-gdb 13.x floor sm_75; open kernel modules Turing+; R580 last driver branch for Pascal (secondary).
GP100 WP: first NVIDIA GPU with hardware page faulting + 49-bit VA; compute preemption at instruction level (GP100). GP104: GTX 1080 WP says "For CUDA compute tasks, Pascal is also capable of preempting at the finest granularity possible— instruction level"; Pascal Tuning Guide 12.9 #compute-preemption says "a new feature specific to GP100". Conflict; dossier tells reader to query cudaDevAttrComputePreemptionSupported (lab prints it).
