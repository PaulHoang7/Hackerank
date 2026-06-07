import { redirect } from "next/navigation"

export default function NewUiComplianceRedirectPage() {
  redirect("/new-ui/workspace?tab=claims")
}
