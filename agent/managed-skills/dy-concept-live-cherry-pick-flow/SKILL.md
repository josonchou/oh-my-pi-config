---
name: dy-concept-live-cherry-pick-flow
description: 在 dy-concept 将功能分支提交安全拣选到最新 live 并原子推送两个远端分支时使用
---

# dy-concept 功能提交同步到 live

## 前提

- 工作目录：`/Users/joson/Workspace/douyu/dy-concept`
- 用户明确要求提交、同步 `live` 并推送。
- 提交信息必须使用中文 Conventional Commits。

## 流程

1. 记录当前功能分支，检查 `git status --short --branch`、实际差异与远端名称。
2. 运行任务相关测试、`npm run typecheck`、`npm run lint`；项目工具链使用：
   ```bash
   mise x npm:npm@11.17.0 -- npm <命令>
   ```
3. 暂存用户要求的全部变更并提交，保存功能分支 commit SHA：
   ```bash
   git add --all
   git diff --cached --check
   git commit -m "fix(<scope>): <中文说明>"
   ```
4. 获取最新远端引用：
   ```bash
   git fetch origin
   ```
5. 切到 `live`，只允许快进到最新远端状态：
   ```bash
   git switch live
   git merge --ff-only origin/live
   ```
6. 拣选功能提交：
   ```bash
   git cherry-pick <功能分支 commit SHA>
   ```
7. 若 `CHANGELOG.md` 冲突，保留双方日期段，按日期从新到旧排列；不要覆盖远端新增条目。处理后：
   ```bash
   git add CHANGELOG.md
   git cherry-pick --continue
   ```
   若冲突合并后仅需修正未推送提交中的格式，可修正并 `git commit --amend --no-edit`。
8. 在更新后的 `live` 上重新运行目标测试、typecheck 和变更文件 ESLint。确认 `git status --short --branch` 仅显示 `live` 领先远端且工作区干净。
9. 原子推送功能分支和 `live`，避免只推送一半：
   ```bash
   git push --atomic --set-upstream origin <功能分支> live
   ```
10. 切回最初的功能分支，并确认工作区干净且与远端一致：
    ```bash
    git switch <功能分支>
    git status --short --branch
    ```

## 禁止

- 不使用 force push。
- 不用 merge commit 更新 `live`；只用 `--ff-only`。
- 不在未同步 `origin/live` 时直接 cherry-pick。
- 不因 `CHANGELOG.md` 冲突丢弃任一方条目。
- 不在 live 集成验证失败时推送。
