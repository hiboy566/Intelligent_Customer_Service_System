#!/usr/bin/env python3
"""Load Qwen3-VL-8B in 4-bit mode and report CUDA memory usage."""

from __future__ import annotations

import argparse

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig


def gib(value: int) -> float:
    return value / 1024**3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct",
    )
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=True)
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        trust_remote_code=True,
        quantization_config=quantization_config,
        device_map={"": 0},
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
    )

    linear4bit_count = sum(module.__class__.__name__ == "Linear4bit" for module in model.modules())
    print(f"model_class={model.__class__.__name__}")
    print(f"processor_class={processor.__class__.__name__}")
    print(f"loaded_in_4bit={getattr(model, 'is_loaded_in_4bit', False)}")
    print(f"linear4bit_modules={linear4bit_count}")
    print(f"model_footprint_gib={gib(model.get_memory_footprint()):.3f}")
    print(f"cuda_allocated_gib={gib(torch.cuda.memory_allocated()):.3f}")
    print(f"cuda_reserved_gib={gib(torch.cuda.memory_reserved()):.3f}")
    print(f"cuda_peak_allocated_gib={gib(torch.cuda.max_memory_allocated()):.3f}")
    print(f"gpu={torch.cuda.get_device_name(0)}")


if __name__ == "__main__":
    main()
