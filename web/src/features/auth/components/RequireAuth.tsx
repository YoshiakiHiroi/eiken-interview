import { Outlet } from "react-router";

import { LoginPage } from "../pages/LoginPage";
import { useAuthStore } from "../store/authStore";

export function RequireAuth(): React.JSX.Element {
  const status = useAuthStore((state) => state.status);

  if (status === "loading") {
    return <p className="p-4 text-center text-gray-500">読み込み中…</p>;
  }
  if (status === "signedOut") {
    return <LoginPage />;
  }
  return <Outlet />;
}
