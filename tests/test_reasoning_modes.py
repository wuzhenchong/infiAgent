#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from core.agent_executor import AgentExecutor
from services.llm_client import LLMResponse


class _DummyEmitter:
    def dispatch(self, _event):
        return None


class ReasoningModeTests(unittest.TestCase):
    def _bare_executor(self):
        executor = AgentExecutor.__new__(AgentExecutor)
        executor.agent_name = "alpha_agent"
        executor.execution_model = "demo-model"
        executor.available_tools = ["file_write", "task_history_search"]
        executor.action_history = []
        executor.action_history_fact = []
        executor.execution_traces = []
        executor.thinking_traces = []
        executor.llm_turn_counter = 0
        executor.event_emitter = _DummyEmitter()
        return executor

    def test_build_messages_includes_react_reflection_and_text_only_turns(self):
        executor = self._bare_executor()
        executor.action_history = [
            {
                "_turn": 0,
                "tool_name": "_react_reflection",
                "arguments": {},
                "result": {"status": "success", "output": "先检查目标文件是否存在"},
                "assistant_content": "先检查目标文件是否存在",
                "reasoning_content": "",
                "_has_image": False,
                "_image_base64": None,
            },
            {
                "_turn": 1,
                "tool_name": "_assistant_text",
                "arguments": {},
                "result": {"status": "success", "output": "我已经知道下一步要写入目标文件"},
                "assistant_content": "我已经知道下一步要写入目标文件",
                "reasoning_content": "",
                "_has_image": False,
                "_image_base64": None,
            },
            {
                "_turn": 2,
                "tool_call_id": "call_2_0",
                "tool_name": "file_write",
                "arguments": {"path": "a.txt", "content": "hello"},
                "result": {"status": "success", "output": "ok"},
                "assistant_content": "现在开始写文件",
                "reasoning_content": "",
                "_has_image": False,
                "_image_base64": None,
            },
        ]

        messages = executor._build_messages_from_action_history()
        assistant_texts = [msg.get("content") for msg in messages if msg.get("role") == "assistant"]

        self.assertIn("先检查目标文件是否存在", assistant_texts)
        self.assertIn("我已经知道下一步要写入目标文件", assistant_texts)
        self.assertIn("现在开始写文件", assistant_texts)

    def test_run_react_reflection_persists_text_to_action_history(self):
        executor = self._bare_executor()
        saved = {"count": 0}

        def fake_execute_llm_call(*args, **kwargs):
            return LLMResponse(
                status="success",
                output="先检查最近一次生成的文档并确认需要补写的部分",
                tool_calls=[],
                model="demo-model",
                finish_reason="stop",
                reasoning_content="",
            )

        def fake_save_state(*args, **kwargs):
            saved["count"] += 1

        executor._execute_llm_call = fake_execute_llm_call
        executor._save_state = fake_save_state

        executor._run_react_reflection(
            task_id="/tmp/demo-task",
            task_input="continue task",
            system_prompt="demo prompt",
            messages=[{"role": "user", "content": "请继续"}],
            turn=0,
        )

        self.assertEqual(executor.llm_turn_counter, 1)
        self.assertEqual(saved["count"], 1)
        self.assertEqual(executor.action_history[-1]["tool_name"], "_react_reflection")
        self.assertIn("先检查最近一次生成的文档", executor.action_history[-1]["assistant_content"])

    def test_model_output_payload_prefers_last_execution_turn_over_react_reflection(self):
        executor = self._bare_executor()
        executor.execution_traces = [
            {"debug_label": "execution", "content": "real tool-driving output", "model": "m1"},
            {"debug_label": "react_reflection", "content": "reflection text", "model": "m1"},
        ]
        executor.thinking_traces = []

        payload = executor._build_model_outputs_payload()

        self.assertEqual(payload["last_execution"]["content"], "real tool-driving output")


if __name__ == "__main__":
    unittest.main()
