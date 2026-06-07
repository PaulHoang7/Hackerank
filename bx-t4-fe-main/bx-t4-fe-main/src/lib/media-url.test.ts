import { describe, expect, it } from "vitest"

import { buildMediaUrl } from "@/lib/media-url"

describe("buildMediaUrl", () => {
  it("keeps absolute URLs", () => {
    expect(buildMediaUrl("https://example.com/a.jpg")).toBe("https://example.com/a.jpg")
  })

  it("prefixes backend URL for relative storage paths", () => {
    expect(buildMediaUrl("/storage/a.jpg")).toBe("http://localhost:8000/storage/a.jpg")
  })
})
