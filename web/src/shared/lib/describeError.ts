import { ApiError } from "./apiClient";

export function describeError(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return "アクセス権がありません。許可されたアカウントでログインしてください。";
  }
  if (error instanceof ApiError && error.status === 401) {
    return "ログインの有効期限が切れました。再読み込みしてください。";
  }
  if (error instanceof TypeError) {
    return "サーバーに接続できませんでした。通信状況を確認してください。";
  }
  return error instanceof Error ? error.message : String(error);
}
