---
name: omp-multi-advisor-roster
description: 在 Oh My Pi 中为不同审查职责配置并验证多角色 Advisor roster 时使用。
---

# OMP 多角色 Advisor 配置

## 适用场景

用户需要多个 Advisor 按不同职责审查，例如需求正确性、架构兼容性、安全数据完整性和验证交付质量。

## 配置步骤

1. 发现当前配置：

   ```bash
   omp config path
   omp config get advisor.enabled --json
   omp config get modelRoles --json
   omp config get advisor.subagents --json
   ```

2. 读取现有 `<agent-dir>/WATCHDOG.md`、`WATCHDOG.yml` 和 `WATCHDOG.yaml`。保留用户既有规则；不得覆盖未知 roster。

3. 在 `<agent-dir>/WATCHDOG.md` 放置所有 Advisor 共享的规则：证据优先、仅报告可执行的实质问题、建议包含位置/证据/风险/最小修正、未发现问题时沉默。按用户要求选择提示词语言。

4. 在 `<agent-dir>/WATCHDOG.yml` 使用 `advisors` roster。每个角色应：
   - 有稳定的 ASCII `name`；
   - 使用互不重叠的 `instructions`；
   - 默认只授予 `tools: [read, grep, glob]`；
   - 省略 `model` 时继承 `modelRoles.advisor`；只有用户明确提出成本或模型分层需求时才为每个角色指定模型。

   推荐的最小角色划分：
   - `requirements-correctness`：需求、行为、错误路径、调用方迁移；
   - `architecture-compatibility`：模块边界、依赖、公共 API、彻底迁移；
   - `security-data-integrity`：鉴权、输入、敏感信息、命令/路径注入、数据丢失；
   - `verification-delivery`：验证是否覆盖契约、失败披露、最终交付事实性。

5. 验证 YAML 可被解析，例如：

   ```bash
   ruby -e 'require "yaml"; p YAML.safe_load_file("<agent-dir>/WATCHDOG.yml").fetch("advisors").map { |advisor| advisor.fetch("name") }'
   ```

   然后确认：

   ```bash
   omp config get advisor.enabled --json
   omp config get modelRoles --json
   ```

## 关键约束

- `advisor.subagents: false` 不会关闭主会话的多角色 roster；它只控制 task/eval 子代理是否也创建 Advisor。
- 多个 roster Advisor 各自使用模型资源。明确告知用户模型继承与用量增加，但不要未经要求改变模型或数量。
- `WATCHDOG.md` / `WATCHDOG.yml` 会在新 Session 中稳定生效。
- 仅当模型和工作区完全可信时才额外授予 `edit`、`write`、`bash` 等变更性工具。
