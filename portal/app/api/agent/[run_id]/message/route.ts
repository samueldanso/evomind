import type { NextRequest } from "next/server";

const SERVER = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export async function POST(
	request: NextRequest,
	{ params }: { params: Promise<{ run_id: string }> },
) {
	const { run_id } = await params;
	const body = await request.json();
	const res = await fetch(`${SERVER}/api/agent/${run_id}/message`, {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify(body),
	});
	const data = await res.json();
	return Response.json(data, { status: res.status });
}
