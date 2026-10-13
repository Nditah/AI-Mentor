"""Write Knowledge Pack v1.0 into the repository `seed-data/` tree."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.domain.knowledge.asset import AssetRecord
from app.domain.knowledge.pack import PACK_VERSION, compile_pack, pack_meets_launch
from app.domain.knowledge.pack_concepts import CONCEPT_ROWS
from app.domain.knowledge.taxonomy import CAREER_ROLES, SKILLS, SOURCES, TAXONOMY

CATEGORY_FILES = {
    "artificial-intelligence": "ai-resources.json",
    "machine-learning": "ml-resources.json",
    "deep-learning": "deep-learning-resources.json",
    "reinforcement-learning": "rl-resources.json",
    "robotics": "robotics-resources.json",
    "computer-vision": "computer-vision-resources.json",
    "nlp": "nlp-resources.json",
    "data-science": "data-science-resources.json",
    "statistics": "statistics-resources.json",
    "mathematics": "mathematics-resources.json",
    "generative-ai": "genai-resources.json",
    "llm-engineering": "llm-engineering-resources.json",
}

TYPE_FILES = {
    "book": "books.json",
    "paper": "papers.json",
    "video": "videos.json",
    "course": "courses.json",
    "certification": "certifications.json",
    "dataset": "datasets.json",
    "repository": "github-repositories.json",
    "learning_path": "learning-paths.json",
    "coding_challenge": "coding-challenges.json",
}


def _asset_json(record: AssetRecord) -> dict:
    payload = {
        "id": record.id,
        "title": record.title,
        "description": record.description,
        "category": record.category,
        "subcategory": record.subcategory,
        "topic": record.topic,
        "resource_type": record.resource_type,
        "provider": record.provider,
        "author": record.author,
        "url": record.url,
        "language": record.language,
        "difficulty": record.difficulty,
        "estimated_duration": record.duration_minutes(),
        "cost_type": record.cost_type,
        "rating": record.rating,
        "tags": record.tags,
        "skills": record.skills,
        "prerequisites": record.prerequisites,
        "learning_outcomes": record.learning_outcomes,
        "publication_date": record.publication_date,
        "thumbnail": record.thumbnail,
        "source_type": record.source_type,
        "quality_score": record.quality_score,
        "ai_generated_summary": record.ai_generated_summary,
        "metadata": record.metadata,
        "licence": record.licence,
        "concepts": record.concepts,
    }
    return payload


def _dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_seed_files(root: Path) -> list[Path]:
    pack = compile_pack()
    shortfalls = pack_meets_launch(pack)
    written: list[Path] = []
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "KnowledgeAsset",
        "type": "object",
        "required": ["title", "description", "category", "resource_type"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string", "minLength": 3, "maxLength": 200},
            "description": {"type": "string", "minLength": 20},
            "category": {"type": "string"},
            "subcategory": {"type": "string"},
            "topic": {"type": "string"},
            "resource_type": {
                "type": "string",
                "enum": [
                    "book",
                    "course",
                    "paper",
                    "video",
                    "repository",
                    "dataset",
                    "tutorial",
                    "blog",
                    "certification",
                    "documentation",
                    "podcast",
                    "learning_path",
                    "coding_challenge",
                ],
            },
            "provider": {"type": "string"},
            "author": {"type": "string"},
            "url": {"type": "string"},
            "language": {"type": "string"},
            "difficulty": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced", "expert", "phd"],
            },
            "estimated_duration": {"type": "integer"},
            "cost_type": {
                "type": "string",
                "enum": ["free", "freemium", "free_audit", "paid", "subscription"],
            },
            "tags": {"type": "array", "items": {"type": "string"}},
            "skills": {"type": "array", "items": {"type": "string"}},
            "prerequisites": {"type": "array", "items": {"type": "string"}},
            "learning_outcomes": {"type": "array", "items": {"type": "string"}},
            "concepts": {"type": "array", "items": {"type": "string"}},
        },
    }
    path = root / "schema" / "knowledge-asset.schema.json"
    _dump(path, schema)
    written.append(path)

    assets = [_asset_json(record) for record in pack.resources]
    for category, filename in CATEGORY_FILES.items():
        items = [item for item in assets if item["category"] == category]
        path = root / filename
        _dump(path, items)
        written.append(path)
    leftover = [
        item
        for item in assets
        if item["category"] not in CATEGORY_FILES and item["resource_type"] not in TYPE_FILES
    ]
    if leftover:
        path = root / "other-resources.json"
        _dump(path, leftover)
        written.append(path)
    for resource_type, filename in TYPE_FILES.items():
        if resource_type == "coding_challenge":
            continue
        items = [item for item in assets if item["resource_type"] == resource_type]
        path = root / filename
        _dump(path, items)
        written.append(path)

    questions = [
        {
            "key": item.key,
            "concept_slug": item.concept_slug,
            "difficulty": item.difficulty,
            "kind": item.kind,
            "prompt": item.prompt,
            "options": item.options,
            "answer_key": item.answer_key,
            "explanation": item.explanation,
            "tags": item.tags,
            "skills": item.skills,
            "bloom_level": item.bloom_level,
            "origin": item.origin,
        }
        for item in pack.questions
    ]
    path = root / "quiz-questions.json"
    _dump(path, questions)
    written.append(path)

    challenges = [asdict(item) for item in pack.challenges]
    path = root / "coding-challenges.json"
    _dump(path, challenges)
    written.append(path)

    concepts = [
        {
            "slug": slug,
            "name": name,
            "category": category,
            "topic": topic,
            "difficulty": difficulty,
            "prerequisites": list(prereqs),
            "skills": list(skills),
            "summary": summary,
        }
        for slug, name, category, topic, difficulty, prereqs, skills, summary in CONCEPT_ROWS
    ]
    path = root / "knowledge-pack" / "v1" / "concepts.json"
    _dump(path, concepts)
    written.append(path)

    graph = [
        {
            "source": edge.source,
            "target": edge.target,
            "relation_type": edge.relation_type,
            "weight": edge.weight,
        }
        for edge in pack.edges
    ]
    path = root / "knowledge-pack" / "v1" / "graph.json"
    _dump(path, graph)
    written.append(path)

    manifest = {
        "name": "AI Mentor Knowledge Pack",
        "version": PACK_VERSION,
        "counts": pack.counts(),
        "launch_shortfalls": shortfalls,
        "files": [str(item.relative_to(root)) for item in written],
        "taxonomy": [node.slug for node in TAXONOMY],
        "skills": [skill.slug for skill in SKILLS],
        "sources": [source.slug for source in SOURCES],
        "career_roles": [role.slug for role in CAREER_ROLES],
    }
    path = root / "knowledge-pack" / "v1" / "manifest.json"
    _dump(path, manifest)
    written.append(path)

    readme = root / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Seed data",
                "",
                "JSON catalogs for the Resource Catalog bounded context.",
                "Regenerate with `python -m app.cli write-pack` from `backend/`.",
                "",
                f"Knowledge Pack **v{PACK_VERSION}** counts:",
                "",
                *[f"- `{key}`: {value}" for key, value in pack.counts().items()],
                "",
                "Launch shortfalls (empty means the floor is met): "
                + (", ".join(shortfalls) if shortfalls else "none"),
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(readme)
    return written
