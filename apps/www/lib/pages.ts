import type { CtaKind } from "@/lib/urls";

export type Block = {
  title: string;
  body: string;
  badge?: string;
  href?: string;
};

export type PageKind =
  | "standard"
  | "demo-instructor"
  | "demo-enterprise"
  | "contact"
  | "faq"
  | "pricing"
  | "paths"
  | "gamification"
  | "resources"
  | "legal"
  | "blog"
  | "about";

export type PageSpec = {
  path: string;
  title: string;
  description: string;
  eyebrow?: string;
  headline: string;
  subheading: string;
  cta: CtaKind;
  secondary?: { label: string; href: string };
  blocks: Block[];
  kind?: PageKind;
  faqs?: [string, string][];
  legal?: string[];
};

export const platformMega: { href: string; title: string; line: string }[] = [
  { href: "/platform/tutor", title: "AI Tutor", line: "Asks first. Explains after you have tried" },
  { href: "/paths", title: "Learning paths", line: "Prerequisites on a graph, not a pile of videos" },
  { href: "/platform/lab", title: "Coding lab", line: "Short-lived Python with an allowlist" },
  { href: "/platform/research", title: "Research assistant", line: "Quotes your PDF. Will not invent a paper" },
  { href: "/platform/gamification", title: "Gamification", line: "XP for mastery, not for clicks" },
  { href: "/platform/assessments", title: "Assessments", line: "Practice now. Summative marking from R3" },
  { href: "/platform/analytics", title: "Analytics", line: "Mastery for you. Org reports from R3" },
  { href: "/content-studio", title: "Content Studio", line: "The repository everyone else consumes" },
];

export const solutionsMega: { href: string; title: string; line: string }[] = [
  { href: "/solutions/learners", title: "Learners", line: "Personal tutor from beginner to research" },
  { href: "/solutions/instructors", title: "Instructors", line: "Cohorts, marking, intervention (pilots)" },
  { href: "/solutions/universities", title: "Universities", line: "Seats, SSO, reports" },
  { href: "/solutions/schools", title: "Schools", line: "16+ programmes only" },
  { href: "/solutions/bootcamps", title: "Bootcamps", line: "Pinned releases for a cohort" },
  { href: "/solutions/corporates", title: "Corporates", line: "Role paths and workforce reports" },
];

export const resourceLinks: { href: string; title: string }[] = [
  { href: "/resources/blog", title: "Blog" },
  { href: "/resources/guides", title: "Guides" },
  { href: "/resources/faq", title: "FAQ" },
  { href: "/resources/docs", title: "Docs" },
];

export const v1Tracks: { slug: string; title: string; difficulty: string; outcome: string }[] = [
  {
    slug: "ai-fundamentals",
    title: "AI Fundamentals",
    difficulty: "Beginner",
    outcome: "Rules versus learning, then the maths later tracks assume",
  },
  {
    slug: "reinforcement-learning",
    title: "Reinforcement Learning",
    difficulty: "Intermediate",
    outcome: "Agent loop through Bellman, Q-learning, PPO, SAC",
  },
  {
    slug: "robotics",
    title: "Robotics",
    difficulty: "Intermediate",
    outcome: "ROS 2, vision, SLAM, navigation, when a policy may touch a motor",
  },
  {
    slug: "llm-engineering",
    title: "LLM Engineering",
    difficulty: "Intermediate",
    outcome: "Grounded systems and research habits",
  },
];

export const homeFaqs: [string, string][] = [
  [
    "Does the tutor give the answer immediately?",
    "Not in Socratic mode. The first turns ask you to retrieve the idea. Direct mode is one switch away.",
  ],
  [
    "Can it review a PDF?",
    "Yes. Text is extracted, chunked, and cited. If no model is connected, the critique is withheld instead of being guessed.",
  ],
  [
    "Is the coding lab a general Python sandbox?",
    "No. It runs a short-lived interpreter with a small module allowlist, a timeout, and no file or network access. It is not a microVM.",
  ],
  [
    "Is this an LMS?",
    "No. We teach, assess, and keep a learning record. LMS integration (LTI) is planned for organisations; we are not your SIS.",
  ],
  ["Is it for children?", "AI Mentor is for people 16 and over. There is no K-12 or under-16 product."],
];

