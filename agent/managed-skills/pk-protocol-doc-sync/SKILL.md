---
name: pk-protocol-doc-sync
description: 基于解码实现与测试回归对齐 PKLayer 协议文档，避免与前端消费契约脱节
---

## 触发场景
- 要更新 PKLayer 协议文档（`pk/PROTOCOL.md`）
- 或出现 `文档与行为不一致` 的疑义

## 步骤
1. 读取并确认前端消费入口文件：`apps/web/entrances/Live/PKLayer/pk/protocol.ts`。
2. 读取 `pk/__tests__/protocol.test.ts`，提取命令/state/event、ts/pv、过期/签名等实际契约断言。
3. 仅基于上述代码与测试作为**权威**，再对齐到外部资料（如 `pk1.md`、飞书文档）中的描述。
4. 将文档中的版本号、`pv` 约束、`ts` 单位、字段生效条件、丢弃规则写成与实现一致。
5. 只改文档时，不改运行时逻辑；若发现实现缺陷，再走代码修复流程。

## 验证
- `git diff` 仅展示文档差异且无无关改动。
- 文档关键条目与解码逻辑逐条可追溯一致（尤其：`pv`、`ts`、`cmd/state` 白名单、`expire_seconds`）。
