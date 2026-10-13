"""Knowledge Pack concept graph. Extends the v1 catalog without renaming its slugs.

Each tuple is (slug, name, category, topic, difficulty, prerequisites, skills, summary).
Edges are `prerequisite_of` from each prerequisite to the concept.
"""

from __future__ import annotations

from app.domain.knowledge.graph import ConceptNode

# fmt: off
CONCEPT_ROWS: tuple[tuple[str, str, str, str, str, tuple[str, ...], tuple[str, ...], str], ...] = (
    ("ai-fundamentals", "AI Fundamentals", "artificial-intelligence", "intelligent-agents", "beginner", (), ("communication",), "Agents, data, and the difference between a rule and a learned policy."),
    ("intelligent-agents", "Intelligent agents", "artificial-intelligence", "intelligent-agents", "beginner", ("ai-fundamentals",), ("communication",), "PEAS descriptors, rationality, and environment types."),
    ("search-planning", "Search and planning", "artificial-intelligence", "search-planning", "intermediate", ("intelligent-agents",), ("python",), "Uninformed, informed, and adversarial search."),
    ("knowledge-representation", "Knowledge representation", "artificial-intelligence", "knowledge-representation", "intermediate", ("ai-fundamentals",), ("communication",), "Logic, ontologies, and representing uncertainty."),
    ("ai-ethics", "AI ethics", "artificial-intelligence", "ai-ethics", "beginner", ("ai-fundamentals",), ("communication",), "Fairness, safety, dual use, and accountability."),
    ("ai-history", "History of AI", "artificial-intelligence", "ai-history", "beginner", ("ai-fundamentals",), ("paper-reading",), "Symbolic, statistical, and foundation-model eras."),
    ("python-language", "Python", "programming", "python-language", "beginner", (), ("python", "git"), "Syntax, types, packaging, and tests before a training loop."),
    ("python-for-ml", "Python for machine learning", "machine-learning", "linear-models", "beginner", ("python-language",), ("python", "numpy", "git"), "Functions, arrays, and tests before a training loop."),
    ("probability", "Probability", "statistics", "probability", "beginner", ("ai-fundamentals",), ("probability",), "Random variables, expectation, and common families."),
    ("linear-algebra", "Linear algebra", "mathematics", "linear-algebra", "beginner", ("ai-fundamentals",), ("linear-algebra",), "Vectors, matrices, eigenvalues, and projections."),
    ("calculus", "Calculus for learning", "mathematics", "calculus", "beginner", ("linear-algebra",), ("calculus",), "Gradients, Jacobians, and Taylor expansions of a loss."),
    ("optimisation-math", "Mathematical optimisation", "mathematics", "optimisation-math", "intermediate", ("calculus",), ("optimisation",), "Convexity, Lagrange multipliers, and first-order methods."),
    ("estimation", "Statistical estimation", "statistics", "estimation", "intermediate", ("probability",), ("statistics",), "MLE, MAP, and the bootstrap."),
    ("hypothesis-testing", "Hypothesis testing", "statistics", "hypothesis-testing", "intermediate", ("estimation",), ("statistics", "experimental-design"), "p-values, power, and multiple testing."),
    ("eda", "Exploratory data analysis", "data-science", "eda", "beginner", ("python-for-ml", "probability"), ("pandas", "sql"), "Distributions, missingness, and plots that change a question."),
    ("feature-engineering", "Feature engineering", "data-science", "feature-engineering", "intermediate", ("eda",), ("pandas", "scikit-learn"), "Transforms that make a linear model honest."),
    ("experimentation", "Experimentation", "data-science", "experimentation", "intermediate", ("hypothesis-testing",), ("statistics", "experimental-design"), "A/B tests and a sketch of causal identification."),
    ("supervised-learning", "Supervised learning", "machine-learning", "linear-models", "beginner", ("probability", "linear-algebra", "python-for-ml"), ("scikit-learn", "statistics"), "Fit a labelled target and say what the loss means."),
    ("linear-models", "Linear models", "machine-learning", "linear-models", "beginner", ("supervised-learning",), ("scikit-learn", "linear-algebra"), "Least squares, logistic regression, and regularisation."),
    ("tree-ensembles", "Trees and ensembles", "machine-learning", "tree-ensembles", "intermediate", ("supervised-learning",), ("scikit-learn",), "Decision trees, random forests, and boosting."),
    ("kernel-methods", "Kernel methods", "machine-learning", "kernel-methods", "advanced", ("linear-models",), ("scikit-learn", "linear-algebra"), "SVMs and the kernel trick."),
    ("clustering", "Clustering", "machine-learning", "clustering", "intermediate", ("linear-algebra", "probability"), ("scikit-learn",), "k-means, GMM, and when a cluster is a story."),
    ("dimensionality-reduction", "Dimensionality reduction", "machine-learning", "dimensionality-reduction", "intermediate", ("linear-algebra",), ("scikit-learn", "linear-algebra"), "PCA, t-SNE, UMAP, and what they preserve."),
    ("model-selection", "Model selection", "machine-learning", "model-selection", "intermediate", ("supervised-learning",), ("scikit-learn", "statistics"), "Cross-validation, calibration, and leakage."),
    ("warehouses", "Warehouses and lakes", "data-engineering", "warehouses", "intermediate", ("eda",), ("sql", "spark"), "Batch storage of analytic data."),
    ("streaming", "Streaming systems", "data-engineering", "streaming", "advanced", ("warehouses",), ("spark",), "Event time, watermarks, and exactly-once myths."),
    ("orchestration", "Pipeline orchestration", "data-engineering", "orchestration", "intermediate", ("warehouses",), ("airflow", "python"), "Airflow, Dagster, and dbt as contracts."),
    ("neural-networks", "Neural networks", "deep-learning", "neural-networks", "intermediate", ("supervised-learning", "calculus"), ("pytorch", "optimisation"), "MLPs, activations, and a loss surface."),
    ("backpropagation", "Backpropagation", "deep-learning", "backpropagation", "intermediate", ("neural-networks",), ("pytorch", "calculus"), "Reverse-mode autodiff."),
    ("optimisation", "Deep learning optimisation", "deep-learning", "optimisation", "intermediate", ("backpropagation",), ("pytorch", "optimisation"), "SGD, Adam, batch norm, and regularisation."),
    ("cnns", "Convolutional networks", "deep-learning", "cnns", "intermediate", ("neural-networks",), ("pytorch", "cnn-design"), "Conv, pooling, and residual connections."),
    ("rnns", "Recurrent networks", "deep-learning", "rnns", "intermediate", ("neural-networks",), ("pytorch",), "RNN, LSTM, GRU, and why they stall."),
    ("transformers", "Transformers", "deep-learning", "transformers", "advanced", ("neural-networks", "rnns"), ("pytorch", "transformers"), "Attention, encoder-decoder, and scaling."),
    ("agent-environment", "Agent and environment", "reinforcement-learning", "mdp", "beginner", ("ai-fundamentals",), ("mdp-reasoning",), "Actions, observations, and reward from interaction."),
    ("mdp", "Markov decision processes", "reinforcement-learning", "mdp", "intermediate", ("agent-environment", "probability"), ("mdp-reasoning", "probability"), "States, actions, rewards, and discounting."),
    ("bellman", "Bellman equations", "reinforcement-learning", "bellman-equation", "intermediate", ("mdp",), ("bellman", "mdp-reasoning"), "Expectation and optimality operators."),
    ("dynamic-programming", "Dynamic programming", "reinforcement-learning", "dynamic-programming-rl", "intermediate", ("bellman",), ("bellman",), "Policy iteration and value iteration."),
    ("monte-carlo", "Monte Carlo methods", "reinforcement-learning", "q-learning", "intermediate", ("bellman",), ("td-learning",), "Learning values from complete returns."),
    ("temporal-difference", "Temporal-difference learning", "reinforcement-learning", "q-learning", "intermediate", ("monte-carlo",), ("td-learning",), "Bootstrapped value updates."),
    ("q-learning", "Q-learning", "reinforcement-learning", "q-learning", "intermediate", ("temporal-difference",), ("td-learning", "mdp-reasoning"), "Off-policy TD control."),
    ("dqn", "Deep Q-networks", "reinforcement-learning", "deep-rl", "advanced", ("q-learning", "neural-networks"), ("deep-rl", "pytorch"), "Function approximation and replay."),
    ("policy-gradient", "Policy gradients", "reinforcement-learning", "policy-gradients", "advanced", ("mdp", "calculus"), ("policy-optimisation",), "REINFORCE and actor-critic."),
    ("ppo", "Proximal policy optimisation", "reinforcement-learning", "policy-gradients", "advanced", ("policy-gradient",), ("policy-optimisation", "deep-rl"), "Clipped surrogate objectives."),
    ("sac", "Soft actor-critic", "reinforcement-learning", "policy-gradients", "advanced", ("policy-gradient", "q-learning"), ("policy-optimisation", "deep-rl"), "Maximum-entropy off-policy control."),
    ("multi-agent", "Multi-agent RL", "reinforcement-learning", "deep-rl", "expert", ("ppo",), ("deep-rl",), "Non-stationarity when several policies learn."),
    ("gans", "Generative adversarial networks", "generative-ai", "gans", "advanced", ("neural-networks",), ("pytorch",), "Adversarial training of a generator."),
    ("vaes", "Variational autoencoders", "generative-ai", "vaes", "advanced", ("neural-networks", "probability"), ("pytorch", "probability"), "ELBO and latent variable models."),
    ("diffusion-models", "Diffusion models", "generative-ai", "diffusion-models", "advanced", ("neural-networks", "probability"), ("pytorch",), "Score matching and denoising."),
    ("prompting", "Prompting", "generative-ai", "prompting", "beginner", ("ai-fundamentals",), ("prompt-engineering",), "Instruction following and in-context learning."),
    ("alignment", "Alignment", "generative-ai", "alignment", "advanced", ("prompting", "policy-gradient"), ("evals", "experimental-design"), "RLHF, constitutional AI, and evals that bite."),
    ("robotics", "Robotics", "robotics", "kinematics", "beginner", ("linear-algebra",), ("kinematics",), "Sensing, planning, and acting in the physical world."),
    ("kinematics", "Kinematics", "robotics", "kinematics", "intermediate", ("robotics", "linear-algebra"), ("kinematics",), "Forward and inverse kinematics."),
    ("control-theory", "Feedback control", "robotics", "control-theory", "intermediate", ("calculus", "robotics"), ("control",), "PID, LQR, and trajectory tracking."),
    ("slam", "SLAM", "robotics", "slam", "advanced", ("probability", "linear-algebra", "robotics"), ("slam",), "Simultaneous localisation and mapping."),
    ("motion-planning", "Motion planning", "robotics", "motion-planning", "advanced", ("kinematics",), ("kinematics",), "Sampling and optimisation-based planners."),
    ("perception-robotics", "Robot perception", "robotics", "perception-robotics", "intermediate", ("robotics", "cnns"), ("opencv",), "Sensors to state estimates."),
    ("ros2", "ROS 2", "ros2", "ros-nodes", "beginner", ("python-for-ml",), ("ros2", "python"), "Nodes, topics, services, and actions."),
    ("ros-nodes", "ROS 2 nodes and topics", "ros2", "ros-nodes", "beginner", ("ros2",), ("ros2",), "Publishers, subscribers, and QoS."),
    ("ros-launch", "ROS 2 launch", "ros2", "ros-launch", "intermediate", ("ros-nodes",), ("ros2",), "Bring-up of a robot system."),
    ("nav2", "Nav2", "ros2", "nav2", "advanced", ("ros-launch", "motion-planning"), ("ros2", "slam"), "The ROS 2 navigation stack."),
    ("navigation", "Robot navigation", "robotics", "motion-planning", "advanced", ("slam", "control-theory"), ("slam", "control"), "From a map to a trajectory a controller can track."),
    ("rl-robotics", "RL for robotics", "reinforcement-learning", "deep-rl", "expert", ("ppo", "robotics"), ("deep-rl", "control"), "Sim-to-real and safety constraints."),
    ("computer-vision", "Computer vision", "computer-vision", "image-formation", "beginner", ("linear-algebra",), ("opencv",), "Images to structure."),
    ("image-formation", "Image formation", "computer-vision", "image-formation", "beginner", ("computer-vision",), ("opencv",), "Cameras, colour, and filtering."),
    ("multiview", "Multiple-view geometry", "computer-vision", "multiview", "advanced", ("image-formation", "linear-algebra"), ("opencv", "linear-algebra"), "Stereo, homography, and structure from motion."),
    ("detection", "Detection and segmentation", "computer-vision", "detection", "advanced", ("cnns", "computer-vision"), ("detection", "cnn-design"), "Boxes, masks, and tracking."),
    ("vision-transformers", "Vision transformers", "computer-vision", "vision-transformers", "advanced", ("transformers", "cnns"), ("transformers", "pytorch"), "ViT, CLIP, and multimodal encoders."),
    ("tokenization", "Tokenization", "nlp", "tokenization", "beginner", ("python-for-ml",), ("huggingface", "language-modeling"), "Words, subwords, and BPE."),
    ("language-models", "Language models", "nlp", "language-models", "intermediate", ("probability", "tokenization"), ("language-modeling",), "n-grams to neural LMs."),
    ("representation-nlp", "Linguistic representations", "nlp", "representation-nlp", "intermediate", ("language-models",), ("huggingface",), "Word2Vec, BERT, and sentence embeddings."),
    ("sequence-labeling", "Sequence labelling", "nlp", "sequence-labeling", "intermediate", ("representation-nlp",), ("huggingface",), "NER, parsing, and tagging."),
    ("generation", "Text generation", "nlp", "generation", "advanced", ("language-models", "transformers"), ("language-modeling", "evals"), "Decoding, evaluation, and hallucination."),
    ("llm-engineering", "LLM engineering", "llm-engineering", "rag", "intermediate", ("transformers", "prompting"), ("prompt-engineering", "evals"), "Products on foundation models."),
    ("rag", "Retrieval-augmented generation", "llm-engineering", "rag", "intermediate", ("llm-engineering", "representation-nlp"), ("rag-systems", "retrieval"), "Ground answers in a corpus."),
    ("agents", "LLM agents", "llm-engineering", "agents", "advanced", ("rag",), ("prompt-engineering",), "Planning, tools, and memory."),
    ("evals", "LLM evals", "llm-engineering", "evals", "intermediate", ("llm-engineering",), ("evals", "experimental-design"), "Task suites, judges, and regression gates."),
    ("serving-llms", "Serving LLMs", "llm-engineering", "serving-llms", "advanced", ("llm-engineering",), ("model-serving", "docker"), "Quantisation, batching, and latency."),
    ("experiment-tracking", "Experiment tracking", "mlops", "experiment-tracking", "beginner", ("supervised-learning",), ("git", "python"), "Runs, artefacts, and lineage."),
    ("serving", "Model serving", "mlops", "serving", "intermediate", ("experiment-tracking",), ("model-serving", "docker"), "Batch, online, and streaming inference."),
    ("monitoring", "ML monitoring", "mlops", "monitoring", "intermediate", ("serving",), ("observability",), "Drift, quality, and incident response."),
    ("feature-stores", "Feature stores", "mlops", "serving", "advanced", ("feature-engineering", "serving"), ("feature-stores",), "Training-time features served online."),
    ("research-methods", "AI research methods", "ai-research-methods", "experimental-design", "intermediate", ("supervised-learning",), ("experimental-design", "paper-reading"), "Baselines, ablations, and seeds."),
    ("experimental-design", "Experimental design", "ai-research-methods", "experimental-design", "intermediate", ("research-methods", "hypothesis-testing"), ("experimental-design",), "Fair comparisons and leakage control."),
    ("reproducibility", "Reproducibility", "ai-research-methods", "reproducibility", "intermediate", ("research-methods",), ("git", "experimental-design"), "Code, data, seeds, and claims."),
    ("reading-papers", "Reading papers", "ai-research-methods", "reading-papers", "beginner", ("ai-fundamentals",), ("paper-reading",), "Extracting a contribution from a PDF."),
    ("paper-structure", "Paper structure", "scientific-writing", "paper-structure", "beginner", ("reading-papers",), ("scientific-writing",), "IMRaD, related work, and figures."),
    ("citation-practice", "Citation practice", "scientific-writing", "citation-practice", "beginner", ("paper-structure",), ("scientific-writing",), "Prior work and academic integrity."),
    ("peer-review", "Peer review", "scientific-writing", "peer-review", "intermediate", ("paper-structure", "research-methods"), ("scientific-writing",), "Giving and receiving technical review."),
    ("information-theory", "Information theory", "mathematics", "optimisation-math", "advanced", ("probability",), ("probability",), "Entropy, KL, and why cross-entropy is a loss."),
    ("bayesian-inference", "Bayesian inference", "statistics", "estimation", "advanced", ("estimation",), ("statistics", "probability"), "Priors, posteriors, and predictive checks."),
    ("causal-inference", "Causal inference", "statistics", "hypothesis-testing", "advanced", ("experimentation",), ("statistics", "experimental-design"), "DAGs, identification, and unconfoundedness."),
    ("graph-ml", "Graph machine learning", "machine-learning", "kernel-methods", "advanced", ("neural-networks",), ("pytorch",), "Message passing on relational data."),
    ("self-supervised", "Self-supervised learning", "deep-learning", "transformers", "advanced", ("cnns", "transformers"), ("pytorch",), "Pretext tasks and contrastive learning."),
    ("few-shot", "Few-shot learning", "deep-learning", "transformers", "advanced", ("transformers",), ("pytorch",), "Adapt with few labelled examples."),
    ("meta-learning", "Meta-learning", "deep-learning", "optimisation", "expert", ("optimisation", "few-shot"), ("pytorch", "optimisation"), "Learning to learn."),
    ("offline-rl", "Offline reinforcement learning", "reinforcement-learning", "deep-rl", "expert", ("dqn", "q-learning"), ("deep-rl",), "Learning from a fixed dataset of decisions."),
    ("imitation-learning", "Imitation learning", "reinforcement-learning", "deep-rl", "advanced", ("mdp", "supervised-learning"), ("deep-rl",), "Policies from demonstrations."),
    ("model-based-rl", "Model-based RL", "reinforcement-learning", "deep-rl", "expert", ("mdp", "neural-networks"), ("deep-rl",), "Learn the transition, then plan."),
    ("safety-rl", "Safe RL", "reinforcement-learning", "deep-rl", "expert", ("ppo", "ai-ethics"), ("deep-rl",), "Constraints, shielding, and conservative updates."),
    ("multimodal", "Multimodal models", "generative-ai", "prompting", "advanced", ("vision-transformers", "transformers"), ("transformers",), "Shared spaces for image and text."),
    ("lora", "Parameter-efficient fine-tuning", "llm-engineering", "serving-llms", "advanced", ("transformers",), ("huggingface", "pytorch"), "LoRA, adapters, and prompt tuning."),
    ("token-engineering", "Context engineering", "llm-engineering", "rag", "intermediate", ("rag",), ("rag-systems", "prompt-engineering"), "What goes in the window, and in what order."),
    ("guardrails", "Guardrails", "llm-engineering", "evals", "intermediate", ("evals", "ai-ethics"), ("evals",), "Policies around a stochastic generator."),
    ("distributed-training", "Distributed training", "mlops", "experiment-tracking", "advanced", ("optimisation",), ("pytorch", "docker"), "Data parallel, FSDP, and communication."),
    ("feature-pipelines", "Feature pipelines", "data-engineering", "orchestration", "intermediate", ("feature-engineering", "orchestration"), ("airflow", "pandas"), "Point-in-time correct training data."),
    ("data-quality", "Data quality", "data-engineering", "warehouses", "intermediate", ("eda",), ("sql", "pandas"), "Contracts, tests, and fresh data."),
    ("time-series", "Time series", "data-science", "feature-engineering", "intermediate", ("supervised-learning", "probability"), ("pandas", "statistics"), "Forecasting without leaking the future."),
    ("recommenders", "Recommender systems", "machine-learning", "linear-models", "intermediate", ("supervised-learning",), ("python", "statistics"), "Collaborative filtering and ranking metrics."),
    ("speech", "Speech processing", "nlp", "language-models", "advanced", ("rnns", "cnns"), ("pytorch",), "ASR, TTS, and spectrograms."),
    ("3d-vision", "3D vision", "computer-vision", "3d-vision", "expert", ("multiview", "cnns"), ("opencv", "pytorch"), "Depth, NeRF, and Gaussian splatting."),
    ("control-ml", "Learning-based control", "robotics", "control-theory", "expert", ("control-theory", "ppo"), ("control", "deep-rl"), "Policies that respect a plant."),
    ("simulation", "Robot simulation", "robotics", "kinematics", "intermediate", ("robotics",), ("python", "ros2"), "Gazebo, Isaac, and domain randomisation."),
    ("tf2", "ROS 2 tf2", "ros2", "ros-nodes", "intermediate", ("ros-nodes", "kinematics"), ("ros2",), "Frames, time, and transforms."),
    ("lifecycle", "ROS 2 managed nodes", "ros2", "ros-launch", "intermediate", ("ros-launch",), ("ros2",), "Configure, activate, deactivate."),
    ("hardware-interfaces", "Hardware interfaces", "ros2", "ros-launch", "advanced", ("lifecycle",), ("ros2", "control"), "ros2_control and real I/O."),
    ("scientific-python", "Scientific Python", "data-science", "eda", "beginner", ("python-for-ml",), ("numpy", "pandas"), "NumPy, SciPy, and matplotlib as a lab bench."),
    ("sql", "SQL for analysis", "data-engineering", "warehouses", "beginner", ("eda",), ("sql",), "Joins, windows, and grain."),
    ("docker", "Containers for ML", "mlops", "experiment-tracking", "beginner", ("python-for-ml",), ("docker",), "A runtime another machine can run."),
    ("kubernetes", "Kubernetes for ML", "mlops", "serving", "advanced", ("docker", "serving"), ("kubernetes", "docker"), "Jobs, services, and rollouts."),
    ("gpu-computing", "GPU computing", "deep-learning", "optimisation", "advanced", ("neural-networks",), ("pytorch",), "Kernels, occupancy, and mixed precision."),
    ("numerical-stability", "Numerical stability", "mathematics", "optimisation-math", "advanced", ("linear-algebra", "optimisation-math"), ("linear-algebra",), "Conditioning, overflow, and log-sum-exp."),
    ("measure-theory-lite", "Measure-theoretic probability", "mathematics", "calculus", "expert", ("probability", "calculus"), ("probability",), "Enough measure to read a theory paper."),
    ("bandits", "Multi-armed bandits", "reinforcement-learning", "mdp", "intermediate", ("probability",), ("statistics", "mdp-reasoning"), "Exploration without a full MDP."),
    ("irl", "Inverse reinforcement learning", "reinforcement-learning", "deep-rl", "expert", ("imitation-learning",), ("deep-rl",), "Recover a reward from demonstrations."),
    ("world-models", "World models", "reinforcement-learning", "deep-rl", "expert", ("model-based-rl", "vaes"), ("deep-rl",), "Learn a compact dynamics, then dream."),
    ("constitutional-ai", "Constitutional AI", "generative-ai", "alignment", "advanced", ("alignment",), ("evals",), "Critique and revise against written principles."),
    ("tool-use", "Tool use", "llm-engineering", "agents", "advanced", ("agents",), ("prompt-engineering",), "Function calling that is allowed to fail."),
    ("prompt-injection", "Prompt injection", "llm-engineering", "evals", "intermediate", ("guardrails",), ("evals", "ai-ethics"), "Untrusted text that tries to become instructions."),
    ("dataset-design", "Dataset design", "ai-research-methods", "experimental-design", "intermediate", ("eda", "research-methods"), ("experimental-design",), "What is in the split, and why."),
    ("ablation", "Ablation studies", "ai-research-methods", "experimental-design", "intermediate", ("experimental-design",), ("experimental-design",), "Remove a piece and measure the drop."),
    ("error-analysis", "Error analysis", "ai-research-methods", "reading-papers", "intermediate", ("model-selection",), ("paper-reading",), "The failures that a mean metric hides."),
    ("grant-writing", "Research communication", "scientific-writing", "paper-structure", "intermediate", ("paper-structure",), ("scientific-writing", "communication"), "Proposals, talks, and a claim a funder can test."),
    ("opencv", "OpenCV", "computer-vision", "opencv", "beginner", ("computer-vision",), ("opencv", "python"), "Cameras, filters, contours, and a first calibrated image."),
    ("yolo", "YOLO", "computer-vision", "yolo", "intermediate", ("detection",), ("detection", "pytorch"), "Single-shot boxes with a real-time budget."),
    ("detr", "DETR", "computer-vision", "detr", "advanced", ("detection", "transformers"), ("detection", "transformers"), "Detection as set prediction, without anchors."),
    ("segmentation", "Image segmentation", "computer-vision", "segmentation", "intermediate", ("cnns", "computer-vision"), ("detection", "cnn-design"), "Pixels to classes, instances, and panoptic maps."),
    ("stereo-vision", "Stereo vision", "computer-vision", "stereo-vision", "intermediate", ("image-formation", "linear-algebra"), ("opencv", "linear-algebra"), "Two views, disparity, and a depth map you can check."),
    ("lidar", "LiDAR", "computer-vision", "lidar", "advanced", ("computer-vision", "probability"), ("opencv", "detection"), "Range returns to objects, lanes, and maps."),
    ("nlp-fundamentals", "NLP fundamentals", "nlp", "nlp-survey", "beginner", ("python-for-ml",), ("huggingface", "communication"), "What language tasks are, before you fine-tune a transformer."),
    ("embeddings", "Embeddings", "nlp", "embeddings", "intermediate", ("tokenization", "nlp-fundamentals"), ("huggingface", "language-modeling"), "Vectors that put similar text near similar text."),
    ("federated-learning", "Federated learning", "federated-learning", "fl-intro", "intermediate", ("supervised-learning",), ("federated-learning", "python"), "Train across clients without sending the raw rows."),
    ("fedavg", "FedAvg", "federated-learning", "fedavg", "intermediate", ("federated-learning",), ("federated-learning", "pytorch"), "Average client updates on a server, then broadcast the new weights."),
    ("fedprox", "FedProx", "federated-learning", "fedprox", "advanced", ("fedavg",), ("federated-learning", "optimisation"), "A proximal term so heterogeneous clients do not drift apart."),
    ("differential-privacy", "Differential privacy", "federated-learning", "differential-privacy", "advanced", ("probability", "federated-learning"), ("differential-privacy", "statistics"), "A privacy budget on what a trained model can reveal about one row."),
    ("edge-ai", "Edge AI", "federated-learning", "edge-ai", "intermediate", ("neural-networks", "federated-learning"), ("federated-learning", "docker"), "Inference and on-device training next to the sensor."),
    ("cpp", "C++", "programming", "cpp", "intermediate", ("python-language",), ("cpp", "git"), "Types, memory, and the subset used on robots."),
    ("ros2-cpp", "ROS 2 C++", "programming", "ros2-cpp", "intermediate", ("ros2", "cpp"), ("ros2", "cpp"), "rclcpp nodes, executors, parameters, and lifecycle."),
    ("software-engineering", "Software engineering", "programming", "software-engineering", "intermediate", ("python-language",), ("software-engineering", "git"), "Design, tests, reviews, and a change you can revert."),
    ("matlab", "MATLAB", "modelling-simulation", "matlab", "beginner", ("linear-algebra",), ("matlab", "linear-algebra"), "Arrays, plots, and a numerical experiment you can re-run."),
    ("simulink", "Simulink", "modelling-simulation", "simulink", "intermediate", ("matlab", "calculus"), ("matlab", "control"), "Block diagrams of continuous and discrete plants."),
    ("gazebo", "Gazebo", "modelling-simulation", "gazebo", "intermediate", ("simulation",), ("simulation-tools", "ros2"), "Rigid-body robots, sensors, and a ROS 2 bring-up in simulation."),
    ("isaac-sim", "Isaac Sim", "modelling-simulation", "isaac-sim", "advanced", ("simulation",), ("simulation-tools", "python"), "GPU-native scenes, synthetic data, and domain randomisation."),
    ("mujoco", "MuJoCo", "modelling-simulation", "mujoco", "advanced", ("simulation", "control-theory"), ("simulation-tools", "control"), "Contact-rich physics for control and RL."),
    ("carla", "CARLA", "modelling-simulation", "carla", "advanced", ("simulation", "computer-vision"), ("simulation-tools", "python"), "Urban driving: sensors, traffic, and a closed loop."),
    ("airsim", "AirSim", "modelling-simulation", "airsim", "advanced", ("simulation",), ("simulation-tools", "cpp"), "Aerial and ground vehicles in Unreal scenes."),
    ("webots", "Webots", "modelling-simulation", "webots", "intermediate", ("simulation",), ("simulation-tools", "python"), "Cross-platform robot scenes with controllers you can step."),
    ("coppeliasim", "CoppeliaSim", "modelling-simulation", "coppeliasim", "intermediate", ("simulation",), ("simulation-tools", "python"), "Scenes, child scripts, and inverse kinematics."),
    ("digital-twins", "Digital twins", "modelling-simulation", "digital-twins", "expert", ("simulink", "gazebo"), ("simulation-tools", "control"), "A live model kept honest by measurements."),
)
# fmt: on


