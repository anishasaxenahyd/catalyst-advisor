import type { RecommendationRequest, Report } from "../types/report";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

export async function requestRecommendation(request: RecommendationRequest): Promise<Report> {
  const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ?? `Request failed (${response.status})`);
  }

  return (await response.json()) as Report;
}
