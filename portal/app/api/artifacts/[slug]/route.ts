import { type NextRequest, NextResponse } from "next/server";

const SERVER_URL = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export const dynamic = "force-dynamic";

export async function GET(_req: NextRequest, ctx: { params: Promise<{ slug: string }> }) {
  const { slug } = await ctx.params;

  try {
    const res = await fetch(`${SERVER_URL}/api/artifacts/${slug}`, {
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

export async function DELETE(_req: NextRequest, ctx: { params: Promise<{ slug: string }> }) {
  const { slug } = await ctx.params;

  try {
    const res = await fetch(`${SERVER_URL}/api/artifacts/${slug}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      const error = await res.text().catch(() => "Backend error");
      return NextResponse.json({ error }, { status: res.status });
    }

    return new NextResponse(null, { status: 204 });
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 502 });
  }
}
