# PHASE 13 — Cost, Scalability & Deployment Evaluation

## 1. Purpose

Phase 11 answered:

> **How well does quantum perform compared with classical?**

Phase 12 answered:

> **Why did the model make that prediction?**

Phase 13 answers the final practical question:

> **Can this system actually be used at scale, and what does it cost to operate?**

This phase is important because our SIH problem statement explicitly asks the platform to be:

* scalable
* computationally efficient
* compatible with near-term quantum hardware
* compatible with simulators
* practical for real biomedical datasets

So we should not build a system that says:

> "VQC achieved 93% recall"

and ignores that it took **8 hours and 20 GB RAM** to produce it.

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
       ┌──────────────┐
       ↓              ↓
   PHASE 7        PHASE 8
   Classical       Quantum
   Models          Models
       ↓              ↓
       └───────┬──────┘
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
┌──────────────────────────────────┐
│ PHASE 13                         │
│ COST & SCALABILITY               │
└────────────────┬─────────────────┘
                 ↓
             FINAL PLATFORM
```

---

# 3. What "Cost" Means Here

We should not think only about money.

There are **four different costs**.

```text
                COST
                  │
       ┌──────────┼───────────┐
       ↓          ↓           ↓
Computational   Quantum     Operational
   Cost          Cost          Cost
       │          │           │
       └──────────┴───────────┘
                  ↓
              Financial
                 Cost
```

---

# 4. Computational Cost

Measure:

```text
CPU time
RAM
GPU time
storage
training time
inference time
```

Example:

```text
XGBoost
Training = 42 sec

VQC
Training = 842 sec
```

This difference matters.

---

# 5. Quantum Cost

For quantum models, track:

```text
number of qubits
circuit depth
gate count
two-qubit gates
shots
circuit executions
optimization iterations
```

For example:

```text
VQC

8 qubits
2 layers
1024 shots
19,932 circuit executions
```

This gives us a measurable quantum workload.

---

# 6. Financial Cost

When running locally:

```text
Financial quantum cost ≈ 0
```

because we are using:

```text
local simulator
```

But:

```text
computational cost ≠ 0
```

We still consume:

```text
CPU
RAM
electricity
time
```

This distinction is important.

---

# 7. Cloud Quantum Cost

If later we execute on a cloud quantum service, the cost model changes.

Conceptually:

```text
Cloud Quantum
      ↓
Backend usage
      ↓
Execution workload
      ↓
Provider pricing
```

We should therefore design the system so that:

```text
LOCAL SIMULATOR
       │
       ├─────── same experiment interface
       │
CLOUD SIMULATOR
       │
       ├─────── same experiment interface
       │
REAL QUANTUM HARDWARE
```

The experiment itself should not need to be rewritten.

---

# 8. Module 13.1 — Resource Profiler

During every experiment, record:

```text
CPU utilization
RAM utilization
GPU utilization
training duration
inference duration
storage consumed
```

For quantum:

```text
qubits
shots
circuit executions
circuit depth
gate count
backend
```

---

# 9. Example Resource Report

```text
EXPERIMENT: EXP-Q-001

Model:
VQC

Performance:
AUC = 0.94

Resources:
────────────────────────
Training time     842 sec
Inference         17 sec
RAM               3.2 GB
CPU               82%
Qubits            8
Circuit depth     12
Shots             1024
Circuit executions 19,932
────────────────────────
```

Now Phase 13 has concrete evidence.

---

# 10. Module 13.2 — Scaling by Dataset Size

We should test:

```text
100 samples
250 samples
500 samples
1000 samples
2000 samples
```

and measure:

```text
training time
memory
circuit executions
performance
```

Example:

| Samples | Classical Time | Quantum Time |
| ------: | -------------: | -----------: |
|     100 |          2 sec |       15 sec |
|     500 |          8 sec |       72 sec |
|   1,000 |         15 sec |      145 sec |
|   2,000 |         31 sec |      290 sec |

The exact values will come from our actual experiments.

The important thing is the **growth trend**.

---

# 11. Module 13.3 — Feature Scaling

Similarly test:

```text
4 features
8 features
12 features
16 features
```

For QML:

```text
features
      ↓
qubits
      ↓
circuit complexity
      ↓
simulation cost
```

This is extremely important.

---

# 12. Why Feature Reduction Matters

Suppose the CNN generates:

```text
1280 features
```

We cannot simply create:

```text
1280 qubits
```

for our current local simulator.

Instead:

```text
1280
 ↓
PCA / feature selection
 ↓
16
 ↓
