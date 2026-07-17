from __future__ import annotations

import asyncio
import hmac
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from service.model_runtime import GpuOutOfMemoryError, ModelRuntime, Settings
from service.schemas import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    HealthResponse,
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
) -> ChatCompletionResponse:
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
            )
        except GpuOutOfMemoryError as error:
            raise HTTPException(status_code=503, detail="GPU out of memory") from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=payload.model or runtime.settings.model_alias,
        choices=[
            ChatChoice(
                message=ChatMessage(role="assistant", content=text),
            )
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )
