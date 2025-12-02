const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function getBaseUrl(): string {
  const envUrl = import.meta.env.VITE_MINICARS_BACKEND_URL as string | undefined;
  return envUrl && envUrl.length > 0 ? envUrl : DEFAULT_BASE_URL;
}

export const API_BASE_URL = getBaseUrl();

type StatusResponse = {
  stream: string;
  car_control: string;
};

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

export function getStatus(): Promise<StatusResponse> {
  return request<StatusResponse>("/status");
}

export function startStream(): Promise<Record<string, unknown>> {
  return request("/actions/start_stream", { method: "POST" });
}

export function stopStream(): Promise<Record<string, unknown>> {
  return request("/actions/stop_stream", { method: "POST" });
}

export function startReceiver(): Promise<Record<string, unknown>> {
  return request("/actions/start_receiver", { method: "POST" });
}

export function stopReceiver(): Promise<Record<string, unknown>> {
  return request("/actions/stop_receiver", { method: "POST" });
}

export function startCarControl(): Promise<Record<string, unknown>> {
  return request("/actions/start_car_control", { method: "POST" });
}

export function stopCarControl(): Promise<Record<string, unknown>> {
  return request("/actions/stop_car_control", { method: "POST" });
}


