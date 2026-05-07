#!/usr/bin/env python3
"""Generate HTML security dashboard from risk assessment reports."""

import json
import sys
import os
import webbrowser
from pathlib import Path

def load_report(filename):
    """Load a JSON report file."""
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def generate_dashboard():
    """Generate HTML dashboard with security metrics."""
    risk_report = load_report("risk-summary.json")
    
    if not risk_report:
        print("Error: risk-summary.json not found")
        return False
    
    overall_risk = risk_report["overall_risk"]
    final_score = risk_report["final_score"]
    timestamp = risk_report["timestamp"]
    branch = risk_report["branch"]
    
    # Determine colors based on risk level
    risk_colors = {
        "CRITICAL": "#d32f2f",
        "HIGH": "#f57c00",
        "MEDIUM": "#fbc02d",
        "LOW": "#388e3c"
    }
    
    risk_color = risk_colors.get(overall_risk, "#999999")
    
    # Prepare data for charts
    bandit = risk_report["components"]["bandit"]
    semgrep = risk_report["components"]["semgrep"]
    deps = risk_report["components"]["dependencies"]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Risk Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .timestamp {{
            color: #bbb;
            font-size: 0.9em;
        }}
        
        .risk-banner {{
            background-color: {risk_color};
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .risk-info {{
            flex: 1;
        }}
        
        .risk-level {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .risk-score {{
            font-size: 1.5em;
            opacity: 0.9;
        }}
        
        .risk-icon {{
            font-size: 4em;
            opacity: 0.3;
            margin-left: 30px;
        }}
        
        .policy-status {{
            background-color: {risk_color};
            padding: 15px 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }}
        
        .card h3 {{
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #64b5f6;
        }}
        
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .stat:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            color: #bbb;
        }}
        
        .stat-value {{
            font-weight: bold;
            color: #fff;
        }}
        
        .chart-container {{
            position: relative;
            margin-top: 20px;
        }}
        
        .severity-bar {{
            display: flex;
            margin: 10px 0;
            font-size: 0.9em;
        }}
        
        .severity-label {{
            width: 80px;
            font-weight: bold;
        }}
        
        .severity-count {{
            color: #bbb;
            margin-left: 10px;
        }}
        
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        
        footer {{
            text-align: center;
            color: #888;
            margin-top: 40px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 20px;
        }}
        
        .metadata {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .meta-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 5px;
        }}
        
        .meta-label {{
            color: #888;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .meta-value {{
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 Security Risk Dashboard</h1>
            <p class="timestamp">Report generated: {timestamp}</p>
        </header>
        
        <div class="risk-banner">
            <div class="risk-info">
                <div class="risk-level">{overall_risk} RISK</div>
                <div class="risk-score">Score: {final_score}/24</div>
            </div>
            <div class="risk-icon">
                {'⚠️' if overall_risk in ['HIGH', 'CRITICAL'] else '✓'}
            </div>
        </div>
        
        <div class="policy-status">
            {'❌ POLICY VIOLATION - Pipeline will FAIL' if risk_report['policy_enforcement']['requires_remediation'] else '✅ POLICY PASSED - Pipeline continues'}
        </div>
        
        <div class="metadata">
            <div class="meta-item">
                <div class="meta-label">Branch</div>
                <div class="meta-value">{branch}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Rule</div>
                <div class="meta-value">{risk_report['policy_enforcement']['rule']}</div>
            </div>
        </div>
        
        <div class="grid">
            <!-- Bandit Card -->
            <div class="card">
                <h3>🐍 Bandit (Python Security)</h3>
                <div class="stat">
                    <span class="stat-label">Findings</span>
                    <span class="stat-value">{bandit['total_findings']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Score</span>
                    <span class="stat-value">{bandit['score']}/8</span>
                </div>
                <div style="margin-top: 15px;">
                    <div class="severity-bar">
                        <div class="severity-label critical">CRITICAL</div>
                        <div class="severity-count">{bandit['severity_distribution'].get('CRITICAL', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label high">HIGH</div>
                        <div class="severity-count">{bandit['severity_distribution'].get('HIGH', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label medium">MEDIUM</div>
                        <div class="severity-count">{bandit['severity_distribution'].get('MEDIUM', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label low">LOW</div>
                        <div class="severity-count">{bandit['severity_distribution'].get('LOW', 0)}</div>
                    </div>
                </div>
            </div>
            
            <!-- Semgrep Card -->
            <div class="card">
                <h3>🔍 Semgrep (Code Patterns)</h3>
                <div class="stat">
                    <span class="stat-label">Findings</span>
                    <span class="stat-value">{semgrep['total_findings']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Score</span>
                    <span class="stat-value">{semgrep['score']}/8</span>
                </div>
                <div style="margin-top: 15px;">
                    <div class="severity-bar">
                        <div class="severity-label critical">CRITICAL</div>
                        <div class="severity-count">{semgrep['severity_distribution'].get('CRITICAL', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label high">HIGH</div>
                        <div class="severity-count">{semgrep['severity_distribution'].get('HIGH', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label medium">MEDIUM</div>
                        <div class="severity-count">{semgrep['severity_distribution'].get('MEDIUM', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label low">LOW</div>
                        <div class="severity-count">{semgrep['severity_distribution'].get('LOW', 0)}</div>
                    </div>
                </div>
            </div>
            
            <!-- Dependency Card -->
            <div class="card">
                <h3>📦 Dependencies (pip-audit)</h3>
                <div class="stat">
                    <span class="stat-label">Vulnerabilities</span>
                    <span class="stat-value">{deps['total_vulnerabilities']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Score</span>
                    <span class="stat-value">{deps['score']}/8</span>
                </div>
                <div style="margin-top: 15px;">
                    <div class="severity-bar">
                        <div class="severity-label critical">CRITICAL</div>
                        <div class="severity-count">{deps['severity_distribution'].get('CRITICAL', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label high">HIGH</div>
                        <div class="severity-count">{deps['severity_distribution'].get('HIGH', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label medium">MEDIUM</div>
                        <div class="severity-count">{deps['severity_distribution'].get('MEDIUM', 0)}</div>
                    </div>
                    <div class="severity-bar">
                        <div class="severity-label low">LOW</div>
                        <div class="severity-count">{deps['severity_distribution'].get('LOW', 0)}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>💡 DevSecOps Pipeline - Automated Security Risk Engine</p>
        </footer>
    </div>
</body>
</html>
"""
    
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    abs_path = os.path.abspath("dashboard.html")
    print(f"SUCCESS: Dashboard generated!")
    print(f"Link: file:///{abs_path.replace(chr(92), '/')}")
    
    # Automatically open in the default web browser
    try:
        webbrowser.open(f"file:///{abs_path.replace(chr(92), '/')}")
    except:
        pass
        
    return True

if __name__ == "__main__":
    if not generate_dashboard():
        sys.exit(1)
