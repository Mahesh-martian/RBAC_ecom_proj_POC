// Streaming client for the RAG service Server-Sent Events (SSE) chat endpoint.
//
// The storefront chatbot calls the RAG service directly at /chat/query/stream
// (the service enables CORS for the storefront origin) and renders tokens as they
// arrive for a live "typing" effect. Falls back gracefully: callers should catch
// errors and show a friendly message.

export interface StreamDoneMeta {
  response_type?: string;
  provider?: string;
  confidence?: number | null;
  conversation_id?: string | null;
  citations?: string[];
  recommendations?: Array<Record<string, unknown>>;
}

export interface StreamChatHandlers {
  onToken: (chunk: string) => void;
  onDone?: (meta: StreamDoneMeta) => void;
  onError?: (error: unknown) => void;
}

// Recent turns sent to the backend so it has lightweight conversational memory.
export interface StreamChatHistoryItem {
  role: "user" | "bot";
  text: string;
}

export interface StreamChatPayload {
  query: string;
  // Logged-in user's name so the assistant can address them personally.
  user_name?: string | null;
  // Caller's role (customer | vendor | admin). The RAG service treats the
  // verified JWT as authoritative; this is a best-effort hint / dev fallback.
  user_role?: string | null;
  // Stable conversation id correlating turns across requests.
  conversation_id?: string | null;
  // Prior messages (most recent last) for short-term context.
  history?: StreamChatHistoryItem[];
}

// Base URL of the RAG service. Configurable for deploys; defaults to local compose.
const RAG_BASE_URL =
  process.env.NEXT_PUBLIC_RAG_URL?.replace(/\/$/, "") || "http://localhost:8000";

/**
 * Stream a chat answer over SSE. Resolves once the stream completes (done/error).
 *
 * `accessToken` (the storefront JWT) is forwarded as a Bearer token so the RAG
 * service can verify the caller's role for RBAC-scoped policy retrieval.
 */
export async function streamChat(
  payload: StreamChatPayload,
  handlers: StreamChatHandlers,
  signal?: AbortSignal,
  accessToken?: string | null,
): Promise<void> {
  const { onToken, onDone, onError } = handlers;

  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (accessToken) {
      // Strip any surrounding quotes that may be present in a stored token.
      const cleanToken = accessToken.replace(/^"|"$/g, "").trim();
      if (cleanToken) {
        headers.Authorization = `Bearer ${cleanToken}`;
      }
    }

    const response = await fetch(`${RAG_BASE_URL}/chat/query/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream request failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    // SSE frames are separated by a blank line ("\n\n"); a frame may span reads,
    // so we buffer and only consume complete frames.
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let separatorIndex: number;
      while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, separatorIndex);
        buffer = buffer.slice(separatorIndex + 2);

        const dataLine = frame
          .split("\n")
          .find((line) => line.startsWith("data:"));
        if (!dataLine) continue;

        const json = dataLine.slice("data:".length).trim();
        if (!json) continue;

        let event: { type?: string; content?: string } & StreamDoneMeta;
        try {
          event = JSON.parse(json);
        } catch {
          continue; // skip malformed frame
        }

        if (event.type === "token" && event.content) {
          onToken(event.content);
        } else if (event.type === "done") {
          onDone?.(event);
        } else if (event.type === "error") {
          throw new Error("stream interrupted");
        }
      }
    }
  } catch (error) {
    onError?.(error);
  }
}
