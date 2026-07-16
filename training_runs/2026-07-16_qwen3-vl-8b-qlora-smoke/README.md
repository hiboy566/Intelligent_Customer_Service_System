# Qwen3-VL-8B QLoRA smoke test

## Result

Status: **passed**

- The local Qwen3-VL-8B-Instruct base model loaded successfully in 4-bit NF4.
- The 50-record smoke dataset completed one QLoRA epoch without CUDA OOM.
- The final PEFT adapter was saved and successfully reloaded on the 4-bit base model.

## Reproducibility

- Date: 2026-07-16
- Project base commit: `5f7c178acc80d33a1fa706b45d560881bbbb959d`
- LLaMA-Factory commit: `d1049d650acccbe72e62b36ac660a5036362ae18`
- Base model: `/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct`
- Model class: `Qwen3VLForConditionalGeneration`
- Dataset: `customer_service_smoke` (50 records)
- Dataset SHA-256: `8d0fe834ebbff7be1ca0a397ab45419c7d37dbfdd48cea81f3df9f08c99772c9`
- Configuration: `configs/qwen3_vl_8b_qlora_smoke.yaml`
- GPU: NVIDIA GeForce RTX 4090, 24 GiB
- Python: 3.12.11
- PyTorch: 2.8.0+cu128
- Transformers: 5.8.0
- PEFT: 0.18.1
- bitsandbytes: 0.49.2

## QLoRA settings

- Quantization: 4-bit NF4 with double quantization
- Compute dtype: bfloat16
- LoRA rank/alpha/dropout: 8 / 16 / 0.05
- LoRA target: all language-model linear modules
- Vision tower: frozen
- Multimodal projector: frozen
- Cutoff length: 512
- Per-device batch size: 1
- Gradient accumulation: 4
- Epochs / optimizer steps: 1 / 13
- Optimizer: paged AdamW 8-bit
- Gradient checkpointing: enabled

## Metrics

- Training runtime: 33.193 seconds
- Samples per second: 1.506
- Steps per second: 0.392
- Final aggregate training loss: 3.3675
- First logged step loss: 4.770
- Last logged step loss: 2.687
- Peak GPU memory from `nvidia-smi`: 9074 MiB
- Standalone 4-bit model-load peak: 8.259 GiB allocated
- Base plus adapter reload peak: 8.275 GiB allocated

## Adapter

- Remote directory: `/root/Intelligent_Customer_Service_System/artifacts/qwen3-vl-8b/qlora/smoke`
- File: `adapter_model.safetensors`
- File size: 87,368,144 bytes
- SHA-256: `ad0cc0ddce2acc8fc54f65533198ed60ce9407714c24f9fe945a50dab0ba3d3e`
- Adapter parameters: 21,823,488
- Reload validation: passed

The output directory also contains `adapter_config.json`, tokenizer and processor files,
trainer state, metrics, a retained checkpoint, and the loss plot. The total remote output
directory size is approximately 232 MiB.

## Commands

```bash
python scripts/check_qwen3_vl_4bit_load.py
llamafactory-cli train configs/qwen3_vl_8b_qlora_smoke.yaml
python scripts/check_qlora_adapter.py
```

## Initial failed attempt

The first attempt stopped before the optimizer step because the preinstalled
`torch 2.9.1+cu130` is blocked by LLaMA-Factory for models containing Conv3D due to a
known severe performance regression. It did not OOM; the observed peak was 9072 MiB.
The environment was changed to the official compatible set:

```text
torch==2.8.0+cu128
torchvision==0.23.0+cu128
torchaudio==2.8.0+cu128
```

After restoring `fsspec==2025.3.0` and `pillow==11.3.0`, `pip check` reported no broken
requirements and the successful smoke test above was run from a clean Python process.
