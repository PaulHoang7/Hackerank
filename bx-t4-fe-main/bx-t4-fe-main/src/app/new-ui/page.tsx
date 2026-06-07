"use client"

import Link from "next/link"
import { ExternalLink, UploadCloud } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  EvidenceThumb,
  MetricCard,
  NewUiShell,
  PageHeader,
  SectionTitle,
  StatusBadge,
} from "@/components/new-ui/primitives"
import { claims, dashboardMetrics, demoVideo, evidence, videos } from "@/lib/new-ui/data"

export default function NewUiDashboardPage() {
  return (
    <NewUiShell>
      <div className="space-y-6">
        <PageHeader
          title="Video intelligence dashboard"
          description="A compact demo surface for upload, evidence-grounded Q&A, claim verification, SKU timeline, and cost telemetry."
          actions={
            <>
              <Button asChild variant="outline">
                <Link href="/new-ui/workspace">
                  <ExternalLink className="h-4 w-4" />
                  Open workspace
                </Link>
              </Button>
              <Button asChild>
                <Link href="/new-ui/upload">
                  <UploadCloud className="h-4 w-4" />
                  Upload video
                </Link>
              </Button>
            </>
          }
        />

        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
          {dashboardMetrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
          <Card>
            <CardContent className="p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold">{demoVideo.title}</h2>
                    <StatusBadge status={demoVideo.status} />
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {demoVideo.filename} · {demoVideo.duration} · {demoVideo.languages.join(", ")}
                  </p>
                </div>
                <Button asChild size="sm" variant="outline">
                  <Link href="/new-ui/workspace">Review evidence</Link>
                </Button>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_280px]">
                <EvidenceThumb
                  title={evidence.price.title}
                  timestamp={evidence.price.timestamp}
                  tone={evidence.price.tone}
                  className="aspect-video"
                />
                <div className="space-y-3">
                  <SectionTitle title="Ready demo flow" description="What judges should see without touching the old UI." />
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li>Upload and processing checklist.</li>
                    <li>Video workspace with Q&A and evidence cards.</li>
                    <li>Timeline, SKU occurrences, claim check, compliance, metrics in one tabbed page.</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-4 p-5">
              <SectionTitle title="Claim alerts" description="Auto-detected moments that need visual grounding." />
              <div className="space-y-3">
                {claims.slice(0, 3).map((claim) => (
                  <div key={claim.id} className="rounded-md border bg-muted/30 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <button type="button" className="text-sm font-medium text-primary hover:underline">
                        {claim.time}
                      </button>
                      <StatusBadge status={claim.verdict} />
                    </div>
                    <p className="mt-2 text-sm">{claim.text}</p>
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{claim.reason}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="space-y-3">
          <SectionTitle title="Recent videos" description="Mock library data for the normalized new UI." />
          <div className="overflow-hidden rounded-lg border bg-card">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="border-b bg-muted/50 text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3">Video</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3">Languages</th>
                    <th className="px-4 py-3">Owner</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {videos.map((video) => (
                    <tr key={video.filename} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <p className="font-medium">{video.title}</p>
                        <p className="text-xs text-muted-foreground">{video.filename}</p>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={video.status} />
                      </td>
                      <td className="px-4 py-3">{video.duration}</td>
                      <td className="px-4 py-3">{video.languages}</td>
                      <td className="px-4 py-3">{video.owner}</td>
                      <td className="px-4 py-3 text-right">
                        <Button asChild size="sm" variant="outline">
                          <Link href="/new-ui/workspace">Open</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </NewUiShell>
  )
}
