---
name: precommit-hook-debug
description: 当 git commit 因 husky/ eslint+prettier 失败时，按顺序修复钩子问题
---

# 预提交钩子失败时的处理流程

1. 先确认失败点

- 运行 `git commit ...` 后查看 `husky - pre-commit` 输出。
- 优先修复 `eslint`/`prettier` 的第一条错误，通常是阻塞项。

2. 若是 React hook 规则问题

- `react-hooks/refs`：避免在 render 阶段读取/写入 `ref.current`。
- 把 `latestRuleRequestContextRef.current = ...` 这类更新移入 `useEffect(() => { ... }, [deps])`。

3. 格式化受影响文件

- 使用仓库约定的 Node 版本执行：
  `mise x node@20 -- npx prettier --write <file1> <file2> ...`
- 尽量只对已变更文件批量处理。

4. 重新提交流程

- `git add ...`（必要时重新暂存）；
- `git commit -m "..."`。
- 不要使用 `--no-verify` 跳过钩子，除非明确授权。

## 适用范围
- 有 `lint-staged`/husky 的仓库提交。
- 任何因 `pre-commit` 报错导致的提交阻塞。
