---
name: pk-layer-browser-smoke
description: "在 douyu-web 本地用代码内置回放对 PKLayer 观众端(双队/多队)做浏览器烟测,并避开结果弹窗去重与回放重叠两个方法学坑"
---

# PKLayer 观众端浏览器烟测(内置回放)

验证 `apps/web/entrances/Live/PKLayer` 观众端新条,无需真实 PK 消息,用代码内置回放。

## 前置
- dev server 需带 `NEXT_PUBLIC_ENABLE_PK_DEBUG=true` 且 `NODE_ENV==='development'`(`PKLayer.tsx` 的 `PK_DEBUG_ENABLED` 门控)。
- 可用直播间(非关闭):`http://localhost:<port>/77590817`(defei666)。页面需等 `[data-testid='pk-debug-toggle']` 出现(播放器 ready 后才挂载 PKLayer/PkDebugLayer)。
- 用 `agent-browser --session <name>`。

## 步骤(每个 round 单独一次干净运行)
1. `navigate` 到直播间,`wait "[data-testid='pk-debug-toggle']"`。
2. `click "[data-testid='pk-debug-toggle']"` 打开调试;点 `回放消息` tab。
3. `snapshot -i -c -s "[data-testid='pk-debug-drawer']"` 取内置 round 按钮 ref:双队=「观众侧 PK 完整流程」,多队=「观众侧多队 PK 完整流程」。
4. 点 round → 点 `回放所选轮次`。
5. 连续轮询(每 ~1.5s,共 ~30 次覆盖全程 44s)。同一次 eval 读取:
   - 相位:`[data-testid=two-team-pk-bar]`/`[data-testid=multi-team-pk-bar]` 的 `data-phase`。
   - 结果弹窗:`[data-testid=two-team-result-dialog]`/`[data-testid=multi-team-result-dialog]`(**全文档查询**,弹窗是 Mantine Modal portal 到 `#js-player-video-case`,不在 `#js-player-above-controller` 内)。双队看 `[data-outcome]`=win/lose/draw。
   - 条文本:`#js-player-above-controller` 的 innerText。

## 内置回放时间线
- 双队:`PK_ID=9_000_001`,15 条;多队:`MULTI_TEAM_PK_ID=9_000_002`,12 条。
- countdown ~4s → in-game ~30s → `PK_RESULT`@35s → `result_close`@44s → hidden。
- 期望:双队结果=胜负(胜利/惜败/平局)+双方助力榜;多队结果=名次(本场第 N 名)+名次列表;多队跳字仅本方;任务失败/完成提示各约 3s 窗口(`expiresAtSec`);终态关闭后 `kind:hidden`。

## 两个必避的方法学坑(先排除再判缺陷)
1. **结果弹窗去重**:`PKLayer.tsx` 的 `activeResultDialog` 按 `resultDialogState.autoShownPkIds` 去重。内置 round 的 pkId 固定,**同一页面会话内二次回放同一 pkId 不会再弹结果弹窗**。想再看必须 `navigate`/刷新重置 `resultDialogState`。
2. **回放重叠**:全程 ~44s。上一段没播完就启动下一段会重叠,采样出现空窗/错乱。每个 round 刷新后单次跑到底。

## 确定性兜底
浏览器时序 flaky 时,以 `debug/__tests__/builtInReplay.test.ts` 为准:`displays[10]`(多队 result+名次)、`displays[13]`(双队 result)已断言,`cd apps/web && npm test -- PKLayer --runInBand`。
