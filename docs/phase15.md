# PHASE 15 — Deployment, Demonstration & SIH Evaluation Readiness

Phase 14 gave us the **complete integrated platform**.

Phase 15 is the final engineering phase:

> **Make the system stable, deployable, demonstrable, and ready to be evaluated by SIH judges.**

This is where we move from:

```text
"It works on our machine"
```

to:

```text
"It can be demonstrated reliably from start to finish."
```

---

# 1. Position in the System

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
Feature Reduction
   ↓
PHASE 7        PHASE 8
Classical      Quantum
   ↓              ↓
   └──────┬───────┘
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
       PHASE 12
   Explainability
          ↓
       PHASE 13
 Cost & Scalability
          ↓
       PHASE 14
 Integration & QA
          ↓
┌──────────────────────────────┐
│ PHASE 15                     │
│ DEPLOYMENT & SIH READINESS   │
└──────────────┬───────────────┘
               ↓
          FINAL DEMO
```

---

# 2. What Phase 15 Must Answer

At the end, a judge should be able to ask:

### "What does your system do?"

We answer:

> It takes biomedical data, constructs controlled classical and hybrid quantum-classical experiments, evaluates them under the same conditions, explains the predictions, measures computational cost, and reports whether the quantum component provides an observed benefit.

---

### "Can you demonstrate it?"

Yes.

```text
Upload
 ↓
Analyze
 ↓
Experiment
 ↓
Compare
 ↓
Explain
 ↓
Report
```

---

### "Is this actually QML?"

Yes.

The platform contains:

```text
Quantum encoding
+
Parameterized quantum circuits / quantum kernels
+
Quantum execution
+
Quantum-specific resource measurements
```

---

### "Did quantum actually beat classical?"

The system doesn't assume that.

It produces:

```text
Quantum advantage
OR
Parity
OR
Trade-off
OR
Classical advantage
```

based on measured experiments.

---

# 3. Phase 15 Architecture

```text
                    DEPLOYMENT
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       Frontend      Backend       Storage
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                    Scheduler
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
        Classical              Quantum
         Worker                 Worker
             │                     │
             └──────────┬──────────┘
                        ↓
                  Result Store
                        ↓
                  Report Engine
                        ↓
                   Final Demo
```

---

# 4. Module 15.1 — Environment Packaging

Our first goal is:

> Anyone on the team should be able to reproduce the environment.

Record:

```text
Python version
Package versions
Quantum SDK
ML libraries
Frontend dependencies
Backend dependencies
OS assumptions
```

Create:

```text
requirements.txt
```

or an equivalent locked environment specification.

---

# 5. Module 15.2 — Configuration Management

Do **not** hardcode things like:

```text
dataset path
model path
backend
number of qubits
shots
```

Instead:

```text
config/
    system.yaml
    datasets.yaml
    models.yaml
    backends.yaml
    experiments.yaml
```

Example:

```yaml
backend:
  type: local_simulator

quantum:
  shots: 1024
  max_qubits: 8
```

---

# 6. Why This Matters

Tomorrow we change:

```text
8 qubits
```

to:

```text
12 qubits
```

We shouldn't need to edit five different Python files.

We change the configuration.

---

# 7. Module 15.3 — Secrets & Credentials

If later using cloud services:

```text
API keys
tokens
credentials
```

must **never** be committed to Git.

Use:

```text
.env
environment variables
secret manager
```

For our local SIH prototype:

```text
LOCAL SIMULATOR
```

can avoid external credentials completely.

---

# 8. Module 15.4 — Containerization

The final platform should ideally be runnable with:

```text
Docker
```

Conceptually:

```text
┌──────────────────────────────┐
│       QML PLATFORM           │
│                              │
│ Frontend                     │
│ Backend                      │
│ ML dependencies              │
│ QML dependencies             │
│ Quantum simulator            │
└──────────────────────────────┘
```

This reduces:

> "It works on my laptop."

---

# 9. Module 15.5 — One-Command Startup

For the demo, we want something close to:

```text
docker compose up
```

or a project-specific startup command.

Then:

```text
Browser
   ↓
Platform
```

This is much better than explaining:

```text
Open terminal 1
Run Python
Open terminal 2
Run FastAPI
Open terminal 3
Run worker
Open terminal 4
Run simulator
...
```

---

# 10. Module 15.6 — Demo Dataset

We should have a **known, prepared demonstration dataset**.

Example:

```text
demo/
    skin_cancer/
        images/
        labels.csv
        metadata.json
```

The demo dataset should be:

```text
small
public
legal to distribute/use
stable
fast
```

---

# 11. Why Not Use the Full Dataset During the Live Demo?

Because:

```text
full dataset
+
quantum training
```

could take too long.

Instead:

```text
LIVE DEMO
→ small controlled dataset

