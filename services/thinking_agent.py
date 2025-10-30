#!/usr/bin/env python3
from utils.windows_compat import safe_print
# -*- coding: utf-8 -*-
"""
Thinking Agent - 任务进展分析服务
"""

from typing import Dict, List
from services.llm_client import SimpleLLMClient, ChatMessage


class ThinkingAgent:
    """思考Agent - 用于分析任务进展"""
    
    def __init__(self):
        """初始化Thinking Agent"""
        # 使用简化的LLM客户端
        self.llm_client = SimpleLLMClient()
        
        # Thinking Agent的系统提示词
        self.system_prompt = """你是一个任务进展分析专家。你的职责是：

1. 分析当前任务的整体目标
2. 总结已完成的工作
3. 识别正在进行的任务
4. 列出剩余待完成的任务
5. 评估当前进度状态

请提供清晰、结构化的分析，包括：
- 任务概述
- 已完成项目
- 当前状态
- 剩余任务
- 下一步行动
- 风险评估（如有）

**重要**：
- 如果发现Agent陷入死循环，用严厉语气警告并明确下一步任务
- 如果发现Agent执行了职责外的工作，立即警告停止
- 进度必须精准，例如coding任务要明确已实现多少功能、完成多少文件
- 使用中文输出
"""
    
    def analyze_first_thinking(self, task_description: str, agent_system_prompt: str, 
                               available_tools: List[str]) -> str:
        """
        首次思考 - 初始规划
        
        Args:
            task_description: 任务描述
            agent_system_prompt: Agent的系统提示词
            available_tools: 可用工具列表
            
        Returns:
            初始规划结果
        """
        try:
            # 构建分析请求
            analysis_request = f"""当前任务：{task_description}

Agent的系统提示词和工作流程：
{agent_system_prompt}

可用工具：{', '.join(available_tools)}

这是任务的初始阶段，请进行初始规划：
1. 理解任务目标
2. 规划执行步骤
3. 确定需要使用的工具
4. 预判可能的风险

请提供简洁但全面的初始规划。"""
            
            history = [ChatMessage(role="user", content=analysis_request)]
            
            # 使用第一个可用模型，不需要工具
            response = self.llm_client.chat(
                history=history,
                model=self.llm_client.models[0],
                system_prompt=self.system_prompt,
                tool_list=[],  # Thinking不使用工具
                tool_choice="auto"
            )
            
            if response.status == "success":
                return f"[🤖 初始规划]\n\n{response.output}"
            else:
                return f"[初始规划失败: {response.error_information}]"
        
        except Exception as e:
            safe_print(f"⚠️ 首次thinking失败: {e}")
            return f"[初始规划失败: {str(e)}]"
    
    def analyze_progress(self, task_description: str, agent_system_prompt: str,
                        tool_call_counter: int) -> str:
        """
        进度分析 - 周期性分析
        
        Args:
            task_description: 任务描述
            agent_system_prompt: Agent的完整系统提示词（包含<历史动作>）
            tool_call_counter: 工具调用计数
            
        Returns:
            进度分析结果
        """
        try:
            # 构建分析请求（agent_system_prompt已包含完整的<历史动作>）
            analysis_request = f"""当前任务：{task_description}

Agent的完整上下文（包含系统角色、历史动作等）：
{agent_system_prompt}

已执行的工具调用数：{tool_call_counter}

基于以上完整上下文信息，请分析：
1. 任务进展到什么程度？
2. 已完成哪些任务？
3. 还需要完成什么？
4. 当前执行状态如何？
5. Agent是否正确遵循其系统提示词？
6. 下一步应该做什么？（只建议当前Agent的下一步！）
7. 是否有遗漏的步骤或注意事项？
8. 列出Agent未来可能使用的所有文件路径和描述

**关键**：
- 进度必须精准！
- 如果发现死循环，严厉警告
- 如果发现越界操作，立即指出"""
            
            history = [ChatMessage(role="user", content=analysis_request)]
            
            response = self.llm_client.chat(
                history=history,
                model=self.llm_client.models[0],
                system_prompt=self.system_prompt,
                tool_list=[],
                tool_choice="auto"
            )
            
            if response.status == "success":
                return f"[🤖 进度分析 - 第{tool_call_counter}轮]\n\n{response.output}"
            else:
                return f"[进度分析失败: {response.error_information}]"
        
        except Exception as e:
            safe_print(f"⚠️ 进度分析失败: {e}")
            return f"[进度分析失败: {str(e)}]"


if __name__ == "__main__":
    # 测试Thinking Agent
    thinking_agent = ThinkingAgent()
    
    result = thinking_agent.analyze_first_thinking(
        task_description="生成斐波那契数列文件",
        agent_system_prompt="你是一个编程助手",
        available_tools=["file_write", "execute_code"]
    )
    
    safe_print("="*80)
    safe_print(result)
    safe_print("="*80)

