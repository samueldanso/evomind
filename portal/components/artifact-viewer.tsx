"use client";

export function ArtifactViewer({ html }: { html: string }) {
  return (
    <iframe
      srcDoc={html}
      sandbox="allow-scripts allow-same-origin"
      className="w-full rounded-lg border-0"
      style={{ height: "100vh", minHeight: "800px" }}
      title="Artifact content"
    />
  );
}
