import { LearnerShell } from "@/components/studio/shell";

export default function LearnLayout({ children }: { children: React.ReactNode }) {
  return <LearnerShell>{children}</LearnerShell>;
}
