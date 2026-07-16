import { useState } from 'react';
import AppHeader from './components/AppHeader';
import FloatingBubble from './components/FloatingBubble';
import ChatHome from './components/ChatHome';
import ChatThread from './components/ChatThread';
import HomePage from './components/HomePage';
import { useChat } from './hooks/useChat';
import { useDraggable } from './hooks/useDraggable';

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const chat = useChat();
  const bubble = useDraggable(() => setIsOpen(true));

  const handleClose = () => {
    setIsOpen(false);
    chat.reset();
  };

  // Panel scale animation grows out of the bubble's current position
  const dynamicOriginStyle = {
    transformOrigin: `${bubble.pos.x + 32}px ${bubble.pos.y + 32 - 70}px` // adjusted for top header offset
  };

  return (
    <div className="app-viewport">
      {/* Mock CSUCI homepage rendered behind the chatbot — the Navigator
          floats over it as a widget, like on the real university site. */}
      <HomePage />

      {/* Navigator header only while the chat panel is open; when closed,
          the homepage masthead is the page header. */}
      {isOpen && <AppHeader />}

      <FloatingBubble hidden={isOpen} pos={bubble.pos} handlers={bubble.handlers} />

      <div className={`main-dashboard ${isOpen ? 'open' : 'closed'}`} style={dynamicOriginStyle}>
        {/* Customizable Background Sticker Layer */}
        <div className="chatbot-sticker-bg" />

        <button className="close-dashboard-btn" onClick={handleClose}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>

        {!chat.isChatActive ? (
          <ChatHome
            input={chat.input}
            setInput={chat.setInput}
            loading={chat.loading}
            onSubmit={chat.submit}
            language={chat.language}
            onLanguageChange={chat.setLanguage}
          />
        ) : (
          <ChatThread
            messages={chat.messages}
            loading={chat.loading}
            input={chat.input}
            setInput={chat.setInput}
            onSubmit={chat.submit}
            onCreateTicket={chat.createTicket}
            onDismissTicket={chat.dismissTicket}
            language={chat.language}
            onLanguageChange={chat.setLanguage}
          />
        )}
      </div>
    </div>
  );
}

export default App;
