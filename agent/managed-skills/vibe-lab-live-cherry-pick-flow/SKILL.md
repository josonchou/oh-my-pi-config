---
name: vibe-lab-live-cherry-pick-flow
description: 在 vibe-lab 将当前功能分支提交安全拣选到最新 live，并原子推送功能分支与 live 时使用
---

# Vibe Lab 功能提交同步到 live

## 目标

把当前功能分支的单个新提交安全同步到最新 `live`，同时推送功能分支与 `live`，避免覆盖远端并发提交或产生部分推送。

## 流程

1. 记录当前分支；检查 `git status --short --branch`。工作区必须只包含本次任务文件。
2. 运行相关验证；精确暂存本次文件，执行 `git diff --cached --check`。
3. 使用中文 Conventional Commit 创建提交；禁止 `--no-verify`，失败后禁止 amend。
4. 记录新提交完整 SHA，并确认提交后工作区干净。
5. 刷新远端：
   ```bash
   git fetch origin <feature-branch> live
   ```
6. 检查分歧：
   ```bash
   git rev-list --left-right --count <feature-branch>...origin/<feature-branch>
   git rev-list --left-right --count live...origin/live
   ```
   - 功能分支预期仅本地领先新提交。
   - `live` 若仅远端领先，可安全 fast-forward。
   - 任一分支存在双向分歧时停止，不做 reset/force；先调查提交关系。
7. 更新并拣选：
   ```bash
   git switch live
   git merge --ff-only origin/live
   git cherry-pick <new-commit-sha>
   ```
   冲突时按仓库冲突处理流程解决，禁止跳过文件或强行覆盖。
8. 确认 `live` 工作区干净且仅领先远端一个拣选提交。
9. 原子推送两个分支：
   ```bash
   git push --atomic origin <feature-branch> live
   ```
   原子推送可避免只更新一个分支。远端不支持 `--atomic` 时，先说明风险再决定顺序。
10. 切回原功能分支并确认同步状态：
    ```bash
    git switch <feature-branch>
    git status --short --branch
    ```

## 交付证据

报告：
- 功能分支提交完整 SHA 与提交标题；
- `live` cherry-pick 后 SHA；
- 推送输出中两个远端 ref 的更新范围；
- 最终所在分支及干净状态。
