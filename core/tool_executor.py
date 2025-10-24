#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具执行器 - 通过HTTP调用toolServer
参考原项目tool_utils.py的逻辑
"""

import requests
import yaml
import json
from typing import Dict, Any
from pathlib import Path


class ToolExecutor:
    """工具执行器 - 通过HTTP调用toolServer"""
    
    def __init__(self, config_loader, hierarchy_manager):
        """
        初始化工具执行器
        
        Args:
            config_loader: 配置加载器
            hierarchy_manager: 层级管理器
        """
        self.config_loader = config_loader
        self.hierarchy_manager = hierarchy_manager
        self.task_cache = {}  # 缓存已创建的任务
        
        # 从tool_config.yaml读取toolServer URL
        self.tools_server_url = self._load_tools_server_url()
    
    def _load_tools_server_url(self) -> str:
        """从配置文件加载工具服务器URL"""
        try:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "run_env_config" / "tool_config.yaml"
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                url = config.get('tools_server', 'http://127.0.0.1:8001/')
                # 移除末尾的斜杠
                return url.rstrip('/')
        except Exception as e:
            print(f"⚠️ 加载工具服务器配置失败: {e}，使用默认值")
            return "http://127.0.0.1:8001"
    
    def _ensure_task_exists(self, task_id: str):
        """确保任务在toolServer中存在"""
        if task_id in self.task_cache:
            return
        
        try:
            # 检查任务状态
            status_url = f"{self.tools_server_url}/api/task/{task_id}/status"
            response = requests.get(status_url, timeout=5)
            
            if response.status_code == 200:
                self.task_cache[task_id] = True
                return
            
            # 任务不存在，创建它
            create_url = f"{self.tools_server_url}/api/task/create"
            params = {"task_id": task_id, "task_name": f"MLA-V3-{task_id}"}
            create_response = requests.post(create_url, params=params, timeout=10)
            
            if create_response.status_code == 200:
                print(f"✅ 任务 '{task_id}' 已在toolServer中创建")
                self.task_cache[task_id] = True
            else:
                print(f"⚠️ 创建任务失败: {create_response.text}")
        
        except Exception as e:
            print(f"⚠️ 检查/创建任务时出错: {e}")
    
    def execute(self, tool_name: str, arguments: Dict[str, Any], task_id: str) -> Dict:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            task_id: 任务ID
            
        Returns:
            执行结果字典
        """
        try:
            # 获取工具配置
            tool_config = self.config_loader.get_tool_config(tool_name)
            tool_type = tool_config.get("type")
            
            # 特殊处理final_output
            if tool_name == "final_output":
                return {
                    "status": arguments.get("status", "success"),
                    "output": arguments.get("output", ""),
                    "error_information": arguments.get("error_information", "")
                }
            
            # 判断是普通工具还是子Agent
            if tool_type == "tool_call_agent":
                # 普通工具 - 通过HTTP调用toolServer
                return self._call_toolserver(tool_name, arguments, task_id)
            
            elif tool_type == "llm_call_agent":
                # 子Agent - 递归调用
                # 给 task_input 添加随机后缀（避免同样输入的缓存冲突）
                import uuid
                original_input = arguments.get("task_input", "")
                random_suffix = f" [call-{uuid.uuid4().hex[:8]}]"
                arguments["task_input"] = original_input + random_suffix
                return self._execute_sub_agent(tool_name, tool_config, arguments, task_id)
            
            else:
                return {
                    "status": "error",
                    "output": "",
                    "error_information": f"不支持的工具类型: {tool_type}"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error_information": f"工具执行失败: {str(e)}"
            }
    
    def _call_toolserver(self, tool_name: str, arguments: Dict, task_id: str) -> Dict:
        """通过HTTP调用toolServer执行工具"""
        try:
            # 确保任务存在
            self._ensure_task_exists(task_id)
            
            # 构建请求
            execute_url = f"{self.tools_server_url}/api/tool/execute"
            payload = {
                "task_id": task_id,
                "tool_name": tool_name,
                "params": arguments
            }
            
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json; charset=utf-8'
            }
            
            print(f"   🔗 调用toolServer: {tool_name}")
            
            # 发送请求
            response = requests.post(
                execute_url,
                json=payload,
                headers=headers,
                timeout=100000
            )
            response.raise_for_status()
            
            # 解析响应
            tool_server_response = response.json()
            
            if tool_server_response.get("success"):
                output_data = tool_server_response.get("data", {})
                return {
                    "status": "success",
                    "output": json.dumps(output_data, indent=2, ensure_ascii=False),
                    "error_information": ""
                }
            else:
                error_msg = tool_server_response.get("error", "工具服务器返回未知错误")
                return {
                    "status": "error",
                    "output": "",
                    "error_information": error_msg
                }
        
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error_information": f"调用toolServer失败: {str(e)}"
            }
    
    def _execute_sub_agent(
        self,
        agent_name: str,
        agent_config: Dict,
        arguments: Dict,
        task_id: str
    ) -> Dict:
        """执行子Agent调用"""
        try:
            # 导入Agent执行器（避免循环导入）
            from core.agent_executor import AgentExecutor
            
            # 获取任务输入
            task_input = arguments.get("task_input", "")
            
            # 创建子Agent执行器
            sub_agent = AgentExecutor(
                agent_name=agent_name,
                agent_config=agent_config,
                config_loader=self.config_loader,
                hierarchy_manager=self.hierarchy_manager
            )
            
            # 执行子Agent
            result = sub_agent.run(task_id, task_input)
            
            return result
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 子Agent执行失败: {e}")
            print(f"详细错误:\n{error_detail}")
            return {
                "status": "error",
                "output": "",
                "error_information": f"子Agent执行失败: {str(e)}\n{error_detail}"
            }


if __name__ == "__main__":
    from utils.config_loader import ConfigLoader
    from core.hierarchy_manager import get_hierarchy_manager
    
    # 测试工具执行器
    config_loader = ConfigLoader("infiHelper")
    hierarchy_manager = get_hierarchy_manager("test_task")
    
    executor = ToolExecutor(config_loader, hierarchy_manager)
    print(f"✅ 工具执行器初始化成功")
    print(f"   ToolServer URL: {executor.tools_server_url}")
    
    # 测试final_output
    result = executor.execute("final_output", {
        "task_id": "test",
        "status": "success",
        "output": "测试完成"
    }, "test_task")
    
    print(f"✅ final_output测试: {result}")
