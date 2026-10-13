import { FaqAccordion } from "@/components/faq";
import { Hero } from "@/components/hero";
import { ProofBar } from "@/components/proof-bar";
import { Button } from "@/components/ui/button";
import { homeFaqs, platformMega, v1Tracks } from "@/lib/pages";
import { ctas } from "@/lib/urls";

const problems = [
  ["Fixed sequences", "Video libraries do not stop you skipping the Bellman equation."],
  ["Ungrounded help", "A general model will happily invent a citation, and keep no mastery record."],
  ["Teachers cannot scale 1:1", "Institutions cannot see either, without losing control of grades."],
];

const pillars = [
  ["Grounded tutor", "Asks before it explains, and cites reviewed sources."],
  ["Prerequisite graph", "Weak foundations are repaired before the next concept."],
  ["Practice that counts", "Quizzes, flashcards, and a restricted lab. XP is not for clicks."],
  ["Humans decide", "High-stakes marks and publishing stay with a named person."],
];

const steps = [
  ["Ask, then wait", "The first reply is a question. The explanation arrives after you have tried."],
  ["Practice on purpose", "Quizzes, flashcards, and a small Python lab record what you can actually do."],
  ["Read papers without inventing them", "Uploaded documents are quoted. A critique appears only when a citation supports it."],
];

const showcases = [
  ["/platform/tutor", "Tutor", "Socratic mode asks what an agent does before it names the reward."],
  ["/paths", "Paths", "Four v1 tracks plus Knowledge Pack paths, ordered by the graph."],
  ["/platform/gamification", "Gamification", "XP for mastery, passing code, and completed reviews. Daily cap 400."],
  ["/platform/research", "Research", "Paper notes stay tied to the pages you uploaded."],
];

const scenarios = [
  ["A first RL course", "The learner can say who produces a reward before they see the Bellman equation."],
  ["A lab hour", "One Q-learning step runs in the sandbox, and the review names the missing loop."],
  ["A paper afternoon", "The summary quotes the upload. Gaps stay empty when the text does not support them."],
];

const prices = [
  ["Studio", "Free", "Fundamentals, the socratic tutor, and flashcards."],
  ["Pro", "$29", "Every track, the coding lab, and generated quizzes."],
  ["Research", "$79", "Document upload and a model critique when a provider is configured."],
];

