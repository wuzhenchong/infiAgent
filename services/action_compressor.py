#!/usr/bin/env python3
from utils.windows_compat import safe_print
# -*- coding: utf-8 -*-
"""
历史动作压缩服务
策略：总结历史XML + 保留最新action + 压缩最新action的大字段
"""

import json
from typing import List, Dict

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


class ActionCompressor:
    """历史动作压缩器"""
    
    def __init__(self, llm_client):
        """
        初始化
        
        Args:
            llm_client: LLM客户端实例（用于总结）
        """
        self.llm_client = llm_client
        
        # 初始化tiktoken
        if HAS_TIKTOKEN:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """统计token数"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + other_chars / 4)
    
    def compress_if_needed(
        self,
        action_history: List[Dict],
        max_context_window: int,
        save_callback=None  # 添加保存回调，确保压缩后立即保存
    ) -> List[Dict]:
        """
        检查并压缩历史动作
        
        策略：
        1. 保留最新1条action（完整或压缩大字段）
        2. 之前的所有action总结为一个summary_action
        
        Args:
            action_history: 动作历史
            max_context_window: 最大窗口大小
            
        Returns:
            压缩后的action_history
        """
        if not action_history:
            return []
        
        # 如果只有一条
        if len(action_history) == 1:
            # 检查是否需要压缩字段
            return [self._compress_action_fields(action_history[0], max_context_window // 2)]
        
        # 分离最新和历史
        recent_action = action_history[-1]
        historical_actions = action_history[:-1]
        
        # 计算整体token数
        total_text = self._actions_to_xml(action_history)
        total_tokens = self.count_tokens(total_text)
        
        # 如果不超限，不压缩
        if total_tokens <= max_context_window - 20000:
            return action_history
        
        safe_print(f"🔄 历史动作需要压缩: {total_tokens} tokens > {max_context_window - 20000}")
        
        # 压缩策略：
        # 1. 历史 → 总结为5k tokens
        # 2. 最新 → 压缩为max_window的50%
        
        summary_action = self._summarize_historical_xml(
            self._actions_to_xml(historical_actions),
            target_tokens=5000  # 历史总结固定5k tokens
        )
        
        # 压缩最新action的大字段（50% of max_window）
        compressed_recent = self._compress_action_fields(
            recent_action,
            int(max_context_window * 0.5)  # 80000 * 0.5 = 40000 tokens
        )
        
        result = [summary_action, compressed_recent]
        
        # 验证压缩效果
        result_xml = self._actions_to_xml(result)
        result_tokens = self.count_tokens(result_xml)
        safe_print(f"✅ 压缩完成: {total_tokens} tokens → {result_tokens} tokens (压缩比: {result_tokens/total_tokens*100:.1f}%)")
        
        return result
    
    def _actions_to_xml(self, actions: List[Dict]) -> str:
        """将actions转换为XML格式文本"""
        xml_parts = []
        for action in actions:
            tool_name = action.get("tool_name", "")
            arguments = action.get("arguments", {})
            result = action.get("result", {})
            
            action_xml = f"<action>\n  <tool_name>{tool_name}</tool_name>\n"
            
            # 参数
            for k, v in arguments.items():
                v_str = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                action_xml += f"  <tool_use:{k}>{v_str}</tool_use:{k}>\n"
            
            # 结果
            result_json = json.dumps(result, ensure_ascii=False, indent=2)
            action_xml += f"  <result>\n{result_json}\n  </result>\n</action>"
            
            xml_parts.append(action_xml)
        
        return "\n\n".join(xml_parts)
    
    def _summarize_historical_xml(self, xml_text: str, target_tokens: int = 5000) -> Dict:
        """
        总结历史XML内容为一个summary action
        
        Args:
            xml_text: 历史actions的XML文本
            
        Returns:
            一个summary action
        """
        try:
            from services.llm_client import ChatMessage
            
            prompt = f"""请总结以下历史动作的关键信息（严格不超过{target_tokens} tokens）：

{xml_text}

要求：
1. 说明执行了哪些工具
2. 关键的输出和结果
3. 重要的文件路径
4. 目标长度：{target_tokens} tokens
5. 极度简洁但保留核心信息

