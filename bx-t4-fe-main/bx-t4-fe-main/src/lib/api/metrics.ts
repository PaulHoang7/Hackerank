import { apiFetch } from "@/lib/api/client"
import type { MetricsOverviewResponse } from "@/lib/api/types"

export function getMetricsOverview() {
  return apiFetch<MetricsOverviewResponse>("/metrics/overview")
}
