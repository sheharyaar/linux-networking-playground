# Verified references — LLM layer (agent fetch, 2026-10-02)

Quotes came back through WebFetch summaries; re-check any you print verbatim.

## Papers
- https://arxiv.org/abs/1706.03762 — Attention Is All You Need (Vaswani et al., 2017). §3.2 scaled dot-product, multi-head.
- https://arxiv.org/abs/2307.09288 — Llama 2: Open Foundation and Fine-Tuned Chat Models (Touvron et al., 2023).
- https://arxiv.org/abs/2407.21783 — The Llama 3 Herd of Models (Grattafiori et al., 2024).
- https://arxiv.org/abs/2305.13245 — GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints (Ainslie et al., EMNLP 2023).
- https://arxiv.org/abs/1911.02150 — Fast Transformer Decoding: One Write-Head is All You Need (Shazeer, 2019). Bandwidth analysis of incremental decoding.
- https://arxiv.org/abs/2104.09864 — RoFormer: Enhanced Transformer with Rotary Position Embedding (Su et al.).
- https://arxiv.org/abs/1910.07467 — Root Mean Square Layer Normalization (Zhang, Sennrich, NeurIPS 2019).
- https://arxiv.org/abs/2002.05202 — GLU Variants Improve Transformer (Shazeer, 2020).
- https://arxiv.org/abs/2205.14135 — FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness (Dao et al., 2022).
- https://arxiv.org/abs/2307.08691 — FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning (Dao, 2023).
- https://arxiv.org/abs/2407.08608 — FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision (Shah et al., 2024). Hopper only.
- https://arxiv.org/abs/1805.02867 — Online normalizer calculation for softmax (Milakov, Gimelshein, 2018).
- https://arxiv.org/abs/2211.05102 — Efficiently Scaling Transformer Inference (Pope et al., 2022).
- https://arxiv.org/abs/2309.06180 — Efficient Memory Management for Large Language Model Serving with PagedAttention (Kwon et al., SOSP 2023).
- https://www.usenix.org/conference/osdi22/presentation/yu — Orca: A Distributed Serving System for Transformer-Based Generative Models (Yu et al., OSDI '22).
- https://www.usenix.org/conference/osdi24/presentation/agrawal — Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve (OSDI '24). arXiv 2403.02310.
- https://arxiv.org/abs/2211.17192 — Fast Inference from Transformers via Speculative Decoding (Leviathan et al., ICML 2023).
- https://arxiv.org/abs/1909.08053 — Megatron-LM (Shoeybi et al., 2019).
- https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin — DistServe (OSDI '24). arXiv 2401.09670.
- https://arxiv.org/abs/2311.18677 — Splitwise: Efficient generative LLM inference using phase splitting (Patel et al.).
- https://pldi19.sigplan.org/details/mapl-2019-papers/1/Triton-An-Intermediate-Language-and-Compiler-for-Tiled-Neural-Network-Computations — Triton (Tillet, Kung, Cox, MAPL 2019).

## vLLM (docs.vllm.ai/en/latest)
- /design/arch_overview/ — Architecture Overview (API server, EngineCore, GPU workers).
- /design/prefix_caching/ — Automatic Prefix Caching (hash of parent hash + block tokens + extra keys; LRU free queue).
- /design/paged_attention/ — legacy V0 kernel doc; concept only.
- /design/cuda_graphs/ — CUDA Graphs (NONE … FULL_AND_PIECEWISE; CudagraphDispatcher).
- /design/torch_compile/ — torch.compile integration (piecewise split at attention).
- /design/metrics/ and /usage/metrics/ — metrics.
- /design/hybrid_kv_cache_manager/
- /features/disagg_prefill/ — experimental.
- /configuration/optimization/ — chunked prefill on by default in V1; max_num_batched_tokens guidance.
- /getting_started/installation/gpu/ — Linux, Python 3.10–3.13, compute capability 7.5+, CUDA 12.9 default wheels (12.8/13.0 variants).
- https://vllm.ai/blog/2025-01-27-v1-alpha-release — vLLM V1: A Major Upgrade to vLLM's Core Architecture.
- https://vllm.ai/blog/2023-06-20-vllm — vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention.
- https://vllm.ai/blog/2025-09-05-anatomy-of-vllm — Inside vLLM: Anatomy of a High-Throughput LLM Inference System (Aleksa Gordić, 2025-09-05).

Metric names (docs): vllm:time_to_first_token_seconds, vllm:inter_token_latency_seconds, vllm:request_time_per_output_token_seconds, vllm:e2e_request_latency_seconds, vllm:request_queue_time_seconds, vllm:request_prefill_time_seconds, vllm:request_decode_time_seconds, vllm:request_inference_time_seconds, vllm:kv_cache_usage_perc, vllm:num_requests_running, vllm:num_requests_waiting, vllm:num_preemptions, vllm:request_num_preemptions, vllm:prefix_cache_hits, vllm:prefix_cache_queries. Counters get _total in exposition. Confirm on a live /metrics.

## llama.cpp / ggml
- https://github.com/ggml-org/llama.cpp
- https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md — -DGGML_CUDA=ON, CMAKE_CUDA_ARCHITECTURES, GGML_CUDA_FORCE_MMQ/CUBLAS.
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md — --parallel slots, --kv-unified, cont batching default, --metrics; llamacpp:* metric names.
- https://github.com/ggml-org/ggml/blob/master/docs/gguf.md — GGUF spec v3.
- https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md — bpw table (Llama 3.1 8B): Q4_K_M 4.89, Q8_0 8.50.
- https://github.com/ggml-org/llama.cpp/pull/1684 — k-quants PR (Q4_K 4.5 bpw).

## Explainers
- https://jalammar.github.io/illustrated-transformer/ — The Illustrated Transformer (encoder-decoder; Llama is decoder-only).
- https://horace.io/brrr_intro.html — Making Deep Learning go Brrrr From First Principles.
- https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/ — Mastering LLM Techniques: Inference Optimization (Nov 2023).
- https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts — LLM Inference Benchmarking: Fundamental Concepts (Apr 2025). TTFT includes queueing+prefill+network; ITL≈TPOT in NVIDIA's usage; vLLM exports both separately.
- https://docs.pytorch.org/docs/2.14/notes/cuda.html — CUDA semantics.
- https://docs.pytorch.org/docs/2.14/generated/torch.compile.html — torch.compile.
- https://triton-lang.org/main/index.html — Triton docs.

## Model configs (HF raw config.json)
| | Qwen2.5-0.5B-Instruct | Qwen2.5-7B-Instruct | Llama-3.1-8B |
|---|---|---|---|
| layers | 24 | 28 | 32 |
| hidden | 896 | 3584 | 4096 |
| intermediate | 4864 | 18944 | 14336 |
| heads / kv heads | 14 / 2 | 28 / 4 | 32 / 8 |
| head_dim | 64 | 128 | 128 |
| vocab | 151936 | 152064 | 128256 |
| tied embeddings | yes | no | no |
| params | 0.49B | 7.61B | ~8.0B |
| KV bytes/token bf16 | 12,288 | 57,344 | 131,072 |
Official GGUF: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF (Q4_K_M 491 MB, Q8_0 676 MB).
