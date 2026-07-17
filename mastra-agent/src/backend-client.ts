import { config } from "./config.js";

export async function backendRequest(
  path: string,
  init?: RequestInit,
): Promise<Record<string, unknown>> {
  const response = await fetch(`${config.mockBackendUrl}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...init?.headers },
    signal: AbortSignal.timeout(5_000),
  });
  const body = (await response.json()) as Record<string, unknown>;
  return { httpStatus: response.status, ...body };
}
