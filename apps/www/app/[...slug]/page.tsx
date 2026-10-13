import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ContentPage } from "@/components/content-page";
import { pages } from "@/lib/pages";

type Params = { slug: string[] };

export const dynamicParams = false;

export function generateStaticParams() {
  return Object.keys(pages).map((path) => ({ slug: path.split("/") }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const spec = pages[(await params).slug.join("/")];
  if (!spec) return {};
  return {
    title: spec.title,
    description: spec.description,
    alternates: { canonical: spec.path },
  };
}

export default async function CatchAllPage({ params }: { params: Promise<Params> }) {
  const spec = pages[(await params).slug.join("/")];
  if (!spec) notFound();
  return <ContentPage spec={spec} />;
}
