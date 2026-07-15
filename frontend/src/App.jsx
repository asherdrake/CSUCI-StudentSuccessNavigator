import React, { useState, useRef, useEffect } from 'react';

// Read API URL from configuration, fallback to local dev server
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat';

function App() {
  const [isOpen, setIsOpen] = useState(false);
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

  // Floating bubble draggable coordinates
  const [bubblePos, setBubblePos] = useState({
    x: window.innerWidth - 90,
    y: window.innerHeight - 90
  });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const bubbleStart = useRef({ x: 0, y: 0 });
  const clickStart = useRef(0); // Timestamp to distinguish click vs drag

  const chatEndRef = useRef(null);

  // Auto-scroll chat to latest bubble
  useEffect(() => {
    if (isOpen && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, isOpen]);

  // Adjust coordinates if window is resized
  useEffect(() => {
    const handleResize = () => {
      setBubblePos((prev) => ({
        x: Math.min(prev.x, window.innerWidth - 80),
        y: Math.min(prev.y, window.innerHeight - 80)
      }));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // --- Draggable Handlers for the Bubble ---
  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    clickStart.current = Date.now();
    dragStart.current = { x: e.clientX, y: e.clientY };
    bubbleStart.current = { x: bubblePos.x, y: bubblePos.y };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const deltaX = e.clientX - dragStart.current.x;
    const deltaY = e.clientY - dragStart.current.y;
    
    const newX = Math.max(10, Math.min(bubbleStart.current.x + deltaX, window.innerWidth - 74));
    const newY = Math.max(80, Math.min(bubbleStart.current.y + deltaY, window.innerHeight - 74));

    setBubblePos({ x: newX, y: newY });
  };

  const handleMouseUp = (e) => {
    setIsDragging(false);
    const duration = Date.now() - clickStart.current;
    const distance = Math.hypot(e.clientX - dragStart.current.x, e.clientY - dragStart.current.y);

    if (distance < 6 && duration < 300) {
      setIsOpen(true);
    }
  };

  // --- Touch Support for Mobile Dragging ---
  const handleTouchStart = (e) => {
    const touch = e.touches[0];
    setIsDragging(true);
    clickStart.current = Date.now();
    dragStart.current = { x: touch.clientX, y: touch.clientY };
    bubbleStart.current = { x: bubblePos.x, y: bubblePos.y };
  };

  const handleTouchMove = (e) => {
    if (!isDragging) return;
    const touch = e.touches[0];
    const deltaX = touch.clientX - dragStart.current.x;
    const deltaY = touch.clientY - dragStart.current.y;
    
    const newX = Math.max(10, Math.min(bubbleStart.current.x + deltaX, window.innerWidth - 74));
    const newY = Math.max(80, Math.min(bubbleStart.current.y + deltaY, window.innerHeight - 74));

    setBubblePos({ x: newX, y: newY });
  };

  const handleTouchEnd = (e) => {
    setIsDragging(false);
    const duration = Date.now() - clickStart.current;
    const touch = e.changedTouches[0];
    const distance = Math.hypot(touch.clientX - dragStart.current.x, touch.clientY - dragStart.current.y);

    if (distance < 6 && duration < 300) {
      setIsOpen(true);
    }
  };

  // --- Close & Reset Handler ---
  const handleClose = () => {
    setIsOpen(false);
    setMessages([
      {
        id: 'welcome',
        role: 'bot',
        content: 'Hello! I am the CSUCI Student Success Navigator. How can I help you find registration, advising, degree requirements, or financial aid information today?',
        citations: [],
        escalation: null,
        answered: true
      }
    ]);
    setHistory([]);
    setSessionId(null);
    setInput('');
  };

  const parseMarkdownLinks = (text) => {
    if (!text) return '';
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      const title = match[1];
      const url = match[2];
      parts.push(
        <a key={match.index} href={url} target="_blank" rel="noopener noreferrer" style={{ color: '#C51B29', textDecoration: 'underline', fontWeight: '600' }}>
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

  // --- API Submission ---
  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    setInput('');
    setLoading(true);

    const newUserMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: userQuery,
      citations: [],
      escalation: null,
      answered: true
    };
    setMessages((prev) => [...prev, newUserMsg]);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userQuery,
          history: history,
          sessionId: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.sessionId) {
        setSessionId(data.sessionId);
      }

      const newBotMsg = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.answer || '',
        citations: data.citations || [],
        escalation: data.escalation,
        answered: data.answered
      };

      setMessages((prev) => [...prev, newBotMsg]);

      if (data.answered && data.answer) {
        setHistory((prev) => [
          ...prev,
          { role: 'user', content: userQuery },
          { role: 'assistant', content: data.answer }
        ]);
      }

    } catch (err) {
      console.error("Connection failed:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'bot',
          content: "Sorry, I am unable to connect to the navigator backend. Please ensure the local server is running on http://localhost:8000/chat.",
          citations: [],
          escalation: null,
          answered: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Has a real conversation session started?
  const isChatActive = messages.some((m) => m.role === 'user');

  // Dynamic origin style applied inline on full-screen dashboard panel
  const dynamicOriginStyle = {
    transformOrigin: `${bubblePos.x + 32}px ${bubblePos.y + 32 - 70}px` // adjusted for top header offset
  };

  return (
    <div className="app-viewport">
      {/* 1. Fixed CSUCI Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">CI</div>
          <div className="brand-info">
            <h1>Student Success Navigator</h1>
            <p>California State University Channel Islands</p>
          </div>
        </div>
        <div className="api-badge">
          <div className="api-indicator"></div>
          Bedrock Active
        </div>
      </header>

      {/* 2. Floating Draggable Bubble */}
      <div
        className={`chat-trigger-bubble ${isOpen ? 'hidden' : ''}`}
        style={{ left: `${bubblePos.x}px`, top: `${bubblePos.y}px` }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <svg className="bubble-icon" viewBox="0 0 24 24">
          <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z" />
        </svg>
      </div>

      {/* 3. Main Dashboard Panel (Restored back to full-screen view under header) */}
      <div
        className={`main-dashboard ${isOpen ? 'open' : 'closed'}`}
        style={dynamicOriginStyle}
      >
        <button className="close-dashboard-btn" onClick={handleClose}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>

        {!isChatActive ? (
          /* --- Gemini Home Page Layout --- */
          <div className="gemini-home-container">
            <div className="gemini-content-wrapper">
              {/* Centered intense red radial fade backplate */}
              <div className="gemini-glow-bg"></div>

              <h2 className="gemini-greeting">I&apos;m Ekho, how may I help you today?</h2>
              
              <form onSubmit={handleSubmit} className="gemini-pill-input-box">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask the Success Navigator..."
                  className="gemini-pill-input"
                  disabled={loading}
                />
                <button type="submit" disabled={loading || !input.trim()} className="gemini-input-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                </button>
              </form>
            </div>
          </div>
        ) : (
          /* --- Active Conversation Thread View --- */
          <div className="active-chat-container">
            <div className="chat-messages-scroll">
              {messages.map((msg) => (
                <div key={msg.id} className={`chat-bubble-row ${msg.role}`}>
                  <div className="chat-text-bubble">
                    {!msg.answered && msg.role === 'bot' ? (
                      <span style={{ color: 'var(--csuci-muted)', fontStyle: 'italic' }}>
                        User response can't be processed. Routing request...
                      </span>
                    ) : (
                      <div>{parseMarkdownLinks(msg.content)}</div>
                    )}

                    {/* Source Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="citations-wrapper">
                        {msg.citations.map((cite, index) => (
                          <a key={index} href={cite.url} target="_blank" rel="noopener noreferrer" className="citation-btn">
                            🔗 {cite.title}
                          </a>
                        ))}
                      </div>
                    )}

                    {/* Escalation Card */}
                    {msg.escalation && (
                      <div className="escalation-alert-box">
                        <h3>⚠️ Human Advisor Handoff</h3>
                        <p>We are transferring your question to the appropriate campus office:</p>
                        <div className="escalation-details">
                          <strong>Office:</strong> {msg.escalation.office}<br />
                          {msg.escalation.contact.location && (
                            <>
                              <strong>Location:</strong> {msg.escalation.contact.location}{' '}
                              {msg.escalation.contact.map_url && (
                                <a href={msg.escalation.contact.map_url} target="_blank" rel="noopener noreferrer" style={{ color: '#C51B29', textDecoration: 'underline', marginLeft: '4px' }}>
                                  (Google Maps)
                                </a>
                              )}
                              <br />
                            </>
                          )}
                          <strong>Phone:</strong> {msg.escalation.contact.phone}<br />
                          <strong>Direct Link:</strong> <a href={msg.escalation.contact.url} target="_blank" rel="noopener noreferrer">Visit Website</a>
                        </div>
                        {msg.escalation.ticket_draft && (
                          <div className="ticket-draft-log">
                            <strong>Draft Support Ticket:</strong>
                            <div className="ticket-draft-log-box">{msg.escalation.ticket_draft.summary}</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
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

            {/* Bottom input text bar */}
            <div className="chat-bottom-input-bar">
              <form onSubmit={handleSubmit} className="gemini-pill-input-box">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a follow-up question..."
                  className="gemini-pill-input"
                  disabled={loading}
                />
                <button type="submit" disabled={loading || !input.trim()} className="gemini-input-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
