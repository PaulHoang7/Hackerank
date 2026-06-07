import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ClaimVerdictBadge } from "@/components/video/status-badge"

describe("ClaimVerdictBadge", () => {
  it("maps unclear to insufficient evidence wording", () => {
    render(<ClaimVerdictBadge verdict="unclear" />)
    expect(screen.getByText("insufficient_evidence")).toBeInTheDocument()
  })
})
