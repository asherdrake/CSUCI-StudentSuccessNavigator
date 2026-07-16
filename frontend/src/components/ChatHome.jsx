import ChatInput from './ChatInput';

/** Landing view shown before the first user message. */
export default function ChatHome({ input, setInput, loading, onSubmit, language, onLanguageChange }) {
  return (
    <div className="gemini-home-container">
      <div className="gemini-content-wrapper">
        {/* Centered intense red radial fade backplate */}
        <div className="gemini-glow-bg"></div>

        <h2 className="gemini-greeting">I&apos;m Ekho, how may I help you today?</h2>

        <ChatInput
          value={input}
          onChange={setInput}
          onSubmit={onSubmit}
          placeholder="Ask the Success Navigator..."
          disabled={loading}
          language={language}
          onLanguageChange={onLanguageChange}
        />
      </div>
    </div>
  );
}
