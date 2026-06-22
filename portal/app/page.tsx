import { Suspense } from "react";
import { AgentForm } from "@/components/agent-form";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Evo</h1>
          <p className="mt-1 text-muted-foreground">
            Research a topic. Get taught. Build your corpus.
          </p>
        </header>
        <Suspense>
          <AgentForm />
        </Suspense>
      </div>
    </div>
  );
}
