---
name: douyu-web-safe-commit-validation-flow
description: 在 douyu-web 提交含测试/协议与 UI 改动时按最小变更范围进行提交前可复用的校验与暂存流程。
---

# 值班流程：douyu-web 安全提交闭环

目标：在保持最小变更范围的前提下，避免遗漏文件、误提交环境文件、漏验证。

## 适用场景
- 任何需提交代码的任务，尤其是 PKLayer/debug、协议、前端逻辑跨文件改动。

## 先决条件
- 已完成需求设计与实现。
- 不提交未确认的敏感配置（如 `.env` 本地临时变量）。

## 执行步骤

1. **可见性检查（提交前）**
   - `git status --short`
   - 识别 staged / unstaged / untracked 数量与路径。
   - 若存在与需求无关的文件（如 `.env.live`）先剥离决策。

2. **规模与影响核验**
   - `git diff --stat --`
   - 结合预期核对是否有明显超范围改动。

3. **相关验证**
   - 运行与改动域相关测试，例如：
     - `npm test -- entrances/Live/PKLayer/debug/__tests__/import.test.ts entrances/Live/PKLayer/debug/__tests__/storage.test.ts entrances/Live/PKLayer/debug/__tests__/PKDebugLayer.test.tsx --runInBand`
   - 运行风格校验：`mise x node@20 -- npx eslint <改动 ts/tsx 文件>`。
   - `eslint` 对测试文件忽略警告仅用于提示时，结合配置确认非错误。

4. **精准暂存**
   - `git add <精确路径或目录>`，避免手误写成 `app/web`。
   - 多次 `git status --short` 验证 staged/unstaged。
   - 使用 `git diff --cached --stat` 再核对提交范围。

5. **提交**
   - `git commit -m "<type(scope)>: <中文说明>"`
   - 本仓库允许的 type/scope 要与约定一致；当前建议 `feat(room)`。

6. **提交后收敛**
   - `git status --short` 再检查，仅保留本次预期外文件。
   - `git log -1 --oneline` 与 `git show --stat --name-only` 确认提交内容。

## 禁忌
- 不跳过 hooks（如 `--no-verify`）。
- 不在没核对范围时直接提交大量目录。
- 不把不属于本次任务的 `.env` 临时开关混进提交。
