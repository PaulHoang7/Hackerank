export type DisplayLanguage = "vi" | "en"

export const displayLanguageTabs: Array<{ value: DisplayLanguage; label: string }> = [
  { value: "vi", label: "Tiếng Việt" },
  { value: "en", label: "English" },
]

export function textForLanguage(sourceText: string | null | undefined, translation: string | null | undefined, language: DisplayLanguage) {
  const source = sourceText?.trim() ?? ""
  const translated = translation?.trim() ?? ""
  if (language === "en" && translated) return translated
  return source
}
