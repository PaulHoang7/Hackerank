"use client"

import Link from "next/link"
import { ExternalLink, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/state"
import { VideoStatusBadge } from "@/components/video/status-badge"
import { useDeleteVideo } from "@/features/videos/queries"
import { formatBytes, formatDate, formatTimestamp } from "@/lib/format"
import type { VideoResponse } from "@/lib/api/types"

export function VideoTable({ videos }: { videos: VideoResponse[] }) {
  const deleteMutation = useDeleteVideo()

  if (!videos.length) {
    return <EmptyState title="Chưa có video" description="Upload video thương mại điện tử để bắt đầu lập chỉ mục." />
  }

  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead className="border-b bg-muted/50 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Video</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Languages</th>
              <th className="px-4 py-3">Size</th>
              <th className="px-4 py-3">Uploaded</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {videos.map((video) => (
              <tr key={video.id} className="hover:bg-muted/30">
                <td className="max-w-xs px-4 py-3">
                  <p className="truncate font-medium">{video.title || video.original_filename}</p>
                  <p className="truncate text-xs text-muted-foreground">{video.original_filename}</p>
                </td>
                <td className="px-4 py-3">
                  <VideoStatusBadge status={video.status} />
                </td>
                <td className="px-4 py-3">{video.duration_seconds ? formatTimestamp(video.duration_seconds) : "-"}</td>
                <td className="px-4 py-3">{video.detected_languages.length ? video.detected_languages.join(", ") : "-"}</td>
                <td className="px-4 py-3">{formatBytes(video.file_size)}</td>
                <td className="px-4 py-3">{formatDate(video.created_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    <Button asChild size="sm" variant="outline">
                      <Link href={`/videos/${video.id}`}>
                        <ExternalLink className="h-4 w-4" />
                        Open
                      </Link>
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Delete ${video.title}`}
                      disabled={deleteMutation.isPending}
                      onClick={() => {
                        if (window.confirm(`Xóa video "${video.title}"?`)) {
                          deleteMutation.mutate(video.id, {
                            onSuccess: () => toast.success("Đã xóa video"),
                            onError: (error) => toast.error(error.message),
                          })
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
