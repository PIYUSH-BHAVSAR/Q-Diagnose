cd D:\projects\SIH2026\mvp
python run_experiment.py data/demo/breast_cancer.csv


D:\projects\SIH2026\mvp\venv\Lib\site-packages\pennylane\__init__.py:212: PennyLaneDeprecationWarning: PennyLane v0.44
 has dropped maintainence support for NumPy < 2.0.0. You have version 1.26.4 installed. Future versions of PennyLane will not work with NumPy<2.0. Please consider upgrading NumPy using `python -m pip install numpy --upgrade`.             warnings.warn(
======================================================================
QuantWarriors Hybrid QML Platform - Experiment Runner
======================================================================

Dataset: data/demo/breast_cancer.csv

[2026-09-15 23:13:46] INFO - quantwarriors - ======================================================================
[2026-09-15 23:13:46] INFO - quantwarriors - STARTING EXPERIMENT EXECUTION
[2026-09-15 23:13:46] INFO - quantwarriors - ======================================================================
[2026-09-15 23:13:46] INFO - quantwarriors - [5%] Loading dataset
[2026-09-15 23:13:46] INFO - quantwarriors - Dropped empty columns: ['Unnamed: 32']
[2026-09-15 23:13:46] INFO - quantwarriors - Loaded CSV: data/demo/breast_cancer.csv with 569 rows, 32 columns
[2026-09-15 23:13:46] INFO - quantwarriors - [10%] Profiling dataset
[2026-09-15 23:13:46] INFO - quantwarriors - Profiling dataset: DS-2DB37EA9
[2026-09-15 23:13:46] INFO - quantwarriors - Profile complete: 569 rows, 32 columns, target: diagnosis, binary: True
[2026-09-15 23:13:46] INFO - quantwarriors - [15%] Validating dataset
[2026-09-15 23:13:46] INFO - quantwarriors - Validating dataset: DS-2DB37EA9
[2026-09-15 23:13:46] INFO - quantwarriors - Validation complete: valid=True, ready_for_ml=True, issues=0
[2026-09-15 23:13:46] INFO - quantwarriors - Using adapter: breast_cancer_wisconsin
[2026-09-15 23:13:46] INFO - quantwarriors - Created experiment: EXP-D60D373B
[2026-09-15 23:13:46] INFO - quantwarriors - Resource monitoring started
[2026-09-15 23:13:46] INFO - quantwarriors - [20%] Preprocessing data
[2026-09-15 23:13:46] INFO - quantwarriors - Experiment EXP-D60D373B: preprocessing
[2026-09-15 23:13:46] INFO - quantwarriors - ============================================================
[2026-09-15 23:13:46] INFO - quantwarriors - Starting Feature Pipeline
[2026-09-15 23:13:46] INFO - quantwarriors - ============================================================
[2026-09-15 23:13:46] INFO - quantwarriors - Step 1: Preprocessing (split, impute, scale)
[2026-09-15 23:13:46] INFO - quantwarriors - Starting preprocessing pipeline
[2026-09-15 23:13:46] INFO - quantwarriors - Split data: train=455, test=114, type=stratified
[2026-09-15 23:13:46] INFO - quantwarriors - Scaled features
[2026-09-15 23:13:46] INFO - quantwarriors - Preprocessing complete: 30 features, train=455, test=114
[2026-09-15 23:13:46] INFO - quantwarriors - Step 2: Feature Reduction (PCA)
[2026-09-15 23:13:46] INFO - quantwarriors - Starting feature reduction: 30 features -> target=8
[2026-09-15 23:13:46] INFO - quantwarriors - PCA complete: 8 components, variance explained: 0.9276
[2026-09-15 23:13:46] INFO - quantwarriors - ============================================================
[2026-09-15 23:13:46] INFO - quantwarriors - Feature Pipeline Complete: 30 -> 8 features
[2026-09-15 23:13:46] INFO - quantwarriors - ============================================================
[2026-09-15 23:13:46] INFO - quantwarriors - [30%] Training classical models
[2026-09-15 23:13:46] INFO - quantwarriors - Experiment EXP-D60D373B: running_classical
[2026-09-15 23:13:46] INFO - quantwarriors - [30%] Training logistic_regression
[2026-09-15 23:13:46] INFO - quantwarriors - Training logistic_regression...
[2026-09-15 23:13:46] INFO - quantwarriors - Training Logistic Regression model
[2026-09-15 23:13:46] INFO - quantwarriors - Logistic Regression trained: train_acc=0.9802, time=0.0060s
[2026-09-15 23:13:46] INFO - quantwarriors - logistic_regression complete: accuracy=0.9825, time=0.01s
[2026-09-15 23:13:46] INFO - quantwarriors - [40%] Training svm
[2026-09-15 23:13:46] INFO - quantwarriors - Training svm...
[2026-09-15 23:13:46] INFO - quantwarriors - Training SVM model (kernel=rbf)
D:\projects\SIH2026\mvp\venv\Lib\site-packages\sklearn\svm\_base.py:239: FutureWarning: The `probability` parameter wa
s deprecated in 1.9 and will be removed in version 1.11. Use `CalibratedClassifierCV(SVC(), ensemble=False)` instead of `SVC(probability=True)`                                                                                               warnings.warn(
[2026-09-15 23:13:46] INFO - quantwarriors - SVM trained: train_acc=0.9824, time=0.0077s
[2026-09-15 23:13:46] INFO - quantwarriors - svm complete: accuracy=0.9561, time=0.01s
[2026-09-15 23:13:46] INFO - quantwarriors - [50%] Training random_forest
[2026-09-15 23:13:46] INFO - quantwarriors - Training random_forest...
[2026-09-15 23:13:46] INFO - quantwarriors - Training Random Forest model (n_estimators=100, max_depth=10)
[2026-09-15 23:13:46] INFO - quantwarriors - Random Forest trained: train_acc=1.0000, time=0.1195s
[2026-09-15 23:13:46] INFO - quantwarriors - random_forest complete: accuracy=0.9474, time=0.12s
[2026-09-15 23:13:46] INFO - quantwarriors - [60%] Training quantum model
[2026-09-15 23:13:46] INFO - quantwarriors - Experiment EXP-D60D373B: running_quantum
[2026-09-15 23:13:46] INFO - quantwarriors - ============================================================
[2026-09-15 23:13:46] INFO - quantwarriors - Training VQC Model
[2026-09-15 23:13:46] INFO - quantwarriors -   n_qubits: 8
[2026-09-15 23:13:46] INFO - quantwarriors -   n_layers: 2
[2026-09-15 23:13:46] INFO - quantwarriors -   epochs: 20
[2026-09-15 23:13:46] INFO - quantwarriors -   shots: 1024
[2026-09-15 23:13:46] INFO - quantwarriors - ============================================================
[2026-09-15 23:13:46] INFO - quantwarriors - Initialized VQC: qubits=8, layers=2, params=32
[2026-09-15 23:20:54] INFO - quantwarriors - Epoch 20/20, Loss: 0.5253
[2026-09-15 23:21:03] INFO - quantwarriors - VQC training complete: 427.38s, 9100 executions
[2026-09-15 23:21:03] INFO - quantwarriors - VQC complete: accuracy=0.8421, time=427.38s
[2026-09-15 23:21:03] INFO - quantwarriors - [80%] Comparing models
[2026-09-15 23:21:03] INFO - quantwarriors - Experiment EXP-D60D373B: benchmarking
[2026-09-15 23:21:03] INFO - quantwarriors - Comparing 4 models
[2026-09-15 23:21:03] INFO - quantwarriors - Resource monitoring stopped: elapsed=437.12s, peak_memory=191.44MB
[2026-09-15 23:21:03] INFO - quantwarriors - [95%] Finalizing results
[2026-09-15 23:21:03] INFO - quantwarriors - Experiment EXP-D60D373B: completed
[2026-09-15 23:21:03] INFO - quantwarriors - [100%] Experiment completed
[2026-09-15 23:21:03] INFO - quantwarriors - ======================================================================
[2026-09-15 23:21:03] INFO - quantwarriors - EXPERIMENT COMPLETED SUCCESSFULLY
[2026-09-15 23:21:03] INFO - quantwarriors - ======================================================================

======================================================================
EXPERIMENT COMPLETED SUCCESSFULLY
======================================================================

Experiment ID: EXP-D60D373B

📊 Model Results:
----------------------------------------------------------------------
Model                     Type         Accuracy   Recall     F1         Time      
----------------------------------------------------------------------
logistic_regression       classical    0.9825     0.9762     0.9762     0.01      s
svm                       classical    0.9561     0.9048     0.9383     0.01      s
random_forest             classical    0.9474     0.9048     0.9268     0.12      s
vqc                       quantum      0.8421     0.5714     0.7273     427.38    s

🏆 Best Models:
  Best Classical: logistic_regression
  Best Quantum:   vqc
  Overall Best:   logistic_regression

📋 Recommendation:
----------------------------------------------------------------------
CLASSICAL MODEL PREFERRED: Classical model shows +14.0% accuracy advantage with 0.0x lower runtime. Recommended for pr
oduction use.                                                                                                         
💻 Resources:
  Peak Memory: 191.44 MB
  Total Time:  437.12 s

⚛️ Quantum Resources:
  Qubits:      8
  Layers:      2
  Executions:  9100

======================================================================

Results saved to: experiment_results_EXP-D60D373B.json
