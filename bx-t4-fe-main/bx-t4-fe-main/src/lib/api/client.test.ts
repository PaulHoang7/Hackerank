import { describe, expect, it } from "vitest"

import { parseApiError } from "@/lib/api/client"

describe("parseApiError", () => {
  it("parses backend app error shape", () => {
    expect(parseApiError({ error: { code: "VIDEO_NOT_FOUND", message: "Video not found" } })).toEqual({
      code: "VIDEO_NOT_FOUND",
      message: "Video not found",
      details: undefined,
    })
  })

  it("parses FastAPI validation detail", () => {
    expect(parseApiError({ detail: [{ msg: "required" }] })).toEqual({
      message: "Request validation failed",
      details: [{ msg: "required" }],
    })
  })
})
