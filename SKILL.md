---
name: code-review
description: AI代码评审助手。用于评审代码变更、Pull Request，或当用户请求代码分析、缺陷检测、安全审查、最佳实践反馈时。支持多语言并提供结构化JSON输出。
license: MIT
compatibility: 需要 Python 3.10+、git 及提示词平台API访问权限
metadata:
  author: HarikKang
  version: "1.0"
  supported_languages: ["python", "javascript", "typescript", "java", "go", "rust", "c++"]
---

# AI代码评审Skill

## 概述

此Skill执行AI驱动的代码评审，流程如下：
1. 从提示词平台获取评审提示词
2. 通过上下文管理分析代码变更
3. 使用AST技术处理大型代码变更
4. 输出结构化JSON报告

## 工作流程

### 第1步：获取评审提示词

从提示词平台获取AI评审提示词：

```bash
python3 scripts/fetch-prompt.py --type code-review --output temp-prompt.md
```

如果提示词超过8000 tokens，将自动按优先级裁剪：
1. 核心指令
2. 语言特定规则
3. 常见模式
4. 边缘情况

### 第2步：准备待评审代码

**Git diff格式：**
```bash
git diff HEAD~1 --no-color > changes.diff
```

**大型代码库处理：**
使用AST分块处理超过500行的文件：
```bash
python3 scripts/code-chunker.py --file large_file.py --output-dir chunks/
```

### 第3步：执行AI评审

向AI模型发送准备好的上下文，包含：
- 已裁剪的提示词（如需要）
- 代码变更/代码块
- 上一轮评审摘要（如为多轮）

**上下文管理：**
- 第一轮：完整上下文
- 后续轮次：将前序发现总结为要点，仅保留关键代码片段
- 每个文件最多3轮

### 第4步：生成报告

输出结构化JSON至`review-result.json`：

```bash
python3 scripts/review-reporter.py --input review-output.md --output review-result.json
```

## 输入格式

### Git Diff
```
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,7 @@
+import logging
 def hello():
+    print("debug")
```

### 文件列表
```
src/main.py
src/utils.py
tests/test_main.py
```

### Pull Request
```
PR #123: 添加用户认证
- 添加登录/登出接口
- 实现JWT令牌
- 添加密码哈希
```

## 输出格式

```json
{
  "review_id": "review_20240410_001",
  "timestamp": "2024-04-10T10:30:00Z",
  "files_reviewed": ["src/main.py", "src/auth.py"],
  "summary": {
    "total_issues": 5,
    "critical": 1,
    "warnings": 3,
    "suggestions": 1
  },
  "findings": [
    {
      "file": "src/main.py",
      "line": 42,
      "severity": "critical",
      "category": "security",
      "message": "SQL注入漏洞",
      "suggestion": "使用参数化查询"
    }
  ],
  "metrics": {
    "complexity": "medium",
    "test_coverage": "75%",
    "maintainability": "good"
  }
}
```

## 常见问题与解决方案

### 问题：上下文窗口溢出
**解决方案**：使用摘要-评审模式
1. 将前序评审总结为要点
2. 仅保留最关键的代码片段
3. 每轮最多3个文件

### 问题：大型文件处理
**解决方案**：基于AST的分块
- 按函数/类边界分割
- 代码块重叠2行以保持上下文
- 每个代码块最多200行

### 问题：多语言项目
**解决方案**：语言检测+针对性规则
- 根据文件扩展名自动检测语言
- 应用语言特定的评审规则
- 处理混合语言的PR

## 脚本说明

- `scripts/fetch-prompt.py` - 获取并裁剪提示词
- `scripts/code-chunker.py` - 基于AST的代码分块
- `scripts/review-reporter.py` - 生成JSON报告

## 使用示例

```bash
# 基础评审
code-review --diff changes.diff --output review-result.json

# 评审特定文件
code-review --files src/*.py --output review-result.json

# 带上下文摘要的评审
code-review --diff changes.diff --summary prev-summary.md --output review-result.json
```

## 环境变量

- `PROMPT_PLATFORM_URL` - 提示词平台API端点
- `PROMPT_PLATFORM_KEY` - API认证密钥
- `REVIEW_MODEL` - 使用的AI模型（默认：gpt-4）
- `MAX_TOKENS` - 最大上下文tokens（默认：8000）