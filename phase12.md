# PHASE 12 — Explainability, Interpretability & Decision Evidence

## 1. Purpose

Phase 11 answered:

> **"Which model performed better, and at what cost?"**

Phase 12 answers:

> **"Why did the model make this prediction, and what information influenced it?"**

This is particularly important because our problem statement explicitly asks for:

* model explainability
* interpretable results
* transparent disease-detection predictions

The goal is **not** to make the quantum circuit magically understandable.

The goal is to build an **evidence layer around the complete hybrid pipeline**.

---

# 2. Position in the System

```text
PHASE 1
Ingestion
   ↓
PHASE 2
Profiling
   ↓
PHASE 3
Validation
   ↓
PHASE 4
Preprocessing
   ↓
PHASE 5
Feature Engineering
   ↓
PHASE 6
Feature Selection / Reduction
   ↓
       ┌───────────────┐
       ↓               ↓
   PHASE 7         PHASE 8
   Classical       Quantum
       ↓               ↓
       └───────┬───────┘
               ↓
            PHASE 9
      Experiment Planning
               ↓
            PHASE 10
          Execution
               ↓
            PHASE 11
       Benchmarking
               ↓
┌─────────────────────────────────┐
│ PHASE 12                        │
│ EXPLAINABILITY & INTERPRETATION │
└────────────────┬────────────────┘
                 ↓
             PHASE 13
       Cost & Scalability
```

---

# 3. Important Concept

We have several different levels of explanation.

```text
RAW INPUT
   ↓
PREPROCESSING
   ↓
FEATURES
   ↓
SELECTED FEATURES
   ↓
QUANTUM ENCODING
   ↓
QUANTUM CIRCUIT
   ↓
PREDICTION
```

We need to be able to explain **different parts of this chain**.

---

# 4. Four Levels of Explainability

Our platform should provide:

### Level 1 — Dataset explanation

> What data was used?

### Level 2 — Feature explanation

> Which features mattered?

### Level 3 — Model explanation

> What influenced the prediction?

### Level 4 — Pipeline explanation

> What steps produced this prediction?

This fourth level is especially important for our platform.

---

# 5. Example

Suppose:

```text
Patient
   ↓
12 selected features
   ↓
Quantum representation
   ↓
VQC
   ↓
Prediction:
High Risk
```

The user should be able to see:

```text
Prediction:
High Risk

Important contributing features:
Feature A
Feature B
Feature F

Model:
VQC

Quantum configuration:
8 qubits
2 layers

Dataset:
DS-000001

Experiment:
EXP-Q-001
```

---

# 6. Module 12.1 — Prediction Explanation

Every prediction gets an explanation object.

Example:

```json
{
  "prediction": "positive",

  "score": 0.87,

  "experiment_id": "EXP-Q-001",

  "model": "VQC",

  "important_features": [
    {
      "feature": "feature_07",
      "importance": 0.31
    },
    {
      "feature": "feature_02",
      "importance": 0.24
    }
  ]
}
```

---

# 7. Important Medical Distinction

We should **not** say:

> "Feature A caused the disease."

Instead:

> "Feature A contributed strongly to the model's prediction."

This is a machine-learning explanation, not a causal medical conclusion.

---

# 8. Module 12.2 — Classical Explainability

For classical models we can use model-appropriate methods.

Examples:

```text
Logistic Regression
→ coefficients

Decision Tree
→ tree paths

Random Forest
→ feature importance / permutation importance

XGBoost
→ feature importance / SHAP

SVM
→ permutation / SHAP where appropriate
```

---

# 9. SHAP

For compatible models, SHAP can provide:

```text
feature
+
direction
+
magnitude
```

Example:

```text
Feature A
██████████
+0.31

Feature B
██████
+0.18

Feature C
████
-0.12
```

This tells us which features pushed the prediction toward or away from a class.

---

# 10. Module 12.3 — Quantum Explainability

This requires more care.

We should **not pretend that a VQC has ordinary feature importance in exactly the same sense as XGBoost**.

Instead, we can use model-agnostic or circuit-aware methods.

Potential methods include:

```text
Feature perturbation
Permutation importance
Sensitivity analysis
Gradient-based analysis
Input ablation
Circuit parameter analysis
```

---

# 11. Feature Perturbation

Suppose the original input is:

```text
F1 = 0.72
F2 = 0.31
F3 = 0.84
```

Run the model:

```text
Prediction score = 0.87
```

Now perturb F1:

```text
F1 = 0.72
→ 0.62
```

Run again:

```text
Score = 0.76
```

Difference:

```text
0.87 → 0.76
```

This suggests F1 strongly influences the prediction.

---

# 12. Feature Ablation

Another approach:

