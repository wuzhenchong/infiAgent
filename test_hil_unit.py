#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIL 功能单元测试
直接测试 Python 代码，不需要服务器运行
"""

import sys
import asyncio
import threading
import time
from pathlib import Path

# 添加 tool_server_lite 到路径
sys.path.insert(0, str(Path(__file__).parent / "tool_server_lite"))

from tools.human_tools import (
    HumanInLoopTool,
    get_hil_status,
    complete_hil_task,
    cancel_hil_task,
    list_hil_tasks,
    HIL_TASKS
)

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_complete():
    """测试 complete 功能"""
    print_section("测试 1: Complete 功能")
    
    # 清空任务列表
    HIL_TASKS.clear()
    
    # 创建 HIL 工具实例
    tool = HumanInLoopTool()
    task_id = "/tmp/test"
    hil_id = "TEST-001"
    
    # 在后台线程运行 HIL 工具
    result_container = []
    
    async def run_hil():
        result = await tool.execute_async(task_id, {
            "hil_id": hil_id,
            "instruction": "请确认操作",
            "timeout": 10
        })
        result_container.append(result)
    
    def thread_worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_hil())
        loop.close()
    
    thread = threading.Thread(target=thread_worker)
    print(f"\n[主线程] 启动 HIL 任务: {hil_id}")
    thread.start()
    
    # 等待任务注册
    time.sleep(1)
    
    # 检查状态
    print(f"[主线程] 检查任务状态...")
    status = get_hil_status(hil_id)
    print(f"  状态: {status}")
    
    if not status.get('found'):
        print("❌ 测试失败: 任务未注册")
        return False
    
    if status.get('status') != 'waiting':
        print(f"❌ 测试失败: 状态不是 waiting，而是 {status.get('status')}")
        return False
    
    # 完成任务
    print(f"[主线程] 完成任务...")
    time.sleep(0.5)
    complete_result = complete_hil_task(hil_id, "用户已确认")
    print(f"  完成结果: {complete_result}")
    
    if not complete_result.get('success'):
        print("❌ 测试失败: 完成操作失败")
        return False
    
    # 等待线程结束
    print(f"[主线程] 等待 HIL 线程返回...")
    thread.join(timeout=5)
    
    # 检查结果
    if not result_container:
        print("❌ 测试失败: 未收到返回结果")
        return False
    
    result = result_container[0]
    print(f"\n[HIL 返回] {result}")
    
    if result['status'] != 'success':
        print(f"❌ 测试失败: 状态不是 success")
        return False
    
    output = result.get('output', '')
    if '人类任务已完成' not in output or '用户已确认' not in output:
        print(f"❌ 测试失败: 输出格式不正确: {output}")
        return False
    
    print("\n✅ 测试通过: Complete 功能正常")
    return True

def test_cancel():
    """测试 cancel 功能"""
    print_section("测试 2: Cancel 功能")
    
    # 清空任务列表
    HIL_TASKS.clear()
    
    # 创建 HIL 工具实例
    tool = HumanInLoopTool()
    task_id = "/tmp/test"
    hil_id = "TEST-002"
    
    # 在后台线程运行 HIL 工具
    result_container = []
    
    async def run_hil():
        result = await tool.execute_async(task_id, {
            "hil_id": hil_id,
            "instruction": "请上传文件",
            "timeout": 10
        })
        result_container.append(result)
    
    def thread_worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_hil())
        loop.close()
    
    thread = threading.Thread(target=thread_worker)
    print(f"\n[主线程] 启动 HIL 任务: {hil_id}")
    thread.start()
    
    # 等待任务注册
    time.sleep(1)
    
    # 检查状态
    print(f"[主线程] 检查任务状态...")
    status = get_hil_status(hil_id)
    print(f"  状态: {status}")
    
    if not status.get('found'):
        print("❌ 测试失败: 任务未注册")
        return False
    
    if status.get('status') != 'waiting':
        print(f"❌ 测试失败: 状态不是 waiting，而是 {status.get('status')}")
        return False
    
    # 取消任务
    print(f"[主线程] 取消任务...")
    time.sleep(0.5)
    cancel_result = cancel_hil_task(hil_id, "用户不需要")
    print(f"  取消结果: {cancel_result}")
    
    if not cancel_result.get('success'):
        print("❌ 测试失败: 取消操作失败")
        return False
    
    # 等待线程结束
    print(f"[主线程] 等待 HIL 线程返回...")
    thread.join(timeout=5)
    
    # 检查结果
    if not result_container:
        print("❌ 测试失败: 未收到返回结果")
        return False
    
    result = result_container[0]
    print(f"\n[HIL 返回] {result}")
    
    if result['status'] != 'success':
        print(f"❌ 测试失败: 状态不是 success")
        return False
    
    output = result.get('output', '')
    if '用户取消操作' not in output or '用户不需要' not in output:
        print(f"❌ 测试失败: 输出格式不正确: {output}")
        return False
    
    print("\n✅ 测试通过: Cancel 功能正常")
    return True

def test_list_tasks():
    """测试列表功能"""
    print_section("测试 3: 列表功能")
    
    # 清空任务列表
    HIL_TASKS.clear()
    
    # 添加一些测试任务
    HIL_TASKS["TEST-A"] = {
        "status": "waiting",
        "instruction": "测试任务 A",
        "task_id": "/tmp/test",
        "result": None
    }
    
    HIL_TASKS["TEST-B"] = {
        "status": "completed",
        "instruction": "测试任务 B",
        "task_id": "/tmp/test",
        "result": "完成"
    }
    
    # 列出任务
    result = list_hil_tasks()
    print(f"\n任务列表: {result}")
    
    if result.get('total') != 2:
        print(f"❌ 测试失败: 任务数量不正确，期望 2，实际 {result.get('total')}")
        return False
    
    tasks = result.get('tasks', [])
    if len(tasks) != 2:
        print(f"❌ 测试失败: 任务列表长度不正确")
        return False
    
    # 检查任务详情
    task_ids = [t['hil_id'] for t in tasks]
    if 'TEST-A' not in task_ids or 'TEST-B' not in task_ids:
        print(f"❌ 测试失败: 任务 ID 不正确")
        return False
    
    print("\n✅ 测试通过: 列表功能正常")
    return True

def test_status_values():
    """测试状态值"""
    print_section("测试 4: 状态值验证")
    
    # 清空任务列表
    HIL_TASKS.clear()
    
    print("\n[测试] 添加不同状态的任务...")
    
    # waiting 状态
    HIL_TASKS["TEST-WAITING"] = {
        "status": "waiting",
        "instruction": "等待中",
        "task_id": "/tmp/test",
        "result": None
    }
    
    # completed 状态
    HIL_TASKS["TEST-COMPLETED"] = {
        "status": "completed",
        "instruction": "已完成",
        "task_id": "/tmp/test",
        "result": "完成"
    }
    
    # cancelled 状态
    HIL_TASKS["TEST-CANCELLED"] = {
        "status": "cancelled",
        "instruction": "已取消",
        "task_id": "/tmp/test",
        "result": "取消原因"
    }
    
    # timeout 状态
    HIL_TASKS["TEST-TIMEOUT"] = {
        "status": "timeout",
        "instruction": "超时",
        "task_id": "/tmp/test",
        "result": None
    }
    
    # 验证所有状态
    all_tasks = list_hil_tasks()
    print(f"\n所有任务: {all_tasks}")
    
    if all_tasks.get('total') != 4:
        print(f"❌ 测试失败: 任务数量不正确")
        return False
    
    # 验证每个状态
    statuses = {task['hil_id']: task['status'] for task in all_tasks['tasks']}
    
    expected = {
        "TEST-WAITING": "waiting",
        "TEST-COMPLETED": "completed",
        "TEST-CANCELLED": "cancelled",
        "TEST-TIMEOUT": "timeout"
    }
    
    for hil_id, expected_status in expected.items():
        if statuses.get(hil_id) != expected_status:
            print(f"❌ 测试失败: {hil_id} 状态不正确，期望 {expected_status}，实际 {statuses.get(hil_id)}")
            return False
    
    print("\n✅ 测试通过: 所有状态值正确")
    return True

def main():
    """主测试流程"""
    print("="*60)
    print("  HIL 功能单元测试")
    print("="*60)
    print("直接测试 Python 代码，无需服务器运行")
    
    results = []
    
    # 运行所有测试
    try:
        results.append(("Complete 功能", test_complete()))
    except Exception as e:
        print(f"\n❌ Complete 测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Complete 功能", False))
    
    time.sleep(1)
    
    try:
        results.append(("Cancel 功能", test_cancel()))
    except Exception as e:
        print(f"\n❌ Cancel 测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Cancel 功能", False))
    
    try:
        results.append(("列表功能", test_list_tasks()))
    except Exception as e:
        print(f"\n❌ 列表测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("列表功能", False))
    
    try:
        results.append(("状态值验证", test_status_values()))
    except Exception as e:
        print(f"\n❌ 状态值测试异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("状态值验证", False))
    
    # 总结
    print_section("测试总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Cancel 功能实现正确！")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()

