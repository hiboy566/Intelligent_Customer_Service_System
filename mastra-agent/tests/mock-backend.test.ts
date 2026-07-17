import { describe, expect, it } from "vitest";
import { mockBackendApp } from "../src/mock-backend/app.js";

describe("mock backend", () => {
  it("queries an order and its logistics", async () => {
    const order = await mockBackendApp.request("/orders/TEST-01-021");
    expect(order.status).toBe(200);
    expect((await order.json()).order.status).toBe("shipped");

    const logistics = await mockBackendApp.request(
      "/orders/TEST-02-024/logistics",
    );
    expect(logistics.status).toBe(200);
    expect((await logistics.json()).logistics.delayed).toBe(true);
  });

  it("returns a controlled error for an unknown order", async () => {
    const response = await mockBackendApp.request("/orders/TEST-99-999");
    expect(response.status).toBe(404);
    expect(await response.json()).toEqual({
      ok: false,
      error: "order_not_found",
    });
  });

  it("creates a support ticket", async () => {
    const response = await mockBackendApp.request("/tickets", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        orderId: "TEST-02-024",
        issue: "用户明确要求人工催件",
      }),
    });
    expect(response.status).toBe(201);
    expect((await response.json()).ticket.ticketId).toMatch(/^MOCK-TICKET-/);
  });
});
