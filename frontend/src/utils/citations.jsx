// Resolve inline [N] passage markers into source links using the citations
// sidecar (each entry: { title, url, passages: [N, ...] }). The model never
// writes URLs — the backend resolves passage numbers to trusted sources.
export function parseCitationMarkers(text, citations) {
  if (!text) return '';

  // Programmatically strip bolding (**) and heading (#) markdown syntax
  let cleanText = text.replace(/\*\*/g, '');
  cleanText = cleanText.replace(/#+\s+/g, '');

  const markerRegex = /\[(\d+)\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = markerRegex.exec(cleanText)) !== null) {
    if (match.index > lastIndex) {
      parts.push(cleanText.substring(lastIndex, match.index));
    }
    const passageNum = parseInt(match[1], 10);
    const cite = (citations || []).find((c) => (c.passages || []).includes(passageNum));
    if (cite && cite.url) {
      parts.push(
        <a
          key={match.index}
          href={cite.url}
          target="_blank"
          rel="noopener noreferrer"
          title={cite.title}
          className="citation-marker"
        >
          [{match[1]}]
        </a>
      );
    } else {
      parts.push(match[0]);
    }
    lastIndex = markerRegex.lastIndex;
  }

  if (lastIndex < cleanText.length) {
    parts.push(cleanText.substring(lastIndex));
  }
  return parts.length > 0 ? parts : cleanText;
}
