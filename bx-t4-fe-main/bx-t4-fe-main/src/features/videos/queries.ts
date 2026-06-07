import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  deleteVideo,
  getClaims,
  getProducts,
  getTimeline,
  getTranscript,
  getVideo,
  getVideoMetrics,
  listVideos,
} from "@/lib/api/videos"

export const videoKeys = {
  all: ["videos"] as const,
  detail: (videoId: string) => ["videos", videoId] as const,
  timeline: (videoId: string) => ["videos", videoId, "timeline"] as const,
  transcript: (videoId: string) => ["videos", videoId, "transcript"] as const,
  products: (videoId: string) => ["videos", videoId, "products"] as const,
  claims: (videoId: string) => ["videos", videoId, "claims"] as const,
  metrics: (videoId: string) => ["videos", videoId, "metrics"] as const,
}

export function useVideos(options?: { refetchInterval?: number | false }) {
  return useQuery({ queryKey: videoKeys.all, queryFn: listVideos, ...options })
}

export function useVideo(videoId: string) {
  return useQuery({ queryKey: videoKeys.detail(videoId), queryFn: () => getVideo(videoId), enabled: Boolean(videoId) })
}

export function useTimeline(videoId: string) {
  return useQuery({ queryKey: videoKeys.timeline(videoId), queryFn: () => getTimeline(videoId), enabled: Boolean(videoId) })
}

export function useTranscript(videoId: string) {
  return useQuery({
    queryKey: videoKeys.transcript(videoId),
    queryFn: () => getTranscript(videoId),
    enabled: Boolean(videoId),
  })
}

export function useProducts(videoId: string) {
  return useQuery({ queryKey: videoKeys.products(videoId), queryFn: () => getProducts(videoId), enabled: Boolean(videoId) })
}

export function useClaims(videoId: string) {
  return useQuery({ queryKey: videoKeys.claims(videoId), queryFn: () => getClaims(videoId), enabled: Boolean(videoId) })
}

export function useVideoMetrics(videoId: string) {
  return useQuery({ queryKey: videoKeys.metrics(videoId), queryFn: () => getVideoMetrics(videoId), enabled: Boolean(videoId) })
}

export function useDeleteVideo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteVideo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: videoKeys.all }),
  })
}
