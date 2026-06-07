import { describe, expect, it } from "vitest"

import { validateVideoFile } from "@/lib/upload-validation"

describe("validateVideoFile", () => {
  it("accepts supported video extensions", () => {
    const file = new File(["x"], "demo.mp4", { type: "video/mp4" })
    expect(validateVideoFile(file)).toBeNull()
  })

  it("rejects unsupported extension", () => {
    const file = new File(["x"], "demo.txt", { type: "text/plain" })
    expect(validateVideoFile(file)).toContain("MP4")
  })

  it("accepts files above the old 500 MB frontend limit", () => {
    const file = new File(["x"], "large.mp4", { type: "video/mp4" })
    Object.defineProperty(file, "size", { value: 600 * 1024 * 1024 })
    expect(validateVideoFile(file)).toBeNull()
  })

  it("rejects files above 1 GB by default", () => {
    const file = new File(["x"], "too-large.mp4", { type: "video/mp4" })
    Object.defineProperty(file, "size", { value: 1024 * 1024 * 1024 + 1 })
    expect(validateVideoFile(file)).toContain("1 GB")
  })
})
