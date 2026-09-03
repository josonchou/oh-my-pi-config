---
name: mgt-contract-legacy-validation
description: 在 mgt-contract 缺少 node_modules 且旧 yarn.lock registry 失效时安全恢复临时依赖并执行 lint/build 验证。
---

# 适用条件

用于 `mgt-contract` 缺少 `node_modules`、`yarn.lock` 中 tarball 指向失效的 `registry.nlark.com`，但需要执行 ESLint、Stylelint 或 webpack 4 构建时。

# 安全流程

1. 先确认仓库没有需要保留的现成 `node_modules`；不得覆盖用户依赖目录。
2. 使用隔离临时目录，复制 `package.json` 与 `yarn.lock`。
3. 只在临时锁文件中将主机 `registry.nlark.com` 替换为 `registry.npmmirror.com`；不得修改仓库的 `package.json` 或 `yarn.lock`。
4. 使用项目兼容工具链安装锁定依赖：

```bash
mise x node@16.20.2 -- yarn install --frozen-lockfile --ignore-scripts
```

5. 将临时目录的 `node_modules` **复制**到仓库用于验证，禁止使用目录符号链接。webpack 的 loader 路径规则会解析真实路径，符号链接可能导致 `@shark/backstage-ui` 的 Less 文件绕过 loader 并报 `Module parse failed`。
6. 按需执行：

```bash
mise x node@16.20.2 -- yarn eslint <目标文件>
mise x node@16.20.2 -- yarn eslint --ext .js --ext .jsx src
mise x node@16.20.2 -- yarn lint:style
env=develop NODE_OPTIONS=--openssl-legacy-provider mise x node@16.20.2 -- yarn build
```

7. 根脚本 `yarn lint` 当前包含不存在的 `mock`、`tests` 路径，可能在 ESLint 开始前失败。应记录该脚本缺陷，并分别运行全量 `src` ESLint 与 `lint:style`，不要伪称 `yarn lint` 通过。
8. 验证完成后，只清理由本次流程创建的仓库 `node_modules`、`dist` 和临时目录；不得删除用户原有产物。

# 验证报告

分别报告目标 ESLint、全量 ESLint、Stylelint、构建、正式测试/typecheck 能力。该仓库当前没有自动化测试、`test` 或 `typecheck` 脚本，不得声称运行过完整测试套件。
