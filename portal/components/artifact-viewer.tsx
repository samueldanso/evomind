"use client";

export function ArtifactViewer({ html }: { html: string }) {
  // Inject a style tag to force light background inside the iframe
  // (research artifacts are generated with white backgrounds)
  const styledHtml = `
    <style>
      html, body { background: #fff !important; color: #111 !important; }
    </style>
    ${html}
  `;

  return (
    <iframe
      srcDoc={styledHtml}
      sandbox="allow-scripts"
      className="w-full rounded-xl"
      style={{
        height: "80vh",
        minHeight: "600px",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
      title="Artifact content"
    />
  );
}
