from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    model_path: str
    adapter_path: str
    model_alias: str
    api_key: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model_path=os.getenv(
                "MODEL_PATH", "/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct"
            ),
            adapter_path=os.getenv(
                "ADAPTER_PATH", "./models/qwen3-vl-8b-qlora-train-v1"
            ),
            model_alias=os.getenv("MODEL_ALIAS", "qwen3-vl-8b-customer-service"),
            api_key=os.getenv("SERVICE_API_KEY") or None,
        )


class ModelRuntime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.processor: Any = None
        self.model: Any = None
        self.device: Any = None
        self.torch: Any = None

    def load(self) -> None:
        import torch
        from peft import PeftModel
        from transformers import (
            AutoModelForImageTextToText,
            AutoProcessor,
            BitsAndBytesConfig,
        )

        if not torch.cuda.is_available():
            raise RuntimeError("QLoRA inference requires an NVIDIA CUDA GPU")
        if not Path(self.settings.adapter_path).is_dir():
            raise FileNotFoundError(
                f"adapter directory not found: {self.settings.adapter_path}"
            )

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        self.processor = AutoProcessor.from_pretrained(
            self.settings.model_path,
            trust_remote_code=True,
        )
        base_model = AutoModelForImageTextToText.from_pretrained(
            self.settings.model_path,
            trust_remote_code=True,
            quantization_config=quantization_config,
            device_map={"": 0},
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
            low_cpu_mem_usage=True,
        )
        self.model = PeftModel.from_pretrained(
            base_model,
            self.settings.adapter_path,
            is_trainable=False,
        )
        self.model.eval()
        self.device = next(self.model.parameters()).device
        self.torch = torch

    def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        repetition_penalty: float,
        tools: list[dict[str, Any]] | None = None,
    ) -> tuple[str, int, int]:
        if (
            self.model is None
            or self.processor is None
            or self.device is None
            or self.torch is None
        ):
            raise RuntimeError("model runtime is not loaded")

        normalized_messages = normalize_messages(messages, tools)
        prompt = self.processor.apply_chat_template(
            normalized_messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.processor(
            text=[prompt],
            return_tensors="pt",
            padding=True,
        )
        inputs = {
            key: value.to(self.device) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }
        prompt_tokens = int(inputs["input_ids"].shape[-1])

        generation_args: dict[str, Any] = {
            "max_new_tokens": max_tokens,
            "repetition_penalty": repetition_penalty,
            "do_sample": temperature > 0,
            "pad_token_id": self.processor.tokenizer.pad_token_id,
            "eos_token_id": self.processor.tokenizer.eos_token_id,
        }
        if temperature > 0:
            generation_args.update(temperature=temperature, top_p=top_p)

        try:
            with self.torch.inference_mode():
                output_ids = self.model.generate(**inputs, **generation_args)
        except self.torch.cuda.OutOfMemoryError as error:
            self.torch.cuda.empty_cache()
            raise GpuOutOfMemoryError("GPU out of memory") from error

        completion_ids = output_ids[:, prompt_tokens:]
        completion_tokens = int(completion_ids.shape[-1])
        text = self.processor.batch_decode(
            completion_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()
        return text, prompt_tokens, completion_tokens


class GpuOutOfMemoryError(RuntimeError):
    """Raised after clearing the CUDA allocator following an inference OOM."""


def normalize_messages(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if tools:
        catalog = [tool["function"] for tool in tools]
        normalized.append(
            {
                "role": "system",
                "content": (
                    "你可以使用后端工具。工具定义如下：\n"
                    f"{json.dumps(catalog, ensure_ascii=False)}\n"
                    "需要调用工具时，只输出 JSON："
                    '{"tool_calls":[{"name":"工具名","arguments":{}}]}。'
                    "不需要工具或已获得工具结果时，只输出 JSON："
                    '{"answer":"给用户的最终答复"}。'
                    "不得编造工具返回值、订单状态、退款状态或工单编号。"
                ),
            }
        )

    for message in messages:
        role = message["role"]
        if role == "tool":
            normalized.append(
                {
                    "role": "user",
                    "content": (
                        f"工具 {message.get('name') or message.get('tool_call_id') or 'unknown'} "
                        f"执行结果：{message.get('content') or ''}"
                    ),
                }
            )
        elif role == "assistant" and message.get("tool_calls"):
            normalized.append(
                {
                    "role": "assistant",
                    "content": json.dumps(
                        {"tool_calls": message["tool_calls"]}, ensure_ascii=False
                    ),
                }
            )
        else:
            normalized.append(
                {
                    "role": role,
                    "content": message.get("content") or "",
                }
            )
    return normalized
