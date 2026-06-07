import { describe, expect, it } from "vitest"

import { questionSchema } from "@/components/questions/qa-chat"

describe("questionSchema", () => {
  it("rejects empty questions", () => {
    expect(questionSchema.safeParse({ question: "" }).success).toBe(false)
  })

  it("accepts valid questions", () => {
    expect(questionSchema.safeParse({ question: "Sản phẩm xuất hiện lúc nào?" }).success).toBe(true)
  })
})
