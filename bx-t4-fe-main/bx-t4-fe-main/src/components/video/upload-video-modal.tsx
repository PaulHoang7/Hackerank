"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { UploadCloud, X, XCircle } from "lucide-react"
import { toast } from "sonner"

import { JobProgress } from "@/components/video/job-progress"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useJob } from "@/features/jobs/queries"
import { uploadVideoWithProgress } from "@/lib/api/videos"
import { formatBytes } from "@/lib/format"
import { MAX_UPLOAD_SIZE_BYTES, validateVideoFile } from "@/lib/upload-validation"
import { cn } from "@/lib/utils"

interface UploadVideoModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function UploadVideoModal({ open, onOpenChange }: UploadVideoModalProps) {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [videoId, setVideoId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const jobQuery = useJob(jobId)

  useEffect(() => {
    if (jobQuery.data?.status === "completed" && videoId) {
      toast.success("Video indexed")
      onOpenChange(false)
      router.push(`/videos/${videoId}`)
    }
  }, [jobQuery.data?.status, onOpenChange, router, videoId])

  useEffect(() => {
    if (!open && !isUploading && jobQuery.data?.status !== "processing" && jobQuery.data?.status !== "queued") {
      setFile(null)
      setError(null)
      setUploadProgress(0)
      setJobId(null)
      setVideoId(null)
      setIsDragging(false)
    }
  }, [isUploading, jobQuery.data?.status, open])

  if (!open) return null

  const chooseFile = (nextFile: File | null) => {
    setError(null)
    setUploadProgress(0)
    setJobId(null)
    setVideoId(null)
    if (!nextFile) {
      setFile(null)
      return
    }
    const validationError = validateVideoFile(nextFile)
    if (validationError) {
      setError(validationError)
      setFile(null)
      return
    }
    setFile(nextFile)
  }

  const startUpload = async () => {
    if (!file) return
    setIsUploading(true)
    setError(null)
    try {
      const response = await uploadVideoWithProgress(file, setUploadProgress)
      setJobId(response.job_id)
      setVideoId(response.video_id)
      toast.success("Upload complete, indexing started")
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed")
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 px-4 py-6">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Upload video"
        className="w-full max-w-2xl rounded-lg border bg-background shadow-xl"
      >
        <div className="flex items-start justify-between gap-4 border-b p-5">
          <div>
            <h2 className="text-lg font-semibold">Upload video</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              MP4, MOV or WebM up to {formatBytes(MAX_UPLOAD_SIZE_BYTES)}.
            </p>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={() => onOpenChange(false)} aria-label="Close upload">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="space-y-4 p-5">
          <label
            className={cn(
              "flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/40 p-8 text-center transition-colors hover:border-primary",
              isDragging && "border-primary bg-primary/5",
              error && "border-destructive"
            )}
            onDragEnter={(event) => {
              event.preventDefault()
              setIsDragging(true)
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault()
              setIsDragging(false)
              chooseFile(event.dataTransfer.files.item(0))
            }}
          >
            <UploadCloud className="mb-3 h-10 w-10 text-primary" />
            <p className="font-medium">Drop video here or click to browse</p>
            <p className="mt-1 text-sm text-muted-foreground">The selected file uploads directly to the backend.</p>
            <input
              type="file"
              className="sr-only"
              accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
              onChange={(event) => chooseFile(event.target.files?.item(0) ?? null)}
            />
          </label>
          {file ? (
            <div className="rounded-md border bg-background p-3 text-sm">
              <p className="font-medium">{file.name}</p>
              <p className="text-muted-foreground">{formatBytes(file.size)}</p>
            </div>
          ) : null}
          {error ? (
            <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <XCircle className="h-4 w-4" />
              {error}
            </div>
          ) : null}
          {isUploading ? (
            <div className="space-y-2">
              <Progress value={uploadProgress} />
              <p className="text-xs text-muted-foreground">Uploading {uploadProgress}%</p>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button type="button" disabled={!file || isUploading} onClick={startUpload}>
              <UploadCloud className="h-4 w-4" />
              {isUploading ? "Uploading..." : "Start upload"}
            </Button>
            {jobQuery.data?.status === "failed" ? (
              <Button type="button" variant="outline" onClick={startUpload} disabled={!file || isUploading}>
                Retry
              </Button>
            ) : null}
          </div>
          {jobQuery.data ? <JobProgress job={jobQuery.data} /> : null}
        </div>
      </div>
    </div>
  )
}
