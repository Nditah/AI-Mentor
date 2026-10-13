from app.domain.knowledge.asset import (
    AssetRecord,
    canonical_url,
    dedupe_key,
    from_mapping,
    slugify,
    validate_record,
)
from app.domain.knowledge.connectors import (
    normalise_bulk,
    parse_csv_resources,
    validate_connector_payload,
)
from app.domain.knowledge.duplicates import find_duplicates, jaccard, pair_score
from app.domain.knowledge.graph import (
    ConceptEdge,
    ConceptNode,
    from_tuples,
    gap_repair,
    quality_issues,
    recommend_concepts,
    sequence_valid,
    topological,
)
from app.domain.knowledge.ingestion import PipelineContext, run_pipeline
from app.domain.knowledge.pack import compile_graph, compile_pack, pack_meets_launch
from app.domain.knowledge.pack_academies import ACADEMIES, academy_gaps
from app.domain.knowledge.quality import score_record
from app.domain.knowledge.recommend import LearnerState, recommend_resources
from app.domain.knowledge.search import SearchQuery, reciprocal_rank_fusion, search
from app.domain.knowledge.taxonomy import TAXONOMY, validate_taxonomy


def _node(slug: str, difficulty: str = "beginner", category: str = "reinforcement-learning"):
    return ConceptNode(
        slug=slug, name=slug.replace("-", " ").title(), category=category, difficulty=difficulty
    )


def test_taxonomy_is_a_tree() -> None:
    validate_taxonomy()
    assert any(node.level == "category" for node in TAXONOMY)
    assert any(node.slug == "bellman-equation" for node in TAXONOMY)


def test_canonical_url_strips_tracking() -> None:
    url = canonical_url("HTTPS://Example.com/Path/?utm_source=x&id=1")
    assert url == "https://example.com/Path?id=1"


def test_validate_record_and_dedupe() -> None:
    record = from_mapping(
        {
            "title": "Spinning Up in Deep RL",
            "description": "OpenAI's educational resource on policy gradients and PPO.",
            "category": "reinforcement-learning",
            "subcategory": "rl-control",
            "topic": "policy-gradients",
            "resource_type": "documentation",
            "url": "https://spinningup.openai.com/en/latest/",
            "provider": "OpenAI",
            "difficulty": "intermediate",
            "licence": "cc-by",
            "estimated_duration": 180,
        }
    )
    assert validate_record(record) is None
    assert dedupe_key(record).startswith("url:")
    assert slugify(record.title, "documentation").startswith("documentation-")
    score, detail = score_record(record)
    assert 0 <= score <= 100
    assert sum(detail.values()) == score or abs(sum(detail.values()) - score) <= 1


def test_unknown_category_is_rejected() -> None:
    record = AssetRecord(
        title="Mystery notes",
        description="A description long enough to pass the minimum length check.",
        category="not-a-category",
        resource_type="blog",
        estimated_duration=15,
    )
    assert validate_record(record) is not None


def test_graph_rejects_cycles_and_sequences_mdp_before_ppo() -> None:
    graph = from_tuples(
        [
            _node("mdp"),
            _node("bellman"),
            _node("q-learning"),
            _node("dqn"),
            _node("ppo", "advanced"),
        ],
        [
            ("mdp", "bellman", "prerequisite_of", 1.0),
            ("bellman", "q-learning", "prerequisite_of", 1.0),
            ("q-learning", "dqn", "prerequisite_of", 1.0),
            ("dqn", "ppo", "prerequisite_of", 1.0),
        ],
    )
    order = topological(graph)
    assert order.index("mdp") < order.index("bellman") < order.index("q-learning")
    assert sequence_valid(graph, ["mdp", "bellman", "q-learning", "dqn", "ppo"]) is None
    assert sequence_valid(graph, ["ppo", "mdp"]) is not None
    try:
        graph.add_edge(ConceptEdge("ppo", "mdp", "prerequisite_of"))
        raise AssertionError("cycle should have been rejected")
    except ValueError as exc:
        assert "cycle" in str(exc)


def test_new_learner_is_not_sent_to_dqn() -> None:
    graph = from_tuples(
        [_node("mdp"), _node("q-learning"), _node("dqn", "advanced")],
        [
            ("mdp", "q-learning", "prerequisite_of", 1.0),
            ("q-learning", "dqn", "prerequisite_of", 1.0),
        ],
    )
    slugs = [item.slug for item in recommend_concepts(graph, {}, limit=4)]
    assert slugs[0] == "mdp"
    assert "dqn" not in slugs
    assert gap_repair(graph, "dqn", {"q-learning": 40})[0] == "mdp"


