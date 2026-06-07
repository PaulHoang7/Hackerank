"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { LocateFixed, MessageSquareText, Send } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
  BoundaryNotice,
  EvidenceCard,
  EvidenceThumb,
  MetricCard,
  NewUiShell,
  PageHeader,
  SectionTitle,
  StatusBadge,
} from "@/components/new-ui/primitives"
import {
  claims,
  demoVideo,
  evidence,
  metrics,
  products,
  qaAnswers,
  sampleQuestions,
  windows,
  workspaceTabs,
  type WorkspaceTab,
} from "@/lib/new-ui/data"

const evidenceById = evidence

export function WorkspaceClient({ initialTab }: { initialTab: WorkspaceTab }) {
  const router = useRouter()
  const [tab, setTab] = useState<WorkspaceTab>(initialTab)

  const setWorkspaceTab = (nextTab: string) => {
    const workspaceTab = nextTab as WorkspaceTab
    setTab(workspaceTab)
    router.replace(`/new-ui/workspace?tab=${workspaceTab}`, { scroll: false })
  }

  return (
    <NewUiShell>
      <div className="space-y-6">
        <PageHeader
          title={demoVideo.title}
          description={`${demoVideo.filename} · ${demoVideo.duration} · ${demoVideo.languages.join(", ")} · evidence-grounded demo workspace`}
          actions={
            <>
              <StatusBadge status={demoVideo.status} />
              <Button asChild variant="outline">
                <Link href="/new-ui/upload">Upload another</Link>
              </Button>
            </>
          }
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(380px,0.75fr)]">
          <section className="space-y-6">
            <Card className="overflow-hidden">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="truncate">Video player</CardTitle>
                <span className="text-sm text-muted-foreground">Current: {evidence.price.timestamp}</span>
              </CardHeader>
              <CardContent className="pt-0">
                <EvidenceThumb
                  title={evidence.price.title}
                  timestamp={evidence.price.timestamp}
                  tone={evidence.price.tone}
                  className="aspect-video"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Evidence inspector</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <EvidenceCard
                  title={evidence.price.title}
                  timestamp={evidence.price.timestamp}
                  visual={evidence.price.visual}
                  ocr={evidence.price.ocr}
                  tone={evidence.price.tone}
                />
                <InspectorRow label="Transcript" value="Giá còn 199K, freeship cho đơn trong phiên này nha." />
                <InspectorRow label="Why supported" value="Speech, OCR, product visibility, and timestamp all point to the same 2-second window." />
              </CardContent>
            </Card>
          </section>

          <QAChat />
        </div>

        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="overflow-x-auto">
              <Tabs tabs={workspaceTabs} value={tab} onChange={setWorkspaceTab} />
            </div>
            {tab === "qa" ? <QAReview /> : null}
            {tab === "timeline" ? <TimelinePanel /> : null}
            {tab === "sku" ? <SkuPanel /> : null}
            {tab === "claims" ? <ClaimsPanel /> : null}
            {tab === "compliance" ? <CompliancePanel /> : null}
            {tab === "metrics" ? <MetricsPanel /> : null}
          </CardContent>
        </Card>
      </div>
    </NewUiShell>
  )
}

