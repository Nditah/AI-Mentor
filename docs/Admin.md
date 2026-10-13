> **v2.0 note (13 October 2026).** This is the original knowledge-portal brief, kept unchanged as history. Content tooling now lives in Content Studio, a separate application: see [platform/13-knowledge-management-architecture.md](platform/13-knowledge-management-architecture.md) and [platform/14-content-studio-specification.md](platform/14-content-studio-specification.md). Platform operations stay in the Admin App.

Knowledge Management System (Admin Portal)

AI Mentor must include a comprehensive Knowledge Management and Content Administration platform that allows administrators, instructors, and subject matter experts to continuously expand, curate, and govern the educational content powering the AI Tutor.

The learning experience should not depend solely on LLM-generated knowledge. Instead, all tutoring, recommendations, quizzes, learning paths, and research guidance should be grounded in a managed knowledge repository.

Content Management Dashboard

Create a dedicated Admin Dashboard where authorised users can manage all educational resources.

Features:

Content Repository

Administrators can upload and manage:

PDFs
Research papers
Books
Lecture notes
PowerPoint presentations
Word documents
Markdown files
Websites
YouTube videos
GitHub repositories
Code samples
Datasets
Images
Audio resources

Supported formats:

PDF
DOCX
PPTX
TXT
CSV
JSON
MP4
HTML
Markdown
URL

Knowledge Library

Create a centralised digital library.

Each knowledge asset should contain:

Title
Description
Topic
Difficulty
Author
Source
Publication Date
Version
Learning Objectives
Estimated Study Time
Tags
Language

Example:

Title:
Introduction to Reinforcement Learning

Category:
Reinforcement Learning

Difficulty:
Intermediate

Topics:
MDP
Bellman Equation
Policy Optimisation

Curriculum Management

Administrators should be able to create and manage:

Learning Paths

Examples:

AI Foundations
Machine Learning Engineer
Deep Learning Specialist
Reinforcement Learning Engineer
Robotics Engineer
AI Researcher

Each learning path should include:

Courses
Modules
Lessons
Assessments
Projects
Recommended Resources

Drag-and-drop curriculum builder preferred.

Knowledge Taxonomy System

Create a hierarchical knowledge structure.

Example:

Artificial Intelligence
|
|-- Machine Learning
|   |-- Supervised Learning
|   |-- Unsupervised Learning
|
|-- Deep Learning
|   |-- CNN
|   |-- RNN
|   |-- Transformers
|
|-- Reinforcement Learning
|   |-- MDP
|   |-- Bellman Equation
|   |-- Q Learning
|   |-- PPO
|
|-- Robotics
    |-- ROS2
    |-- SLAM
    |-- Navigation


This taxonomy should power:

Search
Recommendations
Adaptive learning
Knowledge graphs
Knowledge Graph Engine

Build a relationship engine linking concepts.

The system should understand:

Prerequisites
Dependencies
Related concepts
Advanced concepts
Learning progression

Example:

Q Learning
 -> depends on MDP

PPO
 -> depends on Policy Gradient

SLAM
 -> depends on Probability Theory


The AI Mentor should use these relationships when planning learning journeys.

RAG Knowledge Base

All uploaded content should automatically pass through a RAG pipeline.

Pipeline:

Parse Content
Extract Metadata
Chunk Content
Generate Embeddings
Store in Qdrant
Build Knowledge Links
Make Searchable

The AI Tutor should prioritise this curated knowledge base when generating responses.

Responses should include citations to learning resources where appropriate.

Version Control

Knowledge assets should support versioning.

Track:

Creation Date
Last Modified Date
Editor
Version Number
Change History

Administrators should be able to:

Compare versions
Restore previous versions
Archive outdated resources
AI Content Generation

Administrators can generate resources automatically.

Example:

Upload:

Research Paper PDF


AI can generate:

Lesson Notes
Flashcards
Quizzes
Coding Exercises
Project Ideas
Study Guides
Concept Maps

Generated content can be reviewed before publication.

Content Approval Workflow

Implement publishing workflow.

States:

Draft
Review
Approved
Published
Archived


Only approved content should become available to students.

> **As built (2026-10-13).** The admin portal implements this workflow for the curated library (`/api/v1/admin/assets`):
>
> - Instructors create and edit their own drafts and submit them for review. Admins edit any draft.
> - Approval follows the four-eyes rule (Security-Compliance AZ-5): nobody approves or publishes their own work. A small team may set `CONTENT_SELF_APPROVAL=true`; each self-approval is then flagged in the audit log.
> - Only an admin publishes. Publishing chunks the body and indexes it for the tutor's retrieval; if the index is unavailable, publishing fails and the item stays approved. Archiving or returning to draft removes it from retrieval, and a return to draft starts a new version.
> - Each item carries a licence: `own-work`, `cc-by`, `cc-by-sa`, `cc-by-nc`, `public-domain`, `proprietary-licensed`, or `fair-use-excerpt`. Anything else is rejected.
> - Every edit and transition is versioned and audited.
>
> - There is no separate reviewer role in v1 (decided 2026-10-13). Administrators approve and publish.
>
> The student-facing resource browser, version restore, and the recommendation engine below are not built yet.

Resource Recommendations Engine

The system should automatically recommend resources based on:

Student performance
Weak topics
Career goals
Learning path
Preferred learning style

Example:

If a learner struggles with Bellman Equations:

Recommend:
- Beginner Lesson
- Visual Explanation
- Practice Quiz
- RL Simulation
- Research Paper

Analytics Dashboard

Provide insights for administrators.

Metrics:

Most visited lessons
Most difficult concepts
Quiz pass rates
Content engagement rates
Resource effectiveness
Student completion rates
Knowledge gaps across learners
Future Vision

The Knowledge Management System should evolve into a continuously growing AI Education Repository capable of supporting learners from beginner level through professional certification, advanced industry practice, and PhD-level research, while enabling subject matter experts to contribute, curate, and improve content over time.
