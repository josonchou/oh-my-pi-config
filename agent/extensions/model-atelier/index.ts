import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { lookup } from "@oh-my-pi/pi-coding-agent/config/registry";

type ThinkingLevel = "inherit" | "off" | "minimal" | "low" | "medium" | "high" | "xhigh" | "max";
type SessionThinkingLevel = ThinkingLevel | "auto";
type RoleOverrides = Record<string, string | null>;

type Preset = {
  modelRoles: Record<string, string>;
  defaultThinkingLevel?: SessionThinkingLevel;
};
type RuntimeSnapshot = {
  rolesOverride: RoleOverrides | undefined;
  thinkingOverride: SessionThinkingLevel | undefined;
  activeModel: string;
  thinkingLevel: SessionThinkingLevel;
};

const THINKING_LEVELS: Record<ThinkingLevel, true> = {
  inherit: true,
  off: true,
  minimal: true,
  low: true,
  medium: true,
  high: true,
  xhigh: true,
  max: true,
};

const PRESET_THINKING_LEVELS: Record<SessionThinkingLevel, true> = {
  ...THINKING_LEVELS,
  auto: true,
};

function record(value: unknown): Record<string, unknown> | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return undefined;
  return value as Record<string, unknown>;
}

function parseThinkingLevel(value: unknown): ThinkingLevel | undefined {
  if (typeof value !== "string" || !Object.hasOwn(THINKING_LEVELS, value)) return undefined;
  return value as ThinkingLevel;
}

function parsePresetThinkingLevel(value: unknown): SessionThinkingLevel | undefined {
  if (typeof value !== "string" || !Object.hasOwn(PRESET_THINKING_LEVELS, value)) return undefined;
  return value as SessionThinkingLevel;
}

function readPreset(value: unknown): Preset | undefined {
  const source = record(value);
  const modelRoles = record(source?.modelRoles);
  if (!modelRoles) return undefined;
  const roles: Record<string, string> = {};
  for (const [role, selector] of Object.entries(modelRoles)) {
    if (typeof selector !== "string") return undefined;
    roles[role] = selector;
  }
  const level = source?.defaultThinkingLevel === undefined
    ? undefined
    : parsePresetThinkingLevel(source.defaultThinkingLevel);
  if (source?.defaultThinkingLevel !== undefined && level === undefined) return undefined;
  return {
    modelRoles: roles,
    ...(level ? { defaultThinkingLevel: level } : {}),
  };
}

type ModelIdentity = {
  provider: string;
  id: string;
};

type SelectorResolution = {
  model: ModelIdentity;
  thinking: ThinkingLevel | undefined;
};

function resolveSelector(
  selector: string,
  roles: Record<string, unknown>,
  resolveModel: (selector: string) => ModelIdentity | undefined,
  aliases: Set<string> = new Set<string>(),
): SelectorResolution | undefined {
  for (const rawCandidate of selector.split(",")) {
    const candidate = rawCandidate.trim();
    if (!candidate) continue;
    const colon = candidate.lastIndexOf(":");
    const level = colon < 0 ? undefined : parseThinkingLevel(candidate.slice(colon + 1));
    const base = level ? candidate.slice(0, colon) : candidate;
    let alias: string | undefined;
    if (base === "*") alias = "default";
    else if (base.startsWith("@")) alias = base.slice(1);
    if (alias !== undefined) {
      if (aliases.has(alias)) continue;
      const target = roles[alias];
      if (typeof target !== "string") continue;
      const nextAliases = new Set(aliases);
      nextAliases.add(alias);
      const resolved = resolveSelector(target, roles, resolveModel, nextAliases);
      if (resolved) {
        return { model: resolved.model, thinking: level ?? resolved.thinking };
      }
      continue;
    }
    const model = resolveModel(base);
    if (model) return { model, thinking: level };
  }
  return undefined;
}

type RuntimeSetting<Value> = {
  clearOverride(scope: ExtensionAPI["pi"]["settings"]): void;
  override(scope: ExtensionAPI["pi"]["settings"], value: Value): void;
};

