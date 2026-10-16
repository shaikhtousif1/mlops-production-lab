# Day 0 — From DevOps to AI: Understanding the Landscape

Welcome to Day 0 of our learning journey.

This is not about abandoning our DevOps and Cloud experience. It is about **reusing that experience to build, deploy, operate, and improve AI systems in production**.

Our learning path will move from **MLOps fundamentals → LLMOps → production GenAI applications**. We will learn concepts, build working examples, explain our decisions, and practice the kinds of questions that come up in technical interviews.

---

## 1. First, understand the AI landscape

“AI” is the broad umbrella. Traditional predictive AI and Generative AI are two important approaches within it.

```text
Artificial Intelligence (AI)
├── Traditional / Predictive AI
│   ├── Machine Learning (ML)
│   │   ├── Classification
│   │   ├── Regression
│   │   └── Clustering
│   └── Deep Learning (DL)
│       └── Neural networks for tasks such as vision, speech, and language
│
└── Generative AI (GenAI)
    ├── Large Language Models (LLMs)
    ├── Image / audio / video generation models
    └── Applications: chatbots, RAG, assistants, agents, content generation
```

This is a simplified map, not a strict taxonomy: deep learning also powers many GenAI models, and language models existed before today's GenAI wave.

### Traditional / predictive AI vs. Generative AI

| Dimension | Traditional / Predictive AI | Generative AI |
|---|---|---|
| Main goal | Predict, classify, rank, detect, or estimate | Generate or transform content such as text, code, images, or audio |
| Typical question | “Will this transaction be fraudulent?” | “Explain why this transaction looks suspicious.” |
| Typical output | Label, score, probability, forecast, or ranking | Text, code, image, audio, structured output, or a generated response |
| Common techniques | Regression, decision trees, gradient boosting, neural networks | Foundation models, LLMs, diffusion models, and other generative models |
| Data and workflow | Often structured/tabular data plus features and labels | Often large-scale text, code, image, audio, or multimodal data; applications may also use private enterprise data |
| Evaluation | Accuracy, precision, recall, F1, ROC-AUC, MAE/RMSE, business outcomes | Task-specific quality, groundedness, relevance, safety, latency, cost, and human evaluation |
| Common failure | Wrong prediction or poor generalization | Hallucination, irrelevant output, prompt injection, unsafe output, or poor retrieval |
| Production concerns | Data quality, feature consistency, model drift, retraining | All relevant ML concerns plus prompts, context, retrieval, model/provider changes, token cost, and output quality |

**Important:** GenAI is not automatically more accurate or more intelligent than traditional AI. Choose the approach based on the problem, evidence, risk, and cost.

### A practical example

Imagine a support-ticket platform:

- **Traditional ML:** Predict ticket priority or route a ticket to the right team.
- **GenAI:** Summarize the ticket, draft a response, or explain a likely resolution.
- **Combined solution:** ML assigns priority; a retrieval-augmented LLM drafts a response using approved documentation; rules and a human review control what gets sent.

---

## 2. Where MLOps, LLMOps, and GenAI fit

These terms are related, but they are not interchangeable.

### MLOps — operating machine learning systems

MLOps applies software engineering, automation, infrastructure, testing, and operational practices to the machine-learning lifecycle.

A typical lifecycle:

1. Collect and validate data.
2. Prepare data and engineer features.
3. Train and evaluate a model.
4. Track experiments and register model versions.
5. Package and deploy the model.
6. Monitor service health and model performance.
7. Detect drift or quality degradation and retrain when appropriate.

Typical tools include Python, scikit-learn, MLflow, Docker, Kubernetes, CI/CD, object storage, workflow orchestration, and monitoring systems.

### LLMOps — operating LLM-powered applications

LLMOps applies operational practices to applications built with large language models. It overlaps with MLOps but adds concerns specific to language-model applications.

Typical lifecycle:

1. Select a model and provider, or deploy a model you host.
2. Version prompts, model settings, and application code.
3. Connect enterprise data when needed using retrieval-augmented generation (RAG).
4. Evaluate response quality, retrieval quality, safety, latency, and cost.
5. Trace requests across prompts, retrieval, tools, and model calls.
6. Apply access controls, privacy protections, guardrails, and fallback strategies.
7. Monitor production behaviour and improve the system from evidence.

Typical building blocks include model APIs or self-hosted models, prompt templates, embedding models, vector databases, RAG pipelines, evaluation datasets, tracing, and policy controls.

### GenAI — the application and model space

Generative AI is the capability and application space: generating or transforming content. LLMOps is one set of practices used to build and operate LLM-based GenAI applications.

Not every GenAI system uses an LLM, and not every LLM application needs RAG or agents.

### How the concepts relate

