import { Hono } from "hono";
import { z } from "zod";

const orders = {
  "TEST-01-021": {
    orderId: "TEST-01-021",
    product: "机械键盘",
    status: "shipped",
    paidAmount: 399,
    currency: "CNY",
    logistics: {
      carrier: "顺丰速运",
      trackingNumber: "MOCK-SF-100021",
      lastEvent: "快件已到达上海转运中心",
      lastUpdatedAt: "2026-07-17T08:30:00+08:00",
      delayed: false,
    },
    refund: { status: "not_requested", refundable: true },
  },
  "TEST-02-024": {
    orderId: "TEST-02-024",
    product: "蓝牙耳机",
    status: "shipping_delayed",
    paidAmount: 259,
    currency: "CNY",
    logistics: {
      carrier: "中通快递",
      trackingNumber: "MOCK-ZTO-200024",
      lastEvent: "运输途中，物流信息超过 48 小时未更新",
      lastUpdatedAt: "2026-07-14T15:20:00+08:00",
      delayed: true,
    },
    refund: { status: "not_requested", refundable: true },
  },
  "TEST-03-031": {
    orderId: "TEST-03-031",
    product: "显示器支架",
    status: "refunding",
    paidAmount: 189,
    currency: "CNY",
    logistics: null,
    refund: {
      status: "processing",
      refundable: false,
      requestedAt: "2026-07-16T10:00:00+08:00",
    },
  },
} as const;

const ticketSchema = z.object({
  orderId: z.string().regex(/^TEST-\d{2}-\d{3}$/),
  issue: z.string().min(3).max(300),
});

const tickets: Array<{
  ticketId: string;
  orderId: string;
  issue: string;
  status: "open";
}> = [];

export const mockBackendApp = new Hono();

mockBackendApp.get("/health", (context) => context.json({ status: "ok" }));

mockBackendApp.get("/orders/:orderId", (context) => {
  const orderId = context.req.param("orderId") as keyof typeof orders;
  const order = orders[orderId];
  return order
    ? context.json({ ok: true, order })
    : context.json({ ok: false, error: "order_not_found" }, 404);
});

mockBackendApp.get("/orders/:orderId/logistics", (context) => {
  const orderId = context.req.param("orderId") as keyof typeof orders;
  const order = orders[orderId];
  if (!order) return context.json({ ok: false, error: "order_not_found" }, 404);
  if (!order.logistics) {
    return context.json({ ok: false, error: "logistics_not_available" }, 409);
  }
  return context.json({ ok: true, orderId, logistics: order.logistics });
});

mockBackendApp.get("/orders/:orderId/refund", (context) => {
  const orderId = context.req.param("orderId") as keyof typeof orders;
  const order = orders[orderId];
  return order
    ? context.json({ ok: true, orderId, refund: order.refund })
    : context.json({ ok: false, error: "order_not_found" }, 404);
});

mockBackendApp.post("/tickets", async (context) => {
  const parsed = ticketSchema.safeParse(await context.req.json());
  if (!parsed.success) {
    return context.json(
      { ok: false, error: "invalid_ticket", details: parsed.error.issues },
      400,
    );
  }
  if (!(parsed.data.orderId in orders)) {
    return context.json({ ok: false, error: "order_not_found" }, 404);
  }
  const ticket = {
    ticketId: `MOCK-TICKET-${String(tickets.length + 1).padStart(4, "0")}`,
    orderId: parsed.data.orderId,
    issue: parsed.data.issue,
    status: "open" as const,
  };
  tickets.push(ticket);
  return context.json({ ok: true, ticket }, 201);
});
