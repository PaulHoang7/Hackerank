import type { WorkspaceTab } from "@/lib/new-ui/data"
import { workspaceTabs } from "@/lib/new-ui/data"
import { WorkspaceClient } from "@/components/new-ui/workspace-client"

export default function NewUiWorkspacePage({ searchParams }: { searchParams: { tab?: string } }) {
  const requestedTab = searchParams.tab
  const initialTab = workspaceTabs.some((tab) => tab.value === requestedTab) ? (requestedTab as WorkspaceTab) : "qa"

  return <WorkspaceClient initialTab={initialTab} />
}
