"use client"

import Image from "next/image"
import { LocateFixed, PackageSearch } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useVideoTime } from "@/hooks/use-video-time"
import type { ProductResponse } from "@/lib/api/types"
import { formatTimestamp } from "@/lib/format"
import { buildMediaUrl } from "@/lib/media-url"

export function ProductsPanel({ products }: { products: ProductResponse[] }) {
  const { seekTo } = useVideoTime()

  if (!products.length) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
        Backend has not verified any product candidates for this video.
      </div>
    )
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {products.map((product) => {
        const imageUrl = buildMediaUrl(product.image_url)
        return (
          <div key={product.id} className="rounded-lg border bg-card p-4">
            <div className="flex gap-4">
              <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-md bg-muted">
                {imageUrl ? (
                  <Image src={imageUrl} alt={product.name} fill sizes="96px" className="object-cover" unoptimized />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <PackageSearch className="h-6 w-6 text-muted-foreground" />
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium">{product.name}</p>
                <p className="text-sm text-muted-foreground">SKU {product.sku}</p>
                {product.description ? <p className="mt-2 line-clamp-2 text-sm">{product.description}</p> : null}
              </div>
            </div>
            <div className="mt-3 space-y-2">
              {product.occurrences.length ? (
                product.occurrences.map((occurrence) => (
                  <div key={occurrence.id} className="flex items-center justify-between gap-3 rounded-md border p-2">
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <Badge variant="neutral">{occurrence.occurrence_type}</Badge>
                      <span className="font-medium">{formatTimestamp(occurrence.timestamp)}</span>
                      <span className="text-muted-foreground">{Math.round(occurrence.confidence * 100)}%</span>
                    </div>
                    <Button size="sm" variant="outline" onClick={() => seekTo(occurrence.timestamp)}>
                      <LocateFixed className="h-4 w-4" />
                      Jump
                    </Button>
                  </div>
                ))
              ) : (
                <p className="rounded-md border border-dashed p-2 text-sm text-muted-foreground">
                  No verified product occurrence timestamp is available.
                </p>
              )}
            </div>
            <pre className="mt-3 max-h-28 overflow-auto rounded-md bg-muted p-2 text-xs text-muted-foreground">
              {JSON.stringify(product.product_metadata, null, 2)}
            </pre>
          </div>
        )
      })}
    </div>
  )
}
