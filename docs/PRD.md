# AI Mentor — Product Requirements Document

| | |
| --- | --- |
| Product | AI Mentor |
| Document | Product Requirements Document (PRD), MVP and beyond |
| Version | 1.0 |
| Date | 13 October 2026 |
| Owner | Product |
| Status | Draft for review by founders, product, design, engineering, and investors |
| Source specifications | [Requirements.md](Requirements.md), [Admin.md](Admin.md), [README.md](../README.md) |

This document describes what AI Mentor is, who it serves, why it will win, and what must be true for the MVP to ship. It deliberately avoids implementation detail. Engineering decisions live in the ReadMe and the codebase.

Figures marked **(hypothesis)** are planning assumptions that must be validated with data during the MVP and beta. They are not claims of fact.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision](#2-product-vision)
3. [Problem Statement](#3-problem-statement)
4. [Market Opportunity](#4-market-opportunity)
5. [User Personas](#5-user-personas)
6. [User Needs](#6-user-needs)
7. [User Journeys](#7-user-journeys)
8. [Core Features](#8-core-features)
9. [MVP Scope](#9-mvp-scope)
10. [Out-of-Scope Items](#10-out-of-scope-items)
11. [Success Metrics (KPIs)](#11-success-metrics-kpis)
12. [Engagement Metrics](#12-engagement-metrics)
13. [Retention Metrics](#13-retention-metrics)
14. [Learning Outcome Metrics](#14-learning-outcome-metrics)
15. [Monetisation Strategy](#15-monetisation-strategy)
16. [Risks and Dependencies](#16-risks-and-dependencies)
17. [Release Criteria](#17-release-criteria)
18. [Product Roadmap](#18-product-roadmap)
19. [Future Vision](#19-future-vision)
20. [Appendix](#appendix)

---

## 1. Executive Summary

**AI Mentor is a personal AI tutor that takes anyone from complete beginner to professional or researcher in Artificial Intelligence.** It combines the habit-forming engagement of Duolingo, the structure and rigour of a university curriculum, and the one-to-one attention of an expert mentor, all available 24/7 in English, French, and Spanish.

### The problem

Demand for AI skills is growing faster than any education system can supply them. Learners today choose between three imperfect options:

- **Courses and MOOCs** are structured but one-size-fits-all, passive, and have notoriously low completion rates.
- **General-purpose chatbots** are responsive but have no curriculum, no memory of what the learner has mastered, no assessment, and will confidently answer questions the learner is not ready for.
- **Human tutors and bootcamps** work, but are expensive, scarce, and mostly English-only.

### The solution

AI Mentor is a **curriculum-grounded, adaptive, gamified learning system** built around a Socratic AI tutor. It:

1. **Profiles each learner** on day one (knowledge, maths comfort, coding experience, goals, time available, preferred teaching style).
2. **Teaches the way each learner learns** — simple, storytelling, visual, mathematical, research, or industry mode, at the right depth and pace.
3. **Checks understanding before moving on** using a concept graph that knows what depends on what, so gaps are fixed before they compound.
4. **Grounds answers in curated, cited content** managed by subject experts, rather than relying on the model's memory alone.
5. **Makes learning a daily habit** through XP, levels, streaks, badges, daily challenges, and leaderboards.

### Why now

- Large language models have made a convincing one-to-one tutor economically possible for the first time.
- AI literacy is moving from a specialist skill to a baseline professional requirement.
- Large francophone and Spanish-speaking learner populations, notably across Africa and Latin America, are underserved by English-first AI education.

### Business model

Freemium subscription. A generous **Free** tier drives acquisition and habit; **Pro** unlocks unlimited tutoring, the coding lab, and advanced paths; **Research** adds paper analysis and research supervision tools. Regional pricing makes the product accessible in emerging markets. Institutional (university and enterprise) licensing and paid certification follow after product-market fit.

### MVP in one sentence

In 8–12 weeks, ship onboarding, the Socratic tutor, four launch learning paths (AI Fundamentals, Reinforcement Learning, Robotics, LLM Engineering), quizzes, daily challenges, gamification and leaderboards, a progress dashboard, trilingual support, and an admin knowledge portal that grounds the tutor in curated content — then prove that learners **come back** and **actually learn**.

### MVP success targets

| Signal | Target |
| --- | --- |
| Active learners | 100+ |
| Onboarding completion | 70% |
| Weekly retention | 40% |
| Sessions per learner per week | 3+ |
| Daily challenge participation | 60% |
| Quiz completion | 75% |
| Measurable mastery gain (pre vs post check) | +25 points average **(hypothesis)** |
| Tutor response starts streaming | Under 1.5 seconds |

---

## 2. Product Vision

### Vision statement

> **Give every person on earth a world-class private AI tutor that knows them, adapts to them, and takes them as far as they want to go — from their first line of Python to publishable research.**

### Mission

Help anyone progress from complete beginner to industry professional, researcher, or PhD-level expert in Artificial Intelligence, Machine Learning, Deep Learning, Reinforcement Learning, Data Science, Robotics, Autonomous Systems, MLOps, and AI Engineering.

### What AI Mentor is — and is not

AI Mentor is not a chatbot bolted onto a course catalogue. It is one learning companion that plays eight roles:

| Role | What it does for the learner |
| --- | --- |
| Teacher | Explains concepts in the learner's preferred style and depth |
| Mentor | Encourages, motivates, and keeps the learner on track |
| Coach | Sets daily goals, streaks, and challenges |
| Examiner | Generates and grades adaptive quizzes and coding checks |
| Study companion | Builds study plans and schedules spaced-repetition reviews |
| Coding assistant | Reviews code, explains bugs, suggests improvements |
| Researcher | Analyses papers, explains equations, critiques methodology |
| Career advisor | Maps skills to roles and recommends next steps |

### Product principles

1. **Understanding before answers.** The tutor asks, probes, and checks before it gives the full solution. Learners earn progress; they do not skip it.
2. **Grounded, not guessed.** The tutor prefers curated, expert-approved content and cites it. When it does not know, it says so.
3. **Personal by default.** No two learners see the same path. Style, depth, pace, and language are always under the learner's control.
4. **Fun that serves learning.** Gamification rewards real learning (mastery, passing code, completed reviews), never empty clicks. XP is capped daily to prevent farming.
5. **Prerequisites are respected.** A weak foundation is repaired before the next topic is taught.
6. **Accessible everywhere.** Multilingual, mobile-friendly, regionally priced, and useful on modest bandwidth.
7. **Safe and trustworthy.** Learner data is private to the learner; content is reviewed before it reaches students; code runs in a restricted environment.

### Positioning

> For **ambitious learners** who want to build real AI skills, **AI Mentor** is the **personal AI tutor** that **adapts every lesson to you and checks you truly understand before moving on**. Unlike **online courses**, it is interactive and personal. Unlike **general chatbots**, it follows a real curriculum, remembers your progress, and cites trusted sources.

---

## 3. Problem Statement

### Core problem

**People who want to learn AI cannot get personalised, rigorous, and engaging instruction at a price and in a language they can access.** As a result, most quit early, learn superficially, or never start.

### Problem breakdown

| # | Problem | Who feels it most | Consequence |
| --- | --- | --- | --- |
| P1 | **One-size-fits-all content.** Courses assume one background, one pace, one teaching style. | Career switchers, non-STEM learners | Content is either too hard (learner quits) or too easy (learner gets bored). |
| P2 | **Hidden prerequisite gaps.** Learners attempt Q-learning without understanding MDPs, or transformers without linear algebra. | Self-taught learners | Confusion compounds; learners conclude "AI is not for me." |
| P3 | **Passive learning.** Watching videos creates an illusion of competence without practice or feedback. | Everyone | Poor retention; skills don't transfer to jobs or exams. |
| P4 | **Low motivation and completion.** Self-paced online courses are widely reported to have low completion rates. | Busy professionals | Paid courses go unfinished; learners lose confidence. |
| P5 | **Chatbots lack structure and reliability.** General AI assistants have no curriculum, no mastery tracking, and can hallucinate. | Learners using ChatGPT-style tools to self-study | No sense of progress; learners can't tell if answers are correct. |
| P6 | **Language and cost barriers.** Quality AI education is predominantly English-language and priced for high-income markets. | Francophone and Hispanophone learners, emerging markets | Large talent pools are excluded. |
| P7 | **No bridge from learning to research.** Moving from coursework to reading, critiquing, and writing papers has almost no structured support. | Graduate students, aspiring researchers | High drop-off before first publication. |
| P8 | **Educators can't scale or govern AI-generated teaching.** Institutions worry about accuracy and want control over what an AI tutor says. | Instructors, universities, training teams | Slow adoption of AI tutoring in formal education. |

### How we will know the problem is solved

- Learners return several times a week without being prompted (habit formed).
- Learners show measurable mastery gains on checks they could not pass before.
- Learners complete paths at materially higher rates than typical self-paced course benchmarks.
- Instructors trust the tutor because it cites approved material.

---

## 4. Market Opportunity

### Market drivers

1. **AI skills demand.** Employers across every sector are adding AI and data skills to job requirements, and governments are funding national AI-skilling initiatives.
2. **Shift to AI-native learning.** Learners increasingly expect conversational, on-demand help rather than static video.
3. **Cost collapse of AI tutoring.** Falling model inference costs make a personalised tutor viable at consumer subscription prices.
4. **Underserved language markets.** French and Spanish together cover a very large global speaking population, including some of the fastest-growing youth populations in Africa and Latin America.
5. **Gamified learning is proven.** Consumer language-learning apps have demonstrated that daily-habit mechanics can sustain engagement at very large scale.

### Market segments

| Segment | Description | MVP focus |
| --- | --- | --- |
| Consumer self-learners (B2C) | Students, career switchers, professionals, enthusiasts paying for themselves | **Primary** |
| Researchers and graduate students (B2C premium) | Masters/PhD students and early-career researchers | Secondary (Research tier) |
| Universities and bootcamps (B2B2C) | Institutions licensing AI Mentor as a tutor alongside courses | Post-MVP |
| Enterprises (B2B) | Companies upskilling teams into AI | Post-MVP |
| Governments and NGOs | National skilling programmes, especially in emerging markets | Future |

### Market sizing approach

We will size the market bottom-up from addressable learners rather than relying on top-down "EdTech market" figures. The model below is a **planning model (hypothesis)**; each input must be replaced with sourced data before an investor round.

| Layer | Definition | How to size |
| --- | --- | --- |
| **TAM** | All people globally actively learning AI/ML/data skills online, across English, French, and Spanish | Learner counts from major MOOC and learning platforms in AI/data categories × annual spend per learner on AI education |
| **SAM** | Self-directed learners in our three launch languages who would pay for a digital tutor | TAM × share in EN/FR/ES markets × share willing to pay for digital learning |
| **SOM (3-year)** | Learners we can realistically acquire and convert | Acquisition plan × paid conversion × blended ARPU |

**Illustrative 3-year SOM (hypothesis):**

| Input | Year 1 | Year 2 | Year 3 |
| --- | --- | --- | --- |
| Registered learners | 25,000 | 150,000 | 500,000 |
| Monthly active share | 30% | 30% | 30% |
| Paid conversion (of registered) | 3% | 4% | 5% |
| Paying subscribers | 750 | 6,000 | 25,000 |
| Blended annual ARPU (after regional pricing) | $90 | $95 | $100 |
| Consumer ARR | ~$68K | ~$570K | ~$2.5M |
| Institutional ARR (from Year 2) | — | ~$200K | ~$1.5M |
| **Total ARR** | **~$68K** | **~$770K** | **~$4.0M** |

### Competitive landscape

| Category | Examples | Strength | Gap AI Mentor fills |
| --- | --- | --- | --- |
| MOOCs and course platforms | Coursera, edX, Udacity | Brand, certificates, university content | Passive, not personalised, low completion |
| Skills platforms | DataCamp, Codecademy | Hands-on practice | Fixed paths; limited depth into RL, robotics, research |
| General AI assistants | ChatGPT, Claude, Gemini | Powerful, flexible | No curriculum, no mastery tracking, no gamification, no grounding in approved content |
| AI tutors for schools | Khanmigo and similar | Socratic tutoring, trusted brand | K-12 focus; not built for professional or research-level AI |
| Gamified learning apps | Duolingo, Brilliant | Habit formation | Not focused on deep AI/ML, coding, or research |
| Bootcamps and human tutors | Various | Accountability, depth | Expensive, scarce, rarely multilingual |

### Our defensible advantages

1. **Concept graph + mastery model.** A structured map of AI knowledge with prerequisites, so the tutor teaches in the right order. Hard to replicate with a prompt.
2. **Curated, governed knowledge base.** Expert-approved content with citations and a review workflow — the foundation institutions require.
3. **Depth ceiling.** One product that goes from beginner to PhD-level reinforcement learning, robotics, and research methods.
4. **Multilingual from day one,** with regional pricing for emerging markets.
5. **Learning data flywheel.** Every quiz, code submission, and review improves our understanding of which concepts are hard and which explanations work — improving recommendations and content for everyone.

---

## 5. User Personas

The MVP prioritises three primary personas. Others are supported but not optimised for.

### Primary persona 1 — Amara, the University Student

| | |
| --- | --- |
| Age / location | 21, Lagos, Nigeria |
| Background | Third-year Computer Science; comfortable with Python, shaky on probability and linear algebra |
| Goal | Pass her ML module with top marks and build a portfolio for a graduate role |
| Time available | 45 minutes on weekdays, more before exams |
| Language | English |
| Device | Mid-range Android phone; laptop at university |
| Frustrations | Lectures move too fast; YouTube explanations contradict each other; can't afford paid tutoring |
| Quote | *"I don't need more videos. I need someone to tell me what I don't understand."* |
| What success looks like | Clear exam preparation, quizzes at the right level, visible progress, a streak she's proud of |
| Willingness to pay | Low; highly sensitive to regional pricing |

### Primary persona 2 — Carlos, the Career Switcher

| | |
| --- | --- |
| Age / location | 34, Madrid, Spain |
| Background | Data analyst for 8 years; strong SQL and Excel, basic Python, little maths since school |
| Goal | Become an ML engineer within 12 months |
| Time available | 5–7 hours per week, mostly evenings and weekends |
| Language | Spanish (prefers it for concepts), English for code |
| Frustrations | Courses assume a maths background; doesn't know what to learn in what order; worried about wasting time |
| Quote | *"Just tell me the shortest path from where I am to getting hired."* |
| What success looks like | A personal roadmap, practical coding, explanations in Spanish, evidence he's job-ready |
| Willingness to pay | Medium–high if it accelerates a career change |

### Primary persona 3 — Dr. Élodie, the Early-Career Researcher

| | |
| --- | --- |
| Age / location | 28, Montréal, Canada |
| Background | PhD student in control engineering moving into reinforcement learning for robotics |
| Goal | Understand modern RL deeply (PPO, SAC, multi-agent) and publish her first RL paper |
| Time available | Irregular, intensive bursts |
| Language | French and English |
| Frustrations | Papers assume knowledge she lacks; supervisor has little time; general chatbots hallucinate citations |
| Quote | *"I need the derivation, not the analogy — and I need to trust the source."* |
| What success looks like | Full mathematical depth, paper analysis, methodology critique, reliable citations |
| Willingness to pay | High (often via grant or institution) |

### Secondary personas

| Persona | Summary | Key need |
| --- | --- | --- |
| **Priya, the Upskilling Professional** | Product manager at a fintech who must understand LLMs and RAG to lead AI features | Industry mode, short sessions, practical vocabulary |
| **Kwame, the Robotics Engineer** | Embedded engineer moving into AI-powered robotics (ROS 2, SLAM, navigation) | Robotics path, visual explanations, simulations later |
| **Sofia, the Entrepreneur** | Founder building an AI product | LLM Engineering path, career/business framing |
| **Tom, the Enthusiast** | Retired engineer learning for curiosity | Storytelling mode, slow pace, no pressure |
| **Dr. Mensah, the Instructor / Content Admin** | Lecturer who curates material and wants to trust what the tutor says | Upload, tag, approve content; see where students struggle |

### Anti-personas (not designed for in MVP)

- Children under 16 (requires separate safeguarding and consent model).
- Users seeking a general-purpose coding assistant for production work.
- Learners seeking accredited university degrees.

---

## 6. User Needs

Needs are expressed as jobs-to-be-done and mapped to personas and features.

### Learner needs

| ID | Job to be done | Personas | Importance | Addressed by |
| --- | --- | --- | --- | --- |
| N1 | *When I start, help me understand where I am and what to learn first.* | All | Critical | Onboarding assessment, starting path |
| N2 | *Explain things the way I understand best.* | All | Critical | Teaching modes, depth, maths level |
| N3 | *Tell me what I'm missing before I fall behind.* | Amara, Carlos | Critical | Concept graph, mastery tracking, recommendations |
| N4 | *Let me practise and get instant, specific feedback.* | All | Critical | Quizzes, coding lab, code review |
| N5 | *Keep me motivated to show up every day.* | Amara, Carlos, Tom | High | XP, streaks, badges, daily challenges, leaderboards |
| N6 | *Show me I'm making progress.* | All | High | Dashboard, mastery, reports |
| N7 | *Let me learn in my own language.* | Carlos, Élodie, Amara (future FR markets) | High | Multilingual UI, lessons, tutor |
| N8 | *Give me answers I can trust and verify.* | Élodie, Priya | High | Curated knowledge base, citations |
| N9 | *Help me remember what I learned.* | Amara, Carlos | High | Spaced-repetition flashcards |
| N10 | *Give me a plan that fits my time and goal.* | Carlos, Priya | High | Study plans, pace settings |
| N11 | *Help me read and critique research papers.* | Élodie | Medium (High for Research tier) | Research assistant |
| N12 | *Tell me how my skills map to jobs.* | Carlos, Sofia | Medium | Career advisor |
| N13 | *Make the tutor feel like my tutor.* | All | Medium | Avatar and personality |

### Administrator and instructor needs

| ID | Job to be done | Importance | Addressed by |
| --- | --- | --- | --- |
| A1 | *Upload and organise trusted teaching material quickly.* | Critical | Content repository, metadata |
| A2 | *Control what students see; nothing unreviewed goes live.* | Critical | Approval workflow |
| A3 | *Structure content into paths, modules, and concepts with prerequisites.* | Critical | Curriculum builder, taxonomy, knowledge graph |
| A4 | *Turn a paper into lessons, quizzes, and flashcards without hours of work.* | High | AI content generation |
| A5 | *See where learners struggle and which content works.* | High | Admin analytics |
| A6 | *Fix mistakes and roll back bad changes.* | Medium | Version control |

### Business needs

| ID | Need | Addressed by |
| --- | --- | --- |
| B1 | Prove retention and learning outcomes to investors | Instrumented KPIs, learning outcome measurement |
| B2 | Validate willingness to pay | Subscription tiers, paywall experiments |
| B3 | Control AI cost per learner | Usage limits on Free tier, curated-content-first answers, fallback to authored curriculum |
| B4 | Protect brand from harmful or wrong answers | Guardrails, grounding, review workflow |
| B5 | Build a defensible content and data asset | Knowledge base, concept graph, learning analytics |

---

## 7. User Journeys

### Journey 1 — First session: from sign-up to first "aha" (Amara)

**Goal:** Within 10 minutes of signing up, the learner has a personal path, has learned one concept, passed one check, and earned their first XP.

| Step | Learner action | What AI Mentor does | Emotion | Design goal |
| --- | --- | --- | --- | --- |
| 1 | Lands on the site from a friend's leaderboard share | Shows value proposition and "Start free" | Curious | Clear promise, no friction |
| 2 | Signs up with Google | Creates account; asks preferred language | Neutral | Under 30 seconds |
| 3 | Completes onboarding (goal, background, maths comfort, coding, time, style) | Adaptive questions; skips irrelevant ones | Engaged | Under 4 minutes; feels like a conversation, not a form |
| 4 | Takes a short placement check | Estimates starting level and initial skill score | Slightly anxious | Reassure: "This just helps us start in the right place" |
| 5 | Sees her personal path and first lesson | Recommends "Probability for ML" because it detected a gap before supervised learning | Surprised, understood | **First "aha": it knows what I need** |
| 6 | Chats with the tutor about the concept | Socratic explanation in her chosen style; asks her a checking question | Focused | Tutor feels personal and patient |
| 7 | Passes a 3-question check | Awards XP, starts a streak, unlocks first badge | Proud | Celebrate genuinely |
| 8 | Sees dashboard and tomorrow's daily challenge | Shows level, streak, next lesson | Motivated | Clear reason to come back tomorrow |

**Drop-off risks and mitigations:** Long onboarding (keep adaptive and skippable); placement check feels like an exam (frame as optional and short); tutor reply slow (stream within 1.5s).

### Journey 2 — Daily habit loop (all learners)

```text
Reminder / intrinsic trigger
        ↓
Open app → see streak + daily challenge
        ↓
Complete challenge (quiz, coding, or lesson goal)  →  XP, badge progress
        ↓
Due flashcard reviews (spaced repetition)
        ↓
Continue path: next recommended concept with tutor
        ↓
Check understanding → mastery updated
        ↓
Leaderboard position / streak saved → close app
```

**Design goal:** a meaningful session in 10–15 minutes. The loop must be rewarding even on a busy day (a 3-minute challenge keeps the streak).

### Journey 3 — Repairing a knowledge gap (Carlos)

1. Carlos is studying Q-learning and fails a check on value updates.
2. The tutor diagnoses the misconception and checks the prerequisite (Bellman equations / MDPs).
3. The concept graph shows MDP mastery is weak; the tutor proposes a short detour.
4. Carlos chooses **Visual mode** and **Light mathematics**; the tutor re-explains in Spanish.
5. Recommendations surface a beginner lesson, a visual explanation, and a practice quiz from the curated library, with citations.
6. Carlos passes the MDP check; mastery updates; the path returns to Q-learning.
7. He passes the Q-learning check and the dashboard shows "Weak topic resolved."

**Moment of value:** *"It caught the real problem and fixed it before I wasted a week."*

### Journey 4 — Coding practice and review (Carlos, Kwame)

1. Learner opens a coding exercise attached to a lesson (e.g. implement epsilon-greedy).
2. Writes Python in the coding lab and runs it.
3. Sees output and pass/fail against expected results.
4. Requests a review; the tutor explains the bug and hints rather than rewriting the solution.
5. Fixes the code, passes, earns XP; the concept's mastery increases.

### Journey 5 — Researcher paper analysis (Élodie, Research tier)

1. Élodie uploads a PPO-variant paper she owns.
2. Requests a summary, equation-by-equation explanation, and methodology critique.
3. Switches to **Mathematical mode** with **Full proofs**.
4. Asks the tutor to simulate a reviewer's critique.
5. Receives identified research gaps and suggested experiments.
6. Saves the analysis to her research notes; links prerequisite concepts she should review.

**Trust requirement:** analysis uses only her uploaded file and the curated library; the tutor never invents citations.

### Journey 6 — Instructor curates content (Dr. Mensah)

1. Uploads a lecture PDF on SLAM and tags topic, difficulty, language, and learning objectives.
2. Places it in the taxonomy under Robotics → SLAM and links prerequisites (probability theory).
3. Uses AI content generation to draft lesson notes, flashcards, and a quiz.
4. Reviews and edits the drafts; moves them through Draft → Review → Approved → Published.
5. Published content becomes available to learners and the tutor begins citing it.
6. A week later, the analytics dashboard shows quiz pass rates and the hardest SLAM concepts; he revises the weakest lesson as a new version.

### Journey 7 — Upgrade to Pro (conversion journey)

1. A Free learner hits the daily tutor message limit during an engaged session, or tries to open an advanced path or the coding lab.
2. Sees a clear, non-blocking upgrade prompt explaining what Pro adds, at their regional price.
3. Starts a trial or subscribes via checkout.
4. Returns to the exact point they left; limit lifted.

**Design rule:** never interrupt mid-explanation; let the current answer finish before showing the limit.

---

## 8. Core Features

Priorities use **MoSCoW** for the **MVP release**:

- **Must** — the MVP fails without it.
- **Should** — important; included if at all possible, can slip to the first post-MVP release.
- **Could** — desirable; only if time allows.
- **Won't (this release)** — explicitly deferred; see [Out-of-Scope](#10-out-of-scope-items).

### Feature summary

| ID | Feature | Area | Priority |
| --- | --- | --- | --- |
| F1 | Accounts, roles, and profiles | Foundation | Must |
| F2 | Intelligent onboarding and placement | Personalisation | Must |
| F3 | Socratic AI tutor | Learning | Must |
| F4 | Adaptive teaching controls | Personalisation | Must |
| F5 | Learning paths and concept graph | Curriculum | Must |
| F6 | Personalised recommendations and study plans | Personalisation | Must |
| F7 | Intelligent quiz system | Practice | Must |
| F8 | Daily challenges | Engagement | Must |
| F9 | Gamification: XP, levels, streaks, badges, titles | Engagement | Must |
| F10 | Leaderboards | Engagement | Must (global, country) / Could (friends) |
| F11 | Progress dashboard and learning analytics | Progress | Must |
| F12 | Multilingual experience (EN, FR, ES) | Accessibility | Must |
| F13 | Knowledge repository and library (admin) | Content | Must |
| F14 | Curriculum management, taxonomy, and knowledge graph (admin) | Content | Must |
| F15 | Grounded answers with citations (RAG) | Trust | Must |
| F16 | Content approval workflow | Governance | Must |
| F17 | Trust, safety, and privacy guardrails | Trust | Must |
| F18 | Subscriptions and billing | Monetisation | Must |
| F19 | Coding lab with AI code review | Practice | Should |
| F20 | Flashcards with spaced repetition | Retention | Should |
| F21 | Research assistant | Research | Should |
| F22 | AI content generation for admins | Content | Should |
| F23 | Content version control | Governance | Should |
| F24 | Admin analytics dashboard | Content | Should |
| F25 | Weekly progress reports | Progress | Should |
| F26 | Tutor avatar and personality | Delight | Could (personality: Should) |
| F27 | Career advisor | Career | Could |

---

### F1 — Accounts, roles, and profiles

Sign-up and sign-in by email or Google, password reset, and three roles: **student**, **instructor**, **admin**. Profiles store name, country, language, level, learning goal, and tutor preferences.

| | |
| --- | --- |
| **User value** | Fast, familiar sign-in; progress and preferences are saved and follow the learner across devices and languages. |
| **Business value** | Foundation for retention, personalisation, monetisation, and country leaderboards; role separation protects content governance. |
| **Priority** | **Must** |

**Acceptance criteria**

- A new user can register with email or Google and reach onboarding in under 60 seconds.
- Password reset works end to end via email.
- Every user has exactly one role; only admins can change roles.
- Students cannot access admin or instructor screens, even via direct links.
- A learner's progress, preferences, and documents are visible only to that learner (and aggregated anonymously to admins).
- Profile country drives country leaderboard placement; the learner can edit it.
- A learner can delete their account and data on request.

---

### F2 — Intelligent onboarding and placement

A conversational onboarding that captures current knowledge, education, professional experience, industry, career goal, research interests, learning style, language, available time, preferred difficulty, maths comfort, programming experience, and preferred teaching style — followed by an optional short placement check.

| | |
| --- | --- |
| **User value** | The learner starts at the right level from minute one, without wading through content they already know or content that is too advanced. |
| **Business value** | Onboarding is the strongest predictor of activation; personalised starts drive retention. Captured goals enable targeted upgrade offers and cohort analysis. |
| **Priority** | **Must** |

**Acceptance criteria**

- Onboarding completes in under 5 minutes for the median user.
- Questions adapt: a learner with no programming experience is not asked about frameworks.
- Every question except language and goal can be skipped; sensible defaults apply.
- On completion the learner is assigned a **persona**, a **starting path**, an **initial skill score**, and default teaching settings.
- The placement check is optional, takes under 3 minutes, and adjusts the starting concept.
- The first recommended lesson is shown immediately after onboarding.
- Learners can re-take onboarding or edit any answer from settings.
- Onboarding completion rate is tracked per step to identify drop-off.

---

### F3 — Socratic AI tutor

A streaming conversational tutor that explains, gives examples, builds analogies, walks through mathematics, and generates exercises. It asks checking questions before giving complete answers, and routes requests (planning, quiz, coding, research, career) to the right experience.

| | |
| --- | --- |
| **User value** | A patient, expert tutor available 24/7 that makes the learner think, not just copy — leading to real understanding. |
| **Business value** | The core differentiator and primary reason to pay. Socratic design increases session depth and measurable learning outcomes, which drive word of mouth and institutional sales. |
| **Priority** | **Must** |

**Acceptance criteria**

- The tutor's reply begins appearing within **1.5 seconds** for 95% of messages under normal load.
- When a learner asks for an answer to a practice question, the tutor first offers a hint or guiding question; the full answer is available if the learner explicitly asks again.
- The tutor uses the learner's current teaching mode, depth, maths level, personality, and language.
- The tutor is aware of the learner's current concept and mastery, and references prior conversation within a session.
- Requests to plan, quiz, code, research, or get career advice are recognised and handed to the right flow.
- When curated content exists for a topic, the answer draws on it and cites it (see F15).
- If no AI model is available, the tutor falls back to authored curriculum content instead of failing.
- The tutor declines out-of-scope or unsafe requests politely and redirects to learning.
- Conversations are saved and can be resumed.
- On an internal evaluation set, at least **90%** of tutor answers are rated factually correct by subject experts; at least **85%** follow Socratic behaviour where appropriate.

---

### F4 — Adaptive teaching controls

Learners control how they are taught, and can change any setting at any time:

| Control | Options |
| --- | --- |
| Teaching style | Simple, Storytelling, Visual, Mathematical, Research, Industry, Mixed |
| Pace | Slow, Moderate, Fast, Intensive |
| Technical depth | Beginner, Intermediate, Advanced, Expert, Researcher, PhD |
| Mathematical depth | None, Light, Moderate, Formal, Full proofs and derivations |
| Breadth | Broad survey, Deep specialist, Balanced |

| | |
| --- | --- |
| **User value** | Content that matches how each person thinks — a novice gets plain English, a PhD student gets full derivations — on the same topic. |
| **Business value** | Expands the addressable audience from beginners to researchers in one product; a visible, easy-to-explain differentiator in marketing. |
| **Priority** | **Must** |

**Acceptance criteria**

- All five controls are available from the tutor screen and settings, with defaults set by onboarding.
- Changing a setting affects the **next** tutor reply without restarting the conversation.
- The same question asked in Simple mode with No mathematics and in Mathematical mode with Full proofs produces visibly different explanations (verified by an expert review panel on a sample of 30 concepts).
- Pace affects study plan density and how quickly new concepts are introduced.
- Breadth affects recommendations (survey favours new topics; specialist favours depth within a topic).
- Settings persist across sessions and languages.

---

### F5 — Learning paths and concept graph

Structured paths made of concepts, lessons, and checks, connected by a concept graph that records prerequisites and related ideas. Launch paths:

1. **AI Fundamentals** — rules versus learning, Python for ML, probability, linear algebra, supervised learning.
2. **Reinforcement Learning** — agent–environment loop, MDPs, Bellman equations, dynamic programming, Monte Carlo, temporal difference, Q-learning, DQN, policy gradients, PPO, SAC, multi-agent RL.
3. **Robotics** — the robot loop, ROS 2, computer vision, SLAM, navigation, safe use of RL in control.
4. **LLM Engineering** — building systems that can abstain, cite, and be evaluated, plus research methods.

| | |
| --- | --- |
| **User value** | A clear route from where I am to where I want to be, with the guarantee that I won't be taught something before I'm ready. |
| **Business value** | The curriculum graph is a defensible asset that general chatbots lack; deep RL and robotics paths target an underserved, high-willingness-to-pay niche. |
| **Priority** | **Must** |

**Acceptance criteria**

- All four launch paths are available in full, each with lessons and at least one check per concept.
- Each concept lists its prerequisites; the learner can see them.
- A learner cannot be recommended a concept whose prerequisites are below the mastery threshold (they can still choose to open it, with a warning).
- Path progress is shown as a percentage and as concepts mastered.
- Learners can switch or follow multiple paths; progress on shared concepts counts across paths.
- Curriculum updates never erase learner progress.

---

### F6 — Personalised recommendations and study plans

Recommendations follow the concept graph and the learner's mastery, goals, style, and time. Study plans turn a goal ("Become an RL engineer in 6 months", "Pass my exam on 15 December") into a scheduled sequence.

| | |
| --- | --- |
| **User value** | Always knowing the single best next step; a realistic plan that fits my week. |
| **Business value** | Reduces "what do I do now?" drop-off; plans create commitment, which increases retention and conversion. |
| **Priority** | **Must** |

**Acceptance criteria**

- The dashboard always shows one primary "next step" and up to three alternatives.
- When a learner fails a check, the next recommendation addresses the weakest prerequisite.
- Recommendations include curated resources (lesson, visual explanation, practice quiz, paper) matched to style and level.
- A learner can generate a study plan from a goal, target date, and weekly hours; the plan is editable.
- Plans adjust automatically when the learner falls behind or gets ahead.
- Each recommendation shows a short reason ("Because you found Bellman equations difficult").

---

### F7 — Intelligent quiz system

Automatically generated quizzes — multiple choice, true/false, fill in the blank, short answer, coding questions, mathematical derivations, and research critique — at Beginner, Intermediate, Advanced, Expert, and PhD levels, with difficulty that adapts to performance.

| | |
| --- | --- |
| **User value** | Practice at exactly the right difficulty with instant, explained feedback; proof to myself that I understand. |
| **Business value** | Quizzes are the main source of mastery data powering personalisation and learning-outcome evidence for investors and institutions. |
| **Priority** | **Must** |

**Acceptance criteria**

- Quizzes can be generated for any concept in the launch paths at any supported difficulty.
- MVP supports multiple choice, true/false, fill in the blank, short answer, and coding checks; derivation and research critique questions are available at Expert/PhD level as **Should**.
- Every answer receives immediate feedback with an explanation of why it is right or wrong.
- After two consecutive correct answers, difficulty increases; after two incorrect, it decreases.
- Results update concept mastery within the same session.
- Quiz questions are reviewed against curated content; at least **95%** of sampled auto-generated questions have a correct answer key (expert audit).
- Quizzes are available in all three languages.

---

### F8 — Daily challenges

A fresh challenge every day: a quiz, coding, research, debugging, or robotics challenge. MVP launches with **quiz**, **coding**, and **lesson-goal** challenges.

| | |
| --- | --- |
| **User value** | A small, achievable reason to learn every day, with special rewards. |
| **Business value** | The primary driver of daily active use and streaks — the strongest leading indicator of retention. |
| **Priority** | **Must** |

**Acceptance criteria**

- A new challenge is available to every learner at local midnight.
- Challenges are matched to the learner's level and current path.
- A challenge can be completed in under 5 minutes.
- Completing a challenge awards XP, contributes to streaks, and may award a badge.
- Learners see time remaining and whether today's challenge is complete.
- Participation rate is tracked daily.
- Research, debugging, and robotics challenge types are **Could** for MVP.

---

### F9 — Gamification: XP, levels, streaks, badges, titles

Learners earn XP, achievement points, streaks, badges, levels, and titles (e.g. AI Apprentice → Data Scientist → RL Explorer → Robotics Engineer → AI Researcher → AI Master → Grandmaster AI Engineer).

| | |
| --- | --- |
| **User value** | Visible progress, a sense of achievement, and motivation on days willpower is low. |
| **Business value** | Proven habit-forming mechanics increase retention and session frequency; shareable achievements drive organic acquisition. |
| **Priority** | **Must** |

**Acceptance criteria**

- XP is awarded only for learning actions: lessons completed, quizzes passed, code that passes, flashcard reviews, and daily challenges.
- A daily XP cap (currently 400 XP) prevents farming; learners see when they reach it.
- Levels advance every 250 XP; the learner sees XP to the next level.
- A streak increases only on consecutive active days (in the learner's time zone) and resets after a missed day.
- At least 15 badges exist at launch, covering milestones, streaks, path completion, and mastery.
- Titles are tied to mastery milestones, not just XP, so they reflect real ability.
- Level-ups, badges, and streak milestones trigger a celebratory moment that does not interrupt an active lesson.
- Learners can share a badge or level-up as an image/link.

---

### F10 — Leaderboards

Global top 10, country top 10, and the learner's own global position, national position, and percentile. Ranking based on XP, challenge completion, quiz performance, and project completion. Friends and regional leaderboards follow.

| | |
| --- | --- |
| **User value** | Healthy competition and recognition; seeing "Top 5% in Nigeria" is motivating and shareable. |
| **Business value** | Social motivation increases engagement; country rankings create local word-of-mouth and community. |
| **Priority** | **Must** (global and country) · **Could** (friends) · **Won't** (regional, community participation scoring) |

**Acceptance criteria**

- Global and country leaderboards show the top 10 learners, refreshed at least hourly.
- Every learner sees their global rank, country rank, and percentile, even if outside the top 10.
- Weekly leaderboards reset so new learners can compete; all-time rankings are also available.
- Learners can opt out of public leaderboards and choose a display name instead of their real name.
- Suspicious XP patterns are flagged and excluded from rankings pending review.

---

### F11 — Progress dashboard and learning analytics

A home dashboard showing level, XP, streak, path progress, strong and weak concepts, learning velocity, quiz and coding performance, and the next recommended lesson.

| | |
| --- | --- |
| **User value** | A clear picture of what I know, what I don't, and how fast I'm improving. |
| **Business value** | Makes progress tangible, reinforcing the value of a subscription; data supports outcome claims. |
| **Priority** | **Must** (dashboard) · **Should** (weekly reports, F25) · **Could** (monthly reports) |

**Acceptance criteria**

- The dashboard loads in under 2 seconds and is the default screen after sign-in.
- It shows level, XP to next level, streak, path progress, top 3 strong and top 3 weak concepts, and next step.
- Mastery per concept is shown on a simple, understandable scale (e.g. Not started, Learning, Practised, Mastered).
- Learning velocity shows concepts mastered per week over the past 4 weeks.
- Quiz accuracy and coding pass rates are shown over time.
- Selecting a weak concept starts a targeted review.

---

### F12 — Multilingual experience (English, French, Spanish)

Full UI translation, lesson and quiz translation, and tutor responses in the selected language. Learners can switch at any time; progress stays the same.

| | |
| --- | --- |
| **User value** | Learn complex concepts in the language I think in. |
| **Business value** | Opens francophone and Hispanophone markets that competitors underserve; strong differentiator for African and Latin American growth. |
| **Priority** | **Must** (UI, lessons, quizzes, tutor text) · **Won't** (voice translation in MVP) |

**Acceptance criteria**

- 100% of UI strings are available in English, French, and Spanish.
- All launch-path lessons and checks are available in all three languages, reviewed by a fluent subject-matter reviewer.
- The tutor responds in the selected language; technical terms keep the English term in brackets where helpful (e.g. "apprentissage par renforcement (reinforcement learning)").
- Switching language does not reset progress, streaks, XP, or conversation history.
- English is the default when no preference is set.
- Learners can ask the tutor for a translation of any explanation.

---

### F13 — Knowledge repository and library (admin)

Administrators and instructors upload and manage PDFs, research papers, books, lecture notes, slides, documents, Markdown, web pages, YouTube links, GitHub repositories, code samples, datasets, and images. Each asset carries title, description, topic, difficulty, author, source, publication date, version, learning objectives, estimated study time, tags, and language.

| | |
| --- | --- |
| **User value** | (Learners) Answers and resources come from trusted, expert-selected material. (Admins) One place to manage all teaching content. |
| **Business value** | The curated library is a compounding, defensible asset and a prerequisite for institutional sales. |
| **Priority** | **Must** (PDF, DOCX, PPTX, TXT, Markdown, URL) · **Should** (CSV, JSON, HTML, GitHub) · **Won't** (MP4, audio processing in MVP) |

**Acceptance criteria**

- Admins can upload MVP formats and see processing status (queued, processing, ready, failed with reason).
- Each asset requires title, topic, difficulty, and language; other metadata is optional.
- Assets are searchable by title, topic, tag, difficulty, and language.
- Admins can edit metadata and archive assets.
- A 50-page PDF becomes searchable by the tutor within 10 minutes of upload.
- Uploaded content is never visible to learners until published (see F16).

---

### F14 — Curriculum management, taxonomy, and knowledge graph (admin)

Admins build learning paths (courses, modules, lessons, assessments, projects, recommended resources), maintain a hierarchical taxonomy (e.g. Artificial Intelligence → Reinforcement Learning → MDP), and define concept relationships (prerequisites, dependencies, related, advanced).

| | |
| --- | --- |
| **User value** | Learners get coherent, well-sequenced paths; instructors can shape the curriculum without engineers. |
| **Business value** | Enables rapid content expansion and partner-created paths; the graph powers personalisation quality. |
| **Priority** | **Must** (taxonomy, prerequisites, path structure) · **Could** (drag-and-drop builder) |

**Acceptance criteria**

- Admins can create, edit, reorder, and retire paths, modules, lessons, and checks.
- Admins can add a concept to the taxonomy and link prerequisites and related concepts.
- The system prevents circular prerequisites (A requires B requires A).
- Changes to the taxonomy are reflected in search, recommendations, and the learner's concept view after publishing.
- Retiring a concept preserves the learner's historic mastery and XP.

---

### F15 — Grounded answers with citations (RAG)

All published content is automatically parsed, tagged, chunked, indexed, and linked into the knowledge base. The tutor prioritises this curated knowledge when answering and cites sources.

| | |
| --- | --- |
| **User value** | I can trust the answer and click through to the source to learn more. |
| **Business value** | Reduces hallucination risk (brand protection), differentiates from general chatbots, and is a hard requirement for universities and enterprises. |
| **Priority** | **Must** |

**Acceptance criteria**

- When relevant curated content exists, the tutor's answer cites at least one source with a link to the resource.
- Citations always point to real, published library items; the tutor never fabricates a citation (0 fabricated citations on the evaluation set).
- When no relevant curated source exists, the tutor states that it is answering from general knowledge.
- When asked something it cannot answer reliably, the tutor says so rather than guessing.
- Unpublished, archived, or draft content is never used in learner answers.
- On an expert-labelled evaluation set, at least **85%** of answers on covered topics retrieve a relevant source.

---

### F16 — Content approval workflow

Every piece of content moves through **Draft → Review → Approved → Published → Archived**. Only published content reaches learners.

| | |
| --- | --- |
| **User value** | (Learners) Only reviewed, quality content. (Instructors) Confidence and control. |
| **Business value** | Quality assurance at scale; governance that institutions require before adopting AI tutoring. |
| **Priority** | **Must** |

**Acceptance criteria**

- New and AI-generated content always starts as Draft.
- Only instructors or admins can move content to Review; only admins (or designated reviewers) can Approve and Publish.
- The author of a piece cannot be its sole approver (configurable for small teams during MVP).
- Every state change records who made it and when.
- Archiving removes content from learners and the tutor immediately without deleting it.
- Admins can see a queue of items awaiting review.

---

### F17 — Trust, safety, and privacy guardrails

Protection for learners and the brand: input screening, length limits, prompt-injection defences, rate limits, restricted code execution, data scoping per learner, and privacy compliance.

| | |
| --- | --- |
| **User value** | A safe space to learn; my data and documents stay private. |
| **Business value** | Avoids reputational, legal, and cost incidents; necessary for GDPR compliance and institutional procurement. |
| **Priority** | **Must** |

**Acceptance criteria**

- Learner documents, conversations, and progress are accessible only to that learner and authorised admins.
- The tutor refuses harmful content and attempts to override its instructions, and stays on learning topics.
- Per-user rate limits prevent abuse of AI features; limits differ by tier.
- Pasted code in chat is never executed; only the coding lab runs code, in a restricted environment.
- A privacy policy and terms of service are published; consent is captured at sign-up.
- Learners can export and delete their data.
- Users must confirm they are 16 or older at sign-up.
- A red-team test of at least 100 adversarial prompts shows no critical safety failures before launch.

---

### F18 — Subscriptions and billing

Free, Pro, and Research tiers with self-serve checkout, upgrade, downgrade, and cancellation, and regional pricing.

| | |
| --- | --- |
| **User value** | Start free; pay only when the value is clear, at a price fair for my country. |
| **Business value** | Validates willingness to pay during MVP; establishes revenue and unit economics for investors. |
| **Priority** | **Must** |

**Acceptance criteria**

- Learners can subscribe to Pro or Research monthly or annually via secure checkout.
- Entitlements apply within 1 minute of successful payment.
- Learners can cancel from settings; access continues until period end.
- Free-tier limits are enforced and clearly communicated before they are reached.
- Prices display in local currency where supported, with regional pricing for at least three price bands.
- Failed payments trigger a grace period and email before downgrade.
- Conversion events (paywall view, checkout start, purchase, cancellation) are tracked.

---

### F19 — Coding lab with AI code review

A built-in Python environment for exercises. Learners run code, see output, are graded against expected results, and receive tutor reviews that explain bugs, suggest improvements, and generate follow-up exercises.

| | |
| --- | --- |
| **User value** | Learn by doing without installing anything; get mentor-quality feedback on my code. |
| **Business value** | Hands-on practice is a key Pro feature and a strong conversion lever for career switchers. |
| **Priority** | **Should** (Python exercises and review) · **Won't** (notebooks, robotics simulations in MVP) |

**Acceptance criteria**

- Learners can write and run Python exercises attached to lessons in the browser.
- Output or errors display within 5 seconds for typical exercises.
- Submissions are graded against expected output; pass/fail is clear.
- Code review explains issues and offers hints before offering a full solution.
- Passing a coding check awards XP and updates mastery.
- At least 20 coding exercises exist across the launch paths.
- Unsafe operations (file system, network, long-running processes) are blocked with a clear message.

---

### F20 — Flashcards with spaced repetition

Flashcards generated from lessons, scheduled using spaced repetition so learners review just before they would forget.

| | |
| --- | --- |
| **User value** | Remember what I learned for the exam and the job — not just for the day. |
| **Business value** | Creates a daily reason to return (due reviews), improves long-term retention outcomes. |
| **Priority** | **Should** |

**Acceptance criteria**

- Flashcards can be generated from any completed lesson.
- The dashboard shows how many cards are due today.
- Each review asks the learner to rate recall; the next review date adjusts accordingly.
- Completing due reviews awards XP and counts toward the streak.
- Recall accuracy over time is recorded for learning-outcome measurement.

---

### F21 — Research assistant

For advanced learners: upload a paper you own and get a summary, equation explanations, research gap detection, methodology critique, reviewer simulation, citation assistance, and experimental design suggestions.

| | |
| --- | --- |
| **User value** | A tireless research partner that helps me understand, critique, and build on papers. |
| **Business value** | Anchors the premium Research tier; targets a high-willingness-to-pay segment and the university channel. |
| **Priority** | **Should** (upload, summary, equation explanation, methodology critique) · **Could** (reviewer simulation, gap detection) · **Won't** (literature review generation, research project supervision) |

**Acceptance criteria**

- Research-tier learners can upload a PDF paper up to 50 pages.
- Analysis uses only the uploaded paper (plus curated library for background) and states this clearly.
- Learners can request a summary, explanation of a specific equation, and methodology critique.
- The assistant never invents references; any suggested citation is drawn from the paper or the curated library.
- Uploaded papers are private to the uploader and can be deleted.
- Expert reviewers rate at least 80% of sampled analyses as accurate and useful.

---

### F22 — AI content generation for admins

From an uploaded source (e.g. a research paper), generate draft lesson notes, flashcards, quizzes, coding exercises, project ideas, study guides, and concept maps for human review.

| | |
| --- | --- |
| **User value** | (Instructors) Turn hours of content preparation into minutes of review. |
| **Business value** | Dramatically lowers content production cost, enabling rapid curriculum expansion and new languages. |
| **Priority** | **Should** (lesson notes, flashcards, quizzes) · **Could** (coding exercises, study guides) · **Won't** (concept maps, project ideas in MVP) |

**Acceptance criteria**

- Admins can generate lesson notes, flashcards, and quizzes from a published or draft source.
- All generated content is created as Draft and linked to its source.
- Generated items can be edited before submission for review.
- Generation of a lesson + 10 flashcards + 5-question quiz completes in under 2 minutes.
- At least 70% of generated drafts are approved with minor or no edits (tracked).

---

### F23 — Content version control

Track creation date, last modified, editor, version number, and change history; compare and restore versions.

| | |
| --- | --- |
| **User value** | (Instructors) Freedom to improve content without fear of losing good work. |
| **Business value** | Auditability for institutions; reduces cost of content errors. |
| **Priority** | **Should** (history and restore) · **Could** (visual side-by-side compare) |

**Acceptance criteria**

- Every published change creates a new version with editor and timestamp.
- Admins can view the history of any asset and restore a previous version.
- Restoring creates a new version rather than deleting history.
- Learners always see the latest published version.

---

### F24 — Admin analytics dashboard

Most visited lessons, most difficult concepts, quiz pass rates, content engagement, resource effectiveness, completion rates, and knowledge gaps across learners.

| | |
| --- | --- |
| **User value** | (Instructors) Know which content works and where learners struggle. |
| **Business value** | Data-driven content investment; reporting that institutional customers will pay for. |
| **Priority** | **Should** |

**Acceptance criteria**

- Admins see the top 10 most visited lessons and the 10 concepts with the lowest pass rates.
- Quiz pass rates and completion rates are shown per path and per concept.
- Data can be filtered by date range, language, and country.
- All learner data shown is aggregated; no individual learner content is exposed without the admin role and a stated reason.
- Data refreshes at least daily.

---

### F25 — Weekly progress reports

An AI-generated weekly summary: what was learned, mastery changes, streak, time spent, weak areas, and recommendations for next week.

| | |
| --- | --- |
| **User value** | A motivating reflection and a clear plan for the week ahead. |
| **Business value** | A low-cost re-engagement channel (email/in-app) that recovers lapsing learners. |
| **Priority** | **Should** |

**Acceptance criteria**

- Every active learner receives a weekly report in-app and optionally by email, in their language.
- The report includes concepts mastered, XP, streak, top weak concept, and up to three recommendations.
- Learners can unsubscribe from report emails.
- Report email open and click-through rates are tracked.

---

### F26 — Tutor avatar and personality

Learners choose the tutor's personality (Friendly, Professional, Academic, Motivational, Strict Coach, Socratic Mentor) and a visual avatar (age appearance, gender presentation). Voice accents (British, American, French, Spanish, Nigerian, and others) follow with voice.

| | |
| --- | --- |
| **User value** | A tutor that feels like *mine*, building an emotional connection and accountability. |
| **Business value** | Emotional attachment increases retention; personality choice is a delightful, marketable feature. |
| **Priority** | **Should** (personality) · **Could** (static visual avatar) · **Won't** (voice, accents, animated avatar in MVP) |

**Acceptance criteria**

- Learners can choose one of six personalities; the tone of tutor responses changes accordingly while accuracy is unaffected.
- (Could) Learners can select from at least six static avatar images spanning age and gender presentation.
- The chosen personality and avatar remain consistent across sessions and languages.
- Personality can be changed at any time.

---

### F27 — Career advisor

Maps the learner's skills and mastery to target roles (e.g. ML Engineer, RL Engineer, Robotics Engineer, AI Researcher), identifies skill gaps, and suggests next steps.

| | |
| --- | --- |
| **User value** | Confidence that what I'm learning leads to a real job. |
| **Business value** | Strong motivator for career switchers (high-value segment); future revenue via job partnerships. |
| **Priority** | **Could** (basic advice in tutor chat) · **Won't** (full career surface, job matching in MVP) |

**Acceptance criteria**

- Learners can ask the tutor for career advice and receive a role-specific skill gap list based on their actual mastery data.
- Advice links to the concepts and paths that close the gaps.
- Advice states clearly that it is guidance, not a guarantee of employment.

---

## 9. MVP Scope

### MVP objective

**Prove that AI Mentor creates a learning habit and measurable learning gains, and that learners will pay for it.**

### Hypotheses the MVP must test

| # | Hypothesis | Validated if |
| --- | --- | --- |
| H1 | Personalised onboarding gets learners to value fast | ≥70% onboarding completion; ≥60% complete first lesson on day 1 |
| H2 | Socratic, grounded tutoring produces real learning | Average mastery gain ≥ +25 points on pre/post checks; ≥4.2/5 tutor satisfaction |
| H3 | Gamification + daily challenges create a habit | ≥40% week-1 retention; ≥3 sessions/week among active learners |
| H4 | Learners value multilingual teaching | ≥20% of FR/ES-market learners choose a non-English language; equal or better retention vs English |
| H5 | Learners will pay | ≥3% Free-to-paid conversion within 30 days among activated learners (beta) |
| H6 | Admin-curated content improves trust | ≥85% of covered answers cite a source; lower "incorrect" flags on grounded vs ungrounded answers |

### MVP feature set

| Included in MVP | Notes |
| --- | --- |
| Accounts, roles, profiles (F1) | Email and Google sign-in |
| Onboarding and placement (F2) | Adaptive, under 5 minutes |
| Socratic AI tutor (F3) | Streaming, grounded, cited |
| Adaptive teaching controls (F4) | All five controls |
| Four launch learning paths + concept graph (F5) | AI Fundamentals, RL, Robotics, LLM Engineering |
| Recommendations and study plans (F6) | |
| Quiz system (F7) | Five core question types |
| Daily challenges (F8) | Quiz, coding, lesson-goal types |
| Gamification (F9) | XP, levels, streaks, badges, titles |
| Leaderboards (F10) | Global and country |
| Progress dashboard (F11) | |
| Multilingual EN/FR/ES (F12) | Text only |
| Admin knowledge repository (F13) | Core document formats |
| Curriculum, taxonomy, knowledge graph (F14) | Form-based editing |
| Grounded answers with citations (F15) | |
| Approval workflow (F16) | |
| Trust, safety, privacy (F17) | |
| Subscriptions and billing (F18) | Free, Pro, Research |
| **Should:** Coding lab (F19), flashcards (F20), research assistant core (F21), AI content generation core (F22), version history (F23), admin analytics (F24), weekly reports (F25), tutor personality (F26) | Ship if possible; first fast-follow otherwise |

### MVP platform

- Responsive web application, optimised for both desktop and mobile browsers.
- Native mobile apps are post-MVP.

### MVP timeline (8–12 weeks)

| Weeks | Milestone | Outcome |
| --- | --- | --- |
| 1–2 | Foundations | Accounts, roles, curriculum catalogue for four paths, onboarding flow designed and tested with 5–8 users |
| 3–5 | Core learning loop | Tutor, teaching controls, concept graph, quizzes, mastery, dashboard |
| 6–7 | Engagement and content | Gamification, daily challenges, leaderboards, admin portal, approval workflow, grounding and citations |
| 8–9 | Localisation and monetisation | French and Spanish content review, subscriptions, regional pricing; Should-features as capacity allows |
| 10 | Quality and safety | Expert accuracy evaluation, red-team testing, accessibility and performance passes |
| 11–12 | Closed beta | 100–300 learners from target personas; instrument, interview, iterate; release decision |

---

## 10. Out-of-Scope Items

These are explicitly **not** in the MVP. They are deferred, not abandoned, unless noted.

| Item | Reason for deferral | Target |
| --- | --- | --- |
| Native iOS and Android apps | Validate the learning loop on web first | Phase 2 |
| Voice tutor, voice accents, voice translation | Cost and complexity; text proves value first | Phase 2 |
| Animated / 3D tutor avatar | Delight feature; not needed to test core hypotheses | Phase 3 |
| Full notebook environment (Jupyter-style) | Simple exercises suffice for MVP | Phase 2 |
| Robotics simulations, 3D kinematics, path-planning visualisers | High build cost; text + diagrams first | Phase 2 |
| Additional paths: Deep Learning, Generative AI, MLOps, Data Science, Computer Vision, AI Research methods (full) | Focus on four launch paths with depth | Phase 2 |
| Friends and regional leaderboards | Needs social graph; global/country first | Phase 2 |
| Research, debugging, and robotics daily challenges | Start with three challenge types | Phase 2 |
| Community features (forums, peer review, community challenges) | Moderation burden; needs critical mass | Phase 2–3 |
| Research project supervision and literature review generation | Requires higher accuracy bar and expert validation | Phase 3 |
| Full career surface and job matching | Needs employer partnerships | Phase 3 |
| Certificates and accredited certification | Requires assessment rigour and partners | Phase 2 (certificates) / Phase 3 (accredited) |
| Institution / enterprise accounts (SSO, cohorts, instructor dashboards for classes) | B2C validation first | Phase 2 |
| Video and audio ingestion in the knowledge base | Processing cost; documents first | Phase 2 |
| Drag-and-drop curriculum builder | Form-based editing suffices | Phase 2 |
| Languages beyond EN/FR/ES | Prove the multilingual model first | Phase 3 |
| Offline mode | Connectivity solutions for emerging markets after MVP | Phase 3 |
| Users under 16 | Requires a separate safeguarding and consent model | Not planned |
| General-purpose coding assistant for production work | Not our product | Not planned |

---

## 11. Success Metrics (KPIs)

### North Star Metric

> **Weekly Mastering Learners (WML):** the number of learners who, in a given week, master at least one new concept (pass its check at the mastery threshold).

**Why:** it combines engagement (they came back) with learning outcome (they actually learned). It cannot be gamed by empty clicks, and it correlates with both retention and willingness to pay.

### KPI tree

```text
                       Weekly Mastering Learners (North Star)
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
     Acquisition                  Engagement                    Learning quality
  (new sign-ups,              (sessions/week,                (mastery gain,
   activation rate)            challenge participation,       quiz accuracy trend,
         │                     streaks)                       concepts mastered)
         │                             │                             │
         └──────────────┬──────────────┴──────────────┬──────────────┘
                    Retention                     Monetisation
             (D1, D7, D30, W4)              (conversion, MRR, churn)
```

### Primary KPIs

| Category | KPI | Definition | MVP / beta target | 12-month target **(hypothesis)** |
| --- | --- | --- | --- | --- |
| North Star | Weekly Mastering Learners | Learners mastering ≥1 new concept in the week | 50+ | 10,000+ |
| Acquisition | Registered learners | Accounts created | 300 (beta) | 25,000 |
| Activation | Activation rate | % of sign-ups who complete onboarding **and** pass their first check within 24 hours | 50% | 60% |
| Activation | Onboarding completion | % of sign-ups who finish onboarding | 70% | 80% |
| Engagement | Active learners | Learners with ≥1 learning action in the week | 100+ | 7,500 |
| Engagement | Sessions per active learner per week | | 3+ | 4+ |
| Retention | Week-1 retention | % of new learners active in week 2 | 40% | 45% |
| Learning | Mastery gain | Average improvement pre vs post on a concept check | +25 points | +30 points |
| Monetisation | Free-to-paid conversion (30-day, activated) | | 3% | 5% |
| Satisfaction | Tutor satisfaction (CSAT) | Average rating of tutor replies | 4.2 / 5 | 4.5 / 5 |
| Satisfaction | Net Promoter Score | | 30+ | 45+ |
| Quality | Tutor accuracy | Expert-rated correct answers on evaluation set | 90% | 95% |
| Performance | Tutor first response | Time until reply starts streaming (p95) | < 1.5s | < 1.0s |

### Business KPIs (post-launch)

| KPI | Definition | 12-month target **(hypothesis)** |
| --- | --- | --- |
| Monthly Recurring Revenue (MRR) | | $5,700+ (≈ $68K ARR) |
| Paying subscribers | | 750+ |
| Monthly paid churn | % of paid subscribers cancelling per month | < 6% |
| Customer Acquisition Cost (CAC) | Blended marketing spend ÷ new paying subscribers | < $30 |
| Lifetime Value (LTV) | ARPU × gross margin ÷ churn | > 3× CAC |
| AI cost per monthly active learner | Model + retrieval cost | < $0.60 Free, < $3.00 Pro |
| Gross margin | | > 70% |
| Organic share of sign-ups | Referral, share, SEO, word of mouth | > 50% |

---

## 12. Engagement Metrics

| Metric | Definition | Target | Why it matters |
| --- | --- | --- | --- |
| DAU / MAU ratio ("stickiness") | Daily actives ÷ monthly actives | ≥ 25% | Indicates habit formation |
| Sessions per active learner per week | | ≥ 3 | Core habit measure |
| Average session length | Time from first to last action in a session | 12–20 min | Long enough to learn, short enough to fit a day |
| Learning actions per session | Lessons, quiz answers, code runs, reviews | ≥ 8 | Distinguishes real learning from browsing |
| Tutor messages per session | | 6–15 | Shows dialogue depth; too high may signal confusion |
| Socratic engagement rate | % of tutor checking questions the learner answers (rather than skipping to the answer) | ≥ 60% | Learners are thinking, not copying |
| Daily challenge participation | % of daily actives who attempt the daily challenge | ≥ 60% | Primary daily trigger |
| Daily challenge completion | % of attempts completed | ≥ 80% | Challenges are pitched right |
| Quiz completion rate | % of started quizzes finished | ≥ 75% | Quizzes are the right length and difficulty |
| Coding lab usage | % of weekly actives who run code | ≥ 30% (Pro: ≥ 50%) | Hands-on practice adoption |
| Flashcard review completion | % of due cards reviewed on the due day | ≥ 50% | Spaced repetition effectiveness |
| Active streak share | % of weekly actives with a streak of 3+ days | ≥ 35% | Habit strength |
| Median streak length | | ≥ 5 days | |
| Teaching control usage | % of learners who change a teaching setting at least once | ≥ 40% | Validates personalisation as valued |
| Language switch usage | % of learners using a non-English language | Tracked; ≥ 20% in FR/ES markets | Validates multilingual investment |
| Leaderboard views per week | % of weekly actives viewing leaderboards | ≥ 30% | Social motivation |
| Share rate | % of learners sharing a badge or level | ≥ 5% | Organic growth driver |
| Citation click-through | % of cited answers where the learner opens the source | ≥ 10% | Trust and depth |

**Guardrail metrics** (must not deteriorate while optimising engagement):

- Mastery gain must not drop when engagement features are added.
- XP earned per concept mastered must stay stable (detects farming).
- Proportion of learners hitting the daily XP cap should stay below 10%.
- Tutor "this was wrong" flags should stay below 3% of rated replies.

---

## 13. Retention Metrics

### Cohort retention targets

| Metric | Definition | MVP target | 12-month target **(hypothesis)** |
| --- | --- | --- | --- |
| Day-1 retention | % of new learners who return the next day | 45% | 50% |
| Day-7 retention | % active on day 7 | 30% | 35% |
| Week-1 retention | % active at least once in week 2 | 40% | 45% |
| Day-30 retention | % active on day 30 | 15% | 20% |
| Week-4 retention | % active at least once in week 5 | 25% | 30% |
| Paid subscriber monthly retention | | — | ≥ 94% |
| Annual plan renewal | | — | ≥ 60% |

### Retention drivers to monitor

| Driver | Metric | Hypothesis |
| --- | --- | --- |
| Activation quality | Retention by whether the learner passed a check on day 1 | Day-1 mastery doubles W4 retention |
| Streaks | Retention by streak length at day 7 | Learners with 5+ day streaks are 3× more likely to be active at day 30 |
| Study plan | Retention with vs without an active study plan | Plans increase W4 retention by 10 points |
| Language | Retention by language | Native-language learners retain equal or better |
| Teaching style | Retention by whether learner customised teaching | Customisers retain better |
| Path | Retention by path | Identifies paths needing content work |

### Resurrection and churn

| Metric | Definition | Target |
| --- | --- | --- |
| Resurrection rate | % of learners inactive 14+ days who return in a month | ≥ 10% |
| Streak recovery | % of broken streaks restarted within 3 days | ≥ 40% |
| Churn reasons | Captured on cancellation (too expensive, no time, too hard, achieved goal, other) | Reviewed monthly |
| Weekly report reactivation | % of lapsed learners returning within 48h of a report email | ≥ 5% |

---

## 14. Learning Outcome Metrics

Learning outcomes are our moat and our most important investor and institutional proof point. Every outcome metric must be measured with a method that cannot be inflated by engagement mechanics.

| Metric | Definition | Measurement method | Target |
| --- | --- | --- | --- |
| **Mastery gain** | Improvement on a concept check before vs after studying it | Pre-check (placement or first attempt) vs post-check of equivalent difficulty | Average +25 points (of 100) |
| **Concepts mastered per learner per week** | Concepts passing the mastery threshold | Mastery model | ≥ 2 for active learners |
| **Time to mastery** | Median minutes of study per concept mastered | Activity time per concept | Decreasing over time (signals better teaching) |
| **Long-term retention of knowledge** | Recall accuracy on spaced-repetition reviews and delayed re-checks at 7 and 30 days | Flashcard recall; surprise re-check items | ≥ 80% at 7 days; ≥ 70% at 30 days |
| **Prerequisite repair success** | % of learners who fail a concept, complete a recommended prerequisite detour, then pass | Recommendation outcomes | ≥ 60% |
| **First-attempt pass rate trend** | Change in first-attempt quiz accuracy over a learner's first 8 weeks | Quiz data | Increasing |
| **Coding proficiency** | Pass rate on first submission; reduction in attempts needed | Coding lab | First-attempt pass rate improves by 20 points over 6 weeks |
| **Path completion rate** | % of learners who start and complete a path | Path progress | ≥ 15% within 6 months (benchmark: well above typical self-paced MOOC completion) |
| **Difficulty progression** | % of learners advancing at least one depth level (e.g. Beginner → Intermediate) in 8 weeks | Adaptive difficulty data | ≥ 30% |
| **Self-reported confidence** | Learner confidence rating per concept before and after | In-app micro-survey | +1.5 points on 5-point scale |
| **Real-world outcome** | Learners reporting exam success, new role, promotion, or published paper | Quarterly survey | Tracked; case studies for marketing |

### Measurement principles

- **Equivalent forms:** pre- and post-checks use different questions of equivalent difficulty so learners cannot memorise answers.
- **Expert validation:** a sample of questions and grading is audited by subject experts each release.
- **Control comparisons:** where ethical, A/B tests compare variants (e.g. Socratic vs direct explanation) on mastery gain, not just engagement.
- **Outcome over activity:** no outcome metric counts XP, time, or messages alone.

---

## 15. Monetisation Strategy

### Model: freemium subscription, followed by institutional licensing

The Free tier must be **genuinely useful** — enough to form a habit and experience the "aha" — while the paid tiers remove limits and unlock depth, hands-on practice, and research tools.

### Tiers (pricing is a hypothesis to test in beta)

| | **Free** | **Pro** | **Research** |
| --- | --- | --- | --- |
| Target | Students, curious learners, trial | Career switchers, professionals, serious students | Graduate students, researchers, advanced engineers |
| Suggested price (high-income markets) | $0 | **$14.99 / month** or **$119 / year** | **$29.99 / month** or **$239 / year** |
| Tutor messages | 20 per day | Unlimited (fair use) | Unlimited (fair use) |
| Learning paths | AI Fundamentals + first module of each other path | All paths | All paths |
| Teaching controls | All styles; depth up to Intermediate | All styles and depths | All styles and depths, incl. PhD and full proofs |
| Quizzes and daily challenges | Yes | Yes, plus advanced and Expert difficulty | Yes, incl. PhD-level, derivation, and critique questions |
| Gamification and leaderboards | Yes | Yes | Yes |
| Multilingual | Yes | Yes | Yes |
| Coding lab and code review | 3 runs per day | Unlimited | Unlimited |
| Flashcards | Yes (limited decks) | Unlimited | Unlimited |
| Study plans | 1 basic plan | Unlimited, adaptive | Unlimited, adaptive |
| Weekly reports | Summary | Full report with recommendations | Full report |
| Research assistant (paper upload and analysis) | — | — | Yes (e.g. 30 papers / month) |
| Career advisor | Basic | Full | Full |
| Priority on new features | — | — | Yes |

### Regional pricing

Purchasing-power-adjusted pricing is essential to the strategy in Africa, Latin America, and other emerging markets.

| Band | Example markets | Pro monthly (indicative) |
| --- | --- | --- |
| Band A | US, UK, Western Europe, Canada | $14.99 |
| Band B | Eastern Europe, Latin America upper-middle income | $7.99 |
| Band C | Nigeria, Kenya, Ghana, francophone West Africa, India | $3.99 |

Additional levers: **student discount** (verified, 40% off), **annual plans** (about 33% off), and local payment methods where available.

### Conversion levers

| Lever | Mechanism |
| --- | --- |
| Usage limits | Free daily tutor messages and coding runs, reached during engaged sessions |
| Depth gates | Advanced depth, mathematical proofs, and full paths in Pro |
| Free trial | 7-day Pro trial after activation (not at sign-up) |
| Moments of high intent | Upgrade offers after a streak milestone, path milestone, or failed check with a recommended advanced resource |
| Study plan commitment | Learners who set a goal date are offered an annual plan aligned to it |
| Research identity | Research tier marketed to graduate programmes and research communities |

### Future revenue streams

| Stream | Description | Phase |
| --- | --- | --- |
| **Institutional licensing (B2B2C)** | Universities and bootcamps license seats; instructors upload course material, see class analytics | Phase 2 |
| **Enterprise upskilling (B2B)** | Team plans with SSO, admin reporting, custom paths | Phase 2–3 |
| **Certificates** | Paid, proctored assessment-backed certificates per path | Phase 2 |
| **Accredited certification** | Partner-accredited professional credentials | Phase 3 |
| **Government and NGO programmes** | National AI skilling contracts, especially in Africa | Phase 3 |
| **Expert content marketplace** | Subject experts publish premium paths and share revenue | Phase 3 |
| **Talent marketplace** | Employers sponsor challenges and recruit verified-mastery learners | Phase 3 |

### Unit economics guardrails

- Keep AI cost per Free monthly active learner low through message limits, grounding answers in curated content, caching common explanations, and routing simple requests to cheaper models.
- The tutor's fallback to authored content means the product degrades gracefully, not catastrophically, if model costs spike or a provider fails.
- Target blended gross margin above 70% by month 12.

### Monetisation experiments in beta

1. Price sensitivity: two price points per band.
2. Trial timing: at activation vs after the first streak of 3 days.
3. Message limit: 15 vs 25 per day on Free.
4. Annual vs monthly default on the checkout page.

---

## 16. Risks and Dependencies

### Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| R1 | **Incorrect or hallucinated answers** damage trust | Medium | High | Ground answers in curated content; citations; expert evaluation set; "I don't know" behaviour; learner flagging; tutor accuracy release gate | Product + AI |
| R2 | **AI costs exceed revenue** per learner | Medium | High | Free-tier limits; caching; model routing; cost per learner as a tracked KPI; fallback to authored content | Product + Finance |
| R3 | **"Why not just use ChatGPT?"** — weak perceived differentiation | High | High | Lead with curriculum, mastery tracking, prerequisites, gamification, citations; demonstrate in first session; outcome case studies | Product + Marketing |
| R4 | **Gamification overshadows learning** (XP farming, shallow engagement) | Medium | Medium | XP only for real learning; daily cap; titles tied to mastery; guardrail metrics | Product + Design |
| R5 | **Content supply bottleneck** — not enough high-quality lessons across 4 paths × 3 languages | High | High | AI content generation with human review; recruit subject experts; prioritise depth on high-traffic concepts | Content |
| R6 | **Translation quality** in technical French and Spanish | Medium | Medium | Fluent subject-matter reviewers; glossary of terms; keep English technical terms in brackets | Content |
| R7 | **Low conversion** due to price sensitivity in target markets | Medium | High | Regional pricing; student discounts; institutional channel; test price points | Product + Growth |
| R8 | **Model provider outage or policy change** | Medium | High | Multi-provider routing; fallback to authored curriculum | Engineering |
| R9 | **Privacy and regulatory compliance** (GDPR, data from minors, education regulations) | Medium | High | 16+ age gate; consent; data export/deletion; data processing agreements with providers; legal review before launch | Legal + Product |
| R10 | **Copyright** of uploaded content (admin and learner uploads) | Medium | Medium | Admin attestation of rights; learners analyse only papers they own; takedown process | Legal + Content |
| R11 | **Coding lab abuse or security breach** | Low | High | Restricted execution environment; resource limits; security review and testing | Engineering |
| R12 | **Leaderboard cheating or toxicity** | Medium | Low | Anomaly detection; display names; opt-out; no free-text social features in MVP | Product |
| R13 | **Scope creep** delays MVP beyond 12 weeks | High | Medium | Strict MoSCoW; weekly scope review; Should-features are first to slip | Product |
| R14 | **Competitor launches similar AI tutor** (big platform or AI lab) | High | Medium | Move fast in niche depth (RL, robotics, research) and multilingual emerging markets; build content and data moat | Leadership |
| R15 | **Learners feel the Socratic approach is slow or frustrating** | Medium | Medium | Always allow "just show me"; tune hint depth by persona; measure CSAT by mode | Design + AI |
| R16 | **Small beta sample** produces unreliable metrics | Medium | Medium | Recruit 300 learners across personas; combine metrics with interviews; treat targets as directional | Research |

### Dependencies

| Dependency | Type | Needed for | Risk if unavailable | Fallback |
| --- | --- | --- | --- | --- |
| AI model providers (OpenAI, Anthropic, Google) | External | Tutor, quizzes, content generation | Core experience degraded | Multi-provider routing; authored curriculum fallback |
| Authentication provider (Clerk) | External | Sign-in, roles | Users cannot sign in | Status monitoring; vendor SLA |
| Payments provider (Stripe) | External | Subscriptions | No revenue collection | Grace periods; manual reconciliation |
| Vector search (Qdrant) | External/infra | Grounded answers and citations | Ungrounded answers | Tutor states it is answering from general knowledge; local index for development |
| Cloud hosting (Vercel, Azure) | External | Availability | Downtime | Monitoring, backups, incident runbook |
| Subject-matter experts | People | Content creation, review, accuracy evaluation | Content gaps, quality risk | Contract a pool of 6–10 experts across AI, RL, robotics, LLMs |
| Translators with technical expertise | People | FR and ES launch quality | Weak localisation | Phase languages; English-first for advanced content |
| Beta learners (target personas) | People | Validating hypotheses | No evidence for investors | University partnerships, AI communities, social channels in Nigeria, Spain, France, Canada, Latin America |
| Legal counsel | People | Privacy policy, terms, copyright | Launch blocked | Engage before week 8 |

---

## 17. Release Criteria

The MVP is released to public launch only when **all** Must criteria are met. Should criteria failing produces a documented decision, not a block.

### Functional

| Criterion | Level |
| --- | --- |
| All Must features (F1–F18) meet their acceptance criteria | Must |
| A new learner can complete sign-up → onboarding → first lesson → first passed check → first XP without assistance | Must |
| All four launch paths are complete with lessons and checks for every concept | Must |
| Admin can upload, tag, generate (if F22 shipped), review, approve, and publish content end to end | Must |
| Subscription purchase, upgrade, cancellation, and entitlement changes work in production payment mode | Must |
| No open critical or high-severity defects; medium defects have a documented plan | Must |

### Quality and trust

| Criterion | Level |
| --- | --- |
| Tutor accuracy ≥ 90% on an expert-labelled evaluation set of at least 300 questions across all paths and three languages | Must |
| Zero fabricated citations on the evaluation set | Must |
| Auto-generated quiz answer keys ≥ 95% correct on expert audit | Must |
| Red-team test of ≥ 100 adversarial prompts with no critical failures | Must |
| French and Spanish content reviewed by fluent subject-matter reviewers | Must |
| Tutor CSAT ≥ 4.0 / 5 in closed beta | Must |

### Performance and reliability

| Criterion | Level |
| --- | --- |
| Tutor reply begins streaming in under 1.5 seconds at p95 | Must |
| Dashboard loads in under 2 seconds at p95 on a typical mobile connection | Must |
| 99.5% availability during the final two weeks of beta | Must |
| Graceful fallback when the AI provider is unavailable (verified by test) | Must |
| Supports 1,000 concurrent learners without degradation (load tested) | Should |

### Security, privacy, and compliance

| Criterion | Level |
| --- | --- |
| Learner data isolation verified by test (no learner can access another's data) | Must |
| Development authentication modes impossible to enable in production | Must |
| Privacy policy, terms of service, and cookie consent published | Must |
| Data export and deletion available | Must |
| Coding lab security review passed | Must (if F19 ships) |

### Accessibility and usability

| Criterion | Level |
| --- | --- |
| WCAG 2.1 AA for core learner flows (onboarding, tutor, quiz, dashboard) | Must |
| Fully usable on mobile browsers (360px width and up) | Must |
| Usability test with ≥ 8 target users: ≥ 80% complete the first-session journey unaided | Must |

### Measurement readiness

| Criterion | Level |
| --- | --- |
| All KPIs in Sections 11–14 are instrumented and visible in a product analytics dashboard | Must |
| Pre/post mastery measurement in place for all launch-path concepts | Must |
| Conversion funnel tracked from paywall view to purchase | Must |

### Beta exit criteria (go / no-go for public launch)

| Signal | Go threshold |
| --- | --- |
| Onboarding completion | ≥ 65% |
| Week-1 retention | ≥ 35% |
| Average mastery gain | ≥ +20 points |
| Tutor CSAT | ≥ 4.0 / 5 |
| "Very disappointed if AI Mentor disappeared" (Sean Ellis test) | ≥ 30% of active beta learners |
| At least one paid conversion signal | ≥ 2% of activated beta learners purchase or pre-commit |

---

## 18. Product Roadmap

The roadmap is outcome-oriented. Dates are relative to MVP kick-off (Week 1 = mid-October 2026) and are planning estimates.

### Phase 0 — MVP and closed beta (Q4 2026, Weeks 1–12)

**Outcome:** Prove habit, learning gains, and willingness to pay.

- Onboarding, Socratic tutor, teaching controls
- Four launch paths with concept graph
- Quizzes, daily challenges, gamification, global and country leaderboards
- Progress dashboard
- English, French, Spanish
- Admin knowledge portal, approval workflow, grounded answers with citations
- Free, Pro, Research subscriptions
- Should-features as capacity allows: coding lab, flashcards, research assistant core, content generation, weekly reports, tutor personality

### Phase 1 — Public launch and product-market fit (Q1 2027)

**Outcome:** 5,000+ registered learners; W4 retention ≥ 25%; first $1K+ MRR.

- Ship all remaining MVP Should-features
- Friends leaderboards and social sharing improvements
- Research, debugging, and robotics daily challenges
- Weekly and monthly reports, email re-engagement
- Expanded badge and title system
- Pricing and paywall optimisation from beta experiments
- Growth: referral programme, SEO landing pages per concept, university ambassador programme in Nigeria, France, Spain, Canada, and Latin America

### Phase 2 — Depth, mobile, and institutions (Q2–Q3 2027)

**Outcome:** 25,000+ learners; first institutional customers; certificates revenue.

- **Native iOS and Android apps** with offline flashcards
- **Voice tutor** with accents (British, American, French, Spanish, Nigerian)
- **Notebook-style coding environment** and in-browser ML/RL projects
- **Interactive robotics visualisers** (kinematics, path planning, RL environments)
- **New paths:** Deep Learning, Generative AI, MLOps, Data Science, Computer Vision
- **Institution accounts:** cohorts, class analytics, SSO, instructor-uploaded course material
- **Path certificates** backed by proctored assessment
- Video and audio ingestion; drag-and-drop curriculum builder; side-by-side version compare
- Community challenges and moderated discussion

### Phase 3 — Platform and ecosystem (Q4 2027 – 2028)

**Outcome:** 500,000 learners; ~$4M ARR **(hypothesis)**; recognised credential.

- **Research supervision:** literature review generation, research gap detection, reviewer simulation, experimental design, reproducible-research workflows
- **Animated, persistent tutor avatar** with emotional continuity
- **Full career surface:** skill passports, portfolio projects, job matching, employer-sponsored challenges
- **Accredited certification** with university and industry partners
- **Expert content marketplace** with revenue sharing
- **Enterprise upskilling** plans
- Additional languages (e.g. Portuguese, Arabic, Swahili, Hindi)
- Low-bandwidth and offline-first experience for emerging markets
- Government and NGO skilling programmes

### Roadmap at a glance

```text
            Q4 2026          Q1 2027          Q2–Q3 2027              Q4 2027 – 2028
           ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  ┌───────────────────────┐
Learning   │ Tutor, 4    │  │ Should-     │  │ +5 paths, voice,   │  │ Research supervision, │
           │ paths, quiz │  │ features    │  │ notebooks, sims    │  │ animated avatar       │
           ├─────────────┤  ├─────────────┤  ├────────────────────┤  ├───────────────────────┤
Engagement │ XP, streaks,│  │ Friends LB, │  │ Mobile apps,       │  │ Community, sponsored  │
           │ challenges  │  │ referrals   │  │ community          │  │ challenges            │
           ├─────────────┤  ├─────────────┤  ├────────────────────┤  ├───────────────────────┤
Business   │ Free/Pro/   │  │ Pricing     │  │ Institutions,      │  │ Accreditation, B2B,   │
           │ Research    │  │ optimisation│  │ certificates       │  │ marketplace, gov.     │
           └─────────────┘  └─────────────┘  └────────────────────┘  └───────────────────────┘
```

---

## 19. Future Vision

### The five-year picture

**AI Mentor becomes the world's most personal AI education platform — the place where anyone, in their own language, can go from curiosity to career to contribution in Artificial Intelligence.**

1. **A lifelong mentor, not a course.** The same tutor knows a learner from their first Python script through their first job, their first paper, and their next career move. It remembers what they struggled with, what inspired them, and how they learn best.

2. **The most complete map of AI knowledge.** A living concept graph, curated and improved by thousands of subject experts and validated by millions of learning interactions, spanning foundations to frontier research.

3. **Proof of skill, not proof of attendance.** Credentials backed by demonstrated mastery — passed checks, working code, completed projects, and research contributions — trusted by employers and universities.

4. **From learner to researcher.** A guided pathway from understanding papers to reproducing them, critiquing them, designing experiments, and publishing — opening research careers to people who never had access to a supervisor.

5. **Global by design.** Teaching in many languages, priced fairly for every economy, working on modest devices and connections, so that talent anywhere can participate in the AI economy.

6. **An ecosystem.** Universities deliver courses through AI Mentor; companies upskill teams and recruit verified talent; experts publish and earn; governments run national programmes on it.

### Long-term moats

| Moat | How it compounds |
| --- | --- |
| **Learning data** | Every interaction reveals which explanations work for which learners, improving personalisation for everyone |
| **Curated knowledge graph** | Expert-governed, versioned content is slow and expensive for competitors to replicate |
| **Trusted credentials** | Mastery-based certificates grow in value as employer recognition grows |
| **Network effects** | Leaderboards, community challenges, expert marketplace, and employer partnerships each strengthen with scale |
| **Emotional connection** | A persistent, personal tutor that learners feel attached to creates high switching costs |

### The promise

> *Duolingo's engagement. A university's depth. An expert mentor's attention. The power of modern AI. In your language, at your pace, for your goals.*

---

## Appendix

### A. Glossary

| Term | Meaning |
| --- | --- |
| Activation | A new learner completes onboarding and passes their first concept check within 24 hours |
| Concept | The smallest unit of knowledge in the curriculum (e.g. "Bellman equation") |
| Concept graph / knowledge graph | The map of concepts and their prerequisite and related relationships |
| Mastery | A learner's demonstrated understanding of a concept, based on checks and practice |
| Mastery threshold | The level at which a concept is considered mastered and its dependants unlocked for recommendation |
| Grounding / RAG | Answering from the curated knowledge library rather than the AI model's memory alone |
| Socratic tutoring | Teaching by asking guiding questions so the learner reasons to the answer |
| Spaced repetition | Scheduling reviews at increasing intervals just before the learner would forget |
| WML | Weekly Mastering Learners — the North Star Metric |
| MoSCoW | Prioritisation: Must, Should, Could, Won't (this release) |

### B. Open questions

| # | Question | Owner | Decide by |
| --- | --- | --- | --- |
| Q1 | Final pricing per band and trial length | Product + Finance | End of beta |
| Q2 | Mastery threshold value (e.g. 80% on a check) and how mastery decays over time | Product + Learning science | Week 3 |
| Q3 | Which concepts get full French/Spanish human review vs machine translation with spot checks at launch | Content | Week 4 |
| Q4 | Should the Free tier include the coding lab at all, or only Pro? | Product | Week 6 |
| Q5 | Leaderboard scoring weights (XP vs quiz performance vs challenges) | Product + Design | Week 6 |
| Q6 | Beta recruitment mix by persona and country | Research + Growth | Week 8 |
| Q7 | Data retention period for conversations and uploaded papers | Legal | Week 8 |

### C. Traceability to source specifications

| Source specification area | PRD feature(s) |
| --- | --- |
| Personalised learning engine and onboarding | F2, F6 |
| Fully adaptive teaching style; adjustable learning depth | F4 |
| Comprehensive curriculum coverage | F5 (launch paths), Roadmap Phase 2 (additional paths) |
| Gamification system, leaderboards, daily challenges | F8, F9, F10 |
| Intelligent quiz system | F7 |
| AI tutor avatar system | F26 |
| Multilingual support | F12 |
| Learning analytics | F11, F25 |
| Coding lab | F19 |
| Research assistant | F21 |
| Admin: content repository and knowledge library | F13 |
| Admin: curriculum management, taxonomy, knowledge graph | F14 |
| Admin: RAG knowledge base | F15 |
| Admin: version control | F23 |
| Admin: AI content generation | F22 |
| Admin: content approval workflow | F16 |
| Admin: resource recommendations engine | F6 |
| Admin: analytics dashboard | F24 |
| Accounts, roles, subscriptions (ReadMe) | F1, F18 |
| Security (ReadMe) | F17 |
| Career advisor (ReadMe) | F27 |
