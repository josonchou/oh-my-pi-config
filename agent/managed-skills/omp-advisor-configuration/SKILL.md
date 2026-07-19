---
name: omp-advisor-configuration
description: 在用户要求配置或优化 Oh My Pi Advisor 模式时，检查现有模型与设置，应用安全且高信噪比的全局 Advisor 基线并验证。
---

# OMP Advisor 配置

用于配置或优化 Oh My Pi 的 Advisor mode。

## 1. 发现当前状态

```bash
omp config path
omp config get modelRoles --json
omp config get advisor.enabled --json
omp config get advisor.subagents --json
omp config get advisor.syncBacklog --json
omp config get advisor.immuneTurns --json
omp config get tier.advisor --json
omp config get retry.fallbackChains --json
```

同时检查 `<agent-dir>/WATCHDOG.md` 与 `<agent-dir>/WATCHDOG.yml` 是否存在。不要直接假设某个模型已配置或可用。

## 2. 选择最小配置

默认只运行一个 Advisor；不要因为 roster 功能存在就创建多个 reviewer。对高能力主模型，推荐：

```yaml
modelRoles:
  advisor: <主力模型>:high

advisor:
  enabled: true
  subagents: false
  syncBacklog: 1
  immuneTurns: 3

tier:
  advisor: inherit
```

理由：

- `:high` 通常足以审查，避免与 `:xhigh` primary 重复消耗。
- `syncBacklog: 1` 让意见尽可能在 primary 的下一步前抵达；每轮最多等待 30 秒。
- `subagents: false` 避免 task/eval fan-out 时增加成本、延迟和重复意见。
- `tier.advisor: inherit` 跟随主会话的服务等级。
- 保持 advisor 默认只读工具池 `read`、`grep`、`glob`。`WATCHDOG.yml` 的 `edit`、`write`、`bash` 等 grant 不受主会话 approval wrapper 约束，除非用户明确要求且 workspace/model 已受信任，不要授予。

现有 `retry.fallbackChains` 已覆盖 advisor 的模型 selector 时无需重复添加。

## 3. 添加审查规则

无现有规则时，在 `<agent-dir>/WATCHDOG.md` 写入精简、可执行的 reviewer policy：

```markdown
# Advisor review policy

Review the primary agent as an independent senior engineer.

- Send advice only for a concrete defect, missed requirement, security/data-loss risk, or an avoidable cross-file regression.
- Verify claims against the workspace before advising. Prefer the shared root cause over patching a single symptom.
- Check changed public APIs, call sites, error paths, concurrency, and user-visible behavior when relevant.
- Keep one note specific: state the location, risk, and the smallest corrective action.
- Do not advise on style, speculative abstractions, or work already verified. Silence means no issue.
```

若已有 `WATCHDOG.md`，保留用户规则，只添加不重复的条目。

## 4. 验证

用 `omp config get` 核对每个修改后的 key。其成功解析即验证 YAML settings 生效；读取 `WATCHDOG.md` 确认内容。说明：Advisor 运行时和 WATCHDOG 发现从新 session 开始生效。
