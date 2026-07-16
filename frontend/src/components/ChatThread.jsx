import { useRef, useEffect } from 'react';
import ChatInput from './ChatInput';
import MessageBubble from './MessageBubble';

/** Active conversation view: scrolling message list + bottom input bar. */
export default function ChatThread({
  messages,
  loading,
  input,
  setInput,
  onSubmit,
  onCreateTicket,
  onDismissTicket,
  language,
  onLanguageChange
}) {
  const chatEndRef = useRef(null);

  // Auto-scroll chat to latest bubble
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  return (
    <div className="active-chat-container">
      <div className="chat-messages-scroll">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            onCreateTicket={onCreateTicket}
            onDismissTicket={onDismissTicket}
          />
        ))}

        {/* Loading / Typing indicator */}
        {loading && (
          <div className="chat-bubble-row bot">
            <div className="chat-text-bubble typing-dots">
              <div className="typing-dot-bubble"></div>
              <div className="typing-dot-bubble"></div>
              <div className="typing-dot-bubble"></div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div className="chat-bottom-input-bar">
        <ChatInput
          value={input}
          onChange={setInput}
          onSubmit={onSubmit}
          placeholder="Ask a follow-up question..."
          disabled={loading}
          language={language}
          onLanguageChange={onLanguageChange}
        />
      </div>
    </div>
  );
}
