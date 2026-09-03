import { type NextRequest, NextResponse } from "next/server";

const SERVER_URL = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q") ?? "";

  try {
    const res = await fetch(`${SERVER_URL}/api/search?q=${encodeURIComponent(q)}`, {
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      const error = await res.text().catch(() => "Backend error");
      return NextResponse.json({ error }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 502 });
  }
}
