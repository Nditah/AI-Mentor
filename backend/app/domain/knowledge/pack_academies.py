"""Mandatory academies: named curricula and a coverage audit.

An academy is a product curriculum, not a sixth launcher app. It lists the
modules a learner must meet, in graph order, and names the concept slugs the
pack must actually contain. Category foundations/applied/research paths still
emit from `_paths`; these rows are the named academies the CPO asked for.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.knowledge.pack_concepts import CONCEPT_ROWS


@dataclass(frozen=True)
class Academy:
    slug: str
    title: str
    category: str
    summary: str
    modules: tuple[tuple[str, str], ...]  # (label, concept_slug)


ACADEMIES: tuple[Academy, ...] = (
    Academy(
        slug="computer-vision-academy",
        title="Computer Vision Academy",
        category="computer-vision",
        summary="Images to structure: classic vision, detectors, and 3D.",
        modules=(
            ("OpenCV", "opencv"),
            ("YOLO", "yolo"),
            ("DETR", "detr"),
            ("Segmentation", "segmentation"),
            ("Stereo Vision", "stereo-vision"),
            ("LiDAR", "lidar"),
            ("3D Vision", "3d-vision"),
        ),
    ),
    Academy(
        slug="natural-language-processing-academy",
        title="Natural Language Processing Academy",
        category="nlp",
        summary="Tokens to products: embeddings, transformers, RAG, and agents.",
        modules=(
            ("NLP Fundamentals", "nlp-fundamentals"),
            ("Embeddings", "embeddings"),
            ("Transformers", "transformers"),
            ("LLM Engineering", "llm-engineering"),
            ("RAG", "rag"),
            ("AI Agents", "agents"),
        ),
    ),
    Academy(
        slug="federated-learning-academy",
        title="Federated Learning Academy",
        category="federated-learning",
        summary="Train across clients without centralising the raw data.",
        modules=(
            ("FedAvg", "fedavg"),
            ("FedProx", "fedprox"),
            ("Differential Privacy", "differential-privacy"),
            ("Edge AI", "edge-ai"),
        ),
    ),
    Academy(
        slug="programming-academy",
        title="Programming Academy",
        category="programming",
        summary="The languages and craft the rest of the catalog assumes.",
        modules=(
            ("Python", "python-language"),
            ("C++", "cpp"),
            ("ROS2 C++", "ros2-cpp"),
            ("Software Engineering", "software-engineering"),
        ),
    ),
    Academy(
        slug="modelling-and-simulation-academy",
        title="Modelling and Simulation Academy",
        category="modelling-simulation",
        summary="Maths models and robot/vehicle simulators, including digital twins.",
        modules=(
            ("MATLAB", "matlab"),
            ("Simulink", "simulink"),
            ("Gazebo", "gazebo"),
            ("Isaac Sim", "isaac-sim"),
            ("MuJoCo", "mujoco"),
            ("CARLA", "carla"),
            ("AirSim", "airsim"),
            ("Webots", "webots"),
            ("CoppeliaSim", "coppeliasim"),
            ("Digital Twins", "digital-twins"),
        ),
    ),
)


def academy_required_slugs() -> set[str]:
    return {slug for academy in ACADEMIES for _label, slug in academy.modules}


def academy_path_concepts(academy: Academy) -> list[str]:
    """Spine first, then required modules, unique, in pedagogical order."""

    extra = {
        "computer-vision-academy": (
            "computer-vision",
            "image-formation",
            "opencv",
            "stereo-vision",
            "multiview",
            "detection",
            "vision-transformers",
        ),
        "natural-language-processing-academy": (
            "nlp-fundamentals",
            "tokenization",
            "language-models",
            "representation-nlp",
            "sequence-labeling",
            "generation",
        ),
        "federated-learning-academy": ("federated-learning",),
        "programming-academy": (
            "python-language",
            "python-for-ml",
            "scientific-python",
            "ros2",
        ),
        "modelling-and-simulation-academy": ("simulation", "control-theory"),
    }.get(academy.slug, ())
    ordered: list[str] = []
    for slug in (*extra, *(item[1] for item in academy.modules)):
        if slug not in ordered:
            ordered.append(slug)
    known = {row[0] for row in CONCEPT_ROWS}
    return [slug for slug in ordered if slug in known]


def academy_gaps(pack: object) -> list[str]:
    """Human-readable shortfalls. Empty means every mandatory academy is complete."""

    concept_slugs = {node.slug for node in getattr(pack, "concepts", [])}
    questions_by = {item.concept_slug for item in getattr(pack, "questions", [])}
    challenges = list(getattr(pack, "challenges", []))
    challenge_slugs = {item.concept_slug for item in challenges}
    project_slugs = {
        item.concept_slug for item in challenges if getattr(item, "variant", "") == "implement"
    }
    resources = list(getattr(pack, "resources", []))
    resource_concepts: set[str] = set()
    types_by_concept: dict[str, set[str]] = {}
    for record in resources:
        for slug in record.concepts:
            resource_concepts.add(slug)
            types_by_concept.setdefault(slug, set()).add(record.resource_type)
    path_titles = {path.title for path in getattr(pack, "paths", [])}
    path_concept_sets = [set(path.concepts) for path in getattr(pack, "paths", [])]

    gaps: list[str] = []
    known = {row[0] for row in CONCEPT_ROWS}
    for academy in ACADEMIES:
        if academy.title not in path_titles:
            gaps.append(f"missing academy path: {academy.title}")
        for label, slug in academy.modules:
            if slug not in known:
                gaps.append(f"{academy.title}: module {label} has no concept slug {slug}")
                continue
            if slug not in concept_slugs:
                gaps.append(
                    f"{academy.title}: concept {slug} ({label}) is not in the compiled pack"
                )
            if slug not in questions_by:
                gaps.append(f"{academy.title}: {label} has no assessment items")
            if slug not in challenge_slugs:
                gaps.append(f"{academy.title}: {label} has no coding challenges")
            if slug not in project_slugs:
                gaps.append(f"{academy.title}: {label} has no project-style challenge")
            if slug not in resource_concepts:
                gaps.append(f"{academy.title}: {label} has no catalog resources")
            else:
                have = types_by_concept.get(slug, set())
                for needed in ("documentation", "tutorial", "video", "course", "paper", "book"):
                    if needed not in have:
                        gaps.append(f"{academy.title}: {label} is missing a {needed}")
            if not any(slug in concepts for concepts in path_concept_sets):
                gaps.append(f"{academy.title}: {label} is on no learning path")
    return gaps
