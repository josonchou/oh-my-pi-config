from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from collections.abc import Callable


EXTENSION_DIR = Path(__file__).resolve().parents[1]
EXTENSION = EXTENSION_DIR / "index.ts"
FIXTURE = EXTENSION_DIR / "tests" / "fixture.ts"


def write_config(path: Path) -> None:
    path.write_text(
        """modelRoles:
  default: atelier-test/atelier-alpha
  smol: atelier-test/atelier-beta
  plan: atelier-test/atelier-beta
  task: atelier-test/atelier-beta
  tiny: atelier-test/atelier-alpha
  commit: atelier-test/atelier-alpha
  advisor: atelier-test/atelier-beta
  vision: atelier-test/atelier-alpha
  slow: atelier-test/atelier-beta
  memory: atelier-test/atelier-alpha
  reviewer: atelier-test/atelier-alpha
defaultThinkingLevel: low
modelPresets:
  alpha:
    modelRoles:
      default: atelier-test/atelier-alpha:high
      smol: atelier-test/atelier-beta
      task: atelier-test/atelier-alpha
    defaultThinkingLevel: medium
  beta:
    modelRoles:
      default: atelier-test/atelier-beta
      plan: atelier-test/atelier-alpha
      task: atelier-test/atelier-beta
    defaultThinkingLevel: high
  aliased:
    modelRoles:
      default: "@task:low"
      task: atelier-test/atelier-beta:high
      plan: "@task"
  candidate:
    modelRoles:
      default: "atelier-test/not-present,atelier-test/atelier-alpha:medium"
  partial:
    modelRoles:
      default: atelier-test/atelier-alpha
  alias-loop:
    modelRoles:
      default: "@task"
      task: "@default"
  missing-default:
    modelRoles:
      smol: atelier-test/atelier-alpha
  unavailable:
    modelRoles:
      default: atelier-test/not-present
  auto-level:
    modelRoles:
      default: atelier-test/atelier-beta:high
    defaultThinkingLevel: auto
  bad-level:
    modelRoles:
      default: atelier-test/atelier-alpha
    defaultThinkingLevel: meddium
advisor:
  enabled: false
retry:
  enabled: false
  modelFallback: false
autolearn:
  enabled: false
contextPromotion:
  enabled: false
""",
        encoding="utf-8",
    )

def write_safety_config(path: Path) -> None:
    path.write_text(
        """advisor:
  enabled: false
retry:
  enabled: false
  modelFallback: false
autolearn:
  enabled: false
contextPromotion:
  enabled: false
""",
        encoding="utf-8",
    )


