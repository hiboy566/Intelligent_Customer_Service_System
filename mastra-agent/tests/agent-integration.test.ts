import type { AddressInfo } from "node:net";
import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { mockBackendApp } from "../src/mock-backend/app.js";

let backendServer: ReturnType<typeof serve>;
let qloraServer: ReturnType<typeof serve>;
let qloraRequests = 0;
let sawToolResult = false;

const fakeQlora = new Hono();
fakeQlora.post("/v1/chat/completions", async (context) => {
  qloraRequests += 1;
  const body = (await context.req.json()) as {
    model: string;
    messages: Array<{ role: string; content?: string }>;
    tools?: Array<{ function: { name: string; description?: string } }>;
  };
  const toolMessage = body.messages.find((message) => message.role === "tool");
  sawToolResult ||= Boolean(
    toolMessage?.content?.includes('"delayed":true') ||
      toolMessage?.content?.includes("物流信息超过 48 小时未更新"),
  );
  const toolName = body.tools?.find((tool) =>
    tool.function.description?.includes("运单号"),
  )?.function.name;

  const message = toolMessage
    ? {
        role: "assistant",
        content: "订单 TEST-02-024 的物流已超过 48 小时未更新，建议发起催件。",
      }
    : {
        role: "assistant",
        content: null,
        tool_calls: [
          {
            id: "call_fake_logistics",
            type: "function",
            function: {
              name: toolName,
              arguments: JSON.stringify({ orderId: "TEST-02-024" }),
            },
          },
        ],
      };

  return context.json({
    id: `chatcmpl-fake-${qloraRequests}`,
    object: "chat.completion",
    created: Math.floor(Date.now() / 1000),
    model: body.model,
    choices: [
      {
        index: 0,
        message,
        finish_reason: toolMessage ? "stop" : "tool_calls",
      },
    ],
    usage: { prompt_tokens: 20, completion_tokens: 10, total_tokens: 30 },
  });
});

beforeAll(async () => {
  backendServer = serve({ fetch: mockBackendApp.fetch, hostname: "127.0.0.1", port: 0 });
  qloraServer = serve({ fetch: fakeQlora.fetch, hostname: "127.0.0.1", port: 0 });
  await Promise.all([
    new Promise<void>((resolve) => backendServer.once("listening", resolve)),
    new Promise<void>((resolve) => qloraServer.once("listening", resolve)),
  ]);
  const backendPort = (backendServer.address() as AddressInfo).port;
  const qloraPort = (qloraServer.address() as AddressInfo).port;
  process.env.MOCK_BACKEND_URL = `http://127.0.0.1:${backendPort}`;
  process.env.QLORA_BASE_URL = `http://127.0.0.1:${qloraPort}/v1`;
  process.env.QLORA_MODEL = "fake-qlora";
});

afterAll(() => {
  backendServer.close();
  qloraServer.close();
});

describe("Mastra agent integration", () => {
  it("calls a mock backend tool through an OpenAI-compatible QLoRA endpoint", async () => {
    const { customerServiceAgent } = await import(
      "../src/mastra/agents/customer-service-agent.js"
    );
    const result = await customerServiceAgent.generate(
      "查询订单 TEST-02-024 的物流",
      { maxSteps: 5 },
    );

    expect(result.text).toContain("超过 48 小时未更新");
    expect(qloraRequests).toBe(2);
    expect(sawToolResult).toBe(true);
  });
});
