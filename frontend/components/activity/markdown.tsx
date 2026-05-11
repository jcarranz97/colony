"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Minimal Markdown renderer for comment bodies.
 *
 * - GFM extensions enabled (tables, strikethrough, autolinks).
 * - Raw HTML is intentionally NOT rendered (no rehype-raw) so comment
 *   bodies cannot inject scripts or styles.
 * - Links open in a new tab so the user doesn't lose the cycle page.
 */
export function Markdown({ source }: { source: string }) {
  return (
    <div className="nb-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
