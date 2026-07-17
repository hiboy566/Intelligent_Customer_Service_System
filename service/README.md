# FastAPI QLoRA inference service

This service loads Qwen3-VL-8B-Instruct in bitsandbytes 4-bit NF4 and attaches the
`train-v1` PEFT adapter. It currently accepts text chat messages; image inputs are not
exposed by the HTTP schema.

## Requirements

- Linux with an NVIDIA CUDA GPU (tested on RTX 4090 24 GiB)
- Python 3.12
- The Qwen3-VL-8B-Instruct base model
- `models/qwen3-vl-8b-qlora-train-v1/adapter_model.safetensors`

On the training server, the existing `py312` environment already contains the PyTorch,
Transformers, PEFT and bitsandbytes versions. Install FastAPI dependencies there with:

```bash
python -m pip install "fastapi>=0.115,<1" "uvicorn[standard]>=0.34,<1"
```

For a clean CUDA 12.8 environment:

```bash
python -m pip install -r service/requirements.txt
```

## Configuration

```bash
export MODEL_PATH=/model/ModelScope/Qwen/Qwen3-VL-8B-Instruct
export ADAPTER_PATH=./models/qwen3-vl-8b-qlora-train-v1
export MODEL_ALIAS=qwen3-vl-8b-customer-service
export SERVICE_API_KEY=replace-with-a-secret
```

`SERVICE_API_KEY` is optional. When set, the chat endpoint requires
`Authorization: Bearer <token>`. Never commit the real value.

## Start

Run exactly one worker because each worker loads a separate copy of the model:

```bash
uvicorn service.app:app --host 0.0.0.0 --port 8000 --workers 1
```

Model loading occurs before the service becomes ready. Check readiness:

```bash
curl http://127.0.0.1:8000/health
```

Send a request:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SERVICE_API_KEY}" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "你是专业、耐心的中文电商客服。不要编造订单状态或平台政策。"
      },
      {
        "role": "user",
        "content": "订单 TEST-99-001 的物流一直没有更新，应该怎么办？"
      }
    ],
    "max_tokens": 256,
    "temperature": 0
  }'
```

The endpoint is compatible with the main structure of OpenAI chat completions, but
streaming and image payloads are not implemented. Requests are serialized with one
GPU lock to keep memory use predictable.

## HTTP contract test

The contract test replaces the GPU runtime with a deterministic fake and validates
readiness, bearer authentication, request parsing and response shape:

```bash
python -m pip install -r service/requirements-test.txt
python -m pytest -q tests/test_service_contract.py
```
