import type { Prompt } from "../../../shared/lib/audio";
import type {
  CardKind,
  Grade,
  GradePart,
  Phrase,
  ProblemSet,
  Question,
  YesNo,
} from "../../../shared/types/api";

export type InterviewStep =
  | { kind: "phrase"; phraseKey: string; card: CardKind; part: GradePart | null }
  | { kind: "timer"; seconds: number; card: CardKind; part: GradePart }
  | { kind: "answer"; card: CardKind; part: GradePart };

export function phraseText(phrase: Phrase | undefined): string {
  if (phrase === undefined) {
    return "";
  }
  return typeof phrase === "string" ? phrase : phrase.join(" ");
}

export function buildInterviewSteps(grade: Grade): InterviewStep[] {
  const steps: InterviewStep[] = grade.opening_phrases.map((phraseKey) => ({
    kind: "phrase",
    phraseKey,
    card: "none",
    part: null,
  }));
  for (const part of grade.parts) {
    for (const phraseKey of part.cue_phrases) {
      steps.push({ kind: "phrase", phraseKey, card: part.card, part });
    }
    if (part.seconds !== null && part.max_score === 0) {
      steps.push({ kind: "timer", seconds: part.seconds, card: part.card, part });
    } else if (part.max_score > 0) {
      steps.push({ kind: "answer", card: part.card, part });
    }
  }
  for (const phraseKey of grade.closing_phrases) {
    steps.push({ kind: "phrase", phraseKey, card: "none", part: null });
  }
  return steps;
}

export function scoredParts(grade: Grade): GradePart[] {
  return grade.parts.filter((part) => part.max_score > 0);
}

export function findQuestion(problemSet: ProblemSet, part: GradePart): Question | null {
  if (part.question_no === null) {
    return null;
  }
  return problemSet.questions.find((question) => question.no === part.question_no) ?? null;
}

export function phrasePrompt(grade: Grade, problemSet: ProblemSet, phraseKey: string): Prompt {
  return {
    url: problemSet.common_audio[phraseKey] ?? null,
    text: phraseText(grade.phrases[phraseKey]),
  };
}

export function questionPrompt(question: Question | null): Prompt | null {
  return question ? { url: question.audio_url, text: question.text } : null;
}

export function followUpPrompt(question: Question | null, yesNo: YesNo): Prompt | null {
  if (!question) {
    return null;
  }
  const text = yesNo === "yes" ? question.follow_up_yes : question.follow_up_no;
  const url = yesNo === "yes" ? question.follow_up_audio_yes_url : question.follow_up_audio_no_url;
  return text ? { url, text } : null;
}
