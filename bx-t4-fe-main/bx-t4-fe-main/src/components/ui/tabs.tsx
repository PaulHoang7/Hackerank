"use client"

import { cn } from "@/lib/utils"

interface TabsProps {
  tabs: Array<{ value: string; label: string }>
  value: string
  onChange: (value: string) => void
  className?: string
}

export function Tabs({ tabs, value, onChange, className }: TabsProps) {
  return (
    <div className={cn("inline-flex rounded-md border bg-background p-1", className)} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          role="tab"
          aria-selected={tab.value === value}
          className={cn(
            "h-8 rounded px-3 text-sm font-medium text-muted-foreground transition-colors",
            tab.value === value && "bg-primary text-primary-foreground"
          )}
          onClick={() => onChange(tab.value)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
