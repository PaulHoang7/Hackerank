import type {
  ClaimResponse,
  ClaimVerificationResponse,
  MetricsOverviewResponse,
  ProductResponse,
  QuestionEvidenceResponse,
  QuestionResponse,
  TimelineWindow,
  TranscriptResponse,
  VideoMetricsResponse,
  VideoResponse,
} from "@/lib/api/types"

export const DEMO_VIDEO_ID = "demo-live-commerce"

const createdAt = "2026-06-06T02:30:00.000Z"

function mockFrame(title: string, detail: string, accent: string) {
  const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#f8fafc"/>
      <stop offset="100%" stop-color="#dbeafe"/>
    </linearGradient>
  </defs>
  <rect width="640" height="360" fill="url(#bg)"/>
  <rect x="32" y="34" width="576" height="292" rx="22" fill="#ffffff" stroke="#cbd5e1" stroke-width="3"/>
  <rect x="70" y="76" width="178" height="214" rx="18" fill="${accent}" opacity="0.18"/>
  <rect x="104" y="108" width="110" height="148" rx="14" fill="${accent}"/>
  <circle cx="445" cy="126" r="48" fill="#0f172a" opacity="0.08"/>
  <rect x="330" y="190" width="210" height="28" rx="14" fill="${accent}" opacity="0.2"/>
  <text x="320" y="118" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#0f172a">${title}</text>
  <text x="320" y="160" font-family="Arial, sans-serif" font-size="18" fill="#475569">${detail}</text>
  <text x="320" y="260" font-family="Arial, sans-serif" font-size="16" fill="#64748b">mock evidence frame</text>
</svg>`
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

const frames = {
  opening: mockFrame("LIVE SALE", "FREE SHIP + countdown", "#087ea4"),
  serumPrice: mockFrame("SERUM C30", "OCR: 199K / FREE SHIP", "#16a34a"),
  authenticClaim: mockFrame("AUTH CLAIM", "No certificate visible", "#f59e0b"),
  qrSeal: mockFrame("QR + SEAL", "Box back and anti-fake label", "#0f766e"),
  bpom: mockFrame("ID SUNSCREEN", "BPOM text is partially blocked", "#7c3aed"),
  mismatch: mockFrame("SIZE CHECK", "Speech: 500ml / OCR: 250ml", "#dc2626"),
  closing: mockFrame("FLASH SALE", "Chat spike + final CTA", "#db2777"),
}

export const demoPosterUrl = frames.opening

export const demoVideo: VideoResponse = {
  id: DEMO_VIDEO_ID,
  title: "Demo livestream e-commerce: Serum C30 flash sale",
  original_filename: "demo-vn-id-live-commerce-12m.mp4",
  storage_key: "",
  content_type: "video/mp4",
  file_size: 184_000_000,
  duration_seconds: 735,
  detected_languages: ["vi", "id"],
  status: "indexed",
  created_at: createdAt,
  updated_at: createdAt,
}

const demoTimelineWindows = [
  {
    id: "demo-window-001",
    start_time: 0,
    end_time: 45,
    transcript: "Chào cả nhà, hôm nay live flash sale serum C30, miễn phí vận chuyển trong 15 phút đầu.",
    translation: "Welcome everyone. Today is a flash sale for Serum C30 with free shipping in the first 15 minutes.",
    scene_description: "Host opens the livestream beside a product shelf. A countdown banner and free shipping badge are visible.",
    ocr_text: [{ text: "FREE SHIP", confidence: 0.94 }, { text: "15:00", type: "countdown", confidence: 0.88 }],
    audio_events: [{ label: "intro_music", confidence: 0.82 }, { label: "chat_cheer", confidence: 0.74 }],
    detected_entities: [{ type: "host", name: "Mai" }, { type: "product", sku: "SERUM-C30" }],
    energy_score: 0.86,
    emotion: "excited",
  },
  {
    id: "demo-window-002",
    start_time: 70,
    end_time: 112,
    transcript: "Serum C30 này đang giảm còn một trăm chín chín nghìn, trên màn hình cũng có mã freeship nha.",
    translation: "This Serum C30 is discounted to 199K, and the free shipping code is also on screen.",
    scene_description: "Host holds a serum bottle close to camera. Price label 199K is visible in the lower third.",
    ocr_text: [{ text: "SERUM C30", confidence: 0.91 }, { text: "199K", confidence: 0.96 }, { text: "FREE SHIP", confidence: 0.93 }],
    audio_events: [{ label: "bell_order", confidence: 0.69 }],
    detected_entities: [{ type: "product", sku: "SERUM-C30", visibility: "front_label" }],
    energy_score: 0.78,
    emotion: "confident",
  },
  {
    id: "demo-window-003",
    start_time: 132,
    end_time: 172,
    transcript: "Em cam kết hàng chính hãng một trăm phần trăm, mọi người yên tâm đặt liền tay.",
    translation: "I guarantee it is 100% authentic, everyone can order with confidence.",
    scene_description: "Host holds the product box, but no certificate, invoice, QR check page, or anti-counterfeit seal is clearly visible.",
    ocr_text: [{ text: "CHINH HANG 100%", confidence: 0.61 }],
    audio_events: [{ label: "host_energy_peak", confidence: 0.81 }],
    detected_entities: [{ type: "product", sku: "SERUM-C30", visibility: "front_box" }],
    energy_score: 0.83,
    emotion: "persuasive",
  },
  {
    id: "demo-window-004",
    start_time: 214,
    end_time: 252,
    transcript: "Mặt sau hộp có tem chống giả và mã QR, mọi người nhìn kỹ chỗ này nha.",
    translation: "The back of the box has an anti-counterfeit seal and QR code. Please look closely here.",
    scene_description: "Camera zooms into the back of the box. A QR code area and small anti-counterfeit label are visible.",
    ocr_text: [{ text: "QR CHECK", confidence: 0.85 }, { text: "ANTI-FAKE", confidence: 0.76 }],
    audio_events: [{ label: "camera_focus_change", confidence: 0.71 }],
    detected_entities: [{ type: "product", sku: "SERUM-C30", visibility: "back_label" }],
    energy_score: 0.65,
    emotion: "explaining",
  },
  {
    id: "demo-window-005",
    start_time: 315,
    end_time: 360,
    transcript: "Untuk sunscreen ini sudah BPOM, cocok untuk kulit berminyak, harga hari ini seratus dua puluh sembilan ribu.",
    translation: "This sunscreen has BPOM registration, is suitable for oily skin, and today's price is 129K.",
    scene_description: "Host switches to an Indonesian sunscreen. The BPOM line is partially blocked by the host's hand.",
    ocr_text: [{ text: "SUNSCREEN", confidence: 0.9 }, { text: "BPOM NA...", confidence: 0.54 }, { text: "129K", confidence: 0.93 }],
    audio_events: [{ label: "language_switch_id", confidence: 0.88 }],
    detected_entities: [{ type: "product", sku: "SUN-BPOM-50" }],
    energy_score: 0.7,
    emotion: "informative",
  },
  {
    id: "demo-window-006",
    start_time: 432,
    end_time: 468,
    transcript: "Chai này là bản năm trăm ml, dùng được cả tháng luôn.",
    translation: "This bottle is the 500ml version and can be used for a whole month.",
    scene_description: "The bottle label visible on screen reads 250ml while the host says 500ml.",
    ocr_text: [{ text: "250ml", confidence: 0.95 }],
    audio_events: [{ label: "chat_question_spike", confidence: 0.77 }],
    detected_entities: [{ type: "product", sku: "SUN-BPOM-50", visibility: "front_label" }],
    energy_score: 0.62,
    emotion: "uncertain",
  },
  {
    id: "demo-window-007",
    start_time: 544,
    end_time: 590,
    transcript: "Bạn nào mua combo serum với sunscreen thì được freeship và tặng thêm bông tẩy trang.",
    translation: "Anyone buying the serum and sunscreen combo gets free shipping and a cotton pad gift.",
    scene_description: "Two products are placed side by side. Combo badge, gift badge, and free shipping text are visible.",
    ocr_text: [{ text: "COMBO", confidence: 0.91 }, { text: "FREE SHIP", confidence: 0.94 }, { text: "GIFT", confidence: 0.86 }],
    audio_events: [{ label: "order_sound_cluster", confidence: 0.82 }],
    detected_entities: [{ type: "product", sku: "SERUM-C30" }, { type: "product", sku: "SUN-BPOM-50" }],
    energy_score: 0.88,
    emotion: "urgent",
  },
  {
    id: "demo-window-008",
    start_time: 650,
    end_time: 700,
    transcript: "Chốt đơn trong năm phút cuối, mã giảm giá sẽ tự áp ở giỏ hàng.",
    translation: "Place your order in the last five minutes, the discount code will apply automatically in the cart.",
    scene_description: "Closing segment with countdown timer, chat reactions, and large final CTA banner.",
    ocr_text: [{ text: "05:00", type: "countdown", confidence: 0.89 }, { text: "LAST CALL", confidence: 0.85 }],
    audio_events: [{ label: "countdown_music", confidence: 0.78 }, { label: "chat_cheer", confidence: 0.8 }],
    detected_entities: [{ type: "host", name: "Mai" }],
    energy_score: 0.91,
    emotion: "urgent",
  },
]

export const demoTimeline: TimelineWindow[] = demoTimelineWindows.map((window) => ({
  chunk_metadata: {},
  index_text: [window.transcript, window.scene_description].join("\n"),
  clip_storage_key: null,
  thumbnail_storage_key: null,
  ...window,
}))

export const demoTranscript: TranscriptResponse = {
  video_id: DEMO_VIDEO_ID,
  transcript: demoTimeline.map((window) => ({
    start_time: window.start_time,
    end_time: window.end_time,
    text: window.transcript,
  })),
}

export const demoProducts: ProductResponse[] = [
  {
    id: "demo-product-serum",
    sku: "SERUM-C30",
    name: "Serum C30 brightening",
    description: "Hero product in the Vietnamese livestream segment.",
    image_url: frames.serumPrice,
    product_metadata: {
      market: "VN",
      brief_required_claims: ["price must match on-screen OCR", "authenticity claim needs visual proof"],
    },
    occurrences: [
      { id: "occ-serum-1", video_window_id: "demo-window-001", occurrence_type: "visual", timestamp: 18, confidence: 0.82 },
      { id: "occ-serum-2", video_window_id: "demo-window-002", occurrence_type: "spoken", timestamp: 88, confidence: 0.96 },
      { id: "occ-serum-3", video_window_id: "demo-window-004", occurrence_type: "visual", timestamp: 225, confidence: 0.9 },
      { id: "occ-serum-4", video_window_id: "demo-window-007", occurrence_type: "visual", timestamp: 555, confidence: 0.87 },
    ],
  },
  {
    id: "demo-product-sunscreen",
    sku: "SUN-BPOM-50",
    name: "Oil-control sunscreen",
    description: "Indonesian-language product segment with BPOM and size claims.",
    image_url: frames.bpom,
    product_metadata: {
      market: "ID",
      brief_required_claims: ["BPOM line must be visible", "size claims must match packaging OCR"],
    },
    occurrences: [
      { id: "occ-sun-1", video_window_id: "demo-window-005", occurrence_type: "spoken", timestamp: 330, confidence: 0.92 },
      { id: "occ-sun-2", video_window_id: "demo-window-006", occurrence_type: "ocr", timestamp: 449, confidence: 0.95 },
      { id: "occ-sun-3", video_window_id: "demo-window-007", occurrence_type: "visual", timestamp: 556, confidence: 0.86 },
    ],
  },
]

export const demoClaims: ClaimResponse[] = [
  {
    id: "demo-claim-price-199",
    video_id: DEMO_VIDEO_ID,
    video_window_id: "demo-window-002",
    claim_text: "Serum C30 đang giảm còn 199K.",
    timestamp: 88,
    speaker: "Mai",
    created_at: createdAt,
  },
  {
    id: "demo-claim-authentic",
    video_id: DEMO_VIDEO_ID,
    video_window_id: "demo-window-003",
    claim_text: "Serum C30 là hàng chính hãng 100%.",
    timestamp: 145,
    speaker: "Mai",
    created_at: createdAt,
  },
  {
    id: "demo-claim-qr-seal",
    video_id: DEMO_VIDEO_ID,
    video_window_id: "demo-window-004",
    claim_text: "Mặt sau hộp có tem chống giả và mã QR.",
    timestamp: 226,
    speaker: "Mai",
    created_at: createdAt,
  },
  {
    id: "demo-claim-bpom",
    video_id: DEMO_VIDEO_ID,
    video_window_id: "demo-window-005",
    claim_text: "Sunscreen đã có BPOM.",
    timestamp: 333,
    speaker: "Mai",
    created_at: createdAt,
  },
  {
    id: "demo-claim-size",
    video_id: DEMO_VIDEO_ID,
    video_window_id: "demo-window-006",
    claim_text: "Chai sunscreen là bản 500ml.",
    timestamp: 448,
    speaker: "Mai",
    created_at: createdAt,
  },
]

export const demoClaimVerifications: Record<string, ClaimVerificationResponse> = {
  "demo-claim-price-199": {
    claim_id: "demo-claim-price-199",
    claim_text: "Serum C30 đang giảm còn 199K.",
    timestamp: 88,
    verdict: "consistent",
    confidence: 0.94,
    explanation: "Transcript says the serum is 199K and OCR in the same window also reads 199K.",
    evidence: [
      {
        timestamp: 88,
        thumbnail_url: frames.serumPrice,
        transcript: demoTimeline[1].transcript,
        visual_description: demoTimeline[1].scene_description,
        rationale: "Speech and on-screen price agree.",
        source: "transcript + OCR + frame",
      },
    ],
  },
  "demo-claim-authentic": {
    claim_id: "demo-claim-authentic",
    claim_text: "Serum C30 là hàng chính hãng 100%.",
    timestamp: 145,
    verdict: "unclear",
    confidence: 0.61,
    explanation: "The claim is spoken clearly, but the visible frame does not show a certificate, invoice, QR verification page, or seal.",
    evidence: [
      {
        timestamp: 145,
        thumbnail_url: frames.authenticClaim,
        transcript: demoTimeline[2].transcript,
        visual_description: demoTimeline[2].scene_description,
        rationale: "Visual evidence is not strong enough to verify authenticity.",
        source: "transcript + frame",
      },
    ],
  },
  "demo-claim-qr-seal": {
    claim_id: "demo-claim-qr-seal",
    claim_text: "Mặt sau hộp có tem chống giả và mã QR.",
    timestamp: 226,
    verdict: "consistent",
    confidence: 0.88,
    explanation: "The host asks viewers to look at the back of the box, and the evidence frame shows QR/check text plus an anti-fake label area.",
    evidence: [
      {
        timestamp: 226,
        thumbnail_url: frames.qrSeal,
        transcript: demoTimeline[3].transcript,
        visual_description: demoTimeline[3].scene_description,
        rationale: "Speech, OCR, and visible packaging features support the claim.",
        source: "transcript + OCR + frame",
      },
    ],
  },
  "demo-claim-bpom": {
    claim_id: "demo-claim-bpom",
    claim_text: "Sunscreen đã có BPOM.",
    timestamp: 333,
    verdict: "unclear",
    confidence: 0.57,
    explanation: "The model detects partial BPOM text, but the registration line is blocked and cannot be read fully.",
    evidence: [
      {
        timestamp: 333,
        thumbnail_url: frames.bpom,
        transcript: demoTimeline[4].transcript,
        visual_description: demoTimeline[4].scene_description,
        rationale: "OCR is partial, so the evidence is insufficient.",
        source: "transcript + partial OCR + frame",
      },
    ],
  },
  "demo-claim-size": {
    claim_id: "demo-claim-size",
    claim_text: "Chai sunscreen là bản 500ml.",
    timestamp: 448,
    verdict: "inconsistent",
    confidence: 0.9,
    explanation: "The transcript says 500ml, but OCR on the bottle reads 250ml in the evidence frame.",
    evidence: [
      {
        timestamp: 448,
        thumbnail_url: frames.mismatch,
        transcript: demoTimeline[5].transcript,
        visual_description: demoTimeline[5].scene_description,
        rationale: "Speech and packaging OCR disagree.",
        source: "transcript + OCR + frame",
      },
    ],
  },
}

export const demoSampleQuestions = [
  "Người dẫn demo Serum C30 lúc nào?",
  "Lúc nói giá 199K có thấy giá trên màn hình không?",
  "Host nói hàng chính hãng có hình ảnh chứng minh không?",
  "Tìm mọi khoảnh khắc có FREE SHIP trong khi đang giới thiệu sản phẩm.",
  "SKU SUN-BPOM-50 được nhắc bằng tiếng Indonesia lúc nào?",
  "Có chỗ nào lời nói không khớp với hình ảnh không?",
  "Sản phẩm nào xuất hiện trong combo cuối livestream?",
  "Đoạn nào có đỉnh năng lượng của host?",
  "Claim BPOM có đủ bằng chứng hình ảnh không?",
  "Tóm tắt các bằng chứng đa phương thức cho Serum C30.",
]

export const demoQuestions: QuestionResponse[] = [
  createDemoQuestion("Người dẫn demo Serum C30 lúc nào?", "demo-question-001"),
  createDemoQuestion("Có chỗ nào lời nói không khớp với hình ảnh không?", "demo-question-002"),
  createDemoQuestion("Host nói hàng chính hãng có hình ảnh chứng minh không?", "demo-question-003"),
]

export const demoVideoMetrics: VideoMetricsResponse = {
  video_id: DEMO_VIDEO_ID,
  window_count: demoTimeline.length,
  claim_count: demoClaims.length,
  question_count: demoQuestions.length,
  estimated_cost: 0.0842,
  model_call_count: 28,
  failed_model_call_count: 0,
  average_model_latency_ms: 1160,
}

export const demoMetricsOverview: MetricsOverviewResponse = {
  videos_total: 1,
  videos_indexed: 1,
  jobs_processing: 0,
  questions_total: demoQuestions.length,
  estimated_cost_total: demoVideoMetrics.estimated_cost,
  average_latency_ms: 1240,
  model_calls_total: demoVideoMetrics.model_call_count,
  model_calls_failed: demoVideoMetrics.failed_model_call_count,
  average_model_latency_ms: demoVideoMetrics.average_model_latency_ms,
}

export function createDemoQuestion(question: string, id = `demo-question-${Date.now()}`): QuestionResponse {
  const normalized = question.toLowerCase()

  if (includesAny(normalized, ["không khớp", "khong khop", "mismatch", "sai"])) {
    return makeQuestion(id, question, "Có một điểm không khớp rõ: host nói chai sunscreen là bản 500ml, nhưng OCR trên nhãn trong frame evidence đọc được 250ml.", 1370, 0.0068, [
      qaEvidence("demo-window-006", 448, frames.mismatch, "Transcript says 500ml while OCR on packaging reads 250ml."),
    ])
  }

  if (includesAny(normalized, ["chính hãng", "chinh hang", "authentic"])) {
    return makeQuestion(id, question, "Host có nói Serum C30 là hàng chính hãng 100%, nhưng frame gần thời điểm đó chưa đủ bằng chứng hình ảnh để xác minh claim.", 1190, 0.0059, [
      qaEvidence("demo-window-003", 145, frames.authenticClaim, "Claim is spoken, but no certificate, QR verification page, invoice, or clear seal is visible."),
    ])
  }

  if (includesAny(normalized, ["199k", "giá", "gia", "price"])) {
    return makeQuestion(id, question, "Giá 199K được nói ở 00:01:28 và được OCR trên màn hình xác nhận trong cùng window.", 1045, 0.0052, [
      qaEvidence("demo-window-002", 88, frames.serumPrice, "Transcript mentions 199K and OCR also reads 199K."),
    ])
  }

  if (includesAny(normalized, ["free ship", "freeship", "miễn phí", "mien phi"])) {
    return makeQuestion(id, question, "FREE SHIP xuất hiện ở phần mở đầu, đoạn giới thiệu Serum C30, và combo cuối livestream.", 1260, 0.0061, [
      qaEvidence("demo-window-001", 18, frames.opening, "Opening banner shows FREE SHIP during the livestream intro."),
      qaEvidence("demo-window-002", 88, frames.serumPrice, "Price window includes both 199K and FREE SHIP OCR."),
      qaEvidence("demo-window-007", 556, frames.closing, "Combo segment includes FREE SHIP and gift badges."),
    ])
  }

  if (includesAny(normalized, ["bpom", "indonesia", "indonesian", "sun-bpom"])) {
    return makeQuestion(id, question, "SKU SUN-BPOM-50 được nhắc ở 00:05:30 bằng tiếng Indonesia, nhưng claim BPOM chỉ có OCR một phần nên chưa đủ chắc.", 1315, 0.0064, [
      qaEvidence("demo-window-005", 333, frames.bpom, "Indonesian speech mentions BPOM, while OCR only partially shows the BPOM registration line."),
    ])
  }

  if (includesAny(normalized, ["combo", "cuối", "cuoi"])) {
    return makeQuestion(id, question, "Combo cuối livestream gồm Serum C30 và sunscreen, kèm FREE SHIP và quà tặng bông tẩy trang.", 980, 0.0048, [
      qaEvidence("demo-window-007", 556, frames.closing, "Two products are visible side by side with combo, free shipping, and gift OCR."),
    ])
  }

  return makeQuestion(id, question, "Điểm liên quan nhất nằm ở đoạn Serum C30: lời thoại, OCR giá 199K, và frame sản phẩm cùng xuất hiện trong một window.", 1110, 0.0054, [
    qaEvidence("demo-window-002", 88, frames.serumPrice, "This window combines spoken product mention, visible product, and OCR price."),
  ])
}

export function getDemoManualVerification(claimText: string, timestamp?: number): ClaimVerificationResponse {
  const normalized = claimText.toLowerCase()
  if (includesAny(normalized, ["500ml", "năm trăm", "nam tram"])) {
    return { ...demoClaimVerifications["demo-claim-size"], claim_text: claimText, timestamp: timestamp ?? 448 }
  }
  if (includesAny(normalized, ["bpom"])) {
    return { ...demoClaimVerifications["demo-claim-bpom"], claim_text: claimText, timestamp: timestamp ?? 333 }
  }
  if (includesAny(normalized, ["chính hãng", "chinh hang", "authentic"])) {
    return { ...demoClaimVerifications["demo-claim-authentic"], claim_text: claimText, timestamp: timestamp ?? 145 }
  }
  if (includesAny(normalized, ["199k", "giá", "gia"])) {
    return { ...demoClaimVerifications["demo-claim-price-199"], claim_text: claimText, timestamp: timestamp ?? 88 }
  }
  return {
    ...demoClaimVerifications["demo-claim-qr-seal"],
    claim_text: claimText || "Mặt sau hộp có tem chống giả và mã QR.",
    timestamp: timestamp ?? 226,
  }
}

function makeQuestion(
  id: string,
  question: string,
  answer: string,
  latencyMs: number,
  estimatedCost: number,
  evidence: QuestionEvidenceResponse[]
): QuestionResponse {
  return {
    id,
    video_id: DEMO_VIDEO_ID,
    question,
    answer,
    latency_ms: latencyMs,
    estimated_cost: estimatedCost,
    created_at: createdAt,
    evidence,
  }
}

function qaEvidence(
  windowId: string,
  timestamp: number,
  thumbnailUrl: string,
  rationale: string
): QuestionEvidenceResponse {
  const window = demoTimeline.find((item) => item.id === windowId) ?? demoTimeline[0]
  return {
    timestamp,
    start_time: window.start_time,
    end_time: window.end_time,
    thumbnail_url: thumbnailUrl,
    transcript: window.transcript,
    visual_description: window.scene_description,
    rationale,
  }
}

function includesAny(text: string, needles: string[]) {
  return needles.some((needle) => text.includes(needle))
}
