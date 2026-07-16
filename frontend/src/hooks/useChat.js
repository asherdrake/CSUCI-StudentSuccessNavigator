import { useEffect, useRef, useState } from 'react';
import { API_URL, WELCOME_MESSAGE } from '../config';

/**
 * Chat state + backend API orchestration.
 *
 * Owns messages, client-managed LLM history, session id, input text,
 * language preference, the word-by-word reveal of bot replies, and the
 * interactive-ticket state on escalation messages. Backend responses follow
 * the type-discriminated contract:
 *   { type, message, citations?, escalation?, sessionId }
 */
export function useChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [history, setHistory] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);

  // Simulated streaming: the response arrives complete, then reveals
  // word-by-word for a live typing feel.
  const streamIntervalRef = useRef(null);

  const stopStreaming = () => {
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
  };

  useEffect(() => stopStreaming, []); // clear on unmount

  const streamBotMessage = (msgId, fullText) => {
    stopStreaming();
    const words = fullText.split(' ');
    let wordIndex = 0;
    let revealed = '';

    streamIntervalRef.current = setInterval(() => {
      if (wordIndex < words.length) {
        revealed += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
        wordIndex++;
        const content = revealed;
        setMessages((prev) =>
          prev.map((msg) => (msg.id === msgId ? { ...msg, content } : msg))
        );
      } else {
        stopStreaming();
      }
    }, 25); // Fast, premium-feeling 25ms delay per word
  };

  const reset = () => {
    stopStreaming();
    setMessages([WELCOME_MESSAGE]);
    setHistory([]);
    setSessionId(null);
    setInput('');
  };

  const submit = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    setInput('');
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: userQuery,
        citations: [],
        escalation: null
      }
    ]);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userQuery,
          history: history,
          sessionId: sessionId,
          language: language
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned status: ${response.status}`);
      }

      const data = await response.json();

      if (data.sessionId) {
        setSessionId(data.sessionId);
      }

      const botMsgId = (Date.now() + 1).toString();
      const fullMessage = data.message || '';

      setMessages((prev) => [
        ...prev,
        {
          id: botMsgId,
          role: 'bot',
          type: data.type,
          content: '', // revealed word-by-word below
          citations: data.citations || [],
          escalation: data.escalation || null
        }
      ]);
      streamBotMessage(botMsgId, fullMessage);

      // Only real answers and clarifying questions carry dialogue value for
      // the LLM's next turn; canned escalate/decline messages do not.
      if ((data.type === 'answer' || data.type === 'clarify') && fullMessage) {
        setHistory((prev) => [
          ...prev,
          { role: 'user', content: userQuery },
          { role: 'assistant', content: fullMessage }
        ]);
      }
    } catch (err) {
      console.error('Connection failed:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'bot',
          content:
            'Sorry, I am unable to connect to the navigator backend. Please ensure the local server is running on http://localhost:8000/chat.',
          citations: [],
          escalation: null
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const createTicket = (msgId) => {
    const ticketId = `CSUCI-${Math.floor(100000 + Math.random() * 900000)}`;
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === msgId ? { ...msg, ticketStatus: 'created', ticketId } : msg
      )
    );
  };

  const dismissTicket = (msgId) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === msgId ? { ...msg, ticketStatus: 'dismissed' } : msg
      )
    );
  };

  // Has a real conversation session started?
  const isChatActive = messages.some((m) => m.role === 'user');

  return {
    messages,
    input,
    setInput,
    language,
    setLanguage,
    loading,
    isChatActive,
    submit,
    reset,
    createTicket,
    dismissTicket
  };
}
