export default function ChatInput({ value, onChange, onSubmit, placeholder, disabled }) {
  return (
    <form onSubmit={onSubmit} className="gemini-pill-input-box">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="gemini-pill-input"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()} className="gemini-input-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
        </svg>
      </button>
    </form>
  );
}
