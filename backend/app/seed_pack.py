"""Seed Knowledge Pack v1.0 into Postgres. Idempotent. Does not reset learner progress."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.knowledge.asset import dedupe_key, parse_publication_date, search_text
from app.domain.knowledge.pack import PACK_VERSION, compile_pack
from app.domain.knowledge.pack_concepts import CONCEPT_ROWS
from app.domain.knowledge.quality import score_record
from app.domain.knowledge.taxonomy import CAREER_ROLES, SKILLS, SOURCES, TAXONOMY
from app.models import (
    CareerRole,
    ChallengeSpec,
    ConceptRelation,
    ConceptSkill,
    ContentSource,
    KnowledgeAsset,
    PathStep,
    QuestionBankItem,
    Skill,
    TaxonomyNode,
)
from app.models import Concept as ConceptRow

_KIND = {
    "book": "link",
    "course": "link",
    "paper": "paper",
    "video": "link",
    "repository": "code",
    "dataset": "dataset",
    "tutorial": "guide",
    "blog": "link",
    "certification": "link",
    "documentation": "link",
    "podcast": "link",
    "learning_path": "guide",
    "coding_challenge": "code",
}


def seed_reference(session: Session) -> None:
    """Taxonomy, skills, sources, and career roles. Safe on every catalog seed."""

    by_slug: dict[str, TaxonomyNode] = {}
    for entry in TAXONOMY:
        row = session.scalar(select(TaxonomyNode).where(TaxonomyNode.slug == entry.slug))
        if row is None:
            row = TaxonomyNode(slug=entry.slug)
            session.add(row)
        row.name = entry.name
        row.level = entry.level
        row.description = entry.description
        row.aliases = list(entry.aliases)
        row.status = "active"
        by_slug[entry.slug] = row
    session.flush()
    for entry in TAXONOMY:
        by_slug[entry.slug].parent_id = None if entry.parent is None else by_slug[entry.parent].id
    session.flush()

    skills: dict[str, Skill] = {}
    for item in SKILLS:
        row = session.scalar(select(Skill).where(Skill.slug == item.slug))
        if row is None:
            row = Skill(slug=item.slug)
            session.add(row)
        row.name = item.name
        row.family = item.family
        row.kind = item.kind
        row.description = item.description
        row.aliases = list(item.aliases)
        skills[item.slug] = row
    session.flush()

    for source in SOURCES:
        row = session.scalar(select(ContentSource).where(ContentSource.slug == source.slug))
        if row is None:
            row = ContentSource(slug=source.slug)
            session.add(row)
        row.name = source.name
        row.provider = source.provider
        row.connector = source.connector
        row.homepage = source.homepage
        row.description = source.description
        row.resource_types = list(source.resource_types)
        row.schedule = source.schedule
        row.trust_level = source.trust_level
        row.publish_policy = source.publish_policy
        row.terms_note = source.terms_note
        row.credential_env = source.credential_env
        row.status = "active"
        row.enabled = True
    session.flush()

    for role in CAREER_ROLES:
        row = session.scalar(select(CareerRole).where(CareerRole.slug == role.slug))
        if row is None:
            row = CareerRole(slug=role.slug)
            session.add(row)
        row.title = role.title
        row.summary = role.summary
        row.skills = list(role.skills)
        row.concepts = list(role.concepts)
    session.flush()


def seed_pack_concepts(session: Session) -> dict[str, ConceptRow]:
    concepts: dict[str, ConceptRow] = {}
    for slug, name, category, _topic, difficulty, _prereqs, skill_slugs, summary in CONCEPT_ROWS:
        row = session.scalar(select(ConceptRow).where(ConceptRow.slug == slug))
        if row is None:
            row = ConceptRow(slug=slug, domain=category.replace("-", " ").title())
            session.add(row)
        row.name = name
        row.domain = row.domain or category.replace("-", " ").title()
        row.difficulty = difficulty
        row.summary = summary
        row.category = category
        row.origin = row.origin if row.origin == "catalog" else "pack"
        row.status = "active"
        concepts[slug] = row
    session.flush()
    skill_rows = {row.slug: row for row in session.scalars(select(Skill)).all()}
    for slug, _name, _cat, _topic, _diff, _prereqs, skill_slugs, _summary in CONCEPT_ROWS:
        concept = concepts[slug]
        for skill_slug in skill_slugs:
            skill = skill_rows.get(skill_slug)
            if skill is None:
                continue
            exists = session.get(ConceptSkill, {"concept_id": concept.id, "skill_id": skill.id})
            if exists is None:
                session.add(ConceptSkill(concept_id=concept.id, skill_id=skill.id, weight=1.0))
    session.flush()
    return concepts


def seed_pack_edges(session: Session, concepts: dict[str, ConceptRow]) -> None:
    from app.domain.knowledge.pack_concepts import pack_prerequisites

    for source, target, relation, weight in pack_prerequisites():
        if source not in concepts or target not in concepts:
            continue
        exists = session.scalar(
            select(ConceptRelation).where(
                ConceptRelation.source_id == concepts[source].id,
                ConceptRelation.target_id == concepts[target].id,
                ConceptRelation.relation_type == relation,
            )
        )
        if exists is None:
            session.add(
                ConceptRelation(
                    source_id=concepts[source].id,
                    target_id=concepts[target].id,
                    relation_type=relation,
                    weight=weight,
                    origin="imported",
                    status="active",
                )
            )
        else:
            exists.weight = weight
            exists.status = "active"
    session.flush()


def seed_pack_resources(session: Session, pack) -> None:
    source = session.scalar(select(ContentSource).where(ContentSource.slug == "curated-pack"))
    taken = {row.slug: row for row in session.scalars(select(KnowledgeAsset)).all()}
    keys = {row.dedupe_key: row for row in taken.values() if row.dedupe_key}
    for record in pack.resources:
        key = dedupe_key(record)
        row = keys.get(key) or taken.get(record.id)
        if row is None:
            slug = record.id[:80]
            if slug in taken:
                slug = f"{slug[:70]}-{len(taken)}"
            row = KnowledgeAsset(slug=slug, owner_id=None)
            session.add(row)
            taken[slug] = row
        extra = dict(record.metadata or {})
        extra["skills"] = list(record.skills)
        extra["concepts"] = list(record.concepts)
        extra["prerequisites"] = list(record.prerequisites)
        extra["pack_version"] = PACK_VERSION
        score, detail = score_record(record)
        row.title = record.title[:200]
        row.description = record.description
        row.topic = record.topic
        row.difficulty = record.difficulty
        row.author_name = record.author[:200]
        row.source = record.source
        row.language = record.language
        row.kind = _KIND.get(record.resource_type, "link")
        row.state = "published"
        row.objectives = list(record.learning_outcomes)
        row.estimated_minutes = record.duration_minutes()
        row.tags = list(record.tags)
        row.licence = record.licence
        row.resource_type = record.resource_type
        row.category = record.category
        row.subcategory = record.subcategory
        row.provider = record.provider[:120]
        row.url = record.url or None
        row.cost_type = record.cost_type
        row.rating = record.rating
        row.publication_date = parse_publication_date(record.publication_date)
        row.thumbnail_url = record.thumbnail or None
        row.source_type = record.source_type
        row.source_id = None if source is None else source.id
        row.external_id = record.external_id or record.id
        row.dedupe_key = key
        row.quality_score = score
        row.quality_detail = detail
        row.ai_summary = record.ai_generated_summary
        row.extra = extra
        row.search_text = search_text(record)
        row.pack_version = PACK_VERSION
        keys[key] = row
    session.flush()


def seed_pack_questions(session: Session, pack) -> None:
    for item in pack.questions:
        row = session.scalar(select(QuestionBankItem).where(QuestionBankItem.key == item.key))
        if row is None:
            row = QuestionBankItem(key=item.key)
            session.add(row)
        row.concept_slug = item.concept_slug
        row.difficulty = item.difficulty
        row.kind = item.kind
        row.prompt = item.prompt
        row.options = list(item.options)
        row.answer_key = dict(item.answer_key)
        row.explanation = item.explanation
        row.origin = (
            item.origin
            if item.origin in {"computed", "authored", "ai_drafted", "catalog"}
            else "computed"
        )
        row.state = "published"
        row.tags = list(item.tags)
        row.skills = list(item.skills)
        row.bloom_level = item.bloom_level
        row.pack_version = PACK_VERSION
    session.flush()


def seed_pack_challenges(session: Session, pack) -> None:
    assets = {row.slug: row for row in session.scalars(select(KnowledgeAsset)).all()}
    for item in pack.challenges:
        asset = assets.get(item.id)
        if asset is None:
            continue
        spec = session.get(ChallengeSpec, asset.id)
        if spec is None:
            spec = ChallengeSpec(asset_id=asset.id)
            session.add(spec)
        spec.language = item.language
        spec.entrypoint = item.entrypoint
        spec.variant = item.variant
        spec.starter_code = item.starter_code
        spec.visible_tests = list(item.visible_tests)
        spec.hidden_tests = list(item.hidden_tests)
        spec.reference_solution = item.reference_solution
    session.flush()


def seed_pack_paths(session: Session, pack) -> None:
    assets = {row.slug: row for row in session.scalars(select(KnowledgeAsset)).all()}
    for path in pack.paths:
        asset = assets.get(path.id)
        if asset is None:
            continue
        existing = session.scalars(select(PathStep).where(PathStep.path_id == asset.id)).all()
        for row in existing:
            session.delete(row)
        session.flush()
        for step in path.steps:
            session.add(
                PathStep(
                    path_id=asset.id,
                    position=int(step["position"]),
                    kind=step["kind"],
                    title=step["title"],
                    concept_slug=step.get("concept_slug"),
                    notes="",
                    estimated_minutes=step.get("estimated_minutes"),
                )
            )
    session.flush()


def seed_knowledge_pack(session: Session) -> dict[str, int]:
    """Load the launch pack. Catalog seed should run first so v1 concepts keep origin=catalog."""

    seed_reference(session)
    concepts = seed_pack_concepts(session)
    seed_pack_edges(session, concepts)
    pack = compile_pack()
    seed_pack_resources(session, pack)
    seed_pack_questions(session, pack)
    seed_pack_challenges(session, pack)
    seed_pack_paths(session, pack)
    session.flush()
    return pack.counts()
