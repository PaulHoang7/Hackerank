"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, FlaskConical } from "lucide-react"

import { ClaimsPanel } from "@/components/claims/claims-panel"
import { ProductsPanel } from "@/components/products/products-panel"
import { QAChat } from "@/components/questions/qa-chat"
import { TimelineList } from "@/components/timeline/timeline-list"
import { TranscriptPanel } from "@/components/transcript/transcript-panel"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs } from "@/components/ui/tabs"
import { VideoMetricsPanel } from "@/components/metrics/video-metrics-panel"
import { VideoPlayer } from "@/components/video/video-player"
import { VideoStatusBadge } from "@/components/video/status-badge"
import { VideoTimeProvider } from "@/hooks/use-video-time"
import {
  createDemoQuestion,
  demoClaimVerifications,
  demoClaims,
  demoPosterUrl,
  demoProducts,
  demoQuestions,
  demoSampleQuestions,
  demoTimeline,
  demoTranscript,
  demoVideo,
  demoVideoMetrics,
  getDemoManualVerification,
} from "@/lib/mock/live-commerce-demo"

const tabs = [
  { value: "transcript", label: "Transcript" },
  { value: "products", label: "SKU timeline" },
  { value: "claims", label: "Claim Check" },
  { value: "metrics", label: "Metrics" },
]

export function DemoWorkspace() {
  const [tab, setTab] = useState("claims")

  return (
    <VideoTimeProvider>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <Button asChild variant="ghost" size="sm" className="-ml-3 mb-2">
              <Link href="/videos">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
            </Button>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold">{demoVideo.title}</h1>
              <VideoStatusBadge status={demoVideo.status} />
              <Badge variant="warning">
                <FlaskConical className="mr-1 h-3.5 w-3.5" />
                FE mock
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Demo workspace dựng sẵn để review UI flow: hỏi đáp có evidence, SKU timeline, claim-vs-visual và metrics.
            </p>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
          <VideoPlayer
            title={demoVideo.title}
            posterUrl={demoPosterUrl}
            fallbackNote="Đây là mock FE: click timestamp/evidence sẽ cập nhật thời gian và cho bạn thấy thao tác seek trong workspace."
          />
          <QAChat
            videoId={demoVideo.id}
            demoQuestions={demoQuestions}
            sampleQuestions={demoSampleQuestions}
            onDemoAsk={createDemoQuestion}
          />
        </div>

        <TimelineList windows={demoTimeline} claims={demoClaims} />

        <Card>
          <CardContent className="space-y-4 p-5">
            <Tabs tabs={tabs} value={tab} onChange={setTab} />
            {tab === "transcript" ? <TranscriptPanel transcript={demoTranscript} windows={demoTimeline} /> : null}
            {tab === "products" ? <ProductsPanel products={demoProducts} /> : null}
            {tab === "claims" ? (
              <ClaimsPanel
                videoId={demoVideo.id}
                claims={demoClaims}
                demoResults={demoClaimVerifications}
                onDemoManualCheck={getDemoManualVerification}
              />
            ) : null}
            {tab === "metrics" ? <VideoMetricsPanel video={demoVideo} metrics={demoVideoMetrics} /> : null}
          </CardContent>
        </Card>
      </div>
    </VideoTimeProvider>
  )
}
