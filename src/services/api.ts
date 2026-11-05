import type { AdvancedData, Analysis, Overview, Player, Position, RecommendationResponse } from "@/types/api";

const API_URL = (import.meta.env.VITE_FPL_API_URL as string | undefined)?.replace(/\/$/, "");

class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  if (!API_URL) throw new ApiError("VITE_FPL_API_URL is not configured.");
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === "AbortError") throw reason;
    throw new ApiError("The FPL API is unavailable. Check that the backend is running.");
  }
  if (!response.ok) {
    let message = `The API returned ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the HTTP status message when the server response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

export const getOverview = (signal?: AbortSignal) => request<Overview>("/api/data/overview", { signal });
export const getAdvancedData = (signal?: AbortSignal) => request<AdvancedData>("/api/data/advanced", { signal });
export const getPlayers = (signal?: AbortSignal) => getAdvancedData(signal).then((data) => data.players);
export const getAnalysis = (name: string, signal?: AbortSignal) =>
  request<Analysis>(`/api/analyze-player?name=${encodeURIComponent(name)}`, { signal });
export const getRecommendations = (budget: number, position: Position, signal?: AbortSignal) =>
  request<RecommendationResponse>("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ budget, position }),
    signal,
  });
