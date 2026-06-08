import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

const mockFetch = vi.fn();
const originalFetch = globalThis.fetch;
globalThis.fetch = mockFetch as unknown as typeof fetch;

describe("TeachSession API interactions", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it("sendMessage calls correct endpoint with content", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({
				reply: "Next question",
				status: "teaching",
				session_log_length: 3,
			}),
		});

		const { sendMessage } = await import("@/lib/agent-client");
		const result = await sendMessage(42, "My answer");

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining("/api/agent/42/message"),
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({ content: "My answer" }),
			}),
		);
		expect(result.reply).toBe("Next question");
		expect(result.status).toBe("teaching");
		expect(result.session_log_length).toBe(3);
	});

	it("sendMessage handles complete status", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({
				reply: "Checklist content",
				status: "complete",
				session_log_length: 10,
			}),
		});

		const { sendMessage } = await import("@/lib/agent-client");
		const result = await sendMessage(42, "Final answer");

		expect(result.status).toBe("complete");
	});

	it("sendMessage throws on error response", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 409,
			json: async () => ({
				error: "Run status is 'running', expected 'paused_awaiting_input'",
			}),
		});

		const { sendMessage } = await import("@/lib/agent-client");
		await expect(sendMessage(42, "test")).rejects.toThrow("paused_awaiting_input");
	});

	it("getAgentRun fetches run with session_log", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			status: 200,
			json: async () => ({
				run: {
					id: 42,
					status: "paused_awaiting_input",
					session_log: [{ role: "assistant", content: "Hi" }],
				},
			}),
		});

		const { getAgentRun } = await import("@/lib/agent-client");
		const result = await getAgentRun(42);

		expect(result.run.status).toBe("paused_awaiting_input");
		expect(result.run.session_log).toHaveLength(1);
	});
});
