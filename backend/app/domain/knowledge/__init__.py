"""Resource Catalog rules: vocabulary, classification, quality, deduplication, the
knowledge graph engine, search ranking, recommendation scoring, and the ingestion stages.

Nothing here touches the database, HTTP, or a model provider.
"""

from app.domain.knowledge.asset import (
    AssetRecord,
    canonical_url,
    dedupe_key,
    from_mapping,
    search_text,
    slugify,
    validate_record,
)
from app.domain.knowledge.connectors import CONNECTORS, normalise_bulk, validate_connector_payload
from app.domain.knowledge.duplicates import DuplicateHit, find_duplicates, pair_score
from app.domain.knowledge.graph import (
    ConceptEdge,
    ConceptNode,
    Eligibility,
    GraphIssue,
    KnowledgeGraph,
    eligibility,
    gap_repair,
    quality_issues,
    recommend_concepts,
    sequence_valid,
    topological,
)
from app.domain.knowledge.ingestion import STAGES, PipelineContext, PipelineItem, run_pipeline
from app.domain.knowledge.pack import (
    PACK_VERSION,
    KnowledgePack,
    compile_graph,
    compile_pack,
    pack_meets_launch,
)
from app.domain.knowledge.quality import score_record
from app.domain.knowledge.recommend import LearnerState, recommend_resources
from app.domain.knowledge.search import SearchQuery, search
from app.domain.knowledge.taxonomy import (
    CAREER_ROLES,
    SKILLS,
    SOURCES,
    TAXONOMY,
    category_of,
    validate_taxonomy,
)
from app.domain.knowledge.vocabulary import RESOURCE_TYPE_LABELS, RESOURCE_TYPES

__all__ = [
    "PACK_VERSION",
    "RESOURCE_TYPES",
    "RESOURCE_TYPE_LABELS",
    "CAREER_ROLES",
    "SKILLS",
    "SOURCES",
    "STAGES",
    "TAXONOMY",
    "CONNECTORS",
    "AssetRecord",
    "ConceptEdge",
    "ConceptNode",
    "DuplicateHit",
    "Eligibility",
    "GraphIssue",
    "KnowledgeGraph",
    "KnowledgePack",
    "LearnerState",
    "PipelineContext",
    "PipelineItem",
    "SearchQuery",
    "canonical_url",
    "category_of",
    "compile_graph",
    "compile_pack",
    "dedupe_key",
    "eligibility",
    "find_duplicates",
    "from_mapping",
    "gap_repair",
    "normalise_bulk",
    "pack_meets_launch",
    "pair_score",
    "quality_issues",
    "recommend_concepts",
    "recommend_resources",
    "run_pipeline",
    "score_record",
    "search",
    "search_text",
    "sequence_valid",
    "slugify",
    "topological",
    "validate_connector_payload",
    "validate_record",
    "validate_taxonomy",
]
