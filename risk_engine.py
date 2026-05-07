import json
import sys
import os
from datetime import datetime

SEVERITY_WEIGHT = {
    "LOW": 1,
    "MEDIUM": 3,
    "HIGH": 5,
    "CRITICAL": 8
}

BRANCH_WEIGHT = {
    "dev": 1,
    "staging": 2,
    "main": 3
}

def safe_load(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return {}

def count_vulnerabilities(data, severity_key="issue_severity", result_key="results"):
    """Count vulnerabilities by severity."""
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for item in data.get(result_key, []):
        severity = item.get(severity_key, "LOW").upper()
        if severity in severity_counts:
            severity_counts[severity] += 1
    return severity_counts

def get_bandit_score_and_details():
    data = safe_load("bandit-results.json")
    severity_counts = count_vulnerabilities(data, "issue_severity")
    max_score = 0
    for issue in data.get("results", []):
        severity = issue.get("issue_severity", "LOW")
        max_score = max(max_score, SEVERITY_WEIGHT.get(severity.upper(), 1))
    return max_score, severity_counts, len(data.get("results", []))

def get_semgrep_score_and_details():
    data = safe_load("semgrep-results.json")
    severity_counts = count_vulnerabilities(
        data,
        severity_key="extra.severity",
        result_key="results"
    )
    # Properly count severity from nested structure and normalize
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    max_score = 0
    
    for result in data.get("results", []):
        severity = result.get("extra", {}).get("severity", "LOW").upper()
        
        # Normalize Semgrep severities
        if severity == "ERROR":
            severity = "HIGH"
        elif severity == "WARNING":
            severity = "MEDIUM"
        elif severity == "INFO":
            severity = "LOW"
            
        if severity in severity_counts:
            severity_counts[severity] += 1
            
        max_score = max(max_score, SEVERITY_WEIGHT.get(severity, 1))
        
    return max_score, severity_counts, len(data.get("results", []))

def get_dependency_score_and_details():
    data = safe_load("dependency-results.json")
    dependencies = data.get("dependencies", [])
    vuln_count = 0
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    
    for dep in dependencies:
        for vuln in dep.get("vulns", []):
            vuln_count += 1
            # Default to HIGH for dependencies without severity info
            severity = "HIGH"
            severity_counts[severity] += 1
    
    score = 0
    if vuln_count >= 5:
        score = 8
    elif vuln_count >= 3:
        score = 5
    elif vuln_count >= 1:
        score = 3
    return score, severity_counts, vuln_count

def determine_risk(score):
    if score >= 20:
        return "CRITICAL"
    elif score >= 12:
        return "HIGH"
    elif score >= 6:
        return "MEDIUM"
    else:
        return "LOW"

def generate_risk_report(branch, bandit_score, bandit_details, semgrep_score, semgrep_details, 
                        dependency_score, dependency_details, final_score, overall_risk):
    """Generate a comprehensive risk summary report."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "branch": branch,
        "overall_risk": overall_risk,
        "final_score": final_score,
        "components": {
            "bandit": {
                "score": bandit_score,
                "total_findings": bandit_details["total"],
                "severity_distribution": bandit_details["severity_counts"]
            },
            "semgrep": {
                "score": semgrep_score,
                "total_findings": semgrep_details["total"],
                "severity_distribution": semgrep_details["severity_counts"]
            },
            "dependencies": {
                "score": dependency_score,
                "total_vulnerabilities": dependency_details["total"],
                "severity_distribution": dependency_details["severity_counts"]
            }
        },
        "policy_enforcement": {
            "rule": "Fail if risk is HIGH or CRITICAL",
            "passed": overall_risk in ["LOW", "MEDIUM"],
            "requires_remediation": overall_risk in ["HIGH", "CRITICAL"]
        }
    }
    return report

if __name__ == "__main__":
    branch = os.getenv("GITHUB_REF_NAME", "dev")

    bandit_score, bandit_severity_counts, bandit_total = get_bandit_score_and_details()
    semgrep_score, semgrep_severity_counts, semgrep_total = get_semgrep_score_and_details()
    dependency_score, dependency_severity_counts, dependency_total = get_dependency_score_and_details()

    base_score = max(bandit_score, semgrep_score, dependency_score)
    branch_multiplier = BRANCH_WEIGHT.get(branch, 1)

    final_score = base_score * branch_multiplier
    overall_risk = determine_risk(final_score)

    # Print summary
    print("=" * 60)
    print("SECURITY RISK ASSESSMENT")
    print("=" * 60)
    print(f"Branch: {branch}")
    print(f"Bandit Score: {bandit_score} ({bandit_total} findings)")
    print(f"  Severity: {bandit_severity_counts}")
    print(f"Semgrep Score: {semgrep_score} ({semgrep_total} findings)")
    print(f"  Severity: {semgrep_severity_counts}")
    print(f"Dependency Score: {dependency_score} ({dependency_total} vulnerabilities)")
    print(f"  Severity: {dependency_severity_counts}")
    print(f"Base Score: {base_score}")
    print(f"Branch Multiplier: {branch_multiplier}x")
    print(f"Final Risk Score: {final_score}")
    print(f"Overall Risk Level: {overall_risk}")
    print("=" * 60)

    # Generate risk report
    report = generate_risk_report(
        branch,
        bandit_score,
        {"severity_counts": bandit_severity_counts, "total": bandit_total},
        semgrep_score,
        {"severity_counts": semgrep_severity_counts, "total": semgrep_total},
        dependency_score,
        {"severity_counts": dependency_severity_counts, "total": dependency_total},
        final_score,
        overall_risk
    )
    
    with open("risk-summary.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nRisk summary saved to risk-summary.json")

    # Policy enforcement: Fail if HIGH or CRITICAL
    if overall_risk in ["HIGH", "CRITICAL"]:
        print(f"\n[VIOLATION] POLICY VIOLATION: Risk level is {overall_risk}")
        print("Pipeline will FAIL. Remediation required.")
        sys.exit(1)
    else:
        print(f"\n[PASSED] POLICY PASSED: Risk level is {overall_risk}")
        sys.exit(0)