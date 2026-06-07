export type VideoStatus = "queued" | "processing" | "indexed" | "failed" | "deleted"
export type JobStatus = "queued" | "processing" | "completed" | "failed"
export type Verdict = "consistent" | "inconsistent" | "unclear"

export interface UploadResponse {
  video_id: string
  job_id: string
  status: string
}

export interface VideoResponse {
  id: string
  title: string
  original_filename: string
  storage_key: string
  content_type: string
  file_size: number
  duration_seconds: number | null
  detected_languages: string[]
  status: VideoStatus
  created_at: string
  updated_at: string
}

export interface JobResponse {
  id: string
  video_id: string
  status: JobStatus
  current_step: string
  progress_percent: number
  error_message: string | null
  started_at?: string | null
  completed_at?: string | null
  created_at: string
}

export interface TimelineWindow {
  id: string
  start_time: number
  end_time: number
  transcript: string
  translation: string | null
  scene_description: string
  ocr_text: Record<string, unknown>[]
  audio_events: Record<string, unknown>[]
  detected_entities: Record<string, unknown>[]
  chunk_metadata: Record<string, unknown>
  index_text: string
  clip_storage_key: string | null
  thumbnail_storage_key: string | null
  energy_score: number
  emotion: string | null
}

export interface ProductResponse {
  id: string
  sku: string
  name: string
  description: string | null
  image_url: string | null
  product_metadata: Record<string, unknown>
  occurrences: ProductOccurrenceResponse[]
}

export interface ProductOccurrenceResponse {
  id: string
  video_window_id: string
  occurrence_type: "visual" | "spoken" | "ocr"
  timestamp: number
  confidence: number
}

export interface ClaimResponse {
  id: string
  video_id: string
  video_window_id: string
  claim_text: string
  timestamp: number
  speaker: string | null
  created_at: string
}

export interface ClaimVerificationResponse {
  claim_id: string
  claim_text: string
  timestamp: number
  verdict: Verdict
  confidence: number
  explanation: string
  evidence: ClaimEvidenceResponse[]
}

export interface ClaimEvidenceResponse {
  timestamp?: number
  thumbnail_url?: string | null
  transcript?: string
  visual_description?: string
  rationale?: string
  source?: string
}

export interface QuestionRequest {
  question: string
}

export interface QuestionEvidenceResponse {
  timestamp: number
  start_time: number
  end_time: number
  thumbnail_url: string | null
  clip_url?: string | null
  transcript: string
  translation?: string | null
  visual_description: string
  rationale: string
}

export interface QuestionResponse {
  id: string
  video_id: string
  question: string
  answer: string
  latency_ms: number
  estimated_cost: number
  created_at: string
  evidence: QuestionEvidenceResponse[]
}

export interface MetricsOverviewResponse {
  videos_total: number
  videos_indexed: number
  jobs_processing: number
  questions_total: number
  estimated_cost_total: number
  average_latency_ms: number
  model_calls_total: number
  model_calls_failed: number
  average_model_latency_ms: number
}

export interface VideoMetricsResponse {
  video_id: string
  window_count: number
  claim_count: number
  question_count: number
  estimated_cost: number
  model_call_count: number
  failed_model_call_count: number
  average_model_latency_ms: number
}

export interface TranscriptResponse {
  video_id: string
  transcript: Array<{
    start_time: number
    end_time: number
    text: string
    speaker?: string | null
    language?: string | null
    translation?: string | null
  }>
}
