/** Origins for the public site and the five product apps. */

export const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const wwwUrl = process.env.NEXT_PUBLIC_WWW_URL || "http://localhost:3005";
export const learnerUrl = process.env.NEXT_PUBLIC_LEARNER_URL || "http://localhost:3000";
export const adminUrl = process.env.NEXT_PUBLIC_ADMIN_URL || "http://localhost:3001";
export const instructorUrl = process.env.NEXT_PUBLIC_INSTRUCTOR_URL || "http://localhost:3002";
export const institutionUrl = process.env.NEXT_PUBLIC_INSTITUTION_URL || "http://localhost:3003";
export const studioUrl = process.env.NEXT_PUBLIC_STUDIO_URL || "http://localhost:3004";

export const startUrl = "/register";
export const loginUrl = "/login";
export const registerUrl = "/register";
export const dashboardUrl = `${learnerUrl}/dashboard`;
export const tutorUrl = `${learnerUrl}/tutor`;
export const learnerPathsUrl = `${learnerUrl}/paths`;

export function learnerPath(slug: string): string {
  return `${learnerUrl}/paths/${slug}`;
}

export function isAuthPath(pathname: string): boolean {
  return pathname === "/login" || pathname === "/register";
}

export const ctas = {
  learner: { href: "/start", label: "Start learning free" },
  instructor: { href: "/demo/instructor", label: "Book instructor demo" },
  enterprise: { href: "/demo/enterprise", label: "Request enterprise demo" },
  studio: { href: "/company/contact", label: "Talk to content" },
} as const;

export type CtaKind = keyof typeof ctas;