quantum encoding
 ↓
16 qubits
```

Or:

```text
1280
 ↓
8
 ↓
8 qubits
```

Therefore:

> **Classical feature reduction is not an optional decoration. It is what makes the quantum branch computationally feasible.**

---

# 13. Module 13.4 — Qubit Scaling

Test:

```text
4 qubits
8 qubits
12 qubits
16 qubits
```

Measure:

```text
memory
runtime
circuit execution count
```

This helps demonstrate why we aren't simply increasing qubits indefinitely.

---

# 14. Local Simulator Reality

For a state-vector simulator, the state space grows exponentially with the number of qubits.

Conceptually:

```text
n qubits
     ↓
2ⁿ amplitudes
```

So:

```text
8 qubits
→ 256 amplitudes

16 qubits
→ 65,536 amplitudes

20 qubits
→ 1,048,576 amplitudes

30 qubits
→ 1,073,741,824 amplitudes
```

This is one reason our system needs resource-aware planning.

---

# 15. Important Architecture Decision

The system should **never assume**:

> "More qubits = better model."

Instead:

```text
Feature dimension
+
model complexity
+
available resources
+
performance
```

determine whether a larger circuit is worth trying.

---

# 16. Module 13.5 — Circuit Depth Scaling

Compare:

```text
Depth 1
Depth 2
Depth 4
Depth 6
```

Measure:

```text
accuracy
recall
AUC
training time
circuit executions
```

Example:

| Depth |  AUC | Recall | Runtime |
| ----: | ---: | -----: | ------: |
|     1 | 0.90 |    88% |   2 min |
|     2 | 0.93 |    91% |   5 min |
|     4 | 0.94 |    92% |  15 min |
|     6 | 0.94 |    92% |  38 min |

If depth 6 provides almost no improvement:

```text
Depth 4
```

may be the better practical configuration.

---

# 17. Module 13.6 — Shots Scaling

Test:

```text
128 shots
256 shots
512 shots
1024 shots
2048 shots
```

More shots can provide more stable measurement estimates, but increase workload.

So:

```text
more shots
     ↓
potentially more stable estimate
     ↓
more execution cost
```

Again, the platform should measure this rather than assume one setting is universally best.

---

# 18. Module 13.7 — Cost Estimator

For local execution:

```text
Estimated Cost
=
CPU usage
+
GPU usage
+
runtime
+
memory usage
```

We don't need to convert these immediately into rupees.

Instead, first record:

```text
resource units
```

Then optionally map them to:

```text
₹ / $
```

for a particular infrastructure.

---

# 19. Example

Suppose:

```text
CPU:
4 core-hours

GPU:
0.5 GPU-hours

Runtime:
2 hours
```

We can later calculate:

```text
Infrastructure cost
```

based on whichever machine/cloud provider is being used.

This keeps the platform provider-neutral.

---

# 20. Module 13.8 — Cloud Cost Estimation

Eventually:

```text
Local
 ↓
Cloud simulator
 ↓
Cloud quantum hardware
```

The same experiment configuration can estimate:

```text
estimated execution cost
```

before execution.

For example:

```text
EXP-Q-001

Estimated:
Runtime = 12 min
Shots = 1024
Circuit executions = 20,000

Estimated cloud cost:
₹X / $
```

The actual number should come from the selected provider's current pricing, not a hardcoded assumption.

---

# 21. Module 13.9 — Cost-Aware Experiment Planning

Now Phase 13 feeds information **back to Phase 9**.

This is an important feedback loop.

```text
PHASE 9
Experiment Planning
       ↓
PHASE 10
Execution
       ↓
PHASE 13
Cost Analysis
       ↓
Resource observations
       ↓
PHASE 9
Improved planning
```

So the platform learns from previous experiments.

---

# 22. Example

Initial prediction:

```text
VQC-16
Estimated runtime:
10 minutes
```

Actual:

```text
58 minutes
```

The system stores:

```text
estimated = 10
actual = 58
```

Future planning can use:

```text
observed resource history
```

to improve estimates.

---

# 23. Module 13.10 — Scalability Modes

Our platform should support:

### Mode 1 — Local

```text
Laptop / workstation
```

Good for:

```text
development
small datasets
small quantum circuits
```

---

### Mode 2 — GPU / HPC

```text
Powerful workstation
or cluster
```

Good for:

```text
larger classical models
larger simulation workloads
```

---

### Mode 3 — Cloud Simulator

```text
Cloud infrastructure
```

Good for:

```text
larger workloads
parallel experiments
```

---

### Mode 4 — Real Quantum Hardware

```text
Near-term quantum device
```

Good for:

```text
hardware validation
noise experiments
hardware compatibility
```

---

# 24. Module 13.11 — Backend Abstraction

This is a critical technical architecture decision.

Instead of hardcoding:

```python
run_vqc_on_local_simulator()
```

we create:

```text
QuantumBackend
```

with implementations:

```text
LocalSimulatorBackend
CloudSimulatorBackend
HardwareBackend
```

All expose the same basic interface:

```text
submit()
status()
result()
metrics()
```

Conceptually:

```text
                 QuantumBackend
                       │
          ┌────────────┼─────────────┐
          ↓            ↓             ↓
      LocalSim      CloudSim      Hardware
