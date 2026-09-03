---
name: omp-cmux-workflow
description: 在 macOS 上用 cmux 编排多个 OMP 会话、隔离并行开发并统一管理长驻服务时使用。
---

# OMP × cmux 协作工作流

## 职责边界

- **cmux**：管理 workspace、pane、焦点切换和通知。
- **OMP `hub`**：管理项目级长驻进程（Node 服务、调试器等）、日志和生命周期。
- **Git worktree**：隔离并行修改，避免多个 OMP 会话争抢同一工作区。

不要让 cmux 和 OMP 同时启动或管理同一服务。

## 布局

1. 为每个独立开发目标创建一个 Git worktree。
2. 为每个 worktree 创建一个 cmux workspace。
3. 每个 workspace 放一个负责写代码的 OMP pane；测试、日志、审查使用独立 pane。
4. 同一文件同一时间只能由一个 OMP 会话修改。

## 长驻服务

优先将需要跨 OMP 会话共享、可查询状态、需统一日志的服务交由 OMP `hub` 管理：

- 启动：`hub({ op: "start", name, application, args, ready })`
- 查看：`hub({ op: "ps" })`
- 日志：`hub({ op: "logs", name, lines: 100 })`
- 控制：`hub({ op: "stop" | "restart", name })`

注意：`hub ps` 只能列出通过 `hub start` 启动的受管进程。cmux pane 中直接运行的 `npm run dev`、手动启动的浏览器、其他终端后台进程都不在其中。

## 通知

- cmux 适合定位 workspace/pane：`cmux notify --title "OMP" --body "任务已完成"`。
- OMP/PeonPing 适合切换到其他 App 后的系统通知。
- 若要自动把 OMP 回合完成事件推给 cmux，使用 OMP extension 的 turn-end 事件调用 `cmux notify`；先确认当前 cmux session/workspace 命名和通知策略，避免重复提醒。

## 快速检查

```bash
cmux --session agents list-workspaces --json
cmux list-notifications --json
```

cmux 快捷键可被用户配置覆盖，先在 cmux 的配置或命令面板确认，不要假定默认键位。