def test_pack_graph_is_acyclic() -> None:
    graph = compile_graph()
    order = topological(graph)
    assert "mdp" in order and "ppo" in order
    assert order.index("mdp") < order.index("bellman")
    assert order.index("q-learning") < order.index("dqn")
    assert not any(issue.severity == "blocking" for issue in quality_issues(graph))


def test_search_and_recommendations_respect_style_and_cost() -> None:
    video = from_mapping(
        {
            "id": "vid",
            "title": "PPO lecture",
            "description": "A visual walk through proximal policy optimisation.",
            "category": "reinforcement-learning",
            "topic": "policy-gradients",
            "resource_type": "video",
            "concepts": ["ppo"],
            "skills": ["policy-optimisation"],
            "estimated_duration": 45,
            "quality_score": 80,
        }
    )
    paid = from_mapping(
        {
            "id": "book",
            "title": "PPO monograph",
            "description": "A long paid book about proximal policy optimisation.",
            "category": "reinforcement-learning",
            "topic": "policy-gradients",
            "resource_type": "book",
            "concepts": ["ppo"],
            "cost_type": "paid",
            "estimated_duration": 900,
        }
    )
    hits = search([video, paid], SearchQuery(text="PPO", learning_style="visual", limit=5))
    assert hits[0].record.id == "vid"
    graph = from_tuples([_node("ppo", "advanced")], [])
    recs = recommend_resources(
        [video, paid],
        graph,
        LearnerState(goals=("ppo",), learning_style="visual", cost_preference="free_only"),
        limit=4,
    )
    assert recs and recs[0].record.id == "vid"
    fused = reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert fused[0][0] == "b"


def test_duplicates_and_ingestion_pipeline() -> None:
    left = from_mapping(
        {
            "id": "a",
            "title": "Attention Is All You Need",
            "description": "The transformer paper that replaced recurrence.",
            "category": "deep-learning",
            "topic": "transformers",
            "resource_type": "paper",
            "url": "https://arxiv.org/abs/1706.03762",
            "estimated_duration": 60,
        }
    )
    right = from_mapping(
        {
            "id": "b",
            "title": "Attention Is All You Need",
            "description": "The transformer paper that replaced recurrence.",
            "category": "deep-learning",
            "topic": "transformers",
            "resource_type": "paper",
            "url": "https://arxiv.org/abs/1706.03762?utm_source=x",
            "estimated_duration": 60,
        }
    )
    assert jaccard(left.title, right.title) == 1.0
    hit = pair_score(left, right)
    assert hit is not None and hit.method in {"url", "title"}
    assert find_duplicates([left, right])
    items = run_pipeline(
        [
            {
                "title": "PyTorch tutorials",
                "description": "Official tutorials for tensors, autograd, and training loops.",
                "category": "deep-learning",
                "subcategory": "dl-foundations",
                "topic": "neural-networks",
                "resource_type": "tutorial",
                "url": "https://pytorch.org/tutorials/",
                "estimated_duration": 60,
            }
        ],
        PipelineContext(source_slug="pytorch-docs", publish_policy="review"),
    )
    assert items[0].outcome == "created"
    assert items[0].record is not None
    assert validate_connector_payload({"title": "x"}) is not None
    assert len(normalise_bulk({"resources": [{"title": "a"}]})) == 1
    rows = parse_csv_resources(
        "title,url,resource_type,concepts,estimated_duration\n"
        "Spinning Up,https://spinningup.openai.com/en/latest/,documentation,ppo|mdp,180\n"
    )
    assert rows[0]["title"] == "Spinning Up"
    assert rows[0]["concepts"] == ["ppo", "mdp"]
    assert rows[0]["estimated_duration"] == 180
    assert len(normalise_bulk({"csv": "title,url\nNotes,https://example.com/notes\n"})) == 1


def test_knowledge_pack_meets_launch_floor() -> None:
    pack = compile_pack()
    assert pack_meets_launch(pack) == []
    counts = pack.counts()
    assert counts["resources"] >= 2000
    assert counts["paper"] >= 500
    assert counts["book"] >= 300
    assert counts["video"] >= 500
    assert counts["course"] >= 150
    assert counts["certification"] >= 100
    assert counts["dataset"] >= 200
    assert counts["repository"] >= 300
    assert counts["questions"] >= 2000
    assert counts["challenges"] >= 500
    assert len(pack.paths) >= 50


def test_mandatory_academies_are_complete() -> None:
    pack = compile_pack()
    assert academy_gaps(pack) == []
    titles = {path.title for path in pack.paths}
    for academy in ACADEMIES:
        assert academy.title in titles
        path = next(item for item in pack.paths if item.title == academy.title)
        for _label, slug in academy.modules:
            assert slug in path.concepts
