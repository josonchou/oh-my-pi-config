---
name: herdr-auto-tab-title
description: 在 Herdr 中安装、配置或排查根据前台进程与 AI agent 任务自动重命名内部 tab 的插件时使用
---

# Herdr 自动 Tab 标题

## 目标与边界

Herdr 0.8.2 的原生 `ui.window_title` 只控制外层终端窗口标题；`ui.prompt_new_tab_name = false` 只让新 tab 使用自动编号。内部 tab 不会原生跟随 agent 的 `terminal_title`。

优先使用第三方插件 [`qu8n/herdr-automatic-rename`](https://github.com/qu8n/herdr-automatic-rename)：普通 pane 使用前台进程名，coding agent pane 使用任务标题；手动重命名优先。

## 安装前检查

```bash
herdr --version
herdr plugin --help
command -v jq
```

要求：Herdr `>= 0.7.1`，推荐 `>= 0.7.4`；macOS/Linux；`bash` 和 `jq`。

安装第三方插件前必须向用户说明它会执行仓库中的插件脚本与 shell hook；只有用户明确要求安装时才执行。

## 安装

```bash
herdr plugin install qu8n/herdr-automatic-rename --yes
```

在 `~/.config/herdr/config.toml` 已有的 `[ui]` 表内加入，禁止创建第二个 `[ui]`：

```toml
prompt_new_tab_name = false
```

如果希望外层终端标题也展示自动生成的 tab 名，可加入：

```toml
window_title = "{hostname}: {workspace} · {tab}"
```

## Shell hook

zsh，在 `~/.zshrc` 中加入：

```zsh
for _f in ${HOME}/.config/herdr/plugins/github/herdr-automatic-rename-*/shell/hook.zsh(N); do
  source $_f
  break
done
```

bash，在 `~/.bashrc` 中加入，且应放在 starship、atuin 等 prompt/history 工具之后：

```bash
for _f in "$HOME"/.config/herdr/plugins/github/herdr-automatic-rename-*/shell/hook.bash; do
  [ -r "$_f" ] && { source "$_f"; break; }
done
```

fish，在 `~/.config/fish/config.fish` 中加入：

```fish
for _f in $HOME/.config/herdr/plugins/github/herdr-automatic-rename-*/shell/hook.fish
    test -r "$_f"; and source "$_f"; and break
end
```

hook 让命令启动时立即改名；不装 hook 时，通常要等下一次 focus/tab 事件。

## 应用与验证

```bash
herdr server reload-config
herdr plugin list
```

重新载入对应 shell，新建一个未手动命名的 tab，依次运行 shell 命令和 coding agent，观察内部 tab 标题是否从编号变成前台进程/任务标题。手动重命名后插件应保留手动名。

若手动名需要重新交给插件管理：

```bash
herdr plugin action invoke herdr-automatic-rename.reset
```

## 排查

- 新 tab 始终不自动命名：检查 `[ui] prompt_new_tab_name = false`，手动输入名称会让该 tab 退出自动命名。
- 更新不及时：确认 shell hook 已加载；否则只会在 Herdr 事件发生时刷新。
- Linux 容器/沙箱无法识别前台进程：Herdr `>= 0.8.0` 时可在 Herdr 环境中设置 `HERDR_PROCESS_DETECTION=child-groups`。
- 查看插件注册与路径：`herdr plugin list --json`。

## 备选方案

- `elKei24/herdr-title-sync`：每 2 秒轮询并强制把 `terminal_title_stripped` 写入 tab；会覆盖手动名，多 agent tab 只取第一个，通常不优先。
- `Newt6611/herdr-tab-title`：只为现有标题添加 workspace 内编号，不负责根据 agent 任务生成语义标题。
