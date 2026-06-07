import { describe, expect, it } from "vitest"

import { formatTimestamp } from "@/lib/format"

describe("formatTimestamp", () => {
  it("formats seconds as HH:MM:SS", () => {
    expect(formatTimestamp(65)).toBe("00:01:05")
    expect(formatTimestamp(3661)).toBe("01:01:01")
  })
})
