"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Activity, Clock3, DollarSign, Film, Gauge, Loader2, MessageSquareText, TriangleAlert } from "lucide-react"

import { MetricCard } from "@/components/metrics/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { MetricsOverviewResponse, VideoResponse } from "@/lib/api/types"

export function DashboardMetrics({ metrics, videos }: { metrics: MetricsOverviewResponse; videos: VideoResponse[] }) {
  const data = videos.slice(0, 8).map((video) => ({
    name: video.title.slice(0, 12) || video.original_filename.slice(0, 12),
    duration: Math.round(video.duration_seconds ?? 0),
    size: Math.round(video.file_size / 1024 / 1024),
  }))

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <MetricCard icon={Film} label="Total videos" value={metrics.videos_total} />
        <MetricCard icon={Gauge} label="Indexed" value={metrics.videos_indexed} />
        <MetricCard icon={Loader2} label="Processing" value={metrics.jobs_processing} />
        <MetricCard icon={MessageSquareText} label="Questions" value={metrics.questions_total} />
        <MetricCard icon={DollarSign} label="Cost" value={`$${metrics.estimated_cost_total.toFixed(4)}`} />
        <MetricCard icon={Clock3} label="Avg QA latency" value={`${metrics.average_latency_ms} ms`} />
        <MetricCard icon={Activity} label="Model calls" value={metrics.model_calls_total} />
        <MetricCard icon={TriangleAlert} label="Model failures" value={metrics.model_calls_failed} />
        <MetricCard icon={Clock3} label="Avg model latency" value={`${Math.round(metrics.average_model_latency_ms)} ms`} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Throughput preview</CardTitle>
        </CardHeader>
        <CardContent className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="duration" fill="#087ea4" radius={[4, 4, 0, 0]} />
              <Bar dataKey="size" fill="#16a34a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
