import { headers } from "next/headers";
import { DemoForm } from "@/components/demo-form";
import { FaqAccordion } from "@/components/faq";
import { Button } from "@/components/ui/button";
import { catalogStats, curriculumPaths, publicLeaderboard } from "@/lib/api";
import { faqGroups, type PageSpec, v1Tracks } from "@/lib/pages";
import { ctas, learnerPath, learnerUrl, studioUrl } from "@/lib/urls";

export function PageHero({ spec }: { spec: PageSpec }) {
  const primary = ctas[spec.cta];
  return (
    <section className="mx-auto max-w-site px-5 py-12">
      {spec.eyebrow ? (
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1d4ed8]">{spec.eyebrow}</p>
      ) : null}
      <h1 className="mt-3 max-w-4xl font-display text-4xl tracking-tight md:text-5xl">{spec.headline}</h1>
      <p className="mt-4 max-w-2xl text-lg text-slate-700 dark:text-slate-300">{spec.subheading}</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Button href={primary.href}>{primary.label}</Button>
        {spec.secondary ? (
          <Button href={spec.secondary.href} variant="quiet">
            {spec.secondary.label}
          </Button>
        ) : null}
      </div>
    </section>
  );
}

export function BlockGrid({ spec }: { spec: PageSpec }) {
  if (spec.blocks.length === 0) return null;
  return (
    <section className="mx-auto max-w-site px-5 pb-16">
      <div className="grid gap-4 md:grid-cols-2">
        {spec.blocks.map((block) => (
          <article
            key={block.title}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900"
          >
            <div className="mb-4 h-1.5 w-16 rounded-full bg-[#2563EB]" />
            {block.badge ? (
              <p className="text-xs font-semibold uppercase tracking-wide text-[#6d28d9]">{block.badge}</p>
            ) : null}
            <h2 className="mt-2 text-xl font-semibold">{block.title}</h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{block.body}</p>
            {block.href ? (
              <p className="mt-4">
                <a className="font-semibold text-[#1d4ed8]" href={block.href}>
                  Read more
                </a>
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

export async function ContentPage({ spec }: { spec: PageSpec }) {
  const kind = spec.kind ?? "standard";
  return (
    <>
      <PageHero spec={spec} />
      {kind === "pricing" ? <PricingBody spec={spec} /> : null}
      {kind === "paths" ? <PathsBody /> : null}
      {kind === "gamification" ? <LeaderboardPreview /> : null}
      {kind === "faq" ? <FaqBody /> : null}
      {kind === "legal" ? (
        <section className="mx-auto max-w-3xl space-y-4 px-5 pb-16 text-slate-700 dark:text-slate-300">
          {(spec.legal ?? []).map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </section>
      ) : null}
      {kind === "about" ? (
        <blockquote className="mx-auto max-w-site px-5 pb-8 text-lg text-slate-800 dark:text-slate-200">
          Give every person a world-class private AI tutor that knows them and adapts to them, and give the
          teachers and organisations around them the tools to teach, govern, and prove learning at scale, from a
          learner&apos;s first line of Python to publishable research.
        </blockquote>
      ) : null}
      {kind === "blog" ? (
        <p className="mx-auto max-w-site px-5 pb-8 text-sm text-slate-600 dark:text-slate-400">
          Categories are ready. There are no articles yet, and we will not fill this page with invented posts.
        </p>
      ) : null}
      {spec.path === "/resources/docs" ? (
        <p className="mx-auto max-w-site px-5 pb-8 text-slate-700 dark:text-slate-300">
          Architecture, API, runbook, and platform specifications live in the in-repo <code>docs/</code> folder.
          There is no separate public status page yet.
        </p>
      ) : null}
      {kind !== "pricing" && kind !== "paths" ? <BlockGrid spec={spec} /> : null}
      {kind === "demo-instructor" ? (
        <section className="mx-auto max-w-xl px-5 pb-16">
          <DemoForm variant="instructor" />
        </section>
      ) : null}
      {kind === "demo-enterprise" ? (
        <section className="mx-auto max-w-xl px-5 pb-16">
          <DemoForm variant="enterprise" />
        </section>
      ) : null}
      {kind === "contact" ? (
        <section className="mx-auto max-w-xl px-5 pb-16">
          <DemoForm variant="contact" />
        </section>
      ) : null}
      {kind === "standard" && spec.path === "/content-studio" ? (
        <p className="mx-auto max-w-site px-5 pb-16 text-sm text-slate-600 dark:text-slate-400">
          Staff with the role can open{" "}
          <a className="font-semibold text-[#1d4ed8]" href={studioUrl}>
            Content Studio
          </a>
          . The public cannot self-provision that access.
        </p>
      ) : null}
      <ClosingCta spec={spec} />
    </>
  );
}

function ClosingCta({ spec }: { spec: PageSpec }) {
  const primary = ctas[spec.cta];
  return (
    <section className="border-t border-slate-200 px-5 py-16 dark:border-slate-800">
      <div className="mx-auto max-w-site">
        <h2 className="font-display text-3xl tracking-tight">Start with a question, not a video</h2>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button href={primary.href}>{primary.label}</Button>
          {spec.secondary ? (
            <Button href={spec.secondary.href} variant="quiet">
              {spec.secondary.label}
            </Button>
          ) : (
            <Button href="/pricing" variant="quiet">
              See pricing
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}

function PricingBody({ spec }: { spec: PageSpec }) {
  const learnerPlans = [
    ["Studio / Free", "$0", "Fundamentals, Socratic tutor, flashcards."],
    ["Pro", "$29 / month", "Every track, coding lab, generated quizzes."],
    ["Research", "$79 / month", "Document upload and model critique when a provider is configured."],
  ];
  const orgPlans = [
    ["Classroom", "25–500 seats", "$48 / seat / year", "Card or invoice"],
    ["Campus", "500–50,000 seats", "$30 / seat / year", "Annual invoice"],
    ["Enterprise", "250+ seats", "$90 / seat / year", "Contract; white-label and residency add-ons"],
  ];
  const rows: [string, string, string, string, string, string, string][] = [
    ["Tutor", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"],
    ["All tracks", "Fundamentals", "Yes", "Yes", "Yes", "Yes", "Yes"],
    ["Lab", "No", "Yes", "Yes", "Yes", "Yes", "Yes"],
    ["Research critique", "No", "No", "When configured", "Talk to sales", "Talk to sales", "Talk to sales"],
    ["Cohorts", "No", "No", "No", "R3", "R3", "R3"],
    ["SSO", "No", "No", "No", "No", "R3–R4", "R3–R4"],
    ["Branding", "No", "No", "No", "No", "R3–R4", "R4"],
    ["SCIM", "No", "No", "No", "No", "No", "R4"],
    ["LTI", "No", "No", "No", "No", "R4", "R4"],
    ["Data residency", "No", "No", "No", "No", "No", "R4 add-on"],
    ["White-label", "No", "No", "No", "No", "No", "R4 add-on"],
  ];
  return (
    <>
      <section className="mx-auto max-w-site px-5 pb-12">
        <h2 className="font-display text-3xl tracking-tight">Learner plans</h2>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Checkout stays disabled until Stripe is configured. The buttons will say so, rather than pretend a
          charge happened.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {learnerPlans.map(([name, price, copy]) => (
            <article
              key={name}
              className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-lg font-semibold">{name}</h3>
              <p className="mt-2 font-display text-4xl">{price}</p>
              <p className="mt-3 text-slate-700 dark:text-slate-300">{copy}</p>
              <Button className="mt-6 w-full" disabled>
                Checkout is not configured yet
              </Button>
            </article>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 pb-12">
        <h2 className="font-display text-3xl tracking-tight">Organisation plans</h2>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Hypotheses from the PRD, labelled as such. No self-serve Classroom or Enterprise checkout. Instructor
          access is included in Classroom and above.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {orgPlans.map(([name, seats, price, billing]) => (
            <article
              key={name}
              className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-lg font-semibold">{name}</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{seats}</p>
              <p className="mt-2 font-display text-3xl">{price}</p>
              <p className="mt-3 text-slate-700 dark:text-slate-300">{billing}</p>
              <Button
                className="mt-6 w-full"
                href={name === "Classroom" ? "/demo/instructor" : "/demo/enterprise"}
              >
                {name === "Classroom" ? "Book instructor demo" : "Request enterprise demo"}
              </Button>
            </article>
          ))}
        </div>
        <p className="mt-6 text-sm text-slate-600 dark:text-slate-400">
          White label is an Enterprise add-on in R4. It is not a self-serve plan.
        </p>
      </section>
      <section className="mx-auto max-w-site px-5 pb-12">
        <h2 className="font-display text-3xl tracking-tight">Compare</h2>
        <div className="mt-6 overflow-x-auto">
          <table className="min-w-[52rem] border-collapse text-left text-sm">
            <thead>
              <tr>
                {["", "Free", "Pro", "Research", "Classroom", "Campus", "Enterprise"].map((head) => (
                  <th key={head} className="sticky top-0 border-b border-slate-200 bg-[var(--paper)] p-3 dark:border-slate-700">
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row[0]}>
                  {row.map((cell, index) => (
                    <td
                      key={`${row[0]}-${index}`}
                      className={`border-b border-slate-200 p-3 dark:border-slate-700 ${index === 0 ? "sticky left-0 bg-[var(--paper)] font-semibold" : ""}`}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="mx-auto max-w-site px-5 pb-12">
        <h2 className="font-display text-3xl tracking-tight">Illustrative arithmetic, not a guarantee</h2>
        <p className="mt-3 max-w-3xl text-slate-700 dark:text-slate-300">
          A Campus licence of 1,000 seats at the Band A hypothesis is $30,000 a year. Equivalent teaching-assistant
          hours at a conservative loaded cost are usually higher. That comparison is arithmetic, not a case study, and
          not a promise of savings.
        </p>
      </section>
      {spec.faqs ? (
        <section className="mx-auto max-w-3xl px-5 pb-16">
          <h2 className="font-display text-3xl tracking-tight">Billing questions</h2>
          <div className="mt-6">
            <FaqAccordion items={spec.faqs} />
          </div>
        </section>
      ) : null}
    </>
  );
}

async function PathsBody() {
  const [curriculum, stats] = await Promise.all([curriculumPaths(), catalogStats()]);
  return (
    <section className="mx-auto max-w-site px-5 pb-16">
      <h2 className="font-display text-3xl tracking-tight">v1 curriculum</h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {(curriculum && curriculum.length > 0
          ? curriculum.map((path) => ({
              slug: path.slug,
              title: path.title,
              difficulty: path.level,
              outcome: path.description,
            }))
          : v1Tracks
        ).map((path) => (
          <article
            key={path.slug}
            className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-[#6d28d9]">{path.difficulty}</p>
            <h3 className="mt-2 text-xl font-semibold">{path.title}</h3>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{path.outcome}</p>
            <Button className="mt-5" href={learnerPath(path.slug)}>
              Start this path
            </Button>
          </article>
        ))}
      </div>
      {stats && stats.pack_paths.length > 0 ? (
        <>
          <h2 className="mt-14 font-display text-3xl tracking-tight">Knowledge Pack paths</h2>
          <p className="mt-2 text-slate-700 dark:text-slate-300">{stats.note}</p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {stats.pack_paths.map((path) => (
              <article
                key={path.slug}
                className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
              >
                <p className="text-xs font-semibold uppercase tracking-wide text-[#6d28d9]">{path.difficulty}</p>
                <h3 className="mt-2 text-xl font-semibold">{path.title}</h3>
                <p className="mt-2 text-slate-700 dark:text-slate-300">{path.description}</p>
                {path.estimated_minutes ? (
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                    About {path.estimated_minutes} minutes
                  </p>
                ) : null}
                <Button className="mt-5" href={`${learnerUrl}/catalog`}>
                  Open in the Learner App
                </Button>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

async function LeaderboardPreview() {
  const board = await publicLeaderboard();
  if (!board || board.length === 0) return null;
  return (
    <section className="mx-auto max-w-site px-5 pb-12">
      <h2 className="font-display text-3xl tracking-tight">Public board</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
        Public board. Staff and opted-out learners are excluded.
      </p>
      <ol className="mt-6 divide-y divide-slate-200 rounded-3xl border border-slate-200 bg-white dark:divide-slate-700 dark:border-slate-700 dark:bg-slate-900">
        {board.map((row) => (
          <li key={row.rank} className="flex items-center justify-between px-5 py-3">
            <span>
              {row.rank}. {row.display_name}
            </span>
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {row.xp} XP · level {row.level} · {row.streak_days} day streak
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

async function FaqBody() {
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  const items = faqGroups.flatMap((group) => group.items);
  const schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map(([question, answer]) => ({
      "@type": "Question",
      name: question,
      acceptedAnswer: { "@type": "Answer", text: answer },
    })),
  };
  return (
    <section className="mx-auto max-w-3xl px-5 pb-16">
      <script
        nonce={nonce}
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />
      {faqGroups.map((group) => (
        <div key={group.heading} className="mb-10">
          <h2 className="font-display text-2xl tracking-tight">{group.heading}</h2>
          <div className="mt-4">
            <FaqAccordion items={group.items} />
          </div>
        </div>
      ))}
    </section>
  );
}
