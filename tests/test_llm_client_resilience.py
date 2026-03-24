#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from services.llm_client import LLMResponse, SimpleLLMClient


class LLMClientResilienceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.original_user_data_root = os.environ.get("MLA_USER_DATA_ROOT")
        os.environ["MLA_USER_DATA_ROOT"] = self.temp_dir.name
        self.addCleanup(self._restore_user_data_root)

        llm_config_path = Path(__file__).parent / "llm_config_dummy.yaml"
        self.client = SimpleLLMClient(llm_config_path=str(llm_config_path))

    def _restore_user_data_root(self):
        if self.original_user_data_root is None:
            os.environ.pop("MLA_USER_DATA_ROOT", None)
        else:
            os.environ["MLA_USER_DATA_ROOT"] = self.original_user_data_root

    def test_first_chunk_timeout_returns_quickly_without_waiting_for_worker(self):
        self.client.first_chunk_timeout = 0.05
        self.client.timeout = 1
        self.client.stream_timeout = 1

        def slow_completion(**kwargs):
            time.sleep(0.30)
            return iter(())

        started_at = time.perf_counter()
        with patch("services.llm_client.completion", side_effect=slow_completion):
            with patch.object(self.client, "_append_debug_record", lambda **kwargs: None):
                response = self.client._chat_internal(
                    history=[],
                    model="openai/gpt-4o-mini",
                    system_prompt="system",
                    tool_list=[],
                    tool_choice=None,
                    temperature=0,
                    max_tokens=0,
                )
        elapsed = time.perf_counter() - started_at

        self.assertEqual(response.status, "error")
        self.assertEqual(response.finish_reason, "timeout")
        self.assertLess(elapsed, 0.20)

    def test_non_retriable_error_stops_retry_loop_early(self):
        attempts = []

        def fake_chat_internal(*args):
            attempts.append(args[-1])
            return LLMResponse(
                status="error",
                output="",
                tool_calls=[],
                model="openai/gpt-4o-mini",
                finish_reason="error",
                error_information="Invalid API key provided by upstream",
            )

        with patch.object(self.client, "_chat_internal", side_effect=fake_chat_internal):
            with patch("services.llm_client.time.sleep", lambda *_: None):
                with self.assertRaises(Exception) as ctx:
                    self.client.chat(
                        history=[],
                        model="openai/gpt-4o-mini",
                        system_prompt="system",
                        tool_list=[],
                        tool_choice=None,
                        max_retries=3,
                    )

        self.assertEqual(attempts, [1])
        self.assertIn("不可重试", str(ctx.exception))

    def test_retry_emits_stream_reset_before_second_attempt(self):
        streamed = []

        def fake_chat_internal(*args):
            stream_callback = args[-2]
            attempt_index = args[-1]
            if attempt_index == 1:
                stream_callback({
                    "kind": "content",
                    "text": "partial",
                    "model": "demo-model",
                    "debug_label": "execution",
                    "attempt": attempt_index,
                })
                return LLMResponse(
                    status="error",
                    output="",
                    tool_calls=[],
                    model="demo-model",
                    finish_reason="timeout",
                    error_information="request timed out",
                )

            stream_callback({
                "kind": "content",
                "text": "final",
                "model": "demo-model",
                "debug_label": "execution",
                "attempt": attempt_index,
            })
            return LLMResponse(
                status="success",
                output="done",
                tool_calls=[],
                model="demo-model",
                finish_reason="stop",
            )

        with patch.object(self.client, "_chat_internal", side_effect=fake_chat_internal):
            with patch("services.llm_client.time.sleep", lambda *_: None):
                response = self.client.chat(
                    history=[],
                    model="openai/gpt-4o-mini",
                    system_prompt="system",
                    tool_list=[],
                    tool_choice=None,
                    max_retries=1,
                    stream_callback=streamed.append,
                )

        self.assertEqual(response.status, "success")
        self.assertEqual(streamed[0]["kind"], "content")
        self.assertEqual(streamed[0]["attempt"], 1)
        self.assertEqual(streamed[1]["kind"], "reset")
        self.assertEqual(streamed[1]["attempt"], 2)
        self.assertEqual(streamed[1]["reason"], "retry")
        self.assertEqual(streamed[2]["kind"], "content")
        self.assertEqual(streamed[2]["attempt"], 2)


if __name__ == "__main__":
    unittest.main()
