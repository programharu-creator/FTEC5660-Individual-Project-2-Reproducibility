"""Offline request-contract tests; no network or real API keys."""
from types import SimpleNamespace
import pytest

from lits.lm.openai_chat import OpenAIChatModel
from assignment.study import CallLimitReached, Ledger


@pytest.mark.parametrize("endpoint,enabled,expected", [
    ("https://api.deepseek.com", False, {"thinking": {"type": "disabled"}}),
    ("https://api.deepseek.com", True, {"thinking": {"type": "enabled"}}),
    ("https://api.openai.com/v1", False, None),
    ("http://localhost:8000/v1", False, {"chat_template_kwargs": {"enable_thinking": False}}),
])
def test_endpoint_thinking_contract(endpoint, enabled, expected):
    model = OpenAIChatModel("test-model", api_key="offline-test-placeholder",
                            base_url=endpoint, enable_thinking=enabled)
    requests = []
    def fake_request(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="42", tool_calls=[]))],
            usage=SimpleNamespace(prompt_tokens=8, completion_tokens=2))
    model.client.chat.completions.create = fake_request
    try:
        assert model("A test question", temperature=0.7, top_p=1.0).text == "42"
        assert requests[0]["extra_body"] == expected
        assert requests[0]["temperature"] == 0.7
        assert requests[0]["top_p"] == 1.0
    finally:
        model.client.close()


def test_call_limit_stops_before_another_request_and_log_has_no_key(tmp_path):
    calls = []
    def request(fn, *args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(id="offline", model="offline-test-model",
            usage=SimpleNamespace(model_dump=lambda **kw: {"prompt_tokens": 8, "completion_tokens": 2}),
            choices=[SimpleNamespace(finish_reason="stop")])
    ledger = Ledger(tmp_path / "calls.jsonl", limit=1)
    logged = ledger.wrap(request)
    logged(None, model="offline", messages=[{"role": "user", "content": "Public test"}])
    with pytest.raises(CallLimitReached):
        logged(None, model="offline", messages=[])
    assert len(calls) == 1
    text = ledger.path.read_text(encoding="utf-8")
    assert "api_key" not in text and "Public test" not in text


def test_stable_deepseek_tool_schema_keeps_local_validation(monkeypatch):
    from lits.lm.base import ToolCallOutput
    model = OpenAIChatModel("offline", api_key="offline-placeholder",
                            base_url="https://api.deepseek.com")
    requests = []
    def fake(**kwargs):
        requests.append(kwargs)
        function = SimpleNamespace(name="group_answers", arguments='{"n0":"42"}')
        msg = SimpleNamespace(content=None,
            tool_calls=[SimpleNamespace(id="call_offline", function=function)],
            model_dump=lambda: {"content": None})
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5))
    model.client.chat.completions.create = fake
    tool = {"name": "group_answers", "strict": True, "input_schema": {
        "type": "object", "properties": {"n0": {"type": ["string", "null"]}},
        "required": ["n0"], "additionalProperties": False}}
    try:
        result = model("Offline test", tools=[tool], parallel_tool_calls=False)
        assert isinstance(result, ToolCallOutput)
        assert result.tool_calls[0].input_args == {"n0": "42"}
        assert "strict" not in requests[0]["tools"][0]["function"]
        assert requests[0]["tools"][0]["function"]["parameters"] == tool["input_schema"]
        assert tool["strict"] is True
    finally:
        model.client.close()


def test_real_mcts_rollout_depth_regressions_without_inference(monkeypatch):
    from lits.lm import get_lm
    from lits.config import ExperimentConfig
    from lits.components.factory import create_components
    from unit_test.agents.tree.test_selection_hooks import check_rollout_path_cutoffs
    monkeypatch.setenv("PYTHONBREAKPOINT", "0")
    model = get_lm("openai/offline-test-model", api_key="offline-placeholder",
                   base_url="https://api.deepseek.com")
    def forbid_request(**kwargs):
        raise AssertionError("The upstream prepared-path regression must not make API calls")
    model.client.chat.completions.create = forbid_request
    config = ExperimentConfig(dataset="math500", policy_model_name="openai/offline-test-model",
        eval_model_name="openai/offline-test-model", search_framework="rest",
        search_args={"terminate_constraints": ["step_signal"], "max_steps": 3},
        component_args={"think_for_correctness": False, "think_for_usefulness": False,
                        "n_for_correctness": 2, "n_for_usefulness": 1})
    try:
        world, policy, reward = create_components(task_type="language_grounded", task_name="math500",
            base_model=model, eval_base_model=model, terminal_model=None, tool_use_spec=None, config=config)
        failures = check_rollout_path_cutoffs(world, policy, reward)
        assert failures == []
    finally:
        model.client.close()


def test_api_errors_abort_before_component_fallbacks(tmp_path):
    from assignment.study import APIRequestFailed
    def failing_request(fn, *args, **kwargs):
        raise ValueError("sensitive-provider-message-must-not-be-logged")
    ledger = Ledger(tmp_path / "calls.jsonl", limit=5)
    with pytest.raises(APIRequestFailed):
        ledger.wrap(failing_request)(None, model="offline", messages=[])
    record = ledger.path.read_text(encoding="utf-8")
    assert '"error_type": "ValueError"' in record
    assert "sensitive-provider-message" not in record
