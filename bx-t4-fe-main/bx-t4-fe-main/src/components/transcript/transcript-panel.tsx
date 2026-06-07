"use client"

import { useMemo, useState } from "react"
import { Search } from "lucide-react"

import { Input } from "@/components/ui/input"
import { useVideoTime } from "@/hooks/use-video-time"
import type { DisplayLanguage } from "@/lib/display-language"
import { textForLanguage } from "@/lib/display-language"
import { formatTimestamp } from "@/lib/format"
import type { TimelineWindow, TranscriptResponse } from "@/lib/api/types"
import { cn } from "@/lib/utils"

export function TranscriptPanel({
  transcript,
  windows,
  language = "vi",
}: {
  transcript: TranscriptResponse
  windows: TimelineWindow[]
  language?: DisplayLanguage
}) {
  const [search, setSearch] = useState("")
  const { currentTime, seekTo } = useVideoTime()

  const rows = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return transcript.transcript
    return transcript.transcript.filter((row) => {
      const window = windows.find((item) => item.start_time === row.start_time)
      const text = textForLanguage(row.text, row.translation ?? window?.translation, language)
      return text.toLowerCase().includes(query)
    })
  }, [language, search, transcript.transcript, windows])

  return (
    <div className="space-y-4">
      <label className="relative block">
        <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Search transcript"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </label>
      <div className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
        {rows.map((row) => {
          const active = currentTime >= row.start_time && currentTime <= row.end_time
          const window = windows.find((item) => item.start_time === row.start_time)
          const text = textForLanguage(row.text, row.translation ?? window?.translation, language)
          return (
            <button
              key={`${row.start_time}-${row.end_time}`}
              type="button"
              className={cn(
                "w-full rounded-md border p-3 text-left transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active && "border-primary bg-primary/5"
              )}
              onClick={() => seekTo(row.start_time)}
            >
              <div className="mb-1 text-xs font-medium text-primary">
                {formatTimestamp(row.start_time)} - {formatTimestamp(row.end_time)}
              </div>
              <p className="text-sm">{highlight(text, search)}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function highlight(text: string, query: string) {
  if (!query.trim()) return text
  const index = text.toLowerCase().indexOf(query.toLowerCase())
  if (index === -1) return text
  return (
    <>
      {text.slice(0, index)}
      <mark className="rounded bg-amber-200 px-0.5">{text.slice(index, index + query.length)}</mark>
      {text.slice(index + query.length)}
    </>
  )
}
