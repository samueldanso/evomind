export type AgentRequest = {
	task_type: "research" | "teach";
	topic: string;
	mode?: "concept" | "tool" | "company";
	context?: string;
	artifact_slug?: string;
	mastery_context?: string;
	auto_teach?: boolean;
};

export type AgentRunData = {
	id: number;
	agent_type: string;
	status: "running" | "complete" | "failed";
	output: Record<string, unknown> | null;
	error: string | null;
	cost_tokens: number;
	cost_usd: number;
	started_at: string;
	finished_at: string | null;
	tool_calls: unknown[];
};

export type AgentResponse = {
	run: AgentRunData;
	teach_run: AgentRunData | null;
};

export type AgentRunResponse = {
	run: AgentRunData;
};

export type MessageResponse = {
	reply: string;
	status: "teaching" | "complete" | "failed";
};

export type RunsResponse = {
	runs: AgentRunData[];
};

export async function dispatchAgent(body: AgentRequest): Promise<AgentResponse> {
	const res = await fetch("/api/agent", {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify(body),
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.error ?? `Dispatch failed: ${res.status}`);
	}
	return res.json();
}

export async function getAgentRun(runId: number): Promise<AgentRunResponse> {
	const res = await fetch(`/api/agent/${runId}`);
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.error ?? `Fetch run failed: ${res.status}`);
	}
	return res.json();
}

export async function sendMessage(
	runId: number,
	content: string,
): Promise<MessageResponse> {
	const res = await fetch(`/api/agent/${runId}/message`, {
		method: "POST",
		headers: { "content-type": "application/json" },
		body: JSON.stringify({ content }),
	});
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.error ?? `Message failed: ${res.status}`);
	}
	return res.json();
}

export async function listRuns(limit = 20): Promise<RunsResponse> {
	const res = await fetch(`/api/agent?limit=${limit}`);
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.error ?? `List runs failed: ${res.status}`);
	}
	return res.json();
}
