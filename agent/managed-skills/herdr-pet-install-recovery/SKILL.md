---
name: herdr-pet-install-recovery
description: 安装或修复 allmight-ai/herdr-pet，处理非交互确认、Rust E0658 和临时目录 shim 问题
---

# Herdr Pet 安装与修复

1. 非交互安装：
   ```bash
   herdr plugin install allmight-ai/herdr-pet --yes
   ```
2. 若构建报 `E0658` 且涉及 `unsigned_is_multiple_of`：
   ```bash
   rustc --version
   rustup update stable
   herdr plugin install allmight-ai/herdr-pet --yes
   ```
3. 安装后验证：
   ```bash
   herdr-pet status
   ```
4. 若 shim 报 `.tmp-install-*/checkout/target/release/herdr-pet: No such file or directory`，定位已安装插件目录并运行真实二进制的幂等 setup：
   ```bash
   ~/.config/herdr/plugins/github/allmight-ai.herdr-pet-*/target/release/herdr-pet setup
   herdr-pet status
   ```

不要直接编辑 `~/.local/bin/herdr-pet`；`setup` 会同时修复 CLI 路径、快捷键并重新加载 Herdr 配置。验证标准：`herdr-pet status` 成功退出；尚未初始化时提示运行 `herdr-pet init` 属正常结果。
