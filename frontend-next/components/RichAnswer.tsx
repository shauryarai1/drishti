'use client';

import React from 'react';
import { formatAnswer } from '../lib/formatAnswer';

/**
 * Renders an Ask KAVACH answer with the small, safe subset of formatting the
 * assistant is allowed to use (paragraphs, bold, italics, bullet/numbered
 * lists). Everything is built as React elements - React's unsafe raw-HTML
 * injection prop is deliberately never used anywhere, so markup in a model
 * response can never execute and raw formatting tokens never reach the user as
 * literal text.
 */
export function RichAnswer({ text }: { text: string }) {
  const blocks = formatAnswer(text);

  return (
    <>
      {blocks.map((block, index) =>
        block.type === 'paragraph' ? (
          <p key={index} className={index > 0 ? 'mt-2.5' : undefined}>
            {block.spans.map((span, spanIndex) => (
              <Span key={spanIndex} span={span} />
            ))}
          </p>
        ) : (
          <ul
            key={index}
            className={`mt-2.5 space-y-1 ${block.ordered ? 'list-decimal' : 'list-disc'} list-inside`}
          >
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex}>
                {item.map((span, spanIndex) => (
                  <Span key={spanIndex} span={span} />
                ))}
              </li>
            ))}
          </ul>
        ),
      )}
    </>
  );
}

function Span({ span }: { span: { text: string; bold?: boolean; italic?: boolean } }) {
  if (span.bold) return <strong className="font-semibold text-[#F7F5F0]">{span.text}</strong>;
  if (span.italic) return <em>{span.text}</em>;
  return <>{span.text}</>;
}
