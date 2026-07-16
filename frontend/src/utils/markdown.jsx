/**
 * Lightweight markdown renderer for chat bubbles: headings, bold,
 * bullet/numbered lists, links — plus resolution of inline [N] passage
 * markers into source links via the citations sidecar
 * (each entry: { title, url, passages: [N, ...] }).
 *
 * The model never writes URLs; [N] markers are resolved against citations
 * the backend built from retrieved passages. [Title](url) links still render
 * for code-owned text (e.g. the crisis template).
 */
export function renderMarkdown(text, citations) {
  if (!text) return null;

  const lines = text.split('\n');
  let inList = false;
  let listType = null; // 'ul' or 'ol'
  const elements = [];
  let listItems = [];

  const flushList = (key) => {
    if (listItems.length > 0) {
      const Tag = listType;
      elements.push(
        <Tag key={`list-${key}`} style={{ margin: '8px 0', paddingLeft: '20px' }}>
          {listItems}
        </Tag>
      );
      listItems = [];
      inList = false;
      listType = null;
    }
  };

  const parseInline = (inlineText) => {
    let tokens = [{ type: 'text', content: inlineText }];

    const splitTokens = (regex, makeToken) => {
      const nextTokens = [];
      for (const token of tokens) {
        if (token.type !== 'text') {
          nextTokens.push(token);
          continue;
        }
        let match;
        let lastIdx = 0;
        regex.lastIndex = 0;
        while ((match = regex.exec(token.content)) !== null) {
          if (match.index > lastIdx) {
            nextTokens.push({ type: 'text', content: token.content.substring(lastIdx, match.index) });
          }
          nextTokens.push(makeToken(match));
          lastIdx = regex.lastIndex;
        }
        if (lastIdx < token.content.length) {
          nextTokens.push({ type: 'text', content: token.content.substring(lastIdx) });
        }
      }
      tokens = nextTokens;
    };

    // Bold, then [Title](url) links, then bare [N] citation markers
    splitTokens(/\*\*([^*]+)\*\*/g, (m) => ({ type: 'bold', content: m[1] }));
    splitTokens(/\[([^\]]+)\]\(([^)]+)\)/g, (m) => ({ type: 'link', text: m[1], url: m[2] }));
    splitTokens(/\[(\d+)\]/g, (m) => ({ type: 'cite', num: parseInt(m[1], 10), raw: m[0] }));

    return tokens.map((token, idx) => {
      if (token.type === 'bold') {
        return <strong key={idx} style={{ fontWeight: 600 }}>{token.content}</strong>;
      }
      if (token.type === 'link') {
        return (
          <a
            key={idx}
            href={token.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--csuci-red)', textDecoration: 'underline', fontWeight: 500 }}
          >
            {token.text}
          </a>
        );
      }
      if (token.type === 'cite') {
        const cite = (citations || []).find((c) => (c.passages || []).includes(token.num));
        if (cite && cite.url) {
          return (
            <a
              key={idx}
              href={cite.url}
              target="_blank"
              rel="noopener noreferrer"
              title={cite.title}
              className="citation-marker"
            >
              {token.raw}
            </a>
          );
        }
        return token.raw;
      }
      return token.content;
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      flushList(i);
      elements.push(<div key={`br-${i}`} style={{ height: '8px' }} />);
      continue;
    }

    // Headings
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushList(i);
      const level = headingMatch[1].length;
      const HeadingTag = `h${level}`;
      elements.push(
        <HeadingTag key={`h-${i}`} style={{ margin: '12px 0 6px 0', fontWeight: 600, fontSize: level === 3 ? '16px' : '18px', color: 'var(--csuci-dark)' }}>
          {parseInline(headingMatch[2])}
        </HeadingTag>
      );
      continue;
    }

    // Bullet lists (* or - or •)
    const bulletMatch = line.match(/^\s*(\*|-|•)\s+(.*)$/);
    if (bulletMatch) {
      if (inList && listType !== 'ul') {
        flushList(i);
      }
      inList = true;
      listType = 'ul';
      listItems.push(
        <li key={`li-${i}`} style={{ margin: '4px 0', lineHeight: '1.5' }}>
          {parseInline(bulletMatch[2])}
        </li>
      );
      continue;
    }

    // Numbered lists
    const numberMatch = line.match(/^\s*(\d+)\.\s+(.*)$/);
    if (numberMatch) {
      if (inList && listType !== 'ol') {
        flushList(i);
      }
      inList = true;
      listType = 'ol';
      listItems.push(
        <li key={`li-${i}`} style={{ margin: '4px 0', lineHeight: '1.5' }}>
          {parseInline(numberMatch[2])}
        </li>
      );
      continue;
    }

    // Regular text line
    flushList(i);
    elements.push(
      <p key={`p-${i}`} style={{ margin: '6px 0', lineHeight: '1.5' }}>
        {parseInline(line)}
      </p>
    );
  }

  flushList(lines.length);

  return elements;
}
