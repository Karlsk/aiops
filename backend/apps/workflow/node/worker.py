"""
Worker 节点实现
支持 MCP 类型的工作节点，集成 Game Agent 逻辑
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from langchain_core.runnables import Runnable, RunnableLambda

from .base import BaseNode
from apps.models.workflow.models import NodeType, WorkerConfig, ExecutionLog, OperatorLog
from apps.utils.utils import convert_state_to_dict, map_output_to_state
from apps.workflow.agent.game_react.action import ActionRegistry, Action
from apps.workflow.agent.game_react.agent_language import AgentFunctionCallingActionLanguage
from apps.workflow.agent.game_react.environment import Environment
from apps.workflow.agent.game_react.goal import Goal
from apps.workflow.agent.game_react.agent import Agent
from apps.workflow.agent.game_react.llm import generate_response
from apps.workflow.agent.game_react.memory import Memory
from ..client.mcp_client import MCPClientManager

from apps.utils.logger import TerraLogUtil


class WorkerNode(BaseNode):
    """
    Worker 节点：基于 Game Agent 的工作节点
    支持 MCP 工具调用，可配置目标和记忆
    """

    def __init__(
            self,
            name: str,
            config: Dict[str, Any],
            operator_log: Optional[OperatorLog] = None
    ):
        """
        初始化 Worker 节点

        Args:
            name: 节点名称
            config: 节点配置（WorkerConfig 格式），包含：
                - sub_type: Worker 子类型（MCP 或 RAG）
                - mcp_configs/mcp_config: MCP 服务器配置
                - goals: 智能体目标列表（可选）
                - memory: 初始记忆对象（可选）
            operator_log: 操作符日志
        """
        super().__init__(name, NodeType.Worker, config, operator_log)
        self.worker_config = WorkerConfig(**config) if isinstance(config, dict) else config
        
        # 从 config 中提取 mcp_configs
        self.mcp_configs = self.worker_config.mcp_configs or {}
        
        # 从 config 中提取和初始化 goals
        self.goals = []
        if self.worker_config.goals:
            for goal_dict in self.worker_config.goals:
                if isinstance(goal_dict, dict):
                    self.goals.append(Goal(**goal_dict))
                elif isinstance(goal_dict, Goal):
                    self.goals.append(goal_dict)

        # 从 config 中提取和初始化 memory
        self.memory = Memory()
        if self.worker_config.memory:
            memory_data = self.worker_config.memory
            if isinstance(memory_data, Memory):
                self.memory = memory_data
            elif isinstance(memory_data, dict) and 'items' in memory_data:
                self.memory.items = memory_data['items']
        
        # 初始化 Agent 相关组件
        self.agent = None
        self.mcp_manager = None
        self.action_registry = None
        self.agent_language = AgentFunctionCallingActionLanguage()
        self.environment = Environment()

    def validate_config(self) -> bool:
        """验证 Worker 配置"""
        if self.worker_config.sub_type.value == "mcp":
            if not self.mcp_configs:
                raise ValueError(f"Worker '{self.name}': MCP configs are required for MCP sub-type")
        return True

    async def _init_mcp_actions(self) -> ActionRegistry:
        """
        异步初始化 MCP 工具到 action registry
        
        Returns:
            ActionRegistry: 包含所有 MCP 工具和 terminate 动作的注册表
        """
        if not self.mcp_configs:
            raise ValueError("MCP configs are not configured")

        self.mcp_manager = MCPClientManager()
        action_registry = ActionRegistry()

        try:
            # 获取工具列表
            tools = await self.mcp_manager.get_tools(self.mcp_configs)

            # 为每个 MCP 工具创建一个 Action
            for tool in tools:
                # 提取工具信息
                tool_name = tool.name if hasattr(tool, 'name') else tool.get('name', '')
                tool_desc = tool.description if hasattr(tool, 'description') else tool.get('description', '')
                tool_args_schema = tool.args_schema if hasattr(tool, 'args_schema') else tool.get('args_schema', {})

                # 验证工具的必需字段
                if not tool_name or not tool_name.strip():
                    TerraLogUtil.error(f"⚠️ 警告: 工具缺少有效的 name 字段，跳过该工具。工具信息: {tool}")
                    continue

                # 清理 name（移除多余空白）
                tool_name = tool_name.strip()

                # 如果 description 为空，使用默认描述
                if not tool_desc or not tool_desc.strip():
                    tool_desc = f"调用 {tool_name} 工具"
                else:
                    tool_desc = tool_desc.strip()

                # 如果 parameters 为空，使用默认的空对象
                if not tool_args_schema:
                    tool_args_schema = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }

                # 创建一个闭包，为每个工具捕获参数
                def make_tool_callable(tool_name_closure, mcp_configs_closure, mcp_manager_closure):
                    """为每个工具创建一个可调用的函数"""

                    def tool_callable(**kwargs):
                        # 在实际调用时执行 MCP 工具。
                        # 使用 asyncio.run 来同步执行异步函数

                        coro = mcp_manager_closure.call_tool(
                            server_configs=mcp_configs_closure,
                            tool_name=tool_name_closure,
                            arguments=kwargs
                        )
                        try:
                            return asyncio.run(coro)
                        except RuntimeError as e:
                            # 如果已经有运行中的事件循环，使用 nest_asyncio
                            if "asyncio.run() cannot be called from a running event loop" in str(e):
                                import nest_asyncio
                                nest_asyncio.apply()

                                # 注意：这里不需要重新创建 coro，因为之前的 coro 还没开始跑
                                return asyncio.run(coro)
                            raise

                    return tool_callable

                # 创建 Action
                action = Action(
                    name=tool_name,
                    description=tool_desc,
                    function=make_tool_callable(tool_name, self.mcp_configs, self.mcp_manager),
                    parameters=tool_args_schema if isinstance(tool_args_schema, dict) else {},
                    terminal=False
                )
                # 注册 Action
                print(f"✓ 注册工具: {tool_name}")
                action_registry.register(action)

        except Exception as e:
            print(f"❌ 初始化 MCP 工具失败: {str(e)}")
            raise

        # 添加 terminate 终止动作
        action_registry.register(Action(
            name="terminate",
            function=lambda message: f"{message}\nTerminating...",
            description="Terminates the session and prints the message to the user.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": []
            },
            terminal=True
        ))

        return action_registry

    def _sync_init_mcp_actions(self) -> ActionRegistry:
        """
        同步初始化 MCP 工具到 action registry
        当异步初始化失败时的备选方案
        
        Returns:
            ActionRegistry: 基本的 action registry，仃包含 terminate 动作
        """
        action_registry = ActionRegistry()
        
        # 添加一个预置的 terminate 动作
        action_registry.register(Action(
            name="terminate",
            function=lambda message: f"{message}\nTerminating...",
            description="Terminates the session and prints the message to the user.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": []
            },
            terminal=True
        ))
        
        return action_registry

    def build_runnable(self) -> Runnable:
        """构建 Worker 节点的 Runnable"""
        self.validate_config()

        def worker_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """执行 Worker 节点逻辑"""
            state_dict = convert_state_to_dict(state)
            
            # 从状态中提取新的 goals（避免累积）
            goals_from_state = state_dict.get("goals", [])
            current_goals = list(self.goals)  # 从配置中初始化的 goals
            cur_steps = []
            
            # 处理从状态传入的动态 goals
            if goals_from_state and isinstance(goals_from_state, list):
                for goal_dict in goals_from_state:
                    if isinstance(goal_dict, dict):
                        goal_dict['priority'] = goal_dict.get('priority', 1)
                        current_goals.append(Goal(**goal_dict))
                        cur_steps.append(goal_dict.get('name', ''))
                    elif isinstance(goal_dict, Goal):
                        current_goals.append(goal_dict)
                        cur_steps.append(goal_dict.name)
                    elif isinstance(goal_dict, str):
                        current_goals.append(Goal(
                            priority=1,
                            name=goal_dict,
                            description=f"调用 MCP 工具获取: {goal_dict}"
                        ))
                        cur_steps.append(goal_dict)



            start_time = time.time()
            try:
                # 异步初始化 MCP 工具和 Agent
                if self.worker_config.sub_type.value == "mcp":
                    # 只在首次调用时初始化 action_registry，避免重复初始化
                    if self.action_registry is None:
                        # 使用 try-except 来处理已存在的事件循环
                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            # 没有运行中的事件循环，创建新的
                            loop = None
                        
                        if loop is None:
                            # 没有运行中的循环，安全地创建新循环
                            try:
                                self.action_registry = asyncio.run(self._init_mcp_actions())
                            except RuntimeError as e:
                                # 如果仍然失败，尝试使用 nest_asyncio
                                if "asyncio.run() cannot be called from a running event loop" in str(e):
                                    import nest_asyncio
                                    nest_asyncio.apply()
                                    self.action_registry = asyncio.run(self._init_mcp_actions())
                                else:
                                    raise
                        else:
                            # 已有运行中的事件循环，使用 ensure_future
                            import concurrent.futures
                            try:
                                # 在线程中运行异步操作
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, self._init_mcp_actions())
                                    self.action_registry = future.result()
                            except Exception as e:
                                print(f"⚠️ 线程执行失败，尝试直接使用已有循环: {e}")
                                # 回退到同步方式
                                self.action_registry = self._sync_init_mcp_actions()

                    # 创建 Agent 实例（每次调用都创建新实例，使用当前的 goals）
                    agent = Agent(
                        goals=current_goals,
                        agent_language=self.agent_language,
                        action_registry=self.action_registry,
                        generate_response=generate_response,
                        environment=self.environment
                    )

                    # 从状态中提取用户输入（通常是 'input' 或 'user_input' 字段）
                    user_input = state_dict.get('input') or state_dict.get('user_input') or ''

                    # 从状态中获取或使用初始化时的 memory
                    short_memory = state_dict.get("history", [])
                    current_memory = self.memory
                    if short_memory and isinstance(short_memory, list):
                        for item in short_memory:
                            if isinstance(item, dict):
                                current_memory.add_memory(item)
                            elif isinstance(item, str):
                                current_memory.add_memory({
                                    "type": "user",
                                    "content": item
                                })

                    # 运行 Agent
                    print(f"🤖 Worker '{self.name}' 开始执行，输入: {user_input}")
                    final_memory = agent.run(user_input, memory=current_memory)

                    # 获取最终的记忆信息
                    memories = final_memory.get_memories()

                    # 从记忆中提取工具调用结果（除了 terminate）
                    results = []
                    for i, memory_item in enumerate(memories):
                        # 查找 assistant 的工具调用
                        if memory_item.get('type') == 'assistant':
                            try:
                                import json
                                assistant_content = json.loads(memory_item.get('content', '{}'))
                                tool_name = assistant_content.get('tool', '')
                                
                                # 跳过 terminate 工具
                                if tool_name and tool_name != 'terminate':
                                    # 查找对应的 environment 结果（下一条或附近的记忆）
                                    tool_result = None
                                    for j in range(i + 1, len(memories)):
                                        if memories[j].get('type') == 'environment':
                                            try:
                                                env_content = json.loads(memories[j].get('content', '{}'))
                                                tool_result = env_content.get('result', '')
                                                break
                                            except:
                                                pass
                                    
                                    # 如果找到结果，添加到列表
                                    if tool_result:
                                        results.append({
                                            "tool": tool_name,
                                            "args": assistant_content.get('args', {}),
                                            "result": tool_result
                                        })
                            except (json.JSONDecodeError, ValueError):
                                # 如果不是 JSON 格式，跳过
                                pass

                    # 构造输出
                    output = {
                        "steps": cur_steps,
                        "status": "completed",
                        "results": results,
                        "memories": memories,
                        "memory_count": len(memories)
                    }

                else:
                    # 其他 Worker 子类型（如 RAG）的处理
                    output = {
                        "status": "unsupported",
                        "message": f"Worker sub-type '{self.worker_config.sub_type}' not yet implemented"
                    }

                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))
                state_dict["worker_status"] = output.get("status", "error")
                if output.get("status") == "completed":
                    state_dict["worker_result"] = {
                        "steps": output.get("steps", []),
                        "results": output.get("results", [])
                    }
                    cur_history = [
                        {
                            "type": "user",
                            "content": output.get("steps", [])
                        },
                        {
                            "type": "assistant",
                            "content": output.get("results", [])
                        }
                    ]
                else:
                    cur_history = []
                # 使用 map_output_to_state 将输出映射到状态更新
                # 采用 Dify 风格，为输出添加 {node_name}_result 字段
                return map_output_to_state(self.name, output, state_dict, cur_history)

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                error_msg = str(e)
                print(f"❌ Worker '{self.name}' 执行失败: {error_msg}")
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data={},
                    execution_time_ms=execution_time,
                    error=error_msg
                ))
                raise

        return RunnableLambda(worker_func).with_config(tags=[self.name])

    def set_mcp_configs(self, mcp_configs: Dict[str, Dict[str, str]]) -> None:
        """更新 MCP 服务器配置"""
        self.mcp_configs = mcp_configs

    def set_goals(self, goals: List[Goal]) -> None:
        """更新智能体目标"""
        self.goals = goals

    def set_memory(self, memory: Memory) -> None:
        """更新记忆对象"""
        self.memory = memory

    def get_memory(self) -> Memory:
        """获取当前记忆对象"""
        return self.memory
