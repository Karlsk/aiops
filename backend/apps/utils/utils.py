import time
from functools import wraps
from .logger import TerraLogUtil
from typing import Any, Dict, Optional
import json
import requests
from apps.models.workflow.models import PlanSubType
# from apps.llm.llm_helper import LLMHelper


def retry_with_backoff(max_attempts=3, base_delay=1.0):
    """自定义重试装饰器，实现指数退避"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        TerraLogUtil.error(f"重试失败，已达到最大尝试次数: {e}")
                        raise e

                    delay = base_delay * (2 ** attempt)  # 指数退避
                    TerraLogUtil.warning(f"第{attempt + 1}次尝试失败，{delay}秒后重试: {e}")
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def timeout_handler(timeout_seconds=30.0):
    """超时控制装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_signal_handler(signum, frame):
                raise TimeoutError(f"操作超时 ({timeout_seconds}秒)")

            # 设置超时信号
            old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
            signal.alarm(int(timeout_seconds))

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消超时
                return result
            except TimeoutError:
                TerraLogUtil.error(f"操作超时: {timeout_seconds}秒")
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


# _llm_helper: Optional[LLMHelper] = None


# def _get_llm_helper() -> LLMHelper:
#     """获取 LLMHelper 实例，首次调用时初始化（延迟初始化模式）

#     这种设计避免了模块导入时的初始化，只在实际需要时创建实例。
#     这对于测试环境特别重要，可以避免导入错误。
#     """
#     global _llm_helper
#     if _llm_helper is None:
#         _llm_helper = LLMHelper(
#             temperature=0.1,
#             max_tokens=1024,
#             enable_timeout=False
#         )
#     return _llm_helper


def convert_state_to_dict(state: Any) -> Dict[str, Any]:
    """
    将状态转换为字典
    支持 Pydantic 模型、字典和其他类型

    Args:
        state: 任何类型的状态对象

    Returns:
        Dict: 转换后的字典
    """
    if hasattr(state, 'model_dump'):
        return state.model_dump()
    elif isinstance(state, dict):
        return state
    else:
        return {}


def map_output_to_state(node_name: str, node_output: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[
    str, Any]:
    """
    将节点输出映射到状态更新
    采用类似 Dify 的机制：将输出存储为 {node_name}_result
    后续节点可通过 state[f"{prev_node_name}_result"] 获取前面节点的数据

    Args:
        node_name: 节点名称
        node_output: 节点返回的输出
        state: 当前状态（用于更新 history）

    Returns:
        Dict: 返回给 LangGraph 的状态更新
    """
    # 使用通用的模式：{node_name}_result
    # 这样后续节点可以灵活访问任何前面节点的输出
    state_update = {}

    # 主要输出存储为 {node_name}_result
    state_update[f"{node_name}_result"] = node_output

    # 同时保留原始的逐字段更新（用于兼容旧的使用方式）
    state_update.update(node_output)

    # 更新 history（如果存在）
    if state and "history" in state:
        # 获取当前 history
        history = state.get("history", [])
        if not isinstance(history, list):
            history = []

        # 添加当前节点的执行记录
        entry = f"{node_name}: {str(node_output)[:100]}..."
        history_update = history + [entry]
        state_update["history"] = history_update

    return state_update


# --- Neo4j 工具函数（通过 FastAPI 接口调用） ---

def generate_plan_json(event_name: str, database: str, sub_type: str = "simple",
                       base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    独立函数：生成 JSON 格式的 Plan Schema
    通过调用本项目的 FastAPI 接口获取工作流规划
    
    Args:
        event_name: 事件名称，用于查询 Neo4j 路径
        database: 数据库名称
        sub_type: 规划子类型，支持 "simple" (默认) 和 "supervision"
        base_url: FastAPI 服务器地址，默认为 http://localhost:8000，由调用者传入
        
    Returns:
        Dict: 包含 JSON 格式 Plan Schema 的字典，格式为：
            {
                "id": "plan_xxx",
                "nodes": {...},
                "edges": [...],
                "start": "node_id",
                "stats": {...}
            }
            
    Raises:
        ValueError: 如果事件名称不存在或没有对应的路径
        requests.RequestException: 如果网络请求失败
    """

    try:
        # 输入校验
        if not event_name or not event_name.strip():
            raise ValueError("Event name cannot be empty")
        if not database or not database.strip():
            raise ValueError("Database name cannot be empty")

        event_name = event_name.strip()
        database = database.strip()

        # 使用传入的 base_url
        api_base_url = base_url

        # 构建 API URL
        if sub_type == PlanSubType.SUPERVISION:
            url = f"{api_base_url}/api/v1/neo4j/workflow/next-node"
        else:
            # 默认为 simple 类型
            url = f"{api_base_url}/api/v1/neo4j/json"

        params = {"name": event_name, "database": database}

        # 调用 FastAPI 接口
        TerraLogUtil.info(f"Calling API to generate plan for event: {event_name}")
        response = requests.get(url, params=params, timeout=30)

        # 检查响应状态
        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
            raise ValueError(f"API returned status code {response.status_code}: {error_detail}")

        # 解析响应
        result = response.json()
        if result.get("status") != "success":
            raise ValueError(f"API error: {result.get('message', 'Unknown error')}")

        # 返回 data 部分（包含 id, nodes, edges, start, stats）
        return result.get("data", {})

    except requests.RequestException as e:
        TerraLogUtil.error(f"Network error when calling API: {e}")
        raise ValueError(f"Failed to connect to API server: {str(e)}")
    except Exception as e:
        TerraLogUtil.error(f"Failed to generate plan JSON for event '{event_name}': {e}")
        raise


def extract_json_block(s: str) -> Optional[str]:
    """从文本中提取 JSON 块

    Args:
        s: 包含 JSON 的文本

    Returns:
        提取出的 JSON 字符串，如果找不到则返回 None
    """
    s = s.strip()
    try:
        json.loads(s)
        return s
    except Exception:
        pass

    # 逐字符扫描找到第一个 { 和对应的 }
    brace_count = 0
    start_idx = -1

    for i, char in enumerate(s):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            brace_count += 1
        elif char == '}':
            if start_idx != -1:
                brace_count -= 1
                if brace_count == 0:
                    # 找到了匹配的右括号
                    json_str = s[start_idx:i + 1]
                    try:
                        json.loads(json_str)
                        return json_str
                    except Exception:
                        # 继续查找下一个可能的 JSON
                        start_idx = -1

    return None