class RpcProcess:
    def __init__(self, ui: bool = False, cli_role_overrides: bool = True) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="model-atelier-")
        self.home = Path(self.temp.name)
        self.agent_dir = self.home / "agent"
        self.config_dir = self.home / "omp"
        self.cwd = self.home / "project"
        self.agent_dir.mkdir(parents=True)
        self.config_dir.mkdir(parents=True)
        self.cwd.mkdir(parents=True)
        self.global_config = self.agent_dir / "config.yml"
        self.overlay_config = self.home / "overlay.yml"
        write_config(self.global_config)
        write_safety_config(self.overlay_config)
        self.original_global = self.global_config.read_bytes()
        self.original_overlay = self.overlay_config.read_bytes()

        binary = shutil.which("omp")
        if binary is None:
            self.temp.cleanup()
            raise RuntimeError("未找到 omp 可执行文件。")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.home),
            "TMPDIR": str(self.home),
            "PI_CONFIG_DIR": str(self.config_dir),
            "PI_CODING_AGENT_DIR": str(self.agent_dir),
            "PI_NO_TITLE": "1",
            "ATELIER_TEST_API_KEY": "not-a-real-account-key",
        }
        command = [
            binary,
            "--mode", "rpc-ui" if ui else "rpc",
            "--no-tools",
            "--no-lsp",
            "--no-skills",
            "--no-rules",
            "--no-title",
            "--no-extensions",
            "--config", str(self.overlay_config),
            "-e", str(EXTENSION),
            "-e", str(FIXTURE),
        ]
        if cli_role_overrides:
            command.extend([
                "--smol", "atelier-test/atelier-alpha:low",
                "--plan", "atelier-test/atelier-beta:high",
            ])
        if not ui:
            command.append("--no-ui")
        self.process = subprocess.Popen(
            command,
            cwd=self.cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        if self.process.stdout is None or self.process.stdin is None:
            raise RuntimeError("无法打开 OMP RPC 标准流。")
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer = bytearray()
        self.frames: list[dict[str, object]] = []
        self.sequence = 0
        self.wait_for(lambda frame: frame.get("type") == "ready")
        request_id = self.request("get_available_commands")
        command_frame = self.wait_for(
            lambda frame: frame.get("type") == "response" and frame.get("id") == request_id
        )
        commands = command_frame.get("data", {}).get("commands", [])
        names = {command.get("name") for command in commands}
        if "atelier" not in names or "atelier-inspect" not in names:
            raise AssertionError(f"扩展命令未由 OMP 注册：{names}")

    def send(self, payload: dict[str, object]) -> None:
        if self.process.stdin is None:
            raise RuntimeError("RPC 标准输入已关闭。")
        self.process.stdin.write((json.dumps(payload) + "\n").encode())
        self.process.stdin.flush()

    def request(self, command: str, **values: object) -> str:
        self.sequence += 1
        request_id = f"test-{self.sequence}"
        self.send({"id": request_id, "type": command, **values})
        return request_id

    def wait_for(
        self,
        predicate: Callable[[dict[str, object]], bool],
        timeout: float = 30.0,
        start: int = 0,
    ) -> dict[str, object]:
        import time

        deadline = time.monotonic() + timeout
        while True:
            for frame in self.frames[start:]:
                if predicate(frame):
                    return frame
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"等待 RPC 帧超时；已收到 {len(self.frames)} 帧。")
            ready = self.selector.select(remaining)
            if not ready:
                continue
            stdout = self.process.stdout
            if stdout is None:
                raise RuntimeError("RPC 标准输出已关闭。")
            chunk = os.read(stdout.fileno(), 65536)
            if not chunk:
                raise AssertionError(f"OMP 提前退出，状态码 {self.process.poll()}。")
            self.buffer.extend(chunk)
            while b"\n" in self.buffer:
                line, _, remainder = self.buffer.partition(b"\n")
                self.buffer = bytearray(remainder)
                try:
                    frame = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if isinstance(frame, dict):
                    self.frames.append(frame)
    def prompt(self, text: str) -> dict[str, object]:
        request_id = self.request("prompt", message=text)
        frame = self.wait_for(
            lambda item: (
                item.get("type") == "prompt_result" and item.get("id") == request_id
            ) or (
                item.get("type") == "response"
                and item.get("id") == request_id
                and item.get("data", {}).get("agentInvoked") is False
            )
        )
        result = frame.get("data", frame)
        if result.get("agentInvoked") is not False:
            raise AssertionError(f"扩展 slash command 意外启动了 agent turn：{frame}")
        return frame

    def inspect(self, wait_for_config: bool = False) -> dict[str, object]:
        start = len(self.frames)
        message = "/atelier-inspect"
        if wait_for_config:
            message += " wait-for-config"
        self.prompt(message)
        return self.wait_for(lambda item: item.get("type") == "atelier_inspect", start=start)

    def assert_files_unchanged(self, test: unittest.TestCase) -> None:
        test.assertEqual(self.global_config.read_bytes(), self.original_global)
        test.assertEqual(self.overlay_config.read_bytes(), self.original_overlay)

    def close(self, cleanup: bool = True) -> None:
        if self.process.poll() is None:
            if self.process.stdin is not None:
                self.process.stdin.close()
            stdout = self.process.stdout
            if stdout is not None:
                for key in list(self.selector.get_map().values()):
                    self.selector.unregister(key.fileobj)
                self.selector.close()
                drain = selectors.DefaultSelector()
                drain.register(stdout, selectors.EVENT_READ)
                while self.process.poll() is None:
                    if drain.select(1):
                        os.read(stdout.fileno(), 65536)
                    else:
                        break
                drain.close()
            self.process.wait(timeout=10)
        if cleanup:
            self.temp.cleanup()
        if self.process.stdout is not None:
            self.process.stdout.close()


class ModelAtelierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rpc = RpcProcess()

    def tearDown(self) -> None:
        self.rpc.close()

    def test_switch_twice_then_reset_restores_roles_thinking_and_active_model(self) -> None:
        before = self.rpc.inspect()
        self.assertEqual(before["runtimeRoles"], {
            "smol": "atelier-test/atelier-alpha:low",
            "plan": "atelier-test/atelier-beta:high",
        })
        self.rpc.prompt("/atelier alpha")
        alpha = self.rpc.inspect()
        self.assertEqual(alpha["current"], "atelier-test/atelier-alpha")
        self.assertEqual(alpha["roles"]["task"], "atelier-test/atelier-alpha")
        self.assertEqual(alpha["thinking"], "high")
        self.rpc.prompt("/atelier beta")
        beta = self.rpc.inspect()
        self.assertEqual(beta["current"], "atelier-test/atelier-beta")
        self.assertEqual(beta["resolved"]["plan"], "atelier-test/atelier-alpha")
        self.assertEqual(beta["resolved"]["task"], "atelier-test/atelier-beta")
        self.rpc.prompt("/atelier reset")
        after = self.rpc.inspect()
        self.assertEqual(after["current"], before["current"])
        self.assertEqual(after["roles"], before["roles"])
        self.assertEqual(after["resolved"], before["resolved"])
        self.assertEqual(after["thinking"], before["thinking"])
        self.assertEqual(after["runtimeRoles"], before["runtimeRoles"])
        self.assertEqual(after["runtimeThinking"], before["runtimeThinking"])
        self.assertEqual(after["defaultThinkingLevel"], before["defaultThinkingLevel"])
        self.rpc.assert_files_unchanged(self)

    def test_reset_clears_runtime_override_when_it_did_not_exist_before(self) -> None:
        self.rpc.close()
        self.rpc = RpcProcess(cli_role_overrides=False)
        before = self.rpc.inspect()
        self.assertIsNone(before["runtimeRoles"])
        self.rpc.prompt("/atelier beta")
        self.rpc.prompt("/atelier reset")
        after = self.rpc.inspect()
        self.assertIsNone(after["runtimeRoles"])
        self.assertEqual(after["roles"], before["roles"])
        self.assertEqual(after["resolved"], before["resolved"])
        self.rpc.assert_files_unchanged(self)

    def test_reset_reads_lower_layer_changes_instead_of_freezing_merged_roles(self) -> None:
        before = self.rpc.inspect()
        self.assertEqual(before["roles"]["reviewer"], "atelier-test/atelier-alpha")
        self.rpc.prompt("/atelier beta")
        temporary = self.rpc.inspect()
        self.assertNotEqual(temporary["roles"].get("reviewer"), "atelier-test/atelier-alpha")

        original_config = self.rpc.global_config.read_text(encoding="utf-8")
        old_role = "  reviewer: atelier-test/atelier-alpha\n"
        new_role = "  reviewer: atelier-test/atelier-beta\n"
        self.assertEqual(original_config.count(old_role), 1)
        updated_config = original_config.replace(old_role, new_role, 1)
        self.rpc.global_config.write_text(updated_config, encoding="utf-8")

        self.rpc.prompt("/atelier reset")
        after = self.rpc.inspect(wait_for_config=True)
        self.assertEqual(after["roles"]["reviewer"], "atelier-test/atelier-beta")
        self.assertEqual(after["resolved"]["reviewer"], "atelier-test/atelier-beta")
        self.assertEqual(self.rpc.global_config.read_text(encoding="utf-8"), updated_config)
        self.assertEqual(self.rpc.overlay_config.read_bytes(), self.rpc.original_overlay)


    def test_alias_suffix_precedence_and_candidate_fallback_follow_core_resolution(self) -> None:
        self.rpc.prompt("/atelier aliased")
        aliased = self.rpc.inspect()
        self.assertEqual(aliased["current"], "atelier-test/atelier-beta")
        self.assertEqual(aliased["thinking"], "low")
        self.assertEqual(aliased["resolved"]["plan"], "atelier-test/atelier-beta")
        self.rpc.prompt("/atelier reset")

        self.rpc.prompt("/atelier candidate")
        candidate = self.rpc.inspect()
        self.assertEqual(candidate["current"], "atelier-test/atelier-alpha")
        self.assertEqual(candidate["thinking"], "medium")
        self.rpc.prompt("/atelier reset")
        self.rpc.assert_files_unchanged(self)
    def test_partial_preset_does_not_inherit_roles_from_previous_preset(self) -> None:
        self.rpc.prompt("/atelier beta")
        self.rpc.prompt("/atelier partial")
        result = self.rpc.inspect()
        self.assertEqual(result["current"], "atelier-test/atelier-alpha")
        self.assertNotEqual(result["resolved"]["task"], "atelier-test/atelier-beta")
        self.rpc.prompt("/atelier reset")
        self.rpc.assert_files_unchanged(self)

    def test_auto_default_thinking_level_preset_switches_and_restores(self) -> None:
        before = self.rpc.inspect()
        self.rpc.prompt("/atelier auto-level")
        switched = self.rpc.inspect()
        self.assertEqual(switched["current"], "atelier-test/atelier-beta")
        self.assertEqual(switched["thinking"], "high")
        self.assertEqual(switched["defaultThinkingLevel"], "auto")
        self.rpc.prompt("/atelier reset")
        after = self.rpc.inspect()
        self.assertEqual(after["current"], before["current"])
        self.assertEqual(after["thinking"], before["thinking"])
        self.assertEqual(after["defaultThinkingLevel"], before["defaultThinkingLevel"])
        self.rpc.assert_files_unchanged(self)

    def test_invalid_presets_leave_state_unchanged_and_do_not_start_agent_turn(self) -> None:
        before = self.rpc.inspect()
        for name in ("absent", "missing-default", "unavailable", "alias-loop", "bad-level"):
            self.rpc.prompt(f"/atelier {name}")
            after = self.rpc.inspect()
            self.assertEqual(after["current"], before["current"], name)
            self.assertEqual(after["roles"], before["roles"], name)
            self.assertEqual(after["thinking"], before["thinking"], name)
        self.rpc.assert_files_unchanged(self)

    def test_headless_picker_lists_presets_without_blocking_and_reset_is_idempotent(self) -> None:
        self.rpc.prompt("/atelier")
        self.rpc.prompt("/atelier reset")
        state = self.rpc.inspect()
        self.assertEqual(state["current"], "atelier-test/atelier-alpha")
        self.rpc.assert_files_unchanged(self)

    def test_ui_picker_cancel_is_a_no_op(self) -> None:
        self.rpc.close()
        self.rpc = RpcProcess(ui=True)
        before = self.rpc.inspect()
        request_id = self.rpc.request("prompt", message="/atelier")
        request = self.rpc.wait_for(
            lambda frame: frame.get("type") == "extension_ui_request" and frame.get("method") == "select"
        )
        options = request.get("options", [])
        self.assertIn("alpha", options)
        self.assertNotIn("missing-default", options)
        self.rpc.send({
            "type": "extension_ui_response",
            "id": request["id"],
            "cancelled": True,
        })
        self.rpc.wait_for(
            lambda frame: frame.get("type") == "prompt_result" and frame.get("id") == request_id
        )
        after = self.rpc.inspect()
        self.assertEqual(after["current"], before["current"])
        self.assertEqual(after["roles"], before["roles"])
        self.rpc.assert_files_unchanged(self)

    def test_new_session_releases_temporary_runtime_override(self) -> None:
        self.rpc.prompt("/atelier beta")
        request_id = self.rpc.request("new_session")
        self.rpc.wait_for(
            lambda frame: frame.get("type") == "response"
            and frame.get("id") == request_id
            and frame.get("command") == "new_session"
        )
        state = self.rpc.inspect()
        self.assertEqual(state["current"], "atelier-test/atelier-alpha")
        self.assertEqual(state["roles"]["task"], "atelier-test/atelier-beta")
        self.rpc.assert_files_unchanged(self)

    def test_shutdown_releases_runtime_override_without_persisting_it(self) -> None:
        self.rpc.prompt("/atelier beta")
        self.rpc.close(cleanup=False)
        self.assertEqual(self.rpc.global_config.read_bytes(), self.rpc.original_global)
        self.assertEqual(self.rpc.overlay_config.read_bytes(), self.rpc.original_overlay)


if __name__ == "__main__":
    unittest.main()

