"use client"

import { createContext, useContext, useMemo, useRef, useState } from "react"

interface VideoTimeContextValue {
  currentTime: number
  setCurrentTime: (time: number) => void
  seekTo: (time: number) => void
  registerVideo: (element: HTMLVideoElement | null) => void
}

const VideoTimeContext = createContext<VideoTimeContextValue | null>(null)

export function VideoTimeProvider({ children }: { children: React.ReactNode }) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [currentTime, setCurrentTime] = useState(0)

  const value = useMemo<VideoTimeContextValue>(
    () => ({
      currentTime,
      setCurrentTime,
      seekTo: (time) => {
        const nextTime = Math.max(0, time)
        if (videoRef.current) {
          videoRef.current.currentTime = nextTime
          void videoRef.current.play().catch(() => undefined)
        }
        setCurrentTime(nextTime)
      },
      registerVideo: (element) => {
        videoRef.current = element
      },
    }),
    [currentTime]
  )

  return <VideoTimeContext.Provider value={value}>{children}</VideoTimeContext.Provider>
}

export function useVideoTime() {
  const value = useContext(VideoTimeContext)
  if (!value) {
    throw new Error("useVideoTime must be used inside VideoTimeProvider")
  }
  return value
}
