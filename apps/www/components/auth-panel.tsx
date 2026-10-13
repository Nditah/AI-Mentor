import { AuthForm, type AuthMode } from "@/components/auth-form";

const copy: Record<AuthMode, { eyebrow: string; headline: string; subheading: string }> = {
  login: {
    eyebrow: "Learner App",
    headline: "Welcome back",
    subheading:
      "Sign in to continue. Staff roles open from the app launcher after you are in. This form does not grant instructor or admin access.",
  },
  register: {
    eyebrow: "Beginner to research",
    headline: "Start learning free",
    subheading:
      "A Socratic tutor, four tracks, and a restricted lab. You must be 16 or over. After you register you land on the Learner App dashboard.",
  },
};

export function AuthPanel({ mode }: { mode: AuthMode }) {
  const text = copy[mode];
  return (
    <section className="mx-auto grid w-full max-w-site flex-1 items-center gap-10 px-5 py-8 lg:grid-cols-[1.05fr_0.95fr]">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1d4ed8]">{text.eyebrow}</p>
        <h1 className="mt-3 font-display text-4xl tracking-tight md:text-5xl">{text.headline}</h1>
        <p className="mt-4 max-w-xl text-lg text-slate-700 dark:text-slate-300">{text.subheading}</p>
        {mode === "register" ? (
          <ol className="mt-8 space-y-3 text-slate-700 dark:text-slate-300">
            <li>1. Ask, then wait. The first reply is a question.</li>
            <li>2. Practice on purpose. Quizzes, flashcards, and a small Python lab.</li>
            <li>3. Read papers without inventing them.</li>
          </ol>
        ) : (
          <p className="mt-8 max-w-xl text-slate-700 dark:text-slate-300">
            Forgot your password? Use the link on the form. Reset email is sent when Clerk is configured.
          </p>
        )}
      </div>
      <AuthForm mode={mode} />
    </section>
  );
}
