#!/usr/bin/env python3
import argparse
import os
import sys
import hashlib
from typing import Optional

MOCK_PROMPT_PLATFORM = """
# AI代码评审提示词

## 核心指令
你是一位专业代码评审专家，精通：
- 软件安全最佳实践
- 性能优化
- 代码可维护性与可读性
- 设计模式与SOLID原则
- 测试覆盖率与质量

## 评审指南

### 严重问题（必须报告）
- 安全漏洞（SQL注入、XSS等）
- 内存泄漏与资源管理问题
- 竞态条件与并发bug
- 可能导致崩溃的逻辑错误

### 警告（应该报告）
- 代码重复超过3次
- 复杂函数（超过50行）
- 缺失错误处理
- 可以使用O(n)算法却使用了O(n²)

### 建议（最好报告）
- 命名改进
- 注释清晰度
- 代码组织
- 文档完整性

## 语言特定规则

### Python
- 遵循PEP 8风格指南
- 适当使用类型提示
- 避免通配符导入
- 使用列表推导式代替循环

### JavaScript/TypeScript
- 遵循ESLint推荐规则
- 使用const/let代替var
- 回调函数优先使用箭头函数
- 正确处理async/await错误

### Java
- 遵循Oracle命名规范
- 使用try-with-resources
- 避免 raw type 泛型
- 实现正确的equals/hashCode

## 输出格式
以JSON格式提供评审发现，包含：
- file: 源文件路径
- line: 行号
- severity: critical/warning/suggestion
- category: security/performance/maintainability/best-practice
- message: 问题描述
- suggestion: 建议修复方案
"""

DEFAULT_MAX_TOKENS = 8000
TOKEN_BUFFER = 500


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def truncate_prompt(prompt: str, max_tokens: int) -> str:
    current_tokens = estimate_tokens(prompt)
    if current_tokens <= max_tokens:
        return prompt

    priority_sections = [
        ("核心指令", 2000),
        ("语言特定规则", 1500),
        ("评审指南", 1500),
        ("输出格式", 500),
    ]

    truncated = []
    remaining = max_tokens - TOKEN_BUFFER

    for section_name, section_budget in priority_sections:
        start = prompt.find(f"## {section_name}")
        if start == -1:
            continue

        end = prompt.find("## ", start + 3)
        if end == -1:
            end = len(prompt)

        section = prompt[start:end]
        section_tokens = estimate_tokens(section)

        if section_tokens <= remaining:
            truncated.append(section)
            remaining -= section_tokens
        else:
            chars_to_take = remaining * 4
            truncated.append(section[:chars_to_take] + "\n\n[...已裁剪...]")
            break

    return "\n\n".join(truncated)


def fetch_prompt_from_platform(prompt_type: str, platform_url: Optional[str] = None,
                                api_key: Optional[str] = None) -> str:
    return MOCK_PROMPT_PLATFORM


def save_prompt_cache(prompt: str, prompt_type: str) -> str:
    cache_dir = os.path.join(os.path.dirname(__file__), "..", ".cache")
    os.makedirs(cache_dir, exist_ok=True)

    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    cache_file = os.path.join(cache_dir, f"prompt_{prompt_type}_{prompt_hash}.md")

    with open(cache_file, 'w') as f:
        f.write(prompt)

    return cache_file


def main():
    parser = argparse.ArgumentParser(description="从提示词平台获取AI代码评审提示词")
    parser.add_argument("--type", "-t", default="code-review", help="提示词类型（默认：code-review）")
    parser.add_argument("--output", "-o", default="prompt.md", help="输出文件路径（默认：prompt.md）")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help=f"最大token数（默认：{DEFAULT_MAX_TOKENS}）")
    parser.add_argument("--platform-url", default=os.getenv("PROMPT_PLATFORM_URL"), help="提示词平台URL")
    parser.add_argument("--api-key", default=os.getenv("PROMPT_PLATFORM_KEY"), help="API密钥")
    parser.add_argument("--no-cache", action="store_true", help="禁用提示词缓存")
    parser.add_argument("--split", "-s", type=int, default=0, help="将提示词拆分为N块（供orchestrator使用）")
    parser.add_argument("--split-dir", default="prompts", help="拆分块输出目录（默认：prompts）")

    args = parser.parse_args()

    print(f"正在获取 {args.type} 提示词...")

    prompt = fetch_prompt_from_platform(args.type, args.platform_url, args.api_key)

    original_tokens = estimate_tokens(prompt)
    if original_tokens > args.max_tokens:
        print(f"提示词过长（{original_tokens} tokens），正在裁剪...")
        prompt = truncate_prompt(prompt, args.max_tokens)
        truncated_tokens = estimate_tokens(prompt)
        print(f"已裁剪至约 {truncated_tokens} tokens")

    if args.split > 0:
        os.makedirs(args.split_dir, exist_ok=True)
        lines = prompt.split('\n')
        chunk_size = len(lines) // args.split
        for i in range(args.split):
            start = i * chunk_size
            end = start + chunk_size if i < args.split - 1 else len(lines)
            chunk = '\n'.join(lines[start:end])
            chunk_file = os.path.join(args.split_dir, f"prompt_{i+1:03d}.md")
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
            print(f"已生成: {chunk_file}")
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"提示词已保存至: {args.output}")

    if not args.no_cache:
        cache_path = save_prompt_cache(prompt, args.type)
        print(f"缓存至: {cache_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())