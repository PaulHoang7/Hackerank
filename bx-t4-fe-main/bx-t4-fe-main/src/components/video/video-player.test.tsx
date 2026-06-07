import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { VideoPlayer } from "@/components/video/video-player"
import { VideoTimeProvider } from "@/hooks/use-video-time"

describe("VideoPlayer", () => {
  it("updates displayed current time from video timeupdate", () => {
    render(
      <VideoTimeProvider>
        <VideoPlayer src="/demo.mp4" title="Demo video" />
      </VideoTimeProvider>
    )
    const video = screen.getByLabelText("Demo video")
    Object.defineProperty(video, "currentTime", { value: 75, writable: true })
    fireEvent.timeUpdate(video)
    expect(screen.getByText("00:01:15")).toBeInTheDocument()
  })
})
