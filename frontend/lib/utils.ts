import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const devAuth = process.env.NEXT_PUBLIC_DEV_AUTH === "true";
export const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
