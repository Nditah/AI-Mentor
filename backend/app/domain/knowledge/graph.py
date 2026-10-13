"""Typed knowledge graph: eligibility, sequencing, gap repair, and quality checks.

Edges read left to right: `source relation_type target`. `prerequisite_of` means the
source must be mastered before the target (ADR 0020). The planner walks those edges
backwards when a learner fails a check.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.knowledge.vocabulary import (
    ACYCLIC_RELATIONS,
    BLOCKING_WEIGHT,
    DIFFICULTY_RANK,
    RELATION_TYPES,
    SYMMETRIC_RELATIONS,
    difficulty_rank,
)
from app.domain.publishing import DIFFICULTIES

PREREQ_MET_AT = 70
HARD_PREREQ_FOR_ADVANCED = 85
RECOMMEND_BELOW = 75
ADVANCED_INDEX = DIFFICULTY_RANK["advanced"]
MAX_REPAIR_HOPS = 3


@dataclass(frozen=True)
class ConceptNode:
    slug: str
    name: str
    category: str
    difficulty: str
    summary: str = ""
    aliases: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptEdge:
    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    rationale: str = ""
    origin: str = "authored"
    status: str = "active"


@dataclass(frozen=True)
class GraphIssue:
    code: str
    severity: str
    message: str
    slugs: tuple[str, ...]


@dataclass(frozen=True)
class Eligibility:
    slug: str
    eligible: bool
    missing: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass
class KnowledgeGraph:
    """Adjacency lists over an in-memory snapshot. The database remains the record."""

    nodes: dict[str, ConceptNode] = field(default_factory=dict)
    edges: list[ConceptEdge] = field(default_factory=list)

    def add_node(self, node: ConceptNode) -> None:
        self.nodes[node.slug] = node

    def add_edge(self, edge: ConceptEdge) -> None:
        issue = edge_issue(self, edge)
        if issue:
            raise ValueError(issue)
        self.edges.append(edge)
        if edge.relation_type in SYMMETRIC_RELATIONS:
            reverse = ConceptEdge(
                source=edge.target,
                target=edge.source,
                relation_type=edge.relation_type,
                weight=edge.weight,
                rationale=edge.rationale,
                origin=edge.origin,
                status=edge.status,
            )
            if not _has_edge(self, reverse.source, reverse.target, reverse.relation_type):
                self.edges.append(reverse)

    def neighbours(self, slug: str, relation_type: str | None = None) -> list[ConceptEdge]:
        return [
            edge
            for edge in self.edges
            if edge.source == slug
            and edge.status == "active"
            and (relation_type is None or edge.relation_type == relation_type)
        ]

    def incoming(self, slug: str, relation_type: str | None = None) -> list[ConceptEdge]:
        return [
            edge
            for edge in self.edges
            if edge.target == slug
            and edge.status == "active"
            and (relation_type is None or edge.relation_type == relation_type)
        ]

    def blocking_prerequisites(self, slug: str) -> list[ConceptEdge]:
        return [
            edge
            for edge in self.incoming(slug, "prerequisite_of")
            if edge.weight >= BLOCKING_WEIGHT
        ]

    def mermaid(self, category: str | None = None) -> str:
        nodes = [
            node for node in self.nodes.values() if category is None or node.category == category
        ]
        slugs = {node.slug for node in nodes}
        lines = ["flowchart TD"]
        for node in nodes:
            ident = node.slug.replace("-", "_")
            lines.append(f'  {ident}["{node.name}"]')
        for edge in self.edges:
            if edge.relation_type != "prerequisite_of" or edge.status != "active":
                continue
            if edge.source not in slugs or edge.target not in slugs:
                continue
            src = edge.source.replace("-", "_")
            dst = edge.target.replace("-", "_")
            lines.append(f"  {src} --> {dst}")
        return "\n".join(lines)


def _has_edge(graph: KnowledgeGraph, source: str, target: str, relation_type: str) -> bool:
    return any(
        edge.source == source and edge.target == target and edge.relation_type == relation_type
        for edge in graph.edges
    )


def edge_issue(graph: KnowledgeGraph, edge: ConceptEdge) -> str | None:
    if edge.relation_type not in RELATION_TYPES:
        return f"Unknown relation {edge.relation_type}."
    if edge.source == edge.target:
        return "A concept cannot relate to itself."
    if edge.source not in graph.nodes or edge.target not in graph.nodes:
        return "Both ends of an edge must be known concepts."
    if not 0 <= edge.weight <= 1:
        return "Weight must be between 0 and 1."
    if _has_edge(graph, edge.source, edge.target, edge.relation_type):
        return "That edge already exists."
    if edge.relation_type in ACYCLIC_RELATIONS and _reaches(
        graph, edge.target, edge.source, edge.relation_type
    ):
        return f"{edge.relation_type} would create a cycle."
    return None


def _reaches(graph: KnowledgeGraph, start: str, goal: str, relation_type: str) -> bool:
    seen: set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node == goal:
            return True
        if node in seen:
            continue
        seen.add(node)
        for edge in graph.neighbours(node, relation_type):
            stack.append(edge.target)
    return False


def topological(graph: KnowledgeGraph, slugs: set[str] | None = None) -> list[str]:
    """Stable Kahn sort on blocking `prerequisite_of` edges. Raises on a cycle."""

    wanted = slugs if slugs is not None else set(graph.nodes)
    indegree = {slug: 0 for slug in wanted}
    dependents: dict[str, list[str]] = {slug: [] for slug in wanted}
    for edge in graph.edges:
        if edge.relation_type != "prerequisite_of" or edge.status != "active":
            continue
        if edge.weight < BLOCKING_WEIGHT:
            continue
        if edge.source not in wanted or edge.target not in wanted:
            continue
        indegree[edge.target] += 1
        dependents[edge.source].append(edge.target)
    ready = sorted(slug for slug, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in sorted(dependents[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(order) != len(wanted):
        raise ValueError("prerequisite cycle")
    return order


def eligibility(graph: KnowledgeGraph, slug: str, mastery: dict[str, int]) -> Eligibility:
    node = graph.nodes.get(slug)
    if node is None:
        raise KeyError(slug)
    missing: list[str] = []
    warnings: list[str] = []
    advanced = difficulty_rank(node.difficulty) >= ADVANCED_INDEX
    threshold = HARD_PREREQ_FOR_ADVANCED if advanced else PREREQ_MET_AT
    for edge in graph.incoming(slug, "prerequisite_of"):
        score = mastery.get(edge.source, 0)
        if edge.weight >= 0.8 and score < threshold:
            missing.append(edge.source)
        elif BLOCKING_WEIGHT <= edge.weight < 0.8 and score < PREREQ_MET_AT:
            warnings.append(edge.source)
    mastered_enough = mastery.get(slug, 0) < RECOMMEND_BELOW
    return Eligibility(slug, mastered_enough and not missing, tuple(missing), tuple(warnings))


def recommend_concepts(
    graph: KnowledgeGraph, mastery: dict[str, int], limit: int = 4
) -> list[Eligibility]:
    results: list[Eligibility] = []
    for slug in topological(graph):
        status = eligibility(graph, slug, mastery)
        if status.eligible:
            results.append(status)
        if len(results) >= limit:
            break
    return results


def gap_repair(graph: KnowledgeGraph, slug: str, mastery: dict[str, int]) -> list[str]:
    """Deepest weak blocking ancestor first, capped at three hops."""

    status = eligibility(graph, slug, mastery)
    if status.eligible:
        return []
    needed: list[str] = []
    stack = [(item, 1) for item in status.missing]
    seen: set[str] = set()
    while stack:
        current, depth = stack.pop()
        if current in seen or depth > MAX_REPAIR_HOPS:
            continue
        seen.add(current)
        child = eligibility(graph, current, mastery)
        if child.missing:
            stack.extend((item, depth + 1) for item in child.missing)
        if mastery.get(current, 0) < PREREQ_MET_AT:
            needed.append(current)
    order = topological(graph, set(needed) | {slug})
    return [item for item in order if item in needed]


def sequence_valid(graph: KnowledgeGraph, slugs: list[str]) -> str | None:
    """None when a path teaches concepts in an order the graph allows."""

    taught: set[str] = set()
    known = set(slugs)
    for slug in slugs:
        if slug not in graph.nodes:
            return f"Unknown concept {slug}."
        for parent in _blocking_ancestors(graph, slug):
            if parent in known and parent not in taught:
                return f"{parent} is a prerequisite of {slug} and is taught later."
        taught.add(slug)
    return None


def _blocking_ancestors(graph: KnowledgeGraph, slug: str) -> set[str]:
    found: set[str] = set()
    stack = [edge.source for edge in graph.blocking_prerequisites(slug)]
    while stack:
        current = stack.pop()
        if current in found:
            continue
        found.add(current)
        stack.extend(edge.source for edge in graph.blocking_prerequisites(current))
    return found


def quality_issues(graph: KnowledgeGraph) -> list[GraphIssue]:
    issues: list[GraphIssue] = []
    try:
        topological(graph)
    except ValueError:
        issues.append(GraphIssue("cycle", "blocking", "A blocking prerequisite cycle exists.", ()))
    for slug, node in graph.nodes.items():
        if not graph.neighbours(slug) and not graph.incoming(slug):
            issues.append(
                GraphIssue("orphan", "warning", f"{node.name} has no relations.", (slug,))
            )
        for edge in graph.blocking_prerequisites(slug):
            parent = graph.nodes.get(edge.source)
            if parent is None:
                continue
            if difficulty_rank(parent.difficulty) > difficulty_rank(node.difficulty) + 1:
                issues.append(
                    GraphIssue(
                        "difficulty_inversion",
                        "warning",
                        f"{parent.slug} is harder than {slug} but gates it.",
                        (parent.slug, slug),
                    )
                )
    return issues


def from_tuples(
    nodes: list[ConceptNode],
    edges: list[tuple[str, str, str, float] | tuple[str, str, str]],
) -> KnowledgeGraph:
    graph = KnowledgeGraph()
    for node in nodes:
        graph.add_node(node)
    for item in edges:
        relation = item[2]
        weight = item[3] if len(item) == 4 else 1.0
        graph.add_edge(
            ConceptEdge(source=item[0], target=item[1], relation_type=relation, weight=weight)
        )
    return graph


def difficulty_progression_ok(parent: str, child: str) -> bool:
    if parent not in DIFFICULTIES or child not in DIFFICULTIES:
        return True
    return difficulty_rank(parent) <= difficulty_rank(child) + 1
