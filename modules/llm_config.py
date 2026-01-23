"""
LLM Configuration for Job Autopilot
配置各种LLM用于不同用途
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# LLM配置
LLM_CONFIG = {
    'resume': 'gpt-4o',               # 简历优化 - 长篇创意写作
    'message_generation': 'gemini-2.5-flash',  # 消息生成 - 快、便宜、短文本
    'profile_analysis': 'gpt-4o-mini',  # Profile分析 - 便宜
    'ranking': 'gpt-4o-mini',           # 打分 - 便宜
    'scam_detection': 'gpt-4o-mini',    # 诈骗检测 - 便宜
}


# ============================================
# Gemini Setup
# ============================================
def get_gemini_model():
    """
    获取Gemini模型实例
    
    需要在.env中配置 GOOGLE_API_KEY
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in .env file. "
            "Please add your Gemini API key from https://makersuite.google.com/app/apikey"
        )
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except ImportError:
        raise ImportError(
            "google-generativeai package not installed. "
            "Please run: pip install google-generativeai"
        )


async def call_gemini(prompt: str) -> str:
    """
    调用Gemini模型生成内容
    
    Args:
        prompt: 提示词
        
    Returns:
        生成的文本
    """
    try:
        model = get_gemini_model()
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        from modules.logger_config import app_logger
        app_logger.error(f"Gemini API error: {e}")
        # 返回fallback消息
        return f"[Gemini Error] {str(e)}"


def call_gemini_sync(prompt: str) -> str:
    """
    同步调用Gemini模型
    
    Args:
        prompt: 提示词
        
    Returns:
        生成的文本
    """
    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        from modules.logger_config import app_logger
        app_logger.error(f"Gemini API error: {e}")
        return f"[Gemini Error] {str(e)}"


# ============================================
# OpenAI Setup
# ============================================
def get_openai_client():
    """
    获取OpenAI客户端
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        raise ImportError("openai package not installed. Please run: pip install openai")


async def call_gpt(prompt: str, model: str = None, json_mode: bool = False) -> str:
    """
    调用OpenAI GPT模型
    
    Args:
        prompt: 提示词
        model: 模型名称（默认使用配置的模型）
        json_mode: 是否返回JSON格式
        
    Returns:
        生成的文本
    """
    import asyncio
    
    if model is None:
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    try:
        client = get_openai_client()
        
        # 同步调用，在线程池中运行
        def _call():
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        
        return await asyncio.get_event_loop().run_in_executor(None, _call)
    
    except Exception as e:
        from modules.logger_config import app_logger
        app_logger.error(f"OpenAI API error: {e}")
        return f"[OpenAI Error] {str(e)}"


def call_gpt_sync(prompt: str, model: str = None, json_mode: bool = False) -> str:
    """
    同步调用OpenAI GPT模型
    
    Args:
        prompt: 提示词
        model: 模型名称
        json_mode: 是否返回JSON格式
        
    Returns:
        生成的文本
    """
    if model is None:
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    try:
        client = get_openai_client()
        
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    except Exception as e:
        from modules.logger_config import app_logger
        app_logger.error(f"OpenAI API error: {e}")
        return f"[OpenAI Error] {str(e)}"


# ============================================
# Test Functions
# ============================================
def test_gemini():
    """测试Gemini连接"""
    try:
        response = call_gemini_sync("Say 'Hello from Gemini!' in one line.")
        print(f"✅ Gemini: {response}")
        return True
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return False


def test_openai():
    """测试OpenAI连接"""
    try:
        response = call_gpt_sync("Say 'Hello from OpenAI!' in one line.")
        print(f"✅ OpenAI: {response}")
        return True
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return False


if __name__ == "__main__":
    print("Testing LLM connections...\n")
    print("-" * 50)
    test_openai()
    print()
    test_gemini()
