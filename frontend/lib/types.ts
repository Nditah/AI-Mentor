export type Recommendation = { slug: string; name: string; reason: string };
export type ConceptScore = { slug: string; name: string; score: number };
export type PathProgress = {
  slug: string;
  title: string;
  description: string;
  level: string;
  completed: number;
  total: number;
};
export type Badge = { slug: string; name: string; description: string; earned: boolean };
export type Dashboard = {
  display_name: string;
  role: string;
  xp: number;
  level: number;
  xp_into_level: number;
  xp_per_level: number;
  streak_days: number;
  subscription_status: string;
  mastery: number;
  strengths: ConceptScore[];
  developing: ConceptScore[];
  weaknesses: ConceptScore[];
  recommendations: Recommendation[];
  paths: PathProgress[];
  badges: Badge[];
  lessons_completed: number;
  quizzes_taken: number;
};
export type ChatReply = {
  conversation_id: string;
  mode: string;
  stage: number;
  concept_slug: string | null;
  reply: { id: string; role: string; content: string };
};
export type PathDetail = {
  slug: string;
  title: string;
  description: string;
  level: string;
  steps: {
    position: number;
    slug: string | null;
    title: string;
    estimated_minutes: number | null;
    completed: boolean;
    prerequisites: string[];
    content_md: string | null;
  }[];
};
