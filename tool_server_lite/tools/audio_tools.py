#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio分析工具 - 音频内容分析（只做转录）
"""

from pathlib import Path
from typing import Dict, Any

from .file_tools import BaseTool, get_abs_path


class AudioTool(BaseTool):
    """音频分析工具 - 转录音频为文本"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Audio分析（转录音频）
        
        Parameters:
            audio_path (str): 音频文件相对路径（相对于任务目录）
            question (str, optional): 要问的问题（用于描述）
            model (str, optional): 模型名称（可选）
        
        Returns:
            status: "success" 或 "error"
            output: 转录文本
            error: 错误信息（如有）
            multimedia_content: 多媒体内容（包含转录文本）
        """
        try:
            # 获取参数
            audio_path = parameters.get("audio_path")
            question = parameters.get("question", "请描述这段音频的内容")
            
            if not audio_path:
                return {
                    "status": "error",
                    "output": "",
                    "error": "缺少必需参数: audio_path"
                }
            
            # 转换为绝对路径
            abs_audio_path = get_abs_path(task_id, audio_path)
            
            if not abs_audio_path.exists():
                return {
                    "status": "error",
                    "output": "",
                    "error": f"音频文件不存在: {audio_path}"
                }
            
            try:
                # 转录音频
                import yaml
                import os
                from pathlib import Path
                
                # 读取配置
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = Path(parent_dir).parent / "config" / "run_env_config" / "llm_config.yaml"
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                api_key = config.get("api_key")
                api_base = config.get("base_url", "")
                
                # 使用 openai Audio API 转录
                try:
                    import openai
                    
                    with open(abs_audio_path, "rb") as f:
                        transcript = openai.Audio.transcribe(
                            "whisper-1",
                            f,
                            api_key=api_key,
                            api_base=api_base if api_base else None
                        )
                        transcript_text = transcript['text']
                    
                    # 描述（直接返回转录文本）
                    description = f"{question}\n\n【音频转录内容】\n{transcript_text}"
                    
                    return {
                        "status": "success",
                        "output": description,
                        "error": ""
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "output": "",
                        "error": f"音频转录失败: {str(e)}"
                    }
                
            except FileNotFoundError as e:
                return {
                    "status": "error",
                    "output": "",
                    "error": f"音频文件不存在: {str(e)}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "output": "",
                    "error": f"音频处理失败: {str(e)}"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"执行失败: {str(e)}"
            }

