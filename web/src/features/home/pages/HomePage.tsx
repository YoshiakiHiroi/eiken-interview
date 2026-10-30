import { useEffect } from "react";
import { Link } from "react-router";

import { useAuthStore } from "../../auth/store/authStore";
import { useGradeStore } from "../../grades/store/gradeStore";
import { ErrorMessage } from "../../../shared/components/ErrorMessage";

export function HomePage(): React.JSX.Element {
  const { grades, selected, error, load, select } = useGradeStore();
  const email = useAuthStore((state) => state.email);
  const signOut = useAuthStore((state) => state.signOut);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold">英検 面接練習</h1>
        <button
          type="button"
          className="text-xs text-gray-500 underline"
          onClick={() => void signOut()}
        >
          {email} からログアウト
        </button>
      </header>

      <ErrorMessage error={error} />

      {grades.length > 0 && (
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-600">級</span>
          <select
            className="rounded-lg border border-gray-300 px-3 py-2"
            value={selected ?? ""}
            onChange={(event) => select(event.target.value)}
          >
            {grades.map((grade) => (
              <option
                key={grade.grade}
                value={grade.grade}
              >
                {grade.label}
              </option>
            ))}
          </select>
        </label>
      )}

      <Link
        to="/interview"
        className="rounded-xl bg-blue-600 py-4 text-center text-lg font-bold text-white"
      >
        模擬面接を始める
      </Link>
    </div>
  );
}