```

---

# 25. Why This Matters for SIH

The problem statement explicitly mentions:

> compatibility with near-term quantum hardware and simulators.

This architecture lets us demonstrate:

```text
Today:
Local Simulator
```

and say:

> The same experiment abstraction can target a compatible near-term backend later.

That is much more credible than pretending we need real quantum hardware from day one.

---

# 26. Module 13.12 — Parallel Execution

Suppose Phase 9 creates:

```text
20 experiments
```

Some can run independently:

```text
EXP-001 ───────┐
EXP-002 ───────┤
EXP-003 ───────┼──→ results
EXP-004 ───────┤
EXP-005 ───────┘
```

The scheduler can parallelize where resources permit.

This reduces:

```text
wall-clock time
```

without changing the scientific experiment.

---

# 27. But Quantum Simulations Compete for Resources

If we have:

```text
8 GB RAM
```

we shouldn't run:

```text
4 × 6 GB simulations
```

simultaneously.

Therefore the scheduler needs:

```text
resource-aware scheduling
```

which is another reason Phase 9 and Phase 13 are connected.

---

# 28. Module 13.13 — Caching

Suppose we already generated:

```text
CNN embedding
```

for 3,000 images.

We shouldn't regenerate it for every experiment.

Instead:

```text
Image
 ↓
MobileNetV2
 ↓
Embedding
 ↓
CACHE
```

Then:

```text
Experiment 1 → cached embedding
Experiment 2 → cached embedding
Experiment 3 → cached embedding
```

This can dramatically reduce repeated computation.

---

# 29. Cache Layers

Potential caches:

```text
Raw dataset cache

Preprocessed dataset cache

Feature embedding cache

Reduced representation cache

Quantum kernel cache

Experiment result cache
```

But each cache needs a version/hash so stale results aren't reused incorrectly.

---

# 30. Module 13.14 — Reuse Quantum Kernels

Quantum kernel methods can be especially expensive because kernel matrices may require many pairwise evaluations.

For:

```text
N samples
```

the kernel matrix contains approximately:

```text
N × N
```

entries.

Therefore:

```text
N = 1,000
```

can mean:

```text
~1 million pairwise entries
```

before accounting for symmetry or implementation optimizations.

This is another reason sample-size scaling must be measured.

---

# 31. Module 13.15 — Batch / Subset Strategy

For very large datasets, we can define:

```text
Development
→ 100 samples

Pilot
→ 500 samples

Benchmark
→ prescribed full evaluation set

Scale test
→ increasing subsets
```

But the final benchmark must clearly state:

```text
which samples were used
```

so we don't accidentally compare incomparable results.

---

# 32. Module 13.16 — Scalability Report

The system should produce:

```text
SCALABILITY REPORT

Dataset size
Feature dimension
Qubits
Circuit depth
Shots
Runtime
Memory
Circuit executions
```

Example:

```text
                    8-QUBIT VQC

Samples   Runtime   RAM    AUC
--------------------------------
100       12 sec    1.1GB  0.89
500       60 sec    1.2GB  0.91
1000      124 sec   1.4GB  0.92
2000      251 sec   1.7GB  0.92
```

---

# 33. Module 13.17 — Performance vs Cost Curve

One of the most useful visualizations:

```text
Performance
    ↑
    │                 ●
    │            ●
    │       ●
    │   ●
    └────────────────────→
             Cost
```

Each point represents:

```text
model configuration
```

This lets us identify:

> **the practical sweet spot.**

---

# 34. Example

Suppose:

```text
VQC-4:
AUC = 0.89
Cost = low

VQC-8:
AUC = 0.93
Cost = medium

