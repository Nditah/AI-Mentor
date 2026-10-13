"""Subject taxonomy, skills, career roles, and registered content sources.

The tree is category → subcategory → topic. A concept hangs off one topic. Facet
counts stay honest because a node has one parent (docs/platform/13).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.knowledge.vocabulary import RESOURCE_TYPES


@dataclass(frozen=True)
class TaxonomyEntry:
    slug: str
    name: str
    level: str
    parent: str | None
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillDef:
    slug: str
    name: str
    family: str
    kind: str
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CareerRoleDef:
    slug: str
    title: str
    summary: str
    skills: tuple[str, ...]
    concepts: tuple[str, ...]


@dataclass(frozen=True)
class SourceDef:
    slug: str
    name: str
    provider: str
    connector: str
    homepage: str
    description: str
    resource_types: tuple[str, ...]
    schedule: str = "manual"
    trust_level: int = 4
    publish_policy: str = "review"
    terms_note: str = ""
    credential_env: str | None = None


def _cat(slug: str, name: str, description: str, *aliases: str) -> TaxonomyEntry:
    return TaxonomyEntry(slug, name, "category", None, description, aliases)


def _sub(parent: str, slug: str, name: str, description: str) -> TaxonomyEntry:
    return TaxonomyEntry(slug, name, "subcategory", parent, description)


def _topic(parent: str, slug: str, name: str, description: str) -> TaxonomyEntry:
    return TaxonomyEntry(slug, name, "topic", parent, description)


TAXONOMY: tuple[TaxonomyEntry, ...] = (
    _cat(
        "artificial-intelligence",
        "Artificial Intelligence",
        "Agents, search, knowledge representation, and the history of AI.",
        "ai",
    ),
    _sub(
        "artificial-intelligence",
        "ai-foundations",
        "Foundations",
        "What an agent is and how it acts.",
    ),
    _topic(
        "ai-foundations",
        "intelligent-agents",
        "Intelligent agents",
        "PEAS, rationality, and environments.",
    ),
    _topic(
        "ai-foundations",
        "search-planning",
        "Search and planning",
        "Uninformed, informed, and adversarial search.",
    ),
    _topic(
        "ai-foundations",
        "knowledge-representation",
        "Knowledge representation",
        "Logic, ontologies, and uncertainty.",
    ),
    _sub(
        "artificial-intelligence",
        "ai-practice",
        "Practice",
        "How AI systems are built and evaluated.",
    ),
    _topic("ai-practice", "ai-ethics", "AI ethics", "Fairness, safety, and accountability."),
    _topic(
        "ai-practice",
        "ai-history",
        "History of AI",
        "Symbolic, statistical, and foundation-model eras.",
    ),
    _cat(
        "machine-learning",
        "Machine Learning",
        "Supervised, unsupervised, and classical statistical learning.",
        "ml",
    ),
    _sub("machine-learning", "ml-supervised", "Supervised learning", "Predict a labelled target."),
    _topic(
        "ml-supervised",
        "linear-models",
        "Linear models",
        "Least squares, logistic regression, regularisation.",
    ),
    _topic(
        "ml-supervised",
        "tree-ensembles",
        "Trees and ensembles",
        "Decision trees, random forests, boosting.",
    ),
    _topic(
        "ml-supervised", "kernel-methods", "Kernel methods", "SVMs and kernel ridge regression."
    ),
    _sub(
        "machine-learning", "ml-unsupervised", "Unsupervised learning", "Structure without labels."
    ),
    _topic("ml-unsupervised", "clustering", "Clustering", "k-means, GMM, hierarchical, spectral."),
    _topic(
        "ml-unsupervised",
        "dimensionality-reduction",
        "Dimensionality reduction",
        "PCA, t-SNE, UMAP, autoencoders.",
    ),
    _sub("machine-learning", "ml-evaluation", "Evaluation", "How we know a model is any good."),
    _topic(
        "ml-evaluation",
        "model-selection",
        "Model selection",
        "Cross-validation, bias-variance, calibration.",
    ),
    _cat(
        "deep-learning",
        "Deep Learning",
        "Neural networks, representation learning, and modern architectures.",
        "dl",
    ),
    _sub(
        "deep-learning",
        "dl-foundations",
        "Foundations",
        "What a network computes and how it is trained.",
    ),
    _topic(
        "dl-foundations", "neural-networks", "Neural networks", "MLPs, activations, loss surfaces."
    ),
    _topic(
        "dl-foundations", "optimisation", "Optimisation", "SGD, Adam, batch norm, regularisation."
    ),
    _topic("dl-foundations", "backpropagation", "Backpropagation", "Reverse-mode autodiff."),
    _sub("deep-learning", "dl-architectures", "Architectures", "Families of models."),
    _topic(
        "dl-architectures", "cnns", "Convolutional networks", "Conv, pooling, residual connections."
    ),
    _topic("dl-architectures", "rnns", "Sequence models", "RNN, LSTM, GRU, and their limits."),
    _topic(
        "dl-architectures", "transformers", "Transformers", "Attention, encoder-decoder, scaling."
    ),
    _cat(
        "reinforcement-learning",
        "Reinforcement Learning",
        "Sequential decision making under uncertainty.",
        "rl",
    ),
    _sub(
        "reinforcement-learning", "rl-foundations", "Foundations", "MDPs and the Bellman equations."
    ),
    _topic(
        "rl-foundations",
        "mdp",
        "Markov decision processes",
        "States, actions, rewards, and discounting.",
    ),
    _topic(
        "rl-foundations",
        "bellman-equation",
        "Bellman equation",
        "Expectation and optimality operators.",
    ),
    _topic(
        "rl-foundations",
        "dynamic-programming-rl",
        "Dynamic programming",
        "Policy and value iteration.",
    ),
    _sub("reinforcement-learning", "rl-control", "Control", "Learning a policy from interaction."),
    _topic("rl-control", "q-learning", "Q-learning", "Off-policy TD control."),
    _topic(
        "rl-control", "policy-gradients", "Policy gradients", "REINFORCE, actor-critic, PPO, SAC."
    ),
    _topic("rl-control", "deep-rl", "Deep RL", "DQN and function approximation."),
    _cat(
        "generative-ai",
        "Generative AI",
        "Models that produce text, images, audio, and code.",
        "genai",
    ),
    _sub(
        "generative-ai",
        "gen-models",
        "Generative models",
        "Likelihood, adversarial, and diffusion families.",
    ),
    _topic("gen-models", "gans", "GANs", "Adversarial training of generators."),
    _topic("gen-models", "vaes", "Variational autoencoders", "ELBO and latent variable models."),
    _topic("gen-models", "diffusion-models", "Diffusion models", "Score matching and denoising."),
    _sub("generative-ai", "gen-applications", "Applications", "How generative systems are used."),
    _topic(
        "gen-applications",
        "prompting",
        "Prompting",
        "Instruction following and in-context learning.",
    ),
    _topic("gen-applications", "alignment", "Alignment", "RLHF, constitutional AI, and evals."),
    _cat(
        "data-science",
        "Data Science",
        "Asking questions of data and communicating the answer.",
        "ds",
    ),
    _sub("data-science", "ds-workflow", "Workflow", "From question to decision."),
    _topic("ds-workflow", "eda", "Exploratory analysis", "Distributions, missingness, and plots."),
    _topic(
        "ds-workflow",
        "feature-engineering",
        "Feature engineering",
        "Transforms that make models learn.",
    ),
    _topic("ds-workflow", "experimentation", "Experimentation", "A/B tests and causal sketches."),
    _cat(
        "data-engineering",
        "Data Engineering",
        "Pipelines, warehouses, and the path from event to feature.",
        "de",
    ),
    _sub("data-engineering", "de-systems", "Systems", "Storage and compute for data."),
    _topic("de-systems", "warehouses", "Warehouses and lakes", "Batch storage of analytic data."),
    _topic(
        "de-systems", "streaming", "Streaming", "Event time, watermarks, and Kafka-class systems."
    ),
    _topic("de-systems", "orchestration", "Orchestration", "Airflow, Dagster, and dbt."),
    _cat(
        "statistics",
        "Statistics",
        "Uncertainty, estimation, and testing.",
        "stats",
    ),
    _sub("statistics", "stats-inference", "Inference", "From sample to population."),
    _topic(
        "stats-inference", "probability", "Probability", "Random variables and common families."
    ),
    _topic("stats-inference", "estimation", "Estimation", "MLE, Bayes, bootstrap."),
    _topic(
        "stats-inference",
        "hypothesis-testing",
        "Hypothesis testing",
        "p-values, power, multiple testing.",
    ),
    _cat(
        "mathematics",
        "Mathematics",
        "The language the rest of the catalog is written in.",
        "maths",
        "math",
    ),
    _sub("mathematics", "math-core", "Core", "Linear algebra, calculus, and optimisation."),
    _topic("math-core", "linear-algebra", "Linear algebra", "Vectors, matrices, eigenvalues."),
    _topic("math-core", "calculus", "Calculus", "Gradients, Jacobians, and Taylor."),
    _topic(
        "math-core",
        "optimisation-math",
        "Optimisation",
        "Convexity, Lagrange, first-order methods.",
    ),
    _cat(
        "robotics",
        "Robotics",
        "Embodied agents: sensing, planning, and acting in the world.",
    ),
    _sub("robotics", "robot-foundations", "Foundations", "Kinematics, dynamics, and control."),
    _topic("robot-foundations", "kinematics", "Kinematics", "Forward and inverse kinematics."),
    _topic("robot-foundations", "control-theory", "Control", "PID, LQR, and trajectory tracking."),
    _topic("robot-foundations", "slam", "SLAM", "Localisation and mapping."),
    _sub("robotics", "robot-systems", "Systems", "How a robot is assembled in software."),
    _topic("robot-systems", "perception-robotics", "Perception", "Sensors to state estimates."),
    _topic(
        "robot-systems", "motion-planning", "Motion planning", "Sampling and optimisation planners."
    ),
    _cat(
        "ros2",
        "ROS 2",
        "The Robot Operating System as a teaching platform.",
        "ros",
    ),
    _sub("ros2", "ros-core", "Core", "Nodes, topics, services, and actions."),
    _topic("ros-core", "ros-nodes", "Nodes and topics", "Publishers, subscribers, and QoS."),
    _topic("ros-core", "ros-launch", "Launch and parameters", "Bring-up of a robot system."),
    _topic("ros-core", "nav2", "Nav2", "Navigation stack in ROS 2."),
    _cat(
        "computer-vision",
        "Computer Vision",
        "Images to structure: detection, geometry, and video.",
        "cv",
        "vision",
    ),
    _sub("computer-vision", "cv-classic", "Classic vision", "Geometry and hand-crafted features."),
    _topic("cv-classic", "image-formation", "Image formation", "Cameras, colour, and filtering."),
    _topic("cv-classic", "multiview", "Multiple views", "Stereo, homography, and SfM."),
    _sub("computer-vision", "cv-learning", "Learning-based vision", "Convnets and beyond."),
    _topic("cv-learning", "detection", "Detection and segmentation", "Boxes, masks, and tracking."),
    _topic(
        "cv-learning",
        "vision-transformers",
        "Vision transformers",
        "ViT, CLIP, and multimodal models.",
    ),
    _cat(
        "nlp",
        "Natural Language Processing",
        "Language as data: from tokens to meaning.",
        "natural-language-processing",
    ),
    _sub("nlp", "nlp-foundations", "Foundations", "Text as sequences."),
    _topic("nlp-foundations", "tokenization", "Tokenization", "Words, subwords, and BPE."),
    _topic("nlp-foundations", "language-models", "Language models", "n-grams to transformers."),
    _topic(
        "nlp-foundations",
        "representation-nlp",
        "Representations",
        "Word2Vec, BERT, and sentence embeddings.",
    ),
    _sub("nlp", "nlp-tasks", "Tasks", "What we ask language models to do."),
    _topic("nlp-tasks", "sequence-labeling", "Sequence labelling", "NER, parsing, and tagging."),
    _topic("nlp-tasks", "generation", "Generation", "Decoding, evaluation, and hallucination."),
    _cat(
        "mlops",
        "MLOps",
        "Taking a model from a notebook to a living service.",
    ),
    _sub("mlops", "mlops-lifecycle", "Lifecycle", "Train, ship, watch, retrain."),
    _topic(
        "mlops-lifecycle",
        "experiment-tracking",
        "Experiment tracking",
        "Runs, artefacts, and lineage.",
    ),
    _topic("mlops-lifecycle", "serving", "Serving", "Batch, online, and streaming inference."),
    _topic("mlops-lifecycle", "monitoring", "Monitoring", "Drift, quality, and incident response."),
    _cat(
        "llm-engineering",
        "LLM Engineering",
        "Building products on large language models.",
        "llm",
    ),
    _sub("llm-engineering", "llm-build", "Building", "Context, tools, and evaluation."),
    _topic("llm-build", "rag", "Retrieval-augmented generation", "Ground answers in a corpus."),
    _topic("llm-build", "agents", "Agents and tools", "Planning, function calling, and memory."),
    _topic("llm-build", "evals", "Evals", "Task suites, judges, and regression gates."),
    _topic("llm-build", "serving-llms", "Serving LLMs", "Quantisation, batching, and latency."),
    _cat(
        "ai-research-methods",
        "AI Research Methods",
        "How a result is produced, reviewed, and reproduced.",
        "research-methods",
    ),
    _sub("ai-research-methods", "research-practice", "Practice", "The craft of a paper."),
    _topic(
        "research-practice",
        "experimental-design",
        "Experimental design",
        "Baselines, ablations, and seeds.",
    ),
    _topic("research-practice", "reproducibility", "Reproducibility", "Code, data, and claims."),
    _topic(
        "research-practice", "reading-papers", "Reading papers", "How to extract a contribution."
    ),
    _cat(
        "scientific-writing",
        "Scientific Writing",
        "Clear claims, honest limits, and a paper that can be reviewed.",
        "writing",
    ),
    _sub("scientific-writing", "writing-craft", "Craft", "Structure and style."),
    _topic(
        "writing-craft", "paper-structure", "Paper structure", "IMRaD, related work, and figures."
    ),
    _topic("writing-craft", "citation-practice", "Citation", "Prior work and academic integrity."),
    _topic("writing-craft", "peer-review", "Peer review", "Giving and receiving technical review."),
)

SKILLS: tuple[SkillDef, ...] = (
    SkillDef("python", "Python", "programming", "tool", "The working language of the catalog."),
    SkillDef("numpy", "NumPy", "programming", "tool", "Array computing."),
    SkillDef("pandas", "pandas", "data", "tool", "Tabular analysis."),
    SkillDef("scikit-learn", "scikit-learn", "ml", "tool", "Classical machine learning."),
    SkillDef("pytorch", "PyTorch", "deep-learning", "tool", "Autodiff and neural nets."),
    SkillDef("tensorflow", "TensorFlow", "deep-learning", "tool", "Graphs, Keras, and serving."),
    SkillDef("jax", "JAX", "deep-learning", "tool", "Composable function transformations."),
    SkillDef("huggingface", "Hugging Face", "nlp", "tool", "Models, datasets, and tokenizers."),
    SkillDef("langchain", "LangChain", "llm", "tool", "Chains, tools, and retrieval."),
    SkillDef("ros2", "ROS 2", "robotics", "tool", "Robot middleware."),
    SkillDef("opencv", "OpenCV", "vision", "tool", "Classic computer vision."),
    SkillDef("sql", "SQL", "data", "tool", "Relational queries."),
    SkillDef("spark", "Apache Spark", "data", "tool", "Distributed data processing."),
    SkillDef("airflow", "Apache Airflow", "data", "tool", "Workflow orchestration."),
    SkillDef("docker", "Docker", "mlops", "tool", "Reproducible runtimes."),
    SkillDef("kubernetes", "Kubernetes", "mlops", "tool", "Container orchestration."),
    SkillDef("git", "Git", "engineering", "tool", "Version control."),
    SkillDef(
        "probability", "Probability", "maths", "mathematical", "Random variables and expectation."
    ),
    SkillDef(
        "linear-algebra",
        "Linear algebra",
        "maths",
        "mathematical",
        "Vector spaces and decompositions.",
    ),
    SkillDef("calculus", "Calculus", "maths", "mathematical", "Derivatives used in learning."),
    SkillDef("optimisation", "Optimisation", "maths", "mathematical", "Minimise a loss."),
    SkillDef("statistics", "Statistics", "maths", "mathematical", "Estimation and testing."),
    SkillDef("mdp-reasoning", "MDP reasoning", "rl", "technical", "States, values, and policies."),
    SkillDef("bellman", "Bellman equations", "rl", "technical", "Recursive value relationships."),
    SkillDef(
        "td-learning",
        "Temporal-difference learning",
        "rl",
        "technical",
        "Bootstrapped value updates.",
    ),
    SkillDef(
        "policy-optimisation",
        "Policy optimisation",
        "rl",
        "technical",
        "Directly improving a policy.",
    ),
    SkillDef(
        "deep-rl",
        "Deep reinforcement learning",
        "rl",
        "technical",
        "Function approximation in control.",
    ),
    SkillDef(
        "transformers",
        "Transformers",
        "deep-learning",
        "technical",
        "Attention-based sequence models.",
    ),
    SkillDef("cnn-design", "CNN design", "vision", "technical", "Convolutional architectures."),
    SkillDef(
        "detection", "Object detection", "vision", "technical", "Localising instances in images."
    ),
    SkillDef(
        "language-modeling", "Language modeling", "nlp", "technical", "Next-token prediction."
    ),
    SkillDef("retrieval", "Retrieval", "llm", "technical", "Finding the right passage."),
    SkillDef(
        "prompt-engineering",
        "Prompt engineering",
        "llm",
        "technical",
        "Steering a model with text.",
    ),
    SkillDef(
        "evals", "Model evaluation", "llm", "technical", "Measuring quality without self-deception."
    ),
    SkillDef(
        "rag-systems", "RAG systems", "llm", "technical", "Grounded generation over a corpus."
    ),
    SkillDef(
        "feature-stores",
        "Feature stores",
        "mlops",
        "technical",
        "Serving training-time features online.",
    ),
    SkillDef(
        "model-serving", "Model serving", "mlops", "technical", "Latency, batching, and rollback."
    ),
    SkillDef(
        "observability", "Observability", "mlops", "technical", "Logs, traces, and data drift."
    ),
    SkillDef("kinematics", "Kinematics", "robotics", "technical", "Geometry of mechanisms."),
    SkillDef("control", "Feedback control", "robotics", "technical", "Stabilising a plant."),
    SkillDef("slam", "SLAM", "robotics", "technical", "Where am I, and what is around me."),
    SkillDef(
        "scientific-writing",
        "Scientific writing",
        "research",
        "professional",
        "Claims a reviewer can check.",
    ),
    SkillDef(
        "experimental-design",
        "Experimental design",
        "research",
        "professional",
        "Fair comparisons.",
    ),
    SkillDef(
        "paper-reading", "Paper reading", "research", "professional", "Extracting a contribution."
    ),
    SkillDef(
        "communication",
        "Technical communication",
        "professional",
        "professional",
        "Explaining a result.",
    ),
)

CAREER_ROLES: tuple[CareerRoleDef, ...] = (
    CareerRoleDef(
        "ml-engineer",
        "Machine Learning Engineer",
        "Ships models that stay correct after they leave the notebook.",
        ("python", "scikit-learn", "pytorch", "docker", "model-serving"),
        ("supervised-learning", "neural-networks", "mlops-lifecycle"),
    ),
    CareerRoleDef(
        "data-scientist",
        "Data Scientist",
        "Turns a business question into an experiment and a decision.",
        ("python", "pandas", "sql", "statistics", "communication"),
        ("eda", "probability", "model-selection"),
    ),
    CareerRoleDef(
        "data-engineer",
        "Data Engineer",
        "Makes the data trustworthy enough for everyone else to use.",
        ("sql", "spark", "airflow", "python", "docker"),
        ("warehouses", "streaming", "orchestration"),
    ),
    CareerRoleDef(
        "rl-engineer",
        "Reinforcement Learning Engineer",
        "Learns policies in simulation and transfers them with care.",
        ("python", "pytorch", "mdp-reasoning", "deep-rl", "policy-optimisation"),
        ("mdp", "q-learning", "ppo"),
    ),
    CareerRoleDef(
        "robotics-engineer",
        "Robotics Engineer",
        "Puts perception, planning, and control on a real machine.",
        ("python", "ros2", "kinematics", "control", "slam"),
        ("ros-nodes", "kinematics", "nav2"),
    ),
    CareerRoleDef(
        "cv-engineer",
        "Computer Vision Engineer",
        "Reads the world from pixels.",
        ("python", "pytorch", "opencv", "cnn-design", "detection"),
        ("cnns", "detection", "vision-transformers"),
    ),
    CareerRoleDef(
        "nlp-engineer",
        "NLP Engineer",
        "Builds language systems that stay on the source.",
        ("python", "pytorch", "huggingface", "language-modeling", "retrieval"),
        ("tokenization", "transformers", "rag"),
    ),
    CareerRoleDef(
        "llm-engineer",
        "LLM Engineer",
        "Products on foundation models, with evals that bite.",
        ("python", "huggingface", "rag-systems", "prompt-engineering", "evals"),
        ("rag", "agents", "evals"),
    ),
    CareerRoleDef(
        "mlops-engineer",
        "MLOps Engineer",
        "The path from a trained artefact to a watched service.",
        ("python", "docker", "kubernetes", "observability", "model-serving"),
        ("experiment-tracking", "serving", "monitoring"),
    ),
    CareerRoleDef(
        "research-scientist",
        "Research Scientist",
        "A result that another lab can reproduce.",
        ("python", "pytorch", "experimental-design", "scientific-writing", "paper-reading"),
        ("experimental-design", "reproducibility", "paper-structure"),
    ),
)

_ALL_TYPES = tuple(RESOURCE_TYPES)

SOURCES: tuple[SourceDef, ...] = (
    SourceDef(
        "curated-pack",
        "AI Mentor Knowledge Pack",
        "AI Mentor",
        "pack",
        "https://aimentor.local/knowledge-pack",
        "Launch catalog authored and compiled into Knowledge Pack v1.0.",
        _ALL_TYPES,
        schedule="manual",
        trust_level=5,
        publish_policy="publish",
        terms_note="Original catalog records and citations of public educational pages.",
    ),
    SourceDef(
        "microsoft-learn",
        "Microsoft Learn",
        "Microsoft",
        "learn_catalog",
        "https://learn.microsoft.com",
        "Official Microsoft learning modules, including Azure AI and data.",
        ("course", "tutorial", "documentation", "certification"),
        schedule="weekly",
        terms_note="Import metadata and links; do not copy module bodies.",
    ),
    SourceDef(
        "coursera",
        "Coursera",
        "Coursera",
        "catalog_api",
        "https://www.coursera.org",
        "University and industry courses. Many allow a free audit.",
        ("course", "certification"),
        schedule="weekly",
        credential_env="COURSERA_API_KEY",
        terms_note="Partner API. Store links and metadata only.",
    ),
    SourceDef(
        "edx",
        "edX",
        "edX",
        "catalog_api",
        "https://www.edx.org",
        "Open edX and 2U catalog, including MITx and HarvardX.",
        ("course", "certification"),
        schedule="weekly",
        terms_note="Public course pages. No lecture video files.",
    ),
    SourceDef(
        "mit-ocw",
        "MIT OpenCourseWare",
        "MIT",
        "ocw",
        "https://ocw.mit.edu",
        "Full MIT courses with notes, assignments, and many videos.",
        ("course", "video", "tutorial", "documentation"),
        schedule="monthly",
        trust_level=5,
        publish_policy="publish",
        terms_note="CC licences on OCW materials. Record the licence on each asset.",
    ),
    SourceDef(
        "stanford-ai",
        "Stanford AI",
        "Stanford University",
        "web",
        "https://cs.stanford.edu",
        "CS229, CS231n, CS224n, CS234 and related public lecture pages.",
        ("course", "video", "paper"),
        schedule="monthly",
        trust_level=5,
    ),
    SourceDef(
        "deeplearning-ai",
        "DeepLearning.AI",
        "DeepLearning.AI",
        "web",
        "https://www.deeplearning.ai",
        "Andrew Ng specialisations and short courses on Coursera.",
        ("course", "certification"),
        schedule="monthly",
    ),
    SourceDef(
        "fastai",
        "fast.ai",
        "fast.ai",
        "web",
        "https://www.fast.ai",
        "Practical deep learning courses and the fastai library.",
        ("course", "video", "documentation", "repository"),
        schedule="monthly",
        trust_level=5,
        publish_policy="publish",
    ),
    SourceDef(
        "huggingface",
        "Hugging Face",
        "Hugging Face",
        "hub",
        "https://huggingface.co",
        "Models, datasets, papers, and the course.",
        ("dataset", "repository", "course", "documentation", "paper"),
        schedule="daily",
        terms_note="Hub cards and licences. Respect gated datasets.",
    ),
    SourceDef(
        "openai-docs",
        "OpenAI Documentation",
        "OpenAI",
        "docs",
        "https://platform.openai.com/docs",
        "API, prompting, and eval guides.",
        ("documentation", "tutorial"),
        schedule="weekly",
    ),
    SourceDef(
        "anthropic-docs",
        "Anthropic Documentation",
        "Anthropic",
        "docs",
        "https://docs.anthropic.com",
        "Claude API, tool use, and constitutional prompting.",
        ("documentation", "tutorial"),
        schedule="weekly",
    ),
    SourceDef(
        "ros-docs",
        "ROS Documentation",
        "Open Robotics",
        "docs",
        "https://docs.ros.org",
        "ROS 2 tutorials, interfaces, and Nav2.",
        ("documentation", "tutorial"),
        schedule="weekly",
        trust_level=5,
        publish_policy="publish",
    ),
    SourceDef(
        "nvidia-learn",
        "NVIDIA Learning",
        "NVIDIA",
        "web",
        "https://www.nvidia.com/en-us/training/",
        "DLI courses and GPU-accelerated libraries.",
        ("course", "certification", "documentation"),
        schedule="monthly",
    ),
    SourceDef(
        "kaggle",
        "Kaggle",
        "Kaggle",
        "kaggle",
        "https://www.kaggle.com",
        "Datasets, notebooks, and competitions.",
        ("dataset", "tutorial", "coding_challenge"),
        schedule="weekly",
        credential_env="KAGGLE_API_TOKEN",
        terms_note="Dataset licences vary. Store the licence from the data card.",
    ),
    SourceDef(
        "arxiv",
        "arXiv",
        "Cornell arXiv",
        "arxiv",
        "https://arxiv.org",
        "Preprints in cs.LG, cs.AI, cs.CV, cs.CL, cs.RO, stat.ML.",
        ("paper",),
        schedule="daily",
        trust_level=3,
        publish_policy="review",
        terms_note="Metadata and abstracts. Full PDF only when the licence allows.",
    ),
    SourceDef(
        "paperswithcode",
        "Papers with Code",
        "Meta AI",
        "pwc",
        "https://paperswithcode.com",
        "Paper–code–dataset links and leaderboards.",
        ("paper", "repository", "dataset"),
        schedule="daily",
    ),
    SourceDef(
        "github",
        "GitHub",
        "GitHub",
        "github",
        "https://github.com",
        "Pinned educational repositories.",
        ("repository",),
        schedule="weekly",
        credential_env="GITHUB_TOKEN",
        terms_note="README and SPDX licence at a commit SHA. No secrets.",
    ),
    SourceDef(
        "tensorflow-docs",
        "TensorFlow Documentation",
        "Google",
        "docs",
        "https://www.tensorflow.org",
        "Guides, tutorials, and the TensorFlow Certificate study path.",
        ("documentation", "tutorial", "course"),
        schedule="weekly",
        publish_policy="publish",
    ),
    SourceDef(
        "pytorch-docs",
        "PyTorch Documentation",
        "PyTorch Foundation",
        "docs",
        "https://pytorch.org/docs",
        "API reference, tutorials, and recipes.",
        ("documentation", "tutorial"),
        schedule="weekly",
        publish_policy="publish",
        trust_level=5,
    ),
    SourceDef(
        "sklearn-docs",
        "scikit-learn Documentation",
        "scikit-learn",
        "docs",
        "https://scikit-learn.org/stable",
        "User guide and examples for classical ML.",
        ("documentation", "tutorial"),
        schedule="monthly",
        publish_policy="publish",
        trust_level=5,
    ),
)


def taxonomy_index() -> dict[str, TaxonomyEntry]:
    return {node.slug: node for node in TAXONOMY}


def skill_index() -> dict[str, SkillDef]:
    return {skill.slug: skill for skill in SKILLS}


def source_index() -> dict[str, SourceDef]:
    return {source.slug: source for source in SOURCES}


def category_of(slug: str) -> str:
    """Walk parents until a category. Unknown slugs return empty."""

    nodes = taxonomy_index()
    current = nodes.get(slug)
    while current is not None:
        if current.level == "category":
            return current.slug
        current = nodes.get(current.parent) if current.parent else None
    return ""


def path_of(slug: str) -> tuple[str, ...]:
    nodes = taxonomy_index()
    chain: list[str] = []
    current = nodes.get(slug)
    while current is not None:
        chain.append(current.slug)
        current = nodes.get(current.parent) if current.parent else None
    return tuple(reversed(chain))


def children_of(slug: str) -> tuple[TaxonomyEntry, ...]:
    return tuple(node for node in TAXONOMY if node.parent == slug)


def validate_taxonomy() -> None:
    """Raise if a parent is missing, a slug repeats, or a topic hangs off a category."""

    seen: set[str] = set()
    by_slug = {}
    for node in TAXONOMY:
        if node.slug in seen:
            raise ValueError(f"duplicate taxonomy slug {node.slug}")
        seen.add(node.slug)
        by_slug[node.slug] = node
    for node in TAXONOMY:
        if node.level == "category" and node.parent is not None:
            raise ValueError(f"category {node.slug} has a parent")
        if node.level != "category":
            if node.parent is None or node.parent not in by_slug:
                raise ValueError(f"{node.slug} is missing its parent")
            parent = by_slug[node.parent]
            expected = {"subcategory": "category", "topic": "subcategory"}[node.level]
            if parent.level != expected:
                raise ValueError(f"{node.slug} hangs off a {parent.level}, want {expected}")