请用中文总结："""
            
            history = [ChatMessage(role="user", content=prompt)]
            
            response = self.llm_client.chat(
                history=history,
                model=self.llm_client.models[0],
                system_prompt=f"你是内容总结助手。目标：将内容压缩到{target_tokens} tokens以内。",
                tool_list=[],
                tool_choice="auto"
            )
            
            summary = response.output if response.status == "success" else "[总结失败]"
            
            return {
                "tool_name": "_historical_summary",
                "arguments": {},
                "result": {
                    "status": "success",
                    "output": summary,
                    "_is_summary": True
                }
            }
        
        except Exception as e:
            safe_print(f"⚠️ 总结失败: {e}")
            return {
                "tool_name": "_historical_summary",
                "arguments": {},
                "result": {"status": "success", "output": "[历史动作已省略]", "_is_summary": True}
            }
    
    def _compress_action_fields(self, action: Dict, max_field_tokens: int) -> Dict:
        """
        压缩action中的大字段（arguments和result）
        
        Args:
            action: 原始action
            max_field_tokens: 单个字段的最大token数（通常是max_context_window/2）
            
        Returns:
            压缩后的action
        """
        compressed_action = action.copy()
        
        # 压缩arguments中的大字段
        if "arguments" in compressed_action:
            compressed_args = {}
            for k, v in compressed_action["arguments"].items():
                v_str = str(v)
                v_tokens = self.count_tokens(v_str)
                
                if v_tokens > max_field_tokens:
                    safe_print(f"   🤖 LLM压缩arguments.{k}: {v_tokens} tokens → {max_field_tokens} tokens")
                    compressed_v = self._llm_compress_field(v_str, max_field_tokens, action.get("tool_name", "unknown"))
                    compressed_args[k] = compressed_v
                else:
                    compressed_args[k] = v
            compressed_action["arguments"] = compressed_args
        
        # 压缩result.output
        if "result" in compressed_action and "output" in compressed_action["result"]:
            output = compressed_action["result"]["output"]
            output_tokens = self.count_tokens(output)
            
            if output_tokens > max_field_tokens:
                safe_print(f"   🤖 LLM压缩result.output: {output_tokens} tokens → {max_field_tokens} tokens")
                compressed_output = self._llm_compress_field(output, max_field_tokens, action.get("tool_name", "unknown"))
                compressed_action["result"]["output"] = compressed_output
                compressed_action["result"]["_compressed"] = True
                compressed_action["result"]["_original_tokens"] = output_tokens
        
        return compressed_action
    
    def _llm_compress_field(self, text: str, target_tokens: int, tool_name: str) -> str:
        """
        使用LLM智能压缩单个字段
        
        Args:
            text: 原始文本
            target_tokens: 目标token数
            tool_name: 工具名称（用于优化提示词）
            
        Returns:
            压缩后的文本
        """
        try:
            from services.llm_client import ChatMessage
            
            # 根据工具类型定制提示词
            if "parse" in tool_name.lower() or "read" in tool_name.lower():
                content_type = "文档内容"
                focus = "保留文档的关键章节、核心论点、重要数据和结论"
            elif "execute" in tool_name.lower() or "run" in tool_name.lower():
                content_type = "代码执行结果"
                focus = "保留关键输出、错误信息、返回值和执行状态"
            elif "search" in tool_name.lower():
                content_type = "搜索结果"
                focus = "保留最相关的搜索结果和关键匹配信息"
            else:
                content_type = "内容"
                focus = "保留最重要的核心信息"
            
            prompt = f"""请智能压缩以下{content_type}到约{target_tokens} tokens：

{text}

压缩要求：
1. 目标长度：{target_tokens} tokens
2. {focus}
3. 保持信息的连贯性和可读性
4. 使用总结和提炼，而非简单截断
5. 如果有结构化内容（表格、列表），保留关键部分

请直接输出压缩后的内容（不要额外说明）："""
            
            history = [ChatMessage(role="user", content=prompt)]
            
            response = self.llm_client.chat(
                history=history,
                model=self.llm_client.models[0],
                system_prompt=f"你是智能内容压缩助手。目标：将{content_type}压缩到{target_tokens} tokens，同时保留核心信息。",
                tool_list=[],
                tool_choice="auto"
            )
            
            compressed = response.output if response.status == "success" else text[:1000] + "\n[压缩失败，仅保留前1000字符]"
            
            # 验证压缩效果
            actual_tokens = self.count_tokens(compressed)
            safe_print(f"      压缩效果: {actual_tokens}/{target_tokens} tokens ({actual_tokens/target_tokens*100:.1f}%)")
            
            return compressed
            
        except Exception as e:
            safe_print(f"⚠️ LLM压缩失败，使用fallback: {e}")
            # fallback：首尾保留
            return self._fallback_compress(text, target_tokens)
    
    def _fallback_compress(self, text: str, max_tokens: int) -> str:
        """
        备用压缩方案（首尾保留法）- 当LLM压缩失败时使用
        """
        if self.encoding:
            tokens = self.encoding.encode(text)
            head_count = int(max_tokens * 0.1)
            tail_count = int(max_tokens * 0.1)
            head_tokens = tokens[:head_count]
            tail_tokens = tokens[-tail_count:]
            head_text = self.encoding.decode(head_tokens)
            tail_text = self.encoding.decode(tail_tokens)
            omitted = len(tokens) - head_count - tail_count
            return f"{head_text}\n\n[中间省略约{omitted}个tokens]\n\n{tail_text}"
        else:
            # 简单字符截取
            chars = int(max_tokens * 2)
            head = chars // 2
            tail = chars // 2
            return f"{text[:head]}\n\n[中间省略]\n\n{text[-tail:]}"


if __name__ == "__main__":
    safe_print("✅ ActionCompressor模块加载成功")
    safe_print("\n压缩策略：")
    safe_print("1. 历史actions → LLM总结为5k tokens")
    safe_print("2. 最新action → 保留结构，LLM智能压缩大字段到50% max_window")
    safe_print("3. 备用方案 → 首尾保留法（当LLM失败时）")

