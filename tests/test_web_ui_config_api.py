#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


SERVER_PATH = Path(__file__).resolve().parents[1] / "web_ui" / "server" / "server.py"


def _load_web_server(tmp_path):
    os.environ["WEB_UI_USER_DATA_ROOT"] = str(tmp_path)
    for key in ["user_runtime", "server", "mla_web_ui_server_test"]:
        sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location("mla_web_ui_server_test", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _auth_client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["logged_in"] = True
        session["username"] = "tester"
        session["role"] = "admin"
    return client


def test_guided_config_roundtrip_and_run_env_list(tmp_path):
    module = _load_web_server(tmp_path)
    client = _auth_client(module.app)

    list_resp = client.get("/api/config/list?type=run_env")
    assert list_resp.status_code == 200
    names = [item["name"] for item in list_resp.get_json()["files"]]
    assert "llm_config.yaml" in names
    assert "app_config.json" in names

    guided_resp = client.get("/api/config/guided")
    assert guided_resp.status_code == 200
    payload = guided_resp.get_json()
    assert "llm_config" in payload
    assert "app_config" in payload

    payload["llm_config"]["base_url"] = "https://openrouter.ai/api/v1"
    payload["llm_config"]["models"] = [
        {"name": "openrouter/google/gemini-3-flash-preview", "tool_choice": "required"}
    ]
    payload["app_config"].setdefault("runtime", {})["thinking_enabled"] = False
    payload["app_config"].setdefault("runtime", {})["thinking_steps"] = 9
    payload["app_config"].setdefault("context", {})["user_history_recent_items"] = 4

    save_resp = client.post(
        "/api/config/guided",
        json={
            "llm_config": payload["llm_config"],
            "app_config": payload["app_config"],
        },
    )
    assert save_resp.status_code == 200
    assert save_resp.get_json()["success"] is True

    app_cfg_resp = client.get("/api/config/read?file=app_config.json&type=run_env")
    assert app_cfg_resp.status_code == 200
    app_cfg_text = app_cfg_resp.get_json()["content"]
    assert '"thinking_enabled": false' in app_cfg_text
    assert '"user_history_recent_items": 4' in app_cfg_text

    llm_cfg_resp = client.get("/api/config/read?file=llm_config.yaml&type=run_env")
    assert llm_cfg_resp.status_code == 200
    llm_cfg_text = llm_cfg_resp.get_json()["content"]
    assert "openrouter/google/gemini-3-flash-preview" in llm_cfg_text
