# DeepSeek V4 Perf Tracker Status

Generated: `2026-08-09T16:48:05.326404+00:00`

## Executive summary
- Total items: **53**
- Active items: **53**
- Done items: **0**
- Blocked items: **23**
- Critical-path focus: dspark-c128-online-compressor, overlap-scheduling-online-c128-mtp, compile-hc-head-during-cuda-graph-capture
- Quick-win focus: add-dsv4-nvfp4-tests, flashmla-norm-rope-ilp, occupancy-tuning-dsa-indexer-fp8-q

## Section status counts
- **Attention & compression kernels** — todo: 7
- **CI & bug tracking** — todo: 3
- **CUDA graph & scheduling** — todo: 4
- **Communication & context parallelism** — todo: 11
- **Docs & recipes** — todo: 3
- **Indexer & top-k** — todo: 5
- **Memory & KV capacity** — todo: 4
- **MoE & quantization** — todo: 5
- **Speculative decoding (MTP / DSpark / EAGLE3)** — todo: 10
- **mHC** — todo: 1

## Top next actions
| ID | Priority | Status | Section | Title |
| --- | --- | --- | --- | --- |
| add-dsv4-nvfp4-tests | p0 | todo | CI & bug tracking | Add DSV4 NVFP4 tests |
| decode-context-parallelism-dsv4 | p0 | todo | Communication & context parallelism | Decode context parallelism for DeepSeek V4 |
| compile-hc-head-during-cuda-graph-capture | p1 | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Compile draft / draft-extend `hc_head` during CUDA graph capture |
| dspark-c128-online-compressor | p1 | todo | Speculative decoding (MTP / DSpark / EAGLE3) | DSpark C128 online compressor |
| flashmla-norm-rope-ilp | p1 | todo | Attention & compression kernels | FlashMLA norm-rope: K-tokens-per-block ILP to hide load latency |

## Critical path candidates
| ID | Status | Depth | Score | Title |
| --- | --- | --- | --- | --- |
| dspark-c128-online-compressor | todo | 8 | 55 | DSpark C128 online compressor |
| overlap-scheduling-online-c128-mtp | todo | 8 | 55 | Overlap scheduling for online C128 MTP |
| compile-hc-head-during-cuda-graph-capture | todo | 7 | 52 | Compile draft / draft-extend `hc_head` during CUDA graph capture |
| fuse-draft-extend-swa-translation | todo | 6 | 49 | Fuse draft-extend SWA location translation |
| decode-context-parallelism-dsv4 | todo | 3 | 47 | Decode context parallelism for DeepSeek V4 |

## Quick wins
| ID | Status | Depth | Score | Title |
| --- | --- | --- | --- | --- |
| add-dsv4-nvfp4-tests | todo | 0 | 21 | Add DSV4 NVFP4 tests |
| flashmla-norm-rope-ilp | todo | 0 | 18 | FlashMLA norm-rope: K-tokens-per-block ILP to hide load latency |
| occupancy-tuning-dsa-indexer-fp8-q | todo | 0 | 18 | Occupancy tuning for the DSA indexer fp8-quant Q kernel |
| optimize-c128-epilogue | todo | 0 | 18 | Optimize the c128 epilogue |
| remove-prefill-cp-kv-compressor-materialization | todo | 0 | 18 | Remove prefill CP KV and compressor materialization |

