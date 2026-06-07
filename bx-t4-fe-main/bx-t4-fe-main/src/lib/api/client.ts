export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly details?: unknown
  ) {
    super(message)
  }
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000/api/v1"

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  const isMultipart = typeof FormData !== "undefined" && init?.body instanceof FormData

  if (!headers.has("Content-Type") && init?.body && !isMultipart) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  })

  const text = await response.text()
  const data = text ? safeJson(text) : undefined

  if (!response.ok) {
    const parsed = parseApiError(data)
    throw new ApiError(parsed.message, response.status, parsed.code, parsed.details)
  }

  return data as T
}

export function parseApiError(data: unknown): { message: string; code?: string; details?: unknown } {
  if (typeof data === "object" && data && "error" in data) {
    const error = (data as { error?: { code?: string; message?: string; details?: unknown } }).error
    return {
      message: error?.message ?? "Request failed",
      code: error?.code,
      details: error?.details,
    }
  }
  if (typeof data === "object" && data && "detail" in data) {
    return { message: "Request validation failed", details: (data as { detail: unknown }).detail }
  }
  return { message: "Request failed" }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}
