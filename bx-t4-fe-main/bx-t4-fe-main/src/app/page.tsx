"use client"

import { RefreshCcw } from "lucide-react"

import { DashboardMetrics } from "@/components/metrics/dashboard-metrics"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/ui/state"
import { VideoTable } from "@/components/video/video-table"
import { useMetricsOverview } from "@/features/metrics/queries"
import { useVideos } from "@/features/videos/queries"
import { cn } from "@/lib/utils"

const DASHBOARD_POLLING_INTERVAL_MS = 5000

export default function DashboardPage() {
  const metricsQuery = useMetricsOverview({ refetchInterval: DASHBOARD_POLLING_INTERVAL_MS })
  const videosQuery = useVideos({ refetchInterval: DASHBOARD_POLLING_INTERVAL_MS })
  const isRefreshing = metricsQuery.isFetching || videosQuery.isFetching

  if (metricsQuery.isLoading || videosQuery.isLoading) {
    return <DashboardSkeleton />
  }

  if (metricsQuery.isError || videosQuery.isError || !metricsQuery.data || !videosQuery.data) {
    return (
      <ErrorState
        message={metricsQuery.error?.message ?? videosQuery.error?.message ?? "Backend unavailable"}
        onRetry={() => {
          metricsQuery.refetch()
          videosQuery.refetch()
        }}
      />
    )
  }

  const videos = videosQuery.data

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Video intelligence dashboard</h1>
          <p className="text-sm text-muted-foreground">Cost, latency, throughput và video gần đây từ FastAPI backend.</p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            metricsQuery.refetch()
            videosQuery.refetch()
          }}
        >
          <RefreshCcw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
          Polling 5s
        </Button>
      </div>
      <DashboardMetrics metrics={metricsQuery.data} videos={videos} />
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Recent videos</h2>
        <VideoTable videos={videos.slice(0, 6)} />
      </section>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-16 w-full" />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
      <Skeleton className="h-72 w-full" />
    </div>
  )
}
