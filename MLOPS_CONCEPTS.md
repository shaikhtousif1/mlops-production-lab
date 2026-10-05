# MLOps Concepts — Production Mental Model

## Lifecycle
Data → Training → Evaluation → Quality Gate → Registry → Promotion → Packaging → Deployment → Monitoring → Feedback/Retraining.

Deployment is not the end of an ML lifecycle.

## Reproducibility and lineage
A production model should be traceable through:
dataset version + code version + training parameters + training run → model version → release → serving artifact.

This repository records dataset lineage in MLflow, training parameters/metrics in MLflow, model version/run ID in release metadata, and the application build with Git SHA.

## Registry vs promotion
A model version is an immutable registered artifact identity. The production alias is a movable authorization pointer.

Quality gate asks: “Is this candidate good enough?”
Promotion asks: “Which validated model is authorized for production?”

A mature system should compare a candidate with the current production baseline, not only absolute thresholds.

## Continuous Training
CT is not simply scheduled retraining. A useful loop is:
new data → validate → train → evaluate → compare with production → promote only if policy passes.

Triggers can be scheduled, data-driven, drift-driven, business-driven, or manual. A trigger is not authorization to deploy.

## Drift
- Data drift: input distributions change.
- Concept drift: the relationship between features and target changes.
- Prediction drift: model output distribution changes.

Drift is a signal, not proof of model failure.

`src/monitor.py` demonstrates infrastructure-free batch monitoring using PSI for numeric feature distributions and prediction-rate delta. It deliberately does not auto-retrain.

## Monitoring
ML monitoring has several dimensions:

System: latency, errors, availability.
Data: schema, missing values, feature distributions.
Model: prediction distributions, confidence/score distributions, realized performance.
Business: outcome rates and business impact.

A healthy HTTP endpoint can still be serving a bad model.

## Delayed ground truth
Production performance often requires joining predictions made at T0 with outcomes available at T+7/T+30. This makes ML monitoring fundamentally different from ordinary application health monitoring.

## Rollback
Two rollback planes exist.

Model rollback:
production alias v5 → v4.

Application/GitOps rollback:
Git desired state → previous image → Flux → Kubernetes.

They solve different failures. `src/rollback_model.py` demonstrates the model rollback operation.

## Lineage question
The operational question is:
Why is this exact model running here?

The desired chain is:
dataset → MLflow run → model version → production alias → packaged release → Git SHA → image → GitOps commit → Kubernetes.

## Transition to LLMOps
Classical MLOps often centers on training a model.
LLMOps often centers on operating an application around a foundation model:

foundation model + system prompt + user input + retrieval/tool context → LLM application → evaluation → observability → feedback.

New first-class artifacts include prompts, model/provider configuration, retrieval configuration, embeddings/vector indexes, evaluation datasets, guardrail policies, tool definitions, traces, and token/cost metrics.