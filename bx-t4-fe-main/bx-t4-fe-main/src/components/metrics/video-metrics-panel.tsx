"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Activity, Clock3, DollarSign, Film, MessageSquareText, Rows3, ShieldQuestion, TriangleAlert } from "lucide-react"

import { MetricCard } from "@/components/metrics/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { VideoMetricsResponse, VideoResponse } from "@/lib/api/types"
import { formatTimestamp } from "@/lib/format"

export function VideoMetricsPanel({ video, metrics }: { video: VideoResponse; metrics: VideoMetricsResponse }) {
  const data = [
    { name: "windows", value: metrics.window_count },
    { name: "claims", value: metrics.claim_count },
    { name: "questions", value: metrics.question_count },
    { name: "model calls", value: metrics.model_call_count },
  ]

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        <MetricCard icon={Film} label="Duration" value={video.duration_seconds ? formatTimestamp(video.duration_seconds) : "-"} />
        <MetricCard icon={Rows3} label="Windows" value={metrics.window_count} />
        <MetricCard icon={ShieldQuestion} label="Claims" value={metrics.claim_count} />
        <MetricCard icon={MessageSquareText} label="Questions" value={metrics.question_count} />
        <MetricCard icon={DollarSign} label="Estimated cost" value={`$${metrics.estimated_cost.toFixed(4)}`} />
        <MetricCard icon={Activity} label="Model calls" value={metrics.model_call_count} />
        <MetricCard icon={TriangleAlert} label="Model failures" value={metrics.failed_model_call_count} />
        <MetricCard icon={Clock3} label="Model latency" value={`${Math.round(metrics.average_model_latency_ms)} ms`} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Indexed objects</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#087ea4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
