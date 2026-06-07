import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { askQuestion, listQuestions } from "@/lib/api/questions"

export const questionKeys = {
  list: (videoId: string) => ["videos", videoId, "questions"] as const,
}

export function useQuestions(videoId: string) {
  return useQuery({
    queryKey: questionKeys.list(videoId),
    queryFn: () => listQuestions(videoId),
    enabled: Boolean(videoId),
  })
}

export function useAskQuestion(videoId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (question: string) => askQuestion(videoId, question),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: questionKeys.list(videoId) }),
  })
}
