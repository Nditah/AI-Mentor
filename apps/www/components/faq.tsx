export function FaqAccordion({ items }: { items: [string, string][] }) {
  return (
    <div className="space-y-3">
      {items.map(([question, answer]) => (
        <details
          key={question}
          className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
        >
          <summary className="cursor-pointer font-semibold">{question}</summary>
          <p className="mt-2 text-slate-700 dark:text-slate-300">{answer}</p>
        </details>
      ))}
    </div>
  );
}
