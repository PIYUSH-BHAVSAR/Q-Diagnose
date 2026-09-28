# Setup Guide — Q-Diagnose

## Prerequisites
- Python 3.11+
- Node.js 18+ and npm 9+

## Clone
```bash
git clone https://github.com/PIYUSH-BHAVSAR/Q-Diagnose.git
cd Q-Diagnose
```

## Backend
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Frontend
```bash
cd frontend
npm install
cd ..
```

## Run

**Terminal 1 (backend) — run from repo root:**
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (frontend) — run from repo root:**
```bash
cd frontend && npm run dev
```

Open **http://localhost:5173**  
Swagger docs: **http://localhost:8000/docs**

## Demo dataset
`data/demo/breast_cancer.csv` — 569 rows, 32 features, binary classification.  
Upload it via the UI to run your first experiment.

## Configuration
Edit `config.yaml` to change storage paths, quantum settings, or model hyperparameters.
