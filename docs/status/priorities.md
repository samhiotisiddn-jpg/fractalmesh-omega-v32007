# DeepSeek V4 Prioritization Outputs

## Critical path candidates
- `dspark-c128-online-compressor` (score=55, depth=8): DSpark C128 online compressor
- `overlap-scheduling-online-c128-mtp` (score=55, depth=8): Overlap scheduling for online C128 MTP
- `compile-hc-head-during-cuda-graph-capture` (score=52, depth=7): Compile draft / draft-extend `hc_head` during CUDA graph capture
- `fuse-draft-extend-swa-translation` (score=49, depth=6): Fuse draft-extend SWA location translation
- `decode-context-parallelism-dsv4` (score=47, depth=3): Decode context parallelism for DeepSeek V4
- `fuse-compressed-metadata-init` (score=46, depth=5): Fuse compressed metadata initialization
- `fuse-target-verify-metadata-prologue` (score=43, depth=4): Fuse the target-verify metadata prologue
- `flashinfer-megamoe-zero-copy-adapter` (score=41, depth=1): FlashInfer MegaMoE, plus the zero-copy adapter path
- `skip-inactive-target-verify-metadata-tails` (score=40, depth=3): Skip inactive target-verify metadata tails
- `mtp-trtllm-sparse-attention` (score=40, depth=1): Enable MTP on the TRT-LLM sparse attention path

## Quick wins
- `add-dsv4-nvfp4-tests` (score=21, depth=0): Add DSV4 NVFP4 tests
- `flashmla-norm-rope-ilp` (score=18, depth=0): FlashMLA norm-rope: K-tokens-per-block ILP to hide load latency
- `occupancy-tuning-dsa-indexer-fp8-q` (score=18, depth=0): Occupancy tuning for the DSA indexer fp8-quant Q kernel
- `optimize-c128-epilogue` (score=18, depth=0): Optimize the c128 epilogue
- `remove-prefill-cp-kv-compressor-materialization` (score=18, depth=0): Remove prefill CP KV and compressor materialization

## Blocked items
- `dspark-c128-online-compressor` blocked by [compile-hc-head-during-cuda-graph-capture] — DSpark C128 online compressor
- `overlap-scheduling-online-c128-mtp` blocked by [compile-hc-head-during-cuda-graph-capture] — Overlap scheduling for online C128 MTP
- `compile-hc-head-during-cuda-graph-capture` blocked by [fuse-draft-extend-swa-translation] — Compile draft / draft-extend `hc_head` during CUDA graph capture
- `fuse-draft-extend-swa-translation` blocked by [fuse-compressed-metadata-init] — Fuse draft-extend SWA location translation
- `fuse-compressed-metadata-init` blocked by [fuse-target-verify-metadata-prologue] — Fuse compressed metadata initialization
- `fuse-target-verify-metadata-prologue` blocked by [skip-inactive-target-verify-metadata-tails] — Fuse the target-verify metadata prologue
- `decode-context-parallelism-dsv4` blocked by [cp-v2-strategy] — Decode context parallelism for DeepSeek V4
- `skip-inactive-target-verify-metadata-tails` blocked by [remove-redundant-draft-metadata-copies] — Skip inactive target-verify metadata tails
- `cp-v2-strategy` blocked by [cp-layersplit-full-implementation] — CP V2 strategy
- `remove-redundant-draft-metadata-copies` blocked by [skip-unused-draft-metadata] — Remove redundant draft metadata copies
- `alt-stream-during-bcg-prefill` blocked by [enable-prefill-bcg-v4-memory-reserve] — Alt stream during BCG prefill
- `batched-round-robin-cp-prefill-indexer` blocked by [indexcache-pd-cp-hicache] — Batched and round-robin CP prefill in the non-paged indexer
- `bound-c4-indexer-logits-memory` blocked by [rewrite-paged-mqa-metadata] — Bound C4 indexer logits peak memory via varlen routing + query-axis chunking
- `breakable-cuda-graph-mixed-chunk-prefill` blocked by [enable-prefill-bcg-v4-memory-reserve] — Breakable CUDA graph for mixed-chunk prefill
- `cp-layersplit-full-implementation` blocked by [cp-layersplit-common-infra] — CP cache LayerSplit: full implementation
- `decode-radix-cache-mtp-pd-disagg` blocked by [swa-recompute-trailing-window] — Decode radix cache with MTP under P/D disagg
- `flashinfer-megamoe-zero-copy-adapter` blocked by [auto-select-fp4-moe-backends] — FlashInfer MegaMoE, plus the zero-copy adapter path
- `fused-norm-rope-fp8-store` blocked by [trtllm-dsv4-attention-sm100-103] — Fused norm + RoPE + uniform fp8 store for TRT-LLM DSv4 sparse attention
- `keep-fp32-routing-weights-mxfp4-trtllm-moe` blocked by [auto-select-fp4-moe-backends] — Keep fp32 routing weights in the MXFP4 trtllm MoE
- `mtp-trtllm-sparse-attention` blocked by [trtllm-dsv4-attention-sm100-103] — Enable MTP on the TRT-LLM sparse attention path
- `nightly-aime25-dsv4-pro-b200` blocked by [add-dsv4-nvfp4-tests] — Nightly AIME25 for DeepSeek-V4-Pro on B200
- `skip-unused-draft-metadata` blocked by [fuse-offline-c128-draft-cleanup] — Skip unused draft metadata
- `split-mixed-chunk-fp8-paged-mla` blocked by [q8kv8-sparse-mla-prefill-sm90] — Split mixed-chunk attention: route decode tokens to the fp8 paged MLA kernel