export default function HomePage() {
  return (
    <>
      <Hero />
      <ProofBar />
      <section className="mx-auto max-w-site px-5 py-16">
        <h2 className="font-display text-3xl tracking-tight">
          Courses play. Chatbots guess. Neither knows what you understand
        </h2>
        <p className="mt-3 max-w-2xl text-slate-700 dark:text-slate-300">
          Video libraries do not stop you skipping the Bellman equation. A general model will happily invent a
          citation. Institutions cannot see either.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {problems.map(([title, copy]) => (
            <article
              key={title}
              className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-xl font-semibold">{title}</h3>
              <p className="mt-2 text-slate-700 dark:text-slate-300">{copy}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 py-8">
        <h2 className="font-display text-3xl tracking-tight">Understanding before answers</h2>
        <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
          A governed curriculum, a tutor that checks you, and a record you keep.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {pillars.map(([title, copy]) => (
            <article key={title}>
              <div className="mb-4 h-1.5 w-16 rounded-full bg-[#2563EB]" />
              <h3 className="text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-slate-700 dark:text-slate-300">{copy}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 py-16">
        <h2 className="font-display text-3xl tracking-tight">Five applications. One platform</h2>
        <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
          Learners, instructors, institutions, operators, and content teams each get an app. Rules live in the API.
        </p>
        <ul className="mt-6 flex flex-wrap gap-2">
          {["Learner", "Instructor", "Institution", "Admin", "Content Studio"].map((name) => (
            <li
              key={name}
              className="rounded-full border border-slate-300 px-4 py-2 text-sm dark:border-slate-600"
            >
              {name}
              {name === "Instructor" || name === "Institution" ? (
                <span className="ml-2 text-xs text-[#6d28d9]">Pilots from R3</span>
              ) : null}
            </li>
          ))}
        </ul>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {platformMega.slice(0, 6).map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <p className="mt-2 text-slate-700 dark:text-slate-300">{item.line}</p>
            </a>
          ))}
        </div>
      </section>
      <section className="mx-auto grid max-w-site gap-6 px-5 py-8 md:grid-cols-3">
        {steps.map(([title, copy], index) => (
          <article key={title}>
            <p className="font-display text-4xl text-[#1d4ed8]">{index + 1}</p>
            <h2 className="mt-2 text-xl font-semibold">{title}</h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{copy}</p>
          </article>
        ))}
      </section>
      <section className="mx-auto max-w-site px-5 py-16">
        <h2 className="font-display text-3xl tracking-tight">Tracks with prerequisites</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {v1Tracks.map((track) => (
            <article
              key={track.slug}
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900"
            >
              <div className="mb-4 h-1.5 w-16 rounded-full bg-[#2563EB]" />
              <h3 className="text-xl font-semibold">{track.title}</h3>
              <p className="mt-2 text-slate-700 dark:text-slate-300">{track.outcome}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 py-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {showcases.map(([href, title, copy]) => (
            <a
              key={href}
              href={href}
              className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-slate-700 dark:text-slate-300">{copy}</p>
            </a>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 py-16">
        <div className="grid gap-4 md:grid-cols-2">
          <article className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#6d28d9]">Pilots from R3</p>
            <h2 className="mt-2 text-2xl font-semibold">Instructors</h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">
              Teach the cohort. Let the tutor handle the 1:1. Marks you release.
            </p>
            <Button className="mt-6" href={ctas.instructor.href}>
              {ctas.instructor.label}
            </Button>
          </article>
          <article className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#6d28d9]">R3–R4</p>
            <h2 className="mt-2 text-2xl font-semibold">Institutions</h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">
              Every learner gets a tutor. You keep control. SSO is not self-serve today.
            </p>
            <Button className="mt-6" href={ctas.enterprise.href}>
              {ctas.enterprise.label}
            </Button>
          </article>
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 py-8">
        <h2 className="font-display text-3xl tracking-tight">What a session is for</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Illustrative scenarios, not customer claims.</p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {scenarios.map(([title, copy]) => (
            <article key={title} className="rounded-3xl bg-[#111827] p-6 text-slate-100">
              <h3 className="text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-slate-300">{copy}</p>
            </article>
          ))}
        </div>
      </section>
      <section id="pricing" className="mx-auto max-w-site px-5 py-16">
        <h2 className="font-display text-3xl tracking-tight">Pricing</h2>
        <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
          Checkout stays disabled until Stripe is configured. Organisations: Classroom, Campus, Enterprise — see
          Pricing.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {prices.map(([name, price, copy]) => (
            <article
              key={name}
              className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-lg font-semibold">{name}</h3>
              <p className="mt-2 font-display text-4xl">{price}</p>
              <p className="mt-3 text-slate-700 dark:text-slate-300">{copy}</p>
            </article>
          ))}
        </div>
        <Button className="mt-8" href="/pricing" variant="quiet">
          Compare plans
        </Button>
      </section>
      <section id="faq" className="mx-auto max-w-3xl px-5 py-16">
        <h2 className="font-display text-3xl tracking-tight">Questions</h2>
        <div className="mt-6">
          <FaqAccordion items={homeFaqs} />
        </div>
      </section>
      <section className="border-t border-slate-200 px-5 py-16 dark:border-slate-800">
        <div className="mx-auto max-w-site">
          <h2 className="font-display text-3xl tracking-tight">Start with a question, not a video</h2>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href={ctas.learner.href}>{ctas.learner.label}</Button>
            <Button href="/demo/enterprise" variant="quiet">
              Request a demo
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}
