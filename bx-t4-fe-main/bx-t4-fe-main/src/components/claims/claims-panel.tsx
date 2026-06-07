"use client"

import { useState } from "react"
import Image from "next/image"
import { CheckCircle2, LocateFixed } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { ClaimVerdictBadge } from "@/components/video/status-badge"
import { useVerifyClaim } from "@/features/claims/queries"
import { useVideoTime } from "@/hooks/use-video-time"
import type { ClaimResponse, ClaimVerificationResponse } from "@/lib/api/types"
import { formatTimestamp } from "@/lib/format"
import { buildMediaUrl } from "@/lib/media-url"

interface ClaimsPanelProps {
  videoId: string
  claims: ClaimResponse[]
  demoResults?: Record<string, ClaimVerificationResponse>
  onDemoManualCheck?: (claimText: string, timestamp?: number) => ClaimVerificationResponse
}

export function ClaimsPanel({ videoId, claims, demoResults, onDemoManualCheck }: ClaimsPanelProps) {
  if (demoResults || onDemoManualCheck) {
    return <DemoClaimsPanel claims={claims} demoResults={demoResults ?? {}} onManualCheck={onDemoManualCheck} />
  }

  return <LiveClaimsPanel videoId={videoId} claims={claims} />
}

function LiveClaimsPanel({ videoId, claims }: { videoId: string; claims: ClaimResponse[] }) {
  const [results, setResults] = useState<Record<string, ClaimVerificationResponse>>({})
  const verifyMutation = useVerifyClaim(videoId)
  const { seekTo } = useVideoTime()

  if (!claims.length) {
    return <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">Backend chưa phát hiện claim nào.</div>
  }

  return (
    <div className="space-y-3">
      {claims.map((claim) => {
        const result = results[claim.id]
        return (
          <ClaimCard
            key={claim.id}
            claim={claim}
            result={result}
            isVerifying={verifyMutation.isPending}
            onJump={seekTo}
            onVerify={() =>
              verifyMutation.mutate(claim.id, {
                onSuccess: (data) => {
                  setResults((current) => ({ ...current, [claim.id]: data }))
                  toast.success("Đã verify claim")
                },
                onError: (error) => toast.error(error.message),
              })
            }
          />
        )
      })}
    </div>
  )
}

function DemoClaimsPanel({
  claims,
  demoResults,
  onManualCheck,
}: {
  claims: ClaimResponse[]
  demoResults: Record<string, ClaimVerificationResponse>
  onManualCheck?: (claimText: string, timestamp?: number) => ClaimVerificationResponse
}) {
  const { seekTo } = useVideoTime()
  const [manualClaim, setManualClaim] = useState("Host nói Serum C30 là hàng chính hãng 100%")
  const [manualTimestamp, setManualTimestamp] = useState("145")
  const [manualResult, setManualResult] = useState<ClaimVerificationResponse | null>(null)

  return (
    <div className="space-y-4">
      <section className="rounded-lg border bg-muted/30 p-4">
        <div className="mb-3">
          <h3 className="text-sm font-semibold">Manual claim check</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            User nhập claim hoặc timestamp cụ thể; BE sẽ lấy transcript + frame gần đó để đối chiếu lời nói với hình ảnh.
          </p>
        </div>
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_140px_auto]">
          <Textarea
            className="min-h-20"
            value={manualClaim}
            onChange={(event) => setManualClaim(event.target.value)}
            placeholder='Ví dụ: "Host nói sản phẩm chính hãng"'
          />
          <Input
            value={manualTimestamp}
            onChange={(event) => setManualTimestamp(event.target.value)}
            inputMode="decimal"
            placeholder="timestamp"
          />
          <Button
            onClick={() => {
              const timestamp = Number.parseFloat(manualTimestamp)
              const result = onManualCheck?.(manualClaim, Number.isFinite(timestamp) ? timestamp : undefined)
              if (result) {
                setManualResult(result)
                toast.success("Demo visual check complete")
              }
            }}
          >
            <CheckCircle2 className="h-4 w-4" />
            Check
          </Button>
        </div>
        {manualResult ? (
          <div className="mt-4 rounded-lg border bg-background p-4">
            <VerificationSummary result={manualResult} onJump={seekTo} />
          </div>
        ) : null}
      </section>

      <section className="space-y-3">
        <div>
          <h3 className="text-sm font-semibold">Auto-detected claims</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Đây là các câu BE/AI tự phát hiện là đáng kiểm chứng trong lúc index video.
          </p>
        </div>
        {claims.map((claim) => (
          <ClaimCard
            key={claim.id}
            claim={claim}
            result={demoResults[claim.id]}
            onJump={seekTo}
            onVerify={() => toast.info("Demo đã mock sẵn kết quả verify cho claim này")}
          />
        ))}
      </section>
    </div>
  )
}

