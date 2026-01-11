"""
MCP (Model Context Protocol) 服务器管理路由
支持添加、削除、获取 MCP 服务器配置，以及获取工具列表和调用工具功能
"""
from typing import Dict, Any
from fastapi import HTTPException, Depends
from pydantic import BaseModel

from apps.service.mcp_service import MCPServerService
from apps.models.service.api_schema import MCPServerUpdate, MCPServerResponse, MCPServerCreate

from apps.workflow.client.mcp_client import MCPClientManager, get_tools_info
from apps.utils.deps import SessionDep
from apps.utils.logger import TerraLogUtil

from fastapi import APIRouter

router = APIRouter(tags=["mcp"], prefix="/mcp")


class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_name: str
    arguments: Dict[str, Any]


def get_mcp_service():
    return MCPServerService()


@router.post("/servers", response_model=MCPServerResponse)
async def add_mcp_server(
        server_config: MCPServerCreate,
        session: SessionDep,
        service: MCPServerService = Depends(get_mcp_service),
):
    try:
        server = await service.create_server(session, server_config)
        MCPClientManager().reset()  # 重置客户端以加载新配置
        return server
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error adding MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/servers/{server_id}")
async def delete_mcp_server(
        server_id: int,
        session: SessionDep,
        service: MCPServerService = Depends(get_mcp_service),
):
    """删除 MCP 服务器
            
    Args:
        server_id (int): 要删除的服务器 ID
    """
    try:
        ser_name = await service.delete_server(session, server_id)
        MCPClientManager().reset()  # 重置客户端以加载新配置
        return {
            "success": True,
            "message": f"Successfully removed MCP server {ser_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error removing MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers", response_model=Dict[str, Any])
async def list_mcp_servers(
        session: SessionDep,
        service: MCPServerService = Depends(get_mcp_service),
):
    """获取所有 MCP 服务器配置"""
    try:
        servers = await service.get_all_servers(session)
        return {
            "success": True,
            "total": len(servers),
            "servers": servers
        }
    except Exception as e:
        TerraLogUtil.error(f"Error fetching MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server_by_id(
        server_id: int,
        session: SessionDep,
        service: MCPServerService = Depends(get_mcp_service),
):
    """根据 ID 获取 MCP 服务器配置"""
    try:
        server = await service.get_server_by_id(session, server_id)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server with ID '{server_id}' not found")
        return server
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error fetching MCP server by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/servers/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
        server_id: int,
        update_data: MCPServerUpdate,
        session: SessionDep,
        service: MCPServerService = Depends(get_mcp_service)
):
    
    try:
        server = await service.update_server(session, server_id, update_data)
        MCPClientManager().reset()  # 重置客户端以加载新配置
        return server
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error updating MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{server_id}/tools", response_model=Dict[str, Any])
async def get_available_tools(
    server_id: int,
    session: SessionDep,
    service: MCPServerService = Depends(get_mcp_service),
):
    try:
        server = await service.get_server_by_id(session, server_id)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server with ID '{server_id}' not found")
        # 构建单个服务器配置
        server_configs = {
            server.name: {
                "url": server.url,
                "transport": server.transport
            }
        }
        manager = MCPClientManager()
        tools = await manager.get_tools(server_configs)
        tools_info = get_tools_info(tools)
        
        return {
            "success": True,
            "server_id": server_id,
            "server_name": server.name,
            "total": len(tools_info),
            "tools": tools_info
        }
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error fetching available tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{server_id}/tools/call", response_model=Dict[str, Any])
async def call_tool(
    server_id: int,
    request: ToolCallRequest,
    session: SessionDep,
    service: MCPServerService = Depends(get_mcp_service)
):
    """调用指定 MCP 服务器上的工具
            
    Args:
        server_id: MCP 服务器 ID（必需）
        request: 工具调用请求 (tool_name, arguments)
            
    Returns:
        工具执行结果
    """
    try:
        server = await service.get_server_by_id(session, server_id)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server with ID '{server_id}' not found")
        server_configs = {
            server.name: {
                "url": server.url,
                "transport": server.transport
            }
        }
        manager = MCPClientManager()
        result = await manager.call_tool(server_configs, request.tool_name, request.arguments)
        return {
            "success": True,
            "server_id": server_id,
            "server_name": server.name,
            "tool_name": request.tool_name,
            "result": result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        TerraLogUtil.error(f"Error calling tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