export const faqGroups: { heading: string; items: [string, string][] }[] = [
  { heading: "Platform", items: homeFaqs },
  {
    heading: "Pricing",
    items: [
      [
        "What do Free, Pro, and Research include?",
        "Studio/Free covers fundamentals, the Socratic tutor, and flashcards. Pro adds every track, the coding lab, and generated quizzes. Research adds document upload and model critique when a provider is configured. Checkout stays disabled until Stripe is configured.",
      ],
      [
        "How do seats work?",
        "One learner, one seat. A consumer subscription can be paused while the learner is on an organisation seat. Classroom, Campus, and Enterprise prices are hypotheses until those plans are sold.",
      ],
    ],
  },
  {
    heading: "Tutoring",
    items: [
      [
        "Can I switch to direct answers?",
        "Yes. Socratic mode is the default. Direct mode is one switch. Off-topic work is refused. Sources are cited.",
      ],
      ["Does the tutor speak other languages?", "The product supports English, French, and Spanish locales."],
    ],
  },
  {
    heading: "Institutions",
    items: [
      [
        "Does an Instructor App login appear after I request a demo?",
        "No. A person grants the role. The form creates a sales lead only.",
      ],
      [
        "When is SSO available?",
        "SSO, branding, and LMS integration are R3–R4 for Campus and Enterprise. They are not self-serve today.",
      ],
    ],
  },
  {
    heading: "Research",
    items: [
      [
        "Will it invent a paper?",
        "Uploaded documents are quoted. A critique appears only when a model is configured and a citation supports it. Otherwise the critique is withheld.",
      ],
    ],
  },
  {
    heading: "Privacy",
    items: [
      [
        "Where does my data live?",
        "See the privacy and security documents. Data residency is an R4 Enterprise add-on, not a default today.",
      ],
      [
        "Can I export my learning record?",
        "Yes. Signed-in learners can call GET /me/export from the Learner App account screen.",
      ],
    ],
  },
  {
    heading: "Security",
    items: [
      [
        "Who sees the leaderboard?",
        "A pseudonymous public top 10. Staff and opted-out learners are excluded. No real names or emails.",
      ],
    ],
  },
  {
    heading: "Certifications",
    items: [
      [
        "Do you confer degrees or vendor certificates?",
        "No. We record mastery, labs, and reviews. Open Badges and employer-recognised certificates need partners. We are not an awarding body.",
      ],
      ["Are answer keys in the Learner App?", "No. Answer keys and hidden tests stay on the server."],
    ],
  },
];

