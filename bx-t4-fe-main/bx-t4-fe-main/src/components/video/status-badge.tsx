import { Badge } from "@/components/ui/badge"
import type { JobStatus, VideoStatus, Verdict } from "@/lib/api/types"

export function VideoStatusBadge({ status }: { status: VideoStatus | JobStatus }) {
  const variant =
    status === "indexed" || status === "completed"
      ? "success"
      : status === "failed"
        ? "danger"
        : status === "processing" || status === "queued"
          ? "warning"
          : "neutral"

  return <Badge variant={variant}>{status}</Badge>
}

export function ClaimVerdictBadge({ verdict }: { verdict?: Verdict | "pending" }) {
  if (!verdict || verdict === "pending") {
    return <Badge variant="neutral">pending</Badge>
  }
  if (verdict === "consistent") {
    return <Badge variant="success">consistent</Badge>
  }
  if (verdict === "inconsistent") {
    return <Badge variant="danger">inconsistent</Badge>
  }
  return <Badge variant="warning">insufficient_evidence</Badge>
}
