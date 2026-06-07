import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva("inline-flex items-center rounded-md px-2 py-1 text-xs font-medium", {
  variants: {
    variant: {
      default: "bg-primary/10 text-primary",
      success: "bg-emerald-100 text-emerald-700",
      warning: "bg-amber-100 text-amber-800",
      danger: "bg-red-100 text-red-700",
      neutral: "bg-muted text-muted-foreground",
    },
  },
  defaultVariants: {
    variant: "default",
  },
})

export function Badge({
  className,
  variant,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
