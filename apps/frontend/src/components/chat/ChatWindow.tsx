"use client";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDispatch, useSelector } from "react-redux";
import {
  addMessage,
  appendToMessage,
  ChatMessage,
  ChatRecommendation,
  clearConversations,
  setRecommendations,
} from "@/redux/slices/chatSlice";
import { streamChat } from "@/redux/api/streamChat";
import { RootState } from "@/redux/store";
import { useState } from "react";
import Link from "next/link";
import { MessageCircle, Send, Trash2 } from "lucide-react";

const ChatWindow = () => {
  const dispatch = useDispatch();
  const conversations = useSelector(
    (state: RootState) => state.chat.conversations,
  );
  const conversationId = useSelector(
    (state: RootState) => state.chat.conversationId,
  );
  const userName = useSelector(
    (state: RootState) => state.auth.user?.name ?? null,
  );
  const userRole = useSelector(
    (state: RootState) => state.auth.user?.role ?? null,
  );

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false); // Track if chat is open

  // Request a higher-resolution image from the Flipkart CDN, which encodes the
  // thumbnail size directly in the URL path (e.g. /image/128/128/ -> /image/416/416/).
  const hiResImage = (url?: string | null): string => {
    if (!url) return "/placeholder-product.svg";
    return url.replace(/\/image\/\d+\/\d+\//, "/image/416/416/");
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      text: input,
    };
    dispatch(addMessage(userMessage));

    const query = input;
    setInput(""); // Clear input field immediately

    // Snapshot recent turns (skip the welcome + any empty placeholder) so the
    // backend has short-term conversational context.
    const history = conversations
      .filter((m) => m.text && m.id !== "welcome-message")
      .slice(-6)
      .map((m) => ({ role: m.role, text: m.text }));

    // Create an empty bot message that we fill in as tokens stream in.
    const botMessageId = `${Date.now()}-bot`;
    dispatch(addMessage({ id: botMessageId, role: "bot", text: "" }));

    setIsLoading(true);
    let received = false;

    // Forward the storefront JWT so the RAG service can verify the caller's role
    // for RBAC-scoped policy retrieval (token is authoritative server-side).
    const accessToken =
      typeof window !== "undefined"
        ? localStorage.getItem("accessToken")
        : null;

    await streamChat(
      {
        query,
        user_name: userName,
        user_role: userRole,
        conversation_id: conversationId,
        history,
      },
      {
      onToken: (chunk) => {
        received = true;
        dispatch(appendToMessage({ id: botMessageId, chunk }));
      },
      onDone: (meta) => {
        const recs = (meta.recommendations ??
          []) as unknown as ChatRecommendation[];
        if (recs.length) {
          dispatch(
            setRecommendations({ id: botMessageId, recommendations: recs }),
          );
        }
      },
      onError: (error) => {
        console.error("Error streaming message:", error);
        if (!received) {
          dispatch(
            appendToMessage({
              id: botMessageId,
              chunk: "Sorry, I couldn't reach the assistant. Please try again.",
            }),
          );
        }
      },
      },
      undefined,
      accessToken,
    );

    setIsLoading(false);
  };

  const handlePopoverOpen = () => {
    setIsChatOpen(true);
    // Only greet on a fresh conversation; a persisted chat (restored after a
    // refresh) keeps its existing history.
    if (conversations.length === 0) {
      const firstName = userName ? ` ${userName.split(" ")[0]}` : "";
      const welcomeMessage: ChatMessage = {
        id: "welcome-message",
        role: "bot",
        text: `Hi there${firstName}! How can I help you today?`,
      };
      dispatch(addMessage(welcomeMessage));
    }
  };

  const handlePopoverClose = () => {
    setIsChatOpen(false);
  };

  return (
    <div className="fixed bottom-2 lg:bottom-4 right-16">
      <Popover
        onOpenChange={(isOpen) =>
          isOpen ? handlePopoverOpen() : handlePopoverClose()
        }
      >
        <PopoverTrigger className="p-3 rounded-full bg-primary text-primary-foreground shadow-lg cursor-pointer">
          <MessageCircle className="w-6 h-6" />
        </PopoverTrigger>
        <PopoverContent className="w-80 p-4 shadow-lg rounded-lg bg-card text-card-foreground">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">
              Shopping Assistant
            </span>
            <button
              type="button"
              onClick={() => dispatch(clearConversations())}
              disabled={isLoading || conversations.length === 0}
              title="Clear chat"
              className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition hover:bg-muted hover:text-foreground disabled:opacity-40"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear
            </button>
          </div>
          <ScrollArea className="h-64 w-full border border-border rounded-md p-2">
            {conversations.map((msg) => (
              <div
                key={msg.id}
                className={`mb-2 ${msg.role === "user" ? "text-right" : "text-left"}`}
              >
                <div
                  className={`inline-block p-2 rounded-md ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {msg.text ||
                    (msg.role === "bot" && isLoading ? (
                      <span className="inline-block animate-pulse">▍</span>
                    ) : (
                      ""
                    ))}
                </div>
                {msg.role === "bot" &&
                  msg.recommendations &&
                  msg.recommendations.length > 0 && (
                    <div className="mt-2 flex flex-col gap-2">
                      {msg.recommendations.map((rec) => (
                        <Link
                          key={rec.id}
                          href={`/products/${rec.id}`}
                          className="flex items-center gap-2 rounded-md border border-border bg-background p-2 text-left transition hover:bg-muted"
                        >
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={hiResImage(rec.image_url)}
                            alt={rec.name}
                            width={56}
                            height={56}
                            loading="lazy"
                            className="h-14 w-14 flex-shrink-0 rounded object-cover"
                            onError={(e) => {
                              (e.currentTarget as HTMLImageElement).src =
                                "/placeholder-product.svg";
                            }}
                          />
                          <div className="min-w-0">
                            <p className="truncate text-xs font-medium text-foreground">
                              {rec.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              ₹{Number(rec.price).toFixed(2)}
                            </p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
              </div>
            ))}
          </ScrollArea>

          <div className="mt-3 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Type your message..."
              className="flex-1 px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              className="p-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center"
              disabled={isLoading}
            >
              {isLoading ? (
                <svg
                  className="animate-spin h-5 w-5 text-primary-foreground"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8z"
                  ></path>
                </svg>
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
};

export default ChatWindow;
