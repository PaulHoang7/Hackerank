import { redirect } from "next/navigation"

export default function NewUiTimelineRedirectPage() {
  redirect("/new-ui/workspace?tab=timeline")
}