```text
All features
   ↓
Prediction = 0.87
```

Remove F1:

```text
Without F1
   ↓
Prediction = 0.68
```

Remove F2:

```text
Without F2
   ↓
Prediction = 0.83
```

Therefore:

```text
F1
→ stronger observed influence

F2
→ weaker observed influence
```

---

# 13. Why This Is Useful for QML

It allows us to answer:

> "The quantum model is not a black box that simply outputs 0.87."

Instead:

```text
Input features
      ↓
Feature perturbation
      ↓
Change in quantum model output
      ↓
Importance estimate
```

---

# 14. Module 12.4 — Quantum Circuit Explanation

The platform should expose the circuit itself.

Example:

```text
Input
 ↓
Angle Encoding
 ↓
┌───┐     ┌─────────┐
│RX │─────│ RY      │
└───┘     └─────────┘
    \       /
     ───────
       ↓
   Measurement
```

The UI can show:

```text
Qubits:
8

Layers:
2

Encoding:
Angle Encoding

Measurements:
Z expectation
```

This makes the quantum component inspectable.

---

# 15. Circuit Metrics

For every quantum model:

```text
Number of qubits
Circuit depth
Gate count
Two-qubit gate count
Parameters
Measurements
Shots
```

These should appear in the explanation panel.

---

# 16. Module 12.5 — Pipeline Trace

This is one of the most important features of our whole platform.

Suppose the user gets:

```text
Prediction:
Disease Positive
```

They can click:

> **"How was this prediction produced?"**

and see:

```text
INPUT
↓
Dataset: DS-000001
↓
Preprocessing: PREP-000001
↓
Feature Engineering: FE-000002
↓
Feature Selection: FS-000001
↓
Representation: QREP-001
↓
Quantum Model: VQC
↓
Experiment: EXP-Q-001
↓
Prediction
```

---

# 17. This Connects All Phases

This is why we built versioning earlier.

```text
Dataset
   ↓
Version
   ↓
Pipeline
   ↓
Representation
   ↓
Model
   ↓
Experiment
   ↓
Prediction
```

The user can trace the complete lineage.

---

# 18. Module 12.6 — Decision Trace

We should also explain **why the platform selected a model**.

For example:

```text
Why was VQC selected?

✓ Binary classification
✓ 8-dimensional representation
✓ Compatible with 8 qubits
✓ Local simulator available
✓ Resource budget satisfied
```

This comes from Phase 9.

So:

```text
Phase 9
Decision reasoning
       ↓
Phase 12
Explanation display
```

---

# 19. Example

User uploads dataset.

System selects:

```text
VQC
```

User asks:

> Why VQC?

System shows:

```text
Reason:

1. Task = binary classification
2. Selected representation = 8 features
3. Quantum candidate supports 8 qubits
4. Estimated memory = 1.4 GB
5. Available memory = 8 GB
6. Experiment priority = P0
```

This is much better than:

> "AI selected VQC."

---

# 20. Module 12.7 — Confidence Information

The platform can display:

```text
Prediction:
Positive

Raw score:
0.87

Confidence:
High
```

But we need to define carefully what "confidence" means.

If the model outputs an uncalibrated score, we should label it:

```text
Model score:
0.87
```

rather than:

```text
87% probability of disease
```

unless calibration has been established.

---

# 21. Calibration

Where appropriate:

```text
Raw model score
      ↓
Calibration
      ↓
Calibrated probability
```

Possible approaches:

```text
Platt scaling
Isotonic regression
```

The chosen method and calibration dataset must be recorded.

---

# 22. Module 12.8 — Global Explainability

Prediction explanations answer:

> "Why this particular sample?"

Global explanations answer:

> "What does the model generally rely on?"

Example:

```text
Top features across test dataset:

Feature A
Feature F
Feature B
Feature D
```

This can be visualized as:

```text
Feature A ███████████
Feature F █████████
Feature B ███████
Feature D █████
```

---

# 23. Local vs Global

Our UI should explicitly separate:

### Local explanation

```text
This patient/sample
```

### Global explanation

```text
Entire evaluation dataset
```

This prevents users from confusing a single prediction with general model behavior.

---

# 24. Module 12.9 — Error Explanation

Explainability should not only explain correct predictions.

Suppose:

```text
Actual:
Positive

Predicted:
Negative
```

The system should show:

```text
FALSE NEGATIVE
```

and allow inspection of:

```text
important features
model score
nearest comparable samples
```

where appropriate.

---

# 25. Why False Negatives Matter

For disease screening:

```text
False Negative
```

can be particularly important.

Therefore the dashboard should explicitly track:

```text
TP
TN
FP
FN
```

and highlight the model's false-negative behavior.

