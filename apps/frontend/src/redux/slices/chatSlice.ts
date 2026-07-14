import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { logout } from "./authSlice";

export interface ChatRecommendation {
  id: string;
  name: string;
  sku?: string | null;
  price: number;
  currency: string;
  image_url?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
  // Product recommendations attached to a bot message (rendered as cards).
  recommendations?: ChatRecommendation[];
}

interface ChatState {
  conversations: ChatMessage[];
  // Stable id for the current conversation so the backend can correlate turns.
  conversationId: string | null;
}

const STORAGE_KEY = "chat";

// Load persisted chat so the conversation survives a page refresh.
const loadChatFromLocalStorage = (): ChatState => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as Partial<ChatState>;
        return {
          conversations: parsed.conversations ?? [],
          conversationId: parsed.conversationId ?? null,
        };
      } catch {
        // Ignore corrupt storage and start fresh.
      }
    }
  }
  return { conversations: [], conversationId: null };
};

const saveChatToLocalStorage = (state: ChatState) => {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }
};

const initialState: ChatState = loadChatFromLocalStorage();

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addMessage(state, action: PayloadAction<ChatMessage>) {
      // Add a new message to the conversation array
      state.conversations.push(action.payload);
      if (!state.conversationId) {
        state.conversationId = `conv-${Date.now()}-${Math.random()
          .toString(36)
          .slice(2, 8)}`;
      }
      saveChatToLocalStorage(state);
    },
    appendToMessage(
      state,
      action: PayloadAction<{ id: string; chunk: string }>,
    ) {
      // Append a streamed token to an existing message (live typing effect).
      const message = state.conversations.find(
        (m) => m.id === action.payload.id,
      );
      if (message) {
        message.text += action.payload.chunk;
        saveChatToLocalStorage(state);
      }
    },
    setRecommendations(
      state,
      action: PayloadAction<{ id: string; recommendations: ChatRecommendation[] }>,
    ) {
      // Attach product recommendations to a bot message once streaming completes.
      const message = state.conversations.find(
        (m) => m.id === action.payload.id,
      );
      if (message) {
        message.recommendations = action.payload.recommendations;
        saveChatToLocalStorage(state);
      }
    },
    clearConversations(state) {
      // Clear all chat conversations
      state.conversations = [];
      state.conversationId = null;
      saveChatToLocalStorage(state);
    },
  },
  extraReducers: (builder) => {
    // Wipe the conversation (and the personalized greeting/name) on logout so a
    // signed-out user never sees the previous account's chat history.
    builder.addCase(logout, (state) => {
      state.conversations = [];
      state.conversationId = null;
      if (typeof window !== "undefined") {
        localStorage.removeItem(STORAGE_KEY);
      }
    });
  },
});

export const {
  addMessage,
  appendToMessage,
  setRecommendations,
  clearConversations,
} = chatSlice.actions;
export default chatSlice.reducer;
