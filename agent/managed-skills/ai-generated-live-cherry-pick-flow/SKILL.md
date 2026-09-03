---
name: ai-generated-live-cherry-pick-flow
description: 在 ai-generated 仓库将功能提交安全拣选到最新 live、验证并推送 origin/live 时使用
---

# ai-generated live 拣选发布

## 前置条件

- 仓库：`/Users/joson/Workspace/douyu/ai-generated`
- 用户明确要求将提交拣选到 `live` 并推送远端。
- 禁止强推；默认只推 `live`，除非用户明确要求同时推功能分支。

## 流程

1. 运行 `git status --short --branch`，确认工作区干净并记录当前功能提交。
2. 运行 `git fetch origin`，刷新远端引用。
3. 核对源提交是否尚未进入 `origin/live`。注意历史提交可能已以不同哈希被拣选到 `live`，不要仅按哈希判断其前置提交是否缺失；结合文件状态和提交内容判断。
4. 切换并同步：
   ```bash
   git switch live
   git merge --ff-only origin/live
   ```
5. 拣选目标提交：
   ```bash
   git cherry-pick <source-commit>
   ```
   若发生冲突，进入标准冲突解决流程，不跳过提交、不覆盖远端改动。
6. 按影响范围验证。`revenue` 页面变更至少运行相关定向测试和：
   ```bash
   mise x -- npm run build --workspace revenue
   ```
7. 推送：
   ```bash
   git push origin live
   ```
   依赖普通非快进拒绝保护；禁止 `--force`。
8. 验证发布结果：
   ```bash
   git status --short --branch
   git rev-parse --short HEAD
   git rev-parse --short origin/live
   ```
   完成条件：工作区干净，本地 `live` 与 `origin/live` 哈希一致。

## 输出

报告源提交、新 live 提交、推送范围、验证命令结果，以及当前分支。
