import type { LucideIcon } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"

export function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: LucideIcon
  label: string
  value: string | number
  detail?: string
}) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-4">
        <div className="rounded-md bg-primary/10 p-2 text-primary">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-1 truncate text-2xl font-semibold">{value}</p>
          {detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}
        </div>
      </CardContent>
    </Card>
  )
}
