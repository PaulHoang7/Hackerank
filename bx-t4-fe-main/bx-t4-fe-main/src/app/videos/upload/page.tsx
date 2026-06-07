"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { UploadCloud, XCircle } from "lucide-react"
import { toast } from "sonner"

import { JobProgress } from "@/components/video/job-progress"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useJob } from "@/features/jobs/queries"
import { uploadVideoWithProgress } from "@/lib/api/videos"
import { formatBytes } from "@/lib/format"
import { MAX_UPLOAD_SIZE_BYTES, validateVideoFile } from "@/lib/upload-validation"
import { cn } from "@/lib/utils"

export default function UploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [videoId, setVideoId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const jobQuery = useJob(jobId)

  useEffect(() => {
    if (jobQuery.data?.status === "completed" && videoId) {
      toast.success("Video indexed")
      router.push(`/videos/${videoId}`)
    }
  }, [jobQuery.data?.status, router, videoId])

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
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Upload video</h1>
        <p className="text-sm text-muted-foreground">
          MP4, MOV or WebM up to {formatBytes(MAX_UPLOAD_SIZE_BYTES)}. The app polls the indexing job every 2 seconds.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Source video</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <label
            className={cn(
              "flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/40 p-8 text-center transition-colors hover:border-primary",
              error && "border-destructive"
            )}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault()
              chooseFile(event.dataTransfer.files.item(0))
            }}
          >
            <UploadCloud className="mb-3 h-10 w-10 text-primary" />
            <p className="font-medium">Drag video here or click to browse</p>
            <p className="mt-1 text-sm text-muted-foreground">Backend field name: file</p>
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
          <div className="flex gap-2">
            <Button disabled={!file || isUploading} onClick={startUpload}>
              <UploadCloud className="h-4 w-4" />
              {isUploading ? "Uploading..." : "Start upload"}
            </Button>
            {jobQuery.data?.status === "failed" ? (
              <Button variant="outline" onClick={startUpload} disabled={!file || isUploading}>
                Retry
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>
      {jobQuery.data ? <JobProgress job={jobQuery.data} /> : null}
    </div>
  )
}
