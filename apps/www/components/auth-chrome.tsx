import { ThemeToggle } from "@/components/theme-toggle";

export function AuthChrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-site items-center justify-between px-5 py-5">
        <a href="/" className="font-display text-2xl tracking-tight">
          AI Mentor
        </a>
        <ThemeToggle />
      </header>
      <main id="main" className="flex flex-1 flex-col">
        {children}
      </main>
      <p className="px-5 py-6 text-center text-sm text-slate-600 dark:text-slate-400">
        16 and over. Not an awarding body.{" "}
        <a className="font-semibold text-[#1d4ed8]" href="/legal/privacy">
          Privacy
        </a>
        {" · "}
        <a className="font-semibold text-[#1d4ed8]" href="/legal/terms">
          Terms
        </a>
      </p>
    </div>
  );
}
