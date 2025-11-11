"""
阿里云通义千问服务集成
"""

import dashscope
from dashscope import Generation, TextEmbedding
import os
from dotenv import load_dotenv

load_dotenv()

# 配置API Key
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

# 性格模板
PERSONALITY_TEMPLATES = {
    "gentle": "你性格温柔体贴，善解人意，总是给予关怀和支持。说话温和细腻。",
    "energetic": "你性格活泼开朗，热情洋溢，充满活力，能带来欢乐和正能量。",
    "intellectual": "你知性理性，逻辑清晰，善于分析和解决问题。",
    "humorous": "你幽默风趣，机智诙谐，妙语连珠，总能逗对方开心。",
    "calm": "你沉稳冷静，成熟稳重，遇事不慌，给人安全感。",
    "creative": "你富有创意，想象力丰富，思维跳跃，总有新奇想法。"
}


def generate_personality_prompt(dh_data):
    """
    根据数字人数据生成性格提示词

    Args:
        dh_data: 数字人字典数据

    Returns:
        str: 性格提示词
    """
    prompt_parts = []

    # 基础性格
    personality = dh_data.get("personality", "gentle")
    base = PERSONALITY_TEMPLATES.get(personality, PERSONALITY_TEMPLATES["gentle"])
    prompt_parts.append(base)

    # 特质描述
    traits = dh_data.get("traits", {})

    if traits.get("liveliness", 50) > 70:
        prompt_parts.append("你说话时很活泼外向，充满活力。")
    elif traits.get("liveliness", 50) < 30:
        prompt_parts.append("你说话时比较沉稳内敛，不太主动。")

    if traits.get("humor", 50) > 70:
        prompt_parts.append("你经常使用幽默的语言，让对话更轻松愉快。")

    if traits.get("empathy", 50) > 70:
        prompt_parts.append("你有很强的同理心，能敏锐地感知对方的情绪和需求。")

    if traits.get("initiative", 50) > 70:
        prompt_parts.append("你会主动发起话题，关心对方的近况。")

    if traits.get("creativity", 50) > 70:
        prompt_parts.append("你思维开阔，善于提出创新的想法和解决方案。")

    # 自定义描述
    if dh_data.get("customPersonality"):
        prompt_parts.append(dh_data["customPersonality"])

    return "\n".join(prompt_parts)


def chat_with_qianwen(messages, dh_data, stream=True):
    """
    与通义千问进行对话

    Args:
        messages: 对话历史列表 [{"role": "user", "content": "..."}]
        dh_data: 数字人数据字典
        stream: 是否使用流式输出

    Yields:
        str: 生成的回复文本（流式）或返回完整回复（非流式）
    """
    # 生成性格提示词
    personality_prompt = generate_personality_prompt(dh_data)

    # 构建系统提示词
    system_message = {
        "role": "system",
        "content": f"""你是一个温暖、善解人意的数字人助手，名字叫{dh_data.get('name', '小助手')}。

{personality_prompt}

请用自然、友好的语气回复，像真实的朋友一样交流。回复要简洁明了，不要过于冗长。"""
    }

    # 构建完整消息列表
    full_messages = [system_message] + messages

    # 限制上下文长度（保留最近10轮对话）
    if len(full_messages) > 21:  # 1个system + 10轮对话(每轮2条消息)
        full_messages = [full_messages[0]] + full_messages[-20:]

    try:
        if stream:
            # 流式对话
            responses = Generation.call(
                model=os.getenv('LLM_MODEL', 'qwen-turbo'),
                messages=full_messages,
                result_format='message',
                stream=True,
                incremental_output=True
            )

            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    yield content
                else:
                    yield f"Error: {response.message}"
        else:
            # 非流式对话
            response = Generation.call(
                model=os.getenv('LLM_MODEL', 'qwen-turbo'),
                messages=full_messages,
                result_format='message'
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"API Error: {response.message}")

    except Exception as e:
        if stream:
            yield f"对话出错: {str(e)}"
        else:
            raise e


def get_embeddings(texts):
    """
    文本向量化

    Args:
        texts: 文本列表

    Returns:
        list: 向量列表
    """
    try:
        response = TextEmbedding.call(
            model=os.getenv('EMBEDDING_MODEL', 'text-embedding-v2'),
            input=texts
        )

        if response.status_code == 200:
            return [item['embedding'] for item in response.output['embeddings']]
        else:
            raise Exception(f"Embedding Error: {response.message}")

    except Exception as e:
        raise Exception(f"文本向量化失败: {str(e)}")


def analyze_emotion(text):
    """
    分析文本情绪（简单版本）

    Args:
        text: 文本内容

    Returns:
        str: 情绪类型 ('happy', 'sad', 'calm', 'anxious', 'excited')
    """
    # 简单的情绪词典匹配
    happy_words = ['开心', '高兴', '快乐', '哈哈', '😊', '😄', '棒', '好的', '谢谢']
    sad_words = ['难过', '伤心', '失落', '😢', '😭', '不开心', '郁闷']
    anxious_words = ['紧张', '焦虑', '担心', '害怕', '压力', '忧虑']
    excited_words = ['兴奋', '激动', '期待', '哇', '😍', '太好了']

    text_lower = text.lower()

    if any(word in text_lower for word in happy_words):
        return 'happy'
    elif any(word in text_lower for word in sad_words):
        return 'sad'
    elif any(word in text_lower for word in anxious_words):
        return 'anxious'
    elif any(word in text_lower for word in excited_words):
        return 'excited'
    else:
        return 'calm'