VQC-16:
AUC = 0.935
Cost = very high
```

Then:

```text
VQC-8
```

might be the most practical choice.

Even though VQC-16 has slightly higher AUC.

---

# 35. Module 13.18 — Cost-Performance Frontier

We can classify configurations as:

```text
Dominated
```

if another model provides:

```text
better/equal performance
AND
lower/equal cost
```

Example:

```text
Model A
AUC = 0.91
Cost = 100

Model B
AUC = 0.94
Cost = 80
```

Model A is dominated.

Model B is preferable.

---

# 36. Practical Pareto Frontier

This can produce:

```text
PERFORMANCE
     ↑
     │        ●
     │      ●
     │    ●
     │  ●
     │
     └────────────────→ COST
```

The points on the frontier represent different tradeoffs.

This is a strong way to answer:

> "Is quantum actually worth its computational cost?"

---

# 37. Module 13.19 — Scaling Beyond the Current Hardware

We should explicitly document:

```text
Current supported:
4–16 qubits
```

if that is what our local environment can realistically handle.

Then:

```text
Architecture supports:
future backend
larger simulator
real hardware
```

This is better than claiming unlimited scalability.

---

# 38. Module 13.20 — Deployment Architecture

At this stage the final platform can be separated into:

```text
                WEB UI
                  │
                  ↓
             API SERVER
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
   Experiment           Results
   Service              Service
        │
        ↓
     Scheduler
        │
   ┌────┴──────────────┐
   ↓                   ↓
Classical           Quantum
Runtime             Runtime
                       │
          ┌────────────┼───────────┐
          ↓            ↓           ↓
      Local Sim    Cloud Sim   Hardware
```

---

# 39. Local Development Architecture

For our current project:

```text
Browser
   ↓
FastAPI
   ↓
Python Backend
   ↓
Experiment Manager
   ↓
Local CPU/GPU
   ↓
Local Quantum Simulator
```

Everything can run on one machine.

The user doesn't need to know:

> "This is currently running locally."

The platform simply exposes:

```text
Backend:
Local Simulator
```

in the execution details.

---

# 40. Production Architecture Later

Eventually:

```text
Frontend
   ↓
API Gateway
   ↓
Job Queue
   ↓
Scheduler
   ↓
Worker Nodes
   ├── Classical Worker
   ├── Quantum Simulator Worker
   └── Hardware Worker
   ↓
Object Storage
   ↓
Database
```

This is the scalable architecture.

---

# 41. Module 13.21 — User-Level Cost View

The user shouldn't have to understand:

```text
circuit depth
shots
RAM
```

unless they want to.

Instead, show:

```text
┌──────────────────────────────────┐
│ EXPERIMENT COST                  │
├──────────────────────────────────┤
│ Estimated runtime: 14 min        │
│ Memory: 2.1 GB                   │
│ Quantum executions: 18,240      │
│ Backend: Local Simulator         │
│ Financial cost: Local / ₹0*      │
└──────────────────────────────────┘

*Excludes local electricity/hardware cost.
```

For cloud:

```text
Estimated cloud cost:
₹X
```

---

# 42. Module 13.22 — System-Level Cost

We should calculate the cost of the **entire pipeline**, not just QML.

Example:

```text
Image preprocessing
       ↓
CNN feature extraction
       ↓
PCA
       ↓
Quantum training
       ↓
Evaluation
```

Maybe:

```text
CNN:
80% of compute

Quantum:
15%

Other:
5%
```

This could reveal something very important:

> The quantum component may not even be the largest computational expense.

That is exactly the kind of insight our platform should expose.

---

# 43. Module 13.23 — End-to-End Cost

For each experiment:

```text
Total Cost
=
Data Processing
+
Feature Extraction
+
Feature Reduction
+
Model Training
+
Inference
+
Evaluation
```

For quantum:

```text
Quantum Cost
=
Circuit Construction
+
Circuit Execution
+
Measurement
+
Optimization
```

---

# 44. Module 13.24 — Scalability Decision

At the end, the system can generate:

```text
SCALABILITY STATUS
```

Example:

```text
Dataset:
3,000 samples

Quantum:
8 qubits

Status:
FEASIBLE ON LOCAL MACHINE

16 qubits:
FEASIBLE WITH HIGH RESOURCE USAGE

32 qubits:
NOT RECOMMENDED FOR CURRENT LOCAL SETUP
```

---

# 45. This Connects Directly to Our Original Concern

You previously raised:

> **"What about cost? What is actually in it for people?"**

Phase 13 lets us answer this honestly.

The platform isn't promising:

> "Quantum is cheaper."

Instead it asks:

```text
Does quantum provide:

