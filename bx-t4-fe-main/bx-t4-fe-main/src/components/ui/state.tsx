import { AlertCircle, Inbox, RotateCcw } from "lucide-react"

import { Button } from "@/components/ui/button"

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-lg border border-dashed bg-card p-8 text-center">
      <Inbox className="mb-3 h-8 w-8 text-muted-foreground" />
      <p className="font-medium">{title}</p>
      {description ? <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p> : null}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-lg border bg-card p-8 text-center">
      <AlertCircle className="mb-3 h-8 w-8 text-destructive" />
      <p className="font-medium">Không tải được dữ liệu</p>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>
      {onRetry ? (
        <Button className="mt-4" variant="outline" onClick={onRetry}>
          <RotateCcw className="h-4 w-4" />
          Thử lại
        </Button>
      ) : null}
    </div>
  )
}
