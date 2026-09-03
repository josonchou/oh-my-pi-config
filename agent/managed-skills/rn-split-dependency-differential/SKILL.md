---
name: rn-split-dependency-differential
description: 在 RN split bundle 发布后失效且依赖变更恢复时，用锁文件、单变量构建、source map 和模块可达性定位 external manifest/Bridge 版本错配。
---

# RN split bundle 依赖差分排障

适用于：业务源码未变，修改 npm 包版本并重新发布后恢复；项目由 `@shark/rn-build` 等工具按 external manifest 拆包。

## 1. 固定故障/修复边界

- 找到首次恢复的提交，确认它是否只改了 `package.json` 与 lockfile。
- 从两个 commit 的 lockfile读取**实际解析版本**，不要只看 semver 声明。
- 特别区分“把 `^x.y.z` 改成另一个 caret”与“精确版本 + lockfile 真正变化”。

## 2. 建立受控版本矩阵

至少构建：

1. 故障 lock 全量；
2. 修复 lock 全量；
3. 修复基线 + 单独恢复最可疑包；
4. 修复基线 + 单独恢复第二候选包。

每组使用隔离 worktree、同一源码、同一 external manifest、项目指定 Node 版本。安装优先 `npm ci`；老项目 peer 冲突时记录并使用仓库既有的 `--legacy-peer-deps` 约定。若安装跳过 scripts 导致 `sharp` 等原生包不可用，只重建该依赖后继续，不把环境失败当业务结论。

## 3. 对比产物，而不只看“构建成功”

对 Android/iOS分别确认：

- bundle、sourcemap、平台 config、业务 config 均存在；
- bundle 字节数；
- sourcemap `sources` 数量；
- 可疑包被打入的源文件数量；
- 包的 root、环境初始化器、核心单例是否被内联；
- 业务入口、`registerComponent`、`registerShell` 是否仍存在。

单变量若显著改变模块图，优先级高于“版本更新日志看起来相关”。

## 4. 检查 external manifest 失配

读取构建工具的 moduleId 与 filter 实现。常见模式：

- `node_modules` 相对路径参与 hash；
- external manifest 按 moduleId 判断是否剔除；
- 包从 `index.js` 改到 `dist/cjs/index.js` 会生成不同 moduleId；
- 结果是宿主已有依赖未被去重，业务包又内联一份。

比较 `package.json` 的 `main`、`module`、`type`、`exports` 和实际 `require.resolve` 路径。不要把目录布局变化误写成 Babel 语法问题。

## 5. 区分模块“定义”和“执行”

Metro bundle 中：

```js
__d(factory, moduleId, dependencyIds)
```

只是在模块表中定义模块；只有被 `r(moduleId)` 触达才执行。

解析每条 `__d` 的依赖数组，从业务 entry 做 BFS：

- root/core 可达而 env initializer 不可达，说明存在未初始化单例风险；
- 同时计算 env module 的引用数；
- 比较宿主旧路径与业务新路径的 moduleId，排除误碰撞。

不要仅因 sourcemap 中出现 env 文件就声称它已执行。

## 6. 验证单例隔离

若宿主与业务包包含两个版本：

- 分别加载两版核心单例；
- 初始化宿主版本；
- 检查业务版本是否仍未初始化；
- 结合业务首个调用链判断失败位置。

例如：`_enterRoom → updateRoomInfo → InternalBridge.invoke → catch → 不 createView`。

## 7. 排除 Babel/runtime

- 对比前后 lockfile 的实际 Runtime 版本；
- 对比 sourcemap 中归属于 `@babel/runtime` 的对应源文件集合和内容 hash；
- 检查 Babel 配置是否真的启用 `transform-runtime`；
- 不要把“Runtime 加到 dependencies 是正确治理”误写成“它修复了本次故障”。

若 `@babel/runtime` 同时出现在 dependencies/devDependencies 且范围冲突，单独标记为可复现性风险；先合并为一个明确版本、重锁、clean build，再讨论因果。

## 8. 证据分级

- **已验证事实**：lock 实际版本、构建结果、bundle/source map 差异、模块可达性、单例是否相同。
- **高置信候选**：静态故障链与用户症状完全吻合。
- **已确认根因**：还需要实际发布 bundle 的首个异常、Tower/Bugly 日志，或测试渠道单变量 A/B。

没有宿主运行证据时，禁止把高置信候选写成 100% 已确认。

## 9. 清理

结论记录后删除本次创建的临时脚本、包快照和隔离 worktree；不得影响主工作区。