better accuracy?
better recall?
better generalization?
acceptable cost?
acceptable latency?
acceptable resource usage?
```

If yes:

```text
Potential practical value
```

If no:

```text
Classical remains preferable
```

That is a much stronger platform.

---

# 46. Phase 13 Output

Main artifacts:

```text
cost_report.json
resource_report.json
scalability_report.json
backend_report.json
performance_cost.csv
scaling_experiments.csv
deployment_config.json
```

Example:

```json
{
  "experiment_id": "EXP-Q-001",

  "performance": {
    "roc_auc": 0.94,
    "recall": 0.93
  },

  "resources": {
    "runtime_seconds": 842,
    "ram_gb": 3.2,
    "qubits": 8,
    "shots": 1024,
    "circuit_executions": 19932
  },

  "scalability": {
    "status": "FEASIBLE_LOCAL",
    "recommended_qubits": 8
  }
}
```

---

# 47. Phase 13 Success Criteria

Phase 13 is complete when the platform can:

* [ ] Measure CPU usage
* [ ] Measure RAM usage
* [ ] Measure GPU usage
* [ ] Measure training time
* [ ] Measure inference time
* [ ] Track quantum circuit executions
* [ ] Track qubits
* [ ] Track circuit depth
* [ ] Track gate counts
* [ ] Track shots
* [ ] Estimate computational cost
* [ ] Estimate cloud cost when provider pricing is available
* [ ] Perform dataset-size scaling experiments
* [ ] Perform feature-size scaling experiments
* [ ] Perform qubit scaling experiments
* [ ] Perform circuit-depth scaling experiments
* [ ] Perform shot scaling experiments
* [ ] Support local simulation
* [ ] Support simulator backend abstraction
* [ ] Support future hardware backends
* [ ] Support resource-aware scheduling
* [ ] Support caching
* [ ] Generate scalability reports
* [ ] Generate performance-vs-cost analysis
* [ ] Identify practical Pareto-efficient configurations
* [ ] Produce deployment recommendations

---

# 48. Final Architecture After Phase 13

```text
                           USER
                            │
                            ▼
                    ┌──────────────┐
                    │ WEB / GUI    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ API /        │
                    │ CONTROLLER   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ DATA LAYER   │
                    └──────┬───────┘
                           │
         ┌─────────────────┼──────────────────┐
         ↓                 ↓                  ↓
    Classical          Quantum            Analysis
      Branch            Branch              Branch
         │                 │                  │
         ↓                 ↓                  ↓
    Phase 7             Phase 8            Phase 11
         │                 │                  │
         └────────────┬────┘                  │
                      ↓                       │
                  Phase 9                     │
             Experiment Planner               │
                      ↓                       │
                  Phase 10                    │
                  Executor                    │
                      │                       │
             ┌────────┴─────────┐             │
             ↓                  ↓             │
       Classical Runtime   Quantum Runtime   │
                                │             │
                  ┌─────────────┼───────┐     │
                  ↓             ↓       ↓     │
               Local Sim    Cloud Sim Hardware│
                  │             │       │     │
                  └─────────────┼───────┘     │
                                ↓             │
                           Phase 13           │
                       Cost & Scalability     │
                                │             │
                                └──────┬──────┘
                                       ↓
                                   Phase 12
                                Explainability
                                       ↓
                                  FINAL REPORT
```

---

# 49. The Complete 13-Phase Logic

```text
01 — INGESTION
     Get the data

02 — PROFILING
     Understand the data

03 — VALIDATION
     Check whether it is usable

04 — PREPROCESSING
     Clean and prepare it

05 — FEATURE ENGINEERING
     Extract useful information

06 — FEATURE SELECTION / REDUCTION
     Create representations suitable for ML/QML

07 — CLASSICAL MODEL CANDIDATES
     Establish strong classical baselines

08 — QUANTUM MODEL CANDIDATES
     Build feasible QML candidates

09 — EXPERIMENT PLANNING
     Decide what should be run

10 — TRAINING & EXECUTION
     Actually run the experiments

11 — BENCHMARKING
     Compare quantum vs classical

12 — EXPLAINABILITY
     Understand predictions and decisions

13 — COST & SCALABILITY
     Determine whether the approach is practical
```

## The most important outcome of Phase 13

We don't end with:

> **"We used quantum computing."**

We end with something much stronger:

> **"For this type of biomedical dataset, under this feature representation and resource budget, this quantum configuration achieved this performance, required this computational workload, and compared with the classical baseline in this specific way."**

That is the evidence needed to make the platform scientifically credible rather than just a **QML demonstration**.
