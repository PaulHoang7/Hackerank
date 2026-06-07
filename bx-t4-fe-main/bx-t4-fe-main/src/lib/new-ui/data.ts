import type { LucideIcon } from "lucide-react"
import { BarChart3, Gauge, UploadCloud, Video } from "lucide-react"

export type NewUiStatus =
  | "queued"
  | "processing"
  | "indexed"
  | "failed"
  | "pending"
  | "consistent"
  | "inconsistent"
  | "insufficient_evidence"

export type WorkspaceTab = "qa" | "timeline" | "sku" | "claims" | "compliance" | "metrics"

export interface NavItem {
  href: string
  label: string
  icon: LucideIcon
}

export const navItems: NavItem[] = [
  { href: "/new-ui", label: "Dashboard", icon: BarChart3 },
  { href: "/new-ui/upload", label: "Upload", icon: UploadCloud },
  { href: "/new-ui/workspace", label: "Workspace", icon: Video },
]

export const workspaceTabs: Array<{ value: WorkspaceTab; label: string }> = [
  { value: "qa", label: "Q&A" },
  { value: "timeline", label: "Timeline" },
  { value: "sku", label: "SKU" },
  { value: "claims", label: "Claims" },
  { value: "compliance", label: "Compliance" },
  { value: "metrics", label: "Metrics" },
]

export const demoVideo = {
  id: "new-ui-demo-video",
  title: "TikTok Live - Glow Serum Campaign",
  filename: "vn-id-live-commerce-demo.mp4",
  duration: "12:34",
  languages: ["Vietnamese", "Indonesian"],
  status: "indexed" as NewUiStatus,
  uploadedAt: "2026-06-06 14:32",
}

export const dashboardMetrics = [
  { label: "Videos", value: "18", note: "14 indexed" },
  { label: "Processing", value: "2", note: "1 partial window" },
  { label: "Questions", value: "126", note: "100% grounded" },
  { label: "Claims", value: "31", note: "7 need review" },
  { label: "Cost", value: "$18.42", note: "$0.034 / QA" },
  { label: "Avg latency", value: "1.2s", note: "P95 2.8s" },
]

export const videos = [
  {
    title: "TikTok Live - Glow Serum Campaign",
    filename: "vn-id-live-commerce-demo.mp4",
    status: "indexed" as NewUiStatus,
    duration: "12:34",
    languages: "VI, ID",
    owner: "Brand Ops",
  },
  {
    title: "Shopee Buyer Reviews Batch",
    filename: "review-batch-q2.mov",
    status: "processing" as NewUiStatus,
    duration: "10:18",
    languages: "ID",
    owner: "Research",
  },
  {
    title: "KOL Sunscreen Compliance",
    filename: "kol-sunscreen.mp4",
    status: "failed" as NewUiStatus,
    duration: "11:42",
    languages: "TH, EN",
    owner: "MCN",
  },
]

export const processingSteps = [
  { label: "Validate video", detail: "MP4/MOV/HLS, 10-15 minute target", progress: 100, status: "indexed" as NewUiStatus },
  { label: "Detect scenes", detail: "Stable 10-30 second analysis windows", progress: 100, status: "indexed" as NewUiStatus },
  { label: "Extract frames", detail: "Representative evidence thumbnails", progress: 86, status: "processing" as NewUiStatus },
  { label: "Analyze windows", detail: "Seed Omni transcript, OCR, visual, audio, product", progress: 68, status: "processing" as NewUiStatus },
  { label: "Build evidence map", detail: "Every answer must cite timestamp and thumbnail", progress: 42, status: "queued" as NewUiStatus },
]