function QAChat() {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Q&A evidence</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form className="space-y-2">
          <Textarea placeholder="Ví dụ: Lúc nói giá 199K có thấy giá trên màn hình không?" defaultValue={sampleQuestions[1]} />
          <Button type="button">
            <Send className="h-4 w-4" />
            Ask demo
          </Button>
        </form>
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase text-muted-foreground">Sample questions</p>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.slice(0, 6).map((question) => (
              <button
                key={question}
                type="button"
                className="rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
        <div className="max-h-[520px] space-y-3 overflow-y-auto pr-1">
          {qaAnswers.map((answer) => (
            <div key={answer.id} className="rounded-lg border bg-muted/30 p-3">
              <p className="text-sm font-medium">Q: {answer.question}</p>
              <p className="mt-2 text-sm">A: {answer.answer}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {answer.latencyMs} ms · ${answer.cost.toFixed(4)}
              </p>
              <div className="mt-3 space-y-2">
                {answer.evidenceIds.map((id) => {
                  const item = evidenceById[id as keyof typeof evidenceById]
                  return (
                    <EvidenceCard
                      key={id}
                      title={item.title}
                      timestamp={item.timestamp}
                      visual={item.visual}
                      ocr={item.ocr}
                      tone={item.tone}
                    />
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function QAReview() {
  return (
    <div className="space-y-3">
      <SectionTitle title="Grounded answer contract" description="Every valid answer includes at least one timestamp and one frame thumbnail." />
      <div className="grid gap-3 md:grid-cols-2">
        {qaAnswers.map((answer) => (
          <div key={answer.id} className="rounded-lg border bg-muted/30 p-4">
            <p className="text-sm font-medium">{answer.question}</p>
            <p className="mt-2 text-sm">{answer.answer}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Evidence: {answer.evidenceIds.length} frame · latency {answer.latencyMs} ms
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

function TimelinePanel() {
  return (
    <div className="space-y-3">
      <SectionTitle title="Multimodal timeline" description="Transcript, visual scene, OCR, audio, product, and claim signals in each window." />
      <div className="space-y-3">
        {windows.map((window) => {
          const frame = evidenceById[window.evidenceId as keyof typeof evidenceById]
          return (
            <button key={window.id} type="button" className="w-full rounded-lg border bg-card p-4 text-left transition-colors hover:border-primary/60 hover:bg-primary/5">
              <div className="grid gap-3 md:grid-cols-[110px_150px_1fr_72px]">
                <div>
                  <p className="text-sm font-medium text-primary">
                    {window.start} - {window.end}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">{window.emotion}</p>
                </div>
                <EvidenceThumb title={frame.title} timestamp={frame.timestamp} tone={frame.tone} className="h-24" />
                <div className="min-w-0">
                  <p className="line-clamp-2 text-sm">{window.transcript}</p>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{window.visual}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <Badge variant="neutral">OCR: {window.ocr}</Badge>
                    <Badge variant="neutral">Audio: {window.audio}</Badge>
                    <Badge variant="neutral">SKU: {window.product}</Badge>
                    {window.claim ? <Badge variant="warning">Claim</Badge> : null}
                  </div>
                </div>
                <div className="text-right text-xs text-muted-foreground">
                  <p className="text-lg font-semibold text-foreground">{window.energy}%</p>
                  energy
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function SkuPanel() {
  return (
    <div className="space-y-3">
      <SectionTitle title="Product / SKU timeline" description="Where each SKU is shown, spoken, demoed, priced, or risky." />
      <div className="grid gap-3 md:grid-cols-2">
        {products.map((product) => (
          <div key={product.sku} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium">{product.name}</p>
                <p className="text-sm text-muted-foreground">
                  {product.sku} · {product.market}
                </p>
                <p className="mt-2 text-sm">{product.description}</p>
              </div>
              <Badge variant="default">{product.occurrences.length} hits</Badge>
            </div>
            <div className="mt-4 space-y-2">
              {product.occurrences.map((occurrence) => (
                <div key={`${product.sku}-${occurrence.type}-${occurrence.time}`} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="neutral">{occurrence.type}</Badge>
                    <span className="font-medium">{occurrence.time}</span>
                    <span className="text-muted-foreground">{Math.round(occurrence.confidence * 100)}%</span>
                  </div>
                  <Button size="sm" variant="outline">
                    <LocateFixed className="h-4 w-4" />
                    Jump
                  </Button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ClaimsPanel() {
  return (
    <div className="space-y-4">
      <BoundaryNotice />
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_auto]">
        <Textarea defaultValue='Host nói "hàng chính hãng 100%" nhưng có thấy chứng nhận không?' />
        <Input defaultValue="03:18:44" />
        <Button type="button">Check</Button>
      </div>
      <div className="space-y-3">
        {claims.map((claim) => {
          const frame = evidenceById[claim.evidenceId as keyof typeof evidenceById]
          return (
            <div key={claim.id} className="rounded-lg border bg-card p-4">
              <div className="grid gap-3 md:grid-cols-[140px_1fr_auto]">
                <EvidenceThumb title={frame.title} timestamp={claim.time} tone={frame.tone} className="h-24" />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={claim.verdict} />
                    <span className="text-sm text-muted-foreground">confidence {Math.round(claim.confidence * 100)}%</span>
                  </div>
                  <p className="mt-2 text-sm font-medium">{claim.text}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{claim.reason}</p>
                </div>
                <Button size="sm" variant="outline">
                  Verify
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function CompliancePanel() {
  return (
    <div className="grid gap-4 lg:grid-cols-[420px_minmax(0,1fr)]">
      <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
        <SectionTitle title="Find moments where X happens while Y is true" />
        <Input defaultValue="host says authenticity claim" />
        <Input defaultValue="no certificate visible within 5 seconds" />
        <Button className="w-full">Run query</Button>
      </div>
      <div className="space-y-3">
        {claims.filter((claim) => claim.verdict !== "consistent").map((claim) => (
          <div key={claim.id} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium">{claim.text}</p>
                <p className="mt-1 text-sm text-muted-foreground">{claim.reason}</p>
              </div>
              <StatusBadge status={claim.verdict} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function MetricsPanel() {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Model calls" value={String(metrics.modelCalls)} note="Seed Omni requests" />
        <MetricCard label="Cost" value={metrics.estimatedCost} note="Current demo run" />
        <MetricCard label="Avg latency" value={metrics.averageLatency} note="Q&A and verify" />
        <MetricCard label="Throughput" value={metrics.throughput} note={`${metrics.failedWindows} failed window`} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Seed Omni calls by request type</CardTitle>
        </CardHeader>
        <CardContent className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={metrics.byType}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} />
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

function InspectorRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/30 p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm">{value}</p>
    </div>
  )
}
