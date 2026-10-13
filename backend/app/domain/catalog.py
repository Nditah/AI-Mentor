"""Curriculum graph, authored questions, and the roles those skills map to.

This module is the source of truth the database is seeded from. Changing a
lesson here and restarting the API updates catalog rows. It does not touch
learner progress.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Concept:
    slug: str
    name: str
    domain: str
    difficulty: str
    prerequisites: tuple[str, ...]
    opener: str
    scaffold: str
    explanation: str
    exercise: str
    checks: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    track_aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class PathDef:
    slug: str
    title: str
    description: str
    level: str
    concepts: tuple[str, ...]


@dataclass(frozen=True)
class QuestionTemplate:
    concept: str
    difficulty: str
    kind: str
    prompt: str
    options: tuple[str, ...] = ()
    answer: str = ""
    phrases: tuple[str, ...] = ()
    explanation: str = ""
    expected_stdout: str = ""


@dataclass(frozen=True)
class ProjectDef:
    slug: str
    title: str
    concept: str
    difficulty: str
    language: str
    brief: str
    starter: str


@dataclass(frozen=True)
class AchievementDef:
    slug: str
    name: str
    description: str
    xp_reward: int
    icon: str
    category: str = "learning"
    tier: str = "bronze"
    rarity: str = "common"


@dataclass(frozen=True)
class RoleDef:
    title: str
    requires: tuple[str, ...]
    summary: str


CONCEPTS: tuple[Concept, ...] = (
    Concept(
        slug="ai-fundamentals",
        name="AI Fundamentals",
        domain="Artificial Intelligence",
        difficulty="beginner",
        prerequisites=(),
        opener="What would you count as the difference between a program that follows fixed rules and a program that changes its behavior from feedback?",
        scaffold="A learning system changes later behavior from examples or from reward. A fixed program does not, however large it is.",
        explanation=(
            "Artificial intelligence is the attempt to build systems that predict, plan, perceive, or use language. "
            "Machine learning is the part of that attempt in which the behavior comes from data or feedback instead of a hand-written rule for every case. "
            "The rest of this studio hangs off that distinction: supervised learning fits examples, reinforcement learning pursues reward, and research methods ask whether a claimed result is actually supported."
        ),
        exercise="Name one task you would still write as ordinary code, and one you would rather learn from data. Say where the behavior comes from in each case.",
        checks=(
            "Where does the behavior come from in each system: a person writing rules, or experience?",
            "If the data changed tomorrow, which of your two systems would have to be rewritten by hand?",
        ),
        track_aliases=("artificial intelligence", "ai fundamentals"),
    ),
    Concept(
        slug="python-for-ml",
        name="Python for Machine Learning",
        domain="Python",
        difficulty="beginner",
        prerequisites=(),
        opener="When you write a function that returns a number, what would you test before you trust it inside a training loop?",
        scaffold="Test the function on one input whose answer you can compute by hand. Then give it an empty input and an input of the wrong type.",
        explanation=(
            "The labs in this studio use a small Python subset: functions, loops, dictionaries, and the standard library. "
            "A training loop is just a function you call many times. If you cannot say what one call returns, the loop will only hide the mistake.\n\n"
            "```python\ndef step(value: float, rate: float) -> float:\n"
            '    """Move value toward zero by rate."""\n'
            "    return value - rate\n```"
        ),
        exercise="Write `step` so that `step(1.0, 0.1)` returns `0.9`. What does it return for `step(0.0, 0.1)`?",
        checks=(
            "What is the single number you would compute by hand before running the function?",
            "What should happen when the step size is larger than the value?",
        ),
        aliases=("python",),
        track_aliases=("python for machine learning",),
    ),
    Concept(
        slug="probability",
        name="Probability",
        domain="Statistics",
        difficulty="beginner",
        prerequisites=("ai-fundamentals",),
        opener="If a coin has come up heads three times, what exactly do you believe about the fourth toss, and what would change your mind?",
        scaffold="A probability is a number you assign to an uncertain outcome before you see it. Independent tosses do not remember the earlier ones. The evidence that should move you is a biased coin, not a short streak.",
        explanation=(
            "Probability is how this studio talks about uncertainty. A random variable takes values with probabilities. "
            "Expectation is the probability-weighted average of those values, which is why a reward that is sometimes 1 and sometimes 0 becomes a single number an agent can compare. "
            "Independence means one outcome does not change the probabilities of the next."
        ),
        exercise="An action pays 1 with probability 0.2 and 0 otherwise. What is its expected reward? What would a second independent trial change about that number?",
        checks=(
            "Does the streak of heads change the probability, or only your suspicion that the coin is fair?",
            "Why is an expected reward more useful to an agent than a single lucky outcome?",
        ),
        aliases=("probability", "statistics"),
    ),
    Concept(
        slug="linear-algebra",
        name="Linear Algebra",
        domain="Linear Algebra",
        difficulty="intermediate",
        prerequisites=("ai-fundamentals",),
        opener="A grayscale image is a grid of numbers. What operation would you use to combine a whole grid into one weighted sum?",
        scaffold="A vector is an ordered list of numbers. A dot product multiplies matching entries and adds them up. Matrices apply that idea to every row.",
        explanation=(
            "Most models in this studio are linear algebra with a training rule attached. A vector stores features or pixel values. "
            "A dot product is a weighted sum. A matrix multiplies every row as its own weighted sum, which is the forward pass of a linear layer before the nonlinearity. "
            "You do not need a new object for every idea: state values in dynamic programming are just vectors indexed by state."
        ),
        exercise="Compute the dot product of `[1, 0, -1]` and `[0.2, 0.5, 0.3]`. Which input feature pulled the sum down?",
        checks=(
            "Which feature contributed nothing, and which pulled the sum negative?",
            "If this dot product were a prediction, what would a larger weight on the third feature do?",
        ),
        aliases=("linear algebra", "vectors", "matrices"),
    ),
    Concept(
        slug="supervised-learning",
        name="Supervised Learning",
        domain="Machine Learning",
        difficulty="intermediate",
        prerequisites=("python-for-ml", "probability", "linear-algebra"),
        opener="You have input and output pairs. What are you allowed to look at while you fit the model, and what must you refuse to look at until the end?",
        scaffold="The training pairs teach the model. A held-out set is how you notice that the model memorized those pairs instead of learning the pattern. Looking at the held-out set while you tune is how the test silently becomes more training data.",
        explanation=(
            "Supervised learning fits a function from inputs to labels. The loss measures how wrong the current function is on the training pairs, and the update reduces that loss. "
            "Generalization is the claim that the same function works on new inputs from the same process. "
            "A test set can support that claim only if it stayed unseen while you chose the model, the features, and the stopping point."
        ),
        exercise="Describe a dataset you care about. What is the input, what is the label, and what leak would make the test score look better than the real system?",
        checks=(
            "What, concretely, is the model not allowed to see until the evaluation is finished?",
            "If the loss on training data is near zero and the loss on new data is large, what happened?",
        ),
        aliases=("supervised learning", "machine learning"),
        track_aliases=("machine learning",),
    ),
    Concept(
        slug="agent-environment",
        name="Agent and Environment",
        domain="Reinforcement Learning",
        difficulty="beginner",
        prerequisites=("ai-fundamentals",),
        opener="What do you think an agent does in an environment?",
        scaffold="The agent selects an action. The environment answers with a new state and a reward. The agent does not get to rewrite the laws of the environment.",
        explanation=(
            "An **agent** chooses actions. The **environment** returns the next state and a reward. "
            "The boundary is a modeling choice: a robot's motors can sit inside the agent, while the physics of the room sits inside the environment.\n\n"
            "```mermaid\nflowchart LR\n  Agent -->|action| Environment\n  Environment -->|state and reward| Agent\n```\n\n"
            "Reward is a scalar the environment emits. It is not a judgement the agent makes about itself."
        ),
        exercise="For a robot vacuum, name the agent, one state, one action, and the reward. Who produces the reward?",
        checks=(
            "Who produces the reward: the agent, or the environment?",
            "Can the agent change the transition rules, or only its actions?",
        ),
        aliases=("agent", "environment"),
        track_aliases=("reinforcement learning", "rl"),
    ),
    Concept(
        slug="mdp",
        name="Markov Decision Process",
        domain="Reinforcement Learning",
        difficulty="intermediate",
        prerequisites=("agent-environment", "probability"),
        opener="If you already know the current state, which parts of the history are you still not allowed to need?",
        scaffold="The Markov property says the current state is a sufficient summary: the next state and reward depend on the past only through that state and the action you take now.",
        explanation=(
            "A Markov decision process is a tuple of states, actions, transition probabilities, rewards, and a discount factor. "
            "The Markov property is the modeling claim that the state already contains whatever history the future depends on. "
            "If your state hides something the future depends on, the process is not Markov and the later equations do not apply to the thing you actually built."
        ),
        exercise="A maze agent that only observes its current room is Markov. What extra state would you add if one door is sometimes locked and the agent cannot see the lock?",
        checks=(
            "What does the next state depend on, under the Markov property?",
            "Give an example of a hidden fact that would make the current observation not enough.",
        ),
        aliases=("mdp", "markov decision process", "markov"),
    ),
    Concept(
        slug="bellman",
        name="Bellman Equations",
        domain="Reinforcement Learning",
        difficulty="intermediate",
        prerequisites=("mdp",),
        opener="A state's value is supposed to be a single number. What future quantities do you think that number has to agree with?",
        scaffold="The value of a state is the immediate reward plus the discounted value of wherever you land next. The equation is a consistency condition, not a separate definition stacked on top.",
        explanation=(
            "The state-value function $V(s)$ is the expected discounted return from state $s$. "
            "Bellman's equation says that value must agree with one step of the process:\n\n"
            "$$V(s) = \\sum_a \\pi(a|s) \\sum_{s'} P(s'|s,a)\\,[R(s,a,s') + \\gamma V(s')]$$\n\n"
            "Gamma, between 0 and 1, decides how much a reward next step matters compared with a reward now. "
            "The optimal action-value form replaces the policy with a max over actions."
        ),
        exercise="Set gamma to 0. What does $V(s)$ collapse to, in words? Then set gamma to 0.99 and say which rewards start to matter.",
        checks=(
            "What does a larger gamma ask the agent to care about?",
            "Why is the equation a consistency check rather than a new goal?",
        ),
        aliases=("bellman", "bellman equation"),
    ),
    Concept(
        slug="dynamic-programming",
        name="Dynamic Programming",
        domain="Reinforcement Learning",
        difficulty="intermediate",
        prerequisites=("bellman",),
        opener="If you already knew the value of every next state, what would stop you from updating this state immediately?",
        scaffold="Dynamic programming sweeps the Bellman equations using a model of the transitions. Policy evaluation updates values for a fixed policy. Policy improvement makes the policy greedy with respect to those values.",
        explanation=(
            "Dynamic programming solves a known MDP by turning the Bellman equations into an assignment. "
            "You need the transition model. That is the difference from Monte Carlo and temporal difference, which learn from sampled experience. "
            "Policy iteration alternates evaluation and improvement and is the cleanest place to see that a better value estimate can produce a better policy."
        ),
        exercise="Name a problem where you have the transition model, and one where you only have the ability to try actions. Which method belongs to each?",
        checks=(
            "What object does dynamic programming require that sampling methods do not?",
            "After values change, what does the greedy policy do?",
        ),
        aliases=("dynamic programming",),
    ),
    Concept(
        slug="monte-carlo",
        name="Monte Carlo Methods",
        domain="Reinforcement Learning",
        difficulty="intermediate",
        prerequisites=("bellman", "mdp"),
        opener="If you cannot see the transition probabilities, what could you average instead?",
        scaffold="Monte Carlo waits until an episode ends, then averages the observed returns. There is no bootstrap from your own value estimates. The cost is that you learn nothing until the episode finishes.",
        explanation=(
            "Monte Carlo methods estimate values from complete returns. After an episode, each visited state is updated toward the discounted sum of rewards that actually followed. "
            "Because the target is a full return, the estimate is unbiased given enough episodes, and it has high variance. "
            "It also cannot update a continuing task that never ends, which is one reason temporal-difference methods exist."
        ),
        exercise="An episode returns rewards 1, then 0, then 1, with gamma 1. What return does the first state receive? What changes if you are only allowed to update at the end?",
        checks=(
            "Why does Monte Carlo refuse to update in the middle of the episode?",
            "What goes wrong if the task never terminates?",
        ),
        aliases=("monte carlo", "monte-carlo"),
    ),
    Concept(
        slug="temporal-difference",
        name="Temporal-Difference Learning",
        domain="Reinforcement Learning",
        difficulty="intermediate",
        prerequisites=("monte-carlo",),
        opener="You have seen one reward and you already have a guess for the next state. What error could you form without waiting for the episode to end?",
        scaffold="The TD error is the reward plus the discounted value of the next state, minus the value you predicted. You bootstrap: the target uses your own current guess.",
        explanation=(
            "Temporal-difference learning updates a state from the next state instead of from the full return. "
            "The one-step target is $R + \\gamma V(s')$. The difference between that target and $V(s)$ is the TD error. "
            "Bootstrapping lowers variance compared with Monte Carlo and introduces bias, because the target depends on a guess that is still wrong."
        ),
        exercise="Suppose $V(s)=0$, the reward is 1, gamma is 0.9, and $V(s')=0$. What is the TD error? What is it if $V(s')$ were already 1?",
        checks=(
            "Which term in the TD target is the bootstrap?",
            "Compared with Monte Carlo, what did you gain, and what bias did you accept?",
        ),
        aliases=("temporal difference", "td learning", "td error"),
    ),
    Concept(
        slug="q-learning",
        name="Q-Learning",
        domain="Reinforcement Learning",
        difficulty="intermediate",
        prerequisites=("temporal-difference",),
        opener="If the behavior you use to explore is not the behavior you want to learn, which action should the update pretend you will take next?",
        scaffold="Q-learning is off-policy. The next action in the target is the greedy action, max over Q, even if the action you actually take is exploratory.",
        explanation=(
            "Q-learning stores an action value $Q(s,a)$ and updates it toward $R + \\gamma \\max_{a'} Q(s',a')$. "
            "The max is what makes it off-policy: the target does not have to match the policy that collected the sample. "
            "Exploration, often epsilon-greedy, only affects which samples you see. It does not appear inside the max.\n\n"
            "```python\ntarget = reward + gamma * max(q_next)\n"
            "q[state][action] += alpha * (target - q[state][action])\n```"
        ),
        exercise="Your behavior policy takes a random action 20% of the time. Does that 20% belong inside the Q-learning target? Why or why not?",
        checks=(
            "Which action does the target use: the one you took, or the best one according to Q?",
            "What would go wrong if the target bootstrapped from the exploratory action instead?",
        ),
        aliases=("q-learning", "q learning"),
    ),
    Concept(
        slug="dqn",
        name="Deep Q-Networks",
        domain="Deep Learning",
        difficulty="advanced",
        prerequisites=("q-learning", "supervised-learning"),
        opener="A table cannot hold an image. What new problem appears the moment a neural net approximates Q?",
        scaffold="A network generalizes across similar states, which is what you wanted, and it also moves the values of states you did not intend to update. Replay and a slowly updated target network are there to keep the bootstrap target from chasing itself.",
        explanation=(
            "A deep Q-network represents Q with a neural network so the method can take image states and other large inputs. "
            "Two practical pieces keep the bootstrap stable enough to train. The replay buffer stores past transitions and samples them, breaking the strong correlation of consecutive frames. "
            "The target network is an older copy of the weights that produces the max term, so the target does not change on every gradient step."
        ),
        exercise="Say which failure replay is meant to reduce, and which failure the target network is meant to reduce. They are not the same failure.",
        checks=(
            "Why is a batch of consecutive game frames a poor training batch?",
            "What is the target network a copy of, and why must it lag?",
        ),
        aliases=("dqn", "deep q-network", "deep q network"),
    ),
    Concept(
        slug="policy-gradient",
        name="Policy Gradients",
        domain="Reinforcement Learning",
        difficulty="advanced",
        prerequisites=("mdp", "python-for-ml"),
        opener="Instead of learning values and then acting greedy, what object could you adjust directly?",
        scaffold="A policy gradient increases the probability of actions that were followed by high return, and decreases the probability of actions followed by low return. The policy itself is the thing you differentiate.",
        explanation=(
            "Policy gradients parameterize the action distribution and ascend the expected return. "
            "The score-function estimator multiplies the gradient of the log-probability of the taken action by a return. "
            "Subtracting a baseline, often a learned value, does not change the expected gradient and cuts variance. That baseline is the bridge from this method to actor-critic algorithms."
        ),
        exercise="An action was unlikely and the return was high. Should its probability go up or down? What changes if you subtract a baseline equal to the average return?",
        checks=(
            "What is being parameterized: Q, or the policy?",
            "Why can a baseline reduce variance without changing the expected update?",
        ),
        aliases=("policy gradient", "policy gradients"),
    ),
    Concept(
        slug="ppo",
        name="Proximal Policy Optimization",
        domain="Reinforcement Learning",
        difficulty="advanced",
        prerequisites=("policy-gradient", "temporal-difference"),
        opener="A single huge policy update can collapse performance. What would you limit, the step in parameter space or the change in action probabilities?",
        scaffold="PPO limits how far the new policy may move from the policy that collected the data, by clipping the probability ratio inside the objective.",
        explanation=(
            "Proximal policy optimization reuses a batch of samples for several small updates. "
            "The probability ratio between the new policy and the behavior policy multiplies the advantage. "
            "The clip stops that ratio from leaving a narrow band, so a single batch cannot rewrite the policy. "
            "A value function, trained with a temporal-difference loss, supplies the baseline inside the advantage."
        ),
        exercise="If the clip range is tiny, what happens to learning speed? If you remove the clip, which failure mode returns?",
        checks=(
            "What does the ratio compare?",
            "Which earlier method supplies the value baseline?",
        ),
        aliases=("ppo", "proximal policy optimization"),
    ),
    Concept(
        slug="sac",
        name="Soft Actor-Critic",
        domain="Reinforcement Learning",
        difficulty="expert",
        prerequisites=("ppo", "q-learning"),
        opener="Maximum reward is not the only thing an agent can maximize. What else might you want in the policy so that it does not collapse onto one action?",
        scaffold="Soft actor-critic maximizes expected return plus the entropy of the policy. The entropy term keeps the policy from becoming certain too early, which is useful for continuous control.",
        explanation=(
            "Soft actor-critic is an off-policy actor-critic method for continuous actions. "
            "The objective adds an entropy bonus, so the policy is paid both for reward and for remaining stochastic. "
            "It learns Q functions and a policy, and it reuses a replay buffer the way Q-learning does. "
            "The temperature controls the trade: too little entropy and the policy collapses; too much and it never exploits."
        ),
        exercise="Describe a robot joint-control task where a deterministic policy would be a bad early answer. What would the entropy term keep alive?",
        checks=(
            "What two quantities does the SAC objective add together?",
            "Why is a replay buffer compatible with this method when vanilla policy gradient is on-policy?",
        ),
        aliases=("sac", "soft actor-critic", "soft actor critic"),
    ),
    Concept(
        slug="multi-agent",
        name="Multi-Agent Reinforcement Learning",
        domain="Reinforcement Learning",
        difficulty="expert",
        prerequisites=("q-learning", "mdp"),
        opener="If every other player is also learning, what happens to the Markov property you were relying on?",
        scaffold="From one agent's point of view, other learning agents are part of the environment, and that environment is non-stationary because their policies change. The state that used to be enough may no longer be enough.",
        explanation=(
            "Multi-agent reinforcement learning studies several agents whose rewards depend on each other. "
            "Independent Q-learning is the simple baseline and it often fails because each learner treats the others as a fixed environment. "
            "Centralized training with decentralized execution lets agents use extra information during training, then act from their own observations. "
            "Credit assignment, who caused the reward, is the research problem hiding inside the algorithm."
        ),
        exercise="Two robots share a reward when a box reaches a goal. Why can each robot's local Q-learning update become wrong without the other robot changing the physics?",
        checks=(
            "What became non-stationary, the physics or the other policy?",
            "What information is allowed at training time that is not allowed at execution time, in the centralized-training setup?",
        ),
        aliases=("multi-agent", "multi agent"),
    ),
    Concept(
        slug="robotics",
        name="Robotics",
        domain="Robotics",
        difficulty="intermediate",
        prerequisites=("ai-fundamentals",),
        opener="A robot's software can plan a perfect path. What physical fact can still make that path fail?",
        scaffold="A robot couples sensing, estimation, planning, and control. The map is a model, the motor commands are actions, and the floor is under no obligation to match the model.",
        explanation=(
            "Robotics software is a loop: sensors produce observations, an estimator updates a belief about the world, a planner chooses a motion, and a controller tracks it. "
            "The failures that matter are usually at the joints between those pieces: a stale estimate, a plan that ignores the robot's footprint, or a controller asked to track a path the motors cannot follow."
        ),
        exercise="Pick one household robot. Name its observation, its hidden state, and one way the plan can be right while the execution is wrong.",
        checks=(
            "Which part of the loop consumes observations, and which part emits motor commands?",
            "Why is a perfect plan not a complete robot?",
        ),
        aliases=("robotics", "robot"),
        track_aliases=("robotics",),
    ),
    Concept(
        slug="ros2",
        name="ROS 2",
        domain="Robotics",
        difficulty="advanced",
        prerequisites=("robotics", "python-for-ml"),
        opener="Why would you split a robot into separate processes instead of one program that reads the camera and drives the wheels?",
        scaffold="ROS 2 nodes publish and subscribe to typed messages. The split lets a camera driver restart without taking the controller with it. The cost is that you must be explicit about time, frames, and what happens when a message is late.",
        explanation=(
            "ROS 2 is a middleware for robot processes. Nodes communicate with topics, services, and actions. "
            "A message carries data and, when you do it properly, a timestamp and a coordinate frame. "
            "Most integration bugs in a ROS graph are time bugs: a transform looked up at the wrong stamp, or a controller acting on a scan that is already old."
        ),
        exercise="Draw three nodes for a mobile robot: camera, estimator, and controller. Which messages must carry a timestamp, and what should the controller do if the newest scan is too old?",
        checks=(
            "What does a node publish, and what does it subscribe to?",
            "Why is a timestamp part of the interface and not an optional extra?",
        ),
        aliases=("ros2", "ros 2"),
    ),
    Concept(
        slug="computer-vision",
        name="Computer Vision",
        domain="Computer Vision",
        difficulty="advanced",
        prerequisites=("python-for-ml", "linear-algebra"),
        opener="A camera gives you brightness on a grid. What is still missing before that grid is a statement about the world?",
        scaffold="Vision turns an image into geometric or semantic claims: this edge, that object, this distance. The image itself is not the claim. Calibration, viewpoint, and lighting decide whether the claim is supported.",
        explanation=(
            "Computer vision estimates world structure from images. Classical methods use geometry: features, epipolar constraints, and calibration. "
            "Learned methods map pixels to labels or boxes and then still have to be checked against geometry when a robot will act on them. "
            "A detector score is not a position in the room until something relates the camera frame to the robot frame."
        ),
        exercise="A model says 'door' with high confidence. What extra measurement do you need before a robot may drive toward it?",
        checks=(
            "What does the image contain, and what do you still have to infer?",
            "Why is a label in pixel space not yet a navigation goal?",
        ),
        aliases=("computer vision", "vision"),
    ),
    Concept(
        slug="slam",
        name="SLAM",
        domain="Robotics",
        difficulty="expert",
        prerequisites=("robotics", "probability"),
        opener="You are building a map from a sensor that is itself moving. What are the two estimates that keep corrupting each other?",
        scaffold="SLAM estimates the map and the robot's path at the same time. An error in the pose warps the map, and an error in the map then warps the next pose.",
        explanation=(
            "Simultaneous localization and mapping estimates where the robot is and what the world looks like, using the same sensor stream. "
            "The two estimates are coupled: landmarks are observed from a pose you do not know exactly, and the pose is inferred from landmarks you do not know exactly. "
            "Filters and pose-graph optimizers exist to keep that coupling from drifting without bound. Loop closure, recognizing a place you have seen, is what pulls a long trajectory back into agreement."
        ),
        exercise="A robot drives down a long corridor with few features, then re-enters the starting room. Which event can correct the drift, and why could the corridor not?",
        checks=(
            "Name the two quantities SLAM refuses to estimate separately.",
            "What observation makes loop closure possible?",
        ),
        aliases=("slam",),
    ),
    Concept(
        slug="navigation",
        name="Navigation",
        domain="Robotics",
        difficulty="advanced",
        prerequisites=("slam", "robotics"),
        opener="You have a map and a goal. What costs, other than distance, should a path refuse to ignore?",
        scaffold="Global planning finds a path on the map. Local planning keeps the robot on that path while reacting to obstacles the map did not contain. Distance is only one cost; clearance, time, and the robot's footprint are others.",
        explanation=(
            "Navigation stacks a global planner on a local controller. The global plan is a path or a cost field from the current pose to the goal on the known map. "
            "The local planner consumes fresh sensors and can deviate when something blocks the path. "
            "A common failure is a global plan that treats the robot as a point, then a local planner that discovers the robot does not fit."
        ),
        exercise="Give a hallway scene where the shortest path is a bad path. Name the cost you would add.",
        checks=(
            "What does the global planner know that the local planner might not?",
            "What does the local planner see that the map might lack?",
        ),
        aliases=("navigation", "path planning"),
    ),
    Concept(
        slug="rl-robotics",
        name="RL for Robotics",
        domain="Robotics",
        difficulty="expert",
        prerequisites=("navigation", "q-learning"),
        opener="A learned policy can outperform a planned one in simulation. What has to be true before you let it command a real motor?",
        scaffold="The policy is only as meaningful as the reward and the simulator. A reward that pays for progress can also pay for falling in a way the simulator forgives. Transfer to hardware needs a constraint the reward does not get to negotiate.",
        explanation=(
            "Reinforcement learning on robots uses the same agent-environment loop, with motor commands as actions and sensors as observations. "
            "It is rarely a replacement for the whole navigation stack. It is a way to learn a local skill, a grasp, a gait, a recovery, inside limits a planner or a safety filter still enforces. "
            "Sim-to-real failure is usually a lied-about contact, friction, or delay, not a mystery of the optimizer."
        ),
        exercise="Write a reward for walking that a simulator could hack. Then write the constraint you would refuse to put inside that reward.",
        checks=(
            "Which part of a classical stack is the learned policy replacing, and which part should remain in charge of safety?",
            "Name one simulator lie that would make a successful training curve meaningless on hardware.",
        ),
        aliases=("rl robotics", "robot learning"),
    ),
    Concept(
        slug="llm-engineering",
        name="LLM Engineering",
        domain="LLM Engineering",
        difficulty="expert",
        prerequisites=("python-for-ml",),
        opener="A language model answered confidently. What would you need to see, besides the prose, before you trusted a factual claim?",
        scaffold="The model generates plausible text. A system around it chooses tools, retrieval, and checks. A citation the model invented is worse than no citation, so the application has to verify that the quoted source actually contains the claim.",
        explanation=(
            "LLM engineering is the design of the system around a model: prompts, tools, retrieval, evaluation, and the decision to abstain. "
            "The prompt is not the product. The product is the contract: which claims must be grounded, which tools may be called, and what the system does when the model is unsure. "
            "Evaluation has to include cases the prompt was not written to flatter."
        ),
        exercise="Take a tutor you would trust. What is it allowed to answer from memory, and what must it tie to a source you can open?",
        checks=(
            "What is the difference between a fluent answer and a grounded one?",
            "Where would you put the check that a citation really contains the sentence?",
        ),
        aliases=("llm", "llm engineering", "large language model"),
        track_aliases=("llm engineering",),
    ),
    Concept(
        slug="research-methods",
        name="AI Research Methods",
        domain="AI Research Methods",
        difficulty="phd",
        prerequisites=("ai-fundamentals", "probability"),
        opener="A paper reports a higher score than the baseline. What, other than the method, could have produced that difference?",
        scaffold="A result is a claim tied to a procedure. The procedure includes data, seeds, compute, and what the authors tried and did not report. A higher number is not yet a finding until those are fixed enough for someone else to be surprised.",
        explanation=(
            "Research methods in this studio mean the habits that keep a claim attached to evidence: a pre-specified comparison, a baseline that is actually trying, an ablation that removes one piece, and a limitation a reader can use. "
            "Reading a paper is the same skill as reviewing one. You identify the claim, the experiment that could have falsified it, and the gap the authors earned the right to suggest. "
            "A future-work paragraph that the evidence does not motivate is advertising."
        ),
        exercise="Pick one table in a paper you are reading. State the claim the table is supposed to support, and one confound the table does not rule out.",
        checks=(
            "What would have counted as evidence against the claim?",
            "Which limitation is supported by the paper's own results, rather than by a generic list?",
        ),
        aliases=("research methods", "paper review"),
        track_aliases=("research", "ai research"),
    ),
)


PATHS: tuple[PathDef, ...] = (
    PathDef(
        slug="ai-fundamentals",
        title="AI Fundamentals",
        description="The distinctions every later track assumes: learning versus rules, Python, probability, linear algebra, and supervised learning.",
        level="beginner",
        concepts=(
            "ai-fundamentals",
            "python-for-ml",
            "probability",
            "linear-algebra",
            "supervised-learning",
        ),
    ),
    PathDef(
        slug="reinforcement-learning",
        title="Reinforcement Learning",
        description="From the agent-environment loop through MDPs, Bellman equations, dynamic programming, Monte Carlo, TD, Q-learning, DQN, policy gradients, PPO, SAC, and multi-agent RL.",
        level="intermediate",
        concepts=(
            "agent-environment",
            "mdp",
            "bellman",
            "dynamic-programming",
            "monte-carlo",
            "temporal-difference",
            "q-learning",
            "dqn",
            "policy-gradient",
            "ppo",
            "sac",
            "multi-agent",
        ),
    ),
    PathDef(
        slug="robotics",
        title="Robotics",
        description="The robot loop, ROS 2, vision, SLAM, navigation, and where reinforcement learning is allowed to touch a motor.",
        level="advanced",
        concepts=("robotics", "ros2", "computer-vision", "slam", "navigation", "rl-robotics"),
    ),
    PathDef(
        slug="llm-engineering",
        title="LLM Engineering",
        description="How to put a language model inside a system that can abstain, cite, and be evaluated.",
        level="advanced",
        concepts=("llm-engineering", "research-methods"),
    ),
)


QUESTIONS: tuple[QuestionTemplate, ...] = (
    QuestionTemplate(
        concept="agent-environment",
        difficulty="beginner",
        kind="mcq",
        prompt="In the agent-environment loop, who produces the reward?",
        options=(
            "The agent, as a self-score",
            "The environment, as a scalar signal",
            "The policy gradient",
            "The discount factor",
        ),
        answer="The environment, as a scalar signal",
        explanation="Reward is part of the environment's response, together with the next state.",
    ),
    QuestionTemplate(
        concept="mdp",
        difficulty="intermediate",
        kind="mcq",
        prompt="The Markov property says the next state and reward depend on the past only through what?",
        options=(
            "The full action history",
            "The current state and the current action",
            "The value function",
            "The discount factor alone",
        ),
        answer="The current state and the current action",
        explanation="If something the future depends on is missing from the state, the process you built is not Markov.",
    ),
    QuestionTemplate(
        concept="bellman",
        difficulty="intermediate",
        kind="mcq",
        prompt="Raising the discount factor gamma makes the agent care more about which rewards?",
        options=(
            "Only the immediate reward",
            "Rewards further in the future",
            "Rewards that have already been received",
            "The entropy of the policy",
        ),
        answer="Rewards further in the future",
        explanation="Gamma weights future returns. Larger gamma reaches further.",
    ),
    QuestionTemplate(
        concept="bellman",
        difficulty="intermediate",
        kind="short",
        prompt="In one or two sentences, what consistency does a Bellman equation demand?",
        phrases=("reward", "next", "discount"),
        explanation="The value of a state must match the immediate reward plus the discounted value of the next state.",
    ),
    QuestionTemplate(
        concept="q-learning",
        difficulty="intermediate",
        kind="mcq",
        prompt="Q-learning is off-policy because the target bootstraps from which action?",
        options=(
            "The exploratory action that was just taken",
            "The greedy action, via a max over Q",
            "A random action sampled from the behavior policy",
            "The first action in the action list",
        ),
        answer="The greedy action, via a max over Q",
        explanation="The max is the target policy. Exploration only chooses the samples.",
    ),
    QuestionTemplate(
        concept="q-learning",
        difficulty="intermediate",
        kind="coding",
        prompt="GridWorld starts at (0, 0). Action 1 steps right. Reset the environment, take action 1, and print the resulting state tuple.",
        expected_stdout="(1, 0)",
        explanation="One step right from the origin on this 4x4 grid is the state (1, 0).",
    ),
    QuestionTemplate(
        concept="dqn",
        difficulty="advanced",
        kind="mcq",
        prompt="What is the replay buffer in DQN primarily there to break?",
        options=(
            "The Markov property",
            "Correlation between consecutive transitions",
            "The use of a discount factor",
            "The need for a reward",
        ),
        answer="Correlation between consecutive transitions",
        explanation="Consecutive frames are strongly dependent. A random minibatch from replay is less so.",
    ),
    QuestionTemplate(
        concept="ppo",
        difficulty="advanced",
        kind="mcq",
        prompt="What does the PPO clip limit?",
        options=(
            "The discount factor",
            "How far the new policy's action probabilities may move from the behavior policy",
            "The size of the replay buffer",
            "The number of robots",
        ),
        answer="How far the new policy's action probabilities may move from the behavior policy",
        explanation="The clipped ratio keeps one batch from taking an unbounded policy step.",
    ),
    QuestionTemplate(
        concept="research-methods",
        difficulty="phd",
        kind="research",
        prompt="A paper claims a new optimizer is better because one table shows a higher score. In a short review, name the claim, one confound the table may not rule out, and what evidence would have counted against the claim.",
        phrases=("claim", "baseline", "confound"),
        explanation="A higher number is not a finding until the comparison, the baseline, and the unreported choices are fixed enough to falsify.",
    ),
    QuestionTemplate(
        concept="supervised-learning",
        difficulty="intermediate",
        kind="short",
        prompt="Why does looking at the test set while you tune the model invalidate the test score?",
        phrases=("test", "training"),
        explanation="The test set has become more training data, so the score no longer estimates performance on unseen data.",
    ),
)


PROJECTS: tuple[ProjectDef, ...] = (
    ProjectDef(
        slug="tabular-q-learning",
        title="One honest Q-learning step",
        concept="q-learning",
        difficulty="intermediate",
        language="python",
        brief=(
            "GridWorld is already in the lab. It is a 4 by 4 grid, start (0, 0), goal (3, 3). "
            "Actions are 0 up, 1 right, 2 down, 3 left. The reward is 1 at the goal and -0.04 otherwise.\n\n"
            "Write a function `one_step` that resets the world, takes action 1, and returns the next state. "
            "Print that state. Then, in comments or a docstring, say whether the Q-learning target should use the action you took or the greedy action."
        ),
        starter=("env = GridWorld()\n# Reset, step right (action 1), and print the state.\n"),
    ),
)


ACHIEVEMENTS: tuple[AchievementDef, ...] = (
    AchievementDef("first_steps", "First steps", "Completed a lesson.", 20, "footprints"),
    AchievementDef("streak_3", "Three-day streak", "Showed up three days in a row.", 30, "flame", "streak"),
    AchievementDef(
        "week_streak", "Week streak", "Showed up seven days in a row.", 80, "flame", "streak", "silver"
    ),
    AchievementDef(
        "streak_30",
        "Thirty-day streak",
        "Showed up thirty days in a row. A freeze covers one missed day.",
        120,
        "flame",
        "streak",
        "gold",
        "rare",
    ),
    AchievementDef(
        "streak_100",
        "Hundred-day streak",
        "A hundred local days of practice.",
        200,
        "flame",
        "streak",
        "platinum",
        "epic",
    ),
    AchievementDef(
        "streak_365",
        "Year streak",
        "A year of local days. Cosmetic recognition only.",
        400,
        "flame",
        "streak",
        "platinum",
        "legendary",
    ),
    AchievementDef("perfect_quiz", "Clean quiz", "Scored every part of a quiz.", 40, "check"),
    AchievementDef("mastery", "Mastery", "Reached 80 on a concept.", 60, "seal", "mastery", "gold"),
    AchievementDef("reviewer", "Reviewer", "Ran a grounded paper pass.", 40, "scroll", "research"),
    AchievementDef(
        "shipped_code",
        "Ran in the lab",
        "Ran a Python snippet the sandbox accepted.",
        30,
        "terminal",
        "coding",
    ),
    AchievementDef(
        "rl_pioneer",
        "RL Pioneer",
        "Completed the RL Foundations learning path.",
        80,
        "seal",
        "mastery",
        "gold",
        "rare",
    ),
    AchievementDef(
        "ai_apprentice",
        "AI Apprentice",
        "Reached level 10.",
        40,
        "spark",
        "learning",
        "silver",
    ),
    AchievementDef(
        "grandmaster_architect",
        "Grandmaster AI Architect",
        "Reached level 40. A recognition title, not a degree.",
        0,
        "crown",
        "mastery",
        "platinum",
        "legendary",
    ),
)


ROLES: tuple[RoleDef, ...] = (
    RoleDef(
        title="Machine learning engineer",
        requires=("python-for-ml", "supervised-learning", "linear-algebra"),
        summary="Fits and evaluates models, and is trusted with the boundary between training data and the test.",
    ),
    RoleDef(
        title="Reinforcement learning engineer",
        requires=("mdp", "q-learning", "ppo"),
        summary="Builds agents whose updates match the Bellman target they claim to optimize.",
    ),
    RoleDef(
        title="Robotics software engineer",
        requires=("robotics", "ros2", "navigation"),
        summary="Ships the loop from sensor message to motor command, including the late-message case.",
    ),
    RoleDef(
        title="LLM engineer",
        requires=("llm-engineering", "python-for-ml"),
        summary="Puts a model behind retrieval, tools, and a refusal when a claim is not grounded.",
    ),
    RoleDef(
        title="AI research scientist",
        requires=("research-methods", "probability", "mdp"),
        summary="States a claim that an experiment could have falsified, and reads other people's papers the same way.",
    ),
)


_BY_SLUG = {concept.slug: concept for concept in CONCEPTS}


def get_concept(slug: str) -> Concept | None:
    return _BY_SLUG.get(slug)


def concept_index(slug: str) -> int:
    for index, concept in enumerate(CONCEPTS):
        if concept.slug == slug:
            return index
    raise KeyError(slug)


def _alias_pairs(specific: bool) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for concept in CONCEPTS:
        source = concept.aliases if specific else concept.track_aliases
        for alias in source:
            pairs.append((alias.lower(), concept.slug))
        if specific:
            pairs.append((concept.name.lower(), concept.slug))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


_SPECIFIC = _alias_pairs(True)
_TRACKS = _alias_pairs(False)


def detect_concept(text: str) -> Concept | None:
    """Prefer a named concept over a track name. 'Q-learning in RL' resolves to Q-learning."""

    import re

    lowered = text.lower()

    def find(pairs: list[tuple[str, str]]) -> str | None:
        best: tuple[int, int, str] | None = None
        for alias, slug in pairs:
            match = re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", lowered)
            if not match:
                continue
            candidate = (len(alias), -match.start(), slug)
            if best is None or candidate > best:
                best = candidate
        return None if best is None else best[2]

    slug = find(_SPECIFIC) or find(_TRACKS)
    return None if slug is None else _BY_SLUG[slug]
