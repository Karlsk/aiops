"""
MCP 服务器配置示例
展示如何配置不同类型的 MCP 服务器
"""

import os
from typing import List
from .mcp_client import MCPServerConfig


def get_existing_service_configs() -> List[MCPServerConfig]:
    """获取现有 MCP 服务的配置"""
    configs = []
    
    # 从环境变量读取现有服务配置
    service_type = os.getenv("MCP_EXISTING_SERVICE_TYPE", "sse")
    
    if service_type == "sse":
        url = os.getenv("MCP_EXISTING_SERVICE_URL", "http://localhost:8080/sse")
        timeout = int(os.getenv("MCP_EXISTING_SERVICE_TIMEOUT", "30"))
        
        configs.append(MCPServerConfig(
            name="existing_service",
            server_type="sse", 
            url=url,
            timeout=timeout
        ))
        
    elif service_type == "stdio":
        command = os.getenv("MCP_EXISTING_SERVICE_COMMAND", "python")
        args_str = os.getenv("MCP_EXISTING_SERVICE_ARGS", "")
        args = args_str.split(",") if args_str else []
        working_dir = os.getenv("MCP_EXISTING_SERVICE_WORKING_DIR")
        
        env_vars = {}
        if working_dir:
            env_vars["PYTHONPATH"] = working_dir
            
        configs.append(MCPServerConfig(
            name="existing_service",
            server_type="stdio",
            command=command,
            args=args,
            env=env_vars
        ))
    
    # 支持多个服务配置
    for i in range(1, 10):  # 支持最多9个额外服务
        name_key = f"MCP_SERVICE_{i}_NAME"
        type_key = f"MCP_SERVICE_{i}_TYPE"
        
        if not os.getenv(name_key) or not os.getenv(type_key):
            break
            
        name = os.getenv(name_key)
        svc_type = os.getenv(type_key)
        
        if svc_type == "sse":
            url = os.getenv(f"MCP_SERVICE_{i}_URL")
            timeout = int(os.getenv(f"MCP_SERVICE_{i}_TIMEOUT", "30"))
            
            if url:
                configs.append(MCPServerConfig(
                    name=name,
                    server_type="sse",
                    url=url, 
                    timeout=timeout
                ))
                
        elif svc_type == "stdio":
            command = os.getenv(f"MCP_SERVICE_{i}_COMMAND")
            args_str = os.getenv(f"MCP_SERVICE_{i}_ARGS", "")
            args = args_str.split(",") if args_str else []
            
            if command:
                configs.append(MCPServerConfig(
                    name=name,
                    server_type="stdio",
                    command=command,
                    args=args,
                    env=None
                ))
    
    return configs


def get_development_configs() -> List[MCPServerConfig]:
    """获取开发环境的 MCP 配置"""
    # 开发环境优先使用现有服务
    existing_configs = get_existing_service_configs()
    if existing_configs:
        return existing_configs
    
    # 如果没有现有服务配置，使用默认配置
    return [
        MCPServerConfig(
            name="filesystem",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env=None
        ),
        MCPServerConfig(
            name="memory", 
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
            env=None
        )
    ]


def get_production_configs() -> List[MCPServerConfig]:
    """获取生产环境的 MCP 配置"""
    # 生产环境优先使用现有服务
    existing_configs = get_existing_service_configs()
    if existing_configs:
        return existing_configs
        
    # 生产环境的备用配置
    return [
        MCPServerConfig(
            name="filesystem",
            server_type="stdio", 
            command="/usr/local/bin/mcp-filesystem-server",
            args=["--root", "/app/data"],
            env={"LOG_LEVEL": "INFO"}
        ),
        MCPServerConfig(
            name="database",
            server_type="stdio",
            command="/usr/local/bin/mcp-database-server", 
            args=["--connection", os.getenv("DATABASE_URL", "")],
            env={"LOG_LEVEL": "INFO"}
        ),
        MCPServerConfig(
            name="api_service",
            server_type="sse",
            url=os.getenv("MCP_API_SERVICE_URL", ""),
            timeout=30
        )
    ]


# 根据环境变量选择配置
def get_configs_for_environment() -> List[MCPServerConfig]:
    """根据环境变量获取适当的配置"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return get_production_configs()
    elif env == "development":
        return get_development_configs()
    else:
        # 默认使用现有服务配置
        return get_existing_service_configs()