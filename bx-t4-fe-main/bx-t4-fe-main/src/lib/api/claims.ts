import { apiFetch } from "@/lib/api/client"
import type { ClaimResponse, ClaimVerificationResponse } from "@/lib/api/types"

export function getClaim(videoId: string, claimId: string) {
  return apiFetch<ClaimResponse>(`/videos/${videoId}/claims/${claimId}`)
}

export function verifyClaim(videoId: string, claimId: string) {
  return apiFetch<ClaimVerificationResponse>(`/videos/${videoId}/claims/${claimId}/verify`, {
    method: "POST",
  })
}
