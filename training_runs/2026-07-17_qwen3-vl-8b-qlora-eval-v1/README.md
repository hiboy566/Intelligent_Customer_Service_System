# Qwen3-VL-8B base + QLoRA adapter evaluation v1

## Result

Status: **passed with one identifier-grounding error**

The Qwen3-VL-8B-Instruct base model was loaded in bitsandbytes 4-bit NF4 with the
`train-v1` LoRA adapter. All 100 validation records were evaluated with deterministic
greedy generation and no CUDA OOM.

## Reproducibility

- Date: 2026-07-17 (Asia/Shanghai)
- Project base commit: `5f7c178acc80d33a1fa706b45d560881bbbb959d`
- LLaMA-Factory commit: `d1049d650acccbe72e62b36ac660a5036362ae18`
- Base model: `/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct`
- Adapter: `./artifacts/qwen3-vl-8b/qlora/train-v1`
- Adapter SHA-256: `4594c2ffa2b837667f01fd86e4be4caad04052c4ba4d064cb3b0b77be58f9c37`
- Evaluation dataset: `customer_service_validation` (100 records)
- Dataset SHA-256: `7f603ce8c805f512d6b714138186ba976e7aa7c6215f811f3ef822c5d0e6c84f`
- Configuration: `configs/qwen3_vl_8b_qlora_eval.yaml`
- Quantization: 4-bit NF4 with double quantization
- Template: `qwen3_vl_nothink`
- Decoding: greedy, `do_sample=false`, maximum 256 new tokens
- GPU: NVIDIA GeForce RTX 4090, 24 GiB

## Generation metrics

- ROUGE-1: 100.0
- ROUGE-2: 100.0
- ROUGE-L: 99.984848
- BLEU-4: 99.039663
- Normalized exact match: 99/100 (99%)
- Empty predictions: 0
- Special-token leaks: 0
- Identifier grounded in prompt: 99/100 (99%)
- Identifier equal to reference: 99/100 (99%)
- Prediction length: 92 / 106.07 / 119 characters (min/mean/max)
- Generation runtime: 811.963 seconds (13:31.96)
- Throughput: 0.123 samples/second
- Peak GPU memory from `nvidia-smi`: 9174 MiB

The prediction file SHA-256 is
`34b29497f31758733e5550563d200d5fd9514d22a1b8d69b715d7ca7cfd21285`.

## Error analysis

Prediction index 7 was the only non-exact answer and the only ungrounded identifier.
The prompt/reference order ID was `TEST-02-024`, while the model generated
`TEST-02-02-024`. The remainder of that answer matched the reference. This is a real
customer-service risk because an apparently small identifier mutation can target the
wrong order; production code should inject verified order data rather than relying on
the model to reproduce identifiers from memory.

## Interpretation

The near-perfect overlap metrics mainly show that the adapter learned this synthetic
dataset's repeated answer templates. They verify the base-plus-adapter inference
pipeline but do not establish production generalization. A stronger evaluation should
include newly authored intents, paraphrases, adversarial requests, incomplete context,
policy conflicts, and identifiers not represented by the training templates.

## Commands

```bash
bash scripts/run_qwen3_vl_8b_qlora_eval.sh
python scripts/analyze_customer_service_predictions.py \
  artifacts/qwen3-vl-8b/qlora/eval-v1/generated_predictions.jsonl \
  --output artifacts/qwen3-vl-8b/qlora/eval-v1/integrity_metrics.json
```

## Remote artifacts

`/root/Intelligent_Customer_Service_System/artifacts/qwen3-vl-8b/qlora/eval-v1`
contains the complete generated predictions and metric files.
