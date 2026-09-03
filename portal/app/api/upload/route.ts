import { NextRequest, NextResponse } from "next/server";

const SERVER_URL = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export async function POST(request: NextRequest) {
  const formData = await request.formData();

  const res = await fetch(`${SERVER_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.text().catch(() => "Upload server error");
    return NextResponse.json({ error }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