## Blocked items
| ID | Status | Depth | Active blockers | Title |
| --- | --- | --- | --- | --- |
| dspark-c128-online-compressor | todo | 8 | compile-hc-head-during-cuda-graph-capture | DSpark C128 online compressor |
| overlap-scheduling-online-c128-mtp | todo | 8 | compile-hc-head-during-cuda-graph-capture | Overlap scheduling for online C128 MTP |
| compile-hc-head-during-cuda-graph-capture | todo | 7 | fuse-draft-extend-swa-translation | Compile draft / draft-extend `hc_head` during CUDA graph capture |
| fuse-draft-extend-swa-translation | todo | 6 | fuse-compressed-metadata-init | Fuse draft-extend SWA location translation |
| fuse-compressed-metadata-init | todo | 5 | fuse-target-verify-metadata-prologue | Fuse compressed metadata initialization |
| fuse-target-verify-metadata-prologue | todo | 4 | skip-inactive-target-verify-metadata-tails | Fuse the target-verify metadata prologue |
| decode-context-parallelism-dsv4 | todo | 3 | cp-v2-strategy | Decode context parallelism for DeepSeek V4 |
| skip-inactive-target-verify-metadata-tails | todo | 3 | remove-redundant-draft-metadata-copies | Skip inactive target-verify metadata tails |
| cp-v2-strategy | todo | 2 | cp-layersplit-full-implementation | CP V2 strategy |
| remove-redundant-draft-metadata-copies | todo | 2 | skip-unused-draft-metadata | Remove redundant draft metadata copies |
| alt-stream-during-bcg-prefill | todo | 1 | enable-prefill-bcg-v4-memory-reserve | Alt stream during BCG prefill |
| batched-round-robin-cp-prefill-indexer | todo | 1 | indexcache-pd-cp-hicache | Batched and round-robin CP prefill in the non-paged indexer |
| bound-c4-indexer-logits-memory | todo | 1 | rewrite-paged-mqa-metadata | Bound C4 indexer logits peak memory via varlen routing + query-axis chunking |
| breakable-cuda-graph-mixed-chunk-prefill | todo | 1 | enable-prefill-bcg-v4-memory-reserve | Breakable CUDA graph for mixed-chunk prefill |
| cp-layersplit-full-implementation | todo | 1 | cp-layersplit-common-infra | CP cache LayerSplit: full implementation |
| decode-radix-cache-mtp-pd-disagg | todo | 1 | swa-recompute-trailing-window | Decode radix cache with MTP under P/D disagg |
| flashinfer-megamoe-zero-copy-adapter | todo | 1 | auto-select-fp4-moe-backends | FlashInfer MegaMoE, plus the zero-copy adapter path |
| fused-norm-rope-fp8-store | todo | 1 | trtllm-dsv4-attention-sm100-103 | Fused norm + RoPE + uniform fp8 store for TRT-LLM DSv4 sparse attention |
| keep-fp32-routing-weights-mxfp4-trtllm-moe | todo | 1 | auto-select-fp4-moe-backends | Keep fp32 routing weights in the MXFP4 trtllm MoE |
| mtp-trtllm-sparse-attention | todo | 1 | trtllm-dsv4-attention-sm100-103 | Enable MTP on the TRT-LLM sparse attention path |
| nightly-aime25-dsv4-pro-b200 | todo | 1 | add-dsv4-nvfp4-tests | Nightly AIME25 for DeepSeek-V4-Pro on B200 |
| skip-unused-draft-metadata | todo | 1 | fuse-offline-c128-draft-cleanup | Skip unused draft metadata |
| split-mixed-chunk-fp8-paged-mla | todo | 1 | q8kv8-sparse-mla-prefill-sm90 | Split mixed-chunk attention: route decode tokens to the fp8 paged MLA kernel |

