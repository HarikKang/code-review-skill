# AI代码评审Skill - 技术参考文档

## 目录

1. [架构设计](#架构设计)
2. [脚本详解](#脚本详解)
3. [API集成](#api集成)
4. [故障排查](#故障排查)

---

## 架构设计

### 整体流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 获取提示词   │ -> │ 代码分块    │ -> │ 执行评审    │ -> │ 生成报告    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 组件说明

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| fetch-prompt.py | 获取并裁剪提示词 | prompt_type | prompt.md |
| code-chunker.py | AST分块处理 | source_file/diff | chunks/ |
| review-reporter.py | 生成JSON报告 | markdown/json | review-result.json |

---

## 脚本详解

### fetch-prompt.py

**功能**：
- 从提示词平台获取评审提示词
- 智能裁剪超长提示词
- 本地缓存机制

**关键参数**：
- `--type`: 提示词类型（默认code-review）
- `--max-tokens`: 最大token数（默认8000）
- `--platform-url`: 提示词平台URL
- `--no-cache`: 禁用缓存

**裁剪策略**：
1. 核心指令（保留2000 tokens）
2. 语言特定规则（保留1500 tokens）
3. 评审指南（保留1500 tokens）
4. 输出格式（保留500 tokens）

### code-chunker.py

**功能**：
- 基于AST的代码分块
- 支持多种语言
- 处理大型diff文件

**语言支持**：
- Python: 使用ast模块
- JavaScript/TypeScript: 需要esprima库
- 其他语言: 基于行数分块

**参数**：
- `--file`: 源文件路径
- `--diff`: diff文件路径
- `--max-lines`: 每块最大行数（默认200）
- `--overlap`: 重叠行数（默认2）

### review-reporter.py

**功能**：
- 解析AI评审输出
- 提取结构化发现
- 计算汇总统计

**输入格式**：
- Markdown格式
- JSON格式
- 混合格式

**输出字段**：
- review_id: 评审唯一ID
- timestamp: 评审时间
- files_reviewed: 评审的文件列表
- summary: 问题汇总
- findings: 具体发现列表
- metrics: 代码指标

---

## API集成

### 提示词平台API

**请求格式**：
```bash
curl -X GET "https://prompt-platform.example.com/api/prompts/code-review" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**响应格式**：
```json
{
  "id": "prompt_xxx",
  "content": "# AI代码评审提示词...",
  "version": "1.0",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### AI模型调用

**请求格式**（示例）：
```python
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": code_changes}
    ],
    temperature=0.3,
    max_tokens=4000
)
```

---

## 故障排查

### 常见问题

**问题1：提示词获取失败**
- 检查PROMPT_PLATFORM_URL环境变量
- 验证API密钥是否有效
- 确认网络连接

**问题2：代码分块失败**
- 检查Python的ast模块是否可用
- 对于非Python文件，自动降级到行数分块

**问题3：报告生成失败**
- 确认输入文件编码为UTF-8
- 检查JSON格式是否正确

### 日志级别

脚本支持标准Python日志，可通过环境变量控制：
```bash
export LOG_LEVEL=DEBUG
```

---

## 扩展开发

### 添加新语言支持

在code-chunker.py中添加新的分块函数：

```python
def chunk_language_name(code: str, max_lines: int = 200, overlap: int = 2) -> List[Dict]:
    # 实现AST分块逻辑
    pass

# 在chunk_code函数中添加
elif language == 'language_name':
    return chunk_language_name(code, max_lines, overlap)
```

### 自定义评审规则

在fetch-prompt.py的MOCK_PROMPT_PLATFORM中添加：

```markdown
### 自定义规则
- 业务规则1
- 业务规则2
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024-01-01 | 初始版本 |