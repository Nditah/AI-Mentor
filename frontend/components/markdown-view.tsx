"use client";

import { useEffect, useId, useRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

export function MentorMarkdown({ content }: { content: string }) {
  return (
    <div className="prose-mentor">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code({ className, children }) {
            const text = String(children).replace(/\n$/, "");
            const language = /language-(\w+)/.exec(className || "")?.[1];
            if (language === "mermaid") return <Mermaid chart={text} />;
            if (!className) {
              return <code className="rounded bg-slate-100 px-1 py-0.5 text-[0.92em] dark:bg-slate-800">{text}</code>;
            }
            return (
              <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-slate-100">
                <code>{text}</code>
              </pre>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function Mermaid({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const reactId = useId().replace(/:/g, "");
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
      const { svg } = await mermaid.render(`diagram-${reactId}`, chart);
      if (!cancelled && ref.current) ref.current.innerHTML = svg;
    })().catch(() => {
      if (ref.current) ref.current.textContent = "The diagram could not be drawn.";
    });
    return () => {
      cancelled = true;
    };
  }, [chart, reactId]);
  return <div ref={ref} className="my-4 overflow-x-auto" role="img" aria-label="Diagram" />;
}
