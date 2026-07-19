---
name: restore-omp-plugins
description: 仅在用户明确执行 /skill:restore-omp-plugins 或明确要求运行此技能时，恢复 Oh My Pi 的个人插件与其 Marketplace；普通提及插件时不要自动执行。
disableModelInvocation: true
---

# 恢复 Oh My Pi 插件

仅在用户明确调用此技能时执行。不要因排查、列举或讨论插件而安装任何内容。

## 恢复流程

1. 运行 `omp plugin marketplace list` 与 `omp plugin list`，确定已配置的 Marketplace 和已安装插件。
2. 仅在缺失时添加以下 Marketplace：
   ```bash
   omp plugin marketplace add DietrichGebert/ponytail
   omp plugin marketplace add anthropics/claude-plugins-official
   ```
3. 仅安装缺失的插件，保持 user scope：
   ```bash
   omp plugin install @tmustier/pi-tab-status@0.1.4
   omp plugin install ponytail@ponytail --scope=user
   omp plugin install sentry@claude-plugins-official --scope=user
   ```
4. 运行 `omp plugin list` 验证结果，确认以下插件均存在：
   - `@tmustier/pi-tab-status@0.1.4`
   - `ponytail@ponytail`
   - `sentry@claude-plugins-official`

Marketplace 插件按当前 Marketplace 目录安装；OMP CLI 不提供按已安装版本精确锁定 Marketplace 插件的语法。
