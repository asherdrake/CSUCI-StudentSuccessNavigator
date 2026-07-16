import { renderMarkdown } from '../utils/markdown';
import EscalationCard from './EscalationCard';

export default function MessageBubble({ msg, onCreateTicket, onDismissTicket }) {
  return (
    <div className={`chat-bubble-row ${msg.role}`}>
      <div className="chat-text-bubble">
        <div>{renderMarkdown(msg.content, msg.citations)}</div>

        {/* Source list (deduped, resolved server-side from passage numbers) */}
        {msg.citations && msg.citations.length > 0 && (
          <div className="citations-wrapper">
            {msg.citations.map((cite, index) => (
              <a
                key={index}
                href={cite.url}
                target="_blank"
                rel="noopener noreferrer"
                className="citation-btn"
              >
                🔗 {cite.title}
              </a>
            ))}
          </div>
        )}

        {msg.escalation && (
          <EscalationCard
            msg={msg}
            onCreateTicket={onCreateTicket}
            onDismissTicket={onDismissTicket}
          />
        )}
      </div>
    </div>
  );
}
