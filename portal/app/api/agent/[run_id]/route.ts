import type { NextRequest } from "next/server";

const SERVER = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export async function GET(
	_request: NextRequest,
	{ params }: { params: Promise<{ run_id: string }> },
) {
	const { run_id } = await params;
	const res = await fetch(`${SERVER}/api/agent/${run_id}`);
	const data = await res.json();
	return Response.json(data, { status: res.status });
}
