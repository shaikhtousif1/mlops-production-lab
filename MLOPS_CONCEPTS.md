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

# End-to-End Business Flow — Why We Are Doing MLOps

## 1. The business problem

This project simulates a subscription/telecom/SaaS business that wants to predict **customer churn**.

Customers generate activity through systems such as CRM, billing, support, and product analytics. The business wants to identify customers who are likely to leave **before they churn**, so that a retention team or business workflow can intervene.

The important point is:

> **The ML model is not the business application. It is one decision-support component inside a larger business process.**

A simplified flow is:

Customer activity
→ customer data
→ churn model
→ churn prediction
→ business rules
→ retention action
→ customer outcome.

For example:

```text
Customer
   ↓
CRM / Billing / Support / Product Analytics
   ↓
Churn prediction service
   ↓
Churn probability = 0.87
   ↓
Business rules
   ↓
Create retention task / offer / support intervention
   ↓
Customer stays or churns
```

### Key principle

**ML predicts. Business logic decides.**

The model might say that a customer has a high probability of churn. A separate business layer can decide whether that customer qualifies for an offer, whether a retention agent should contact them, or whether no action should be taken.

---

## 2. Where our training data fits

The repository contains data/customers.csv.

That file represents a much larger enterprise data platform.

In a real organization:

```text
CRM
Billing
Support
Product Analytics
       ↓
Data pipelines
       ↓
Data lake / warehouse
       ↓
Curated ML training dataset
       ↓
MLOps training pipeline
```

The training dataset is therefore not normally created manually by the ML engineer. Data engineering and business systems produce the source data, while the ML lifecycle consumes a controlled dataset.

Our dataset version v2 is a simplified representation of that production concept.

---

## 3. What happens when new customer data arrives?

Customer data is generated continuously.

For example:

```text
Monday
  Customer A uses the product
  Customer B opens support tickets

Tuesday
  Customer A's usage decreases
  Customer B opens another ticket
  Customer C changes subscription

Wednesday
  More customer activity...
```

That information eventually becomes part of the organization's data platform.

A future training cycle might therefore consume:

```text
Operational data
      ↓
Data pipelines
      ↓
Curated dataset v3
      ↓
Data validation
      ↓
Training
```

The important MLOps requirement is that the training dataset must be identifiable. We need to know which data produced a particular model.

---

## 4. Why do we retrain?

A model is trained using historical behavior, but the business changes.

Examples:

- customer behavior changes
- pricing changes
- a new product is launched
- competitors change their offers
- support processes change
- the relationship between usage and churn changes

Therefore:

```text
Historical data
      ↓
Model
      ↓
Business changes
      ↓
Model may become less effective
      ↓
New data
      ↓
Retraining
      ↓
New candidate model
```

Retraining can be triggered by a schedule, new data, drift, degraded performance, a business event, or a manual request.

A trigger to retrain is **not automatically authorization to deploy**.

---

## 5. What MLflow is doing in the business lifecycle

MLflow gives us the system of record for the ML experiment/model lifecycle.

Our flow is:

```text
Training
   ↓
MLflow Run
   ├── Parameters
   ├── Metrics
   ├── Dataset lineage
   ├── Tags
   └── Model artifact
   ↓
Model selection
   ↓
MLflow Model Registry
   ↓
Production alias
```

The persistent architecture in this project is:

```text
Supabase PostgreSQL
    ↓
MLflow tracking metadata + Model Registry

Supabase Storage
    ↓
S3-compatible API
    ↓
MLflow artifacts
```

This lets us answer questions such as:

- What data trained this model?
- What parameters were used?
- What metrics did it achieve?
- Which training run produced it?
- Which registered model version is it?
- Which model is currently authorized for production?

---

## 6. From experiment to production

Training can produce many candidates.

For example:

```text
Run 101 → F1 0.58
Run 102 → F1 0.62
Run 103 → F1 0.60
Run 104 → F1 0.57
```

We should not simply deploy the latest run.

Our model-selection policy chooses candidates using deterministic criteria and applies a quality gate.

Current policy includes:

```text
mean CV F1 >= 0.60
test F1    >= 0.60
recall     >= 0.60
```

This demonstrates an important production principle:

> **A training result is not automatically a production model.**

The lifecycle is:

```text
Candidate
   ↓
Evaluate
   ↓
Quality gate
   ↓
Register
   ↓
Promote
```

---

## 7. Registry versus production

The MLflow registry may contain:

```text
customer-churn-model
   ├── Version 1
   ├── Version 2
   ├── Version 3
   ├── Version 4
   └── Version 5
```

The production alias points to the version authorized for production:

```text
production → Version 5
```

Later it can move:

```text
production → Version 6
```

This gives us two different concepts:

**Registry:** What model versions exist?

**Promotion:** Which validated version is authorized for production?

---

## 8. How the API is actually used

FastAPI is the model-serving component.

It is not the entire customer application.

A real production request might look like:

```text
Website / Mobile App / CRM
          ↓
Business or decision service
          ↓
Model prediction API
          ↓
Churn model
          ↓
Prediction
          ↓
Business rules
          ↓
Customer action
```

