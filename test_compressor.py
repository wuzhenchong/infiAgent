#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史动作压缩功能
生成200K tokens的内容并测试压缩
"""

import sys
import random
import string
from services.action_compressor import ActionCompressor
from services.llm_client import SimpleLLMClient


def generate_random_text(token_count: int) -> str:
    """生成指定token数量的随机文本"""
    # 中文1.5字符≈1 token，英文4字符≈1 token
    # 混合生成
    chinese_chars = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"
    
    parts = []
    remaining_tokens = token_count
    
    while remaining_tokens > 0:
        # 随机选择生成中文或英文
        if random.random() > 0.5:
            # 生成中文段落
            chunk_tokens = min(random.randint(50, 200), remaining_tokens)
            chunk_chars = int(chunk_tokens * 1.5)
            chunk = ''.join(random.choices(chinese_chars, k=chunk_chars))
            parts.append(chunk)
            remaining_tokens -= chunk_tokens
        else:
            # 生成英文段落
            chunk_tokens = min(random.randint(50, 200), remaining_tokens)
            chunk_chars = int(chunk_tokens * 4)
            chunk = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=chunk_chars))
            parts.append(chunk)
            remaining_tokens -= chunk_tokens
    
    return '\n\n'.join(parts)


def generate_large_action_history(target_tokens: int = 200000):
    """
    生成大量的action_history，目标达到200K tokens
    
    Args:
        target_tokens: 目标token数
    
    Returns:
        List[Dict]: 模拟的action历史
    """
    print(f"🔧 开始生成 {target_tokens} tokens 的action_history...")
    
    action_history = []
    current_tokens = 0
    action_count = 0
    
    # 模拟不同类型的工具调用
    tool_templates = [
        {
            "name": "file_read",
            "output_type": "文件内容"
        },
        {
            "name": "web_search",
            "output_type": "搜索结果"
        },
        {
            "name": "code_execute",
            "output_type": "执行输出"
        },
        {
            "name": "document_parse",
            "output_type": "文档解析"
        },
        {
            "name": "arxiv_search",
            "output_type": "论文信息"
        }
    ]
    
    while current_tokens < target_tokens:
        action_count += 1
        template = random.choice(tool_templates)
        
        # 每个action生成5k-10k tokens的输出
        action_tokens = random.randint(5000, 10000)
        output_text = generate_random_text(action_tokens)
        
        action = {
            "tool_name": template["name"],
            "arguments": {
                "query": f"测试查询_{action_count}",
                "params": f"参数_{action_count}"
            },
            "result": {
                "status": "success",
                "output": output_text
            }
        }
        
        action_history.append(action)
        current_tokens += action_tokens
        
        if action_count % 10 == 0:
            print(f"   已生成 {action_count} 条actions，约 {current_tokens} tokens")
    
    print(f"✅ 生成完成：{action_count} 条actions，总计约 {current_tokens} tokens\n")
    return action_history


def test_compression():
    """测试压缩功能"""
    print("="*80)
    print("🧪 开始测试历史动作压缩功能")
    print("="*80)
    print()
    
    # 启用 LiteLLM 调试模式
    try:
        import litellm
        litellm.set_verbose = True
        print("🐛 已启用 LiteLLM 调试模式\n")
    except:
        pass
    
    # 1. 初始化LLM客户端和压缩器
    print("📦 初始化LLM客户端和压缩器...")
    try:
        llm_client = SimpleLLMClient()
        compressor = ActionCompressor(llm_client)
        print(f"✅ 初始化成功")
        print(f"   最大上下文窗口: {llm_client.max_context_window} tokens")
        print(f"   压缩模型: {llm_client.compressor_models[0]}")
        print()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 生成大量数据
    action_history = generate_large_action_history(target_tokens=200000)
    
    # 3. 计算原始token数
    print("📊 计算原始token数...")
    original_xml = compressor._actions_to_xml(action_history)
    original_tokens = compressor.count_tokens(original_xml)
    print(f"✅ 原始数据统计:")
    print(f"   Actions数量: {len(action_history)} 条")
    print(f"   XML长度: {len(original_xml)} 字符")
    print(f"   Token数: {original_tokens} tokens")
    print()
    
    # 4. 测试压缩
    print("🔄 开始压缩测试...")
    print(f"   触发阈值: {llm_client.max_context_window - 20000} tokens")
    print(f"   当前数据: {original_tokens} tokens")
    print(f"   是否需要压缩: {'✅ 是' if original_tokens > llm_client.max_context_window - 20000 else '❌ 否'}")
    print()
    
    # 显示将要使用的压缩模型
    print("🤖 压缩配置信息:")
    print(f"   压缩模型列表: {llm_client.compressor_models}")
    print(f"   实际使用模型: {llm_client.compressor_models[0]}")
    print(f"   LLM客户端类型: {type(llm_client).__name__}")
    print()
    
    # 模拟thinking和task_input
    thinking = """
