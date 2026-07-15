import React, { useState, useRef, useEffect } from 'react';

// Read VITE_API_URL from build/environment vars, fallback to local dev server
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'bot',
      content: 'Hello! I am the CSUCI Student Success Navigator. How can I help you find registration, advising, degree requirements, or financial aid information today?',
      citations: [],
      escalation: null,
      answered: true
    }
  ]);
  const [history, setHistory] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const chatEndRef = useRef(null);

  // Auto-scroll chat to the latest message
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Helper to format text markdown citations into HTML or safe react nodes
  const formatText = (text) => {
    if (!text) return '';
    
    // Convert markdown link pattern [Title](URL) into clickable links
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      // Push preceding text block
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      // Push React anchor node
      const title = match[1];
      const url = match[2];
      parts.push(
        <a key={match.index} href={url} target="_blank" rel="noopener noreferrer" style={{ color: '#9E1B32', textDecoration: 'underline', fontWeight: '500' }}>
          {title}
        </a>
      );
      lastIndex = linkRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);

    // Append user message to UI
    const newUserMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      citations: [],
      escalation: null,
      answered: true
    };
    setMessages((prev) => [...prev, newUserMsg]);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage,
          history: history,
          sessionId: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update session tracker
      if (data.sessionId) {
        setSessionId(data.sessionId);
      }

      const newBotMsg = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.answer || 'I am sorry, I am unable to answer this question directly.',
        citations: data.citations || [],
        escalation: data.escalation,
        answered: data.answered
      };

      setMessages((prev) => [...prev, newBotMsg]);

      // Update conversational history state (only if answered successfully)
      if (data.answered && data.answer) {
        setHistory((prev) => [
          ...prev,
          { role: 'user', content: userMessage },
          { role: 'assistant', content: data.answer }
        ]);
      }

    } catch (error) {
      console.error('Failed to contact backend:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'bot',
          content: "Sorry, I am having trouble connecting to the backend. Please check if the local server is running at port 8000, or verify your internet connection.",
          citations: [],
          escalation: null,
          answered: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Brand Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">CI</div>
          <div className="brand-info">
            <h1>Student Success Navigator</h1>
            <p>CSU Channel Islands AI Assistant</p>
          </div>
        </div>
        <div className="api-badge">
          <div className="api-indicator"></div>
          Bedrock Active
        </div>
      </header>

      {/* Messages Scroll Area */}
      <main className="chat-window">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row ${msg.role}`}>
            <div className="message-bubble">
              {/* Bot or User content */}
              {msg.role === 'bot' && !msg.answered ? (
                <div style={{ fontStyle: 'italic', color: '#64748B' }}>
                  No local context found. Redirecting to human support...
                </div>
              ) : (
                <div>{formatText(msg.content)}</div>
              )}

              {/* Citations list */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations-container">
                  {msg.citations.map((cite, index) => (
                    <a
                      key={index}
                      href={cite.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="citation-chip"
                    >
                      🔗 {cite.title}
                    </a>
                  ))}
                </div>
              )}

              {/* Handoff / Escalation Card */}
              {msg.escalation && (
                <div className="escalation-card">
                  <h3>⚠️ Human Advisor Handoff</h3>
                  <p>
                    I couldn't locate official documentation directly addressing this. We have drafted a transfer request for you:
                  </p>
                  
                  <div className="escalation-contact-info">
                    <strong>Target Department:</strong> {msg.escalation.office}<br />
                    <strong>Phone:</strong> {msg.escalation.contact.phone}<br />
                    <strong>Office Site:</strong> <a href={msg.escalation.contact.url} target="_blank" rel="noopener noreferrer">Visit Website</a>
                  </div>

                  {msg.escalation.ticket_draft && (
                    <div className="ticket-draft-section">
                      <strong>Draft Support Ticket:</strong>
                      <div className="ticket-draft-text">
                        {msg.escalation.ticket_draft.summary}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading / Typing indicator */}
        {loading && (
          <div className="message-row bot">
            <div className="message-bubble typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        
        <div ref={chatEndRef} />
      </main>

      {/* Input bar */}
      <form onSubmit={handleSend} className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about registration, major requirements, tutoring..."
          className="chat-input"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-button"
        >
          Send
        </button>
      </form>
    </div>
  );
}

export default App;
