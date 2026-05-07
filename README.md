# 🛡 DevSecOps Automation Tool with Risk Prioritization

## 📌 Overview
This project implements an automated **DevSecOps Security Pipeline** integrated into **GitHub Actions**.

It performs:

- **Static Application Security Testing (SAST)**  
  - Bandit (Python security linter)
  - Semgrep (pattern-based static analysis)
- **Dependency vulnerability scanning**  
  - pip-audit (Python dependency vulnerability scanning)
- **Risk-based analysis & prioritization**
- **Automated policy enforcement (security gate)**
- **Dashboard generation**
- **Security artifact reporting for audit & review**

Unlike traditional pipelines that only *run scanners*, this system also **interprets scan results**, calculates an **overall risk score/level**, and can **fail the pipeline automatically** when risk is too high.

---

## 🎯 Project Objective

### Traditional approach (common in many teams)
**Code → Deploy → Then Security**

### This project’s approach (DevSecOps-first)
**Code → Security Scan → Risk Evaluation → Policy Decision (Gate) → (Optional) Deploy**

Security becomes:

- **Automated** (runs every push)
- **Measurable** (risk scoring)
- **Enforceable** (policy gate pass/fail)
- **Auditable** (artifacts stored in Actions)

---

## ⚙️ Architecture

### 1️⃣ Security Scanning Layer
Integrated tools:

- **Bandit** — Python SAST scanning
- **Semgrep** — SAST / insecure pattern detection
- **pip-audit** — dependency vulnerability scanning (`requirements.txt`)

The pipeline is triggered on pushes to:
- `dev`
- `staging`
- `main`

Outputs generated as JSON:
- `bandit-results.json`
- `semgrep-results.json`
- `dependency-results.json`

Workflow: `.github/workflows/security.yml`

---

### 2️⃣ Intelligent Risk Engine
Custom-built **`risk_engine.py`**:

- Reads scan results JSON files
- Aggregates findings
- Calculates **severity distribution**
- Produces an overall risk decision:
  - `LOW`
  - `MEDIUM`
  - `HIGH`
  - `CRITICAL`

It generates a consolidated report:
- `risk-summary.json`

#### Risk scoring (how it works)
Severity weights used by the engine:

- LOW → 1  
- MEDIUM → 3  
- HIGH → 5  
- CRITICAL → 8  

Branch-based strictness (risk multiplier):

- `dev` → 1×  
- `staging` → 2×  
- `main` → 3×  

Core idea:
- A **base score** is derived from scanner results (max severity weight detected)
- A **branch multiplier** increases strictness as code moves closer to production
- A **final score** is mapped into an overall risk category

---

### 3️⃣ Policy Enforcement (Security Gate)
Pipeline logic:

- `LOW` / `MEDIUM` → ✅ Allow pipeline to continue
- `HIGH` / `CRITICAL` → ❌ Fail the build (remediation required)

This ensures:

- Risky code is **blocked automatically**
- Security becomes part of **CI/CD governance**
- Builds provide a clear **pass/fail security decision**

---

### 4️⃣ Dashboard & Reporting
The pipeline generates and uploads security artifacts per run, including:

- raw scanner outputs (JSON)
- consolidated risk report
- HTML dashboard for visibility

Artifacts are uploaded via GitHub Actions for audit, review, and evidence.

---

## 📊 Key Features

- ✔ Automated CI/CD security integration (GitHub Actions)
- ✔ Multi-tool security scanning (Bandit + Semgrep + pip-audit)
- ✔ Risk-based prioritization & scoring
- ✔ Policy-driven enforcement (security gate)
- ✔ HTML security dashboard for visibility
- ✔ Artifact-based audit trail (downloadable reports)
- ✔ Branch-aware strictness (dev vs staging vs main)

---

## 🏗 Workflow Structure

**Push → GitHub Actions Trigger → Install Tools → Run Scanners → Generate JSON → Run Risk Engine → Enforce Policy → Generate Dashboard → Upload Artifacts**

Workflow file:
- `.github/workflows/security.yml`

---

## 📁 Project Structure

```text
devsecops-project/
│
├── app.py
├── risk_engine.py
├── dashboard_generator.py
├── requirements.txt
│
└── .github/
    └── workflows/
        └── security.yml
```

