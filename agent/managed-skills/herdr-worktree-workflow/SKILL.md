---
name: herdr-worktree-workflow
description: 在 Herdr 中配置、使用或排查 Git worktree 的创建、打开、合并与安全清理流程时使用
---

# Herdr Worktree 工作流

## 边界

Herdr 管理 Git worktree checkout 和对应 workspace；它不负责合并分支。合并必须走标准 Git 或 GitHub/GitLab PR。

## 配置前检查

1. 读取当前 `~/.config/herdr/config.toml` 的完整 `[keys]` 和 `[[keys.command]]`。
2. 运行 `herdr --version`、`herdr worktree --help` 和 `herdr --default-config`，核对当前版本 action 名称与默认按键。
3. 注意 `[keys]` 是默认值上的局部覆盖：未声明的动作仍继承默认按键。
4. 内建 action 的按键可能优先于同键的自定义命令；必须检查冲突。

Herdr 0.8.2 支持：

```toml
new_worktree = "..."
open_worktree = "..."
remove_worktree = "..."
```

修改后运行：

```bash
herdr config check
herdr server reload-config
```

配置检查只能证明语法和加载成功；macOS/外层终端是否拦截 Option/Cmd 组合必须在真实 TUI 中验证。不要为了烟测创建或删除用户真实 worktree。

## 使用

UI：选中 Git workspace 后执行 `new_worktree`。输入已有本地分支时 checkout；否则创建分支并作为子 workspace 打开。`open_worktree` 聚焦已打开 checkout 或打开现有 checkout。

CLI：

```bash
herdr worktree list [--workspace ID | --cwd PATH]
herdr worktree create --cwd /path/to/repo --branch feature/name --base origin/main --focus
herdr worktree open --cwd /path/to/repo --branch feature/name --focus
herdr worktree remove --workspace ID
```

## 合并

先在功能 worktree 提交：

```bash
git status
git add -A
git commit -m "<message>"
```

团队项目优先 push 后走 PR：

```bash
git push -u origin feature/name
```

本地合并时回到目标分支所在的原始 worktree：

```bash
git status
git switch main
git pull --ff-only
git merge --no-ff feature/name
git push origin main
```

发生冲突：解决文件后 `git add`、`git commit`；取消用 `git merge --abort`。

## 安全清理

顺序不可反：

1. 确认功能 worktree 已提交，且 merge/PR 完成。
2. 使用 Herdr 移除 worktree checkout；避免 `--force`，除非明确接受丢弃未提交和未跟踪文件。
3. checkout 移除后再删除本地分支：`git branch -d feature/name`。
4. 需要时删除远程分支：`git push origin --delete feature/name`。

`git branch -d` 优先于 `-D`；删除 checkout 不等于删除分支。