function restoreSettings<RoleValue, ThinkingValue>(
  snapshot: RuntimeSnapshot,
  settings: ExtensionAPI["pi"]["settings"],
  rolesSetting: RuntimeSetting<RoleValue>,
  thinkingSetting: RuntimeSetting<ThinkingValue>,
): void {
  if (snapshot.rolesOverride === undefined) rolesSetting.clearOverride(settings);
  else rolesSetting.override(settings, snapshot.rolesOverride as RoleValue);
  if (snapshot.thinkingOverride === undefined) thinkingSetting.clearOverride(settings);
  else thinkingSetting.override(settings, snapshot.thinkingOverride as ThinkingValue);
}

type CommandContext = Parameters<Parameters<ExtensionAPI["registerCommand"]>[1]["handler"]>[1];

async function applyModel(
  pi: ExtensionAPI,
  ctx: CommandContext,
  selector: string,
): Promise<boolean> {
  const model = ctx.models.resolve(selector);
  if (!model) return false;
  return await pi.setModel(model);
}

function captureRuntime(
  pi: ExtensionAPI,
  settings: ExtensionAPI["pi"]["settings"],
  ctx: CommandContext,
): RuntimeSnapshot {
  const layers = settings.overlayLayers();
  const overrides = record(layers.overrides) ?? {};
  const current = ctx.models.current();
  if (!current) throw new Error("当前活动模型不可读取。");
  const rolesOverride = record(overrides.modelRoles);
  const thinkingOverride = overrides.defaultThinkingLevel === undefined
    ? undefined
    : parsePresetThinkingLevel(overrides.defaultThinkingLevel);
  if (overrides.defaultThinkingLevel !== undefined && thinkingOverride === undefined) {
    throw new Error("无法读取运行期默认思考等级。");
  }
  return {
    rolesOverride: rolesOverride ? structuredClone(rolesOverride) as RoleOverrides : undefined,
    thinkingOverride,
    activeModel: `${current.provider}/${current.id}`,
    thinkingLevel: pi.getThinkingLevel(),
  };
}

