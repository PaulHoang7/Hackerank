import { useQuery } from "@tanstack/react-query"

import { getMetricsOverview } from "@/lib/api/metrics"

export const metricKeys = {
  overview: ["metrics", "overview"] as const,
}

export function useMetricsOverview(options?: { refetchInterval?: number | false }) {
  return useQuery({ queryKey: metricKeys.overview, queryFn: getMetricsOverview, ...options })
}
