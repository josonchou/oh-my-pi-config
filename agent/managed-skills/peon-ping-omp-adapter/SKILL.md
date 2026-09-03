---
name: peon-ping-omp-adapter
description: 为已安装 peon-ping 的环境安全接入并验证 oh-my-pi（OMP）原生扩展
---

# peon-ping 接入 OMP

## 适用场景

用户已安装 `peon-ping`，要求为 `oh-my-pi`（`omp`）启用声音与桌面通知。

## 流程

1. 运行 `peon status --verbose`，确认 `peon-ping: active`，并定位配置目录。
2. 检查 `~/.omp/agent/extensions/peon-ping/`：
   - 不存在：继续安装。
   - 已存在：先读取内容；不得静默覆盖用户改动。
3. 确认 `peon.sh` 存在于以下至少一个位置：
   - `~/.claude/hooks/peon-ping/peon.sh`
   - `~/.openclaw/hooks/peon-ping/peon.sh`
4. 从 PeonPing 官方仓库获取 `adapters/omp/peon-ping.ts` 和 `adapters/omp/package.json`。优先固定已审阅的 tag 或 commit；避免直接执行未审阅、跟随 `main` 的 `curl | bash`。
5. 将两文件安装到 `~/.omp/agent/extensions/peon-ping/`。
6. 启动新的 OMP 进程做烟测：

   ```bash
   omp -p --no-tools --no-session --max-time=2m "只回复 OK"
   ```

7. 检查 `~/.claude/hooks/peon-ping/.state.json`，确认出现：
   - `source: "omp"`
   - `session_id` 以 `omp-` 开头
   - 最终事件通常为 `SessionEnd`
8. 告知用户：安装前已经运行的 OMP 会话不会热加载扩展，需要重启。

## 验证标准

- OMP 烟测无扩展加载错误并正常退出。
- peon-ping 状态文件记录来自 OMP 的事件。
- 扩展目录仅包含预期的 `peon-ping.ts` 与 `package.json`，除非安装前已有其他用户文件。
