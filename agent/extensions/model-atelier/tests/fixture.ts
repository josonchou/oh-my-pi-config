import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { lookup } from "@oh-my-pi/pi-coding-agent/config/registry";

const TEST_PROVIDER = "atelier-test";
const TEST_MODELS = ["atelier-alpha", "atelier-beta"] as const;

export default function atelierFixture(pi: ExtensionAPI): void {
  pi.registerProvider(TEST_PROVIDER, {
    baseUrl: "http://127.0.0.1:1/v1",
    apiKey: "ATELIER_TEST_API_KEY",
    api: "openai-completions",
    models: TEST_MODELS.map((id) => ({
      id,
      name: id,
      reasoning: true,
      input: ["text"],
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      contextWindow: 128000,
      maxTokens: 4096,
    })),
  });

  pi.registerCommand("atelier-inspect", {
    description: "读取隔离测试夹具中各模型角色的真实解析结果。",
    handler: async (args, ctx) => {
      if (args.trim() === "wait-for-config") {
        const { promise, resolve } = Promise.withResolvers<void>();
        ctx.setTimeout(resolve, 600);
        await promise;
      }
      const roleNames = ["default", "smol", "slow", "vision", "plan", "commit", "tiny", "memory", "task", "advisor", "reviewer"];
      const roles = lookup("modelRoles");
      const resolved: Record<string, string | null> = {};
      for (const role of roleNames) {
        const model = ctx.models.resolve(`@${role}`);
        resolved[role] = model ? `${model.provider}/${model.id}` : null;
      }
      const runtime = pi.pi.settings.overlayLayers().overrides as Record<string, unknown>;
      const model = ctx.models.current();
      console.log(JSON.stringify({
        type: "atelier_inspect",
        roles: roles?.get(pi.pi.settings) ?? {},
        runtimeRoles: runtime.modelRoles ?? null,
        runtimeThinking: runtime.defaultThinkingLevel ?? null,
        resolved,
        current: model ? `${model.provider}/${model.id}` : null,
        thinking: pi.getThinkingLevel(),
        defaultThinkingLevel: lookup("defaultThinkingLevel")?.get(pi.pi.settings) ?? null,
      }));
    },
  });
}
