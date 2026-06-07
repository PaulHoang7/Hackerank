import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { JobProgress } from "@/components/video/job-progress"
import type { JobResponse } from "@/lib/api/types"

const job: JobResponse = {
  id: "job-1",
  video_id: "video-1",
  status: "processing",
  current_step: "extracting frames",
  progress_percent: 45,
  error_message: null,
  created_at: "2026-06-05T00:00:00Z",
}

describe("JobProgress", () => {
  it("renders current step and progress", () => {
    render(<JobProgress job={job} />)
    expect(screen.getByText("extracting frames")).toBeInTheDocument()
    expect(screen.getByText("45%")).toBeInTheDocument()
  })
})
