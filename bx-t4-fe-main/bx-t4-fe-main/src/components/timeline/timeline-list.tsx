"use client"

import { useMemo, useState } from "react"
import { Activity, Captions, Eye, Radio, ShieldCheck, UserRound } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Tabs } from "@/components/ui/tabs"
import { useVideoTime } from "@/hooks/use-video-time"
import type { DisplayLanguage } from "@/lib/display-language"
import { textForLanguage } from "@/lib/display-language"
import { formatTimestamp } from "@/lib/format"
import type { ClaimResponse, TimelineWindow } from "@/lib/api/types"

type TimelineFilter = "all" | "transcript" | "ocr" | "entity" | "audio" | "claim"

const filters: Array<{ value: TimelineFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "transcript", label: "Transcript" },
  { value: "ocr", label: "OCR" },
  { value: "entity", label: "Entity" },
  { value: "audio", label: "Audio" },
  { value: "claim", label: "Claim" },
]

export function TimelineList({
  windows,
  claims,
  language = "vi",
}: {
  windows: TimelineWindow[]
  claims: ClaimResponse[]
  language?: DisplayLanguage
}) {
  const [filter, setFilter] = useState<TimelineFilter>("all")
  const { seekTo } = useVideoTime()

  const filtered = useMemo(() => {
    return windows.filter((window) => {
      if (filter === "all") return true
      if (filter === "transcript") return Boolean(window.transcript)
      if (filter === "ocr") return window.ocr_text.length > 0
      if (filter === "entity") return window.detected_entities.length > 0
      if (filter === "audio") return window.audio_events.length > 0
      if (filter === "claim") return claims.some((claim) => claim.video_window_id === window.id)
      return true
    })
  }, [claims, filter, windows])

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Indexed timeline</h2>
          <p className="text-sm text-muted-foreground">{windows.length} windows from backend indexing pipeline</p>
        </div>
        <Tabs tabs={filters} value={filter} onChange={(value) => setFilter(value as TimelineFilter)} />
      </div>
      <div className="space-y-3">
        {filtered.map((window) => {
          const windowClaims = claims.filter((claim) => claim.video_window_id === window.id)
          const transcript = textForLanguage(window.transcript, window.translation, language)
          return (
            <button
              key={window.id}
              type="button"
              className="w-full rounded-lg border bg-card p-4 text-left transition-colors hover:border-primary/60 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => seekTo(window.start_time)}
            >
              <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
                    <Activity className="h-4 w-4 text-primary" />
                    {formatTimestamp(window.start_time)} - {formatTimestamp(window.end_time)}
                    {window.emotion ? <span className="text-muted-foreground">emotion: {window.emotion}</span> : null}
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm">{transcript || "No transcript in this window"}</p>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{window.scene_description}</p>
                </div>
                <div className="text-xs text-muted-foreground">energy {Math.round(window.energy_score * 100)}%</div>
              </div>
              <div className="mt-3 grid gap-2 text-xs text-muted-foreground md:grid-cols-4">
                <Meta icon={Captions} label="OCR" value={compactJson(window.ocr_text)} />
                <Meta icon={Radio} label="Audio" value={compactJson(window.audio_events)} />
                <Meta icon={UserRound} label="Entities" value={compactJson(window.detected_entities)} />
                <Meta icon={ShieldCheck} label="Claims" value={windowClaims.map((claim) => claim.claim_text).join("; ") || "-"} />
              </div>
            </button>
          )
        })}
      </div>
      {!filtered.length ? (
        <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">Không có timeline window phù hợp filter.</div>
      ) : null}
    </section>
  )
}

function Meta({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Eye
  label: string
  value: string
}) {
  return (
    <div className="min-w-0 rounded-md bg-muted/60 p-2">
      <div className="mb-1 flex items-center gap-1 font-medium text-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="line-clamp-2 break-words">{value}</p>
    </div>
  )
}

function compactJson(value: Record<string, unknown>[]) {
  if (!value.length) return "-"
  return value
    .slice(0, 3)
    .map((item) => JSON.stringify(item))
    .join("; ")
}