```text
AI
├── Predictive ML systems ── operated with MLOps practices
└── GenAI systems
    ├── LLM-powered applications ── operated with LLMOps practices
    └── Other generative systems ── use lifecycle practices suited to their models

MLOps and LLMOps overlap in:
version control, automation, testing, deployment, security,
observability, reliability, governance, and cost management.
```

**A useful mental model:** MLOps gives us a strong operational foundation. LLMOps extends that foundation for LLM-specific behaviour. GenAI is the wider family of capabilities and products we can build.

---

## 3. Map your existing DevOps and Cloud skills to AI

You are not starting from zero. Many production AI problems are familiar engineering problems with new components and quality signals.

| Your existing knowledge | Where it applies in MLOps / LLMOps |
|---|---|
| Git and branching | Version application code, training code, prompts, evaluation datasets, and configuration |
| CI/CD pipelines | Test, package, evaluate, and promote application or model changes through environments |
| Docker | Package inference services, workers, evaluation jobs, and supporting components |
| Kubernetes | Run model-serving APIs, RAG services, asynchronous workers, and supporting infrastructure |
| Terraform / IaC | Provision clusters, networking, storage, identity, databases, and model-serving infrastructure |
| Helm / GitOps | Deploy and reconcile AI application components and configuration |
| Secrets management / IAM | Protect API keys, model credentials, data access, and service identities |
| Monitoring and logging | Monitor availability, errors, latency, saturation, traces, and resource use |
| Prometheus / Grafana / OpenTelemetry-style tracing | Observe service metrics and distributed request flows; add AI quality and cost signals |
| Security and DevSecOps | Apply least privilege, data protection, dependency scanning, auditability, and policy enforcement |
| SRE / incident response | Define SLOs, investigate regressions, manage fallbacks, and run post-incident reviews |
| Release management | Version and promote models, prompts, retrieval configuration, and application changes safely |

### What is new and needs focused learning?

- **ML fundamentals:** datasets, features, training versus inference, overfitting, evaluation metrics, and data/model drift.
- **Model lifecycle:** experiment tracking, model artifacts, registries, reproducibility, and model promotion.
- **LLM fundamentals:** tokens, context windows, sampling settings, embeddings, model limitations, and inference cost.
- **RAG:** document ingestion, chunking, retrieval, reranking, citations, and grounding.
- **LLM evaluation:** test datasets, expected behaviour, retrieval metrics, answer quality, safety, and regression testing.
- **LLM observability:** traces, prompt/model versions, token usage, latency, retrieval results, and quality feedback.
- **AI-specific security:** prompt injection, sensitive-data exposure, unsafe tool execution, and permissions around retrieved data.

You do **not** need to become a research scientist before you can contribute to production AI engineering. You do need enough ML and LLM understanding to make sound engineering decisions and recognize when a model or application is failing.

---

## 4. Our learning path: MLOps → LLMOps → GenAI engineering

This is a sequence of learning stages, not a promise that every stage takes a fixed number of weeks. Move forward when you can demonstrate the outcomes, not just finish the reading.

### Stage 1 — Foundations: ML and the model lifecycle

**Learn**
- Python and essential data handling with pandas and NumPy.
- Basic supervised learning: classification and regression.
- Training, validation, and test datasets; data leakage and overfitting.
- Evaluation metrics and why accuracy alone can mislead.
- Inference versus training.

**Build**
- Train a small classification model.
- Track parameters, metrics, and artifacts with MLflow.
- Save the model and expose a prediction endpoint.

**Ready to move on when**
- You can explain the complete path from dataset to prediction.
- You can explain your metric choice and identify at least one way the model could fail.

### Stage 2 — Production MLOps

**Learn**
- Experiment tracking and model registry.
- Data and model versioning; reproducible training.
- Data validation and automated model tests.
- Batch versus online inference.
- Model serving, deployment strategies, monitoring, and drift.
- Retraining triggers and model promotion.

**Build**
- Create a reproducible training pipeline.
- Add tests and a CI pipeline.
- Package and deploy the model using Docker; use Kubernetes where appropriate.
- Track experiments and model versions in MLflow.
- Monitor endpoint health and model-specific quality.

**Ready to move on when**
- Another engineer can reproduce your experiment.
- A model change can be tested, reviewed, deployed, monitored, and rolled back safely.

### Stage 3 — LLM foundations and application engineering

**Learn**
- What LLMs do and how tokens, context windows, and inference settings affect behaviour.
- Model APIs versus self-hosted models.
- System instructions, prompt templates, structured output, and prompt versioning.
- Basic LLM application patterns and limitations.
- Latency, rate limits, token usage, and cost.

**Build**
- Create a small LLM-backed application.
- Keep prompts and configuration versioned.
- Add input validation, error handling, retries with limits, and basic tests.
- Record latency, errors, and token usage.

**Ready to move on when**
- You can explain the request path and its failure modes.
- You can test a prompt change instead of relying only on a few manual examples.

### Stage 4 — RAG and enterprise knowledge

