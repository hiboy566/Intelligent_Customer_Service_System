# Qwen3-VL-8B customer-service QLoRA adapter

- Base model: `Qwen3-VL-8B-Instruct`
- Training run: `training_runs/2026-07-17_qwen3-vl-8b-qlora-train-v1`
- Quantization used for training/inference: bitsandbytes 4-bit NF4 with double quantization
- Adapter parameters: 21,823,488
- Adapter file size: 87,368,144 bytes
- SHA-256: `4594c2ffa2b837667f01fd86e4be4caad04052c4ba4d064cb3b0b77be58f9c37`

The directory contains only the PEFT adapter. The Qwen3-VL-8B-Instruct base model must
be available separately and is selected through the `MODEL_PATH` environment variable.
