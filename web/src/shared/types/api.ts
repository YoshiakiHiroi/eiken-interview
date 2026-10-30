export type PartType =
  | "silent_reading"
  | "read_aloud"
  | "passage_question"
  | "picture_actions"
  | "picture_situation"
  | "picture_story"
  | "opinion"
  | "personal";
export type CardKind = "passage" | "picture_a" | "picture_b" | "none";
export type SessionMode = "full" | "drill_read" | "drill_q2" | "drill_q3" | "drill_q45";
export type YesNo = "yes" | "no";
export type Clarity = "clear" | "somewhat_unclear" | "unclear";
export type Phrase = string | string[];

export interface GradePart {
  id: string;
  label: string;
  type: PartType;
  card: CardKind;
  cue_phrases: string[];
  seconds: number | null;
  prep_seconds: number | null;
  question_no: number | null;
  follow_up: boolean;
  max_score: number;
}

export interface Grade {
  grade: string;
  label: string;
  test_name: string;
  pass_score: number;
  attitude_max_score: number;
  phrases: Record<string, Phrase>;
  opening_phrases: string[];
  closing_phrases: string[];
  parts: GradePart[];
  max_score_total: number;
}

export interface Passage {
  title: string;
  text: string;
  key_sentence: string;
  audio_model_url: string | null;
}

export interface Question {
  no: number;
  type: string;
  text: string;
  audio_url: string | null;
  model_answer: string | null;
  picture_url: string | null;
  actions: string[] | null;
  follow_up_yes: string | null;
  follow_up_no: string | null;
  model_answer_yes: string | null;
  model_answer_no: string | null;
  follow_up_audio_yes_url: string | null;
  follow_up_audio_no_url: string | null;
}

export interface ProblemSet {
  id: string;
  grade: string;
  enabled: boolean;
  topic: string;
  voice: string;
  passage: Passage;
  questions: Question[];
  common_audio: Record<string, string>;
  usage_count: number;
}

export interface Answer {
  part: string;
  audio_url: string;
  follow_up_audio_url: string | null;
  duration_sec: number;
  silence_before_sec: number;
  replay_count: number;
  yes_no: YesNo | null;
  transcript: string | null;
  score: number | null;
  feedback_ja: string | null;
  model_answer: string | null;
  issue_tags: string[];
  confidence: number | null;
  clarity: Clarity | null;
  evaluation_error: string | null;
}

export interface Attitude {
  score: number | null;
  feedback_ja: string | null;
  evaluation_error: string | null;
}

export interface Session {
  id: string;
  uid: string;
  grade: string;
  mode: SessionMode;
  set_id: string;
  started_at: string;
  finished_at: string | null;
  answers: Answer[];
  attitude: Attitude | null;
  total: number | null;
  passed: boolean | null;
}
