---
name: live-activity-common-pendant-build-validation
description: 在 live-activity-common-pendant 功能分支执行生产构建，或排查 Shark 构建 Axios URL undefined 时使用
---

# 适用场景

在 `live-activity-common-pendant` 功能分支执行生产构建；或 `npm run build` 在 `@shark/shark-micro-build` 的 `downloadDll()` 阶段报 Axios `url` 为 `undefined`。

# 原因

老版 Shark 构建器读取当前 Git 分支，并用它索引 `vendorURL`、`sdkURL`、`playerSDKURL`。功能分支通常不在映射中，因此下载 DLL 时把 `undefined` 交给 Axios。这不是业务代码或 Node 编译错误。

# 验证步骤

1. 在仓库根目录执行前端生产构建：

```bash
CURRENT_BRANCH=live NODE_ENV=production \
mise x node@16 -- node node_modules/.bin/smb build
```

2. 前端编译成功后生成服务元数据：

```bash
mise x node@16 -- node node_modules/.bin/collect-service \
  "src/**/*.js" \
  --output dist/service-meta/live-activity-common-pendant \
  -c dist/service-meta-inject/live-activity-common-pendant
```

# 判定

- `smb build` 退出码为 0，并出现编译完成信息。
- `collect-service` 退出码为 0。
- 资源体积警告可以单独记录，不等同于构建失败。
- 不要为修复 DLL URL 去修改活动业务代码、Webpack 配置或锁文件。
