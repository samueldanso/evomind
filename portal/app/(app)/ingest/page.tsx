import { redirect } from "next/navigation";

// Add Source is now a dialog accessible from the sidebar.
// Redirect legacy /ingest URL to the wiki.
export default function IngestPage() {
  redirect("/wiki");
}