export const pages: Record<string, PageSpec> = {
  platform: {
    path: "/platform",
    title: "Platform | AI Mentor",
    description:
      "A Socratic tutor, a knowledge graph, a restricted lab, a research desk, and the apps that govern them.",
    headline: "The ecosystem, in one place",
    subheading:
      "A Socratic tutor, a knowledge graph, a restricted lab, a research desk, and the apps that govern them.",
    cta: "learner",
    secondary: { label: "Request enterprise demo", href: "/demo/enterprise" },
    blocks: [
      {
        title: "AI Tutor",
        body: "Socratic mode asks first. Direct mode is one switch. Off-topic work is refused and sources are cited.",
        badge: "Available now",
        href: "/platform/tutor",
      },
      {
        title: "Learning engine",
        body: "Four v1 tracks plus Knowledge Pack paths. The graph repairs weak foundations before it recommends the next concept.",
        badge: "Available now",
        href: "/paths",
      },
      {
        title: "Research assistant",
        body: "Uploads are quoted. Critique appears only when a model and a citation support it.",
        badge: "Available now",
        href: "/platform/research",
      },
      {
        title: "Coding lab",
        body: "A short-lived Python interpreter with a module allowlist, a timeout, and no file or network access.",
        badge: "Available now",
        href: "/platform/lab",
      },
      {
        title: "Knowledge repository",
        body: "Published catalog assets, not drafts. Learners never see a review queue.",
        badge: "Available now",
        href: "/content-studio",
      },
      {
        title: "Content Studio",
        body: "Authors, reviewers, and publishers work here. Four-eyes publishing. Staff sign-in only.",
        badge: "Available now",
        href: "/content-studio",
      },
      {
        title: "Gamification",
        body: "XP for mastery, passing labs, and finished reviews. Daily cap 400. Never for clicks.",
        badge: "Available now",
        href: "/platform/gamification",
      },
      {
        title: "Leaderboards",
        body: "Public pseudonymous top 10. Staff and opted-out learners are excluded.",
        badge: "Available now",
        href: "/platform/gamification",
      },
      {
        title: "Assessment",
        body: "Practice quizzes and a question bank today. Cohort marking with human release from R3.",
        badge: "R3",
        href: "/platform/assessments",
      },
      {
        title: "Analytics",
        body: "Learners see mastery bands now. Organisation dashboards a dean can read follow in R3.",
        badge: "Split",
        href: "/platform/analytics",
      },
    ],
  },
  "platform/tutor": {
    path: "/platform/tutor",
    title: "AI Tutor | AI Mentor",
    description:
      "Socratic and direct modes, grounded in reviewed content. The tutor checks you understand before it moves on.",
    headline: "It asks first",
    subheading: "Socratic mode is the default. Direct mode is one switch. Off-topic work is refused. Sources are cited.",
    cta: "learner",
    secondary: { label: "See pricing", href: "/pricing" },
    blocks: [
      {
        title: "Modes",
        body: "Socratic turns retrieve the idea before the explanation. Direct mode answers more quickly when you ask for it.",
        badge: "Available now",
      },
      {
        title: "Personalisation",
        body: "Style, depth, and locale are under your control. The catalog still decides prerequisites.",
        badge: "Available now",
      },
      {
        title: "Research mentor",
        body: "Paper notes stay tied to pages you uploaded. Critique is withheld when no model or citation is available.",
        badge: "Available now",
      },
      {
        title: "Coding mentor",
        body: "Lab reviews name missing loops and allowlisted modules. The session is not a general IDE.",
        badge: "Available now",
      },
      {
        title: "Career coach",
        body: "Role readiness from the mastery map. A fuller career planner is on the roadmap.",
        badge: "Roadmap",
      },
      {
        title: "Languages",
        body: "English, French, and Spanish locales. Safety and grounding rules are the same in each.",
        badge: "Available now",
      },
      {
        title: "Voice",
        body: "A spoken tutor is on the roadmap. It is not in the product today.",
        badge: "Roadmap",
      },
    ],
  },
  "platform/lab": {
    path: "/platform/lab",
    title: "Coding lab | AI Mentor",
    description: "A restricted Python lab with an allowlist, a timeout, and no file or network access.",
    headline: "A lab, not a sandbox in the sky",
    subheading:
      "It runs a short-lived interpreter with a small module allowlist, a timeout, and no file or network access. It is not a microVM.",
    cta: "learner",
    secondary: { label: "See pricing", href: "/pricing" },
    blocks: [
      {
        title: "Allowlist",
        body: "Only approved modules load. Hidden tests and reference solutions never reach the Learner App.",
        badge: "Available now",
      },
      {
        title: "Timeout",
        body: "Runs are short. The lab is for one step of an algorithm, not a training job.",
        badge: "Available now",
      },
      {
        title: "Review",
        body: "A written review names what the code missed. Passing a challenge grants XP once.",
        badge: "Available now",
      },
      {
        title: "Production",
        body: "The lab stays off in production until learner code runs in an isolated, secret-free, network-less runner.",
        badge: "Ops",
      },
    ],
  },
  "platform/research": {
    path: "/platform/research",
    title: "Research assistant | AI Mentor",
    description: "Uploads are quoted. Critique appears only when a model and a citation support it.",
    headline: "Read papers without inventing them",
    subheading: "Uploaded documents are quoted. A critique appears only when a citation supports it.",
    cta: "learner",
    secondary: { label: "See pricing", href: "/pricing" },
    blocks: [
      {
        title: "Uploads",
        body: "PDF, DOCX, Markdown, or text, up to 10 MB. Text is extracted, chunked, and cited.",
        badge: "Available now",
      },
      {
        title: "Extractive notes",
        body: "If no model is connected, the critique is withheld instead of being guessed.",
        badge: "Available now",
      },
      {
        title: "Research plan",
        body: "Document critique on the Research plan when a provider is configured. Checkout is not configured yet.",
        badge: "Research",
      },
    ],
  },
  "platform/gamification": {
    path: "/platform/gamification",
    title: "Gamification | AI Mentor",
    description: "XP for mastery, passing labs, and finished reviews. Daily cap 400. Never for clicks.",
    headline: "Fun that serves learning",
    subheading: "XP for mastery, passing labs, and finished reviews. Daily cap 400. Never for clicks.",
    cta: "learner",
    kind: "gamification",
    blocks: [
      {
        title: "XP and levels",
        body: "Lessons, quizzes, projects, reviews, and analyses pay once. Level is 1 + xp ÷ 250. Chat updates the streak and does not grant XP.",
        badge: "Available now",
      },
      {
        title: "Streaks",
        body: "A streak rewards understanding across days, not a tap on a notification.",
        badge: "Available now",
      },
      {
        title: "Leaderboards",
        body: "Public board. Staff and opted-out learners are excluded. Handles or stable pseudonyms only.",
        badge: "Available now",
      },
      {
        title: "Challenges",
        body: "Daily coding challenges on published specs. Hidden tests stay on the server.",
        badge: "Available now",
      },
      {
        title: "Seasonal competitions",
        body: "Cohort boards and seasons are R2–R3. The global board is live.",
        badge: "R2–R3",
      },
    ],
  },
  "platform/assessments": {
    path: "/platform/assessments",
    title: "Assessments | AI Mentor",
    description: "Practice quizzes today. Cohort assessments with human-released marks from R3.",
    headline: "Practice that counts",
    subheading: "Authored items, graded on the server. Answer keys never reach the client. Summative cohort marking is R3.",
    cta: "instructor",
    secondary: { label: "Start learning free", href: "/start" },
    blocks: [
      {
        title: "Practice quizzes",
        body: "Generated from the question bank. Graded on the server. The key is not in the quiz payload.",
        badge: "Available now",
      },
      {
        title: "Item bank",
        body: "Authors and reviewers work in Content Studio. AI drafts stay in review until a person publishes.",
        badge: "Available now",
      },
      {
        title: "AI marking",
        body: "AI can propose a mark. A named human releases it. Proposed marks are not shown to learners first, except for objectively auto-graded items.",
        badge: "Pilots from R3",
      },
    ],
  },
  "platform/analytics": {
    path: "/platform/analytics",
    title: "Analytics | AI Mentor",
    description: "Learners see mastery bands now. Organisation reports follow from R3.",
    headline: "Evidence, not a vanity dashboard",
    subheading: "Learners keep a mastery record today. Instructors and institutions get cohort reports from R3.",
    cta: "learner",
    secondary: { label: "Request enterprise demo", href: "/demo/enterprise" },
    blocks: [
      {
        title: "Learner progress",
        body: "Mastery bands, path completion, XP, streaks, and recommendations on the dashboard.",
        badge: "Available now",
      },
      {
        title: "Instructor insights",
        body: "Who is stuck, which prerequisites failed, and where to intervene. Pilots from R3.",
        badge: "Pilots from R3",
      },
      {
        title: "Organisation reports",
        body: "Seats, coverage, and evidence a dean can read. Not self-serve today.",
        badge: "R3",
      },
    ],
  },
  "solutions/learners": {
    path: "/solutions/learners",
    title: "For learners | AI Mentor",
    description: "Personal paths, a coach that will not skip prerequisites, practice, and a research desk.",
    headline: "A private tutor that already knows the syllabus",
    subheading:
      "Personal paths, a coach that will not skip prerequisites, practice at the right difficulty, and a research desk when you need papers.",
    cta: "learner",
    secondary: { label: "Explore paths", href: "/paths" },
    blocks: [
      {
        title: "Personalised learning",
        body: "Style, depth, and locale are yours. The graph still refuses to skip the Bellman equation.",
        badge: "Available now",
      },
      {
        title: "Paths",
        body: "Four v1 tracks plus Knowledge Pack paths. Weak foundations are repaired first.",
        badge: "Available now",
      },
      {
        title: "AI coach",
        body: "Socratic by default. Direct on one switch. Cited, governed sources.",
        badge: "Available now",
      },
      {
        title: "Career roadmaps",
        body: "Role readiness from mastery today. A fuller career planner is labelled on the roadmap.",
        badge: "Roadmap",
      },
      {
        title: "Progress",
        body: "Mastery bands, not a percentage of videos watched.",
        badge: "Available now",
      },
      {
        title: "Daily challenges",
        body: "Coding specs with hidden tests. XP once per passing review.",
        badge: "Available now",
      },
      {
        title: "Badges",
        body: "Achievements for mastery and completed reviews. Open Badges need partners later.",
        badge: "Available now",
      },
      {
        title: "Competitions",
        body: "Global leaderboard now. Cohort and seasonal boards from R2–R3.",
        badge: "Split",
      },
      {
        title: "Research assistant",
        body: "Quote the upload. Withhold the critique when the text does not support it.",
        badge: "Available now",
      },
    ],
  },
  "solutions/instructors": {
    path: "/solutions/instructors",
    title: "For instructors | AI Mentor",
    description: "Versioned AI curricula, scheduled journeys, and marks you release. Pilots from R3.",
    headline: "Teach the cohort. Let the tutor handle the 1:1",
    subheading: "Versioned AI curricula, scheduled journeys, and marks you release. Pilots from R3.",
    cta: "instructor",
    secondary: { label: "Start learning free", href: "/start" },
    blocks: [
      {
        title: "Learner management",
        body: "See who is on the path and who stalled on a prerequisite. The Instructor App exists; classroom workflows still follow the roadmap.",
        badge: "Pilots from R3",
      },
      {
        title: "Cohorts",
        body: "Pin a cohort to a Content Studio release so every learner sees the same version.",
        badge: "Pilots from R3",
      },
      {
        title: "Assessment creation",
        body: "Draw from the item bank. Keys stay off the client.",
        badge: "Pilots from R3",
      },
      {
        title: "AI marking",
        body: "AI proposes. You accept or override. Learners do not see a proposed mark first.",
        badge: "Pilots from R3",
      },
      {
        title: "Scheduling",
        body: "Journeys with dates, not an endless feed.",
        badge: "Pilots from R3",
      },
      {
        title: "Analytics and communication",
        body: "Risk signals with evidence, then a message to the learner who needs it.",
        badge: "Pilots from R3",
      },
    ],
  },
  "solutions/universities": {
    path: "/solutions/universities",
    title: "AI curriculum for universities | AI Mentor",
    description: "Seats, SSO, reports, and a tutor for every learner. Humans release grades.",
    headline: "Every learner gets a tutor. You keep control",
    subheading:
      "Seats, reporting, and (from R3–R4) SSO, branding, and LMS integration. We are not your SIS.",
    cta: "enterprise",
    secondary: { label: "See pricing", href: "/pricing" },
    blocks: [
      {
        title: "Dashboard",
        body: "The Institution App exists as a shell. Organisation APIs and classroom features still follow the roadmap.",
        badge: "Pilots from R3",
      },
      {
        title: "Reporting",
        body: "Evidence a dean can read: seats, coverage, completion. Not a second SIS.",
        badge: "R3",
      },
      {
        title: "Branding and SSO",
        body: "Campus and Enterprise add-ons from R3–R4. Not self-serve checkout today.",
        badge: "R3–R4",
      },
      {
        title: "Compliance",
        body: "Human control over grades. Four-eyes publishing. A DPA when we sell Enterprise.",
        badge: "Talk to sales",
      },
      {
        title: "Student success",
        body: "The tutor handles 1:1. Instructors intervene on named gaps.",
        badge: "R3",
      },
    ],
  },
  "solutions/schools": {
    path: "/solutions/schools",
    title: "16+ school programmes | AI Mentor",
    description: "Sixth-form and 16+ college programmes. There is no under-16 product.",
    headline: "Sixth-form and 16+ college programmes",
    subheading: "AI Mentor is for people 16 and over. There is no K-12 or children's product.",
    cta: "enterprise",
    secondary: { label: "See pricing", href: "/pricing" },
    blocks: [
      {
        title: "Age",
        body: "Programmes for 16+ only. Safeguarding work is required before any under-16 discussion.",
        badge: "16 and over",
      },
      {
        title: "Curriculum",
        body: "The same governed AI paths as adult learners, with seats and (later) SSO.",
        badge: "R3",
      },
      {
        title: "Teachers",
        body: "Instructors keep control of grades. The tutor does not replace the teacher.",
        badge: "Pilots from R3",
      },
    ],
  },
  "solutions/bootcamps": {
    path: "/solutions/bootcamps",
    title: "AI bootcamp platform | AI Mentor",
    description: "Pinned releases, enrolment codes, and a Classroom plan for cohorts.",
    headline: "Run a cohort on a pinned release",
    subheading: "Enrolment codes, cohort leaderboards, and a Classroom plan. Instructor workflows are pilots from R3.",
    cta: "instructor",
    secondary: { label: "Start learning free", href: "/start" },
    blocks: [
      {
        title: "Pinned releases",
        body: "A cohort stays on the Content Studio version you chose. Fixes reach you when you accept them.",
        badge: "Pilots from R3",
      },
      {
        title: "Classroom plan",
        body: "25–500 seats. Price is a hypothesis until we sell it. Book a demo; there is no self-serve Classroom checkout.",
        badge: "Talk to sales",
      },
      {
        title: "Leaderboards",
        body: "The global board is live. Cohort boards are R2–R3.",
        badge: "Split",
      },
    ],
  },
  "solutions/corporates": {
    path: "/solutions/corporates",
    title: "Workforce AI learning | AI Mentor",
    description: "Role paths, team skills coverage, and Enterprise SSO/SCIM from R3–R4.",
    headline: "Close named skill gaps",
    subheading: "Role paths and workforce reports. SSO and SCIM are Enterprise add-ons from R3–R4.",
    cta: "enterprise",
    secondary: { label: "See pricing", href: "/pricing" },
    blocks: [
      {
        title: "Role paths",
        body: "ML Engineer, Data Scientist, and neighbouring Knowledge Pack paths mapped to the graph.",
        badge: "Available now",
      },
      {
        title: "Workforce reports",
        body: "Coverage and mastery by team, not a completion percentage of videos.",
        badge: "R3",
      },
      {
        title: "SSO and SCIM",
        body: "Enterprise from R3–R4. Not a self-serve switch.",
        badge: "R3–R4",
      },
    ],
  },
  "content-studio": {
    path: "/content-studio",
    title: "Content Studio | AI Mentor",
    description: "Authors, reviewers, and publishers work in Content Studio. Learners never see a draft.",
    headline: "One repository. Many classrooms",
    subheading:
      "Authors, reviewers, and publishers work in Content Studio. Instructors consume releases. Learners never see a draft.",
    cta: "studio",
    secondary: { label: "Read the knowledge catalog", href: "/resources/docs" },
    blocks: [
      {
        title: "Knowledge repository",
        body: "The Knowledge Pack and published catalog. Live counts sit on the public proof bar, not invented MAU.",
        badge: "Available now",
      },
      {
        title: "Curriculum builder",
        body: "Paths, modules, and estimated minutes. Instructors pin a release rather than forking the graph.",
        badge: "Available now",
      },
      {
        title: "Knowledge graph",
        body: "Prerequisite edges stay acyclic and reviewed. Weak foundations are repaired first.",
        badge: "Available now",
      },
      {
        title: "Item bank",
        body: "Questions and coding challenges. Keys and hidden tests never appear in learner screenshots or APIs.",
        badge: "Available now",
      },
      {
        title: "Four-eyes publishing",
        body: "AI drafts stay in review. A person other than the author publishes, unless self-approval is explicitly flagged.",
        badge: "Available now",
      },
      {
        title: "Staff only",
        body: "The public cannot self-provision a Studio admin. Sign-in is for people who already have the role.",
        badge: "Staff",
      },
    ],
  },
  certifications: {
    path: "/certifications",
    title: "Mastery evidence | AI Mentor",
    description: "We record mastery, labs, and reviews. We do not confer degrees.",
    headline: "Evidence of skill, not a diploma mill",
    subheading:
      "We record mastery, labs, and reviews. Open Badges and employer-recognised certificates need partners. We do not confer degrees.",
    cta: "learner",
    secondary: { label: "Talk to partnerships", href: "/company/partners" },
    blocks: [
      {
        title: "Pathways",
        body: "AI, ML, RL, and Robotics as learning pathways, not accredited certificates.",
        badge: "Available now",
      },
      {
        title: "Assessment",
        body: "Practice now. Summative cohort assessment from R3.",
        badge: "Split",
      },
      {
        title: "Digital badges",
        body: "Open Badges 3.0 is a principle. Issuing them needs partners (R5).",
        badge: "R5",
      },
      {
        title: "Employer recognition",
        body: "None yet. We will not invent logos or testimonials.",
        badge: "Honest",
      },
    ],
  },
  pricing: {
    path: "/pricing",
    title: "Pricing | AI Mentor",
    description: "Free, Pro, and Research for learners. Classroom, Campus, and Enterprise for organisations.",
    headline: "Start free. Pay when the lab and the papers matter",
    subheading:
      "Learner plans use the names that already ship. Organisation prices are hypotheses from the PRD until we sell them.",
    cta: "learner",
    kind: "pricing",
    faqs: [
      [
        "Is checkout live?",
        "Checkout stays disabled until Stripe is configured. Buttons say so rather than pretend a charge happened.",
      ],
      ["How do seats relate to enrolments?", "One learner, one seat. Enrolment in several paths still uses one seat."],
      [
        "Can I pause Pro while on a campus seat?",
        "Yes, that is the intended rule. The Institution App will enforce it when seat licences ship.",
      ],
      ["Is this for children?", "No. Students must be 16 and over."],
    ],
    blocks: [],
  },
  paths: {
    path: "/paths",
    title: "Learning paths | AI Mentor",
    description: "Tracks with prerequisites, not a pile of videos. Four v1 curricula plus Knowledge Pack paths.",
    headline: "Tracks with prerequisites, not a pile of videos",
    subheading: "The graph decides what you are ready for. Weak foundations are repaired first.",
    cta: "learner",
    kind: "paths",
    blocks: [],
  },
  resources: {
    path: "/resources",
    title: "Resources | AI Mentor",
    description: "Notes from the same catalog we teach. FAQ, docs, and a blog when we publish.",
    headline: "Notes from the same catalog we teach",
    subheading: "FAQ and docs first. Articles appear here when we publish them. We do not invent reports.",
    cta: "learner",
    kind: "resources",
    blocks: [
      { title: "FAQ", body: "Platform, pricing, tutoring, institutions, research, privacy, security, certifications.", href: "/resources/faq" },
      { title: "Docs", body: "Architecture, API, runbook, and platform specifications in the repository.", href: "/resources/docs" },
      { title: "Guides", body: "How the tutor, lab, and catalog actually behave. No thin listicles.", href: "/resources/guides" },
      { title: "Blog", body: "Curriculum, tutor design, research notes, engineering, teaching, policy. Empty until we publish.", href: "/resources/blog" },
      { title: "Learning hub", body: "Public excerpts that already exist as catalog pages on the Learner App.", href: "/resources/hub" },
    ],
  },
  "resources/blog": {
    path: "/resources/blog",
    title: "Blog | AI Mentor",
    description: "Curriculum, tutor design, research notes, engineering, teaching, and policy. Published pieces only.",
    headline: "Writing from the same catalog",
    subheading:
      "No articles yet. We will not invent research summaries or a top-10 tools list. Until then, read the FAQ and the docs.",
    cta: "learner",
    kind: "blog",
    secondary: { label: "Read the FAQ", href: "/resources/faq" },
    blocks: [
      { title: "Curriculum", body: "How paths and the graph are built." },
      { title: "Tutor design", body: "Why the first reply is a question." },
      { title: "Research notes", body: "Only with citations. No invented papers." },
      { title: "Engineering", body: "Lab, retrieval, and the five apps." },
      { title: "Teaching", body: "Cohorts and human-released marks (from R3)." },
      { title: "Policy", body: "Privacy, 16+, and what we will not claim." },
    ],
  },
  "resources/guides": {
    path: "/resources/guides",
    title: "Guides | AI Mentor",
    description: "How the tutor, lab, and catalog behave in production today.",
    headline: "How it actually works",
    subheading: "Short guides for the behaviour that already ships. No fake webinars or industry reports.",
    cta: "learner",
    blocks: [
      { title: "Start with the tutor", body: "Socratic mode, Direct mode, and what off-topic means.", href: "/platform/tutor" },
      { title: "Pick a path", body: "Four v1 tracks and Knowledge Pack titles.", href: "/paths" },
      { title: "Use the lab", body: "Allowlist, timeout, no network.", href: "/platform/lab" },
      { title: "Read a paper", body: "Upload, cite, withhold when unsupported.", href: "/platform/research" },
    ],
  },
  "resources/hub": {
    path: "/resources/hub",
    title: "Learning hub | AI Mentor",
    description: "Public excerpts of the catalog. Signed-in catalogue pages live on the Learner App.",
    headline: "Public excerpts, then the Learner App",
    subheading: "The marketing /paths page is curated. The signed-in catalog stays on learn.",
    cta: "learner",
    secondary: { label: "Explore paths", href: "/paths" },
    blocks: [
      { title: "Curriculum tracks", body: "AI Fundamentals, RL, Robotics, LLM Engineering.", href: "/paths" },
      { title: "Knowledge Pack", body: "Live published counts on the home proof bar.", href: "/" },
    ],
  },
  "resources/docs": {
    path: "/resources/docs",
    title: "Docs | AI Mentor",
    description: "Architecture, API, runbook, and platform specifications.",
    headline: "The documents we run from",
    subheading: "Platform specs, the API contract, and the runbook live in the repository. Staff apps are not indexed.",
    cta: "learner",
    blocks: [
      { title: "Platform specification", body: "Five apps, tenancy, and the public website spec." },
      { title: "API", body: "OpenAPI plus the narrative guide. Public routes include catalog stats and leads." },
      { title: "Knowledge catalog", body: "What learners search and what Studio publishes." },
      { title: "Security", body: "CSP, rate limits, and production guards. Residency is an R4 add-on." },
    ],
  },
  "resources/faq": {
    path: "/resources/faq",
    title: "FAQ | AI Mentor",
    description: "Answers on the tutor, lab, pricing, institutions, privacy, and certifications.",
    headline: "Questions we already have answers for",
    subheading: "Present tense for shipped behaviour. Future tense for R3–R5.",
    cta: "learner",
    kind: "faq",
    blocks: [],
  },
  "company/about": {
    path: "/company/about",
    title: "About | AI Mentor",
    description: "A private tutor, and the tools for the teachers and organisations around it.",
    headline:
      "Give every person a world-class private tutor — and give their teachers the tools to govern it",
    subheading:
      "Help anyone progress from complete beginner to industry professional, researcher, or PhD-level expert in AI and neighbouring disciplines.",
    cta: "learner",
    kind: "about",
    secondary: { label: "Contact", href: "/company/contact" },
    blocks: [
      {
        title: "Understanding before answers",
        body: "The tutor asks and checks before it gives the full solution. Progress is earned.",
      },
      {
        title: "Grounded, not guessed",
        body: "Published, reviewed content, cited. When it does not know, it says so.",
      },
      {
        title: "Humans decide high-stakes outcomes",
        body: "AI proposes grades, risk flags, and content. A named person accepts, overrides, or publishes.",
      },
      {
        title: "The learner owns their record",
        body: "Mastery, XP, and achievements follow the person. Organisations see what was consented and assigned.",
      },
      {
        title: "One platform, many apps",
        body: "Learner, Instructor, Institution, Admin, and Content Studio. Rules live in the API.",
      },
      {
        title: "Access",
        body: "Three languages, regional pricing, 16 and over. Not a K-12 charity claim.",
      },
    ],
  },
  "company/careers": {
    path: "/company/careers",
    title: "Careers | AI Mentor",
    description: "No open roles listed yet. Contact if you teach, write, or operate AI curricula.",
    headline: "Work on the catalog and the tutor",
    subheading: "We do not invent job listings. When a role is open, it will be here with a real description.",
    cta: "studio",
    secondary: { label: "Contact", href: "/company/contact" },
    blocks: [
      { title: "Content", body: "Authors, reviewers, and knowledge stewards in Content Studio." },
      { title: "Teaching", body: "People who can run a cohort once Instructor workflows ship." },
      { title: "Platform", body: "The API, the five apps, and the public site." },
    ],
  },
  "company/contact": {
    path: "/company/contact",
    title: "Contact | AI Mentor",
    description: "Sales, support, partnerships, or an enterprise demo. The form does not grant a role.",
    headline: "Tell us which door you need",
    subheading: "Sales, support, partnerships, or an enterprise demo. We do not promise 24/7 until operations can keep it.",
    cta: "enterprise",
    kind: "contact",
    blocks: [],
  },
  "company/partners": {
    path: "/company/partners",
    title: "Partners | AI Mentor",
    description: "No partner logos yet. Talk to us about Open Badges, LTI, or curriculum.",
    headline: "Partners, when they are real",
    subheading: "We will not invent university or vendor logos. Open Badges and employer certificates need signed partners.",
    cta: "studio",
    secondary: { label: "Talk to partnerships", href: "/company/contact" },
    blocks: [
      { title: "Curriculum", body: "Publishers and domain experts through Content Studio later (R5 marketplace)." },
      { title: "Recognition", body: "Open Badges and employer-recognised certificates, only with partners." },
      { title: "Integration", body: "LTI, SSO, and SIS remain the institution's systems. We integrate; we do not replace them." },
    ],
  },
  "legal/privacy": {
    path: "/legal/privacy",
    title: "Privacy | AI Mentor",
    description: "What we collect, where it lives, and how you export or erase it.",
    headline: "Privacy",
    subheading: "Learner data is private. Staff apps are not indexed. Residency is an R4 Enterprise add-on.",
    cta: "learner",
    kind: "legal",
    legal: [
      "AI Mentor accounts are created through the Learner App (Clerk). The public site stores demo and contact leads, not passwords.",
      "A signed-in learner can export their record (GET /me/export) and request erasure (DELETE /me). Erasure removes the Clerk user, vectors, and PostgreSQL rows for that account.",
      "The public leaderboard shows a handle or a stable pseudonym. Staff and opted-out learners are excluded.",
      "We teach people 16 and over. This is not a children's product.",
      "Data residency as a contractual add-on is R4. Until then, do not treat a region pin as a live feature.",
    ],
    blocks: [],
  },
  "legal/terms": {
    path: "/legal/terms",
    title: "Terms | AI Mentor",
    description: "Use of the public site, the Learner App, and organisation licences.",
    headline: "Terms of use",
    subheading: "The public site describes shipped behaviour in the present tense. Organisation licences are sold, not self-served, until checkout exists.",
    cta: "learner",
    kind: "legal",
    legal: [
      "You must be 16 or over to create an account.",
      "We are not an awarding body. Mastery evidence is not a degree, a vendor certificate, or a guaranteed job.",
      "The restricted lab is not a general-purpose computer. Do not attempt to exfiltrate secrets or reach the network from learner code.",
      "Instructor and institution roles are granted by a person, never by submitting a demo form.",
      "These pages are product terms in plain language. A signed Enterprise contract can add a DPA and residency clauses.",
    ],
    blocks: [],
  },
  "legal/cookies": {
    path: "/legal/cookies",
    title: "Cookies | AI Mentor",
    description: "Theme, locale, and essential session cookies. Marketing cookies wait on consent.",
    headline: "Cookies",
    subheading: "Theme and locale on this site. Session cookies live on the Learner App after you sign in.",
    cta: "learner",
    kind: "legal",
    legal: [
      "This site stores a theme preference (light, dark, or system) and may store a locale (en, fr, es).",
      "Sign-in cookies are set by Clerk on the Learner App origin, not on the public site.",
      "We do not run a third-party advertising pixel on these pages.",
      "A lead form posts to our API. That is a request you chose to send, not a hidden tracker.",
    ],
    blocks: [],
  },
  "legal/dpa": {
    path: "/legal/dpa",
    title: "DPA | AI Mentor",
    description: "Data processing for Enterprise buyers. Request the pack with a demo.",
    headline: "Data processing",
    subheading: "A signed DPA is part of Enterprise procurement. This page is not the contract.",
    cta: "enterprise",
    kind: "legal",
    legal: [
      "If you are buying Campus or Enterprise, request the security overview and DPA with the demo form.",
      "We do not publish a self-serve DPA PDF here until legal has issued one.",
      "Human control over grades, four-eyes publishing, and learner export/erasure already exist in the product rules.",
      "SSO, SCIM, LTI, and residency are named as R3–R4 capabilities, not present-tense features.",
    ],
    blocks: [],
  },
  "demo/instructor": {
    path: "/demo/instructor",
    title: "Instructor demo | AI Mentor",
    description: "Book an instructor demo. The form does not grant Instructor App access.",
    headline: "Book an instructor demo",
    subheading:
      "Tell us about the cohort. We will write within two working days. Submitting this form does not grant an Instructor App role.",
    cta: "instructor",
    kind: "demo-instructor",
    blocks: [],
  },
  "demo/enterprise": {
    path: "/demo/enterprise",
    title: "Enterprise demo | AI Mentor",
    description: "Request an enterprise demo. The form does not grant organisation admin.",
    headline: "Request an enterprise demo",
    subheading:
      "Seats, SSO, and LMS questions help us prepare. This form does not create an Institution App admin.",
    cta: "enterprise",
    kind: "demo-enterprise",
    blocks: [],
  },
};

export const sitemapPaths = ["/", ...Object.keys(pages).map((path) => `/${path}`), "/start"];
