#!/usr/bin/env python3
"""Reload a QLoRA adapter on the 4-bit Qwen3-VL base model."""

from __future__ import annotations

import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, BitsAndBytesConfig


def gib(value: int) -> float:
    return value / 1024**3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct",
    )
    parser.add_argument(
        "--adapter",
        default="./artifacts/qwen3-vl-8b/qlora/smoke",
    )
    args = parser.parse_args()

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    base_model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        trust_remote_code=True,
        quantization_config=quantization_config,
        device_map={"": 0},
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
    )
    model = PeftModel.from_pretrained(base_model, args.adapter, is_trainable=False)
    adapter_names = sorted(model.peft_config)
    adapter_parameters = sum(
        parameter.numel()
        for name, parameter in model.named_parameters()
        if "lora_" in name
    )
    print(f"adapter_names={adapter_names}")
    print(f"adapter_parameters={adapter_parameters}")
    print(f"adapter_reload=ok")
    print(f"cuda_peak_allocated_gib={gib(torch.cuda.max_memory_allocated()):.3f}")


if __name__ == "__main__":
    main()