Our API exposes the prediction endpoint, but an enterprise application could call it as part of a larger workflow.

For example:

```text
POST /predict
        ↓
Churn prediction
        ↓
High-risk customer?
        ↓
Yes
        ↓
Eligible for retention workflow?
        ↓
Yes
        ↓
Create CRM task
```

This is why the API is valuable: it makes the model consumable by other software.

---

## 9. What happens after the prediction?

Suppose the model produces:

```text
Customer A
Prediction at T0 = high churn risk
```

At T0, we do not necessarily know the true outcome.

The actual outcome might only become available 30 days later:

```text
T0
Prediction = churn

        ↓

T+30 days
Actual outcome = churn
```

This is called **delayed ground truth**.

Production ML monitoring therefore needs to connect:

```text
Prediction logs
      +
Business outcomes
      ↓
Ground-truth dataset
      ↓
Actual model performance
```

This is one of the major differences between ML monitoring and ordinary application monitoring.

---

## 10. Monitoring is not just Kubernetes health

A model API can be completely healthy from an infrastructure perspective:

```text
HTTP 200
Low latency
No crashes
Healthy pod
```

while the model is producing poor business decisions.

Therefore ML monitoring has several layers:

| Layer | Examples |
|---|---|
| System | latency, errors, availability |
| Data | schema, missing values, feature distributions |
| Model | prediction distribution, score distribution, realized F1/recall |
| Business | churn rate, retention success, revenue/customer impact |

Our monitor.py demonstrates lightweight batch monitoring using feature-distribution PSI and prediction-rate delta. It intentionally does not automatically retrain.

---

## 11. The complete business → MLOps → business loop

```text
                     BUSINESS
                         ↓
                 Customer activity
                         ↓
              CRM / Billing / Support
               / Product Analytics
                         ↓
                   Data Platform
                         ↓
                 Training Dataset
                         ↓
                    MLOps
                         ↓
       Validate → Train → Evaluate
                         ↓
                  Quality Gate
                         ↓
                 MLflow Registry
                         ↓
                 Production Alias
                         ↓
                  Exact Model
                         ↓
                    Packaging
                         ↓
               Application Image
                         ↓
                 Kubernetes / API
                         ↓
                Business Application
                         ↓
                    Prediction
                         ↓
                 Business Decision
                         ↓
                  Customer Action
                         ↓
                  Customer Outcome
                         ↓
                  Actual Ground Truth
                         ↓
                 Monitoring / Evaluation
                         ↓
                Retrain when required
                         ↓
                   New Candidate
                         ↓
                    MLOps again
```

This is the core MLOps mental model.

---

## 12. Repository mapping

| Business / ML concept | Repository implementation |
|---|---|
| Customer activity / source data | data/customers.csv |
| Training dataset | Dataset v2 |
| Data validation | validate_data.py |
| Model training | src/train.py |
| Experiment tracking | MLflow |
| Persistent MLflow metadata | Supabase PostgreSQL |
| MLflow artifacts | Supabase Storage / S3-compatible API |
| Model evaluation | Accuracy, Precision, Recall, F1, ROC-AUC |
| Model selection policy | src/select_model.py |
| Quality gate | src/select_model.py |
| Model registry | MLflow Model Registry |
| Production authorization | production alias |
| Exact promoted model | src/package_model.py |
| Packaged release | Hugging Face |
| Model serving | FastAPI |
| Application artifact | Docker image |
| Image registry | GHCR |
| Desired deployment state | Git |
| Reconciliation | Flux |
| Runtime | Kubernetes |
| Drift monitoring | src/monitor.py |
| Model rollback | src/rollback_model.py |
| Deployment rollback | GitOps rollback |

---

## 13. Why this is MLOps

The project has evolved from:

```text
train model → expose API
```

into:

```text
Business problem
      ↓
Data
      ↓
Reproducible training
      ↓
Evaluation
      ↓
Model selection
      ↓
MLflow tracking
      ↓
Model registry
      ↓
Promotion
      ↓
Packaging
      ↓
Deployment
      ↓
Serving
      ↓
Monitoring
      ↓
Ground truth
      ↓
Retraining
      ↓
New model
```

MLOps exists to make this loop **reproducible, traceable, observable, governed, and safe to operate in production**.

---

## 14. Bridge to LLMOps

Classical MLOps often centers on a trained model:

```text
Historical data
      ↓
Train model
      ↓
Evaluate
      ↓
Deploy
      ↓
Predict
      ↓
Collect outcomes
      ↓
Retrain
```

LLMOps often centers on an application built around a foundation model:

```text
Business problem
      ↓
LLM application
      ├── Foundation model
      ├── System prompt
      ├── User input
      ├── Company knowledge
      ├── Retrieval
      ├── Tools
      └── Guardrails
      ↓
Response
      ↓
Business workflow
      ↓
Evaluation / feedback
      ↓
Observability
```

The central production artifact therefore expands from **the trained model** to **the application plus model, prompts, context, tools, evaluation, and guardrails**.

This is the conceptual bridge from this MLOps lab into the LLMOps/FDE phase.
