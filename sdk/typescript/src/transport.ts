import { MnemeError } from "./errors.js";

export interface TransportOptions {
  fetch?: typeof fetch;
  headers?: Record<string, string>;
}

export class JsonRpcTransport {
  private readonly url: string;
  private readonly fetchImpl: typeof fetch;
  private readonly headers: Record<string, string>;
  private id = 0;

  constructor(baseUrl: string, opts: TransportOptions = {}) {
    this.url = baseUrl.replace(/\/$/, "") + "/api/v1/jsonrpc";
    this.fetchImpl = opts.fetch ?? fetch;
    this.headers = { "content-type": "application/json", ...(opts.headers ?? {}) };
  }

  async call<T = unknown>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    const res = await this.fetchImpl(this.url, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ jsonrpc: "2.0", id: ++this.id, method, params }),
    });
    if (!res.ok) {
      throw new MnemeError(res.status, `HTTP ${res.status} ${res.statusText}`);
    }
    const body = (await res.json()) as { result?: T; error?: { code: number; message: string; data?: unknown } };
    if (body.error) {
      throw new MnemeError(body.error.code, body.error.message, body.error.data);
    }
    return body.result as T;
  }
}
