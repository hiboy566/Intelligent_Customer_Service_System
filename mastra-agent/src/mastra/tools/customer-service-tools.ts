import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { backendRequest } from "../../backend-client.js";

const orderIdSchema = z
  .string()
  .regex(/^TEST-\d{2}-\d{3}$/, "订单号格式应为 TEST-00-000");

export const queryOrderTool = createTool({
  id: "query_order",
  description: "根据订单号查询商品、订单状态和支付金额。不得猜测订单信息。",
  inputSchema: z.object({ orderId: orderIdSchema }),
  execute: async (input) =>
    backendRequest(`/orders/${encodeURIComponent(input.orderId)}`),
});

export const queryLogisticsTool = createTool({
  id: "query_logistics",
  description: "查询指定订单的承运商、运单号、最新物流轨迹和是否延迟。",
  inputSchema: z.object({ orderId: orderIdSchema }),
  execute: async (input) =>
    backendRequest(`/orders/${encodeURIComponent(input.orderId)}/logistics`),
});

export const queryRefundTool = createTool({
  id: "query_refund",
  description: "查询指定订单的退款资格和当前退款状态。",
  inputSchema: z.object({ orderId: orderIdSchema }),
  execute: async (input) =>
    backendRequest(`/orders/${encodeURIComponent(input.orderId)}/refund`),
});

export const createSupportTicketTool = createTool({
  id: "create_support_ticket",
  description:
    "仅当用户明确要求人工处理、催件或创建工单时，为已存在的订单创建客服工单。",
  inputSchema: z.object({
    orderId: orderIdSchema,
    issue: z.string().min(3).max(300),
  }),
  execute: async (input) =>
    backendRequest("/tickets", {
      method: "POST",
      body: JSON.stringify(input),
    }),
});
