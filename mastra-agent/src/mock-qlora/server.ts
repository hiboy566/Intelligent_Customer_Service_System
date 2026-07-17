import { serve } from "@hono/node-server";
import { Hono } from "hono";

type ToolDefinition = {
  function: { name: string; description?: string };
};

type ChatMessage = {
  role: string;
  content?: string;
  name?: string;
};

const app = new Hono();

app.get("/health", (context) =>
  context.json({ status: "ok", mode: "local-qlora-stub" }),
);

app.post("/v1/chat/completions", async (context) => {
  const body = (await context.req.json()) as {
    model: string;
    messages: ChatMessage[];
    tools?: ToolDefinition[];
    stream?: boolean;
  };
  const userText = body.messages
    .filter((message) => message.role === "user")
    .map((message) => message.content ?? "")
    .join("\n");
  const orderId = userText.match(/TEST-\d{2}-\d{3}/)?.[0] ?? "TEST-01-021";
  const toolMessages = body.messages.filter((message) => message.role === "tool");
  const availableTools = body.tools ?? [];
  const findTool = (keyword: string) =>
    availableTools.find((tool) =>
      tool.function.description?.includes(keyword),
    )?.function.name;

  let toolName: string | undefined;
  let argumentsValue: Record<string, string> = { orderId };
  if (toolMessages.length === 0) {
    if (userText.includes("退款")) toolName = findTool("退款资格");
    else if (userText.includes("物流") || userText.includes("催件")) {
      toolName = findTool("运单号");
    } else toolName = findTool("支付金额");
  } else if (
    (userText.includes("工单") || userText.includes("催件")) &&
    toolMessages.length === 1
  ) {
    toolName = findTool("创建客服工单");
    argumentsValue = { orderId, issue: "用户明确要求人工催件" };
  }

  const message = toolName
    ? {
        role: "assistant",
        content: null,
        tool_calls: [
          {
            id: `call_stub_${Date.now()}`,
            type: "function",
            function: {
              name: toolName,
              arguments: JSON.stringify(argumentsValue),
            },
          },
        ],
      }
    : {
        role: "assistant",
        content: summarizeToolResult(toolMessages.at(-1)?.content ?? ""),
      };

  const completion = {
    id: `chatcmpl-stub-${Date.now()}`,
    object: "chat.completion",
    created: Math.floor(Date.now() / 1000),
    model: body.model,
    choices: [
      {
        index: 0,
        message,
        finish_reason: toolName ? "tool_calls" : "stop",
      },
    ],
    usage: { prompt_tokens: 20, completion_tokens: 20, total_tokens: 40 },
  };
  if (body.stream) {
    const choice = completion.choices[0]!;
    const chunk = {
      id: completion.id,
      object: "chat.completion.chunk",
      created: completion.created,
      model: completion.model,
      choices: [
        {
          index: 0,
          delta: choice.message,
          finish_reason: choice.finish_reason,
        },
      ],
      usage: completion.usage,
    };
    return context.body(`data: ${JSON.stringify(chunk)}\n\ndata: [DONE]\n\n`, 200, {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
    });
  }
  return context.json(completion);
});

function summarizeToolResult(content: string): string {
  if (content.includes("MOCK-TICKET-")) {
    const ticketId = content.match(/MOCK-TICKET-\d+/)?.[0] ?? "已创建";
    return `催件工单已创建，工单号为 ${ticketId}。请留意后续处理进度。`;
  }
  if (content.includes('"delayed":true')) {
    return "查询到物流信息已超过 48 小时未更新。如需人工催件，请明确告诉我创建催件工单。";
  }
  if (content.includes('"status":"processing"')) {
    return "该订单退款正在处理中，请通过官方订单页面查看最新进度。";
  }
  if (content.includes("order_not_found")) {
    return "没有查询到该订单，请核对脱敏订单号后重试。";
  }
  return `后端查询完成：${content}`;
}

const port = Number(process.env.MOCK_QLORA_PORT ?? 8000);
serve({ fetch: app.fetch, hostname: "127.0.0.1", port }, (info) => {
  console.log(`Local QLoRA stub listening on http://127.0.0.1:${info.port}`);
});
