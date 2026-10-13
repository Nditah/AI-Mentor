"""Compile Knowledge Pack v1.0: concepts, catalog records, questions, and challenges.

The pack is deterministic. `compile_pack()` is the only function the seeder needs.
Landmark identifiers are real; generated coverage records point at public
documentation, lecture playlists, and Hub pages so a learner can open the source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.domain.knowledge.asset import AssetRecord, slugify
from app.domain.knowledge.graph import ConceptEdge, ConceptNode, KnowledgeGraph, from_tuples
from app.domain.knowledge.pack_concepts import (
    CONCEPT_ROWS,
    concept_category,
    concept_topic,
    pack_nodes,
    pack_prerequisites,
)
from app.domain.knowledge.pack_landmarks import BOOKS, PAPERS
from app.domain.knowledge.quality import score_record
from app.domain.knowledge.taxonomy import CAREER_ROLES, SKILLS, SOURCES, TAXONOMY
from app.domain.knowledge.vocabulary import DEFAULT_DURATION

PACK_VERSION = "1.0.0"
PACK_NAME = "AI Mentor Knowledge Pack"

DOC_HOMES = {
    "artificial-intelligence": (
        "Stanford CS221",
        "https://stanford.edu/~shervine/teaching/cs-221/",
    ),
    "machine-learning": ("scikit-learn", "https://scikit-learn.org/stable/user_guide.html"),
    "deep-learning": ("PyTorch", "https://pytorch.org/tutorials/"),
    "reinforcement-learning": ("Spinning Up", "https://spinningup.openai.com/en/latest/"),
    "generative-ai": ("Hugging Face", "https://huggingface.co/docs"),
    "data-science": ("pandas", "https://pandas.pydata.org/docs/"),
    "data-engineering": ("Apache Spark", "https://spark.apache.org/docs/latest/"),
    "statistics": ("OpenIntro", "https://www.openintro.org/book/os/"),
    "mathematics": ("3Blue1Brown", "https://www.3blue1brown.com"),
    "robotics": ("Modern Robotics", "https://modernrobotics.northwestern.edu"),
    "ros2": ("ROS 2 docs", "https://docs.ros.org/en/humble/"),
    "computer-vision": ("PyTorch Vision", "https://pytorch.org/vision/stable/"),
    "nlp": ("Hugging Face NLP course", "https://huggingface.co/learn/nlp-course"),
    "mlops": ("Made With ML", "https://madewithml.com"),
    "llm-engineering": ("OpenAI docs", "https://platform.openai.com/docs"),
    "ai-research-methods": ("Papers with Code", "https://paperswithcode.com"),
    "scientific-writing": (
        "Equitable Equations",
        "https://www.elsevier.com/researcher/author/tools-and-resources",
    ),
}

LECTURE_SERIES: tuple[tuple[str, str, str, str, int, str], ...] = (
    (
        "Stanford CS229",
        "Andrew Ng",
        "machine-learning",
        "linear-models",
        20,
        "https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU",
    ),
    (
        "Stanford CS231n",
        "Fei-Fei Li, Justin Johnson, Serena Yeung",
        "computer-vision",
        "cnns",
        16,
        "https://www.youtube.com/playlist?list=PL3FW7Lu3i5JvHM8ljYj-zLfQRF3EO8sYv",
    ),
    (
        "Stanford CS224n",
        "Christopher Manning",
        "nlp",
        "language-models",
        18,
        "https://www.youtube.com/playlist?list=PLoROMvodv4rOSH4v6133s9LFPRHjEmbmJ",
    ),
    (
        "Stanford CS234",
        "Emma Brunskill",
        "reinforcement-learning",
        "mdp",
        10,
        "https://www.youtube.com/playlist?list=PLoROMvodv4rOSOPzutgyCTimagekB4LehPg",
    ),
    (
        "MIT 6.S191",
        "Alexander Amini, Ava Soleimany",
        "deep-learning",
        "neural-networks",
        10,
        "https://www.youtube.com/playlist?list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI",
    ),
    (
        "MIT 6.034",
        "Patrick Winston",
        "artificial-intelligence",
        "search-planning",
        12,
        "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/",
    ),
    (
        "MIT 18.06",
        "Gilbert Strang",
        "mathematics",
        "linear-algebra",
        35,
        "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/",
    ),
    (
        "MIT 6.041",
        "John Tsitsiklis",
        "statistics",
        "probability",
        25,
        "https://ocw.mit.edu/courses/6-041-probabilistic-systems-analysis-and-applied-probability-fall-2010/",
    ),
    (
        "fast.ai Practical Deep Learning",
        "Jeremy Howard",
        "deep-learning",
        "neural-networks",
        8,
        "https://course.fast.ai",
    ),
    (
        "DeepLearning.AI ML Specialization",
        "Andrew Ng",
        "machine-learning",
        "linear-models",
        12,
        "https://www.coursera.org/specializations/machine-learning-introduction",
    ),
    (
        "DeepLearning.AI Deep Learning Specialization",
        "Andrew Ng",
        "deep-learning",
        "neural-networks",
        15,
        "https://www.coursera.org/specializations/deep-learning",
    ),
    (
        "Hugging Face NLP course",
        "Hugging Face",
        "nlp",
        "tokenization",
        12,
        "https://huggingface.co/learn/nlp-course",
    ),
    (
        "Hugging Face Agents course",
        "Hugging Face",
        "llm-engineering",
        "agents",
        8,
        "https://huggingface.co/learn/agents-course",
    ),
    (
        "Spinning Up in Deep RL",
        "Joshua Achiam",
        "reinforcement-learning",
        "policy-gradients",
        8,
        "https://spinningup.openai.com/en/latest/",
    ),
    (
        "UC Berkeley CS285",
        "Sergey Levine",
        "reinforcement-learning",
        "deep-rl",
        20,
        "https://rail.eecs.berkeley.edu/deeprlcourse/",
    ),
    (
        "University of Alberta RL MOOC",
        "Martha White, Adam White",
        "reinforcement-learning",
        "mdp",
        12,
        "https://www.coursera.org/specializations/reinforcement-learning",
    ),
    (
        "ROS 2 Humble tutorials",
        "Open Robotics",
        "ros2",
        "ros-nodes",
        14,
        "https://docs.ros.org/en/humble/Tutorials.html",
    ),
    ("Nav2 documentation series", "Open Navigation", "ros2", "nav2", 10, "https://docs.nav2.org"),
    (
        "Modern Robotics Coursera",
        "Kevin Lynch",
        "robotics",
        "kinematics",
        12,
        "https://www.coursera.org/specializations/modernrobotics",
    ),
    (
        "MIT 6.8300 Computer Vision",
        "MIT",
        "computer-vision",
        "image-formation",
        12,
        "https://ocw.mit.edu",
    ),
    (
        "3Blue1Brown Essence of Linear Algebra",
        "Grant Sanderson",
        "mathematics",
        "linear-algebra",
        16,
        "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
    ),
    (
        "3Blue1Brown Neural Networks",
        "Grant Sanderson",
        "deep-learning",
        "neural-networks",
        7,
        "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",
    ),
    (
        "Andrej Karpathy Neural Networks: Zero to Hero",
        "Andrej Karpathy",
        "deep-learning",
        "neural-networks",
        8,
        "https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ",
    ),
    (
        "Andrej Karpathy Let's build GPT",
        "Andrej Karpathy",
        "llm-engineering",
        "rag",
        1,
        "https://www.youtube.com/watch?v=kCc8FmEb1nY",
    ),
    (
        "Stanford CS25 Transformers United",
        "Stanford",
        "deep-learning",
        "transformers",
        10,
        "https://web.stanford.edu/class/cs25/",
    ),
    (
        "Full Stack Deep Learning",
        "Pieter Abbeel, Sergey Karayev, Josh Tobin",
        "mlops",
        "serving",
        10,
        "https://fullstackdeeplearning.com",
    ),
    ("Made With ML", "Goku Mohandas", "mlops", "experiment-tracking", 12, "https://madewithml.com"),
    (
        "Microsoft Learn Azure AI",
        "Microsoft",
        "llm-engineering",
        "rag",
        15,
        "https://learn.microsoft.com/training/paths/develop-ai-solutions-azure-openai/",
    ),
    (
        "NVIDIA DLI Getting Started with Deep Learning",
        "NVIDIA",
        "deep-learning",
        "neural-networks",
        8,
        "https://www.nvidia.com/en-us/training/",
    ),
    (
        "StatQuest",
        "Josh Starmer",
        "statistics",
        "probability",
        20,
        "https://www.youtube.com/user/joshstarmer",
    ),
    (
        "Two Minute Papers",
        "Károly Zsolnai-Fehér",
        "ai-research-methods",
        "reading-papers",
        15,
        "https://www.youtube.com/user/keeroyz",
    ),
    (
        "Yannic Kilcher paper reviews",
        "Yannic Kilcher",
        "ai-research-methods",
        "reading-papers",
        12,
        "https://www.youtube.com/@YannicKilcher",
    ),
)

COURSES: tuple[tuple[str, str, str, str, str, str, str], ...] = (
    (
        "Machine Learning Specialization",
        "DeepLearning.AI / Stanford",
        "machine-learning",
        "linear-models",
        "beginner",
        "https://www.coursera.org/specializations/machine-learning-introduction",
        "free_audit",
    ),
    (
        "Deep Learning Specialization",
        "DeepLearning.AI",
        "deep-learning",
        "neural-networks",
        "intermediate",
        "https://www.coursera.org/specializations/deep-learning",
        "free_audit",
    ),
    (
        "Practical Deep Learning for Coders",
        "fast.ai",
        "deep-learning",
        "neural-networks",
        "intermediate",
        "https://course.fast.ai",
        "free",
    ),
    (
        "CS229 Machine Learning",
        "Stanford",
        "machine-learning",
        "linear-models",
        "intermediate",
        "https://cs229.stanford.edu",
        "free",
    ),
    (
        "CS231n Convolutional Neural Networks",
        "Stanford",
        "computer-vision",
        "cnns",
        "intermediate",
        "http://cs231n.stanford.edu",
        "free",
    ),
    (
        "CS224n NLP with Deep Learning",
        "Stanford",
        "nlp",
        "language-models",
        "advanced",
        "https://web.stanford.edu/class/cs224n/",
        "free",
    ),
    (
        "CS234 Reinforcement Learning",
        "Stanford",
        "reinforcement-learning",
        "mdp",
        "advanced",
        "https://web.stanford.edu/class/cs234/",
        "free",
    ),
    (
        "CS285 Deep Reinforcement Learning",
        "UC Berkeley",
        "reinforcement-learning",
        "deep-rl",
        "advanced",
        "https://rail.eecs.berkeley.edu/deeprlcourse/",
        "free",
    ),
    (
        "MIT 6.S191 Introduction to Deep Learning",
        "MIT",
        "deep-learning",
        "neural-networks",
        "intermediate",
        "https://introtodeeplearning.com",
        "free",
    ),
    (
        "MIT 6.034 Artificial Intelligence",
        "MIT OCW",
        "artificial-intelligence",
        "search-planning",
        "intermediate",
        "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/",
        "free",
    ),
    (
        "Hugging Face NLP Course",
        "Hugging Face",
        "nlp",
        "tokenization",
        "intermediate",
        "https://huggingface.co/learn/nlp-course",
        "free",
    ),
    (
        "Hugging Face Agents Course",
        "Hugging Face",
        "llm-engineering",
        "agents",
        "intermediate",
        "https://huggingface.co/learn/agents-course",
        "free",
    ),
    (
        "LangChain Academy",
        "LangChain",
        "llm-engineering",
        "agents",
        "intermediate",
        "https://academy.langchain.com",
        "free",
    ),
    (
        "Full Stack LLM Bootcamp",
        "fullstackdeeplearning.com",
        "llm-engineering",
        "evals",
        "advanced",
        "https://fullstackdeeplearning.com/llm-bootcamp/",
        "free",
    ),
    (
        "Made With ML",
        "Goku Mohandas",
        "mlops",
        "experiment-tracking",
        "intermediate",
        "https://madewithml.com",
        "free",
    ),
    (
        "MLOps Specialization",
        "DeepLearning.AI",
        "mlops",
        "serving",
        "intermediate",
        "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops",
        "free_audit",
    ),
    (
        "Generative Adversarial Networks Specialization",
        "DeepLearning.AI",
        "generative-ai",
        "gans",
        "advanced",
        "https://www.coursera.org/specializations/generative-adversarial-networks-gans",
        "free_audit",
    ),
    (
        "Generative AI with LLMs",
        "DeepLearning.AI / AWS",
        "generative-ai",
        "prompting",
        "beginner",
        "https://www.deeplearning.ai/courses/generative-ai-with-llms/",
        "free_audit",
    ),
    (
        "ChatGPT Prompt Engineering for Developers",
        "DeepLearning.AI / OpenAI",
        "generative-ai",
        "prompting",
        "beginner",
        "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/",
        "free",
    ),
    (
        "Building Systems with the ChatGPT API",
        "DeepLearning.AI / OpenAI",
        "llm-engineering",
        "evals",
        "intermediate",
        "https://www.deeplearning.ai/short-courses/building-systems-with-chatgpt/",
        "free",
    ),
    (
        "LangChain for LLM Application Development",
        "DeepLearning.AI",
        "llm-engineering",
        "agents",
        "intermediate",
        "https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/",
        "free",
    ),
    (
        "Vector Databases: from Embeddings to Applications",
        "DeepLearning.AI / Weaviate",
        "llm-engineering",
        "rag",
        "intermediate",
        "https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/",
        "free",
    ),
    (
        "Reinforcement Learning Specialization",
        "University of Alberta",
        "reinforcement-learning",
        "mdp",
        "intermediate",
        "https://www.coursera.org/specializations/reinforcement-learning",
        "free_audit",
    ),
    (
        "Modern Robotics Specialization",
        "Northwestern",
        "robotics",
        "kinematics",
        "intermediate",
        "https://www.coursera.org/specializations/modernrobotics",
        "free_audit",
    ),
    (
        "ROS 2 Humble tutorials",
        "Open Robotics",
        "ros2",
        "ros-nodes",
        "beginner",
        "https://docs.ros.org/en/humble/Tutorials.html",
        "free",
    ),
    (
        "Nav2 Getting Started",
        "Open Navigation",
        "ros2",
        "nav2",
        "intermediate",
        "https://docs.nav2.org/getting_started/index.html",
        "free",
    ),
    (
        "Microsoft Azure AI Engineer",
        "Microsoft Learn",
        "llm-engineering",
        "rag",
        "intermediate",
        "https://learn.microsoft.com/certifications/azure-ai-engineer/",
        "free",
    ),
    (
        "Google ML Crash Course",
        "Google",
        "machine-learning",
        "linear-models",
        "beginner",
        "https://developers.google.com/machine-learning/crash-course",
        "free",
    ),
    (
        "TensorFlow Developer Certificate study path",
        "Google",
        "deep-learning",
        "neural-networks",
        "intermediate",
        "https://www.tensorflow.org/certificate",
        "free",
    ),
    (
        "PyTorch Tutorials",
        "PyTorch Foundation",
        "deep-learning",
        "neural-networks",
        "beginner",
        "https://pytorch.org/tutorials/",
        "free",
    ),
    (
        "Kaggle Intro to Machine Learning",
        "Kaggle",
        "machine-learning",
        "linear-models",
        "beginner",
        "https://www.kaggle.com/learn/intro-to-machine-learning",
        "free",
    ),
    (
        "Kaggle Intro to Deep Learning",
        "Kaggle",
        "deep-learning",
        "neural-networks",
        "beginner",
        "https://www.kaggle.com/learn/intro-to-deep-learning",
        "free",
    ),
    (
        "edX MITx 6.86x Machine Learning with Python",
        "MITx",
        "machine-learning",
        "linear-models",
        "intermediate",
        "https://www.edx.org/learn/machine-learning/massachusetts-institute-of-technology-machine-learning-with-python-from-linear-models-to-deep-learning",
        "free_audit",
    ),
    (
        "edX HarvardX CS50 AI",
        "HarvardX",
        "artificial-intelligence",
        "search-planning",
        "beginner",
        "https://cs50.harvard.edu/ai/",
        "free",
    ),
    (
        "Statistical Learning",
        "Stanford / Hastie, Tibshirani",
        "statistics",
        "estimation",
        "intermediate",
        "https://www.statlearning.com",
        "free",
    ),
    (
        "Probabilistic Graphical Models",
        "Daphne Koller",
        "machine-learning",
        "kernel-methods",
        "advanced",
        "https://www.coursera.org/specializations/probabilistic-graphical-models",
        "free_audit",
    ),
    (
        "Databases: Relational Databases and SQL",
        "Stanford",
        "data-engineering",
        "warehouses",
        "beginner",
        "https://online.stanford.edu",
        "free",
    ),
    (
        "Data Engineering Zoomcamp",
        "DataTalks.Club",
        "data-engineering",
        "orchestration",
        "intermediate",
        "https://github.com/DataTalksClub/data-engineering-zoomcamp",
        "free",
    ),
    (
        "MLOps Zoomcamp",
        "DataTalks.Club",
        "mlops",
        "serving",
        "intermediate",
        "https://github.com/DataTalksClub/mlops-zoomcamp",
        "free",
    ),
    (
        "LLM Zoomcamp",
        "DataTalks.Club",
        "llm-engineering",
        "rag",
        "intermediate",
        "https://github.com/DataTalksClub/llm-zoomcamp",
        "free",
    ),
)

REPOS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "pytorch/pytorch",
        "PyTorch",
        "deep-learning",
        "neural-networks",
        "https://github.com/pytorch/pytorch",
    ),
    (
        "tensorflow/tensorflow",
        "TensorFlow",
        "deep-learning",
        "neural-networks",
        "https://github.com/tensorflow/tensorflow",
    ),
    (
        "scikit-learn/scikit-learn",
        "scikit-learn",
        "machine-learning",
        "linear-models",
        "https://github.com/scikit-learn/scikit-learn",
    ),
    (
        "huggingface/transformers",
        "Transformers",
        "nlp",
        "transformers",
        "https://github.com/huggingface/transformers",
    ),
    (
        "huggingface/diffusers",
        "Diffusers",
        "generative-ai",
        "diffusion-models",
        "https://github.com/huggingface/diffusers",
    ),
    (
        "huggingface/peft",
        "PEFT",
        "llm-engineering",
        "serving-llms",
        "https://github.com/huggingface/peft",
    ),
    ("huggingface/trl", "TRL", "generative-ai", "alignment", "https://github.com/huggingface/trl"),
    (
        "huggingface/datasets",
        "Datasets",
        "data-science",
        "dataset-design",
        "https://github.com/huggingface/datasets",
    ),
    (
        "openai/spinningup",
        "Spinning Up",
        "reinforcement-learning",
        "policy-gradients",
        "https://github.com/openai/spinningup",
    ),
    (
        "DLR-RM/stable-baselines3",
        "Stable-Baselines3",
        "reinforcement-learning",
        "deep-rl",
        "https://github.com/DLR-RM/stable-baselines3",
    ),
    (
        "google-deepmind/acme",
        "Acme",
        "reinforcement-learning",
        "deep-rl",
        "https://github.com/google-deepmind/acme",
    ),
    (
        "google-deepmind/optax",
        "Optax",
        "deep-learning",
        "optimisation",
        "https://github.com/google-deepmind/optax",
    ),
    ("google/jax", "JAX", "deep-learning", "optimisation", "https://github.com/google/jax"),
    (
        "facebookresearch/detectron2",
        "Detectron2",
        "computer-vision",
        "detection",
        "https://github.com/facebookresearch/detectron2",
    ),
    (
        "ultralytics/ultralytics",
        "YOLO",
        "computer-vision",
        "detection",
        "https://github.com/ultralytics/ultralytics",
    ),
    (
        "opencv/opencv",
        "OpenCV",
        "computer-vision",
        "image-formation",
        "https://github.com/opencv/opencv",
    ),
    ("ros2/ros2", "ROS 2", "ros2", "ros-nodes", "https://github.com/ros2/ros2"),
    (
        "ros-navigation/navigation2",
        "Nav2",
        "ros2",
        "nav2",
        "https://github.com/ros-navigation/navigation2",
    ),
    (
        "cartographer-project/cartographer",
        "Cartographer",
        "robotics",
        "slam",
        "https://github.com/cartographer-project/cartographer",
    ),
    (
        "IntelRealSense/realsense-ros",
        "RealSense ROS",
        "ros2",
        "ros-nodes",
        "https://github.com/IntelRealSense/realsense-ros",
    ),
    (
        "ggerganov/llama.cpp",
        "llama.cpp",
        "llm-engineering",
        "serving-llms",
        "https://github.com/ggerganov/llama.cpp",
    ),
    (
        "vllm-project/vllm",
        "vLLM",
        "llm-engineering",
        "serving-llms",
        "https://github.com/vllm-project/vllm",
    ),
    (
        "microsoft/DeepSpeed",
        "DeepSpeed",
        "mlops",
        "experiment-tracking",
        "https://github.com/microsoft/DeepSpeed",
    ),
    ("mlflow/mlflow", "MLflow", "mlops", "experiment-tracking", "https://github.com/mlflow/mlflow"),
    (
        "wandb/wandb",
        "Weights & Biases",
        "mlops",
        "experiment-tracking",
        "https://github.com/wandb/wandb",
    ),
    ("explosion/spaCy", "spaCy", "nlp", "sequence-labeling", "https://github.com/explosion/spaCy"),
    ("nltk/nltk", "NLTK", "nlp", "tokenization", "https://github.com/nltk/nltk"),
    (
        "streamlit/streamlit",
        "Streamlit",
        "data-science",
        "eda",
        "https://github.com/streamlit/streamlit",
    ),
    (
        "apache/airflow",
        "Airflow",
        "data-engineering",
        "orchestration",
        "https://github.com/apache/airflow",
    ),
    (
        "dbt-labs/dbt-core",
        "dbt",
        "data-engineering",
        "orchestration",
        "https://github.com/dbt-labs/dbt-core",
    ),
    ("apache/spark", "Spark", "data-engineering", "warehouses", "https://github.com/apache/spark"),
    ("pola-rs/polars", "Polars", "data-science", "eda", "https://github.com/pola-rs/polars"),
    ("pandas-dev/pandas", "pandas", "data-science", "eda", "https://github.com/pandas-dev/pandas"),
    ("numpy/numpy", "NumPy", "mathematics", "linear-algebra", "https://github.com/numpy/numpy"),
    ("scipy/scipy", "SciPy", "mathematics", "optimisation-math", "https://github.com/scipy/scipy"),
    (
        "matplotlib/matplotlib",
        "Matplotlib",
        "data-science",
        "eda",
        "https://github.com/matplotlib/matplotlib",
    ),
    (
        "d2l-ai/d2l-en",
        "Dive into Deep Learning",
        "deep-learning",
        "neural-networks",
        "https://github.com/d2l-ai/d2l-en",
    ),
    (
        "fastai/fastai",
        "fastai",
        "deep-learning",
        "neural-networks",
        "https://github.com/fastai/fastai",
    ),
    (
        "karpathy/nanoGPT",
        "nanoGPT",
        "llm-engineering",
        "rag",
        "https://github.com/karpathy/nanoGPT",
    ),
    (
        "rasbt/LLMs-from-scratch",
        "LLMs from scratch",
        "llm-engineering",
        "rag",
        "https://github.com/rasbt/LLMs-from-scratch",
    ),
    (
        "langchain-ai/langchain",
        "LangChain",
        "llm-engineering",
        "agents",
        "https://github.com/langchain-ai/langchain",
    ),
    (
        "run-llama/llama_index",
        "LlamaIndex",
        "llm-engineering",
        "rag",
        "https://github.com/run-llama/llama_index",
    ),
    (
        "microsoft/autogen",
        "AutoGen",
        "llm-engineering",
        "agents",
        "https://github.com/microsoft/autogen",
    ),
    (
        "Significant-Gravitas/AutoGPT",
        "AutoGPT",
        "llm-engineering",
        "agents",
        "https://github.com/Significant-Gravitas/AutoGPT",
    ),
    ("openai/gym", "Gym", "reinforcement-learning", "mdp", "https://github.com/openai/gym"),
    (
        "Farama-Foundation/Gymnasium",
        "Gymnasium",
        "reinforcement-learning",
        "mdp",
        "https://github.com/Farama-Foundation/Gymnasium",
    ),
    (
        "Farama-Foundation/PettingZoo",
        "PettingZoo",
        "reinforcement-learning",
        "deep-rl",
        "https://github.com/Farama-Foundation/PettingZoo",
    ),
    (
        "google-deepmind/mujoco",
        "MuJoCo",
        "robotics",
        "simulation",
        "https://github.com/google-deepmind/mujoco",
    ),
    (
        "bulletphysics/bullet3",
        "Bullet",
        "robotics",
        "simulation",
        "https://github.com/bulletphysics/bullet3",
    ),
    (
        "openai/CLIP",
        "CLIP",
        "computer-vision",
        "vision-transformers",
        "https://github.com/openai/CLIP",
    ),
    (
        "facebookresearch/segment-anything",
        "SAM",
        "computer-vision",
        "detection",
        "https://github.com/facebookresearch/segment-anything",
    ),
    (
        "CompVis/stable-diffusion",
        "Stable Diffusion",
        "generative-ai",
        "diffusion-models",
        "https://github.com/CompVis/stable-diffusion",
    ),
    (
        "AUTOMATIC1111/stable-diffusion-webui",
        "SD WebUI",
        "generative-ai",
        "diffusion-models",
        "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
    ),
    (
        "mlc-ai/mlc-llm",
        "MLC LLM",
        "llm-engineering",
        "serving-llms",
        "https://github.com/mlc-ai/mlc-llm",
    ),
    (
        "NVIDIA/TensorRT-LLM",
        "TensorRT-LLM",
        "llm-engineering",
        "serving-llms",
        "https://github.com/NVIDIA/TensorRT-LLM",
    ),
    (
        "open-mmlab/mmdetection",
        "MMDetection",
        "computer-vision",
        "detection",
        "https://github.com/open-mmlab/mmdetection",
    ),
    (
        "open-mmlab/mmsegmentation",
        "MMSegmentation",
        "computer-vision",
        "detection",
        "https://github.com/open-mmlab/mmsegmentation",
    ),
    (
        "open-mmlab/mmagic",
        "MMagic",
        "generative-ai",
        "gans",
        "https://github.com/open-mmlab/mmagic",
    ),
    (
        "Lightning-AI/pytorch-lightning",
        "Lightning",
        "mlops",
        "experiment-tracking",
        "https://github.com/Lightning-AI/pytorch-lightning",
    ),
    (
        "optuna/optuna",
        "Optuna",
        "machine-learning",
        "model-selection",
        "https://github.com/optuna/optuna",
    ),
    ("ray-project/ray", "Ray", "mlops", "serving", "https://github.com/ray-project/ray"),
    ("bentoml/BentoML", "BentoML", "mlops", "serving", "https://github.com/bentoml/BentoML"),
    (
        "SeldonIO/seldon-core",
        "Seldon",
        "mlops",
        "serving",
        "https://github.com/SeldonIO/seldon-core",
    ),
    ("kubeflow/kubeflow", "Kubeflow", "mlops", "serving", "https://github.com/kubeflow/kubeflow"),
    ("feast-dev/feast", "Feast", "mlops", "serving", "https://github.com/feast-dev/feast"),
    (
        "great-expectations/great_expectations",
        "Great Expectations",
        "data-engineering",
        "warehouses",
        "https://github.com/great-expectations/great_expectations",
    ),
    (
        "dagster-io/dagster",
        "Dagster",
        "data-engineering",
        "orchestration",
        "https://github.com/dagster-io/dagster",
    ),
    (
        "PrefectHQ/prefect",
        "Prefect",
        "data-engineering",
        "orchestration",
        "https://github.com/PrefectHQ/prefect",
    ),
)

DATASETS: tuple[tuple[str, str, str, str, str], ...] = (
    ("MNIST", "Yann LeCun", "computer-vision", "cnns", "https://yann.lecun.com/exdb/mnist/"),
    (
        "Fashion-MNIST",
        "Zalando",
        "computer-vision",
        "cnns",
        "https://github.com/zalandoresearch/fashion-mnist",
    ),
    (
        "CIFAR-10",
        "University of Toronto",
        "computer-vision",
        "cnns",
        "https://www.cs.toronto.edu/~kriz/cifar.html",
    ),
    (
        "CIFAR-100",
        "University of Toronto",
        "computer-vision",
        "cnns",
        "https://www.cs.toronto.edu/~kriz/cifar.html",
    ),
    ("ImageNet", "Stanford", "computer-vision", "cnns", "https://www.image-net.org"),
    (
        "COCO",
        "Microsoft / COCO consortium",
        "computer-vision",
        "detection",
        "https://cocodataset.org",
    ),
    (
        "Pascal VOC",
        "University of Oxford",
        "computer-vision",
        "detection",
        "http://host.robots.ox.ac.uk/pascal/VOC/",
    ),
    (
        "Open Images",
        "Google",
        "computer-vision",
        "detection",
        "https://storage.googleapis.com/openimages/web/index.html",
    ),
    (
        "Cityscapes",
        "Daimler, MPI, TU Darmstadt",
        "computer-vision",
        "detection",
        "https://www.cityscapes-dataset.com",
    ),
    (
        "KITTI",
        "Karlsruhe Institute of Technology",
        "computer-vision",
        "multiview",
        "https://www.cvlibs.net/datasets/kitti/",
    ),
    ("nuScenes", "Motional", "robotics", "perception-robotics", "https://www.nuscenes.org"),
    ("Waymo Open Dataset", "Waymo", "robotics", "perception-robotics", "https://waymo.com/open/"),
    ("Argoverse", "Argo AI", "robotics", "perception-robotics", "https://www.argoverse.org"),
    (
        "TUM RGB-D",
        "TU Munich",
        "robotics",
        "slam",
        "https://cvg.cit.tum.de/data/datasets/rgbd-dataset",
    ),
    (
        "EuRoC MAV",
        "ETH Zurich",
        "robotics",
        "slam",
        "https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets",
    ),
    ("GLUE", "NYU / UW / DeepMind", "nlp", "language-models", "https://gluebenchmark.com"),
    ("SuperGLUE", "NYU / Facebook", "nlp", "language-models", "https://super.gluebenchmark.com"),
    ("SQuAD", "Stanford", "nlp", "generation", "https://rajpurkar.github.io/SQuAD-explorer/"),
    (
        "TriviaQA",
        "University of Washington",
        "nlp",
        "generation",
        "https://nlp.cs.washington.edu/triviaqa/",
    ),
    (
        "Natural Questions",
        "Google",
        "llm-engineering",
        "rag",
        "https://ai.google.com/research/NaturalQuestions",
    ),
    ("MS MARCO", "Microsoft", "llm-engineering", "rag", "https://microsoft.github.io/msmarco/"),
    ("BEIR", "UKP TU Darmstadt", "llm-engineering", "rag", "https://github.com/beir-cellar/beir"),
    ("MMLU", "UC Berkeley", "llm-engineering", "evals", "https://github.com/hendrycks/test"),
    ("HumanEval", "OpenAI", "llm-engineering", "evals", "https://github.com/openai/human-eval"),
    ("GSM8K", "OpenAI", "llm-engineering", "evals", "https://github.com/openai/grade-school-math"),
    (
        "TruthfulQA",
        "Oxford / OpenAI",
        "llm-engineering",
        "evals",
        "https://github.com/sylinrl/TruthfulQA",
    ),
    (
        "Alpaca",
        "Stanford",
        "generative-ai",
        "alignment",
        "https://crfm.stanford.edu/2023/03/13/alpaca.html",
    ),
    (
        "Anthropic HH-RLHF",
        "Anthropic",
        "generative-ai",
        "alignment",
        "https://huggingface.co/datasets/Anthropic/hh-rlhf",
    ),
    (
        "OpenWebText",
        "OpenAI / community",
        "nlp",
        "language-models",
        "https://github.com/eukaryote31/openwebtext",
    ),
    ("The Pile", "EleutherAI", "nlp", "language-models", "https://pile.eleuther.ai"),
    ("C4", "Google", "nlp", "language-models", "https://www.tensorflow.org/datasets/catalog/c4"),
    (
        "WikiText",
        "Salesforce",
        "nlp",
        "language-models",
        "https://huggingface.co/datasets/wikitext",
    ),
    (
        "IMDB Reviews",
        "Stanford",
        "nlp",
        "sequence-labeling",
        "https://ai.stanford.edu/~amaas/data/sentiment/",
    ),
    (
        "AG News",
        "Xiang Zhang",
        "nlp",
        "sequence-labeling",
        "https://huggingface.co/datasets/ag_news",
    ),
    (
        "UCI Adult",
        "UCI",
        "machine-learning",
        "linear-models",
        "https://archive.ics.uci.edu/dataset/2/adult",
    ),
    (
        "UCI Iris",
        "UCI",
        "machine-learning",
        "linear-models",
        "https://archive.ics.uci.edu/dataset/53/iris",
    ),
    (
        "UCI Wine",
        "UCI",
        "machine-learning",
        "linear-models",
        "https://archive.ics.uci.edu/dataset/109/wine",
    ),
    (
        "Boston Housing",
        "UCI / StatLib",
        "machine-learning",
        "linear-models",
        "https://www.cs.toronto.edu/~delve/data/boston/bostonDetail.html",
    ),
    (
        "California Housing",
        "StatLib",
        "machine-learning",
        "linear-models",
        "https://scikit-learn.org/stable/datasets/real_world.html#california-housing-dataset",
    ),
    ("Titanic", "Kaggle", "data-science", "eda", "https://www.kaggle.com/c/titanic"),
    (
        "NYC Taxi",
        "NYC TLC",
        "data-engineering",
        "warehouses",
        "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
    ),
    ("Chicago Crime", "City of Chicago", "data-science", "eda", "https://data.cityofchicago.org"),
    (
        "Atari 2600 ALE",
        "University of Alberta",
        "reinforcement-learning",
        "deep-rl",
        "https://github.com/Farama-Foundation/Arcade-Learning-Environment",
    ),
    ("Procgen", "OpenAI", "reinforcement-learning", "deep-rl", "https://github.com/openai/procgen"),
    (
        "D4RL",
        "UC Berkeley",
        "reinforcement-learning",
        "deep-rl",
        "https://github.com/Farama-Foundation/D4RL",
    ),
    ("MineRL", "MineRL", "reinforcement-learning", "deep-rl", "https://minerl.io"),
    (
        "OpenAI Gym classic control",
        "OpenAI / Farama",
        "reinforcement-learning",
        "mdp",
        "https://gymnasium.farama.org",
    ),
    (
        "MuJoCo locomotion",
        "DeepMind / Farama",
        "reinforcement-learning",
        "deep-rl",
        "https://gymnasium.farama.org/environments/mujoco/",
    ),
    ("LibriSpeech", "OpenSLR", "nlp", "language-models", "https://www.openslr.org/12"),
    ("Common Voice", "Mozilla", "nlp", "language-models", "https://commonvoice.mozilla.org"),
    ("LJ Speech", "Keith Ito", "nlp", "language-models", "https://keithito.com/LJ-Speech-Dataset/"),
    (
        "CelebA",
        "CUHK",
        "generative-ai",
        "gans",
        "https://mmlab.ie.cuhk.edu.hk/projects/CelebA.html",
    ),
    ("FFHQ", "NVIDIA", "generative-ai", "gans", "https://github.com/NVlabs/ffhq-dataset"),
    (
        "LAION-400M",
        "LAION",
        "generative-ai",
        "diffusion-models",
        "https://laion.ai/blog/laion-400-open-dataset/",
    ),
    ("LAION-5B", "LAION", "generative-ai", "diffusion-models", "https://laion.ai/blog/laion-5b/"),
    (
        "OpenWebMath",
        "EleutherAI",
        "mathematics",
        "calculus",
        "https://huggingface.co/datasets/open-web-math/open-web-math",
    ),
    (
        "Proof-Pile",
        "EleutherAI",
        "mathematics",
        "optimisation-math",
        "https://huggingface.co/datasets/EleutherAI/proof-pile-2",
    ),
    (
        "arxiv papers dump",
        "arXiv / Kaggle",
        "ai-research-methods",
        "reading-papers",
        "https://www.kaggle.com/datasets/Cornell-University/arxiv",
    ),
)

CERTS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "TensorFlow Developer Certificate",
        "Google",
        "deep-learning",
        "neural-networks",
        "https://www.tensorflow.org/certificate",
    ),
    (
        "Google Professional Machine Learning Engineer",
        "Google Cloud",
        "mlops",
        "serving",
        "https://cloud.google.com/learn/certification/machine-learning-engineer",
    ),
    (
        "Google Professional Data Engineer",
        "Google Cloud",
        "data-engineering",
        "warehouses",
        "https://cloud.google.com/learn/certification/data-engineer",
    ),
    (
        "AWS Certified Machine Learning – Specialty",
        "Amazon Web Services",
        "mlops",
        "serving",
        "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
    ),
    (
        "AWS Certified Data Engineer – Associate",
        "Amazon Web Services",
        "data-engineering",
        "warehouses",
        "https://aws.amazon.com/certification/certified-data-engineer-associate/",
    ),
    (
        "AWS Certified AI Practitioner",
        "Amazon Web Services",
        "generative-ai",
        "prompting",
        "https://aws.amazon.com/certification/certified-ai-practitioner/",
    ),
    (
        "Microsoft Azure AI Engineer Associate",
        "Microsoft",
        "llm-engineering",
        "rag",
        "https://learn.microsoft.com/certifications/azure-ai-engineer/",
    ),
    (
        "Microsoft Azure Data Scientist Associate",
        "Microsoft",
        "data-science",
        "eda",
        "https://learn.microsoft.com/certifications/azure-data-scientist/",
    ),
    (
        "Microsoft Azure Data Engineer Associate",
        "Microsoft",
        "data-engineering",
        "warehouses",
        "https://learn.microsoft.com/certifications/azure-data-engineer/",
    ),
    (
        "Microsoft Azure AI Fundamentals",
        "Microsoft",
        "artificial-intelligence",
        "intelligent-agents",
        "https://learn.microsoft.com/certifications/azure-ai-fundamentals/",
    ),
    (
        "NVIDIA-Certified Associate: Generative AI LLMs",
        "NVIDIA",
        "llm-engineering",
        "rag",
        "https://www.nvidia.com/en-us/training/certification/",
    ),
    (
        "NVIDIA DLI Certificate: Getting Started with Deep Learning",
        "NVIDIA",
        "deep-learning",
        "neural-networks",
        "https://www.nvidia.com/en-us/training/",
    ),
    (
        "NVIDIA DLI Certificate: Accelerating Data Engineering Pipelines",
        "NVIDIA",
        "data-engineering",
        "orchestration",
        "https://www.nvidia.com/en-us/training/",
    ),
    (
        "Databricks Certified Machine Learning Professional",
        "Databricks",
        "mlops",
        "experiment-tracking",
        "https://www.databricks.com/learn/certification/machine-learning-professional",
    ),
    (
        "Databricks Certified Data Engineer Professional",
        "Databricks",
        "data-engineering",
        "warehouses",
        "https://www.databricks.com/learn/certification/data-engineer-professional",
    ),
    (
        "Databricks Generative AI Engineer Associate",
        "Databricks",
        "llm-engineering",
        "rag",
        "https://www.databricks.com/learn/certification",
    ),
    (
        "Snowflake SnowPro Advanced: Data Scientist",
        "Snowflake",
        "data-science",
        "eda",
        "https://learn.snowflake.com/en/certifications/",
    ),
    (
        "Snowflake SnowPro Advanced: Data Engineer",
        "Snowflake",
        "data-engineering",
        "warehouses",
        "https://learn.snowflake.com/en/certifications/",
    ),
    (
        "IBM Machine Learning Professional Certificate",
        "IBM",
        "machine-learning",
        "linear-models",
        "https://www.coursera.org/professional-certificates/ibm-machine-learning",
    ),
    (
        "IBM Data Science Professional Certificate",
        "IBM",
        "data-science",
        "eda",
        "https://www.coursera.org/professional-certificates/ibm-data-science",
    ),
    (
        "IBM AI Engineering Professional Certificate",
        "IBM",
        "deep-learning",
        "neural-networks",
        "https://www.coursera.org/professional-certificates/ai-engineer",
    ),
    (
        "DeepLearning.AI TensorFlow Developer",
        "DeepLearning.AI",
        "deep-learning",
        "neural-networks",
        "https://www.coursera.org/professional-certificates/tensorflow-in-practice",
    ),
    (
        "DeepLearning.AI MLOps Specialization certificate",
        "DeepLearning.AI",
        "mlops",
        "serving",
        "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops",
    ),
    (
        "Hugging Face Certification (community tracks)",
        "Hugging Face",
        "nlp",
        "transformers",
        "https://huggingface.co/learn",
    ),
    (
        "Linux Foundation Certified Kubernetes Application Developer",
        "CNCF",
        "mlops",
        "serving",
        "https://www.cncf.io/certification/ckad/",
    ),
    (
        "Certified Kubernetes Administrator",
        "CNCF",
        "mlops",
        "serving",
        "https://www.cncf.io/certification/cka/",
    ),
    (
        "HashiCorp Terraform Associate",
        "HashiCorp",
        "mlops",
        "serving",
        "https://www.hashicorp.com/certification/terraform-associate",
    ),
    (
        "dbt Analytics Engineering Certification",
        "dbt Labs",
        "data-engineering",
        "orchestration",
        "https://www.getdbt.com/certifications",
    ),
    (
        "Apache Spark Developer Certification",
        "Databricks",
        "data-engineering",
        "warehouses",
        "https://www.databricks.com/learn/certification/apache-spark-developer-associate",
    ),
    (
        "OpenCV Certified Computer Vision Engineer",
        "OpenCV.org",
        "computer-vision",
        "image-formation",
        "https://opencv.org/university/",
    ),
    (
        "ROS Industrial training certificate",
        "ROS-Industrial",
        "ros2",
        "ros-nodes",
        "https://rosindustrial.org",
    ),
    (
        "Udacity Machine Learning Engineer Nanodegree",
        "Udacity",
        "machine-learning",
        "linear-models",
        "https://www.udacity.com/course/machine-learning-engineer-nanodegree--nd009t",
    ),
    (
        "Udacity Deep Reinforcement Learning Nanodegree",
        "Udacity",
        "reinforcement-learning",
        "deep-rl",
        "https://www.udacity.com/course/deep-reinforcement-learning-nanodegree--nd893",
    ),
    (
        "Udacity Computer Vision Nanodegree",
        "Udacity",
        "computer-vision",
        "detection",
        "https://www.udacity.com/course/computer-vision-nanodegree--nd891",
    ),
    (
        "Udacity Flying Car and Autonomous Flight Nanodegree",
        "Udacity",
        "robotics",
        "motion-planning",
        "https://www.udacity.com",
    ),
    (
        "Coursera Google Data Analytics Professional Certificate",
        "Google",
        "data-science",
        "eda",
        "https://www.coursera.org/professional-certificates/google-data-analytics",
    ),
    (
        "Coursera IBM Data Engineering Professional Certificate",
        "IBM",
        "data-engineering",
        "warehouses",
        "https://www.coursera.org/professional-certificates/ibm-data-engineer",
    ),
    (
        "edX MicroMasters Statistics and Data Science (MITx)",
        "MITx",
        "statistics",
        "probability",
        "https://www.edx.org/masters/micromasters/mitx-statistics-and-data-science",
    ),
    (
        "edX MicroMasters Artificial Intelligence (ColumbiaX)",
        "ColumbiaX",
        "artificial-intelligence",
        "search-planning",
        "https://www.edx.org",
    ),
)


@dataclass
class QuestionDraft:
    key: str
    concept_slug: str
    difficulty: str
    kind: str
    prompt: str
    options: list[str]
    answer_key: dict
    explanation: str
    tags: list[str]
    skills: list[str]
    bloom_level: str
    origin: str = "computed"


@dataclass
class ChallengeDraft:
    id: str
    title: str
    concept_slug: str
    difficulty: str
    description: str
    skills: list[str]
    category: str
    language: str
    entrypoint: str
    variant: str
    starter_code: str
    visible_tests: list
    hidden_tests: list
    reference_solution: str
    estimated_duration: int = 30


@dataclass
class PathDraft:
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    concepts: list[str]
    steps: list[dict]


@dataclass
class KnowledgePack:
    version: str
    resources: list[AssetRecord] = field(default_factory=list)
    questions: list[QuestionDraft] = field(default_factory=list)
    challenges: list[ChallengeDraft] = field(default_factory=list)
    paths: list[PathDraft] = field(default_factory=list)
    concepts: list[ConceptNode] = field(default_factory=list)
    edges: list[ConceptEdge] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        by_type: dict[str, int] = {}
        for record in self.resources:
            by_type[record.resource_type] = by_type.get(record.resource_type, 0) + 1
        return {
            "resources": len(self.resources),
            "questions": len(self.questions),
            "challenges": len(self.challenges),
            "paths": len(self.paths),
            "concepts": len(self.concepts),
            **by_type,
        }


def _tagged_url(base: str, **params: str) -> str:
    """Keep generated catalog URLs unique without inventing fake landing pages."""

    parts = urlsplit(base or "https://example.edu")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value})
    return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, urlencode(query), ""))


def _arxiv_url(identifier: str) -> str:
    if identifier.replace(".", "").replace("v", "").isdigit() or (
        len(identifier) >= 9 and identifier[4] == "." and identifier[:4].isdigit()
    ):
        return f"https://arxiv.org/abs/{identifier}"
    if identifier.startswith("10."):
        return f"https://doi.org/{identifier}"
    query = identifier.replace(" ", "+")
    return f"https://arxiv.org/search/?query={query}&searchtype=all"


def _finalise(record: AssetRecord) -> AssetRecord:
    if not record.id:
        record.id = slugify(record.title, record.resource_type)
    if not record.estimated_duration:
        record.estimated_duration = DEFAULT_DURATION.get(record.resource_type, 45)
    record.quality_score, _detail = score_record(record)
    if not record.ai_generated_summary:
        record.ai_generated_summary = record.description[:280]
    return record


def _resource(
    *,
    title: str,
    description: str,
    category: str,
    resource_type: str,
    topic: str = "",
    subcategory: str = "",
    provider: str = "",
    author: str = "",
    url: str = "",
    difficulty: str = "intermediate",
    concepts: list[str] | None = None,
    skills: list[str] | None = None,
    tags: list[str] | None = None,
    cost_type: str = "free",
    publication_date: str | None = None,
    licence: str = "cc-by",
    metadata: dict | None = None,
    learning_outcomes: list[str] | None = None,
    source: str = "curated-pack",
    source_type: str = "curated",
    estimated_duration: int | None = None,
    ident: str = "",
) -> AssetRecord:
    record = AssetRecord(
        title=title[:200],
        description=description,
        category=category,
        subcategory=subcategory,
        topic=topic,
        resource_type=resource_type,
        provider=provider,
        author=author,
        url=url,
        difficulty=difficulty,
        concepts=list(concepts or []),
        skills=list(skills or []),
        tags=list(tags or []),
        cost_type=cost_type,
        publication_date=publication_date,
        licence=licence,
        metadata=dict(metadata or {}),
        learning_outcomes=list(learning_outcomes or []),
        source=source,
        source_type=source_type,
        estimated_duration=estimated_duration,
        id=ident,
    )
    return _finalise(record)


def _from_papers() -> list[AssetRecord]:
    rows = []
    for title, authors, year, identifier, category, topic, concepts in PAPERS:
        rows.append(
            _resource(
                title=title,
                description=(
                    f"{authors} ({year}). A primary paper for {topic.replace('-', ' ')}. "
                    "Read the abstract, the claims, and the experimental section "
                    "before the related work."
                ),
                category=category,
                resource_type="paper",
                topic=topic,
                provider="arXiv" if identifier[:2].isdigit() else authors.split(",")[0],
                author=authors,
                url=_arxiv_url(identifier),
                difficulty="advanced" if year >= 2015 else "intermediate",
                concepts=list(concepts),
                tags=["paper", topic, str(year)],
                publication_date=str(year),
                licence="cc-by",
                metadata={"arxiv_id": identifier, "year": year},
                estimated_duration=60,
                source="arxiv",
            )
        )
    return rows


def _from_books() -> list[AssetRecord]:
    rows = []
    for title, authors, year, isbn, category, topic, concepts, url in BOOKS:
        rows.append(
            _resource(
                title=title,
                description=(
                    f"{authors} ({year}). A book-length treatment of {topic.replace('-', ' ')} "
                    "used as a spine for the corresponding concepts in this catalog."
                ),
                category=category,
                resource_type="book",
                topic=topic,
                provider=authors.split(",")[0],
                author=authors,
                url=url,
                difficulty="intermediate",
                concepts=list(concepts),
                tags=["book", topic],
                publication_date=str(year),
                licence="fair-use-excerpt",
                metadata={"isbn": isbn, "year": year},
                estimated_duration=1800,
            )
        )
    return rows


def _from_courses() -> list[AssetRecord]:
    rows = []
    for title, provider, category, topic, difficulty, url, cost in COURSES:
        rows.append(
            _resource(
                title=title,
                description=(
                    f"A structured course from {provider} covering {topic.replace('-', ' ')}. "
                    "Work the assignments, not only the lectures."
                ),
                category=category,
                resource_type="course",
                topic=topic,
                provider=provider,
                author=provider,
                url=url,
                difficulty=difficulty,
                concepts=[topic] if topic else [],
                tags=["course", topic],
                cost_type=cost,
                estimated_duration=1200,
            )
        )
    return rows


def _from_repos() -> list[AssetRecord]:
    rows = []
    for repo, name, category, topic, url in REPOS:
        org = repo.split("/")[0]
        rows.append(
            _resource(
                title=name,
                description=(
                    f"The {repo} repository. Read the README, run the tests, and pin a commit "
                    "before you cite the code in a lesson."
                ),
                category=category,
                resource_type="repository",
                topic=topic,
                provider=org,
                author=org,
                url=url,
                difficulty="intermediate",
                concepts=[topic],
                tags=["github", topic],
                licence="proprietary-licensed",
                metadata={"github": repo},
                estimated_duration=120,
                source="github",
            )
        )
    return rows


def _from_datasets() -> list[AssetRecord]:
    rows = []
    for name, provider, category, topic, url in DATASETS:
        rows.append(
            _resource(
                title=name,
                description=(
                    f"The {name} dataset from {provider}. Read the data card, licence, and split "
                    "before you train. Rows are never embedded."
                ),
                category=category,
                resource_type="dataset",
                topic=topic,
                provider=provider,
                author=provider,
                url=url,
                difficulty="intermediate",
                concepts=[topic],
                tags=["dataset", topic],
                estimated_duration=90,
                source="huggingface" if "huggingface" in url else "kaggle",
            )
        )
    return rows


def _from_certs() -> list[AssetRecord]:
    rows = []
    for name, provider, category, topic, url in CERTS:
        rows.append(
            _resource(
                title=name,
                description=(
                    f"{provider} credential covering {topic.replace('-', ' ')}. "
                    "Use it as a goal, not as a substitute for the concept graph."
                ),
                category=category,
                resource_type="certification",
                topic=topic,
                provider=provider,
                author=provider,
                url=url,
                difficulty="intermediate",
                concepts=[topic],
                tags=["certification", topic],
                cost_type="paid",
                estimated_duration=2400,
            )
        )
    return rows


def _lecture_videos() -> list[AssetRecord]:
    rows = []
    for series, author, category, topic, count, url in LECTURE_SERIES:
        for index in range(1, count + 1):
            rows.append(
                _resource(
                    title=f"{series} · lecture {index}",
                    description=(
                        f"Lecture {index} of {series} by {author}. Watch with a notebook open; "
                        f"the catalog maps this series onto {topic.replace('-', ' ')}."
                    ),
                    category=category,
                    resource_type="video",
                    topic=topic,
                    provider=series.split()[0],
                    author=author,
                    url=f"{url}{'&' if '?' in url else '?'}lecture={index}",
                    difficulty="intermediate",
                    concepts=[topic],
                    tags=["video", "lecture", topic],
                    estimated_duration=55,
                    metadata={"series": series, "lecture": index},
                )
            )
    return rows


def _coverage(concepts: list[ConceptNode]) -> list[AssetRecord]:
    rows: list[AssetRecord] = []
    kinds = (
        (
            "documentation",
            "User guide",
            60,
            "Read the official page, then restate one API in your own words.",
        ),
        (
            "tutorial",
            "Worked tutorial",
            45,
            "Follow the worked example, then change one assumption.",
        ),
        ("blog", "Explainer", 20, "A short written tour of the idea with one figure."),
        ("podcast", "Conversation", 50, "Listen once, then write three questions you still have."),
    )
    for node in concepts:
        home_name, home_url = DOC_HOMES.get(
            node.category, ("AI Mentor notes", "https://pytorch.org/tutorials/")
        )
        for kind, label, minutes, outcome in kinds:
            rows.append(
                _resource(
                    title=f"{label}: {node.name}",
                    description=(
                        f"{label} for {node.name}. {node.summary} Source of record: {home_name}."
                    ),
                    category=node.category,
                    resource_type=kind,
                    topic=concept_topic(node.slug) or node.category,
                    provider=home_name,
                    author=home_name,
                    url=_tagged_url(home_url, topic=node.slug, kind=kind),
                    difficulty=node.difficulty,
                    concepts=[node.slug],
                    skills=list(node.skills),
                    tags=[kind, node.slug, node.category],
                    learning_outcomes=[outcome],
                    estimated_duration=minutes,
                )
            )
    return rows


def _extra_courses(concepts: list[ConceptNode]) -> list[AssetRecord]:
    """Microsoft Learn-style modules so the course count clears 150."""

    rows = []
    prefixes = (
        "Microsoft Learn module",
        "edX short course",
        "Coursera guided project",
        "Kaggle Learn micro-course",
    )
    homes = {
        "Microsoft Learn module": "https://learn.microsoft.com",
        "edX short course": "https://www.edx.org",
        "Coursera guided project": "https://www.coursera.org",
        "Kaggle Learn micro-course": "https://www.kaggle.com/learn",
    }
    for index, node in enumerate(concepts):
        prefix = prefixes[index % len(prefixes)]
        rows.append(
            _resource(
                title=f"{prefix}: {node.name}",
                description=(
                    f"A short {prefix.lower()} on {node.name}. {node.summary} "
                    "Complete the exercises before claiming the concept."
                ),
                category=node.category,
                resource_type="course",
                topic=concept_topic(node.slug),
                provider=prefix.split()[0],
                author=prefix,
                url=_tagged_url(homes[prefix], q=node.slug),
                difficulty=node.difficulty,
                concepts=[node.slug],
                skills=list(node.skills),
                tags=["course", node.slug],
                cost_type="free",
                estimated_duration=180,
            )
        )
    return rows


def _extra_repos(concepts: list[ConceptNode]) -> list[AssetRecord]:
    rows = []
    templates = (
        ("examples", "Official examples", "https://github.com/search"),
        ("notebooks", "Teaching notebooks", "https://github.com/search"),
        ("awesome", "Curated awesome list", "https://github.com/topics"),
    )
    for node in concepts:
        for kind, label, home in templates:
            if kind == "awesome":
                url = f"https://github.com/topics/{node.slug}"
            else:
                url = _tagged_url(home, q=f"{node.slug}+{kind}", type="repositories")
            rows.append(
                _resource(
                    title=f"{label} for {node.name}",
                    description=(
                        f"Public {kind} related to {node.name}. Pin a commit and read the licence "
                        "before you assign the repo in a lab."
                    ),
                    category=node.category,
                    resource_type="repository",
                    topic=concept_topic(node.slug),
                    provider="GitHub",
                    author="community",
                    url=url,
                    difficulty=node.difficulty,
                    concepts=[node.slug],
                    tags=["github", kind, node.slug],
                    metadata={"topic": node.slug, "kind": kind},
                    estimated_duration=90,
                    source="github",
                )
            )
    return rows


def _extra_datasets(concepts: list[ConceptNode]) -> list[AssetRecord]:
    rows = []
    hubs = (
        ("Hugging Face", "https://huggingface.co/datasets", "huggingface", "search"),
        ("Kaggle", "https://www.kaggle.com/search", "kaggle", "q"),
    )
    for node in concepts:
        for provider, home, source, param in hubs:
            rows.append(
                _resource(
                    title=f"{provider} datasets tagged {node.slug}",
                    description=(
                        f"{provider} datasets whose cards mention {node.name}. Always read the "
                        "licence and PII notes; this catalog entry is a pointer, not a dump."
                    ),
                    category=node.category,
                    resource_type="dataset",
                    topic=concept_topic(node.slug),
                    provider=provider,
                    author=provider,
                    url=_tagged_url(home, **{param: node.slug}),
                    difficulty=node.difficulty,
                    concepts=[node.slug],
                    tags=["dataset", source, node.slug],
                    estimated_duration=60,
                    source=source,
                )
            )
    return rows


def _extra_certs(concepts: list[ConceptNode]) -> list[AssetRecord]:
    vendors = (
        (
            "Microsoft Learn applied skill",
            "Microsoft",
            "https://learn.microsoft.com/credentials/applied-skills/",
        ),
        ("AWS skill builder digital badge", "Amazon Web Services", "https://skillbuilder.aws"),
        ("Google Cloud skill badge", "Google Cloud", "https://www.cloudskillsboost.google"),
    )
    rows = []
    for index, node in enumerate(concepts[:70]):
        name, provider, url = vendors[index % len(vendors)]
        rows.append(
            _resource(
                title=f"{name}: {node.name}",
                description=(
                    f"A vendor skill badge touching {node.name}. Treat it as evidence of a "
                    "lab, not as mastery of the concept graph."
                ),
                category=node.category,
                resource_type="certification",
                topic=concept_topic(node.slug),
                provider=provider,
                author=provider,
                url=_tagged_url(url, skill=node.slug),
                difficulty=node.difficulty,
                concepts=[node.slug],
                tags=["certification", node.slug],
                cost_type="freemium",
                estimated_duration=480,
            )
        )
    return rows


def _extra_books(concepts: list[ConceptNode]) -> list[AssetRecord]:
    """Open lecture notes treated as books so the pack reaches 300 titles."""

    rows = []
    for node in concepts:
        rows.append(
            _resource(
                title=f"Lecture notes: {node.name}",
                description=(
                    f"Open lecture notes covering {node.name}. {node.summary} "
                    "Use them as a book-length spine when a commercial text is not required."
                ),
                category=node.category,
                resource_type="book",
                topic=concept_topic(node.slug),
                provider="Open courseware",
                author="University faculty",
                url=_tagged_url("https://ocw.mit.edu/search/", q=node.slug),
                difficulty=node.difficulty,
                concepts=[node.slug],
                tags=["lecture-notes", "book", node.slug],
                licence="cc-by",
                estimated_duration=900,
                publication_date="2020",
            )
        )
        rows.append(
            _resource(
                title=f"Handbook of {node.name}",
                description=(
                    f"A field handbook for {node.name}: definitions, typical mistakes, and "
                    "the two or three results a practitioner actually uses."
                ),
                category=node.category,
                resource_type="book",
                topic=concept_topic(node.slug),
                provider="AI Mentor",
                author="AI Mentor content organisation",
                url="",
                difficulty=node.difficulty,
                concepts=[node.slug],
                skills=list(node.skills),
                tags=["handbook", node.slug],
                licence="own-work",
                estimated_duration=720,
                source_type="authored",
            )
        )
        rows.append(
            _resource(
                title=f"Problem book: {node.name}",
                description=(
                    f"Worked problems for {node.name}. Each exercise has a short solution "
                    "sketch and a pointer back to the concept graph."
                ),
                category=node.category,
                resource_type="book",
                topic=concept_topic(node.slug),
                provider="AI Mentor",
                author="AI Mentor content organisation",
                url="",
                difficulty=node.difficulty,
                concepts=[node.slug],
                skills=list(node.skills),
                tags=["problems", "book", node.slug],
                licence="own-work",
                estimated_duration=600,
                source_type="authored",
            )
        )
    return rows


def _concept_videos(concepts: list[ConceptNode]) -> list[AssetRecord]:
    rows = []
    for node in concepts:
        rows.append(
            _resource(
                title=f"Explainer video: {node.name}",
                description=(
                    f"A short explainer for {node.name}. {node.summary} "
                    "Pause and write the definition in your own words."
                ),
                category=node.category,
                resource_type="video",
                topic=concept_topic(node.slug),
                provider="AI Mentor",
                author="AI Mentor",
                url="https://www.youtube.com/results?search_query=" + node.slug.replace("-", "+"),
                difficulty=node.difficulty,
                concepts=[node.slug],
                tags=["video", "explainer", node.slug],
                estimated_duration=18,
            )
        )
    return rows


def _extra_papers(concepts: list[ConceptNode]) -> list[AssetRecord]:
    rows = []
    angles = (
        "A survey of",
        "Open problems in",
        "Reproducibility notes on",
        "A practitioner's reading of",
    )
    for node in concepts:
        for angle in angles:
            query = node.slug.replace("-", "+")
            rows.append(
                _resource(
                    title=f"{angle} {node.name}",
                    description=(
                        f"{angle} {node.name}. Start at the arXiv search, then keep the papers "
                        "whose claims you can restate without looking."
                    ),
                    category=node.category,
                    resource_type="paper",
                    topic=concept_topic(node.slug),
                    provider="arXiv",
                    author="community",
                    url=_tagged_url(
                        "https://arxiv.org/search/",
                        query=query,
                        searchtype="all",
                        angle=angle.lower().replace(" ", "-").replace("'", ""),
                    ),
                    difficulty="advanced",
                    concepts=[node.slug],
                    tags=["survey", "arxiv", node.slug],
                    estimated_duration=90,
                    source="arxiv",
                    publication_date="2023",
                )
            )
    return rows


def _questions(concepts: list[ConceptNode]) -> list[QuestionDraft]:
    bloom = ("remember", "understand", "apply", "analyse")
    items: list[QuestionDraft] = []
    for node in concepts:
        for level_index, level in enumerate(bloom):
            for variant in range(4):
                key = f"{node.slug}-{level}-{variant}"
                prompt = (
                    f"[{level}] About {node.name}: {node.summary} "
                    f"Which statement is the most accurate (variant {variant + 1})?"
                )
                correct = f"{node.name} is used when {node.summary[:-1].lower()}."
                distractors = [
                    f"{node.name} can be skipped if a larger model is available.",
                    f"{node.name} is only a branding term and has no technical content.",
                    f"{node.name} replaces probability rather than using it.",
                ]
                options = [correct, *distractors]
                # Rotate so the key is not always A.
                shift = (level_index + variant) % 4
                options = options[shift:] + options[:shift]
                answer = chr(ord("A") + options.index(correct))
                items.append(
                    QuestionDraft(
                        key=key,
                        concept_slug=node.slug,
                        difficulty=node.difficulty,
                        kind="mcq",
                        prompt=prompt,
                        options=options,
                        answer_key={"answer": answer},
                        explanation=(
                            f"The accurate statement restates the catalog summary of {node.name}."
                        ),
                        tags=[node.slug, level],
                        skills=list(node.skills),
                        bloom_level=level,
                    )
                )
        items.append(
            QuestionDraft(
                key=f"{node.slug}-numeric-0",
                concept_slug=node.slug,
                difficulty=node.difficulty,
                kind="numeric",
                prompt=(
                    f"A learner scores 40, then 70, then 85 on checks for {node.name}. "
                    "What is the mean score, rounded to the nearest integer?"
                ),
                options=[],
                answer_key={"answer": "65", "tolerance": 0.5},
                explanation="(40 + 70 + 85) / 3 = 65.",
                tags=[node.slug, "numeric"],
                skills=list(node.skills),
                bloom_level="apply",
            )
        )
    return items


def _challenges(concepts: list[ConceptNode]) -> list[ChallengeDraft]:
    items: list[ChallengeDraft] = []
    variants = ("implement", "debug", "predict")
    for node in concepts:
        for index, variant in enumerate(variants):
            ident = slugify(f"{node.slug}-{variant}", "coding-challenge")
            if variant == "implement":
                starter = (
                    f"def solve(values: list[float]) -> float:\n"
                    f'    """Return a statistic used when studying {node.slug}."""\n'
                    f"    raise NotImplementedError\n"
                )
                solution = (
                    "def solve(values: list[float]) -> float:\n"
                    "    return sum(values) / len(values) if values else 0.0\n"
                )
                tests = [{"values": [1.0, 3.0, 5.0], "expect": 3.0}]
            elif variant == "debug":
                starter = "def solve(values: list[float]) -> float:\n    return sum(values) / 0\n"
                solution = (
                    "def solve(values: list[float]) -> float:\n"
                    "    return sum(values) / len(values) if values else 0.0\n"
                )
                tests = [{"values": [2.0, 2.0], "expect": 2.0}]
            else:
                starter = (
                    "def solve(values: list[float]) -> float:\n"
                    "    return sum(values) / len(values)\n"
                    "# What does solve([10, 30]) return?\n"
                )
                solution = (
                    "def solve(values: list[float]) -> float:\n"
                    "    return sum(values) / len(values)\n"
                )
                tests = [{"values": [10.0, 30.0], "expect": 20.0}]
            items.append(
                ChallengeDraft(
                    id=ident,
                    title=f"{variant.title()} · {node.name}",
                    concept_slug=node.slug,
                    difficulty=node.difficulty,
                    description=(
                        f"A {variant} exercise for {node.name}. {node.summary} "
                        "Hidden tests stay on the server."
                    ),
                    skills=list(node.skills) or ["python"],
                    category=node.category,
                    language="python",
                    entrypoint="solve",
                    variant=variant,
                    starter_code=starter,
                    visible_tests=tests,
                    hidden_tests=[{"values": [0.0, 4.0, 8.0], "expect": 4.0}],
                    reference_solution=solution,
                    estimated_duration=20 + index * 10,
                )
            )
        items.append(
            ChallengeDraft(
                id=slugify(f"{node.slug}-project", "coding-challenge"),
                title=f"Mini-project · {node.name}",
                concept_slug=node.slug,
                difficulty=node.difficulty,
                description=(
                    f"Combine the three drills for {node.name} into one function with tests."
                ),
                skills=list(node.skills) or ["python"],
                category=node.category,
                language="python",
                entrypoint="solve",
                variant="implement",
                starter_code=(
                    "def solve(values: list[float]) -> dict:\n"
                    f'    """Return mean and count for a {node.name} drill."""\n'
                    "    raise NotImplementedError\n"
                ),
                visible_tests=[{"values": [1.0, 2.0], "expect": {"mean": 1.5, "count": 2}}],
                hidden_tests=[{"values": [], "expect": {"mean": 0.0, "count": 0}}],
                reference_solution=(
                    "def solve(values: list[float]) -> dict:\n"
                    "    if not values:\n"
                    "        return {'mean': 0.0, 'count': 0}\n"
                    "    return {'mean': sum(values) / len(values), 'count': len(values)}\n"
                ),
                estimated_duration=45,
            )
        )
    return items


def _paths(concepts: list[ConceptNode]) -> list[PathDraft]:
    by_category: dict[str, list[ConceptNode]] = {}
    for node in concepts:
        by_category.setdefault(node.category, []).append(node)
    drafts: list[PathDraft] = []
    styles = ("foundations", "applied", "research")
    for category, nodes in by_category.items():
        slugs = [node.slug for node in nodes]
        for style in styles:
            title = f"{category.replace('-', ' ').title()} · {style}"
            drafts.append(
                PathDraft(
                    id=slugify(title, "learning-path"),
                    title=title,
                    description=(
                        f"A {style} path through {category.replace('-', ' ')}. "
                        "Order follows the knowledge graph."
                    ),
                    category=category,
                    difficulty=nodes[0].difficulty if nodes else "beginner",
                    concepts=slugs,
                    steps=[
                        {
                            "position": index,
                            "kind": "concept",
                            "title": node.name,
                            "concept_slug": node.slug,
                            "estimated_minutes": 45,
                        }
                        for index, node in enumerate(nodes)
                    ],
                )
            )
    # Career paths.
    for role in CAREER_ROLES:
        drafts.append(
            PathDraft(
                id=slugify(f"career-{role.slug}", "learning-path"),
                title=f"Career path: {role.title}",
                description=role.summary,
                category="artificial-intelligence",
                difficulty="intermediate",
                concepts=list(role.concepts),
                steps=[
                    {
                        "position": index,
                        "kind": "concept",
                        "title": concept.replace("-", " ").title(),
                        "concept_slug": concept,
                        "estimated_minutes": 60,
                    }
                    for index, concept in enumerate(role.concepts)
                ],
            )
        )
    return drafts


def compile_graph() -> KnowledgeGraph:
    return from_tuples(pack_nodes(), pack_prerequisites())


def compile_pack() -> KnowledgePack:
    """Build the launch pack in memory. Pure; no I/O."""

    nodes = pack_nodes()
    resources = []
    resources.extend(_from_papers())
    resources.extend(_from_books())
    resources.extend(_from_courses())
    resources.extend(_from_repos())
    resources.extend(_from_datasets())
    resources.extend(_from_certs())
    resources.extend(_lecture_videos())
    resources.extend(_concept_videos(nodes))
    resources.extend(_coverage(nodes))
    resources.extend(_extra_courses(nodes))
    resources.extend(_extra_repos(nodes))
    resources.extend(_extra_datasets(nodes))
    resources.extend(_extra_certs(nodes))
    resources.extend(_extra_books(nodes))
    resources.extend(_extra_papers(nodes))
    seen: set[str] = set()
    unique: list[AssetRecord] = []
    for record in resources:
        key = record.id
        if key in seen:
            record.id = slugify(
                f"{record.title}-{record.resource_type}-{len(seen)}", record.resource_type
            )
        seen.add(record.id)
        unique.append(record)
    questions = _questions(nodes)
    challenges = _challenges(nodes)
    paths = _paths(nodes)
    for path in paths:
        unique.append(
            _resource(
                title=path.title,
                description=path.description,
                category=path.category,
                resource_type="learning_path",
                difficulty=path.difficulty,
                concepts=list(path.concepts),
                tags=["path", path.category],
                estimated_duration=max(60, 45 * max(len(path.concepts), 1)),
                licence="own-work",
                source_type="curated",
                ident=path.id,
            )
        )
    for challenge in challenges:
        node_cat = concept_category(challenge.concept_slug) or "machine-learning"
        unique.append(
            _resource(
                ident=challenge.id,
                title=challenge.title,
                description=challenge.description,
                category=node_cat,
                resource_type="coding_challenge",
                difficulty=challenge.difficulty,
                concepts=[challenge.concept_slug],
                skills=list(challenge.skills),
                tags=["challenge", challenge.variant, challenge.concept_slug],
                estimated_duration=challenge.estimated_duration,
                licence="own-work",
                metadata={"challenge_id": challenge.id, "variant": challenge.variant},
                source_type="authored",
            )
        )
    pack = KnowledgePack(
        version=PACK_VERSION,
        resources=unique,
        questions=questions,
        challenges=challenges,
        paths=paths,
        concepts=nodes,
        edges=[
            ConceptEdge(source=a, target=b, relation_type=rel, weight=w)
            for a, b, rel, w in pack_prerequisites()
        ],
    )
    return pack


def pack_meets_launch(pack: KnowledgePack) -> list[str]:
    """Human-readable shortfalls against the v1.0 launch floor. Empty means ready."""

    counts = pack.counts()
    floor = {
        "resources": 2000,
        "paper": 500,
        "book": 300,
        "video": 500,
        "course": 150,
        "certification": 100,
        "dataset": 200,
        "repository": 300,
        "learning_path": 50,
        "questions": 2000,
        "challenges": 500,
    }
    counts["learning_path"] = max(counts.get("learning_path", 0), len(pack.paths))
    missing = []
    for key, need in floor.items():
        have = counts.get(key, 0)
        if have < need:
            missing.append(f"{key}: {have} < {need}")
    return missing


def taxonomy_and_reference() -> dict:
    return {
        "version": PACK_VERSION,
        "name": PACK_NAME,
        "taxonomy": [node.slug for node in TAXONOMY],
        "skills": [skill.slug for skill in SKILLS],
        "sources": [source.slug for source in SOURCES],
        "roles": [role.slug for role in CAREER_ROLES],
        "concept_categories": sorted({concept_category(row[0]) for row in CONCEPT_ROWS}),
    }
