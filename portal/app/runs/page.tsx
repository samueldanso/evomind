import { RunHistory } from "@/components/run-history";

export default function RunsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">Run History</h1>
          <p className="mt-1 text-muted-foreground">Agent runs — research and teaching</p>
        </header>
        <RunHistory />
      </div>
    </div>
  );
}
