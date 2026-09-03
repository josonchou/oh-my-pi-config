---
name: install-peon-ping-omp
description: 在 oh-my-pi 中安装、验证或卸载 PeonPing 通知扩展时使用
---

# 在 OMP 中接入 PeonPing

## 前置条件

先安装并初始化 peon-ping，确保以下任一路径存在：

- `~/.claude/hooks/peon-ping/peon.sh`
- `~/.openclaw/hooks/peon-ping/peon.sh`

macOS/Linux 推荐：

```bash
brew install PeonPing/tap/peon-ping
peon-ping-setup
```

也可使用项目官方安装脚本。

## 安装 OMP 扩展

```bash
curl -fsSL https://raw.githubusercontent.com/PeonPing/peon-ping/main/adapters/omp.sh | bash
```

安装器会写入：

```text
~/.omp/agent/extensions/peon-ping/peon-ping.ts
~/.omp/agent/extensions/peon-ping/package.json
```

安装后重启 OMP。

## 验证

确认上述两个扩展文件存在，并在重启后的 OMP 会话中分别触发会话开始、回合完成或工具失败事件，观察音效或通知。适配器映射：

- `session_start` → `SessionStart`
- `turn_start` → `UserPromptSubmit`
- `turn_end` → `Stop`
- 失败的 `tool_result` → `PostToolUseFailure`
- `auto_compaction_start` → `PreCompact`
- `session_shutdown` → `SessionEnd`

## 卸载

```bash
curl -fsSL https://raw.githubusercontent.com/PeonPing/peon-ping/main/adapters/omp.sh | bash -s -- --uninstall
```

卸载器删除 `~/.omp/agent/extensions/peon-ping/`，随后重启 OMP。
