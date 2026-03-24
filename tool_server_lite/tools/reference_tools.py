#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参考文献管理工具 - 用于管理 reference.bib 文件
"""

import re
from pathlib import Path
from typing import Dict, Any, List
from .file_tools import BaseTool, get_abs_path


class ReferenceListTool(BaseTool):
    """列出所有参考文献（直接显示原文）"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出 reference.bib 中的所有参考文献（原文）
        
        Parameters:
            bib_path (str, optional): bib文件相对路径，默认 "reference.bib"
        
        Returns:
            status: "success" 或 "error"
            output: 文件原文内容
            error: 错误信息（如有）
        """
        try:
            bib_path = parameters.get("bib_path", "reference.bib")
            abs_bib_path = get_abs_path(task_id, bib_path)
            
            if not abs_bib_path.exists():
                return {
                    "status": "error",
                    "output": "",
                    "error": f"文件不存在: {bib_path}"
                }
            
            # 直接读取并返回文件内容
            with open(abs_bib_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return {
                    "status": "success",
                    "output": "(文件为空)",
                    "error": ""
                }
            
            return {
                "status": "success",
                "output": content,
                "error": ""
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"读取失败: {str(e)}"
            }


class ReferenceAddTool(BaseTool):
    """添加参考文献（追加模式，不修改原有内容）"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        向 reference.bib 添加参考文献（使用追加模式，不会修改原有内容）
        
        Parameters:
            entries (list): 参考文献字符串数组，每个元素是一条完整的bib条目
            bib_path (str, optional): bib文件相对路径，默认 "reference.bib"
        
        Returns:
            status: "success" 或 "error"
            output: 添加结果信息
            error: 错误信息（如有）
        
        注意：本工具使用追加模式，不会解析和重写原有内容，确保原始数据安全
        """
        try:
            entries = parameters.get("entries", [])
            bib_path = parameters.get("bib_path", "reference.bib")
            
            if not entries:
                return {
                    "status": "error",
                    "output": "",
                    "error": "缺少必需参数: entries"
                }
            
            if not isinstance(entries, list):
                entries = [entries]
            
            abs_bib_path = get_abs_path(task_id, bib_path)
            
            # 如果文件不存在，创建它
            if not abs_bib_path.exists():
                abs_bib_path.parent.mkdir(parents=True, exist_ok=True)
                needs_separator = False
                needs_newline = False
            else:
                # 检查文件是否为空，以及是否以换行符结尾
                file_size = abs_bib_path.stat().st_size
                if file_size == 0:
                    needs_separator = False
                    needs_newline = False
                else:
                    with open(abs_bib_path, 'rb') as f:
                        f.seek(-1, 2)  # 移到最后一个字符
                        last_char = f.read(1)
                        needs_separator = True
                        # 如果不是换行符，需要先加换行
                        needs_newline = (last_char != b'\n')
            
            # 使用追加模式打开文件
            with open(abs_bib_path, 'a', encoding='utf-8') as f:
                # 如果需要，先添加分隔
                if needs_separator:
                    if needs_newline:
                        f.write('\n')
                    f.write('\n')
                
                # 追加所有新条目
                added_count = 0
                for entry in entries:
                    entry = entry.strip()
                    if not entry:
                        continue
                    
                    f.write(entry)
                    f.write('\n\n')
                    added_count += 1
            
            if added_count == 0:
                return {
                    "status": "error",
                    "output": "",
                    "error": "没有有效的文献被添加"
                }
            
            return {
                "status": "success",
                "output": f"成功添加 {added_count} 条参考文献",
                "error": ""
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"添加失败: {str(e)}"
            }


class ReferenceDeleteTool(BaseTool):
    """删除参考文献"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 reference.bib 删除指定的参考文献
        
        Parameters:
            keys (str or list): 要删除的引用键（如 "sun2023blockchain"）或引用键列表
            bib_path (str, optional): bib文件相对路径，默认 "reference.bib"
        
        Returns:
            status: "success" 或 "error"
            output: 删除结果信息
            error: 错误信息（如有）
        """
        try:
            keys = parameters.get("keys", [])
            bib_path = parameters.get("bib_path", "reference.bib")
            
            if not keys:
                return {
                    "status": "error",
                    "output": "",
                    "error": "缺少必需参数: keys"
                }
            
            # 统一转为列表
            if isinstance(keys, str):
                keys = [keys]
            
            abs_bib_path = get_abs_path(task_id, bib_path)
            
            if not abs_bib_path.exists():
                return {
                    "status": "error",
                    "output": "",
                    "error": f"文件不存在: {bib_path}"
                }
            
            # 读取文件
            with open(abs_bib_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析所有条目
            entries = self._parse_bib_entries(content)
            
            # 过滤掉要删除的条目
            deleted_keys = []
            not_found_keys = []
            remaining_entries = []
            
            for entry in entries:
                if entry["key"] in keys:
                    deleted_keys.append(entry["key"])
                else:
                    remaining_entries.append(entry["content"])
            
            # 检查哪些key没找到
            for key in keys:
                if key not in deleted_keys:
                    not_found_keys.append(key)
            
            if not deleted_keys:
                return {
                    "status": "error",
                    "output": "",
                    "error": f"未找到要删除的文献: {', '.join(keys)}"
                }
            
            # 重新写入文件
            new_content = '\n\n'.join(remaining_entries)
            if new_content and not new_content.endswith('\n'):
                new_content += '\n'
            
            with open(abs_bib_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 生成结果信息
            result_parts = [f"成功删除 {len(deleted_keys)} 条参考文献: {', '.join(deleted_keys)}"]
            if not_found_keys:
                result_parts.append(f"未找到: {', '.join(not_found_keys)}")
            result_parts.append(f"剩余 {len(remaining_entries)} 条参考文献")
            
            return {
                "status": "success",
                "output": "\n".join(result_parts),
                "error": ""
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"删除失败: {str(e)}"
            }
    
    def _parse_bib_entries(self, content: str) -> List[Dict[str, str]]:
        """解析bib文件内容，提取所有条目（改进版，支持多种格式）"""
        if not content.strip():
            return []
        
        entries = []
        # 改进的正则表达式：支持多行和单行格式
        # 匹配 @type{key, 后面的任意内容直到 }
        pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,([^}]*)\}'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            entry_type = match.group(1)
            entry_key = match.group(2).strip()
            entry_content = match.group(0)
            
            entries.append({
                "type": entry_type,
                "key": entry_key,
                "content": entry_content
            })
        
        return entries


if __name__ == "__main__":
    """测试参考文献管理工具"""
    import sys
    from pathlib import Path
    
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    print("=" * 60)
    print("📚 测试参考文献管理工具")
    print("=" * 60)
    
    # 创建测试用的bib文件
    test_bib_content = """@article{sun2023blockchain,
  title={区块链技术, 供应链网络与数据共享: 基于演化博弈视角},
  author={孙国强 and 谢雨菲},
  journal={中国管理科学},
  volume={31},
  number={11},
  pages={155--166},
  year={2023}
}

