#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI助手诊断脚本
用于检查AI助手配置是否正确
"""

import os
import sys

def check_ai_assistant_config():
    """检查AI助手配置"""
    print("=" * 50)
    print("AI助手配置诊断")
    print("=" * 50)
    
    # 1. 检查环境变量
    print("\n1. 检查环境变量 DEEPSEEK_API_KEY...")
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if api_key:
        print(f"   ✓ 环境变量已设置")
        print(f"   ✓ API密钥长度: {len(api_key)} 字符")
        print(f"   ✓ API密钥前缀: {api_key[:10]}...")
    else:
        print("   ✗ 环境变量未设置！")
        print("\n   解决方法：")
        print("   Windows (PowerShell):")
        print("   $env:DEEPSEEK_API_KEY=\"your_api_key_here\"")
        print("\n   Windows (CMD):")
        print("   set DEEPSEEK_API_KEY=your_api_key_here")
        print("\n   Linux/Mac:")
        print("   export DEEPSEEK_API_KEY=your_api_key_here")
        return False
    
    # 2. 检查 openai 库
    print("\n2. 检查 openai 库...")
    try:
        from openai import OpenAI
        print("   ✓ openai 库已安装")
    except ImportError:
        print("   ✗ openai 库未安装！")
        print("\n   解决方法：")
        print("   pip install openai")
        return False
    
    # 3. 测试 API 连接
    print("\n3. 测试 API 连接...")
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 发送测试请求
        print("   正在测试 API 连接...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "你好"}
            ],
            stream=False
        )
        
        print("   ✓ API 连接成功！")
        print(f"   ✓ 测试回复: {response.choices[0].message.content[:50]}...")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"   ✗ API 连接失败: {error_str}")
        
        if "401" in error_str or "Unauthorized" in error_str:
            print("\n   错误原因: API密钥无效")
            print("   解决方法: 检查 API 密钥是否正确，从 https://platform.deepseek.com/ 获取正确的密钥")
        elif "429" in error_str or "rate limit" in error_str.lower():
            print("\n   错误原因: API 调用频率超限")
            print("   解决方法: 等待一段时间后重试，或检查账户额度")
        elif "network" in error_str.lower() or "connection" in error_str.lower():
            print("\n   错误原因: 网络连接问题")
            print("   解决方法: 检查网络连接，确保可以访问 api.deepseek.com")
        else:
            print(f"\n   未知错误: {error_str}")
            print("   解决方法: 检查 API 密钥和网络连接")
        
        return False

if __name__ == "__main__":
    print("\n开始诊断...\n")
    success = check_ai_assistant_config()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 所有检查通过！AI助手应该可以正常工作。")
    else:
        print("✗ 发现问题，请根据上述提示进行修复。")
    print("=" * 50)
    
    sys.exit(0 if success else 1)


