import { Loader2 } from "lucide-react"

import { Progress } from "@/components/ui/progress"
import { VideoStatusBadge } from "@/components/video/status-badge"
import type { JobResponse } from "@/lib/api/types"

export function JobProgress({ job }: { job: JobResponse }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium">{job.current_step || "queued"}</p>
          <p className="text-xs text-muted-foreground">Job {job.id}</p>
        </div>
        <div className="flex items-center gap-2">
          {job.status === "processing" || job.status === "queued" ? (
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
          ) : null}
          <VideoStatusBadge status={job.status} />
        </div>
      </div>
      <Progress className="mt-4" value={job.progress_percent} />
      <div className="mt-2 flex justify-between text-xs text-muted-foreground">
        <span>{job.progress_percent}%</span>
        {job.error_message ? <span className="text-destructive">{job.error_message}</span> : null}
      </div>
    </div>
  )
}
