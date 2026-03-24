#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows兼容性工具
确保emoji和中文字符能在Windows控制台正常显示
"""
import sys


def setup_console_encoding():
    """设置控制台为UTF-8编码（Windows专用），并启用实时输出"""
    if sys.platform == 'win32':
        try:
            import io
            # 强制行缓冲和立即写入，避免输出延迟
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, write_through=True)
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True, write_through=True)
        except Exception:
            # 如果设置失败，不影响程序运行
            pass


def safe_print(*args, **kwargs):
    """
    安全的print函数，自动flush避免Windows缓冲区问题
    """
    print(*args, **kwargs)
    if sys.platform == 'win32':
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass


# 自动设置（导入时执行）
setup_console_encoding()