OFFLINE BENCHMARK
→ full prescribed dataset
```

This distinction should be clearly displayed.

---

# 12. Module 15.7 — Demo Mode

Add:

```text
DEMO MODE
```

to the platform.

Example:

```text
Execution Mode:

○ Development
● Demo
○ Benchmark
○ Hardware
```

---

# 13. Demo Mode

Demo mode can use:

```text
fixed dataset
fixed experiment configuration
fixed seed
prevalidated models
```

This ensures the presentation doesn't fail because of a random training issue.

---

# 14. But Don't Fake the Result

Very important.

Demo mode may use:

```text
precomputed results
```

for speed **only if clearly labelled**.

For example:

```text
Demo Result
Generated from previously completed benchmark experiment.
```

We should never present fabricated live computation as if it happened during the demo.

---

# 15. Module 15.8 — Live vs Cached Result

UI:

```text
RESULT SOURCE

● Live Execution
○ Cached Benchmark
```

If cached:

```text
Experiment:
EXP-Q-001

Status:
Previously completed

Dataset:
DS-000001
```

This is transparent.

---

# 16. Module 15.9 — Demo Script

The entire SIH presentation should follow one story.

### Step 1

Upload dataset.

```text
skin_cancer
```

### Step 2

System profiles it.

```text
3,000 samples
```

### Step 3

System creates representation.

```text
1280 → 8 features
```

### Step 4

System builds:

```text
Classical baseline
+
Quantum model
```

### Step 5

Run experiments.

### Step 6

Compare results.

### Step 7

Explain one prediction.

### Step 8

Show resource usage.

### Step 9

Generate report.

---

# 17. Module 15.10 — The 5-Minute Demo

The ideal live demo should fit roughly into:

```text
00:00
Dataset upload

00:30
Profiling

01:00
Pipeline

01:45
Classical vs quantum

03:00
Benchmark result

04:00
Explainability

04:30
Cost/scalability

05:00
Final conclusion
```

The exact timing can change, but the narrative should remain simple.

---

# 18. Module 15.11 — Demo Narrative

Don't say:

> "We have a quantum neural network."

Instead:

> "Our system first converts the biomedical input into a compact representation that can be processed by a near-term quantum model. We then run the same controlled evaluation against classical baselines."

Then:

> "The system does not assume quantum is better. It measures the difference."

That sentence is central to our project.

---

# 19. Module 15.12 — Judge Question: Why Quantum?

The platform should have an answer ready.

```text
WHY QUANTUM?
```

Answer:

> Biomedical data can be high-dimensional, complex, and noisy. Our platform investigates whether quantum-enhanced representations or learning models can capture useful patterns that provide measurable benefits over classical baselines.

But:

> We treat quantum advantage as an experimental hypothesis, not an assumption.

---

# 20. Judge Question: Why Hybrid?

Answer:

```text
Raw biomedical data
       ↓
Classical preprocessing
       ↓
Feature extraction/reduction
       ↓
Compact quantum representation
       ↓
Quantum model
       ↓
Classical decision/output
```

Because current quantum hardware and simulators have limited resources.

Therefore:

> We use classical computing where it is efficient and reserve the quantum component for the part being experimentally evaluated.

---

# 21. Judge Question: Why Not Pure Quantum?

Answer:

Because current near-term systems face constraints such as:

```text
limited qubits
noise
circuit depth
measurement cost
simulation cost
```

Therefore a fully quantum pipeline is not the practical design target.

---

# 22. Judge Question: How Do You Choose the Number of Qubits?

Our answer:

```text
Feature dimension
       ↓
Reduction
       ↓
Candidate qubit counts
       ↓
Resource feasibility
       ↓
Experiment
       ↓
Benchmark
```

We don't say:

> "8 qubits because 8 sounded good."

We evaluate candidates.

---

# 23. Judge Question: How Do You Choose the Quantum Model?

The platform maintains a model registry.

For example:

```text
Binary classification
        ↓
Quantum candidates
        ├── VQC
        └── Quantum Kernel
```

Then Phase 9 evaluates:

```text
compatibility
+
resource requirements
+
experiment priority
```

and Phase 11 evaluates actual performance.

---

# 24. Judge Question: Is It Agentic?

Our answer should be nuanced.

The core platform **does not need to claim that the entire system is an autonomous agent**.

Instead:

```text
Rule-based / constrained orchestration
```

controls:

```text
dataset validation
model compatibility
experiment construction
execution
resource checks
```

Later we can add an optional intelligent planning layer.

This is much safer than saying:

> "Our LLM decides everything."

---

# 25. Module 15.13 — Optional Agent Layer

If we eventually add one:

```text
                 Controller
                     │
             ┌───────┴────────┐
             ↓                ↓
         Rules Engine       AI Planner
             │                │
             └───────┬────────┘
                     ↓
              Experiment Plan
