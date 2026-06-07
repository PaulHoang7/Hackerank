"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Clock3, LocateFixed, Play, ShieldAlert } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import type { NewUiStatus } from "@/lib/new-ui/data"
import { navItems } from "@/lib/new-ui/data"

export function NewUiShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-card lg:block">
        <div className="flex h-16 items-center border-b px-5">
          <Link href="/new-ui">
            <p className="text-sm font-semibold text-primary">BX-T4</p>
            <p className="text-xs text-muted-foreground">New UI demo</p>
          </Link>
        </div>
        <nav className="space-y-1 p-3">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = item.href === "/new-ui" ? pathname === "/new-ui" : pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground",
                  active && "bg-primary/10 text-primary"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between gap-3 border-b bg-background/95 px-4 backdrop-blur md:px-6">
          <div>
            <p className="text-sm font-semibold text-primary">BX-T4 Video Intelligence</p>
            <p className="text-xs text-muted-foreground">Evidence-first frontend prototype</p>
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = item.href === "/new-ui" ? pathname === "/new-ui" : pathname.startsWith(item.href)
              return (
                <Button key={item.href} asChild size="sm" variant={active ? "default" : "outline"} className="lg:hidden">
                  <Link href={item.href}>
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                </Button>
              )
            })}
            <Button asChild size="sm">
              <Link href="/new-ui/upload">Upload</Link>
            </Button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  )
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string
  description: string
  actions?: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  )
}

export function SectionTitle({ title, description }: { title: string; description?: string }) {
  return (
    <div>
      <h2 className="text-lg font-semibold">{title}</h2>
      {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
    </div>
  )
}

export function StatusBadge({ status }: { status: NewUiStatus }) {
  const label = status === "insufficient_evidence" ? "insufficient evidence" : status
  const variant =
    status === "indexed" || status === "consistent"
      ? "success"
      : status === "failed" || status === "inconsistent"
        ? "danger"
        : status === "processing" || status === "queued" || status === "insufficient_evidence"
          ? "warning"
          : "neutral"

  return <Badge variant={variant}>{label}</Badge>
}

export function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
        <p className="mt-2 text-2xl font-semibold">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{note}</p>
      </CardContent>
    </Card>
  )
}

export function EvidenceThumb({
  title,
  timestamp,
  tone = "bg-primary/10",
  className,
}: {
  title: string
  timestamp: string
  tone?: string
  className?: string
}) {
  return (
    <div className={cn("relative overflow-hidden rounded-md border", tone, className)}>
      <div className="absolute left-2 top-2 rounded bg-background/95 px-2 py-1 text-xs font-medium text-foreground shadow-sm">
        {timestamp}
      </div>
      <div className="flex h-full min-h-24 items-center justify-center p-4 text-center">
        <div>
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-background/90 shadow-sm">
            <Play className="h-5 w-5 text-primary" />
          </div>
          <p className="mt-3 text-sm font-medium">{title}</p>
          <p className="mt-1 text-xs text-muted-foreground">Evidence frame</p>
        </div>
      </div>
    </div>
  )
}

export function EvidenceCard({
  title,
  timestamp,
  visual,
  ocr,
  tone,
}: {
  title: string
  timestamp: string
  visual: string
  ocr: string
  tone?: string
}) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex gap-3">
        <EvidenceThumb title={title} timestamp={timestamp} tone={tone} className="h-24 w-36 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-xs font-medium text-primary">
            <Clock3 className="h-3.5 w-3.5" />
            {timestamp}
          </div>
          <p className="mt-1 line-clamp-2 text-sm">{visual}</p>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">OCR: {ocr}</p>
          <Button className="mt-2" size="sm" variant="outline">
            <LocateFixed className="h-4 w-4" />
            Jump
          </Button>
        </div>
      </div>
    </div>
  )
}

export function ProcessingStep({
  label,
  detail,
  progress,
  status,
}: {
  label: string
  detail: string
  progress: number
  status: NewUiStatus
}) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
        </div>
        <StatusBadge status={status} />
      </div>
      <Progress value={progress} className="mt-3" />
    </div>
  )
}

export function BoundaryNotice() {
  return (
    <div className="flex gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
      <p>
        Claim check chỉ kiểm tra hình ảnh/OCR/frame trong video có ủng hộ lời nói hay không, không fact-check sự thật
        ngoài đời.
      </p>
    </div>
  )
}

export function PanelCard({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: React.ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}
