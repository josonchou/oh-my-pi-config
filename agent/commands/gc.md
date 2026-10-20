---
description: 委派独立 commit 子代理创建安全 Git 提交
---

当前主 Agent 的唯一动作是调用一次 `task` 工具创建独立的 blocking `commit` child session；主 Agent 不得亲自执行任何 Git 命令，不得切换或复用主会话模型。调用使用当前批量参数形状，必须明确提供：

- `context`：非空字符串 `目标：在当前 Git 项目创建一次安全提交。约束：全部 Git 检查、暂存、提交及提交后核验由独立 commit 子代理完成；仅提交，不执行 fetch、cherry-pick 或 push；子代理不依赖父对话历史。`。不得省略或传入空字符串。
- `tasks`：仅一项，设 `agent: "commit"`、`solutionSpace: "安全提交步骤已明确；提交范围以实际工作区差异为准"`，`task` 为下方代码块的完整文本（包含展开后的命令参数）。

等待 blocking child 返回后，只返回子代理的实际结果：

```text
请在当前 Git 项目中完成一次安全提交，并独立承担全部 Git 操作。

- 先检查当前工作区、当前分支、`git status` 和 `git diff`；在任何暂存或提交前，无条件审查完整的 `git diff --cached`，包括既有 staged 内容，逐项确认路径和内容均属于本次任务且安全。任何不相关、敏感或无法确认的条目都必须停止；不得用 `reset`、`restore` 或其他方式覆盖、清除用户既有 index。
- 记录提交前的 `HEAD` 以及获准进入提交的每个 staged 路径和内容。仅暂存本次相关且安全的文件；保护所有不相关改动，以及 `.env`、凭据、密钥、私钥、数据库、缓存、构建产物和运行时文件。暂存完成后，再次无条件审查完整的最终 `git diff --cached`，只允许此前审核通过的路径与内容进入 commit。
- 根据实际 diff 创建中文 Conventional Commit message，使用合适的 type/可选 scope，描述简洁、祈使语气。
- commit hooks 成功后，检查新 commit 相对记录的旧 `HEAD` 的完整实际 diff，并重新检查 `git status`、index 与 worktree。允许 hooks 对已获准路径和内容进行正常格式化；任何新增未获准路径、敏感内容、异常引用或无法确认的副作用都必须停止并报告。post-commit 产生的额外 worktree/index 改动必须明确报告，不能悄然暂存或带入 commit。
- 禁止使用 `--no-verify`、force/强推、修改 Git 配置，以及 `reset --hard`、`clean`、会丢弃改动的 `checkout`/`restore` 等破坏性命令。
- 任一步骤失败立即停止并报告实际错误、当前状态和现场路径；不要把未创建成功的提交说成完成，不要为了收尾清理或重置现场。成功后报告实际创建的 commit SHA。
- 不得要求主 Agent 代执行命令，不得依赖父对话历史；`gc` 只创建提交，不执行 fetch、cherry-pick 或 push。

$ARGUMENTS
```