---

# 26. Module 12.10 — Counterfactual Explanation

Where scientifically appropriate, we can ask:

> "What input changes would alter the model's prediction?"

Example:

```text
Current:
Risk score = 0.72
Prediction = Positive
```

A counterfactual might identify:

```text
If Feature A changed from X to Y
AND
Feature B changed from P to Q

prediction would change.
```

But this must be presented carefully.

It does **not** mean:

> "Changing Feature A will cure the disease."

It means:

> "Under the model, this input configuration changes the prediction."

---

# 27. Module 12.11 — Explainability for Images

If we use a medical-imaging dataset such as skin cancer images, our architecture should support visual explanations.

For a CNN:

```text
Image
 ↓
CNN
 ↓
Prediction
```

we can use methods such as:

```text
Grad-CAM
```

to produce:

```text
Original image
+
heatmap
```

showing regions that influenced the model.

---

# 28. Hybrid Image + Quantum Pipeline

This connects directly to the skin-cancer architecture we discussed earlier.

For example:

```text
Skin Image
     ↓
MobileNetV2
     ↓
1280-dimensional embedding
     ↓
Feature Reduction
     ↓
8 quantum features
     ↓
VQC
     ↓
Prediction
```

Explainability can happen at multiple points:

```text
Image level
→ Grad-CAM

Feature level
→ feature importance / perturbation

Quantum level
→ circuit / parameter / sensitivity analysis
```

This is a very strong demonstration of the hybrid architecture.

---

# 29. Example

Suppose the system predicts:

```text
Malignant
Score = 0.91
```

The UI could show:

```text
┌──────────────────────────────┐
│ PREDICTION                   │
│                              │
│ Malignant                    │
│ Model score: 0.91            │
│                              │
│ Image evidence               │
│ [ Grad-CAM visualization ]    │
│                              │
│ Quantum features             │
│ F3 █████████                  │
│ F7 ███████                    │
│ F2 █████                      │
│                              │
│ Model                         │
│ VQC • 8 qubits • 2 layers    │
└──────────────────────────────┘
```

---

# 30. Module 12.12 — Explanation Confidence / Reliability

We should distinguish:

```text
Model prediction
```

from:

```text
Explanation reliability
```

For example, a perturbation-based explanation may be unstable.

Therefore we can evaluate explanation stability by repeating the explanation process.

Example:

```text
Run 1:
F1, F3, F7

Run 2:
F1, F3, F7

Run 3:
F1, F7, F3
```

This is more reassuring than a one-off importance calculation.

---

# 31. Module 12.13 — Explanation Report

Each experiment can produce:

```text
explainability/
│
├── global_importance.json
├── local_explanations.json
├── feature_perturbation.csv
├── circuit_diagram.png
├── circuit_metrics.json
├── error_analysis.json
└── explanation_report.html
```

---

# 32. Example Local Explanation Object

```json
{
  "sample_id": "PATIENT-001",

  "prediction": "positive",

  "model_score": 0.87,

  "top_features": [
    {
      "feature": "feature_07",
      "effect": "positive",
      "importance": 0.31
    },
    {
      "feature": "feature_02",
      "effect": "positive",
      "importance": 0.24
    },
    {
      "feature": "feature_04",
      "effect": "negative",
      "importance": -0.12
    }
  ],

  "experiment_id": "EXP-Q-001"
}
```

---

# 33. Module 12.14 — Explain the Hybrid Architecture

The platform should explicitly show where quantum fits.

For example:

```text
Image
 ↓
CNN
 ↓
Feature Extraction
 ↓
Feature Selection
 ↓
Quantum Encoding
 ↓
VQC
 ↓
Prediction
```

And show:

```text
Classical components:
CNN
PCA
Feature Selection

Quantum component:
VQC

Classical output:
Prediction
```

This helps judges immediately understand:

> Quantum is not replacing the whole ML pipeline.

---

# 34. This Connects to Our Earlier Skin-Cancer Research

Remember the architecture we discussed:

```text
Skin image
      ↓
MobileNetV2
      ↓
Feature extraction
      ↓
Hybrid Quantum CNN
      ↓
BiLSTM
      ↓
Classification
```

Our platform can generalize the idea.

Instead of hardcoding:

```text
MobileNetV2
```

we can support:

```text
Feature Extractor Registry
```

with models such as:

```text
MobileNetV2
ResNet
EfficientNet
```

and then:

```text
Feature Reduction
      ↓
Quantum Model
```

This makes the platform much more reusable.

---

# 35. Module 12.15 — Explain Model Selection

The user can see:

```text
MODEL SELECTION
```

Example:

