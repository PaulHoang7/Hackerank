"use client"

import { Button } from "@/components/ui/button"

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="max-w-md rounded-lg border bg-card p-6 shadow-sm">
        <h1 className="text-lg font-semibold">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <Button className="mt-4" onClick={reset}>
          Retry
        </Button>
      </div>
    </main>
  )
}
