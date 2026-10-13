export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-slate-200 bg-white px-5 py-12 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
      <div className="mx-auto grid max-w-site gap-8 md:grid-cols-5">
        <div className="md:col-span-1">
          <p className="font-display text-xl text-slate-900 dark:text-slate-100">AI Mentor</p>
          <p className="mt-2">From first Python to publishable research.</p>
          <p className="mt-3" aria-label="Language. English is available now.">
            en · fr · es
          </p>
        </div>
        <FooterColumn
          title="Product"
          links={[
            ["/platform/tutor", "Tutor"],
            ["/paths", "Paths"],
            ["/platform/lab", "Lab"],
            ["/platform/research", "Research"],
            ["/platform/gamification", "Gamification"],
            ["/content-studio", "Content Studio"],
            ["/pricing", "Pricing"],
          ]}
        />
        <FooterColumn
          title="Solutions"
          links={[
            ["/solutions/learners", "Learners"],
            ["/solutions/instructors", "Instructors"],
            ["/solutions/universities", "Universities"],
            ["/solutions/schools", "Schools"],
            ["/solutions/bootcamps", "Bootcamps"],
            ["/solutions/corporates", "Corporates"],
          ]}
        />
        <FooterColumn
          title="Resources"
          links={[
            ["/resources/blog", "Blog"],
            ["/resources/guides", "Guides"],
            ["/resources/faq", "FAQ"],
            ["/resources/docs", "Docs"],
          ]}
        />
        <FooterColumn
          title="Company"
          links={[
            ["/company/about", "About"],
            ["/company/careers", "Careers"],
            ["/company/contact", "Contact"],
            ["/company/partners", "Partners"],
            ["/legal/privacy", "Privacy"],
            ["/legal/terms", "Terms"],
          ]}
        />
      </div>
      <div className="mx-auto mt-10 flex max-w-site flex-wrap justify-between gap-3 border-t border-slate-200 pt-6 dark:border-slate-800">
        <p>© {year} AI Mentor</p>
        <p>16 and over. Not an awarding body.</p>
      </div>
    </footer>
  );
}

function FooterColumn({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <div>
      <p className="font-semibold text-slate-900 dark:text-slate-100">{title}</p>
      <ul className="mt-3 space-y-2">
        {links.map(([href, label]) => (
          <li key={href}>
            <a className="hover:text-[#1d4ed8]" href={href}>
              {label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
