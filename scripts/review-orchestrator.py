#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def load_prompt_chunks(prompt_dir: str) -> List[str]:
    prompt_files = sorted(Path(prompt_dir).glob("prompt_*.md"))
    chunks = []
    for pf in prompt_files:
        with open(pf, 'r', encoding='utf-8') as f:
            chunks.append(f.read())
    return chunks


def load_files_to_review(files_file: str) -> List[str]:
    with open(files_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def generate_session_id(file_idx: int, chunk_idx: int) -> str:
    return f"review_f{file_idx}_c{chunk_idx}_{datetime.now().strftime('%H%M%S')}"


def build_review_request(prompt_chunk: str, file_path: str, previous_summary: Optional[str] = None) -> str:
    return f"""# 代码评审请求

## 提示词
{prompt_chunk}

## 待评审文件
{file_path}

## 历史评审摘要
{previous_summary or '无'}

## 输出要求
请直接输出JSON格式的评审发现，不要包含其他内容。
"""


def call_ai_model(request: str, model: str = "gpt-4") -> str:
    return ""


def parse_review_result(ai_output: str) -> Dict:
    try:
        return json.loads(ai_output)
    except json.JSONDecodeError:
        return {"raw_output": ai_output, "parse_error": True}


def run_single_review(file_idx: int, file_path: str, prompt_chunks: List[str], 
                      model: str, output_dir: str) -> Dict:
    results = {
        'file': file_path,
        'file_index': file_idx,
        'chunks_reviewed': [],
        'findings': [],
        'summary': {}
    }

    previous_summary = None
    for chunk_idx, prompt_chunk in enumerate(prompt_chunks):
        session_id = generate_session_id(file_idx, chunk_idx)
        request = build_review_request(prompt_chunk, file_path, previous_summary)
        output_file = os.path.join(output_dir, f"session_{session_id}.json")
        
        print(f"  [{file_idx+1}] 文件 {chunk_idx+1}/{len(prompt_chunks)}: {session_id}")

        ai_output = call_ai_model(request, model)
        chunk_result = parse_review_result(ai_output)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': session_id,
                'file': file_path,
                'chunk_index': chunk_idx,
                'result': chunk_result
            }, f, ensure_ascii=False, indent=2)

        results['chunks_reviewed'].append({
            'chunk_idx': chunk_idx,
            'session_id': session_id,
            'output_file': output_file
        })

        if chunk_result.get('findings'):
            findings_str = ", ".join([f.get('message', '') for f in chunk_result['findings'][:3]])
            previous_summary = f"前期发现: {findings_str}"

    return results


def run_batch_review(files: List[str], prompt_dir: str, model: str, 
                     max_workers: int, output_dir: str) -> Dict:
    prompt_chunks = load_prompt_chunks(prompt_dir)
    
    if not prompt_chunks:
        print("错误：未找到提示词块，请先运行fetch-prompt.py进行拆分")
        return {}

    print(f"开始评审 {len(files)} 个文件")
    print(f"每个文件将使用 {len(prompt_chunks)} 个提示词块")
    print(f"预计总交互次数: {len(files) * len(prompt_chunks)}")
    print(f"使用 {max_workers} 个并发线程\n")

    os.makedirs(output_dir, exist_ok=True)

    all_results = []
    
    if max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_single_review, i, files[i], prompt_chunks, model, output_dir): i
                for i in range(len(files))
            }
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
    else:
        for i in range(len(files)):
            result = run_single_review(i, files[i], prompt_chunks, model, output_dir)
            all_results.append(result)

    return {
        'total_files': len(files),
        'total_chunks': len(prompt_chunks),
        'total_sessions': len(files) * len(prompt_chunks),
        'results': all_results
    }


def merge_results(all_results: Dict) -> Dict:
    merged = {
        'total_files': all_results['total_files'],
        'total_sessions': all_results['total_sessions'],
        'findings': [],
        'summary': {'critical': 0, 'warnings': 0, 'suggestions': 0}
    }

    for file_result in all_results['results']:
        for finding in file_result.get('findings', []):
            merged['findings'].append(finding)
            sev = finding.get('severity', 'suggestion')
            if sev == 'critical':
                merged['summary']['critical'] += 1
            elif sev == 'warning':
                merged['summary']['warnings'] += 1
            else:
                merged['summary']['suggestions'] += 1

    merged['summary']['total_issues'] = sum(merged['summary'].values())
    return merged


def main():
    parser = argparse.ArgumentParser(description="AI代码评审编排器 - 批量文件+分块提示词")
    parser.add_argument("--files", "-f", required=True, help="待评审文件列表（每行一个文件路径）")
    parser.add_argument("--prompt-dir", "-p", default="prompts", help="提示词块目录（默认：prompts）")
    parser.add_argument("--model", "-m", default="gpt-4", help="AI模型（默认：gpt-4）")
    parser.add_argument("--output", "-o", default="review-sessions", help="输出目录（默认：review-sessions）")
    parser.add_argument("--workers", "-w", type=int, default=4, help="并发线程数（默认：4）")
    parser.add_argument("--merge", action="store_true", help="合并所有结果")

    args = parser.parse_args()

    files = load_files_to_review(args.files)
    if not files:
        print(f"错误：文件列表为空或不存在: {args.files}")
        return 1

    results = run_batch_review(files, args.prompt_dir, args.model, args.workers, args.output)

    results_file = os.path.join(args.output, "batch-review-results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n评审完成:")
    print(f"  文件数: {results['total_files']}")
    print(f"  提示词块: {results['total_chunks']}")
    print(f"  总交互: {results['total_sessions']}")
    print(f"  结果: {results_file}")

    if args.merge:
        merged = merge_results(results)
        merged_file = os.path.join(args.output, "merged-review-result.json")
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"  合并结果: {merged_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())