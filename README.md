# 🛡️ DevSecOps Automated Pipeline with Intelligent Risk Engine

## 📌 Overview
This project implements an automated **DevSecOps Security Pipeline** built directly into GitHub Actions. Rather than taking the traditional approach of simply running scanners and failing builds over minor issues, this pipeline features an **Intelligent Risk Engine**. 

It aggregates raw JSON outputs from multiple SAST and dependency scanners (Bandit, Semgrep, pip-audit), calculates a contextual risk score based on both vulnerability severity and the deployment branch, enforces a strict security gate, and generates a visual HTML dashboard for auditability.

---

## 🎯 Project Motivation

### The Challenge: "Scanner Fatigue"
In many traditional CI/CD pipelines, security tools are bolted on at the end. They scan the code, find hundreds of "Low" severity warnings, and immediately fail the build. Developers often experience "alert fatigue," leading to friction between security and engineering teams.

### The Solution: Context-Aware DevSecOps
This project addresses that friction by placing a custom **Risk Engine** between the scanners and the deployment phase:
**Code Push ➔ Run Scanners ➔ Risk Evaluation ➔ Policy Gate ➔ Deploy**

By quantifying the actual risk and applying branch-based multipliers (e.g., being lenient on `dev` but strictly blocking `main`), security becomes **automated, measurable, and enforceable** without needlessly blocking developer velocity.

---

## ⚙️ Technical Architecture

### 1️⃣ Security Scanning Layer
The pipeline triggers on every push to `dev`, `staging`, or `main`. It runs three distinct security tools:
* **Bandit:** Python-specific Static Application Security Testing (SAST). Scans for hardcoded passwords, unsafe imports, weak cryptography, etc.
* **Semgrep:** Pattern-based SAST. Scans across the architecture for insecure logic and code patterns.
* **pip-audit:** Software Composition Analysis (SCA). Scans `requirements.txt` against known CVE databases to find vulnerable dependencies.

*Note: All scanners are configured to output raw JSON (`-f json`) and exit with a code of `0` (`--exit-zero` or via bash fallback). This ensures the GitHub Action doesn't fail prematurely, passing the raw data directly to the Risk Engine.*

### 2️⃣ The Custom Risk Engine (`risk_engine.py`)
This Python script serves as the decision-making core of the pipeline. It parses the JSON files from the scanners and calculates a final risk score.

**Risk Scoring Logic:**
1. **Base Severity Weights:** `LOW` = 1 | `MEDIUM` = 3 | `HIGH` = 5 | `CRITICAL` = 8.
2. **Branch Multipliers:** The engine detects the active Git branch via environment variables (`GITHUB_REF_NAME`).
   * `dev` ➔ 1x (Testing phase, lenient)
   * `staging` ➔ 2x (Pre-prod, strict)
   * `main` ➔ 3x (Production, extremely strict)
3. **Calculation:** `Final Score = Base Score × Branch Multiplier`. 

*Example:* A `HIGH` vulnerability (5 points) on the `dev` branch yields a score of 5 (MEDIUM Risk). That exact same code pushed to `main` yields a score of 15 (HIGH Risk), instantly failing the build.

### 3️⃣ Policy Enforcement (The Security Gate)
The `risk_engine.py` script enforces governance by making the final pipeline decision:
* **LOW / MEDIUM (Score < 12):** `sys.exit(0)` ➔ ✅ Pipeline passes.
* **HIGH / CRITICAL (Score ≥ 12):** `sys.exit(1)` ➔ ❌ Pipeline fails, deployment blocked.

### 4️⃣ Visual Dashboard & Artifacts (`dashboard_generator.py`)
Because raw JSON is unreadable for managers and auditors, the pipeline takes the consolidated `risk-summary.json` and dynamically generates a `dashboard.html` file (handling cross-platform UTF-8 encoding requirements). This HTML file, along with the raw scans, is zipped and uploaded to GitHub Actions as an **Artifact** for compliance and review.

---

## 🚀 Key Highlights & Differentiators

* **Custom Aggregation over Out-of-the-Box:** Instead of just dropping a generic GitHub Action into a workflow, this pipeline uses a custom Python engine to ingest JSON outputs from multiple disparate tools, standardizing their severities (e.g., mapping Semgrep's INFO/WARNING/ERROR to LOW/MEDIUM/HIGH) into a single unified risk profile.
* **Context-Aware Security:** Demonstrates an understanding that a vulnerability in a test environment isn't as critical as the same vulnerability in production. The dynamic multiplier reflects real-world DevSecOps maturity.
* **Active Security Gate:** The pipeline doesn't just act as a passive scanner; it actively enforces governance by deliberately returning exit codes to block risky deployments.

---

## 📂 Project Structure

```text
devsecops-project/
├── .github/workflows/security.yml  # The CI/CD GitHub Actions definition
├── app.py                          # Sample Python application (contains intentional vulnerabilities for testing)
├── requirements.txt                # Python dependencies (contains vulnerable packages for testing)
├── risk_engine.py                  # The custom Python script that calculates risk scores
└── dashboard_generator.py          # Generates the visual HTML report
```

---

## 💻 How to Run & Test Locally

You can test the Risk Engine on your own machine. 

### 1. Install Requirements
```bash
pip install bandit semgrep pip-audit
```

### 2. Run the Scanners
```bash
python -m bandit -r . -x ./venv,./.venv,./.git -f json -o bandit-results.json --exit-zero
python -m semgrep scan --config=auto --exclude=venv --exclude=.venv --exclude=.git --json --output=semgrep-results.json
python -m pip_audit -r requirements.txt -f json -o dependency-results.json || echo '{"dependencies": []}' > dependency-results.json
```

### 3. Run the Engine & Dashboard
Test how the risk changes by pretending to be on different branches:
```powershell
# Test as if deploying to DEV (Should be MEDIUM risk, passes)
$env:GITHUB_REF_NAME="dev"; python risk_engine.py; python dashboard_generator.py

# Test as if deploying to MAIN (Should be CRITICAL risk, fails)
$env:GITHUB_REF_NAME="main"; python risk_engine.py; python dashboard_generator.py
```
