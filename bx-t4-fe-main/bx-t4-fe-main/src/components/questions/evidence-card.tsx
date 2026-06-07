"use client"

import Image from "next/image"
import { Clock, LocateFixed } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useVideoTime } from "@/hooks/use-video-time"
import type { DisplayLanguage } from "@/lib/display-language"
import { textForLanguage } from "@/lib/display-language"
import type { QuestionEvidenceResponse } from "@/lib/api/types"
import { formatTimestamp } from "@/lib/format"
import { buildMediaUrl } from "@/lib/media-url"

export function EvidenceCard({
  evidence,
  language,
}: {
  evidence: QuestionEvidenceResponse
  language: DisplayLanguage
}) {
  const { seekTo } = useVideoTime()
  const thumbnailUrl = buildMediaUrl(evidence.thumbnail_url)
  const transcript = textForLanguage(evidence.transcript, evidence.translation, language)

  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex gap-3">
        <button
          type="button"
          className="relative h-24 w-36 shrink-0 overflow-hidden rounded bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          onClick={() => seekTo(evidence.timestamp)}
          aria-label={`Jump to ${formatTimestamp(evidence.timestamp)}`}
        >
          {thumbnailUrl ? (
            <Image src={thumbnailUrl} alt="" fill className="object-cover" sizes="144px" unoptimized />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-muted-foreground">No thumbnail</div>
          )}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-xs font-medium text-primary">
            <Clock className="h-3.5 w-3.5" />
            {formatTimestamp(evidence.start_time)} - {formatTimestamp(evidence.end_time)}
          </div>
          <p className="mt-1 line-clamp-2 text-sm">{transcript}</p>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{evidence.visual_description}</p>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">Rationale: {evidence.rationale}</p>
          <Button className="mt-2" size="sm" variant="outline" onClick={() => seekTo(evidence.timestamp)}>
            <LocateFixed className="h-4 w-4" />
            Jump
          </Button>
        </div>
      </div>
    </div>
  )
}
