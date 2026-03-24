#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv 搜索工具
"""

from pathlib import Path
from typing import Dict, Any
import re
from .file_tools import BaseTool, get_abs_path

# arXiv 导入
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False


class ArxivSearchTool(BaseTool):
    """arXiv 搜索工具"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索 arXiv 论文
        
        Parameters:
            query (str): 搜索关键词
            max_results (int, optional): 最大结果数，默认10
            sort_by (str, optional): 排序方式，默认 "relevance"
                - "relevance": 相关性
                - "lastUpdatedDate": 更新时间
                - "submittedDate": 提交时间
            sort_order (str, optional): 排序顺序，默认 "descending"
                - "descending": 降序
                - "ascending": 升序
            save_path (str, optional): 保存结果的相对路径（.md文件）
        """
        try:
            if not ARXIV_AVAILABLE:
                return {
                    "status": "error",
                    "output": "",
                    "error": "arxiv not installed. Run: pip install arxiv"
                }
            
            query = parameters.get("query")
            max_results = parameters.get("max_results", 10)
            sort_by_str = parameters.get("sort_by", "relevance")
            sort_order_str = parameters.get("sort_order", "descending")
            save_path = parameters.get("save_path")
            
            if not query:
                return {
                    "status": "error",
                    "output": "",
                    "error": "query is required"
                }
            
            # 转换排序参数
            sort_by_map = {
                "relevance": arxiv.SortCriterion.Relevance,
                "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
                "submittedDate": arxiv.SortCriterion.SubmittedDate
            }
            sort_order_map = {
                "descending": arxiv.SortOrder.Descending,
                "ascending": arxiv.SortOrder.Ascending
            }
            
            sort_by = sort_by_map.get(sort_by_str, arxiv.SortCriterion.Relevance)
            sort_order = sort_order_map.get(sort_order_str, arxiv.SortOrder.Descending)
            
            # 搜索 arXiv
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            results = list(client.results(search))
            
            # 格式化为 Markdown
            results_md = []
            results_md.append(f"# arXiv Search Results: {query}\n")
            results_md.append(f"**Total**: {len(results)} papers\n")
            results_md.append(f"**Sort By**: {sort_by_str}\n")
            results_md.append(f"**Sort Order**: {sort_order_str}\n")
            
            for i, paper in enumerate(results, 1):
                results_md.append(f"\n---\n")
                results_md.append(f"## {i}. {paper.title}\n")
                results_md.append(f"**Authors**: {', '.join([author.name for author in paper.authors])}\n")
                results_md.append(f"**Published**: {paper.published.strftime('%Y-%m-%d')}\n")
                results_md.append(f"**Updated**: {paper.updated.strftime('%Y-%m-%d')}\n")
                results_md.append(f"**arXiv ID**: {paper.entry_id.split('/')[-1]}\n")
                results_md.append(f"**PDF URL**: {paper.pdf_url}\n")
                
                # 分类
                if paper.categories:
                    results_md.append(f"**Categories**: {', '.join(paper.categories)}\n")
                
                # 摘要
                results_md.append(f"\n**Abstract**:\n")
                # 清理摘要中的多余空白
                abstract = re.sub(r'\s+', ' ', paper.summary).strip()
                results_md.append(f"{abstract}\n")
            
            results_text = '\n'.join(results_md)
            
            # 保存到文件
            if save_path:
                # 生成包含搜索参数的文件名
                save_path_obj = Path(save_path)
                safe_query = re.sub(r'[^\w\s-]', '', query).strip()
                safe_query = re.sub(r'[-\s]+', '_', safe_query)[:50]
                
                new_filename = f"{save_path_obj.stem}_{safe_query}_n{max_results}{save_path_obj.suffix}"
                final_save_path = str(save_path_obj.parent / new_filename)
                
                abs_save_path = get_abs_path(task_id, final_save_path)
                abs_save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(abs_save_path, 'w', encoding='utf-8') as f:
                    f.write(results_text)
                
                output = f"结果保存在 {final_save_path}"
            else:
                output = results_text
            
            return {
                "status": "success",
                "output": output,
                "error": ""
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }

