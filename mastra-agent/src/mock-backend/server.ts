import { serve } from "@hono/node-server";
import { mockBackendApp } from "./app.js";

const port = Number(process.env.MOCK_BACKEND_PORT ?? 8001);

serve({ fetch: mockBackendApp.fetch, hostname: "127.0.0.1", port }, (info) => {
  console.log(`Mock backend listening on http://127.0.0.1:${info.port}`);
});
