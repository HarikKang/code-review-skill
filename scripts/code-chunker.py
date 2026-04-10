#!/usr/bin/env python3
import argparse
import os
import sys
import json
from typing import List, Dict, Optional
from pathlib import Path


def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
    }
    return lang_map.get(ext, 'unknown')


def chunk_python(code: str, max_lines: int = 200, overlap: int = 2) -> List[Dict]:
    chunks = []
    lines = code.split('\n')
    total_lines = len(lines)

    try:
        import ast
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    start = node.lineno - 1
                    end = node.end_lineno
                    chunk_lines = lines[start:end]
                    if len(chunk_lines) <= max_lines:
                        chunks.append({
                            'type': node.__class__.__name__,
                            'name': node.name,
                            'start_line': node.lineno,
                            'end_line': node.end_lineno,
                            'content': '\n'.join(chunk_lines)
                        })
    except Exception:
        pass

    if not chunks:
        return chunk_by_lines(code, max_lines, overlap)

    return chunks


def chunk_javascript(code: str, max_lines: int = 200, overlap: int = 2) -> List[Dict]:
    chunks = []
    lines = code.split('\n')
    total_lines = len(lines)

    try:
        import esprima
        tree = esprima.parse(code, loc=True)
        for node in tree.body:
            if hasattr(node, 'loc') and hasattr(node, 'loc', 'start') and hasattr(node, 'loc', 'end'):
                start = node.loc.start.line - 1
                end = node.loc.end.line
                chunk_lines = lines[start:end]
                if len(chunk_lines) <= max_lines:
                    chunks.append({
                        'type': type(node).__name__,
                        'name': getattr(node, 'id', None) or getattr(node, 'key', None) or 'anonymous',
                        'start_line': start + 1,
                        'end_line': end,
                        'content': '\n'.join(chunk_lines)
                    })
    except Exception:
        pass

    if not chunks:
        return chunk_by_lines(code, max_lines, overlap)

    return chunks


def chunk_java(code: str, max_lines: int = 200, overlap: int = 2) -> List[Dict]:
    return chunk_by_lines(code, max_lines, overlap)


def chunk_by_lines(code: str, max_lines: int = 200, overlap: int = 2) -> List[Dict]:
    chunks = []
    lines = code.split('\n')
    total_lines = len(lines)

    i = 0
    chunk_id = 1
    while i < total_lines:
        end = min(i + max_lines, total_lines)
        chunk_content = lines[i:end]
        overlap_start = max(0, end - overlap) if end < total_lines else i

        chunks.append({
            'type': 'block',
            'name': f'chunk_{chunk_id}',
            'start_line': i + 1,
            'end_line': end,
            'content': '\n'.join(chunk_content),
            'overlap_lines': overlap_start
        })

        i = i + max_lines - overlap
        chunk_id += 1

    return chunks


def chunk_code(file_path: str, max_lines: int = 200, overlap: int = 2) -> List[Dict]:
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    language = detect_language(file_path)

    if language == 'python':
        return chunk_python(code, max_lines, overlap)
    elif language in ('javascript', 'typescript'):
        return chunk_javascript(code, max_lines, overlap)
    elif language == 'java':
        return chunk_java(code, max_lines, overlap)
    else:
        return chunk_by_lines(code, max_lines, overlap)


def chunk_diff(diff_content: str, max_lines: int = 200) -> List[Dict]:
    chunks = []
    current_chunk = []
    current_lines = 0

    for line in diff_content.split('\n'):
        if line.startswith('diff') or line.startswith('@@'):
            if current_chunk:
                chunks.append({
                    'content': '\n'.join(current_chunk),
                    'lines': current_lines
                })
            current_chunk = [line]
            current_lines = 1
        else:
            current_chunk.append(line)
            if not line.startswith('\\'):
                current_lines += 1

        if current_lines >= max_lines:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'lines': current_lines
            })
            current_chunk = []
            current_lines = 0

    if current_chunk:
        chunks.append({
            'content': '\n'.join(current_chunk),
            'lines': current_lines
        })

    return chunks


def main():
    parser = argparse.ArgumentParser(description="使用AST技术对大型代码进行分块")
    parser.add_argument("--file", "-f", help="待分块的源文件")
    parser.add_argument("--diff", "-d", help="待分块的diff文件")
    parser.add_argument("--output-dir", "-o", default="chunks", help="输出目录（默认：chunks）")
    parser.add_argument("--max-lines", type=int, default=200, help="每个代码块最大行数（默认：200）")
    parser.add_argument("--overlap", type=int, default=2, help="代码块重叠行数（默认：2）")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")

    args = parser.parse_args()

    if not args.file and not args.diff:
        parser.error("请提供 --file 或 --diff 参数")

    os.makedirs(args.output_dir, exist_ok=True)

    if args.file:
        chunks = chunk_code(args.file, args.max_lines, args.overlap)
        file_name = os.path.basename(args.file)
    elif args.diff:
        chunks = chunk_diff(args.diff, args.max_lines)
        file_name = "diff"

    if args.json:
        output = {
            'file': args.file or args.diff,
            'total_chunks': len(chunks),
            'chunks': chunks
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for i, chunk in enumerate(chunks):
            output_file = os.path.join(args.output_dir, f"{file_name}_chunk_{i+1}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"--- Chunk {i+1}/{len(chunks)} ---\n")
                f.write(f"Type: {chunk.get('type', 'unknown')}\n")
                f.write(f"Name: {chunk.get('name', 'N/A')}\n")
                f.write(f"Lines: {chunk.get('start_line', '?')}-{chunk.get('end_line', '?')}\n")
                f.write(f"---\n")
                f.write(chunk.get('content', ''))
            print(f"已生成: {output_file}")

    print(f"共生成 {len(chunks)} 个代码块")

    return 0


if __name__ == "__main__":
    sys.exit(main())