export const evidence = {
  price: {
    id: "price",
    timestamp: "02:14:08",
    title: "Price board: 199K",
    visual: "Host holds Serum C30 beside an on-screen price card.",
    ocr: "SERUM C30 · 199K · FREE SHIP",
    tone: "bg-primary/10",
  },
  authentic: {
    id: "authentic",
    timestamp: "03:18:44",
    title: "Authenticity claim",
    visual: "Product box is visible, but no certificate or QR verification is visible.",
    ocr: "CHINH HANG 100%",
    tone: "bg-amber-100",
  },
  qr: {
    id: "qr",
    timestamp: "03:45:22",
    title: "QR and anti-fake seal",
    visual: "Camera zooms into back label with QR area and anti-fake seal.",
    ocr: "QR CHECK · AUTH SEAL",
    tone: "bg-emerald-100",
  },
  mismatch: {
    id: "mismatch",
    timestamp: "06:44:10",
    title: "Size mismatch: 250ml",
    visual: "Bottle label is readable while host says 500ml.",
    ocr: "250ml",
    tone: "bg-red-100",
  },
}

export const windows = [
  {
    id: "w1",
    start: "00:00",
    end: "00:24",
    transcript: "Chào cả nhà, hôm nay deal serum C30 lên sóng trong 15 phút đầu.",
    translation: "Welcome everyone. Serum C30 deal is live in the first 15 minutes.",
    visual: "Host enters frame, product shelf visible, countdown sticker.",
    ocr: "LIVE DEAL · FREE SHIP · 15:00",
    audio: "Intro music, chat cheer",
    product: "SERUM-C30",
    energy: 76,
    emotion: "excited",
    claim: null,
    evidenceId: "price",
  },
  {
    id: "w2",
    start: "02:14",
    end: "02:16",
    transcript: "Giá còn 199K, freeship cho đơn trong phiên này nha.",
    translation: "The price is 199K with free shipping during this session.",
    visual: "Host holds Serum C30 next to price card.",
    ocr: "199K · FREE SHIP",
    audio: "Order bell",
    product: "SERUM-C30",
    energy: 83,
    emotion: "confident",
    claim: "Serum C30 đang giảm còn 199K.",
    evidenceId: "price",
  },
  {
    id: "w3",
    start: "03:18",
    end: "03:26",
    transcript: "Em cam kết hàng chính hãng một trăm phần trăm.",
    translation: "I guarantee it is 100% authentic.",
    visual: "Product box is visible; no certificate, invoice, seal, or QR check page is shown.",
    ocr: "CHINH HANG 100%",
    audio: "Host energy peak",
    product: "SERUM-C30",
    energy: 88,
    emotion: "persuasive",
    claim: "Serum C30 là hàng chính hãng 100%.",
    evidenceId: "authentic",
  },
  {
    id: "w4",
    start: "03:45",
    end: "03:52",
    transcript: "Mặt sau hộp có tem chống giả và mã QR để mọi người kiểm tra.",
    translation: "The back of the box has an anti-fake seal and QR code.",
    visual: "Close-up of back label, QR zone, and anti-fake seal.",
    ocr: "QR CHECK · AUTH SEAL",
    audio: "Camera focus shift",
    product: "SERUM-C30",
    energy: 71,
    emotion: "explaining",
    claim: "Mặt sau hộp có tem chống giả và mã QR.",
    evidenceId: "qr",
  },
  {
    id: "w5",
    start: "05:31",
    end: "05:38",
    transcript: "Untuk sunscreen ini sudah BPOM, cocok untuk kulit berminyak.",
    translation: "This sunscreen has BPOM and is suitable for oily skin.",
    visual: "Sunscreen label is partially blocked by the host's hand.",
    ocr: "BPOM NA... · 129K",
    audio: "Language switch to Indonesian",
    product: "SUN-BPOM-50",
    energy: 69,
    emotion: "informative",
    claim: "Sunscreen đã có BPOM.",
    evidenceId: "authentic",
  },
  {
    id: "w6",
    start: "06:44",
    end: "06:48",
    transcript: "Chai này là bản 500ml, dùng được cả tháng luôn.",
    translation: "This bottle is the 500ml version and lasts a whole month.",
    visual: "Visible packaging label reads 250ml.",
    ocr: "250ml",
    audio: "Chat question spike",
    product: "SUN-BPOM-50",
    energy: 64,
    emotion: "uncertain",
    claim: "Chai sunscreen là bản 500ml.",
    evidenceId: "mismatch",
  },
]

