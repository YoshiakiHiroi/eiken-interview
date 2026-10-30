import { create } from "zustand";

import { apiRequest } from "../../../shared/lib/apiClient";
import type { Grade } from "../../../shared/types/api";

const SELECTED_GRADE_KEY = "eiken.selectedGrade";

interface GradeState {
  grades: Grade[];
  selected: string | null;
  error: unknown;
  load: () => Promise<void>;
  select: (grade: string) => void;
}

function readSavedGrade(): string | null {
  try {
    return window.localStorage.getItem(SELECTED_GRADE_KEY);
  } catch {
    return null;
  }
}

function saveGrade(grade: string): void {
  try {
    window.localStorage.setItem(SELECTED_GRADE_KEY, grade);
  } catch {
    // 保存できない環境（プライベートブラウズなど）では選択をその場限りにする
  }
}

export const useGradeStore = create<GradeState>((set, get) => ({
  grades: [],
  selected: null,
  error: null,
  load: async () => {
    if (get().grades.length > 0) {
      return;
    }
    try {
      const grades = await apiRequest<Grade[]>("/api/grades");
      const saved = readSavedGrade();
      const selected =
        grades.find((grade) => grade.grade === saved)?.grade ?? grades[0]?.grade ?? null;
      set({ grades, selected, error: null });
    } catch (error) {
      set({ error });
    }
  },
  select: (grade) => {
    saveGrade(grade);
    set({ selected: grade });
  },
}));

export function useSelectedGrade(): Grade | null {
  return useGradeStore(
    (state) => state.grades.find((grade) => grade.grade === state.selected) ?? null,
  );
}

export function useGradeConfig(gradeId: string | null): Grade | null {
  return useGradeStore((state) => state.grades.find((grade) => grade.grade === gradeId) ?? null);
}
