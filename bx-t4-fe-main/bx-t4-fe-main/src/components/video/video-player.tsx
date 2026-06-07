"use client"

import { useEffect, useRef } from "react"
import { Play } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useVideoTime } from "@/hooks/use-video-time"
import { formatTimestamp } from "@/lib/format"

export function VideoPlayer({
  src,
  title,
  posterUrl,
  fallbackNote,
}: {
  src?: string
  title: string
  posterUrl?: string | null
  fallbackNote?: string
}) {
  const ref = useRef<HTMLVideoElement | null>(null)
  const { currentTime, registerVideo, setCurrentTime } = useVideoTime()

  useEffect(() => {
    registerVideo(ref.current)
    return () => registerVideo(null)
  }, [registerVideo])

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="truncate">{title}</CardTitle>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Play className="h-4 w-4" />
          {formatTimestamp(currentTime)}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {src ? (
          <video
            ref={ref}
            src={src}
            poster={posterUrl ?? undefined}
            aria-label={title}
            controls
            className="aspect-video w-full rounded-md bg-black"
            onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
          />
        ) : (
          <div
            role="img"
            aria-label={title}
            className="relative flex aspect-video w-full items-end overflow-hidden rounded-md border bg-muted"
            style={
              posterUrl
                ? {
                    backgroundImage: `url("${posterUrl}")`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                  }
                : undefined
            }
          >
            <div className="w-full bg-slate-950/80 p-4 text-white">
              <p className="text-sm font-medium">Prototype video placeholder</p>
              <p className="mt-1 text-xs text-slate-200">
                {fallbackNote ?? "Evidence clicks still update the shared timestamp for UI review."}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