---

## 📦 Outputs (What you get after a run)

After each GitHub Actions run (or local run), the pipeline produces these outputs:

### Raw scanner reports
- `bandit-results.json` — Bandit SAST findings (Python)
- `semgrep-results.json` — Semgrep findings (code patterns / SAST)
- `dependency-results.json` — pip-audit dependency vulnerability report

### Consolidated risk report
- `risk-summary.json` — unified risk score, risk level, severity distributions, and policy evaluation

### Visual report
- `dashboard.html` — HTML dashboard showing:
  - overall risk level + score
  - tool-wise findings
  - severity breakdown
  - policy pass/fail status
  - branch + metadata

### Where to find them in GitHub Actions
These outputs are uploaded as an artifact (named **`security-reports`**) in the workflow run.

---

## 🚀 Quick Start (Run locally)

### Prerequisites
- Python 3.10+
- pip

### 1) Install project dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Install security tools
```bash
pip install bandit semgrep pip-audit
```

### 3) Run scanners
```bash
bandit -r . -x ./venv,./.venv,./.git -f json -o bandit-results.json --exit-zero

semgrep scan --config=auto \
  --exclude=venv --exclude=.venv --exclude=.git \
  --json --output=semgrep-results.json

pip-audit -r requirements.txt -f json -o dependency-results.json 2>/dev/null \
  || echo '{"dependencies": []}' > dependency-results.json
```

### 4) Run risk engine (policy gate)
```bash
python3 risk_engine.py
```

What this does:
- prints a summary to the console
- writes `risk-summary.json`
- exits with:
  - `0` if policy passes (LOW/MEDIUM)
  - `1` if policy fails (HIGH/CRITICAL)

### 5) Generate dashboard
```bash
python3 dashboard_generator.py
```

Output:
Open it in a browser:
- `dashboard.html`
- LOW / MEDIUM → pass
<img width="1856" height="1006" alt="Screenshot from 2026-02-23 13-22-13" src="https://github.com/user-attachments/assets/7341205a-e353-4957-9f19-d433acf57fe2" />
<img width="1856" height="1006" alt="Screenshot from 2026-02-23 13-35-50" src="https://github.com/user-attachments/assets/745f4ba5-6e11-489f-b024-1626c5dfa526" />

- HIGH / CRITICAL → fail
<img width="1856" height="1006" alt="Screenshot from 2026-02-23 13-39-26" src="https://github.com/user-attachments/assets/6612b94e-32b4-461d-a4f7-da95e0351738" />
<img width="1856" height="1006" alt="Screenshot from 2026-02-23 13-40-16" src="https://github.com/user-attachments/assets/f6095223-c7ce-4e7a-a765-bb1d00345112" />


---

## 🔎 Viewing artifacts in GitHub Actions
After a workflow run completes:

1. Go to the repository → **Actions**
2. Open the latest workflow run
3. Scroll to **Artifacts**
4. Download **security-reports**
5. Review:
   - JSON scan outputs
   - `risk-summary.json`
   - `dashboard.html`

---

## 🚀 Future Scope (Next-Level Enhancements)

### 1️⃣ Risk Trend Tracking (Security Analytics Layer)
Store results from every pipeline run:

- risk score
- total vulnerabilities
- severity distribution
- policy result

Then generate trend graphs to track improvement or regression over time.

### 2️⃣ Developer Security Score
Track per-developer security impact:

- number of policy failures triggered
- risk introduced per commit/PR
- improvement trend

Useful for governance and DevSecOps maturity metrics.

### 3️⃣ Context-Based Risk Multipliers (Adaptive Risk)
Enhance scoring model:

**Final Risk = Base Score × Branch Weight × File Sensitivity × Exposure Level**

Examples:
- `main` branch → higher multiplier
- `auth.py` or security-critical modules → higher multiplier
- public API code → higher multiplier

This enables context-aware prioritization and stronger policy enforcement.

### 4️⃣ Multi-Scanner Orchestration
Add more scanners for deeper coverage:

- Trivy (container security scanning)
- Checkov/tfsec (IaC scanning)
- Secret scanning (Gitleaks)
- SBOM generation + validation
