export interface ChatRequest {
  query: string;
  limit?: number;
}

export interface ChatSource {
  slug: string;
  title: string;
  excerpt: string;
  score: number;
  match_type: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

const CHAT_SERVER_URL = "http://localhost:8765/chat";

export async function chat(query: string, limit = 5): Promise<ChatResponse> {
  const res = await fetch(CHAT_SERVER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error ?? `Chat request failed with status ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}
