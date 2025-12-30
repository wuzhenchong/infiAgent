#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理工具
"""

from pathlib import Path
from typing import Dict, Any, List
from .file_tools import BaseTool, get_abs_path


class ParseDocumentTool(BaseTool):
    """PDF/文档解析工具"""
    
    def execute(self, task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析PDF或其他文档
        
        Parameters:
            path (str): 文档相对路径
            save_path (str, optional): 保存解析结果的相对路径
                                      图片会自动保存到 {save_path}_images/ 目录
                                      (仅对PDF有效，Word文档只提取文字和表格)
        """
        try:
            path = parameters.get("path")
            save_path = parameters.get("save_path")
            
            abs_path = get_abs_path(task_id, path)
            
            if not abs_path.exists():
                return {
                    "status": "error",
                    "output": "",
                    "error": f"Document not found: {path}"
                }
            
            # 自动生成图片目录路径（基于save_path）
            if save_path:
                # 从 save_path 生成 images_dir
                # 例如: "result.txt" -> "result_images"
                save_path_obj = Path(save_path)
                images_dir = str(save_path_obj.parent / (save_path_obj.stem + "_images"))
                extract_images = True
            else:
                # 如果没有 save_path，使用默认值
                images_dir = "extracted_images"
                extract_images = True
            
            # 判断文件类型
            suffix = abs_path.suffix.lower()
            
            if suffix == '.pdf':
                content = self._parse_pdf(abs_path, task_id, extract_images, images_dir)
            elif suffix in ['.docx', '.doc']:
                content = self._parse_word(abs_path, task_id, extract_images, images_dir)
            elif suffix in ['.txt', '.md']:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                return {
                    "status": "error",
                    "output": "",
                    "error": f"Unsupported document type: {suffix}"
                }
            
            # 保存解析结果
            if save_path:
                abs_save_path = get_abs_path(task_id, save_path)
                abs_save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(abs_save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                output = f"结果保存在 {save_path}"
            else:
                output = content
            
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
    
    def _parse_pdf(self, pdf_path: Path, task_id: str, extract_images: bool, images_dir: str) -> str:
        """解析PDF文件 - 使用 pdfplumber（质量更高）"""
        try:
            import pdfplumber
            from PIL import Image
            
            text_content = []
            image_counter = 0
            
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文本
                    text = page.extract_text() or ""
                    
                    # 提取表格（转为Markdown格式）
                    tables = page.extract_tables()
                    
                    page_content = f"--- Page {page_num}/{num_pages} ---\n{text}\n"
                    
                    # 如果有表格，添加表格内容（Markdown格式）
                    if tables:
                        page_content += f"\n[Tables found: {len(tables)}]\n"
                        for table_idx, table in enumerate(tables, 1):
                            page_content += f"\n--- Table {table_idx} ---\n"
                            page_content += self._table_to_markdown(table)
                    
                    # 提取图片
                    if extract_images and hasattr(page, 'images'):
                        images = page.images
                        if images:
                            page_content += f"\n[Images found: {len(images)}]\n"
                            for img_idx, img in enumerate(images, 1):
                                image_counter += 1
                                img_filename = f"pdf_page{page_num}_img{img_idx}.png"
                                img_path = self._save_pdf_image(
                                    page, img, task_id, images_dir, img_filename
                                )
                                if img_path:
                                    page_content += f"\n[Image {img_idx}]: {img_path}\n"
                    
                    text_content.append(page_content)
            
            result = '\n'.join(text_content)
            if image_counter > 0:
                result = f"[提取了 {image_counter} 张图片到 {images_dir}/ 目录]\n\n" + result
            
            return result
            
        except ImportError as e:
            if 'pdfplumber' in str(e):
                raise Exception("pdfplumber not installed. Run: pip install pdfplumber")
            elif 'PIL' in str(e):
                raise Exception("Pillow not installed. Run: pip install Pillow")
            else:
                raise e
        except Exception as e:
            raise Exception(f"PDF parsing error: {str(e)}")
    
    def _parse_word(self, doc_path: Path, task_id: str, extract_images: bool, images_dir: str) -> str:
        """解析Word文档 - 只提取文字和表格，不提取图片（避免提取过多小图标）"""
        try:
            import docx
            from docx.oxml.table import CT_Tbl
            from docx.oxml.text.paragraph import CT_P
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            
            doc = docx.Document(doc_path)
            content_parts = []
            table_counter = 0
            
            # 遍历文档的所有元素（保持顺序）
            for element in doc.element.body:
                # 处理段落
                if isinstance(element, CT_P):
                    para = Paragraph(element, doc)
                    para_text = para.text.strip()
                    
                    # 只添加段落文本，忽略图片
                    if para_text:
                        content_parts.append(para_text)
                
                # 处理表格
                elif isinstance(element, CT_Tbl):
                    table = Table(element, doc)
                    table_counter += 1
                    content_parts.append(f"\n--- Table {table_counter} ---\n")
                    
                    # 提取表格数据
                    table_data = []
                    for row in table.rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(row_data)
                    
                    # 转为Markdown格式
                    content_parts.append(self._table_to_markdown(table_data))
            
            result = '\n'.join(content_parts)
            
            # 添加统计信息
            if table_counter > 0:
                result = f"[提取了 {table_counter} 个表格]\n\n" + result
            
            return result
            
        except ImportError:
            raise Exception("python-docx not installed. Run: pip install python-docx")
        except Exception as e:
            raise Exception(f"Word document parsing error: {str(e)}")
    
    def _table_to_markdown(self, table_data: List[List[str]]) -> str:
        """将表格数据转换为Markdown格式"""
        if not table_data or len(table_data) == 0:
            return ""
        
        markdown_lines = []
        
        # 处理表头（第一行）
        header = table_data[0]
        markdown_lines.append("| " + " | ".join([str(cell or "") for cell in header]) + " |")
        
        # 添加分隔线
        markdown_lines.append("| " + " | ".join(["---" for _ in header]) + " |")
        
        # 处理数据行
        for row in table_data[1:]:
            # 确保行的长度与表头一致
            padded_row = row + [""] * (len(header) - len(row)) if len(row) < len(header) else row[:len(header)]
            markdown_lines.append("| " + " | ".join([str(cell or "") for cell in padded_row]) + " |")
        
        return "\n".join(markdown_lines) + "\n"
    
    def _save_pdf_image(self, page, img_info: Dict, task_id: str, images_dir: str, filename: str) -> str:
        """保存PDF中的图片 - 使用PyMuPDF提取"""
        try:
            # 创建图片保存目录
            abs_images_dir = get_abs_path(task_id, images_dir)
            abs_images_dir.mkdir(parents=True, exist_ok=True)
            
            # pdfplumber本身不直接支持提取图片二进制数据
            # 这里使用PyMuPDF (fitz) 来提取
            try:
                import fitz  # PyMuPDF - 可选依赖，用于提取PDF图片
                from PIL import Image
                
                # 获取PDF路径和页码
                pdf_path = page.pdf.path
                page_num = page.page_number - 1  # PyMuPDF使用0索引
                
                # 打开PDF文档
                doc = fitz.open(pdf_path)
                fitz_page = doc[page_num]
                
                # 获取页面中的图片
                image_list = fitz_page.get_images()
                
                if not image_list:
                    return None
                
                # 提取第一张图片（简化处理）
                # 更复杂的实现需要匹配pdfplumber的img_info坐标
                xref = image_list[0][0]  # 获取图片引用
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # 保存图片
                img_path = abs_images_dir / filename.replace('.png', f'.{image_ext}')
                with open(img_path, 'wb') as f:
                    f.write(image_bytes)
                
                doc.close()
                
                # 返回相对路径
                return f"{images_dir}/{img_path.name}"
                
            except ImportError:
                # 如果PyMuPDF未安装，返回占位符信息
                return f"{images_dir}/{filename} (需安装PyMuPDF: pip install PyMuPDF)"
            except Exception as e:
                # 如果提取失败，返回None
                return None
                
        except Exception as e:
            return None
    


if __name__ == "__main__":
    """测试文档解析工具"""
    import sys
    import os
    
    # 添加项目根目录到路径，这样可以正确导入模块
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # 现在可以正确导入
    os.chdir(str(project_root))
    
    # 测试文件路径 - 测试PDF文档解析
    test_doc_path = project_root / "test_doc" / "1.pdf"
    
    print("=" * 60)
    print("📄 测试PDF文档解析工具（文字+表格+图片）")
    print("=" * 60)
    print(f"测试文件: {test_doc_path}")
    print(f"文件存在: {test_doc_path.exists()}")
    print()
    
    if not test_doc_path.exists():
        print("❌ 测试文件不存在!")
        sys.exit(1)
    
    # 创建工具实例
    tool = ParseDocumentTool()
    
    # 设置保存路径（同目录下）
    save_path = "1_parsed.txt"
    # 图片会自动保存到 1_parsed_images/ 目录
    
    # 执行解析
    print("🔄 开始解析PDF文档...")
    print(f"   - 保存路径: {save_path}")
    print(f"   - 图片目录: {Path(save_path).stem}_images/ (自动生成)")
    print()
    
    try:
        # 使用相对路径（相对于test_doc目录）
        result = tool.execute(
            task_id="test_doc",  # 使用test_doc作为task_id
            parameters={
                "path": "1.pdf",
                "save_path": save_path
            }
        )
        
        print("=" * 60)
        print("📊 解析结果")
        print("=" * 60)
        print(f"状态: {result['status']}")
        print()
        
        if result['status'] == 'success':
            print("✅ 解析成功!")
            print(f"\n{result['output']}")
            
            # 显示保存的文件信息
            abs_save_path = get_abs_path("test_doc", save_path)
            if abs_save_path.exists():
                file_size = abs_save_path.stat().st_size
                print(f"\n📁 输出文件信息:")
                print(f"   - 路径: {abs_save_path}")
                print(f"   - 大小: {file_size:,} 字节")
                
                # 显示前500个字符
                with open(abs_save_path, 'r', encoding='utf-8') as f:
                    content_preview = f.read(500)
                print(f"\n📝 内容预览 (前500字符):")
                print("-" * 60)
                print(content_preview)
                if file_size > 500:
                    print("...")
                print("-" * 60)
            
            # 检查图片目录
            images_dir = Path(save_path).stem + "_images"
            abs_images_dir = get_abs_path("test_doc", images_dir)
            if abs_images_dir.exists():
                image_files = list(abs_images_dir.glob("*"))
                if image_files:
                    print(f"\n🖼️  提取的图片:")
                    for img_file in image_files:
                        img_size = img_file.stat().st_size
                        print(f"   - {img_file.name} ({img_size:,} 字节)")
                else:
                    print(f"\n📂 图片目录已创建，但没有提取到图片")
        else:
            print(f"❌ 解析失败!")
            print(f"错误: {result['error']}")
    
    except Exception as e:
        print(f"❌ 测试过程中出错:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

