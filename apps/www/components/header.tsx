"use client";

import { Menu, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { pages, platformMega, resourceLinks, solutionsMega } from "@/lib/pages";
import { ctas, loginUrl } from "@/lib/urls";

function primaryCta(pathname: string) {
  const spec = pages[pathname.replace(/^\//, "")];
  if (spec?.cta === "enterprise") return ctas.enterprise;
  if (spec?.cta === "instructor") return ctas.instructor;
  if (spec?.cta === "studio") return ctas.studio;
  return ctas.learner;
}

function Mega({
  label,
  items,
}: {
  label: string;
  items: { href: string; title: string; line: string }[];
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
  return (
    <div className="relative">
      <button
        type="button"
        className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((value) => !value)}
        onBlur={(event) => {
          if (!event.currentTarget.parentElement?.contains(event.relatedTarget as Node)) {
            setOpen(false);
          }
        }}
      >
        {label}
      </button>
      {open ? (
        <ul
          id={id}
          className="absolute left-0 z-30 mt-2 w-80 rounded-3xl border border-slate-200 bg-white p-3 shadow-card dark:border-slate-700 dark:bg-slate-900"
        >
          {items.map((item) => (
            <li key={item.href}>
              <a
                className="block rounded-2xl px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-800"
                href={item.href}
                onClick={() => setOpen(false)}
              >
                <span className="font-semibold">{item.title}</span>
                <span className="mt-0.5 block text-sm text-slate-600 dark:text-slate-400">{item.line}</span>
              </a>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function Header() {
  const pathname = usePathname() || "/";
  const cta = primaryCta(pathname);
  const [compact, setCompact] = useState(false);
  const [menu, setMenu] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setCompact(window.scrollY > 80);
    onScroll();
    setScrolled(true);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  const compactNav = scrolled && compact;
  useEffect(() => {
    if (!menu) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenu(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menu]);
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-[var(--paper)]/95 backdrop-blur dark:border-slate-800">
      <div className="mx-auto flex max-w-site items-center justify-between gap-3 px-5 py-4">
        <a href="/" className="font-display text-2xl tracking-tight">
          AI Mentor
        </a>
        <nav className="hidden items-center gap-1 text-sm lg:flex" aria-label="Primary">
          {compactNav ? (
            <>
              <a className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800" href="/pricing">
                Pricing
              </a>
              <Button href={loginUrl} variant="ghost">
                Login
              </Button>
              <Button href={cta.href}>{cta.label}</Button>
            </>
          ) : (
            <>
              <Mega label="Platform" items={platformMega} />
              <Mega label="Solutions" items={solutionsMega} />
              <a className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800" href="/paths">
                Paths
              </a>
              <a className="rounded-full px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800" href="/pricing">
                Pricing
              </a>
              <Mega
                label="Resources"
                items={resourceLinks.map((item) => ({ ...item, line: item.title }))}
              />
              <Button href={loginUrl} variant="ghost">
                Login
              </Button>
              <Button href={cta.href}>{cta.label}</Button>
            </>
          )}
          <span className="ml-1 inline-flex items-center gap-1" aria-label="Language. English is available now.">
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold dark:bg-slate-800">en</span>
            <span className="px-1 text-xs text-slate-500" aria-disabled="true">
              fr
            </span>
            <span className="px-1 text-xs text-slate-500" aria-disabled="true">
              es
            </span>
          </span>
          <ThemeToggle />
        </nav>
        <div className="flex items-center gap-2 lg:hidden">
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-300 dark:border-slate-600"
            aria-expanded={menu}
            aria-controls="mobile-nav"
            aria-label={menu ? "Close menu" : "Open menu"}
            onClick={() => setMenu((value) => !value)}
          >
            {menu ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>
      {menu ? (
        <nav
          id="mobile-nav"
          className="space-y-2 border-t border-slate-200 px-5 py-4 lg:hidden dark:border-slate-800"
          aria-label="Mobile"
        >
          <Button href={cta.href} className="w-full">
            {cta.label}
          </Button>
          <details className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
            <summary className="cursor-pointer font-semibold">Platform</summary>
            <ul className="mt-2 space-y-1">
              {platformMega.map((item) => (
                <li key={item.href}>
                  <a className="block py-2" href={item.href} onClick={() => setMenu(false)}>
                    {item.title}
                  </a>
                </li>
              ))}
            </ul>
          </details>
          <details className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
            <summary className="cursor-pointer font-semibold">Solutions</summary>
            <ul className="mt-2 space-y-1">
              {solutionsMega.map((item) => (
                <li key={item.href}>
                  <a className="block py-2" href={item.href} onClick={() => setMenu(false)}>
                    {item.title}
                  </a>
                </li>
              ))}
            </ul>
          </details>
          <details className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
            <summary className="cursor-pointer font-semibold">Resources</summary>
            <ul className="mt-2 space-y-1">
              {resourceLinks.map((item) => (
                <li key={item.href}>
                  <a className="block py-2" href={item.href} onClick={() => setMenu(false)}>
                    {item.title}
                  </a>
                </li>
              ))}
            </ul>
          </details>
          <a className="block py-2" href="/paths">
            Paths
          </a>
          <a className="block py-2" href="/pricing">
            Pricing
          </a>
          <a className="block py-2" href="/company/about">
            About
          </a>
          <a className="block py-2" href="/company/contact">
            Contact
          </a>
          <Button href={loginUrl} variant="quiet" className="w-full">
            Login
          </Button>
        </nav>
      ) : null}
    </header>
  );
}
