import { redirect } from "next/navigation"

export default function NewUiTelemetryRedirectPage() {
  redirect("/new-ui/workspace?tab=metrics")
}
