# Mastra customer-service agent

This TypeScript service uses Mastra with the local QLoRA OpenAI-compatible endpoint and
four typed tools backed by a mock order API.

## Architecture

```text
Mastra Agent (:4111)
  ├─ local QLoRA /v1/chat/completions (:8000)
  └─ mock backend (:8001)
       ├─ query_order
       ├─ query_logistics
       ├─ query_refund
       └─ create_support_ticket
```

The QLoRA service translates the model's strict JSON decision into OpenAI-compatible
`tool_calls`. Mastra executes the selected typed tool and sends the result back to the
model for the final customer-facing answer.

## Install

```bash
cd mastra-agent
npm install
cp .env.example .env
```

## Run

Start the QLoRA service from the repository root:

```bash
uvicorn service.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Start the mock backend and Mastra in two terminals:

```bash
cd mastra-agent
npm run mock
npm run dev
```

Mastra Studio and its agent API are then available from the URL printed by `mastra
dev` (normally port 4111). A direct CLI smoke request can be sent with:

```bash
npm run chat -- "帮我查询订单 TEST-02-024 的物流，并创建催件工单"
```

## Test

```bash
npm run typecheck
npm test
npm run build
```

The backend is intentionally mock data. Do not expose its mutation endpoints as a real
order system. In production, replace `backendRequest` with an authenticated internal
API client and require human approval for consequential tools.

The integration test starts a fake OpenAI-compatible QLoRA endpoint plus the real mock
backend and verifies the complete Mastra model → tool → backend → model loop.
