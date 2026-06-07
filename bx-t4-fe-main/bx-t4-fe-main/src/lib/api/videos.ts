import { apiFetch } from "@/lib/api/client"
import type {
  ClaimResponse,
  ProductResponse,
  TimelineWindow,
  TranscriptResponse,
  UploadResponse,
  VideoMetricsResponse,
  VideoResponse,
} from "@/lib/api/types"

export function listVideos() {
  return apiFetch<VideoResponse[]>("/videos")
}

export function getVideo(videoId: string) {
  return apiFetch<VideoResponse>(`/videos/${videoId}`)
}

export function deleteVideo(videoId: string) {
  return apiFetch<void>(`/videos/${videoId}`, { method: "DELETE" })
}

export function uploadVideo(file: File) {
  const formData = new FormData()
  formData.append("file", file)
  return apiFetch<UploadResponse>("/videos/upload", { method: "POST", body: formData })
}

export function uploadVideoWithProgress(file: File, onProgress: (percent: number) => void) {
  const formData = new FormData()
  formData.append("file", file)

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000/api/v1"

  return new Promise<UploadResponse>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${baseUrl}/videos/upload`)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }
    xhr.onload = () => {
      try {
        const payload = xhr.responseText ? JSON.parse(xhr.responseText) : undefined
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(payload as UploadResponse)
          return
        }
        const detail = payload?.error?.message ?? payload?.detail ?? "Upload failed"
        reject(new Error(typeof detail === "string" ? detail : "Upload validation failed"))
      } catch (error) {
        reject(error)
      }
    }
    xhr.onerror = () => reject(new Error("Cannot reach backend upload endpoint"))
    xhr.send(formData)
  })
}

export function getTimeline(videoId: string) {
  return apiFetch<TimelineWindow[]>(`/videos/${videoId}/timeline`)
}

export function getTranscript(videoId: string) {
  return apiFetch<TranscriptResponse>(`/videos/${videoId}/transcript`)
}

export function getProducts(videoId: string) {
  return apiFetch<ProductResponse[]>(`/videos/${videoId}/products`)
}

export function getClaims(videoId: string) {
  return apiFetch<ClaimResponse[]>(`/videos/${videoId}/claims`)
}

export function getVideoMetrics(videoId: string) {
  return apiFetch<VideoMetricsResponse>(`/videos/${videoId}/metrics`)
}
