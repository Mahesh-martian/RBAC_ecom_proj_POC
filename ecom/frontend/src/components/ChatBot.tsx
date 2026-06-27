import { useState } from 'react'
import { Link } from 'react-router-dom'
import { chatApi } from '@api/client'

type BotRecommendation = {
  id: number
  name: string
  price: number
  currency: string
}

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  recommendations?: BotRecommendation[]
}

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isTypingEffect, setIsTypingEffect] = useState(false)

  const appendAssistantMessageWithTyping = (message: ChatMessage) =>
    new Promise<void>((resolve) => {
      const fullText = message.content || ''
      const chunkSize = fullText.length > 320 ? 4 : 2
      const typingDelayMs = 14

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

      if (!fullText) {
        setMessages((prev) => {
          const next = [...prev]
          if (next.length > 0) {
            next[next.length - 1] = message
          }
          return next
        })
        resolve()
        return
      }

      let index = 0
      const timerId = window.setInterval(() => {
        index = Math.min(fullText.length, index + chunkSize)
        const partial = fullText.slice(0, index)

        setMessages((prev) => {
          const next = [...prev]
          if (next.length > 0 && next[next.length - 1].role === 'assistant') {
            next[next.length - 1] = {
              ...next[next.length - 1],
              content: partial,
            }
          }
          return next
        })

        if (index >= fullText.length) {
          window.clearInterval(timerId)
          setMessages((prev) => {
            const next = [...prev]
            if (next.length > 0) {
              next[next.length - 1] = message
            }
            return next
          })
          resolve()
        }
      }, typingDelayMs)
    })

  const getFallbackReply = (query: string): ChatMessage => {
    const lower = query.toLowerCase()
    if (lower.includes('shoe') || lower.includes('sneaker')) {
      return {
        role: 'assistant',
        content: 'I cannot reach the live AI service right now, but footwear is available in the catalog. Try searching for shoes on the Products page.',
      }
    }
    if (lower.includes('bag') || lower.includes('backpack')) {
      return {
        role: 'assistant',
        content: 'Live AI is currently unavailable. You can still browse bags and accessories from the Products page.',
      }
    }
    return {
      role: 'assistant',
      content: 'AI service is not configured yet (or temporarily unavailable). You can still browse products, add to cart, and checkout normally.',
    }
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isSending || isTypingEffect) return

    // Add user message
    const userMessage = { role: 'user' as const, content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsSending(true)

    try {
      const response = await chatApi.query({ query: trimmed })
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        recommendations: response.recommendations?.map((item) => ({
          id: item.id,
          name: item.name,
          price: item.price,
          currency: item.currency,
        })),
      }
      setIsSending(false)
      setIsTypingEffect(true)
      await appendAssistantMessageWithTyping(assistantMessage)
      setIsTypingEffect(false)
    } catch {
      setMessages((prev) => [
        ...prev,
        getFallbackReply(trimmed),
      ])
    } finally {
      setIsSending(false)
      setIsTypingEffect(false)
    }
  }

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 p-4 bg-primary-600 text-white rounded-full shadow-lg hover:bg-primary-700 transition-all duration-200 z-40"
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" />
            <path d="M6 11a1 1 0 11-2 0 1 1 0 012 0zM10 11a1 1 0 11-2 0 1 1 0 012 0zM14 11a1 1 0 11-2 0 1 1 0 012 0z" />
          </svg>
        </button>
      )}

      {/* Chat Modal */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl flex flex-col z-40">
          {/* Header */}
          <div className="bg-primary-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <h3 className="font-bold">FashionStore Assistant</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <p className="font-medium">Hi! 👋</p>
                <p className="text-sm mt-2">How can we help you find the perfect style?</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    {msg.content}
                    {msg.role === 'assistant' && msg.recommendations && msg.recommendations.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {msg.recommendations.map((item) => (
                          <Link
                            to={`/products/${item.id}`}
                            key={item.id}
                            className="block rounded border border-gray-300 bg-white px-2 py-1 text-sm text-gray-900 hover:bg-gray-100"
                          >
                            <div className="font-medium">{item.name}</div>
                            <div>{item.currency} {item.price.toFixed(2)}</div>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isSending && (
              <div className="flex justify-start">
                <div className="max-w-xs px-4 py-2 rounded-lg bg-gray-200 text-gray-900">
                  Thinking...
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type a message..."
              className="input flex-1"
              disabled={isSending || isTypingEffect}
            />
            <button
              onClick={handleSend}
              className="btn-primary btn-md"
              disabled={isSending || isTypingEffect}
            >
              {isSending ? 'Thinking...' : isTypingEffect ? 'Typing...' : 'Send'}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
