# Qwen3-VL-8B QLoRA train v1

## Result

Status: **passed**

- The 500-record training set completed three QLoRA epochs with 100 validation records.
- Qwen3-VL-8B-Instruct loaded and trained with bitsandbytes 4-bit NF4 without CUDA OOM.
- Checkpoints were saved after every epoch; the best adapter came from step 250.
- The exported PEFT adapter was independently reloaded on the 4-bit base model.

## Reproducibility

- Date: 2026-07-17 (Asia/Shanghai)
- Project base commit: `5f7c178acc80d33a1fa706b45d560881bbbb959d`
- LLaMA-Factory commit: `d1049d650acccbe72e62b36ac660a5036362ae18`
- Base model: `/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct`
- Model class: `Qwen3VLForConditionalGeneration`
- Training dataset: `customer_service_train` (500 records)
- Training dataset SHA-256: `2eef2d6a01f8eb029a694060486ca50dec60199d4fa9bbc525800ee17c8fd8cd`
- Validation dataset: `customer_service_validation` (100 records)
- Validation dataset SHA-256: `7f603ce8c805f512d6b714138186ba976e7aa7c6215f811f3ef822c5d0e6c84f`
- Configuration: `configs/qwen3_vl_8b_qlora_train.yaml`
- GPU: NVIDIA GeForce RTX 4090, 24 GiB
- PyTorch: 2.8.0+cu128
- Transformers: 5.8.0
- PEFT: 0.18.1
- bitsandbytes: 0.49.2

## QLoRA settings

- Quantization: 4-bit NF4 with double quantization
- Compute dtype: bfloat16
- LoRA rank/alpha/dropout: 8 / 16 / 0.05
- LoRA target: all language-model linear modules
- Trainable parameters: 21,823,488 (0.2483%)
- Vision tower and multimodal projector: frozen
- Cutoff length: 512
- Per-device batch size: 1
- Gradient accumulation: 4
- Epochs / optimizer steps: 3 / 375
- Optimizer: paged AdamW 8-bit
- Learning rate: 1e-4 with cosine scheduling
- Gradient checkpointing: enabled

## Metrics

- Training runtime: 962.8281 seconds (16:02.83)
- Samples per second: 1.558
- Steps per second: 0.389
- Aggregate training loss: 0.3748068
- Validation loss at step 125: 0.0188723
- Validation loss at step 250: 0.000707957 (best)
- Validation loss at step 375: 0.000723072
- Final evaluation loss after loading the best adapter: 0.000707957
- Peak GPU memory from `nvidia-smi`: 9074 MiB
- Base plus adapter reload peak: 8.275 GiB allocated

The very low validation loss indicates that these synthetic examples have highly
regular patterns. It verifies the training pipeline, but should not be treated as a
production-quality generalization score. A later run should use more diverse real or
realistically perturbed cases and a less template-aligned holdout set.

## Adapter

- Remote directory: `/root/Intelligent_Customer_Service_System/artifacts/qwen3-vl-8b/qlora/train-v1`
- Best checkpoint: `checkpoint-250`
- Final exported file: `adapter_model.safetensors` (84 MiB)
- SHA-256: `4594c2ffa2b837667f01fd86e4be4caad04052c4ba4d064cb3b0b77be58f9c37`
- Adapter parameters: 21,823,488
- Reload validation: passed
- Full remote output directory: approximately 369 MiB

## Commands

```bash
bash scripts/run_qwen3_vl_8b_qlora_train.sh
python scripts/check_qlora_adapter.py \
  --adapter ./artifacts/qwen3-vl-8b/qlora/train-v1
```

## Preprocessing correction

The first launch stopped before model training because the validation records do not
contain a `history` property while their dataset mapping declared one. The validation
mapping was corrected to omit this optional field. Training examples retain their
multi-turn `history` mapping. No dataset records or dataset hashes were changed.
