import { describeError } from "../lib/describeError";

interface ErrorMessageProps {
  error: unknown;
}

export function ErrorMessage({ error }: ErrorMessageProps): React.JSX.Element | null {
  if (!error) {
    return null;
  }
  return (
    <p
      role="alert"
      className="rounded-lg bg-red-50 p-3 text-sm text-red-700"
    >
      {describeError(error)}
    </p>
  );
}
