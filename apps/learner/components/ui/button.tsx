import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const styles = cva(
  "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-base font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1d4ed8] disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-[#1d4ed8] text-white hover:bg-[#1e40af]",
        secondary: "bg-[#6d28d9] text-white hover:bg-[#5b21b6]",
        quiet:
          "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800",
        ghost:
          "bg-transparent px-3 text-slate-800 hover:bg-slate-100 dark:text-slate-100 dark:hover:bg-slate-800",
      },
    },
    defaultVariants: { variant: "primary" },
  },
);

type Props = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof styles> & { href?: string; children?: ReactNode };

export function Button({ className, variant, href, children, ...props }: Props) {
  const classes = cn(styles({ variant }), className);
  if (href) {
    return (
      <a className={classes} href={href}>
        {children}
      </a>
    );
  }
  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
