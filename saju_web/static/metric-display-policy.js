export const GRADE_LABELS_ASCENDING = Object.freeze([
  "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+",
]);

export const GRADE_VISUAL_POSITIONS = Object.freeze({
  "D-": 24,
  D: 32,
  "D+": 37,
  "C-": 42,
  C: 47,
  "C+": 52,
  "B-": 57,
  B: 62,
  "B+": 67,
  "A-": 72,
  A: 77,
  "A+": 88,
});

export function gradeRank(grade) {
  return GRADE_LABELS_ASCENDING.indexOf(String(grade || "").trim());
}

export function gradeFromQualityScore(score, fallback = "") {
  if (!Number.isFinite(score)) return fallback;
  const safeScore = Math.max(0, Math.min(100, Math.round(score)));
  if (safeScore >= 80) return "A+";
  if (safeScore >= 75) return "A";
  if (safeScore >= 70) return "A-";
  if (safeScore >= 65) return "B+";
  if (safeScore >= 60) return "B";
  if (safeScore >= 55) return "B-";
  if (safeScore >= 50) return "C+";
  if (safeScore >= 45) return "C";
  if (safeScore >= 40) return "C-";
  if (safeScore >= 35) return "D+";
  if (safeScore >= 30) return "D";
  return "D-";
}

export function gradeFromAverage(grades, fallback = "") {
  const ranks = Array.isArray(grades)
    ? grades.map(gradeRank).filter((rank) => rank >= 0)
    : [];
  if (!ranks.length) return fallback;
  const averageRank = ranks.reduce((sum, rank) => sum + rank, 0) / ranks.length;
  const roundedRank = Math.max(0, Math.min(GRADE_LABELS_ASCENDING.length - 1, Math.floor(averageRank + 0.5)));
  return GRADE_LABELS_ASCENDING[roundedRank];
}

export function displayPolicyForAverageGrade(rawAverageGrade) {
  const grade = String(rawAverageGrade || "").trim();
  if (["D-", "D", "D+"].includes(grade)) return "all-plus-b";
  if (grade === "C-") return "all-plus-b";
  if (["C", "C+", "B-"].includes(grade)) return "highlight-b-plus-a-minus-b-minus";
  if (["B", "B+", "A-"].includes(grade)) return "highlight-a";
  return "none";
}

export function buildDisplayAdjustment(grades) {
  const validGrades = Array.isArray(grades)
    ? grades.filter((grade) => gradeRank(grade) >= 0)
    : [];
  const rawAverageGrade = gradeFromAverage(validGrades, "");
  const rawAverageRank = validGrades.length
    ? validGrades.reduce((sum, grade) => sum + gradeRank(grade), 0) / validGrades.length
    : null;
  return Object.freeze({
    rawAverageRank,
    rawAverageGrade,
    averageMethod: "grade-rank-mean",
    policy: displayPolicyForAverageGrade(rawAverageGrade),
    unitCount: validGrades.length,
  });
}

export function displayBoostSteps(rawGrade, adjustment) {
  const grade = String(rawGrade || "").trim();
  const policy = String(adjustment && adjustment.policy || "none");
  if (gradeRank(grade) < 0 || policy === "none") return 0;
  if (policy === "all-plus-b") {
    return gradeRank(grade) >= gradeRank("B") ? 2 : 1;
  }
  if (policy === "all") return 1;
  if (policy === "highlight-b-plus-a-minus-b-minus") {
    return ["B-", "B+", "A-"].includes(grade) ? 1 : 0;
  }
  if (policy === "highlight-a") return grade === "A" ? 1 : 0;
  return 0;
}

export function displayGradeForRawGrade(rawGrade, adjustment) {
  const sourceRank = gradeRank(rawGrade);
  if (sourceRank < 0) return "";
  const targetRank = Math.min(
    GRADE_LABELS_ASCENDING.length - 1,
    sourceRank + displayBoostSteps(rawGrade, adjustment),
  );
  return GRADE_LABELS_ASCENDING[targetRank];
}

export function visualPositionForGrade(grade) {
  const value = Number(GRADE_VISUAL_POSITIONS[grade]);
  return Number.isFinite(value) ? value : null;
}

export function semanticStateForGrade(grade) {
  const rank = gradeRank(grade);
  if (rank >= gradeRank("B+")) return "good";
  if (rank >= 0 && rank < gradeRank("C")) return "bad";
  return "normal";
}
