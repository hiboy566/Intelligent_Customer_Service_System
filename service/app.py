from __future__ import annotations

import asyncio
import hmac
import json
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from service.model_runtime import GpuOutOfMemoryError, ModelRuntime, Settings
from service.schemas import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    HealthResponse,
    ToolCall,
    ToolCallFunction,
    Usage,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    runtime = ModelRuntime(settings)
    await asyncio.to_thread(runtime.load)
    app.state.settings = settings
    app.state.runtime = runtime
    app.state.generation_lock = asyncio.Lock()
    yield


app = FastAPI(
    title="Intelligent Customer Service QLoRA API",
    version="1.0.0",
    lifespan=lifespan,
)


def authorize(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    expected = request.app.state.settings.api_key
    if expected is None:
        return
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid bearer token",
        )


@app.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    runtime: ModelRuntime = request.app.state.runtime
    return HealthResponse(
        status="ready",
        model=runtime.settings.model_alias,
        adapter=runtime.settings.adapter_path,
        device=str(runtime.device),
        quantization="bnb-4bit-nf4-double-quant",
    )


@app.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    dependencies=[Depends(authorize)],
)
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
):
    runtime: ModelRuntime = request.app.state.runtime
    messages = [message.model_dump() for message in payload.messages]

    async with request.app.state.generation_lock:
        try:
            text, prompt_tokens, completion_tokens = await asyncio.to_thread(
                runtime.generate,
                messages,
                max_tokens=payload.max_tokens,
                temperature=payload.temperature,
                top_p=payload.top_p,
                repetition_penalty=payload.repetition_penalty,
                tools=[tool.model_dump() for tool in payload.tools]
                if payload.tools
                else None,
            )
        except GpuOutOfMemoryError as error:
            raise HTTPException(status_code=503, detail="GPU out of memory") from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    response_message, finish_reason = build_assistant_message(text, payload)
    response = ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=payload.model or runtime.settings.model_alias,
        choices=[
            ChatChoice(
                message=response_message,
                finish_reason=finish_reason,
            )
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )
    if payload.stream:
        return StreamingResponse(
            stream_chat_completion(response),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return response


def build_assistant_message(
    text: str,
    payload: ChatCompletionRequest,
) -> tuple[ChatMessage, str]:
    if not payload.tools:
        return ChatMessage(role="assistant", content=text), "stop"

    parsed = extract_json_object(text)
    if isinstance(parsed, dict) and isinstance(parsed.get("tool_calls"), list):
        available = {tool.function.name for tool in payload.tools}
        tool_calls: list[ToolCall] = []
        for index, call in enumerate(parsed["tool_calls"]):
            if not isinstance(call, dict) or call.get("name") not in available:
                continue
            arguments = call.get("arguments", {})
            tool_calls.append(
                ToolCall(
                    id=f"call_{uuid.uuid4().hex}_{index}",
                    function=ToolCallFunction(
                        name=call["name"],
                        arguments=json.dumps(arguments, ensure_ascii=False),
                    ),
                )
            )
        if tool_calls:
            return (
                ChatMessage(role="assistant", content=None, tool_calls=tool_calls),
                "tool_calls",
            )

    if isinstance(parsed, dict) and isinstance(parsed.get("answer"), str):
        return ChatMessage(role="assistant", content=parsed["answer"].strip()), "stop"
    return ChatMessage(role="assistant", content=text), "stop"


def extract_json_object(text: str) -> dict[str, object] | None:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


async def stream_chat_completion(response: ChatCompletionResponse):
    choice = response.choices[0]
    message = choice.message
    delta = message.model_dump(
        exclude_none=True,
        exclude={"role"} if message.tool_calls is None else set(),
    )
    delta["role"] = "assistant"
    chunk = {
        "id": response.id,
        "object": "chat.completion.chunk",
        "created": response.created,
        "model": response.model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": choice.finish_reason,
            }
        ],
        "usage": response.usage.model_dump(),
    }
    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
