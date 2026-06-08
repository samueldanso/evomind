import type { NextRequest } from "next/server";

const SERVER = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export async function POST(request: NextRequest) {
	const body = await request.json();
	const res = await fetch(`${SERVER}/api/agent`, {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify(body),
	});
	const data = await res.json();
	return Response.json(data, { status: res.status });
}

export async function GET(request: NextRequest) {
	const limit = request.nextUrl.searchParams.get("limit") ?? "20";
	const res = await fetch(`${SERVER}/api/agent/runs?limit=${limit}`);
	const data = await res.json();
	return Response.json(data, { status: res.status });
}
