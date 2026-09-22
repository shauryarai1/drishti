/**
 * Safe formatting for Ask KAVACH answers.
 *
 * The model may emit light Markdown (**bold**, *italic*, `- ` / `1. ` lists,
 * blank-line paragraphs). This module turns that text into a small, typed block
 * structure. It is DATA, never HTML: nothing is interpreted as markup and there
 * is no HTML injection path anywhere in the renderer, so raw HTML in a model
 * response can only ever appear as literal text.
 *
 * Deliberately supports only: paragraphs, bold, italics, bullet lists and
 * numbered lists. No headings, no tables, no links, no raw HTML.
 */

export interface AnswerSpan {
  text: string;
  bold?: boolean;
  italic?: boolean;
}

export type AnswerBlock =
  | { type: 'paragraph'; spans: AnswerSpan[] }
  | { type: 'list'; ordered: boolean; items: AnswerSpan[][] };

const BULLET = /^\s*[-*•]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;

/** Split one line into bold/italic spans. Never produces HTML. */
export function parseSpans(line: string): AnswerSpan[] {
  const spans: AnswerSpan[] = [];
  const pattern = /(\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(line)) !== null) {
    if (match.index > lastIndex) {
      spans.push({ text: line.slice(lastIndex, match.index) });
    }
    if (match[2] !== undefined || match[4] !== undefined) {
      spans.push({ text: (match[2] ?? match[4]) as string, bold: true });
    } else {
      spans.push({ text: (match[3] ?? match[5]) as string, italic: true });
    }
    lastIndex = pattern.lastIndex;
  }
  if (lastIndex < line.length) spans.push({ text: line.slice(lastIndex) });

  return spans.filter((span) => span.text.length > 0);
}

/** Turn an answer into blocks. Unknown syntax is kept as plain text. */
export function formatAnswer(input: string): AnswerBlock[] {
  const text = (input ?? '').replace(/\r\n?/g, '\n');
  const blocks: AnswerBlock[] = [];
  let list: { ordered: boolean; items: AnswerSpan[][] } | null = null;
  let paragraph: string[] = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push({ type: 'paragraph', spans: parseSpans(paragraph.join(' ').trim()) });
      paragraph = [];
    }
  };
  const flushList = () => {
    if (list) {
      blocks.push({ type: 'list', ordered: list.ordered, items: list.items });
      list = null;
    }
  };

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trimEnd();
    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }
    const bullet = line.match(BULLET);
    const numbered = bullet ? null : line.match(NUMBERED);
    if (bullet || numbered) {
      flushParagraph();
      const ordered = Boolean(numbered);
      if (!list || list.ordered !== ordered) {
        flushList();
        list = { ordered, items: [] };
      }
      list.items.push(parseSpans((bullet ? bullet[1] : numbered![1]).trim()));
      continue;
    }
    flushList();
    paragraph.push(line.trim());
  }
  flushParagraph();
  flushList();
  return blocks;
}
