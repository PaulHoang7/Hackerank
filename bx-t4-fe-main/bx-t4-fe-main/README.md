# BX-T4 Video Intelligence Frontend

Next.js App Router frontend for the BX-T4 FastAPI backend at `http://localhost:8000/api/v1`.

## Architecture

- `src/app`: dashboard, video list, upload, and video workspace routes.
- `src/lib/api`: typed fetch client and endpoint modules mapped to the current FastAPI OpenAPI schema.
- `src/features`: TanStack Query hooks for videos, jobs, questions, claims, and metrics.
- `src/components`: layout, UI primitives, video player, timeline, transcript, Q&A, claims, products, and metrics.
- `src/hooks/use-video-time.tsx`: shared seek context for timestamp-driven video navigation.

## Run

```bash
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:3000`.

On Windows PowerShell, use `npm.cmd` if `npm.ps1` is blocked:

```powershell
npm.cmd run dev
```

## Environment

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8000
NEXT_PUBLIC_MAX_UPLOAD_SIZE_BYTES=1073741824
```

Components do not hardcode backend URLs. `buildMediaUrl` converts `/storage/...` into the backend origin. Keep `NEXT_PUBLIC_MAX_UPLOAD_SIZE_BYTES` aligned with backend `MAX_UPLOAD_SIZE_BYTES`.

## Integrated Backend Endpoints

- `GET /metrics/overview`
- `POST /videos/upload`
- `GET /videos`
- `GET /videos/{video_id}`
- `DELETE /videos/{video_id}`
- `GET /videos/{video_id}/timeline`
- `GET /videos/{video_id}/transcript`
- `GET /videos/{video_id}/products`
- `GET /videos/{video_id}/claims`
- `GET /videos/{video_id}/metrics`
- `GET /jobs/{job_id}`
- `POST /videos/{video_id}/questions`
- `GET /videos/{video_id}/questions`
- `POST /videos/{video_id}/claims/{claim_id}/verify`

## Main Flows

- Dashboard: overview metrics, throughput preview, and recent videos.
- Video list: status, duration, languages, upload date, workspace link, and delete confirmation.
- Upload: drag/drop, extension and size validation, XHR upload progress, then job polling every 2 seconds.
- Workspace: video player, Q&A evidence, indexed timeline, transcript search, products, claims, and video metrics.
- Seek: timeline rows, transcript timestamps, Q&A evidence, claim timestamps, and product occurrences call the shared `seekTo(timestamp)`.

## Product Occurrences

The Products tab now renders backend product occurrences when available:

- occurrence type
- timestamp
- confidence
- jump-to-timestamp button

If a product has no occurrences, the UI shows an explicit empty occurrence message.

## Checks

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

## Docker

```bash
docker build -t bx-t4-video-intelligence-fe .
docker run --env-file .env -p 3000:3000 bx-t4-video-intelligence-fe
```

## Remaining Backend Gaps Reflected In UI

- Backend still defaults to mock intelligence unless Seed Omni is implemented and configured.
- Video metrics are still basic: processing duration, model/API calls, failed windows, and throughput per video are not fully exposed yet.
- Claim verify response still returns raw evidence objects and needs richer thumbnail/frame URLs.
- Backend verdict enum is `consistent | inconsistent | unclear`; FE maps `unclear` to insufficient-evidence styling.
