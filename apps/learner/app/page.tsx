import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Hero } from "@/components/marketing/hero";

const tracks = [
  ["AI Fundamentals", "Rules versus learning, then the mathematics the later tracks assume."],
  ["Reinforcement Learning", "From the agent loop through Bellman, Q-learning, PPO, and SAC."],
  ["Robotics", "ROS 2, vision, SLAM, navigation, and where a learned policy may touch a motor."],
  ["LLM Engineering", "Grounded systems, and the research habits that keep a claim attached to evidence."],
];

const steps = [
  ["Ask, then wait", "The first reply is a question. The explanation arrives after you have tried."],
  ["Practice on purpose", "Quizzes, flashcards, and a small Python lab record what you can actually do."],
  ["Read papers without inventing them", "Uploaded documents are quoted. A critique appears only when a citation supports it."],
];

const prices = [
  ["Studio", "Free", "Fundamentals, the socratic tutor, and flashcards."],
  ["Pro", "$29", "Every track, the coding lab, and generated quizzes."],
  ["Research", "$79", "Document upload and a model critique when a provider is configured."],
];

const faqs = [
  ["Does the tutor give the answer immediately?", "Not in Socratic mode. The first turns ask you to retrieve the idea. Direct mode is one switch away."],
  ["Can it review a PDF?", "Yes. Text is extracted, chunked, and cited. If no model is connected, the critique is withheld instead of being guessed."],
  ["Is the coding lab a general Python sandbox?", "No. It runs a short-lived interpreter with a small module allowlist, a timeout, and no file or network access. It is not a microVM."],
];

export default function HomePage() {
  return (
    <>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <a href="/" className="font-display text-2xl tracking-tight">
          AI Mentor
        </a>
        <nav className="flex flex-wrap items-center justify-end gap-2 text-sm" aria-label="Primary">
          <a className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800" href="#tracks">
            Tracks
          </a>
          <a className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800" href="#pricing">
            Pricing
          </a>
          <a className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800" href="#faq">
            FAQ
          </a>
          <ThemeToggle />
          <Button href="/dashboard" variant="primary">
            Enter the studio
          </Button>
        </nav>
      </header>
      <main id="main">
        <Hero />
        <section id="tracks" className="mx-auto max-w-6xl px-5 py-16">
          <h2 className="font-display text-3xl tracking-tight">Tracks with prerequisites, not a pile of videos</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {tracks.map(([title, copy]) => (
              <article key={title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900">
                <div className="mb-4 h-1.5 w-16 rounded-full bg-[#2563EB]" />
                <h3 className="text-xl font-semibold">{title}</h3>
                <p className="mt-2 text-slate-700 dark:text-slate-300">{copy}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="mx-auto grid max-w-6xl gap-6 px-5 py-8 md:grid-cols-3">
          {steps.map(([title, copy], index) => (
            <article key={title}>
              <p className="font-display text-4xl text-[#1d4ed8]">{index + 1}</p>
              <h2 className="mt-2 text-xl font-semibold">{title}</h2>
              <p className="mt-2 text-slate-700 dark:text-slate-300">{copy}</p>
            </article>
          ))}
        </section>
        <section id="pricing" className="mx-auto max-w-6xl px-5 py-16">
          <h2 className="font-display text-3xl tracking-tight">Pricing</h2>
          <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
            Checkout stays disabled until Stripe is configured. The buttons will say so, rather than pretend a charge happened.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {prices.map(([name, price, copy]) => (
              <article key={name} className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
                <h3 className="text-lg font-semibold">{name}</h3>
                <p className="mt-2 font-display text-4xl">{price}</p>
                <p className="mt-3 text-slate-700 dark:text-slate-300">{copy}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="mx-auto max-w-6xl px-5 py-8">
          <h2 className="font-display text-3xl tracking-tight">What a session is for</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Illustrative scenarios, not customer claims.</p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              ["A first RL course", "The learner can say who produces a reward before they see the Bellman equation."],
              ["A lab hour", "One Q-learning step runs in the sandbox, and the review names the missing loop."],
              ["A paper afternoon", "The summary quotes the upload. Gaps stay empty when the text does not support them."],
            ].map(([title, copy]) => (
              <article key={title} className="rounded-3xl bg-[#111827] p-6 text-slate-100">
                <h3 className="text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-slate-300">{copy}</p>
              </article>
            ))}
          </div>
        </section>
        <section id="faq" className="mx-auto max-w-3xl px-5 py-16">
          <h2 className="font-display text-3xl tracking-tight">Questions</h2>
          <div className="mt-6 space-y-3">
            {faqs.map(([question, answer]) => (
              <details key={question} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
                <summary className="cursor-pointer font-semibold">{question}</summary>
                <p className="mt-2 text-slate-700 dark:text-slate-300">{answer}</p>
              </details>
            ))}
          </div>
        </section>
      </main>
      <footer className="border-t border-slate-200 px-5 py-8 text-sm text-slate-600 dark:border-slate-800 dark:text-slate-400">
        <div className="mx-auto flex max-w-6xl justify-between">
          <p>AI Mentor</p>
          <a href="/dashboard">Open the studio</a>
        </div>
      </footer>
    </>
  );
}
