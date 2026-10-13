You are a Principal Software Architect, Staff AI Engineer, UX Designer, and Senior Full-Stack Developer.

Build a production-ready SaaS platform called AI Mentor.

Product Vision

AI Mentor is a next-generation AI learning platform that teaches:

Artificial Intelligence
Machine Learning
Deep Learning
Reinforcement Learning
Data Science
Robotics
LLM Engineering
AI Research Methods

The platform should function as:

AI Tutor
Socratic Teacher
Coding Mentor
Quiz Generator
Research Assistant
Career Coach
Study Planner

The objective is to teach users from beginner level to PhD/research level.

Tech Stack

Frontend:

Next.js 15 (App Router)
TypeScript
TailwindCSS
ShadCN UI
Framer Motion
TanStack Query
Zustand

Backend:

FastAPI
Python 3.12

Database:

PostgreSQL

ORM:

SQLAlchemy
Alembic

Authentication:

Clerk

Payments:

Stripe

Vector Database:

Qdrant

AI Layer:

OpenAI
Anthropic
Gemini

Observability:

OpenTelemetry
Langfuse

Infrastructure:

Docker
Docker Compose

Deployment:

Vercel
Azure
AWS
Architecture

Implement clean architecture.

frontend/

backend/

infrastructure/

docs/

scripts/



Backend separation:

app/

    api/
    services/
    agents/
    repositories/
    models/
    schemas/
    middleware/
    core/
    prompts/


Follow:

SOLID
Domain Driven Design
CQRS where useful
Dependency Injection
Repository Pattern
Core Features
1. Authentication

Implement:

Sign up
Login
OAuth
Role system

Roles:

Student
Instructor
Admin
2. AI Tutor Chat

ChatGPT style interface.

Capabilities:

Explain concepts
Answer questions
Generate examples
Generate exercises

Support:

markdown
code highlighting
math equations
diagrams
3. Socratic Teaching Engine

Tutor should not immediately give answers.

Instead:

Example:

Student:

"Teach me Reinforcement Learning"

Tutor:

"What do you think an agent does in an environment?"

Create system prompts implementing:

active recall
guided discovery
scaffolding
spaced repetition
4. Learning Paths

Create predefined tracks.

Track examples:

AI Fundamentals
Python
Statistics
Linear Algebra
Machine Learning
Reinforcement Learning
MDP
Bellman
Dynamic Programming
MC Methods
TD Learning
Q-Learning
DQN
PPO
SAC
Multi-Agent RL
Robotics
ROS2
SLAM
Navigation
Computer Vision
RL Robotics
5. Progress Tracking

Track:

lessons completed
quiz scores
concepts mastered
coding projects completed

Create mastery score:

0-100


Dashboard should display:

strengths
weaknesses
recommended lessons
6. Knowledge Graph

Create concept relationships.

Example:

RL
 ├── Agent
 ├── Policy
 ├── Reward
 ├── MDP
 └── Bellman


Features:

dependency mapping
prerequisite detection
recommendation engine
7. Quiz Generator

Generate:

MCQ
Short answer
Coding challenges
Research questions

Difficulty:

Beginner
Intermediate
Advanced
Expert
PhD

Include automated grading.

8. Coding Lab

Students can:

write code
run code
submit solutions

Tutor should:

review code
provide hints
explain mistakes
suggest improvements

Support:

Python
RL examples
9. Flashcard System

Generate:

flashcards
spaced repetition decks

Algorithm:

Implement FSRS or SM-2.

10. Research Assistant

Users upload PDFs.

Capabilities:

summarization
equation explanation
critique generation
paper review
identify gaps
suggest future work

Use:

RAG
embeddings
Qdrant
Multi-Agent System

Create agents:

Tutor Agent

Explains concepts.

Quiz Agent

Creates assessments.

Planner Agent

Creates study plans.

Research Agent

Analyzes papers.

Coding Agent

Reviews code.

Career Agent

Suggests skills/jobs.

Implement orchestration layer.

Database Schema

Generate full schema.

Entities:

Users
Courses
Modules
Lessons
Concepts
LearningPaths
Conversations
Messages
Quizzes
Questions
QuizResults
Projects
CodeSubmissions
ResearchDocuments
Embeddings
StudyPlans
Progress
Achievements
Flashcards
Reviews


Generate migrations.

RAG System

Create ingestion pipeline.

Accept:

PDFs
DOCX
Markdown

Pipeline:

Parse
Chunk
Embed
Store vectors
Retrieve
Generate

Support citations.

API Design

Generate REST endpoints.

Example:

POST /chat

POST /quiz/generate

POST /research/analyze

POST /study-plan/create

GET /progress

GET /dashboard


Generate OpenAPI documentation.

Frontend Pages

Landing Page

Features:

Hero section
Pricing
Testimonials
FAQ

Dashboard

Sections:

Progress
Learning Paths
Recommendations

Tutor Page

Features:

Chat
Notes
Resources

Research Page

Features:

PDF Upload
Paper Analysis

Coding Lab

Features:

Editor
Execution
Feedback

Admin Portal

Features:

User management
Analytics
UI Design

Use:

Microsoft Learn quality
Coursera quality
Duolingo gamification

Colour Theme:

Primary   #2563EB
Secondary #7C3AED
Accent    #10B981


Must support:

dark mode
responsive design
accessibility WCAG AA
Gamification

Implement:

XP
Levels
Badges
Streaks
Leaderboards
Security

Implement:

JWT
Rate Limiting
RBAC
Input Validation
Prompt Injection Defense
RAG Security
Secrets Management

Follow:

OWASP Top 10
AI Prompts

Create production prompts for:

Tutor Agent
Socratic Tutor
Quiz Agent
Research Agent
Coding Agent
Planner Agent

Store in:

backend/app/prompts

DevOps

Create:

Dockerfiles
Docker Compose
GitHub Actions

Pipelines:

lint
test
build
deploy
Testing

Generate:

unit tests
integration tests
end-to-end tests

Coverage target:

90%+

Documentation

Generate:

README.md
Architecture.md
API.md
Database.md
Deployment.md

Include diagrams using Mermaid.

Deliverables

Produce:

Complete folder structure
System architecture diagram
Database ERD
API specification
Backend scaffold code
Frontend scaffold code
Docker configuration
CI/CD configuration
Initial migration scripts
MVP implementation roadmap

Begin by generating the entire folder structure and architecture before implementing the code. Then scaffold the project incrementally with production-quality code and explain all major design decisions.
