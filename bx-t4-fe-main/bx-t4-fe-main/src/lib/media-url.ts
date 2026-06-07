const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000"

export function buildMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null
  if (url.startsWith("data:") || url.startsWith("blob:")) return url
  if (url.startsWith("http://") || url.startsWith("https://")) return url
  if (url.startsWith("/")) return `${BACKEND_BASE_URL}${url}`
  return `${BACKEND_BASE_URL}/${url}`
}
