---
name: mgt-contract-isolated-validation
description: 在 mgt-contract 缺少依赖且旧 yarn.lock 的 nlark 镜像失效时，隔离安装并运行 lint/build 验证
---

# mgt-contract 隔离验证

用于仓库没有 `node_modules`，且 `yarn install --frozen-lockfile` 因 `registry.nlark.com` 无法解析而失败时。

## 原则

- 不修改仓库 `package.json` 或 `yarn.lock`。
- 只在临时目录替换下载镜像主机；版本、integrity 和依赖图保持锁文件原样。
- 安装时禁用生命周期脚本。
- 构建需要项目根目录下的真实 `node_modules`，不要使用指向 `/tmp` 的 symlink。
- 复制 `node_modules` 时必须保留其内部符号链接，尤其是 `node_modules/.bin/*`。

## 步骤

1. 记录项目根目录原先是否存在 `node_modules` 和 `dist`；存在时不得覆盖或在清理阶段删除。
2. 将仓库 `package.json` 复制到临时目录。
3. 将仓库 `yarn.lock` 内容复制到临时目录，并仅替换：
   - `https://registry.nlark.com` → `https://registry.npmmirror.com`
4. 在临时目录安装：

```bash
mise x node@16.20.2 -- yarn install --frozen-lockfile --ignore-scripts
```

5. 把临时 `node_modules` **复制**到项目根目录，且保留内部符号链接。不能把整个目录 symlink 到 `/tmp`：webpack 的模块真实路径会落到 `/private/tmp`，导致现有 Less loader 规则无法处理 `@shark/backstage-ui` 的 Less。

可用方式：

```bash
cp -R <temp>/node_modules ./node_modules
```

或 Python：

```python
shutil.copytree(temp_node_modules, repo_node_modules, symlinks=True)
```

不得使用默认的 `shutil.copytree(...)`；它会解引用 `.bin` 符号链接，导致 ESLint/Stylelint 报 `Cannot find module '../lib/cli'`。

6. 执行验证：

```bash
mise x node@16.20.2 -- yarn eslint --ext .js --ext .jsx src
mise x node@16.20.2 -- yarn lint:style
NODE_OPTIONS=--openssl-legacy-provider env=develop mise x node@16.20.2 -- yarn build
```

若 Yarn 启动的 `.bin` 子进程意外使用了系统 Node，可显式运行真实入口：

```bash
mise x node@16.20.2 -- node node_modules/eslint/bin/eslint.js --ext .js --ext .jsx src
mise x node@16.20.2 -- node node_modules/stylelint/bin/stylelint.js "**/*.less" --syntax less
```

7. 删除本次生成的项目根目录 `node_modules`、`dist` 及临时验证目录；仅删除步骤 1 确认原先不存在的目录。

## 判断结果

- `yarn lint` 可能因仓库不存在 `mock`、`tests` 目录而失败；分别运行全量源码 ESLint 与 `lint:style`，并如实记录脚本本身的问题。
- 只将本次变更引入的 error/warning 视为回归；历史 warning 单独报告。
- 构建成功后确认仓库锁文件和包清单无差异。