```

The rules remain the safety boundary.

The AI can suggest:

```text
model
features
experiments
```

but the system validates them before execution.

---

# 26. Module 15.14 — Safety Boundary

The planner cannot directly do:

```text
execute arbitrary code
```

Instead:

```text
Planner
 ↓
Structured experiment configuration
 ↓
Validator
 ↓
Approved configuration
 ↓
Executor
```

This is a critical architecture decision.

---

# 27. Module 15.15 — Benchmark Freeze

Before final SIH submission:

```text
FREEZE BENCHMARK
```

Record:

```text
dataset version
train/test split
models
hyperparameters
seeds
backend
shots
metrics
evaluation protocol
```

After that:

> Don't keep changing the benchmark until you get a preferred result.

Otherwise we risk overfitting our experimental process to the benchmark.

---

# 28. Module 15.16 — Final Benchmark Table

The final report should contain something like:

| Model               | Type      | Accuracy | Recall | Specificity | AUC | Runtime |
| ------------------- | --------- | -------: | -----: | ----------: | --: | ------: |
| Logistic Regression | Classical |        — |      — |           — |   — |       — |
| SVM                 | Classical |        — |      — |           — |   — |       — |
| XGBoost             | Classical |        — |      — |           — |   — |       — |
| VQC                 | Quantum   |        — |      — |           — |   — |       — |
| Quantum Kernel      | Quantum   |        — |      — |           — |   — |       — |

The actual values come from our experiments.

---

# 29. Module 15.17 — Final Evidence Package

We should have:

```text
submission/
│
├── source_code/
├── models/
├── configs/
├── datasets/
├── experiments/
├── benchmark_results/
├── explainability/
├── scalability/
├── reports/
├── screenshots/
├── architecture/
└── README.md
```

---

# 30. Module 15.18 — README

The README should answer:

```text
What is this?
How does it work?
How do I install it?
How do I run it?
What datasets are supported?
What quantum backends are supported?
How are experiments evaluated?
How are classical baselines selected?
How are results reproduced?
```

---

# 31. Module 15.19 — Architecture Documentation

Include:

```text
System architecture
Data flow
Experiment flow
Quantum pipeline
Classical pipeline
Backend architecture
Database schema
API architecture
Explainability architecture
```

---

# 32. Module 15.20 — API Documentation

Useful endpoints could be:

```text
POST /datasets
GET  /datasets/{id}

POST /experiments
GET  /experiments/{id}

POST /experiments/{id}/run
GET  /experiments/{id}/status

GET /experiments/{id}/results
GET /experiments/{id}/explanation
GET /experiments/{id}/resources

POST /benchmarks
GET /benchmarks/{id}

POST /reports
GET /reports/{id}
```

---

# 33. Module 15.21 — Final Validation Checklist

Before declaring the platform ready:

### Data

```text
✓ Upload
✓ Validation
✓ Profiling
✓ Versioning
```

### Classical

```text
✓ Baseline
✓ Training
✓ Inference
✓ Metrics
```

### Quantum

```text
✓ Encoding
✓ Circuit
✓ Training
✓ Inference
✓ Simulator
✓ Resource tracking
```

### Comparison

```text
✓ Same test set
✓ Same metrics
✓ Statistical analysis
✓ Resource comparison
```

### Explainability

```text
✓ Feature explanation
✓ Prediction explanation
✓ Pipeline trace
✓ Circuit visualization
```

### Scalability

```text
✓ Runtime
✓ Memory
✓ Qubit scaling
✓ Dataset scaling
```

---

# 34. Module 15.22 — Failure Testing

Intentionally test:

```text
invalid dataset
missing target
too many features
unsupported model
insufficient RAM
invalid qubit count
failed quantum backend
timeout
corrupted file
```

The platform should gracefully respond.

Example:

```text
❌ Experiment cannot start.

Reason:
Selected representation requires 16 qubits,
but the configured backend allows 8.

