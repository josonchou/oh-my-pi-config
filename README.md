# OMP 本地配置

本仓库保存可移植的 OMP 配置。运行时数据、机器专属路径和外置持久化数据不进入 Git。

## 外置管理目录

以下两个路径完全由本机软链接管理：

| OMP 路径 | 内容 | 持久化责任 |
| --- | --- | --- |
| `agent/managed-skills` | OMP 管理的可复用技能 | 软链接目标目录及其 NAS 存储与备份 |
| `agent/memories` | OMP 长期记忆 | 软链接目标目录及其 NAS 存储与备份 |

约束如下：

- 两个路径及其内容均不由本仓库管理；`.gitignore` 同时忽略目录和软链接本身。
- OMP 通过软链接直接读写外部源文件。源文件由 NAS 负责长期持久化、备份和恢复，Git 不提供副本。
- 当前机器可通过 Obsidian/iCloud 等本地同步路径连接 NAS 中的持久化数据；该本地路径属于机器配置，不写入仓库。
- 禁止使用 `git add -f` 强制提交这两个路径。Git 不会跟随软链接提交目标内容。
- 从旧的 Git 跟踪方式迁移时，仓库会出现一次历史文件删除；这只表示 Git 停止跟踪，不会删除软链接目标中的源文件。

## 新机器接入

先完成 NAS 数据挂载或同步，确认外部源目录完整，再手动创建机器专属软链接。不要把实际绝对路径写入仓库：

```bash
ln -s "<EXTERNAL_STORAGE>/managed-skills" "$HOME/.omp/agent/managed-skills"
ln -s "<EXTERNAL_STORAGE>/memories" "$HOME/.omp/agent/memories"
```

如果目标位置已经存在文件或目录，应先人工核对并迁移内容；不得直接覆盖。

## 验证

```bash
test -L "$HOME/.omp/agent/managed-skills"
test -L "$HOME/.omp/agent/memories"
readlink "$HOME/.omp/agent/managed-skills"
readlink "$HOME/.omp/agent/memories"
git check-ignore -v agent/managed-skills agent/memories
```

两个 `test -L` 命令应成功；`readlink` 应指向预期的外部存储路径；`git check-ignore` 应显示 `.gitignore` 中对应规则。

## Sourcebot MCP

- 用户级配置位于 `agent/mcp.json`，通过 Streamable HTTP 连接 `https://fedcode.douyu.tv/api/mcp`。
- `Authorization` 使用 `Bearer ${SOURCEBOT_API_KEY}`；密钥保存在本机 `~/.omp/agent/.env`，文件权限为 `600`，已被 Git 忽略。
- 在 Sourcebot 的 **Settings → API Keys** 创建密钥，以 `SOURCEBOT_API_KEY=实际密钥` 写入上述私有环境文件，OMP 启动时自动读取。
- 已有进程环境中的同名变量优先于 `.env`；如果 Shell 也导出了密钥，轮换时需同步更新，避免旧值覆盖。
- 新增或修改密钥后，退出并重新启动 OMP。仅修改 MCP 配置时可用 `/mcp reload`；它不能让已有进程继承新环境变量。连接状态用 `/mcp list` 检查。
- 可调用 `list_repos` 验证仓库查询；Sourcebot 只能访问服务端已索引的仓库和分支，不能读取本地未提交修改。
