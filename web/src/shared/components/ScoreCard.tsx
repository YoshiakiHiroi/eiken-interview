import type { Grade, Session } from "../types/api";

interface ScoreCardProps {
  grade: Grade;
  session: Session;
}

function formatScore(score: number | null | undefined, max: number): string {
  return `${score ?? "－"} / ${max}`;
}

export function ScoreCard({ grade, session }: ScoreCardProps): React.JSX.Element {
  const scoreByPart = new Map(session.answers.map((answer) => [answer.part, answer.score]));
  const scoredParts = grade.parts.filter((part) => part.max_score > 0);
  const isFull = session.mode === "full";
  const maxTotal = isFull
    ? grade.max_score_total
    : scoredParts
        .filter((part) => scoreByPart.has(part.id))
        .reduce((sum, part) => sum + part.max_score, 0);

  return (
    <section className="flex flex-col gap-3 rounded-xl border border-gray-300 bg-white p-4">
      <div className="text-center">
        <p className="text-4xl font-bold tabular-nums">{formatScore(session.total, maxTotal)}</p>
        {isFull && (
          <p
            className={
              session.passed === null
                ? "text-gray-500"
                : session.passed
                  ? "font-bold text-green-700"
                  : "font-bold text-red-700"
            }
          >
            {session.passed === null
              ? "採点が終わっていないパートがあります"
              : session.passed
                ? "合格ライン到達"
                : "合格ライン未達"}
            （合格目安 {grade.pass_score} 点）
          </p>
        )}
      </div>
      <table className="w-full text-sm">
        <tbody>
          {scoredParts
            .filter((part) => isFull || scoreByPart.has(part.id))
            .map((part) => (
              <tr
                key={part.id}
                className="border-t"
              >
                <th className="py-1 text-left font-normal">{part.label}</th>
                <td className="py-1 text-right tabular-nums">
                  {formatScore(scoreByPart.get(part.id), part.max_score)}
                </td>
              </tr>
            ))}
          {isFull && (
            <tr className="border-t">
              <th className="py-1 text-left font-normal">アティチュード</th>
              <td className="py-1 text-right tabular-nums">
                {formatScore(session.attitude?.score, grade.attitude_max_score)}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
