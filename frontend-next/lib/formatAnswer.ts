/**
 * Safe formatting for Ask KAVACH answers.
 *
 * The model may emit light Markdown (**bold**, *italic*, `- ` / `1. ` lists,
 * blank-line paragraphs) and, defensively, fenced code blocks. This module turns
 * that text into a small, typed block structure. It is DATA, never HTML: nothing
 * is interpreted as markup and there is no HTML injection path anywhere in the
 * renderer, so raw HTML in a model response can only ever appear as literal text.
 *
 * Fenced code is recognised FIRST, before any inline processing, so code content
 * is never treated as emphasis and its indentation and newlines are preserved.
 * Only these forms are supported: paragraphs, bold (**), italics (*), bullet and
 * numbered lists, and fenced code. No headings, tables, links or raw HTML.
 * Underscore emphasis is deliberately NOT supported: identifiers such as
 * `__name__` must never be reinterpreted as formatting.
 */

export interface AnswerSpan {
  text: string;
  bold?: boolean;
  italic?: boolean;
}

export type AnswerBlock =
  | { type: 'paragraph'; spans: AnswerSpan[] }
  | { type: 'list'; ordered: boolean; items: AnswerSpan[][] }
  | { type: 'code'; language: string; code: string };

const BULLET = /^\s*[-*•]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;
const FENCE = /^\s*```(.*)$/;

/** Split one line into bold/italic spans. Never produces HTML. */
export function parseSpans(line: string): AnswerSpan[] {
  const spans: AnswerSpan[] = [];
  const pattern = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(line)) !== null) {
    if (match.index > lastIndex) {
      spans.push({ text: line.slice(lastIndex, match.index) });
    }
    if (match[2] !== undefined) {
      spans.push({ text: match[2], bold: true });
    } else {
      spans.push({ text: (match[3] ?? '') as string, italic: true });
    }
    lastIndex = pattern.lastIndex;
  }
  if (lastIndex < line.length) spans.push({ text: line.slice(lastIndex) });

  return spans.filter((span) => span.text.length > 0);
}

/** Turn an answer into blocks. Unknown syntax is kept as plain text. */
export function formatAnswer(input: string): AnswerBlock[] {
  const text = (input ?? '').replace(/\r\n?/g, '\n');
  const rawLines = text.split('\n');
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
  const flushAll = () => {
    flushParagraph();
    flushList();
  };

  for (let index = 0; index < rawLines.length; index += 1) {
    const rawLine = rawLines[index];

    const fence = rawLine.match(FENCE);
    if (fence) {
      flushAll();
      const language = (fence[1] || '').trim();
      const codeLines: string[] = [];
      index += 1;
      while (index < rawLines.length && !FENCE.test(rawLines[index])) {
        codeLines.push(rawLines[index]);
        index += 1;
      }
      // `index` now sits on the closing fence (or past the end of the input).
      blocks.push({ type: 'code', language, code: codeLines.join('\n') });
      continue;
    }

    const line = rawLine.trimEnd();
    if (!line.trim()) {
      flushAll();
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
  flushAll();
  return blocks;
}