**Learn**
- Document ingestion, parsing, chunking, and metadata.
- Embeddings and vector similarity.
- Vector databases and retrieval strategies.
- Hybrid search and reranking where appropriate.
- Grounded answers, citations, access control, and retrieval evaluation.

**Build**
- Create a RAG application over a small, approved document collection.
- Return relevant source references with answers.
- Test retrieval separately from answer generation.
- Test missing information, irrelevant documents, and access-control boundaries.

**Ready to move on when**
- You can identify whether a poor answer came from ingestion, retrieval, context construction, or generation.
- You have a repeatable evaluation set rather than relying on demos that “look good.”

### Stage 5 — LLMOps: evaluation, observability, and governance

**Learn**
- Evaluation datasets and regression testing.
- Retrieval quality versus answer quality.
- Human review and model-based evaluation, including their limitations.
- Tracing model calls, prompts, retrieval, and tools.
- Prompt/model/configuration versioning and controlled rollouts.
- Guardrails, privacy, security, latency, and cost controls.

**Build**
- Create a baseline evaluation dataset.
- Compare changes to prompts, retrieval settings, or models against the baseline.
- Capture traces, errors, latency, token usage, and evaluation results.
- Add safety tests and a release gate for unacceptable regressions.

**Ready to move on when**
- You can show evidence that a change improved or degraded the system.
- You can investigate a bad response using traces and evaluation results, not guesswork.

### Stage 6 — Advanced GenAI: tools and agents

**Learn**
- Tool/function calling and schema validation.
- Workflow orchestration versus autonomous agents.
- State, memory, permissions, and human approval.
- Timeouts, retries, idempotency, and failure recovery.
- Agent evaluation and protection against prompt injection or unsafe tool use.

**Build**
- Start with a deterministic workflow that calls one or two safe tools.
- Add explicit permissions, logging, bounded retries, and human approval for consequential actions.
- Introduce agent-like behaviour only where it adds measurable value.

**Ready to move on when**
- You can explain why a workflow or agent is appropriate.
- You can constrain its permissions and demonstrate how it behaves when a tool fails.

### Stage 7 — Production-ready GenAI platform

**Learn**
- End-to-end architecture, tenancy, identity, networking, and data boundaries.
- Scaling, caching, rate limits, resilience, and provider fallback.
- Model and provider selection using quality, latency, availability, and cost.
- SLOs, dashboards, incident response, audit trails, and governance.
- Safe release patterns for prompts, models, retrieval configuration, and application code.

**Build**
- Deploy a production-style GenAI application.
- Add CI/CD, infrastructure as code, observability, evaluation gates, security controls, and a rollback plan.
- Document architecture, trade-offs, runbooks, and known limitations.

**Final outcome**
- A portfolio project you can demonstrate and defend in a technical interview.

---

## 5. The production mindset we will use

For every topic, ask these questions:

1. **What problem does it solve?**
2. **How does it work?**
3. **Where does it fit in the architecture?**
4. **How do we deploy and secure it?**
5. **How do we test whether it works?**
6. **How do we observe and troubleshoot it?**
7. **What are the trade-offs in quality, latency, reliability, and cost?**
8. **How would we explain and defend this decision in an interview?**

We will not measure progress only by the number of tools we know. We will measure it by what we can build, explain, test, troubleshoot, and improve.

---

## 6. How our group sessions will work

Each session should be practical and interactive:

- One person explains a topic and its architecture.
- The presenter demonstrates a small working example where possible.
- Other members ask “why?”, “what if?”, and “how would this fail?” questions.
- We discuss trade-offs and real production scenarios.
- We capture key learnings, unresolved questions, and next steps.

Teaching is part of the learning process. If you cannot explain a concept clearly yet, that is useful feedback—not a reason to avoid presenting.

### Day 0 discussion questions

Before moving to Day 1, each member should be able to answer:

1. What is the difference between predictive AI and GenAI?
2. What does MLOps manage, and what additional concerns does LLMOps introduce?
3. Which of my current DevOps/Cloud skills transfer directly?
4. Which ML or LLM concepts do I need to learn first?
5. What small project would help me demonstrate these skills?

---

## 7. Suggested first milestone

Build a small, end-to-end learning project in stages:

1. **MLOps baseline:** train and track a simple model with MLflow.
2. **Reliable delivery:** test, package, deploy, and monitor the prediction service.
3. **LLM application:** add a small LLM-backed feature with versioned prompts.
4. **RAG:** connect the application to a controlled document collection.
5. **LLMOps:** add evaluation, tracing, security controls, and regression checks.
6. **Production readiness:** document deployment, monitoring, cost, failure handling, and rollback.

We will keep the scope manageable and expand it as our understanding improves.

## The principle

> **Learn it. Build it. Explain it. Test it. Operate it. Improve it.**

Our goal is not to collect AI buzzwords. It is to become engineers who can build and operate useful AI systems reliably in production.