Suggested:
Reduce representation to ≤8 dimensions
or select another backend.
```

---

# 35. Module 15.23 — Reproducibility Test

Run:

```text
EXP-Q-001
```

twice under the same simulator configuration.

Compare:

```text
predictions
metrics
training history
```

For stochastic algorithms, we should report expected variation rather than demanding bit-for-bit identity when the stack does not guarantee it.

---

# 36. Module 15.24 — Final Research Claim Validation

Before the presentation, every claim should fall into one of these categories:

```text
OBSERVED
```

Example:

> VQC achieved 93% recall on our evaluated test split.

or:

```text
SUPPORTED BY LITERATURE
```

Example:

> Previous studies have explored hybrid quantum-classical architectures for biomedical classification.

or:

```text
FUTURE WORK
```

Example:

> Future experiments can evaluate the model on real quantum hardware.

Never mix these categories.

---

# 37. Our Final System Should Clearly Separate

```text
WHAT WE BUILT
```

from:

```text
WHAT WE TESTED
```

from:

```text
WHAT WE OBSERVED
```

from:

```text
WHAT WE EXPECT IN FUTURE
```

This will make the SIH presentation much more credible.

---

# 38. Final SIH Demo Architecture

```text
                    USER
                     │
                     ▼
              ┌─────────────┐
              │     GUI     │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │ ORCHESTRATOR│
              └──────┬──────┘
                     │
        ┌────────────┼─────────────┐
        ↓            ↓             ↓
      DATA         MODELS       CONFIG
        │            │             │
        └────────────┼─────────────┘
                     ↓
              EXPERIMENT PLANNER
                     ↓
                 VALIDATOR
                     ↓
                JOB QUEUE
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
   CLASSICAL                  QUANTUM
    WORKER                     WORKER
        │                         │
        │                  ┌──────┼───────┐
        │                  ↓      ↓       ↓
        │               Local   Cloud  Hardware
        │
        └────────────┬────────────┘
                     ↓
                  RESULTS
                     ↓
                BENCHMARK
                     ↓
              EXPLAINABILITY
                     ↓
               COST ANALYSIS
                     ↓
                 REPORT
```

---

# 39. Phase 15 Deliverables

At the end of Phase 15:

```text
1. Deployable application

2. Demo dataset

3. Reproducible experiment configuration

4. Classical baseline results

5. Quantum results

6. Benchmark report

7. Explainability report

8. Cost/scalability report

9. Architecture documentation

10. API documentation

11. Installation guide

12. SIH demonstration workflow

13. Final presentation evidence

14. End-to-end test results
```

---

# 40. Phase 15 Success Criteria

Phase 15 is complete when:

* [ ] A clean machine can reproduce the environment
* [ ] Application starts reliably
* [ ] Demo dataset works
* [ ] End-to-end workflow works
* [ ] Classical experiment works
* [ ] Quantum experiment works
* [ ] Results are reproducible
* [ ] Benchmark is frozen
* [ ] Explainability works
* [ ] Cost analysis works
* [ ] Reports generate correctly
* [ ] Failure cases are handled
* [ ] Documentation is complete
* [ ] Demo can run without manual backend intervention
* [ ] All major claims have supporting evidence

---

# FINAL PROJECT STRUCTURE

After Phase 15, our project is essentially:

```text
                 ┌──────────────────────────┐
                 │       USER / JUDGE       │
                 └────────────┬─────────────┘
                              ↓
                 ┌──────────────────────────┐
                 │       WEB PLATFORM       │
                 └────────────┬─────────────┘
                              ↓
                 ┌──────────────────────────┐
                 │       ORCHESTRATOR       │
                 └────────────┬─────────────┘
                              ↓
          ┌───────────────────┴──────────────────┐
          ↓                                      ↓
   CLASSICAL PIPELINE                     QUANTUM PIPELINE
          │                                      │
          └───────────────────┬──────────────────┘
                              ↓
                    EXPERIMENT EXECUTION
                              ↓
                       BENCHMARKING
                              ↓
                     EXPLAINABILITY
                              ↓
                     COST / SCALING
                              ↓
                       FINAL REPORT
```

## The complete 15-phase project

```text
01  INGESTION
02  PROFILING
03  VALIDATION
04  PREPROCESSING
05  FEATURE ENGINEERING
06  FEATURE SELECTION / REDUCTION

07  CLASSICAL MODEL CANDIDATES
08  QUANTUM MODEL CANDIDATES

09  EXPERIMENT PLANNING
10  TRAINING & EXECUTION
11  BENCHMARKING
12  EXPLAINABILITY
13  COST & SCALABILITY

14  PLATFORM INTEGRATION & QA
15  DEPLOYMENT & SIH READINESS
```

### The actual story of the project is now:

**Data → Understand → Prepare → Represent → Classical/Quantum → Plan → Execute → Compare → Explain → Measure Cost → Integrate → Demonstrate.**

And importantly, **Phase 15 is not another ML phase**. It is where we make the research system we built in Phases 1–14 reliable enough to present as a real software platform rather than a collection of notebooks and experiments.
