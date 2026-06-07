"use client"

import Link from "next/link"
import { FileVideo, Link2, UploadCloud } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  NewUiShell,
  PageHeader,
  ProcessingStep,
  SectionTitle,
  StatusBadge,
} from "@/components/new-ui/primitives"
import { processingSteps } from "@/lib/new-ui/data"

export default function NewUiUploadPage() {
  return (
    <NewUiShell>
      <div className="space-y-6">
        <PageHeader
          title="Upload and setup"
          description="One practical setup flow: source video, optional commerce metadata, market rules, and live processing progress."
          actions={
            <>
              <Button asChild variant="outline">
                <Link href="/new-ui">Back to dashboard</Link>
              </Button>
              <Button asChild>
                <Link href="/new-ui/workspace">
                  <UploadCloud className="h-4 w-4" />
                  Start demo processing
                </Link>
              </Button>
            </>
          }
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
          <section className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Source video</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <label className="flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/40 p-8 text-center transition-colors hover:border-primary">
                  <FileVideo className="mb-3 h-10 w-10 text-primary" />
                  <p className="font-medium">Drag MP4, MOV, or HLS recording here</p>
                  <p className="mt-1 text-sm text-muted-foreground">Target demo length: 10-15 minutes.</p>
                  <input className="sr-only" type="file" />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-medium">Video URL</span>
                  <div className="flex gap-2">
                    <Input value="https://example.com/live/beauty-session.m3u8" readOnly />
                    <Button variant="outline" size="icon" aria-label="Attach URL">
                      <Link2 className="h-4 w-4" />
                    </Button>
                  </div>
                </label>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Commerce context</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="SKU list" value="SERUM-C30, SUN-BPOM-50" />
                  <Field label="Target languages" value="Vietnamese, Indonesian" />
                  <Field label="Brands to recognize" value="Glow Lab, BeautyBox" />
                  <Field label="Host / creator" value="Mai Beauty" />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2">
                    <span className="text-sm font-medium">Required phrases</span>
                    <Textarea value={"Mention price clearly\nShow free shipping code\nSay SKU before demo"} readOnly />
                  </label>
                  <label className="block space-y-2">
                    <span className="text-sm font-medium">Forbidden / risky claims</span>
                    <Textarea value={"FDA-approved\nCures acne in 7 days\nGuaranteed whitening result"} readOnly />
                  </label>
                </div>
              </CardContent>
            </Card>
          </section>

          <aside className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Processing</CardTitle>
                  <StatusBadge status="processing" />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {processingSteps.map((step) => (
                  <ProcessingStep key={step.label} {...step} />
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="space-y-3 p-5">
                <SectionTitle title="What this creates" description="The workspace needs these objects to satisfy the brief." />
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>Timestamped transcript and multilingual translation.</li>
                  <li>OCR and representative evidence thumbnails.</li>
                  <li>Product/SKU occurrences with confidence.</li>
                  <li>Claim-vs-visual checks with grounded verdicts.</li>
                  <li>Cost, latency, throughput metrics for the demo.</li>
                </ul>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </NewUiShell>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-medium">{label}</span>
      <Input value={value} readOnly />
    </label>
  )
}
