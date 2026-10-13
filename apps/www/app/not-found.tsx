import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-site px-5 py-24">
      <h1 className="font-display text-4xl tracking-tight">Page not found</h1>
      <p className="mt-3 text-slate-700 dark:text-slate-300">That URL is not on the public site.</p>
      <Button className="mt-8" href="/">
        Back to home
      </Button>
    </section>
  );
}