## Items missing owners
| ID | Status | Section | Title |
| --- | --- | --- | --- |
| trtllm-dsv4-attention-sm100-103 | todo | Attention & compression kernels | Integrate TRT-LLM DSv4 attention for SM100/103 |
| mtp-trtllm-sparse-attention | todo | Attention & compression kernels | Enable MTP on the TRT-LLM sparse attention path |
| fused-norm-rope-fp8-store | todo | Attention & compression kernels | Fused norm + RoPE + uniform fp8 store for TRT-LLM DSv4 sparse attention |
| flashmla-norm-rope-ilp | todo | Attention & compression kernels | FlashMLA norm-rope: K-tokens-per-block ILP to hide load latency |
| q8kv8-sparse-mla-prefill-sm90 | todo | Attention & compression kernels | Q8KV8 sparse MLA prefill backend on SM90 |
| split-mixed-chunk-fp8-paged-mla | todo | Attention & compression kernels | Split mixed-chunk attention: route decode tokens to the fp8 paged MLA kernel |
| optimize-c128-epilogue | todo | Attention & compression kernels | Optimize the c128 epilogue |
| occupancy-tuning-dsa-indexer-fp8-q | todo | Indexer & top-k | Occupancy tuning for the DSA indexer fp8-quant Q kernel |
| rewrite-paged-mqa-metadata | todo | Indexer & top-k | Rewrite `paged_mqa_metadata` |
| bound-c4-indexer-logits-memory | todo | Indexer & top-k | Bound C4 indexer logits peak memory via varlen routing + query-axis chunking |
| batched-round-robin-cp-prefill-indexer | todo | Indexer & top-k | Batched and round-robin CP prefill in the non-paged indexer |
| indexcache-pd-cp-hicache | todo | Indexer & top-k | IndexCache with PD, CP, and HiCache coverage |
| flashinfer-mhc-fusion | todo | mHC | FlashInfer mHC fusion |
| auto-select-fp4-moe-backends | todo | MoE & quantization | Auto-select FP4 MoE backends after A2A normalization |
| keep-fp32-routing-weights-mxfp4-trtllm-moe | todo | MoE & quantization | Keep fp32 routing weights in the MXFP4 trtllm MoE |
| flashinfer-megamoe-zero-copy-adapter | todo | MoE & quantization | FlashInfer MegaMoE, plus the zero-copy adapter path |
| fused-swiglu-quant-shared-experts | todo | MoE & quantization | Fused SwiGLU + quant for shared experts and EP-normal |
| fused-silu-clamp-mul-fp8-quant-ep-moe | todo | MoE & quantization | Fused SiLU + clamp + mul + FP8-quant AOT kernel for the EP MoE path |
| fuse-offline-c128-draft-cleanup | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Fuse offline C128 draft state cleanup into one launch |
| skip-unused-draft-metadata | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Skip unused draft metadata |
| remove-redundant-draft-metadata-copies | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Remove redundant draft metadata copies |
| skip-inactive-target-verify-metadata-tails | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Skip inactive target-verify metadata tails |
| fuse-target-verify-metadata-prologue | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Fuse the target-verify metadata prologue |
| fuse-compressed-metadata-init | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Fuse compressed metadata initialization |
| fuse-draft-extend-swa-translation | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Fuse draft-extend SWA location translation |
| compile-hc-head-during-cuda-graph-capture | todo | Speculative decoding (MTP / DSpark / EAGLE3) | Compile draft / draft-extend `hc_head` during CUDA graph capture |
| dspark-c128-online-compressor | todo | Speculative decoding (MTP / DSpark / EAGLE3) | DSpark C128 online compressor |
| eagle3-deepseek-v4-flash-0731 | todo | Speculative decoding (MTP / DSpark / EAGLE3) | EAGLE3 for DeepSeek-V4-Flash-0731 |
| flashinfer-mnnvl-pure-allreduce | todo | Communication & context parallelism | FlashInfer MNNVL backend for pure (non-fused) allreduce |
| remove-prefill-cp-kv-compressor-materialization | todo | Communication & context parallelism | Remove prefill CP KV and compressor materialization |
| ag-gemm-moe-rs-overlap-kernels | todo | Communication & context parallelism | `ag_gemm` + `moe_rs` symmetric-memory overlap kernels for CP prefill |
| shared-kv-cache-prefill-cp-vmm | todo | Communication & context parallelism | Shared KV cache for prefill CP via VMM |
| cp-layersplit-common-infra | todo | Communication & context parallelism | CP cache LayerSplit: common infrastructure |
| cp-layersplit-full-implementation | todo | Communication & context parallelism | CP cache LayerSplit: full implementation |
| cp-v2-strategy | todo | Communication & context parallelism | CP V2 strategy |
| decode-context-parallelism-dsv4 | todo | Communication & context parallelism | Decode context parallelism for DeepSeek V4 |
| fix-non-ep-tbo-attention-tp-gt1 | todo | Communication & context parallelism | Fix non-EP TBO for attention TP > 1 |
| fix-dp-attention-gather-semantics | todo | Communication & context parallelism | Fix DP-attention gather semantics |
| support-dsv4-in-pdmux | todo | Communication & context parallelism | Support DeepSeek V4 in PDMux |
| enable-prefill-bcg-v4-memory-reserve | todo | CUDA graph & scheduling | Enable prefill BCG: two-pass capture + V4-aware memory reserve |
| alt-stream-during-bcg-prefill | todo | CUDA graph & scheduling | Alt stream during BCG prefill |
| breakable-cuda-graph-mixed-chunk-prefill | todo | CUDA graph & scheduling | Breakable CUDA graph for mixed-chunk prefill |
| overlap-scheduling-online-c128-mtp | todo | CUDA graph & scheduling | Overlap scheduling for online C128 MTP |
| swa-recompute-trailing-window | todo | Memory & KV capacity | SWA recompute |
| decode-radix-cache-mtp-pd-disagg | todo | Memory & KV capacity | Decode radix cache with MTP under P/D disagg |
| bf16-c4-c128-compressed-state-storage | todo | Memory & KV capacity | BF16 C4/C128 compressed-state storage |
| size-swa-state-pool-by-storage-page | todo | Memory & KV capacity | Size the SWA state pool by storage page size, not the model window |
| gb300-fp4-multinode-pd-recipes | todo | Docs & recipes | GB300 FP4 multi-node PD recipes for DeepSeek-V4-Pro |
| slurm-cluster-cookbook-deployment | todo | Docs & recipes | Slurm cluster deployment in the cookbook |
| switch-v4-flash-cookbook-to-flashinfer-mxfp4 | todo | Docs & recipes | Switch the V4-Flash cookbook from Marlin to `flashinfer_mxfp4` |
| flashinfer-trtllm-moe-runner-asserts-b200 | todo | CI & bug tracking | `flashinfer_trtllm` MoE runner asserts on DeepSeek-V4-Flash on B200 |

## Stale items
- None
