import { apiFetch } from "@/lib/api/client"
import type { JobResponse } from "@/lib/api/types"

export function getJob(jobId: string) {
  return apiFetch<JobResponse>(`/jobs/${jobId}`)
}
