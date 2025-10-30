#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIL API 测试脚本
测试 confirm 和 cancel 功能
"""

import requests
import threading
import time
import sys
from pathlib import Path

# 配置
SERVER_URL = "http://127.0.0.1:8001"
TEST_TASK_ID = "/tmp/test_hil"

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get(f"{SERVER_URL}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False

def call_hil_async(hil_id, instruction):
    """
    异步调用 human_in_loop 工具
    这个函数会阻塞直到 HIL 任务完成或取消
    """
    print(f"\n[Thread] 开始调用 HIL 工具: {hil_id}")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/tool/execute",
            json={
                "task_id": TEST_TASK_ID,
                "tool_name": "human_in_loop",
                "params": {
                    "hil_id": hil_id,
                    "instruction": instruction,
                    "timeout": 30  # 30秒超时
                }
            },
            timeout=35  # 请求超时略大于工具超时
        )
        
        elapsed = time.time() - start_time
        result = response.json()
        
        print(f"\n[Thread] HIL 工具返回 (耗时: {elapsed:.2f}s):")
        print(f"  状态: {result.get('success')}")
        if result.get('success'):
            data = result.get('data', {})
            print(f"  输出: {data.get('output')}")
            print(f"  错误: {data.get('error')}")
        else:
            print(f"  错误: {result.get('error')}")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[Thread] HIL 工具调用失败 (耗时: {elapsed:.2f}s): {e}")
        return None

def test_confirm():
    """测试确认功能"""
    print_section("测试 1: 确认 (Confirm) 功能")
    
    hil_id = "TEST-CONFIRM-001"
    instruction = "请确认是否继续执行任务"
    
    # 在后台线程启动 HIL 任务
    result_container = []
    
    def worker():
        result = call_hil_async(hil_id, instruction)
        result_container.append(result)
    
    thread = threading.Thread(target=worker)
    thread.start()
    
    # 等待任务注册
    print("\n[主线程] 等待 HIL 任务注册...")
    time.sleep(2)
    
    # 查询 HIL 状态
    print(f"\n[主线程] 查询 HIL 任务状态: {hil_id}")
    response = requests.get(f"{SERVER_URL}/api/hil/{hil_id}")
    status = response.json()
    print(f"  状态: {status}")
    
    # 确认 HIL 任务
    print(f"\n[主线程] 确认 HIL 任务...")
    time.sleep(1)
    response = requests.post(
        f"{SERVER_URL}/api/hil/complete/{hil_id}",
        json={"result": "用户已确认，可以继续"}
    )
    complete_result = response.json()
    print(f"  完成响应: {complete_result}")
    
    # 等待线程结束
    print("\n[主线程] 等待 HIL 线程返回...")
    thread.join(timeout=5)
    
    # 检查结果
    if result_container:
        result = result_container[0]
        if result and result.get('success'):
            data = result.get('data', {})
            output = data.get('output', '')
            if '人类任务已完成' in output and '用户已确认' in output:
                print("\n✅ 测试通过: confirm 功能正常")
                return True
            else:
                print(f"\n❌ 测试失败: 输出格式不符合预期: {output}")
                return False
        else:
            print("\n❌ 测试失败: HIL 调用未成功")
            return False
    else:
        print("\n❌ 测试失败: 未收到返回结果")
        return False

def test_cancel():
    """测试取消功能"""
    print_section("测试 2: 取消 (Cancel) 功能")
    
    hil_id = "TEST-CANCEL-002"
    instruction = "请上传文件到 upload 目录"
    
    # 在后台线程启动 HIL 任务
    result_container = []
    
    def worker():
        result = call_hil_async(hil_id, instruction)
        result_container.append(result)
    
    thread = threading.Thread(target=worker)
    thread.start()
    
    # 等待任务注册
    print("\n[主线程] 等待 HIL 任务注册...")
    time.sleep(2)
    
    # 查询 HIL 状态
    print(f"\n[主线程] 查询 HIL 任务状态: {hil_id}")
    response = requests.get(f"{SERVER_URL}/api/hil/{hil_id}")
    status = response.json()
    print(f"  状态: {status}")
    
    # 取消 HIL 任务
    print(f"\n[主线程] 取消 HIL 任务...")
    time.sleep(1)
    response = requests.post(
        f"{SERVER_URL}/api/hil/cancel/{hil_id}",
        json={"reason": "用户不需要此功能"}
    )
    cancel_result = response.json()
    print(f"  取消响应: {cancel_result}")
    
    # 等待线程结束
    print("\n[主线程] 等待 HIL 线程返回...")
    thread.join(timeout=5)
    
    # 检查结果
    if result_container:
        result = result_container[0]
        if result and result.get('success'):
            data = result.get('data', {})
            output = data.get('output', '')
            if '用户取消操作' in output and '不需要此功能' in output:
                print("\n✅ 测试通过: cancel 功能正常")
                return True
            else:
                print(f"\n❌ 测试失败: 输出格式不符合预期: {output}")
                return False
        else:
            print("\n❌ 测试失败: HIL 调用未成功")
            return False
    else:
        print("\n❌ 测试失败: 未收到返回结果")
        return False

def test_list_hil_tasks():
    """测试查询所有 HIL 任务"""
    print_section("测试 3: 查询所有 HIL 任务")
    
    try:
        response = requests.get(f"{SERVER_URL}/api/hil/tasks")
        tasks = response.json()
        print(f"\n当前 HIL 任务列表:")
        print(f"  总数: {tasks.get('total', 0)}")
        for task in tasks.get('tasks', []):
            print(f"  - {task.get('hil_id')}: {task.get('status')} - {task.get('instruction')[:50]}")
        return True
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        return False

def main():
    """主测试流程"""
    print("="*60)
    print("  HIL API 功能测试")
    print("="*60)
    print(f"服务器地址: {SERVER_URL}")
    print(f"测试任务ID: {TEST_TASK_ID}")
    
    # 检查服务器
    print("\n检查服务器状态...")
    if not check_server():
        print("❌ 服务器未运行！")
        print("\n请先启动 Tool Server:")
        print("  cd Multi-Level-Agent-DEV/tool_server_lite")
        print("  python server.py")
        sys.exit(1)
    
    print("✅ 服务器运行正常")
    
    # 运行测试
    results = []
    
    # 测试 1: Confirm
    try:
        results.append(("Confirm 功能", test_confirm()))
    except Exception as e:
        print(f"\n❌ Confirm 测试异常: {e}")
        results.append(("Confirm 功能", False))
    
    time.sleep(2)  # 间隔
    
    # 测试 2: Cancel
    try:
        results.append(("Cancel 功能", test_cancel()))
    except Exception as e:
        print(f"\n❌ Cancel 测试异常: {e}")
        results.append(("Cancel 功能", False))
    
    time.sleep(1)  # 间隔
    
    # 测试 3: List HIL tasks
    try:
        results.append(("查询任务列表", test_list_hil_tasks()))
    except Exception as e:
        print(f"\n❌ 查询测试异常: {e}")
        results.append(("查询任务列表", False))
    
    # 总结
    print_section("测试总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()

