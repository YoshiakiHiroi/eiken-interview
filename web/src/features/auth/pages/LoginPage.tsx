import { useAuthStore } from "../store/authStore";

export function LoginPage(): React.JSX.Element {
  const signIn = useAuthStore((state) => state.signIn);
  const error = useAuthStore((state) => state.error);

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 p-4">
      <h1 className="text-2xl font-bold">英検 面接練習</h1>
      <button
        type="button"
        className="rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white"
        onClick={() => void signIn()}
      >
        Google でログイン
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