@article{li2021evolutionary,
  title={我国战略性新兴产业间供应链企业协同创新演化博弈研究},
  author={李柏洲 and 王雪 and 苏屹 and 罗小芳},
  journal={中国管理科学},
  volume={29},
  number={1},
  pages={11--22},
  year={2021}
}
"""
    
    # 写入测试文件
    test_dir = project_root / "test_reference"
    test_dir.mkdir(exist_ok=True)
    test_bib_path = test_dir / "reference.bib"
    
    with open(test_bib_path, 'w', encoding='utf-8') as f:
        f.write(test_bib_content)
    
    print(f"测试文件已创建: {test_bib_path}\n")
    
    # 测试1: 列出参考文献
    print("=" * 60)
    print("测试1: 列出所有参考文献（原文）")
    print("=" * 60)
    
    list_tool = ReferenceListTool()
    result = list_tool.execute("test_reference", {"bib_path": "reference.bib"})
    print(f"状态: {result['status']}")
    print(f"输出:\n{result['output']}\n")
    
    # 测试2: 添加参考文献
    print("=" * 60)
    print("测试2: 添加新参考文献")
    print("=" * 60)
    
    new_entry = """@article{yang2025stability,
  title={多主体参与下食品安全社会共治演化博弈稳定性},
  author={杨松 and others},
  journal={食品安全质量检测学报},
  volume={16},
  number={4},
  pages={325--334},
  year={2025}
}"""
    
    add_tool = ReferenceAddTool()
    result = add_tool.execute("test_reference", {
        "bib_path": "reference.bib",
        "entries": [new_entry]
    })
    print(f"状态: {result['status']}")
    print(f"输出: {result['output']}\n")
    
    # 测试3: 再次列出（查看添加结果）
    print("=" * 60)
    print("测试3: 再次列出所有参考文献（应该有3条）")
    print("=" * 60)
    
    result = list_tool.execute("test_reference", {"bib_path": "reference.bib"})
    print(f"输出:\n{result['output']}\n")
    
    # 测试4: 测试追加模式（再次添加一条文献）
    print("=" * 60)
    print("测试4: 测试追加模式（添加第4条文献）")
    print("=" * 60)
    
    another_entry = """@article{wang2024test,
  title={测试追加模式的文献},
  author={王测试},
  journal={测试期刊},
  year={2024}
}"""
    
    result = add_tool.execute("test_reference", {
        "bib_path": "reference.bib",
        "entries": [another_entry]
    })
    print(f"状态: {result['status']}")
    print(f"输出: {result['output']}\n")
    
    # 测试4.5: 查看追加结果
    print("=" * 60)
    print("测试4.5: 查看追加结果（应该有4条）")
    print("=" * 60)
    
    result = list_tool.execute("test_reference", {"bib_path": "reference.bib"})
    print(f"输出:\n{result['output']}\n")
    
    # 测试5: 批量删除参考文献（测试数组形式）
    print("=" * 60)
    print("测试5: 批量删除参考文献 ['sun2023blockchain', 'yang2025stability']")
    print("=" * 60)
    
    delete_tool = ReferenceDeleteTool()
    result = delete_tool.execute("test_reference", {
        "bib_path": "reference.bib",
        "keys": ["sun2023blockchain", "yang2025stability"]
    })
    print(f"状态: {result['status']}")
    print(f"输出: {result['output']}\n")
    
    # 测试6: 最后列出（查看删除结果）
    print("=" * 60)
    print("测试6: 最后列出所有参考文献（应该剩2条：li2021evolutionary, wang2024test）")
    print("=" * 60)
    
    result = list_tool.execute("test_reference", {"bib_path": "reference.bib"})
    print(f"输出:\n{result['output']}\n")
    
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)

