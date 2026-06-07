"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { BarChart3, UploadCloud } from "lucide-react"

import { Button } from "@/components/ui/button"
import { UploadVideoModal } from "@/components/video/upload-video-modal"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [uploadOpen, setUploadOpen] = useState(false)

  if (pathname.startsWith("/new-ui")) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-card lg:block">
        <div className="flex h-16 items-center border-b px-5">
          <div>
            <p className="text-sm font-semibold text-primary">BX-T4</p>
            <p className="text-xs text-muted-foreground">Video Intelligence</p>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)
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
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:px-6">
          <div className="lg:hidden">
            <p className="text-sm font-semibold text-primary">BX-T4</p>
            <p className="text-xs text-muted-foreground">Video Intelligence</p>
          </div>
          <nav className="flex gap-1 lg:hidden">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Button key={item.href} asChild variant="ghost" size="icon" aria-label={item.label}>
                  <Link href={item.href}>
                    <Icon className="h-4 w-4" />
                  </Link>
                </Button>
              )
            })}
          </nav>
          <div className="hidden text-sm text-muted-foreground lg:block">FastAPI backend: localhost:8000</div>
          <Button type="button" size="sm" onClick={() => setUploadOpen(true)}>
            <UploadCloud className="h-4 w-4" />
            Upload
          </Button>
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</main>
      </div>
      <UploadVideoModal open={uploadOpen} onOpenChange={setUploadOpen} />
    </div>
  )
}
