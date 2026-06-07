import { apiFetch } from "@/lib/api/client"
import type { QuestionResponse } from "@/lib/api/types"

export function askQuestion(videoId: string, question: string) {
  return apiFetch<QuestionResponse>(`/videos/${videoId}/questions`, {
    method: "POST",
    body: JSON.stringify({ question }),
  })
}

export function listQuestions(videoId: string) {
  return apiFetch<QuestionResponse[]>(`/videos/${videoId}/questions`)
}

export function getQuestion(videoId: string, questionId: string) {
  return apiFetch<QuestionResponse>(`/videos/${videoId}/questions/${questionId}`)
}
