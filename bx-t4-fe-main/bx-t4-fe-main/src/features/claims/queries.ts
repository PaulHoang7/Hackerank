import { useMutation, useQueryClient } from "@tanstack/react-query"

import { verifyClaim } from "@/lib/api/claims"
import { videoKeys } from "@/features/videos/queries"

export function useVerifyClaim(videoId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (claimId: string) => verifyClaim(videoId, claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: videoKeys.claims(videoId) })
      queryClient.invalidateQueries({ queryKey: videoKeys.metrics(videoId) })
    },
  })
}
