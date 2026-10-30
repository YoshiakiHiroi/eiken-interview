import type { CardKind, ProblemSet } from "../types/api";

interface ProblemCardProps {
  card: CardKind;
  problemSet: ProblemSet;
}

const PICTURE_LABELS: Record<"picture_a" | "picture_b", string> = {
  picture_a: "Picture A",
  picture_b: "Picture B",
};

export function ProblemCard({ card, problemSet }: ProblemCardProps): React.JSX.Element | null {
  if (card === "none") {
    return null;
  }
  if (card === "passage") {
    return (
      <article className="rounded-xl border border-gray-300 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-center font-bold">{problemSet.passage.title}</h2>
        <p className="text-lg leading-relaxed">{problemSet.passage.text}</p>
      </article>
    );
  }

  const question = problemSet.questions.find((item) => item.type === card);
  return (
    <figure className="rounded-xl border border-gray-300 bg-white p-2 shadow-sm">
      <figcaption className="mb-1 text-sm font-semibold text-gray-600">
        {PICTURE_LABELS[card]}
      </figcaption>
      {question?.picture_url ? (
        <img
          src={question.picture_url}
          alt={PICTURE_LABELS[card]}
          className="w-full rounded-lg"
        />
      ) : (
        <div className="flex aspect-[4/3] items-center justify-center rounded-lg bg-gray-100 p-4 text-center text-sm text-gray-500">
          イラストは未生成です（問題セット生成後に表示されます）
        </div>
      )}
    </figure>
  );
}
