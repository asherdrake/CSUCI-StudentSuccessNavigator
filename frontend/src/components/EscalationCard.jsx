/**
 * Human-handoff card: office contact details plus the interactive
 * support-ticket flow. `escalation` follows the API contract:
 *   { office, contact: {phone, url, location, map_url}, ticket_draft }
 */
export default function EscalationCard({ msg, onCreateTicket, onDismissTicket }) {
  const { escalation } = msg;

  return (
    <div className="escalation-alert-box">
      <h3>⚠️ Human Advisor Handoff</h3>
      <p>We suggest reaching out to the specialized campus office for this question:</p>
      <div className="escalation-details" style={{ marginBottom: '16px' }}>
        <strong>Office:</strong> {escalation.office}<br />
        {escalation.contact.location && (
          <>
            <strong>Location:</strong> {escalation.contact.location}{' '}
            {escalation.contact.map_url && (
              <a
                href={escalation.contact.map_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#C51B29', textDecoration: 'underline', marginLeft: '4px' }}
              >
                (Google Maps)
              </a>
            )}
            <br />
          </>
        )}
        <strong>Phone:</strong> {escalation.contact.phone}<br />
        <strong>Direct Link:</strong>{' '}
        <a
          href={escalation.contact.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#C51B29', fontWeight: 'bold' }}
        >
          Visit Website
        </a>
      </div>

      {/* Interactive Ticket Flow */}
      {!msg.ticketStatus ? (
        <div style={{ background: '#f8f9fa', border: '1px solid #e9ecef', borderRadius: '6px', padding: '12px', marginTop: '12px' }}>
          <p style={{ fontSize: '13px', fontWeight: '600', color: '#333', margin: '0 0 10px 0' }}>
            Would you like to generate an official support ticket for this request?
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => onCreateTicket(msg.id)}
              style={{ background: '#C51B29', color: '#fff', border: 'none', borderRadius: '4px', padding: '6px 12px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              Yes, Generate Ticket
            </button>
            <button
              onClick={() => onDismissTicket(msg.id)}
              style={{ background: 'transparent', color: '#666', border: '1px solid #ccc', borderRadius: '4px', padding: '6px 12px', fontSize: '12px', cursor: 'pointer' }}
            >
              No, Thanks
            </button>
          </div>
        </div>
      ) : msg.ticketStatus === 'created' ? (
        <div style={{ background: '#d1e7dd', border: '1px solid #badbcc', borderRadius: '6px', padding: '12px', marginTop: '12px', color: '#0f5132' }}>
          <div style={{ fontWeight: 'bold', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            ✅ Support Ticket Generated Successfully
          </div>
          <div style={{ fontSize: '13px' }}>
            <strong>Ticket ID:</strong> #{msg.ticketId}<br />
            <strong>Department:</strong> {escalation.office}<br />
            <strong>Summary:</strong> {escalation.ticket_draft?.summary || 'Academic Inquiry'}
          </div>
        </div>
      ) : (
        <div style={{ background: '#f8f9fa', border: '1px solid #e9ecef', borderRadius: '6px', padding: '12px', marginTop: '12px', color: '#666', fontSize: '12px', fontStyle: 'italic' }}>
          Ticket generation skipped. You can reach the office directly using the contact details above.
        </div>
      )}
    </div>
  );
}