export const products = [
  {
    sku: "SERUM-C30",
    name: "Glow Serum C30",
    market: "Vietnam",
    description: "Hero product in the Vietnamese segment.",
    occurrences: [
      { type: "visual", time: "00:18", confidence: 0.91 },
      { type: "spoken", time: "02:14", confidence: 0.96 },
      { type: "price", time: "02:15", confidence: 0.94 },
      { type: "demo", time: "03:45", confidence: 0.88 },
    ],
  },
  {
    sku: "SUN-BPOM-50",
    name: "Oil-control Sunscreen",
    market: "Indonesia",
    description: "Indonesian segment with BPOM and size claims.",
    occurrences: [
      { type: "spoken", time: "05:31", confidence: 0.9 },
      { type: "ocr", time: "05:34", confidence: 0.55 },
      { type: "risk", time: "06:44", confidence: 0.92 },
    ],
  },
]

export const claims = [
  {
    id: "claim-price",
    time: "02:14:08",
    speaker: "Host Mai",
    text: "Serum C30 đang giảm còn 199K.",
    verdict: "consistent" as NewUiStatus,
    confidence: 0.94,
    reason: "Transcript says 199K and OCR price board also reads 199K.",
    evidenceId: "price",
  },
  {
    id: "claim-authentic",
    time: "03:18:44",
    speaker: "Host Mai",
    text: "Serum C30 là hàng chính hãng 100%.",
    verdict: "insufficient_evidence" as NewUiStatus,
    confidence: 0.63,
    reason: "The frame shows the product box, but no certificate, QR verification page, seal, or invoice is visible.",
    evidenceId: "authentic",
  },
  {
    id: "claim-qr",
    time: "03:45:22",
    speaker: "Host Mai",
    text: "Mặt sau hộp có tem chống giả và mã QR.",
    verdict: "consistent" as NewUiStatus,
    confidence: 0.88,
    reason: "Visual close-up shows QR area and anti-fake label in the same window.",
    evidenceId: "qr",
  },
  {
    id: "claim-size",
    time: "06:44:10",
    speaker: "Host Mai",
    text: "Chai sunscreen là bản 500ml.",
    verdict: "inconsistent" as NewUiStatus,
    confidence: 0.9,
    reason: "Speech says 500ml, but packaging OCR reads 250ml.",
    evidenceId: "mismatch",
  },
]

export const qaAnswers = [
  {
    id: "qa-price",
    question: "Lúc nói giá 199K có thấy giá trên màn hình không?",
    answer: "Có. Ở 02:14:08, transcript nói giá 199K và OCR trong cùng frame cũng đọc được 199K.",
    latencyMs: 1180,
    cost: 0.0062,
    evidenceIds: ["price"],
  },
  {
    id: "qa-authentic",
    question: "Host nói hàng chính hãng có hình ảnh chứng minh không?",
    answer: "Chưa đủ bằng chứng. Host có nói claim chính hãng, nhưng frame gần đó không thấy chứng nhận, seal, QR verification page hoặc invoice.",
    latencyMs: 1320,
    cost: 0.0068,
    evidenceIds: ["authentic"],
  },
]

export const sampleQuestions = [
  "Người dẫn demo Serum C30 lúc nào?",
  "Lúc nói giá 199K có thấy giá trên màn hình không?",
  "Host nói hàng chính hãng có hình ảnh chứng minh không?",
  "Tìm mọi khoảnh khắc FREE SHIP khi sản phẩm xuất hiện.",
  "SKU SUN-BPOM-50 được nhắc bằng tiếng Indonesia lúc nào?",
  "Có chỗ nào lời nói không khớp với hình ảnh không?",
  "Sản phẩm nào xuất hiện trong combo cuối livestream?",
  "Đoạn nào có đỉnh năng lượng của host?",
  "Claim BPOM có đủ bằng chứng hình ảnh không?",
  "Tóm tắt evidence đa phương thức cho Serum C30.",
]

export const metrics = {
  modelCalls: 42,
  estimatedCost: "$18.42",
  averageLatency: "1.2s",
  throughput: "420 windows/min",
  failedWindows: 1,
  retryCount: 2,
  byType: [
    { label: "Window analysis", value: 58 },
    { label: "Q&A", value: 24 },
    { label: "Claim verify", value: 12 },
    { label: "Translation", value: 6 },
  ],
}
