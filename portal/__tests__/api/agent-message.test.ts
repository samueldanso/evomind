import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

const mockFetch = vi.fn();
const originalFetch = globalThis.fetch;
globalThis.fetch = mockFetch as unknown as typeof fetch;

import { POST } from "@/app/api/agent/[run_id]/message/route";

function makeRequest(runId: string, body: Record<string, unknown>): [NextRequest, { params: Promise<{ run_id: string }> }] {
	const req = new NextRequest(`http://localhost/api/agent/${runId}/message`, {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify(body),
	});
	return [req, { params: Promise.resolve({ run_id: runId }) }];
}

describe("POST /api/agent/[run_id]/message", () => {
	afterEach(() => {
		vi.clearAllMocks();
	});

	it("proxies message to FastAPI server", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({
				reply: "Teaching response",
				status: "teaching",
				session_log_length: 3,
			}),
		});

		const [req, ctx] = makeRequest("42", { content: "My answer" });
		const res = await POST(req, ctx);
		const data = await res.json();

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining("/api/agent/42/message"),
			expect.objectContaining({ method: "POST" }),
		);
		expect(res.status).toBe(200);
		expect(data.reply).toBe("Teaching response");
		expect(data.status).toBe("teaching");
	});

	it("forwards error status from server", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 409,
			json: async () => ({
				error: "Run not in paused state",
			}),
		});

		const [req, ctx] = makeRequest("42", { content: "test" });
		const res = await POST(req, ctx);

		expect(res.status).toBe(409);
	});

	it("forwards complete status", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({
				reply: "Final checklist",
				status: "complete",
				session_log_length: 10,
			}),
		});

		const [req, ctx] = makeRequest("42", { content: "Final answer" });
		const res = await POST(req, ctx);
		const data = await res.json();

		expect(data.status).toBe("complete");
		expect(data.session_log_length).toBe(10);
	});
});
