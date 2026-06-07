import type { Metadata, Viewport } from "next"
import { Inter } from "next/font/google"

import { Providers } from "@/app/providers"
import { AppShell } from "@/components/layout/app-shell"

import "./globals.css"

const inter = Inter({ subsets: ["latin"], display: "swap" })

export const metadata: Metadata = {
  title: {
    default: "BX-T4 Video Intelligence",
    template: "%s | BX-T4",
  },
  description: "Video intelligence workspace for ecommerce videos",
}

export const viewport: Viewport = {
  themeColor: "#087ea4",
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  )
}
