#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision分析工具 - 图片内容分析（只做转码）
"""

from pathlib import Path
from typing import Dict, Any

from .file_tools import BaseTool, get_abs_path


class VisionTool(BaseTool):
    """图片Vision分析工具 - 将图片编码为base64"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Vision分析（转码图片）
        
        Parameters:
            image_path (str): 图片文件相对路径（相对于任务目录）
            question (str, optional): 要问的问题（用于描述）
            model (str, optional): 模型名称（可选，目前不使用）
        
        Returns:
            status: "success" 或 "error"
            output: 描述文本
            error: 错误信息（如有）
            multimedia_content: 多媒体内容（包含图片编码）
        """
        try:
            # 获取参数
            image_path = parameters.get("image_path")
            question = parameters.get("question", "请描述这张图片的内容")
            
            if not image_path:
                return {
                    "status": "error",
                    "output": "",
                    "error": "缺少必需参数: image_path"
                }
            
            # 转换为绝对路径
            abs_image_path = get_abs_path(task_id, image_path)
            
            if not abs_image_path.exists():
                return {
                    "status": "error",
                    "output": "",
                    "error": f"图片文件不存在: {image_path}"
                }
            
            try:
                # 读取图片并编码
                with open(abs_image_path, "rb") as image_file:
                    import base64
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
                # 判断图片格式
                suffix = abs_image_path.suffix.lower()
                mime_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_type_map.get(suffix, 'image/jpeg')
                
                # 描述
                description = question if question != "请描述这张图片的内容" else "图片内容"
                
                return {
                    "status": "success",
                    "output": description,
                    "error": "",
                    "multimedia_content": {
                        "type": "image",
                        "data": image_data,
                        "mime_type": mime_type,
                        "description": description
                    }
                }
                
            except FileNotFoundError as e:
                return {
                    "status": "error",
                    "output": "",
                    "error": f"图片文件不存在: {str(e)}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "output": "",
                    "error": f"图片转码失败: {str(e)}"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"执行失败: {str(e)}"
            }

