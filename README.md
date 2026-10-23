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

## 并行子任务隔离

- `agent/config.yml` 启用 `task.isolation.enabled`，使用 `merge: branch` 保留任务分支，并以 `apply: false` 禁止自动应用到父工作区。并发上限沿用宿主默认值；协作约束见 `agent/RULES.md` 的“子代理委派”。
- OMP 18.12.3 已无 `task.isolation.mode`。每个并行写入任务仍须显式传入 `isolated: true`；省略或传 `false` 会共享父 checkout，不能并行写入。隔离任务要求 Git 仓库。
- 本机实测使用独立 Git checkout 克隆，而非父仓库的 linked worktree：运行时分支名可以相同，但工作目录与 Git 状态彼此独立；成功完成后在父仓库保留 `omp/task/<id>` 分支供主 Agent 串行整合。`bash` 默认 cwd 与 `read`/`edit`/`write` 的相对路径均落在各自隔离目录。
- 这是工作区隔离，不是文件访问沙箱。绝对路径、共享目录和外部服务仍需单独约束；不得借此绕过隔离写入父工作区。
- 修改后新建或重启 OMP 会话以加载新规则。项目配置、CLI overlay 和运行时覆盖可能改变全局设置；在目标项目中执行以下命令检查有效值：

```bash
omp config get task.isolation.enabled --json
omp config get task.isolation.merge --json
omp config get task.isolation.apply --json
```

## 模型预设

`agent/config.yml` 保存 `codex` 和 `opencode-go` 两套预设。新增预设不会激活它，当前 `modelRoles` 保持不变。在 OMP 交互会话中切换：

```text
/modelpreset switch opencode-go
/modelpreset switch codex
```

`opencode-go` 面向基础 Go 套餐，按编码质量、长上下文与额度消耗分层；不是所有任务上的绝对最优排名。所有具体模型均来自 `opencode-go` provider：

| 角色 | 模型 | 推理级别 |
| --- | --- | --- |
| `default`、`designer`、`vision` | MiMo-V2.6-Pro | `high` |
| `slow` | DeepSeek V4 Pro | `max` |
| `plan`、`reviewer` | DeepSeek V4 Pro | `high` |
| `task` | MiMo-V2.6-Flash | `high` |
| `advisor` | DeepSeek V4.1 Flash | `high` |
| `smol`、`tiny` | DeepSeek V4.1 Flash | `low` |
| `commit`、`title` | 分别继承 `@smol`、`@tiny` | 跟随目标角色 |

- MiMo-Pro 承担常规编码及视觉工作，MiMo-Flash 承担实现子任务；两者在当前 OMP 目录中均支持约 1M 上下文和图片输入。DeepSeek V4 Pro 用于规划、困难推理和不同模型的独立审查，保留约 1M 上下文，但仅接受文字；图片任务交由 `vision`。
- 按 Go 当前公布的折算价格，每百万 token 的 Kimi K3 输入/输出为 $3/$15，DeepSeek V4 Pro 非高峰为 $0.66/$1.98、高峰为 $1.32/$3.96。两者基础 Go 月额度折算上限均为 $15，因此相同 token 量下替换可降低额度消耗；套餐月费不变，实际消耗仍取决于推理与输出 token 数。
- `task.agentModelOverrides` 已通过 `@role` 引用角色，`WATCHDOG.yml` 未指定独立模型，因此不用维护第二套子代理或 Advisor 配置。
- 预设的 `defaultThinkingLevel` 为 `high`；具体角色的后缀优先。切换替换角色及默认推理级别，不切换凭据、重试链、工具或扩展配置；项目配置或 CLI overlay 仍可能覆盖角色。
- 不依赖限时免费、Preview 或 Contributor 型号。按 Go 官方当前说明，所选模型均不用于训练；DeepSeek 的零保留协议按月续签，当前注明有效至 2026-10-31，并非永久承诺。
- 2026-10-22 在 OMP 18.12.6 关闭模型回退后，四款所选模型均通过最小空值过滤行为校验，MiMo-Pro 还通过图片形状识别。DeepSeek V4 Pro 的 `high`、`max` 两档均通过 `read` 工具调用及空值过滤审查。MiniMax M3 在同题中返回错误数组及非法 JSON，故未纳入；这是单题冒烟，不是完整能力或速度评测。

依据：[Go 模型、额度与隐私](https://opencode.ai/v2/docs/console/go/)、[MiMo-V2.6 官方发布说明](https://mimo.xiaomi.com/mimo-v2-6/article)、[DeepSeek 模型与价格](https://api-docs.deepseek.com/quick_start/pricing/)。厂商评测仅作为选型参考；套餐、价格和模型能力以当前官方资料及实际调用为准。

## Model Atelier（会话级临时预设）

日常仍以 `modelRoles` 的持久配置（这里是 `codex`）为默认；偶尔需要整套换模型时，用 `agent/extensions/model-atelier` 提供的命令，只在当前会话的内存运行期层生效，不写 `config.yml`。扩展由 OMP 自动发现，已在运行的会话需要重启 OMP 才会加载。

```text
/atelier              # 列出现有预设并选择；切过之后额外提供“reset”
/atelier ds           # 本次会话临时套用预设 ds 的全部角色与默认思考级别
/atelier reset        # 精确还原进入前的运行期覆盖、活动模型与思考级别
```

- 与原生 `/modelpreset switch` 的区别：原生命令会把角色写回全局配置，Atelier 只改当前进程的内存层，进程退出或新建会话即失效。连续切换多个预设不会覆盖最初保存的基线，`reset` 始终回到首次切换之前。
- 预设按 `config.yml` 的 `modelPresets` 实时读取，缺失角色会用运行期 `null` 隐藏而不是沿用上一套预设；`@角色` 别名、逗号候选和 `:思考级别` 后缀按 OMP 的核心解析语义处理，别名上的后缀优先于目标角色。预设的 `defaultThinkingLevel` 支持 `auto` 与各具体级别（`off` 到 `max`）。
- 仅在主会话、会话空闲且没有待处理消息时可切换；子代理自动继承父会话的临时角色，不会自行改写。
- 预设不存在、缺少 `default`、默认模型不可用或别名循环时只提示错误，不改变当前状态；恢复时若原模型已不可用，也保持现状不动。
- 无 UI 宿主（如 `--no-ui`）不会弹出选择器，也不会阻塞；此类模式下通知本身会被宿主丢弃，属预期行为。

验证命令（使用隔离临时目录和假模型，不读取真实账户、不发起模型请求）：

```bash
mise x python@3.14 -- python -m unittest discover -s agent/extensions/model-atelier/tests
```