export default function modelAtelier(pi: ExtensionAPI): void {
  pi.setLabel("Model Atelier");

  const settings = pi.pi.settings;
  const rolesSetting = lookup("modelRoles");
  const presetsSetting = lookup("modelPresets");
  const defaultThinkingSetting = lookup("defaultThinkingLevel");
  if (!rolesSetting || !presetsSetting || !defaultThinkingSetting) return;

  let baseline: RuntimeSnapshot | undefined;
  let changedRoles = new Set<string>();
  let operationInProgress = false;

  pi.registerCommand("atelier", {
    description: "临时切换完整模型预设，或恢复切换前的状态。",
    handler: async (args, ctx) => {
      const notify = (text: string): void => ctx.ui.notify(text, "info");
      const reset = async (): Promise<void> => {
        if (!baseline) {
          notify("Model Atelier 当前没有临时预设。");
          return;
        }
        const saved = baseline;
        const previous = captureRuntime(pi, settings, ctx);
        try {
          restoreSettings(saved, settings, rolesSetting, defaultThinkingSetting);
          if (!await applyModel(pi, ctx, saved.activeModel)) {
            restoreSettings(previous, settings, rolesSetting, defaultThinkingSetting);
            notify("原活动模型当前不可用；Model Atelier 状态保持不变。");
            return;
          }
          pi.setThinkingLevel(saved.thinkingLevel);
          baseline = undefined;
          changedRoles = new Set<string>();
          notify("已恢复进入 Model Atelier 前的模型配置。");
        } catch {
          restoreSettings(previous, settings, rolesSetting, defaultThinkingSetting);
          await applyModel(pi, ctx, previous.activeModel);
          pi.setThinkingLevel(previous.thinkingLevel);
          notify("恢复原模型状态失败；Model Atelier 状态保持不变。");
        }
      };
      const switchPreset = async (name: string): Promise<void> => {
        const presets = record(presetsSetting.get(settings));
        const preset = readPreset(presets?.[name]);
        if (!preset) {
          notify(`预设“${name}”不存在或格式无效。`);
          return;
        }
        if (!Object.hasOwn(preset.modelRoles, "default")) {
          notify(`预设“${name}”未设置默认模型。`);
          return;
        }
        const previous = captureRuntime(pi, settings, ctx);
        const firstBaseline = baseline ?? previous;
        const nextChangedRoles = new Set(changedRoles);
        for (const role of Object.keys(rolesSetting.get(settings))) nextChangedRoles.add(role);
        for (const role of Object.keys(firstBaseline.rolesOverride ?? {})) nextChangedRoles.add(role);
        for (const role of Object.keys(preset.modelRoles)) nextChangedRoles.add(role);

        const nextRoles: Record<string, string | null> = {};
        for (const role of nextChangedRoles) nextRoles[role] = preset.modelRoles[role] ?? null;

        try {
          rolesSetting.override(settings, nextRoles as Record<string, string>);
          if (preset.defaultThinkingLevel === undefined) defaultThinkingSetting.clearOverride(settings);
          else defaultThinkingSetting.override(settings, preset.defaultThinkingLevel);
          const roles = rolesSetting.get(settings);
          const selected = resolveSelector(
            preset.modelRoles.default,
            roles,
            (selector) => ctx.models.resolve(selector),
          );
          const target = ctx.models.resolve("@default");
          if (
            !target
            || !selected
            || selected.model.provider !== target.provider
            || selected.model.id !== target.id
          ) {
            restoreSettings(previous, settings, rolesSetting, defaultThinkingSetting);
            notify(`预设“${name}”的默认模型不可用，或角色别名存在循环。`);
            return;
          }
          const switched = await pi.setModel(target);
          if (!switched) {
            restoreSettings(previous, settings, rolesSetting, defaultThinkingSetting);
            await applyModel(pi, ctx, previous.activeModel);
            pi.setThinkingLevel(previous.thinkingLevel);
            notify(`切换到预设“${name}”失败，当前状态已恢复。`);
            return;
          }
          if (selected.thinking && selected.thinking !== "inherit") {
            pi.setThinkingLevel(selected.thinking);
          } else if (!selected.thinking && preset.defaultThinkingLevel) {
            pi.setThinkingLevel(preset.defaultThinkingLevel);
          }
          baseline = firstBaseline;
          changedRoles = nextChangedRoles;
          notify(`已临时切换到预设“${name}”。`);
        } catch {
          restoreSettings(previous, settings, rolesSetting, defaultThinkingSetting);
          await applyModel(pi, ctx, previous.activeModel);
          pi.setThinkingLevel(previous.thinkingLevel);
          notify(`切换到预设“${name}”失败，当前状态已恢复。`);
        }
      };
      if (ctx.agent.kind !== "main") {
        notify("Model Atelier 仅适用于主会话；子代理继承父会话角色配置。");
        return;
      }
      if (!ctx.isIdle() || ctx.hasPendingMessages()) {
        notify("Model Atelier 仅可在会话空闲且没有待处理消息时使用。");
        return;
      }
      if (operationInProgress) {
        notify("Model Atelier 正在处理另一项操作。");
        return;
      }
      operationInProgress = true;
      try {
        const argument = args.trim();
        if (argument === "reset") {
          await reset();
          return;
        }
        const available = record(presetsSetting.get(settings));
        const names = available
          ? Object.keys(available).filter((name) => {
              const preset = readPreset(available[name]);
              return preset !== undefined && Object.hasOwn(preset.modelRoles, "default");
            })
          : [];
        if (!argument) {
          if (!ctx.hasUI) {
            notify(names.length > 0
              ? `可用预设：${names.join("、")}。使用 /atelier <预设名> 切换，/atelier reset 恢复。`
              : "当前没有可用预设。");
            return;
          }
          const items = [...names];
          if (baseline) items.push("reset");
          const selected = await ctx.ui.select("Model Atelier", items);
          if (selected) {
            if (selected === "reset") await reset();
            else await switchPreset(selected);
          }
          return;
        }
        await switchPreset(argument);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        notify(`Model Atelier 操作失败：${message}`);
      } finally {
        operationInProgress = false;
      }
    },
  });
  const release = async (ctx: CommandContext): Promise<void> => {
    if (!baseline) return;
    const saved = baseline;
    baseline = undefined;
    changedRoles = new Set<string>();
    restoreSettings(saved, settings, rolesSetting, defaultThinkingSetting);
    if (await applyModel(pi, ctx, saved.activeModel)) pi.setThinkingLevel(saved.thinkingLevel);
  };
  pi.on("session_before_switch", async (_event, ctx) => release(ctx));
  pi.on("session_shutdown", async (_event, ctx) => release(ctx));
}

