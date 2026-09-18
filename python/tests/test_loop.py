"""Runs without an API key: python tests/test_loop.py (or pytest)."""
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["RUNS_DIR"] = tempfile.mkdtemp()

from agent import loop, tools  # noqa: E402


class FakeMessages:
    def __init__(self):
        self.calls = 0

    def create(self, **kw):
        self.calls += 1
        usage = types.SimpleNamespace(input_tokens=10, output_tokens=5)
        if self.calls == 1:
            block = types.SimpleNamespace(type="tool_use", id="t1", name="get_time", input={})
            return types.SimpleNamespace(stop_reason="tool_use", usage=usage, content=[block])
        # second request must carry the tool result back
        last = kw["messages"][-1]
        assert last["role"] == "user"
        assert last["content"][0]["tool_use_id"] == "t1"
        assert last["content"][0]["is_error"] is False
        block = types.SimpleNamespace(type="text", text="done")
        return types.SimpleNamespace(stop_reason="end_turn", usage=usage, content=[block])


def test_loop_dispatches_tool_and_stops():
    fake = FakeMessages()
    loop.client = types.SimpleNamespace(messages=fake)
    t = loop.run("what time is it")
    assert fake.calls == 2
    assert t["steps"][0]["tool"] == "get_time"
    assert t["output"] == "done"
    assert t["stop_reason"] == "end_turn"
    assert t["usage"] == {"input": 20, "output": 10}
    assert (loop.RUNS_DIR / f"{t['id']}.json").exists()


def test_unknown_tool_is_error_text_not_crash():
    assert tools.dispatch("nope", {}).startswith("error:")
    assert tools.dispatch("fetch_url", {"url": "not a url"}).startswith("error:")


def test_remember_recall_roundtrip():
    tools.remember("k", "v")
    assert tools.recall("k") == "v"
    assert tools.recall("missing").startswith("nothing stored")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
