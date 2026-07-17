export const config = {
  qloraBaseUrl: process.env.QLORA_BASE_URL ?? "http://127.0.0.1:8000/v1",
  qloraApiKey: process.env.QLORA_API_KEY || "local-no-auth",
  qloraModel: process.env.QLORA_MODEL ?? "qwen3-vl-8b-customer-service",
  mockBackendUrl: process.env.MOCK_BACKEND_URL ?? "http://127.0.0.1:8001",
};
