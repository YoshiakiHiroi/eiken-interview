import { createBrowserRouter } from "react-router";

import { RequireAuth } from "../features/auth/components/RequireAuth";
import { HomePage } from "../features/home/pages/HomePage";
import { InterviewPage } from "../features/interview/pages/InterviewPage";
import { ResultPage } from "../features/interview/pages/ResultPage";

export const router = createBrowserRouter([
  {
    element: <RequireAuth />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/interview", element: <InterviewPage /> },
      { path: "/interview/result/:sessionId", element: <ResultPage /> },
    ],
  },
]);
