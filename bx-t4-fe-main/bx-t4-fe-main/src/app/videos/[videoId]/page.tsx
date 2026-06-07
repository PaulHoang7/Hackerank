"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import { ClaimsPanel } from "@/components/claims/claims-panel"
import { ProductsPanel } from "@/components/products/products-panel"
import { QAChat } from "@/components/questions/qa-chat"
import { TimelineList } from "@/components/timeline/timeline-list"
import { TranscriptPanel } from "@/components/transcript/transcript-panel"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/ui/state"
import { Tabs } from "@/components/ui/tabs"
import { VideoMetricsPanel } from "@/components/metrics/video-metrics-panel"
import { VideoPlayer } from "@/components/video/video-player"
import { VideoStatusBadge } from "@/components/video/status-badge"
import { useClaims, useProducts, useTimeline, useTranscript, useVideo, useVideoMetrics } from "@/features/videos/queries"
import { VideoTimeProvider } from "@/hooks/use-video-time"
import type { DisplayLanguage } from "@/lib/display-language"
import { displayLanguageTabs } from "@/lib/display-language"
import { buildMediaUrl } from "@/lib/media-url"

const tabs = [
  { value: "transcript", label: "Transcript" },
  { value: "products", label: "SKU timeline" },
  { value: "claims", label: "Claim Check" },
  { value: "metrics", label: "Metrics" },
]

export default function VideoWorkspacePage({ params }: { params: { videoId: string } }) {
  return <LiveVideoWorkspacePage videoId={params.videoId} />
}

function LiveVideoWorkspacePage({ videoId }: { videoId: string }) {
  const [tab, setTab] = useState("transcript")
  const [language, setLanguage] = useState<DisplayLanguage>("vi")
  const videoQuery = useVideo(videoId)
  const timelineQuery = useTimeline(videoId)
  const transcriptQuery = useTranscript(videoId)
  const productsQuery = useProducts(videoId)
  const claimsQuery = useClaims(videoId)
  const metricsQuery = useVideoMetrics(videoId)

  if (videoQuery.isLoading || timelineQuery.isLoading) {
    return <Skeleton className="h-[720px] w-full" />
  }

  if (videoQuery.isError || timelineQuery.isError || !videoQuery.data || !timelineQuery.data) {
    return (
      <ErrorState
        message={videoQuery.error?.message ?? timelineQuery.error?.message ?? "Cannot load video workspace"}
        onRetry={() => {
          videoQuery.refetch()
          timelineQuery.refetch()
        }}
      />
    )
  }

  const video = videoQuery.data
  const timeline = timelineQuery.data
  const claims = claimsQuery.data ?? []
  const videoSrc = buildMediaUrl(`/storage/${video.storage_key}`) ?? ""

  return (
    <VideoTimeProvider>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <Button asChild variant="ghost" size="sm" className="-ml-3 mb-2">
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
            </Button>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold">{video.title}</h1>
              <VideoStatusBadge status={video.status} />
            </div>
            <p className="text-sm text-muted-foreground">{video.original_filename}</p>
          </div>
          <Tabs
            tabs={displayLanguageTabs}
            value={language}
            onChange={(value) => setLanguage(value as DisplayLanguage)}
          />
        </div>
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
          <VideoPlayer src={videoSrc} title={video.title} />
          <QAChat videoId={video.id} language={language} />
        </div>
        <TimelineList windows={timeline} claims={claims} language={language} />
        <Card>
          <CardContent className="space-y-4 p-5">
            <Tabs tabs={tabs} value={tab} onChange={setTab} />
            {tab === "transcript" && transcriptQuery.data ? (
              <TranscriptPanel transcript={transcriptQuery.data} windows={timeline} language={language} />
            ) : null}
            {tab === "transcript" && transcriptQuery.isLoading ? <Skeleton className="h-72" /> : null}
            {tab === "products" ? <ProductsPanel products={productsQuery.data ?? []} /> : null}
            {tab === "claims" ? <ClaimsPanel videoId={video.id} claims={claims} /> : null}
            {tab === "metrics" && metricsQuery.data ? <VideoMetricsPanel video={video} metrics={metricsQuery.data} /> : null}
            {tab === "metrics" && metricsQuery.isLoading ? <Skeleton className="h-72" /> : null}
          </CardContent>
        </Card>
      </div>
    </VideoTimeProvider>
  )
}
