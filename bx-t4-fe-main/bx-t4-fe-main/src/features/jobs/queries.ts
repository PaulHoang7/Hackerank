import { useQuery } from "@tanstack/react-query"

import { getJob } from "@/lib/api/jobs"

export const jobKeys = {
  detail: (jobId: string) => ["jobs", jobId] as const,
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: jobId ? jobKeys.detail(jobId) : ["jobs", "empty"],
    queryFn: () => getJob(jobId ?? ""),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "completed" || status === "failed" ? false : 2000
    },
  })
}