```text
Dataset:
Skin Cancer

Task:
Binary Classification

Selected:
VQC

Alternatives evaluated:
XGBoost
SVM
Quantum Kernel

Reason:
8-feature representation
+
binary task
+
resource budget
```

This connects:

```text
Phase 9
```

to:

```text
Phase 12
```

---

# 36. Explainability Dashboard

I recommend four tabs:

```text
┌──────────────────────────────────────────┐
│ EXPLAINABILITY                            │
├──────────┬──────────┬──────────┬─────────┤
│ Prediction│ Features │ Circuit │ Pipeline│
└──────────┴──────────┴──────────┴─────────┘
```

---

# 37. Tab 1 — Prediction

Shows:

```text
Prediction
Model score
Input
Experiment
Timestamp
```

---

# 38. Tab 2 — Features

Shows:

```text
Global feature importance
Local feature importance
Perturbation results
Feature direction
```

---

# 39. Tab 3 — Quantum Circuit

Shows:

```text
Circuit diagram
Qubits
Layers
Gates
Parameters
Shots
Backend
```

---

# 40. Tab 4 — Pipeline

Shows:

```text
Dataset
 ↓
Preprocessing
 ↓
Feature Engineering
 ↓
Feature Selection
 ↓
Quantum Encoding
 ↓
Quantum Model
 ↓
Prediction
```

with clickable components.

---

# 41. Full Explainability Example

Suppose:

```text
Input:
Skin image

Prediction:
Malignant

Score:
0.91
```

Click:

> Explain.

The system shows:

```text
IMAGE EVIDENCE
      ↓
Grad-CAM highlights lesion region

      ↓

FEATURE EVIDENCE
      ↓
Feature 3 strongly influenced prediction
Feature 7 strongly influenced prediction

      ↓

QUANTUM MODEL
      ↓
8 qubits
2 layers
Angle encoding

      ↓

EXPERIMENT
      ↓
EXP-Q-001

      ↓

DATASET
      ↓
DS-000001
```

That's a complete explanation chain.

---

# 42. What Phase 12 Does NOT Do

It does **not**:

* prove causality
* prove clinical validity
* claim a model is medically trustworthy just because it is explainable
* guarantee that an explanation is the true internal causal mechanism
* replace expert medical interpretation

It provides:

> **model behavior evidence and pipeline transparency.**

---

# 43. Phase 12 Output

Main output:

```text
EXPLANATION PACKAGE
```

Containing:

```text
Prediction explanation
Feature importance
Circuit explanation
Pipeline lineage
Error analysis
Global explanation
Local explanation
Explanation metadata
```

---

# 44. Phase 12 Success Criteria

Phase 12 is complete when we can:

* [ ] Explain individual predictions
* [ ] Explain global model behavior
* [ ] Provide feature importance
* [ ] Support SHAP for compatible classical models
* [ ] Support perturbation-based quantum explanations
* [ ] Support feature ablation
* [ ] Display quantum circuit structure
* [ ] Display quantum resource configuration
* [ ] Show complete pipeline lineage
* [ ] Explain model-selection decisions
* [ ] Analyze false positives
* [ ] Analyze false negatives
* [ ] Support image-level explanation where applicable
* [ ] Distinguish raw scores from calibrated probabilities
* [ ] Store explanation artifacts
* [ ] Generate explanation reports

---

# 45. Updated Architecture

```text
                         DATASET
                            ↓
                       PHASE 1
                       INGESTION
                            ↓
                       PHASE 2
                       PROFILING
                            ↓
                       PHASE 3
                      VALIDATION
                            ↓
                       PHASE 4
                    PREPROCESSING
                            ↓
                       PHASE 5
                 FEATURE ENGINEERING
                            ↓
                       PHASE 6
                FEATURE REDUCTION
                            ↓
              ┌─────────────┴─────────────┐
              ↓                           ↓
          PHASE 7                     PHASE 8
        CLASSICAL                     QUANTUM
        CANDIDATES                   CANDIDATES
              │                           │
              └─────────────┬─────────────┘
                            ↓
                       PHASE 9
                 EXPERIMENT PLANNING
                            ↓
                       PHASE 10
                     EXECUTION
                            ↓
                       PHASE 11
                    BENCHMARKING
                            ↓
                       PHASE 12
                   EXPLAINABILITY
                            ↓
                       PHASE 13
                  COST & SCALABILITY
```

## The key idea

Our platform now has three separate questions:

```text
PHASE 9
"What should we run?"

        ↓

PHASE 10
"Can we run it correctly?"

        ↓

PHASE 11
"How did it perform?"

        ↓

PHASE 12
"Why did it behave that way?"
```

That separation is important for the SIH solution because it makes the platform **not just a QML demo**, but a traceable hybrid ML experimentation system.
