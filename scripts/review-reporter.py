#!/usr/bin/env python3
import argparse
import json
import sys
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


SEVERITY_ORDER = {'critical': 0, 'warning': 1, 'suggestion': 2}
CATEGORY_ORDER = {'security': 0, 'performance': 1, 'maintainability': 2, 'best-practice': 3}


def generate_review_id() -> str:
    return f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def parse_markdown_findings(markdown_content: str) -> List[Dict]:
    findings = []
    current_file = None
    current_severity = None
    current_category = None

    lines = markdown_content.split('\n')
    for line in lines:
        file_match = re.match(r'^##?\s*文件[:：]\s*(.+)$', line)
        if file_match:
            current_file = file_match.group(1).strip()
            continue

        severity_match = re.match(r'^###?\s*(严重|警告|建议|CRITICAL|WARNING|SUGGESTION)[:：]?\s*(.*)$', line, re.IGNORECASE)
        if severity_match:
            sev = severity_match.group(1).lower()
            if sev in ['严重', 'critical']:
                current_severity = 'critical'
            elif sev in ['警告', 'warning']:
                current_severity = 'warning'
            else:
                current_severity = 'suggestion'
            continue

        finding_match = re.match(r'^\s*[-*]\s*(?:第\s*(\d+)\s*行|行\s*(\d+))?[:：]?\s*(.+)$', line)
        if finding_match and current_severity:
            line_num = finding_match.group(1) or finding_match.group(2)
            message = finding_match.group(3).strip()

            if line_num:
                try:
                    line_num = int(line_num)
                except ValueError:
                    line_num = None

            finding = {
                'file': current_file,
                'line': line_num,
                'severity': current_severity,
                'category': current_category or 'best-practice',
                'message': message,
                'suggestion': ''
            }
            findings.append(finding)

        category_match = re.match(r'^####?\s*类别[:：]\s*(.+)$', line)
        if category_match:
            current_category = category_match.group(1).strip().lower()
            if findings:
                findings[-1]['category'] = current_category

    return findings


def parse_ai_output(ai_output: str) -> Dict:
    json_match = re.search(r'\{[\s\S]*\}', ai_output)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {'raw_output': ai_output}


def calculate_summary(findings: List[Dict]) -> Dict:
    summary = {
        'total_issues': len(findings),
        'critical': 0,
        'warnings': 0,
        'suggestions': 0
    }

    for finding in findings:
        severity = finding.get('severity', 'suggestion')
        if severity == 'critical':
            summary['critical'] += 1
        elif severity == 'warning':
            summary['warnings'] += 1
        else:
            summary['suggestions'] += 1

    return summary


def calculate_metrics(findings: List[Dict], code_stats: Optional[Dict] = None) -> Dict:
    metrics = {
        'complexity': 'low',
        'test_coverage': 'unknown',
        'maintainability': 'good'
    }

    critical_count = sum(1 for f in findings if f.get('severity') == 'critical')
    warning_count = sum(1 for f in findings if f.get('severity') == 'warning')

    if critical_count >= 3:
        metrics['complexity'] = 'high'
        metrics['maintainability'] = 'poor'
    elif critical_count >= 1 or warning_count >= 5:
        metrics['complexity'] = 'medium'
        metrics['maintainability'] = 'fair'
    else:
        metrics['complexity'] = 'low'
        metrics['maintainability'] = 'good'

    return metrics


def extract_files_reviewed(findings: List[Dict]) -> List[str]:
    files = set()
    for finding in findings:
        if finding.get('file'):
            files.add(finding['file'])
    return sorted(list(files))


def generate_review_report(input_content: str, metadata: Optional[Dict] = None) -> Dict:
    findings = parse_markdown_findings(input_content)

    if not findings and metadata:
        ai_data = parse_ai_output(input_content)
        if 'findings' in ai_data:
            findings = ai_data['findings']
        elif 'issues' in ai_data:
            findings = ai_data['issues']

    summary = calculate_summary(findings)
    files_reviewed = extract_files_reviewed(findings)
    metrics = calculate_metrics(findings)

    report = {
        'review_id': generate_review_id(),
        'timestamp': datetime.now().isoformat() + 'Z',
        'files_reviewed': files_reviewed,
        'summary': summary,
        'findings': findings,
        'metrics': metrics
    }

    if metadata:
        report['metadata'] = metadata

    return report


def main():
    parser = argparse.ArgumentParser(description="生成AI代码评审JSON报告")
    parser.add_argument("--input", "-i", required=True, help="AI评审输出文件（Markdown或JSON格式）")
    parser.add_argument("--output", "-o", default="review-result.json", help="输出JSON文件路径（默认：review-result.json）")
    parser.add_argument("--format", choices=['markdown', 'json', 'auto'], default='auto', help="输入格式（默认：auto）")
    parser.add_argument("--metadata", help="额外元数据（JSON格式）")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"错误：输入文件不存在: {args.input}", file=sys.stderr)
        return 1

    with open(args.input, 'r', encoding='utf-8') as f:
        input_content = f.read()

    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            print(f"警告：元数据JSON解析失败: {e}", file=sys.stderr)

    report = generate_review_report(input_content, metadata)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"评审报告已生成: {args.output}")
    print(f"共发现 {report['summary']['total_issues']} 个问题", )
    print(f"  - 严重: {report['summary']['critical']}")
    print(f"  - 警告: {report['summary']['warnings']}")
    print(f"  - 建议: {report['summary']['suggestions']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())