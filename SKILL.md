---
name: code-review
description: AI代码评审助手。用于评审代码变更、Pull Request，或当用户请求代码分析、缺陷检测、安全审查、最佳实践反馈时。支持多语言并提供结构化JSON输出。
license: MIT
compatibility: 需要Python 3.10+、git及访问提示词平台
metadata:
  author: HarikKang
  version: "1.0"
  supported_languages: ["python", "javascript", "typescript", "java", "go", "rust", "c++"]
---

# AI代码评审Skill

## 概述

利用平台agent能力进行AI驱动的代码评审：
1. 通过librarian获取评审提示词
2. 逐文件并行调用agent评审
3. 输出JSON报告

## 工作流程

### 第1步：获取评审提示词

使用librarian agent从提示词平台获取：

```
用librarian获取code-review类型的评审提示词
```

### 第2步：准备待评审文件

获取PR/变更的文件列表：

```
用git获取变更文件：git diff --name-only HEAD~1
```

### 第3步：并行评审

使用task()并行调用多个agent评审：

```python
# 每个agent评审一个文件
task(category="ultrabrain", prompt=f"""
提示词：{prompt}
待评审文件：{file_path}
输出JSON格式评审结果
""")
```

### 第4步：生成报告

合并结果并写入review-result.json：

```json
{
  "review_id": "review_xxx",
  "timestamp": "...",
  "files_reviewed": [...],
  "summary": {...},
  "findings": [...],
  "metrics": {...}
}
```

## 上下文管理

- 每个agent session：1个文件 + 部分提示词 + 前序摘要
- 大文件使用ast_grep_search分块处理
- 多文件用task并行评审

## 脚本说明

- `scripts/fetch-prompt.py` - 备选：本地获取提示词
- `scripts/code-chunker.py` - 备选：大文件分块

## 环境变量

- `PROMPT_PLATFORM_URL` - 提示词平台API
- `PROMPT_PLATFORM_KEY` - API密钥