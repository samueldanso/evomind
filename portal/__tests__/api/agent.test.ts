import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

const mockFetch = vi.fn();
const originalFetch = globalThis.fetch;
globalThis.fetch = mockFetch as unknown as typeof fetch;

import { POST, GET } from "@/app/api/agent/route";

function makePostRequest(body: Record<string, unknown>): NextRequest {
	return new NextRequest("http://localhost/api/agent", {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify(body),
	});
}

function makeGetRequest(limit?: string): NextRequest {
	const url = limit
		? `http://localhost/api/agent?limit=${limit}`
		: "http://localhost/api/agent";
	return new NextRequest(url);
}

describe("POST /api/agent", () => {
	afterEach(() => {
		vi.clearAllMocks();
	});

	it("proxies research dispatch to FastAPI server", async () => {
		const mockResponse = {
			run: { id: 1, status: "complete", agent_type: "research_agent" },
			teach_run: null,
		};
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => mockResponse,
		});

		const req = makePostRequest({
			task_type: "research",
			topic: "KV Cache",
			mode: "concept",
		});
		const res = await POST(req);
		const data = await res.json();

		expect(mockFetch).toHaveBeenCalledOnce();
		expect(res.status).toBe(200);
		expect(data.run.id).toBe(1);
		expect(data.teach_run).toBeNull();
	});

	it("forwards error status from server", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 422,
			json: async () => ({ error: "topic is required" }),
		});

		const req = makePostRequest({ task_type: "research" });
		const res = await POST(req);

		expect(res.status).toBe(422);
	});
});

describe("GET /api/agent (runs list)", () => {
	afterEach(() => {
		vi.clearAllMocks();
	});

	it("proxies runs list request with limit", async () => {
		const mockResponse = { runs: [{ id: 1 }, { id: 2 }] };
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => mockResponse,
		});

		const req = makeGetRequest("5");
		const res = await GET(req);
		const data = await res.json();

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining("/api/agent/runs?limit=5"),
		);
		expect(res.status).toBe(200);
		expect(data.runs).toHaveLength(2);
	});

	it("defaults limit to 20 when not provided", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({ runs: [] }),
		});

		const req = makeGetRequest();
		await GET(req);

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining("limit=20"),
		);
	});
});
