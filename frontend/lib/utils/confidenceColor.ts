export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "bg-green-500";
  if (confidence >= 0.4) return "bg-yellow-500";
  return "bg-red-500";
}

export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.7) return "High";
  if (confidence >= 0.4) return "Medium";
  return "Low";
}
