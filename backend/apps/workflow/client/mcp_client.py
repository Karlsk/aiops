"""
MCP 客户端管理器
负责 MCP 客户端的创建、缓存和工具调用
"""
import asyncio
import time
from calendar import c
from typing import Dict, List, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient

from apps.models.service.mcp_models import MCPServer
from apps.utils.logger import TerraLogUtil


class MCPClientManager:
    """MCP 客户端管理器 - 单例模式
    
    负责：
    1. MCP 客户端的创建和缓存
    2. 工具列表的获取
    3. 工具的调用
    """
    _instance = None
    _mcp_client: Optional[MultiServerMCPClient] = None
    _last_server_config: Optional[Dict] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPClientManager, cls).__new__(cls)
        return cls._instance

    async def get_client(self, server_configs: Dict[str, Dict[str, str]]) -> MultiServerMCPClient:
        """获取或创建 MCP 客户端
        
        如果服务器配置有变化，会重新创建客户端
        
        Args:
            server_configs: 服务器配置字典，格式：{name: {url, transport}}
        
        Returns:
            MultiServerMCPClient 实例
        
        Raises:
            ValueError: 当没有服务器配置时
        """
        # 检查配置是否变化
        if (self._mcp_client is None or
                self._last_server_config != server_configs or
                not server_configs):

            if not server_configs:
                raise ValueError("No MCP servers configured")

            self._mcp_client = MultiServerMCPClient(server_configs)
            self._last_server_config = server_configs

        return self._mcp_client

    async def get_tools(self, server_configs: Dict[str, Dict[str, str]]) -> List[Any]:
        """获取工具列表
        
        Args:
            server_configs: 服务器配置字典
        
        Returns:
            工具列表
        
        Raises:
            ValueError: 当没有服务器配置时
            Exception: 获取工具失败时
        """
        client = await self.get_client(server_configs)
        return await client.get_tools()

    async def call_tool(
            self,
            server_configs: Dict[str, Dict[str, str]],
            tool_name: str,
            arguments: Dict[str, Any]
    ) -> Any:
        """调用工具
        
        Args:
            server_configs: 服务器配置字典
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        
        Raises:
            ValueError: 当没有服务器配置时
            Exception: 调用工具失败时
        """
        client = await self.get_client(server_configs)
        tools = await client.get_tools()
        tools_by_name = {tool.name: tool for tool in tools}
        if tool_name not in tools_by_name:
            raise ValueError(f"Tool with name {tool_name} not found")
        tool = tools_by_name[tool_name]
        TerraLogUtil.debug(f"Calling tool: {tool_name}")
        TerraLogUtil.debug(f"Tool arguments: {arguments}")
        invoke_result = await _invoke_tool_with_timeout(tool, arguments)
        TerraLogUtil.debug(f"Tool invoke result: {invoke_result}")
        call_res = invoke_result["ok"]
        if not call_res:
            raise Exception(f"Tool call failed: {invoke_result['error']}")
        return invoke_result["payload"]

    def reset(self):
        """重置客户端
        
        当 MCP 服务器配置变化时调用此方法
        """
        self._mcp_client = None
        self._last_server_config = None


def get_tools_info(tools: List[Any]) -> List[Dict[str, Any]]:
    """将工具对象转换为信息字典列表
    
    Args:
        tools: 工具对象列表
    
    Returns:
        工具信息字典列表
    """
    tools_info = []
    for tool in tools:
        tool_info = {
            "name": tool.name if hasattr(tool, 'name') else str(tool),
            "description": tool.description if hasattr(tool, 'description') else "No description",
        }
        if hasattr(tool, 'args_schema'):
            tool_info["args_schema"] = (
                tool.args_schema if isinstance(tool.args_schema, dict)
                else str(tool.args_schema)
            )
        tools_info.append(tool_info)

    return tools_info


async def _invoke_tool_with_timeout(tool, args, timeout=10, retries=2):
    """带超时和重试机制的工具调用
    
    参数:
        tool: 工具实例
        args: 工具参数
        timeout: 单次调用超时时间（秒），默认10秒
        retries: 重试次数，默认2次
    
    返回:
        字典格式的结果：
        - ok: bool，是否成功
        - payload: 成功时的结果
        - error: 失败时的错误信息
        - elapsed_ms: 执行耗时（毫秒）
    """
    attempt = 0
    last_exc = None

    while attempt <= retries:
        attempt += 1
        try:
            start = time.time()
            # 优先使用 ainvoke，否则用 to_thread 包装同步 invoke
            coro = tool.ainvoke(args) if hasattr(tool, "ainvoke") else asyncio.to_thread(tool.invoke, args)
            res = await asyncio.wait_for(coro, timeout=timeout)
            elapsed_ms = int((time.time() - start) * 1000)
            return {"ok": True, "payload": res, "elapsed_ms": elapsed_ms}
        except asyncio.TimeoutError as e:
            last_exc = e
            print(f"  ⏱️  第 {attempt} 次尝试超时（{timeout}s）")
            # 超时时进行指数退避
            if attempt <= retries:
                await asyncio.sleep(0.5 * attempt)
        except Exception as e:
            last_exc = e
            print(f"  ❌ 第 {attempt} 次尝试异常: {type(e).__name__}: {str(e)[:100]}")
            if attempt <= retries:
                await asyncio.sleep(0.2)

    # 所有重试都失败
    return {"ok": False, "error": str(last_exc), "elapsed_ms": 0}


class MCPServerConfig:
    name: str
    server_type: str
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None

