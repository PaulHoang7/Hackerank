import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { EvidenceCard } from "@/components/questions/evidence-card"
import { VideoTimeProvider } from "@/hooks/use-video-time"
import type { QuestionEvidenceResponse } from "@/lib/api/types"

const evidence: QuestionEvidenceResponse = {
  timestamp: 12,
  start_time: 10,
  end_time: 20,
  thumbnail_url: null,
  transcript: "Presenter mentions the product",
  visual_description: "Product box is visible",
  rationale: "Transcript and visual match",
}

describe("EvidenceCard", () => {
  it("renders timestamp and rationale", () => {
    render(
      <VideoTimeProvider>
        <EvidenceCard evidence={evidence} language="vi" />
      </VideoTimeProvider>
    )
    expect(screen.getByText("00:00:10 - 00:00:20")).toBeInTheDocument()
    expect(screen.getByText(/Transcript and visual match/)).toBeInTheDocument()
  })
})