def pack_nodes() -> list[ConceptNode]:
    nodes = []
    for slug, name, category, _topic, difficulty, _prereqs, skills, summary in CONCEPT_ROWS:
        nodes.append(
            ConceptNode(
                slug=slug,
                name=name,
                category=category,
                difficulty=difficulty,
                summary=summary,
                skills=skills,
            )
        )
    return nodes


def pack_prerequisites() -> list[tuple[str, str, str, float]]:
    edges = []
    slugs = {row[0] for row in CONCEPT_ROWS}
    for slug, _name, _cat, _topic, _diff, prereqs, _skills, _summary in CONCEPT_ROWS:
        for parent in prereqs:
            if parent not in slugs:
                continue
            edges.append((parent, slug, "prerequisite_of", 1.0))
    # Curriculum sequence extras the v1 catalog already teaches.
    extras = [
        ("bellman", "q-learning", "builds_on", 0.6),
        ("q-learning", "dqn", "builds_on", 0.8),
        ("dqn", "ppo", "related_to", 0.5),
        ("ppo", "sac", "contrasts_with", 0.7),
        ("dqn", "policy-gradient", "contrasts_with", 0.6),
        ("cnns", "detection", "applies_to", 0.9),
        ("transformers", "rag", "applies_to", 0.8),
        ("mdp", "robotics", "applies_to", 0.5),
        ("neural-networks", "dqn", "part_of", 0.4),
        ("probability", "mdp", "builds_on", 0.7),
        ("linear-algebra", "cnns", "builds_on", 0.6),
        ("python-for-ml", "ros2", "related_to", 0.4),
        ("opencv", "yolo", "applies_to", 0.7),
        ("detection", "detr", "contrasts_with", 0.6),
        ("segmentation", "detection", "related_to", 0.7),
        ("stereo-vision", "3d-vision", "builds_on", 0.7),
        ("lidar", "3d-vision", "related_to", 0.6),
        ("embeddings", "rag", "applies_to", 0.8),
        ("transformers", "llm-engineering", "applies_to", 0.7),
        ("fedavg", "fedprox", "contrasts_with", 0.7),
        ("differential-privacy", "edge-ai", "related_to", 0.5),
        ("cpp", "ros2-cpp", "applies_to", 0.8),
        ("gazebo", "isaac-sim", "contrasts_with", 0.6),
        ("mujoco", "rl-robotics", "applies_to", 0.6),
        ("matlab", "simulink", "builds_on", 0.8),
    ]
    edges.extend(extras)
    return edges


def concept_topic(slug: str) -> str:
    for row in CONCEPT_ROWS:
        if row[0] == slug:
            return row[3]
    return ""


def concept_category(slug: str) -> str:
    for row in CONCEPT_ROWS:
        if row[0] == slug:
            return row[2]
    return ""
