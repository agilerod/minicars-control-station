import { API_BASE_URL } from "./client";

export type DrivingModeId = "kid" | "normal" | "sport";

export interface ControlProfile {
  active_mode: DrivingModeId;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore JSON parse errors; data stays null
  }

  if (!response.ok) {
    const message =
      typeof data?.message === "string"
        ? data.message
        : data?.detail
        ? JSON.stringify(data.detail)
        : `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data as T;
}

export async function fetchControlProfile(): Promise<ControlProfile> {
  return request<ControlProfile>("/control/profile");
}

export async function updateControlProfile(
  activeMode: DrivingModeId
): Promise<ControlProfile> {
  return request<ControlProfile>("/control/profile", {
    method: "POST",
    body: JSON.stringify({ active_mode: activeMode }),
  });
}