任务进度分析：
1. ✅ 已完成数据收集阶段
2. ✅ 已完成初步分析
3. 🔄 正在进行深度分析
4. ⏳ 待完成结果总结

下一步计划：
- 继续分析剩余数据
- 提取关键信息
- 生成最终报告
"""
    
    task_input = "测试任务：分析大量文档数据并生成综合报告"
    
    try:
        # 临时保存原始的chat方法来监控调用
        original_chat = llm_client.chat
        call_count = [0]  # 使用列表来在闭包中修改
        
        def monitored_chat(*args, **kwargs):
            call_count[0] += 1
            model = kwargs.get('model', 'unknown')
            print(f"\n🔍 LLM调用 #{call_count[0]}:")
            print(f"   模型: {model}")
            print(f"   参数: tool_choice={kwargs.get('tool_choice', 'auto')}")
            if 'history' in kwargs and kwargs['history']:
                first_msg = kwargs['history'][0]
                content_preview = first_msg.content[:150] if hasattr(first_msg, 'content') else str(first_msg)[:150]
                print(f"   消息预览: {content_preview}...")
            
            result = original_chat(*args, **kwargs)
            print(f"   调用状态: {result.status}")
            
            # 如果失败，显示完整错误信息
            if result.status == "error":
                print(f"\n   ❌ 完整错误信息:")
                print(f"   错误输出: {result.output}")
                if hasattr(result, 'error_information') and result.error_information:
                    print(f"\n   详细错误堆栈:")
                    print("   " + "="*60)
                    # 将错误信息按行缩进显示
                    for line in str(result.error_information).split('\n'):
                        print(f"   {line}")
                    print("   " + "="*60)
            
            return result
        
        # 替换为监控版本
        llm_client.chat = monitored_chat
        
        compressed_history = compressor.compress_if_needed(
            action_history=action_history,
            max_context_window=llm_client.max_context_window,
            thinking=thinking,
            task_input=task_input
        )
        
        # 恢复原始方法
        llm_client.chat = original_chat
        
        # 5. 计算压缩后的token数
        print("\n📊 计算压缩后token数...")
        compressed_xml = compressor._actions_to_xml(compressed_history)
        compressed_tokens = compressor.count_tokens(compressed_xml)
        
        print(f"\n{'='*80}")
        print("✅ 压缩测试完成")
        print(f"{'='*80}")
        print(f"\n📈 压缩效果对比:")
        print(f"   原始Actions: {len(action_history)} 条")
        print(f"   压缩后Actions: {len(compressed_history)} 条")
        print(f"   Actions压缩率: {len(compressed_history)/len(action_history)*100:.1f}%")
        print()
        print(f"   原始Tokens: {original_tokens:,} tokens")
        print(f"   压缩后Tokens: {compressed_tokens:,} tokens")
        print(f"   Token压缩率: {compressed_tokens/original_tokens*100:.1f}%")
        print(f"   节省Tokens: {original_tokens - compressed_tokens:,} tokens")
        print()
        print(f"   原始XML长度: {len(original_xml):,} 字符")
        print(f"   压缩后XML长度: {len(compressed_xml):,} 字符")
        print()
        
        # 6. 显示压缩后的结构
        print("📋 压缩后的Actions结构:")
        for i, action in enumerate(compressed_history):
            tool_name = action.get("tool_name", "unknown")
            result = action.get("result", {})
            output = result.get("output", "")
            is_summary = result.get("_is_summary", False)
            
            if is_summary:
                print(f"   [{i+1}] {tool_name} (历史总结)")
                print(f"       输出长度: {len(output)} 字符")
                print(f"       输出预览: {output[:100]}...")
            else:
                compressed_flag = result.get("_compressed", False)
                original_tokens_count = result.get("_original_tokens", 0)
                print(f"   [{i+1}] {tool_name} {'(已压缩)' if compressed_flag else ''}")
                print(f"       参数: {action.get('arguments', {})}")
                print(f"       输出长度: {len(output)} 字符")
                if original_tokens_count:
                    print(f"       原始tokens: {original_tokens_count}")
                print(f"       输出预览: {output[:]}...")
            print()
        
        print(f"{'='*80}")
        print("✅ 测试完成！")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ 压缩过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_compression()

