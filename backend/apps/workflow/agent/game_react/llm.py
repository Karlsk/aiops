from dataclasses import dataclass, field
from typing import List, Dict, Any

from apps.llm.llm_helper import LLMHelper


# Prompt：封装要发给 LLM 的消息与工具定义
# - messages：对话上下文（系统/用户/助手三类）
# - tools：工具（函数）调用的 JSON Schema 描述（让 LLM 能"看见"可用的动作）
# - metadata：元数据（可选扩展，用 dict 保存）
@dataclass
class Prompt:
    messages: List[Dict] = field(default_factory=list)
    tools: List[Dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# 全局 LLMHelper 实例 - 延迟初始化
_llm_helper = None


def _get_llm_helper() -> LLMHelper:
    """获取 LLMHelper 实例，首次调用时初始化（延迟初始化模式）
    
    这种设计避免了模块导入时的初始化，只在实际需要时创建实例。
    这对于测试环境特别重要，可以避免导入错误。
    """
    global _llm_helper
    if _llm_helper is None:
        _llm_helper = LLMHelper(
            temperature=0.1,
            max_tokens=1024,
            enable_timeout=False
        )
    return _llm_helper


def _serialize_messages(messages: List[Dict]) -> str:
    """将消息列表序列化为字符串格式"""
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            serialized.append(f"{role}: {content}")
        else:
            serialized.append(str(msg))
    return "\n".join(serialized)


def generate_response(prompt: Prompt) -> str:
    """统一的 LLM 调用入口函数
    
    为 Game Agent 提供统一的大模型调用接口，自动处理工具调用和普通对话。
    
    工具调用优先使用 OpenAI 的原生 function_calls 机制，而不是提示词引导。
    这样可以确保更准确的工具调用识别和参数解析。
    
    工作原理：
    - 无工具时：调用 llm_helper.invoke()
    - 有工具时：调用 llm_helper.invoke_with_tools()，使用 OpenAI function_calls
    
    所有 LLM 调用都通过 llm_helper 统一管理，自动获得：
    - 自动故障转移（主模型 -> 备用模型）
    - 重试机制（最多 3 次，指数退避）
    - 超时控制
    - 性能统计
    
    Args:
        prompt: Prompt 对象，包含 messages、tools 和 metadata
        
    Returns:
        str: LLM 的响应
            - 无工具时：文本响应
            - 有工具时：JSON 格式的工具调用 {\"tool\": \"name\", \"args\": {...}} 或文本回复
            
    Examples:
        # 普通对话
        prompt = Prompt(messages=[
            {"role": "user", "content": "你好"}
        ])
        response = generate_response(prompt)
        
        # 工具调用（使用 OpenAI function_calls）
        prompt = Prompt(
            messages=[{"role": "user", "content": "查询 BGP 状态"}],
            tools=[
                {
                    "name": "get_bgp_status",
                    "description": "获取 BGP 邻居状态",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device": {"type": "string", "description": "设备名称"},
                            "neighbor_ip": {"type": "string", "description": "邻居 IP"}
                        },
                        "required": ["device", "neighbor_ip"]
                    }
                }
            ]
        )
        response = generate_response(prompt)
        # 返回: {\"tool\": \"get_bgp_status\", \"args\": {\"device\": \"...\", \"neighbor_ip\": \"...\"}}
    """
    # 获取 LLMHelper 实例（首次调用时初始化）
    llm_helper = _get_llm_helper()

    # 根据是否有工具选择调用方式
    if prompt.tools:
        # 有工具：使用原生 function_calls 模式
        messages_text = _serialize_messages(prompt.messages)
        return llm_helper.invoke_with_tools(
            input_data=messages_text,
            tools=prompt.tools,
            return_raw=False
        )
    else:
        # 无工具：普通对话模式
        messages_text = _serialize_messages(prompt.messages)
        return llm_helper.invoke(
            input_data=messages_text,
            return_raw=False
        )
