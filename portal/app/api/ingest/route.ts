import { NextRequest, NextResponse } from "next/server";

const SERVER_URL = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export async function POST(request: NextRequest) {
  const body = await request.json();

  const res = await fetch(`${SERVER_URL}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.text().catch(() => "Ingest server error");
    return NextResponse.json({ error }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
