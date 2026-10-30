import { CONFIG } from "./config";
import { firebaseAuth } from "./firebase";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function authHeader(): Promise<Record<string, string>> {
  const user = firebaseAuth.currentUser;
  if (!user) {
    throw new ApiError(401, "ログインしていません");
  }
  return { Authorization: `Bearer ${await user.getIdToken()}` };
}

async function readError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      return String(body.detail);
    }
  } catch {
    // 本文が JSON でない場合はステータス文言を使う
  }
  return response.statusText;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${CONFIG.apiBaseUrl}${path}`, {
    ...init,
    headers: { ...(await authHeader()), ...init.headers },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await readError(response));
  }
  return (await response.json()) as T;
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
