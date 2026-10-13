# Roadmap

This repository is the first running slice. This page lists the next engineering steps for that slice. The product roadmap for the five-application ecosystem, releases R1 to R5, is [platform/15-roadmap.md](platform/15-roadmap.md). Items 1, 3, and 6 below are R1 gates there, alongside the R1 foundations (tenancy, scoped roles, and the split of the admin portal into the Admin App and Content Studio).

## In this build

- Socratic and direct tutor, with a scripted opening so the model cannot skip the question
- Four paths, prerequisite graph, recommendations, mastery, XP, streaks, badges
- Authored quizzes with server grading
- SM-2 flashcards
- Restricted Python lab and one Q-learning project
- Document ingestion with citations, extractive by default
- Clerk-ready JWT verification, Stripe checkout that stays off until configured
- Docker Compose, CI (lint, test, frontend typecheck and build), image publish on tag

## Next, in order

1. A real OTLP exporter, and a shared rate limiter once more than one API replica runs.
2. Replace the child-interpreter lab with the gVisor runner pool ([ADR 0028](adr/0028-sandbox-runner-pool.md), Firecracker fallback) before the lab is enabled in production.
3. A job queue for ingestion. OCR of scanned PDFs only after that queue exists.
4. FSRS, implemented against the published algorithm and tested beside SM-2, not a partial port.
5. Lesson, path, and item builders in Content Studio. The catalog file remains the seed, not the long-term CMS.

Hosted builds refuse `NEXT_PUBLIC_DEV_AUTH` and require Clerk. Streaming tutor replies, onboarding, review-queue actions, CSV import, model-drafted library notes, and Learner Settings (profile plus teaching preferences that the tutor, catalog, and study plan actually use) are in this build.

## Explicitly later

Multilingual content, daily challenges, country leaderboards, voice, a 3D robotics visualiser, and mobile apps are described in [Requirements.md](Requirements.md). They are outside the current API.
