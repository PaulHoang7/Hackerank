"use client"

import { QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "next-themes"
import { useState } from "react"
import { Toaster } from "sonner"

import { createQueryClient } from "@/lib/query-client"

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => createQueryClient())

  return (
    <ThemeProvider attribute="class" defaultTheme="light">
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position="bottom-right" richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  )
}
