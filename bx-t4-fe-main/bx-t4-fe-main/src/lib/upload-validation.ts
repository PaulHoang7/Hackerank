const allowedExtensions = [".mp4", ".mov", ".webm"]

export const MAX_UPLOAD_SIZE_BYTES =
  Number.parseInt(process.env.NEXT_PUBLIC_MAX_UPLOAD_SIZE_BYTES ?? "", 10) || 1024 * 1024 * 1024

function formatUploadLimit(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) return `${Math.round(bytes / 1024 / 1024 / 1024)} GB`
  return `${Math.round(bytes / 1024 / 1024)} MB`
}

export function validateVideoFile(file: File): string | null {
  const lowerName = file.name.toLowerCase()
  const hasAllowedExtension = allowedExtensions.some((extension) => lowerName.endsWith(extension))

  if (!hasAllowedExtension) {
    return "Only MP4, MOV or WebM files are supported."
  }

  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return `File exceeds ${formatUploadLimit(MAX_UPLOAD_SIZE_BYTES)}.`
  }

  return null
}
