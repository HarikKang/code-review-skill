# AI代码评审提示词模板

## 使用说明

此模板用于构建发送给AI模型的评审请求。根据实际需求选择合适的模块进行组合。

## 模板结构

```
[系统提示词]
你是专业的代码评审专家...

[评审上下文]
- 仓库信息
- 分支信息
- 变更概述

[代码变更]
## 文件: src/main.py
```python
+ 新增代码
- 删除代码
```

[评审要求]
1. 检查安全问题
2. 检查性能问题
3. 检查代码规范

[输出格式]
请以JSON格式输出评审结果...
```

## 模块说明

### 1. 系统提示词模块

包含AI角色定义、评审范围、评审标准。

### 2. 上下文模块

包含仓库、分支、PR描述等背景信息。

### 3. 代码模块

实际待评审的代码变更，支持：
- Git diff格式
- 完整的文件内容
- 代码块（分块后的结果）

### 4. 要求模块

具体的评审要求，如：
- 安全检查
- 性能检查
- 规范检查
- 最佳实践

### 5. 输出模块

期望的输出格式定义，通常为JSON结构。

## 完整示例

```markdown
## 角色
你是一位资深的代码评审专家，拥有10年以上开发经验，精通多种编程语言，熟悉软件安全、性能优化、代码质量等领域。

## 上下文
- 仓库: example/project
- 分支: feature/user-auth
- PR: #123 添加用户认证功能

## 变更概述
本次变更是为了实现用户登录/登出功能，包括JWT令牌生成、密码验证、会话管理等功能。

## 代码变更
### src/auth/login.py
```python
def login(username: str, password: str) -> str:
    user = db.query(username)
    if verify_password(user.password, password):
        return generate_token(user)
    raise AuthError("Invalid credentials")
```

## 评审要求
1. **安全检查**：检查是否存在安全漏洞
2. **代码质量**：检查代码可读性和可维护性
3. **性能考虑**：检查是否存在性能问题
4. **最佳实践**：检查是否符合语言最佳实践

## 输出格式
请以JSON格式输出，包含：
- severity: critical/warning/suggestion
- category: security/performance/maintainability/best-practice
- message: 问题描述
- suggestion: 修复建议
```

## 变量替换

| 变量 | 说明 | 示例 |
|------|------|------|
| {{REPO_NAME}} | 仓库名称 | example/project |
| {{BRANCH_NAME}} | 分支名称 | feature/auth |
| {{PR_NUMBER}} | PR编号 | #123 |
| {{PR_TITLE}} | PR标题 | 添加用户认证 |
| {{PR_DESCRIPTION}} | PR描述 | 本次变更实现... |
| {{FILE_PATH}} | 文件路径 | src/auth.py |
| {{DIFF_CONTENT}} | 代码变更 | diff内容 |

## 注意事项

1. **上下文长度**：确保总长度不超过模型的上下文限制
2. **关键信息优先**：重要的评审要求放在前面
3. **明确输出格式**：清晰定义期望的输出结构
4. **语言一致性**：提示词语言与输出格式语言保持一致