function ClaimCard({
  claim,
  result,
  isVerifying = false,
  onJump,
  onVerify,
}: {
  claim: ClaimResponse
  result?: ClaimVerificationResponse
  isVerifying?: boolean
  onJump: (timestamp: number) => void
  onVerify: () => void
}) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <ClaimVerdictBadge verdict={result?.verdict ?? "pending"} />
            <button
              type="button"
              className="text-sm font-medium text-primary hover:underline"
              onClick={() => onJump(claim.timestamp)}
            >
              {formatTimestamp(claim.timestamp)}
            </button>
            {claim.speaker ? <span className="text-sm text-muted-foreground">speaker: {claim.speaker}</span> : null}
          </div>
          <p className="text-sm">{claim.claim_text}</p>
          {result ? <VerificationSummary result={result} onJump={onJump} /> : null}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onJump(claim.timestamp)}>
            <LocateFixed className="h-4 w-4" />
            Jump
          </Button>
          <Button size="sm" disabled={isVerifying} onClick={onVerify}>
            <CheckCircle2 className="h-4 w-4" />
            Verify
          </Button>
        </div>
      </div>
    </div>
  )
}

function VerificationSummary({
  result,
  onJump,
}: {
  result: ClaimVerificationResponse
  onJump: (timestamp: number) => void
}) {
  return (
    <div className="mt-3 space-y-3 rounded-md bg-muted p-3 text-sm">
      <div>
        <p className="font-medium">Confidence {Math.round(result.confidence * 100)}%</p>
        <p className="mt-1 text-muted-foreground">{result.explanation}</p>
      </div>
      {result.evidence.length ? (
        <div className="space-y-2">
          {result.evidence.map((item, index) => {
            const timestamp = item.timestamp ?? result.timestamp
            const thumbnailUrl = buildMediaUrl(item.thumbnail_url)
            return (
              <div key={`${result.claim_id}-${timestamp}-${index}`} className="rounded-md border bg-background p-3">
                <div className="flex gap-3">
                  <button
                    type="button"
                    className="relative h-20 w-32 shrink-0 overflow-hidden rounded bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    onClick={() => onJump(timestamp)}
                    aria-label={`Jump to claim evidence at ${formatTimestamp(timestamp)}`}
                  >
                    {thumbnailUrl ? (
                      <Image src={thumbnailUrl} alt="" fill className="object-cover" sizes="128px" unoptimized />
                    ) : (
                      <div className="flex h-full items-center justify-center px-2 text-xs text-muted-foreground">
                        Frame evidence
                      </div>
                    )}
                  </button>
                  <div className="min-w-0 flex-1">
                    <button
                      type="button"
                      className="text-xs font-medium text-primary hover:underline"
                      onClick={() => onJump(timestamp)}
                    >
                      {formatTimestamp(timestamp)}
                    </button>
                    {item.source ? <p className="mt-1 text-xs text-muted-foreground">Source: {item.source}</p> : null}
                    {item.transcript ? <p className="mt-1 line-clamp-2 text-xs">Transcript: {item.transcript}</p> : null}
                    {item.visual_description ? (
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">Visual: {item.visual_description}</p>
                    ) : null}
                    {item.rationale ? (
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">Reason: {item.rationale}</p>
                    ) : null}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">Không có evidence frame từ backend.</p>
      )}
    </div>
  )
}
