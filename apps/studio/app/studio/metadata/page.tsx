"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Facets = {
  resource_types: { id: string; label: string }[];
  taxonomy: { slug: string; name: string; level: string }[];
  skills: { slug: string; name: string; family: string }[];
  career_roles: { slug: string; title: string }[];
  sources: { slug: string; name: string; provider: string }[];
};

export default function MetadataPage() {
  const query = useQuery({
    queryKey: ["facets"],
    queryFn: () => api<Facets>("/api/v1/catalog/facets"),
  });
  const data = query.data;
  if (!data) return <p>Loading vocabularies…</p>;
  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-tight">Metadata manager</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Controlled vocabularies for the catalog. Adding a resource type still needs a migration; skills and taxonomy terms can grow here later.
      </p>
      <section className="mt-6">
        <h2 className="text-xl font-semibold">Resource types</h2>
        <p className="mt-2 text-sm">{data.resource_types.map((item) => item.label).join(" · ")}</p>
      </section>
      <section className="mt-6">
        <h2 className="text-xl font-semibold">Skills</h2>
        <ul className="mt-2 columns-2 text-sm">
          {data.skills.map((skill) => (
            <li key={skill.slug}>{skill.name} <span className="text-slate-500">({skill.family})</span></li>
          ))}
        </ul>
      </section>
      <section className="mt-6">
        <h2 className="text-xl font-semibold">Career roles</h2>
        <ul className="mt-2 text-sm">
          {data.career_roles.map((role) => (
            <li key={role.slug}>{role.title}</li>
          ))}
        </ul>
      </section>
      <section className="mt-6">
        <h2 className="text-xl font-semibold">Sources</h2>
        <ul className="mt-2 text-sm">
          {data.sources.map((source) => (
            <li key={source.slug}>{source.name} · {source.provider}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
