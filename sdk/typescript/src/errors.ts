export class MnemeError extends Error {
  readonly code: number;
  readonly data?: unknown;
  constructor(code: number, message: string, data?: unknown) {
    super(`${code}: ${message}`);
    this.name = "MnemeError";
    this.code = code;
    this.data = data;
  }
}
