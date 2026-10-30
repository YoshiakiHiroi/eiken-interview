import { RouterProvider } from "react-router";

import { router } from "./routes";

export function App(): React.JSX.Element {
  return (
    <div className="mx-auto min-h-dvh max-w-md bg-gray-50 p-4 text-gray-900">
      <RouterProvider router={router} />
    </div>
  );
}
