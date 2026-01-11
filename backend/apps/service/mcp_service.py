from fastapi import HTTPException
from sqlmodel import Session
from typing import Any, Dict, Optional, List

from sqlmodel import select

from apps.models.service.api_schema import MCPServerCreate, MCPServerResponse
from apps.models.service.mcp_server_model import MCPServerDBModel
from apps.models.service.mcp_models import MCPServer


class MCPServerService:

    @staticmethod
    def _validate_server_data(data: Dict[str, Any], is_create: bool = True) -> None:
        """校验服务器数据"""
        if is_create:
            # 创建时的必填字段检查
            required_fields = ["name", "url"]
            for field in required_fields:
                if field not in data or data[field] is None:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                if isinstance(data[field], str) and not data[field].strip():
                    raise HTTPException(status_code=400, detail=f"Field '{field}' cannot be empty")

        # 名称校验
        if "name" in data:
            name = data["name"]
            if not isinstance(name, str):
                raise HTTPException(status_code=400, detail="Server name must be a string")
            if not name.strip():
                raise HTTPException(status_code=400, detail="Server name cannot be empty")
            if len(name.strip()) > 100:
                raise HTTPException(status_code=400, detail="Server name cannot exceed 100 characters")

        # URL 校验
        if "url" in data:
            url = data["url"]
            if not isinstance(url, str):
                raise HTTPException(status_code=400, detail="URL must be a string")
            if not url.strip():
                raise HTTPException(status_code=400, detail="URL cannot be empty")
            if not url.startswith(("http://", "https://")):
                raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

        # 传输方式校验
        if "transport" in data:
            transport = data["transport"]
            if not isinstance(transport, str):
                raise HTTPException(status_code=400, detail="Transport must be a string")
            valid_transports = ["streamable_http", "stdio", "sse"]
            if transport not in valid_transports:
                raise HTTPException(status_code=400, detail=f"Invalid transport. Valid values: {valid_transports}")

        # 描述校验
        if "description" in data and data["description"] is not None:
            description = data["description"]
            if not isinstance(description, str):
                raise HTTPException(status_code=400, detail="Description must be a string")

        # 配置信息校验
        if "config" in data and data["config"] is not None:
            config = data["config"]
            if not isinstance(config, dict):
                raise HTTPException(status_code=400, detail="Config must be a dictionary")

    @staticmethod
    async def get_server_by_name(session: Session, name: str) -> Optional[MCPServer]:
        """根据名称获取 MCP 服务器配置"""
        result = session.execute(
            select(MCPServerDBModel).where(MCPServerDBModel.name == name)
        )
        db_server = result.scalar_one_or_none()
        if db_server:
            return MCPServer(**db_server.model_dump())

        return None

    async def _check_server_name_exists(self, session: Session, name: str, exclude_id: Optional[int] = None) -> None:
        """检查服务器名称是否已存在"""
        existing = await self.get_server_by_name(session, name)
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise HTTPException(status_code=409, detail=f"Server with name '{name}' already exists")

    async def create_server(self, session: Session, server_config: MCPServerCreate) -> MCPServerResponse:
        config_dict = server_config.model_dump()
        self._validate_server_data(config_dict, is_create=True)

        name = config_dict.get("name")
        if name:
            await self._check_server_name_exists(session, name)

        db_server = MCPServerDBModel()
        db_server.name = config_dict.get("name")
        db_server.url = config_dict.get("url")
        db_server.transport = config_dict.get("transport", "streamable_http")
        db_server.description = config_dict.get("description", "")
        db_server.config = config_dict.get("config")
        try:
            session.add(db_server)
            session.commit()
            session.refresh(db_server)

            return MCPServerResponse(**db_server.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create server: {e}")

    async def delete_server(self, session: Session, server_id: int):
        result = session.execute(
            select(MCPServerDBModel).where(MCPServerDBModel.id == server_id)
        )
        db_server: MCPServerDBModel = result.scalar_one_or_none()

        if not db_server:
            raise HTTPException(status_code=404, detail=f"Server with ID '{server_id}' not found")
        try:
            session.delete(db_server)
            session.commit()
            return db_server.name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete server: {e}")

    async def get_all_servers(self, session: Session) -> List[Dict[str, Any]]:
        result = session.execute(select(MCPServerDBModel))
        db_servers = result.scalars().all()
        servers = [MCPServerResponse(**db_server.model_dump()).model_dump() for db_server in db_servers]
        return servers

    async def get_server_by_id(self, session, server_id):
        result = session.execute(
            select(MCPServerDBModel).where(MCPServerDBModel.id == server_id)
        )
        db_server = result.scalar_one_or_none()
        if db_server:
            return MCPServer(**db_server.model_dump())
        return None

    async def update_server(self, session, server_id, update_data):
        existing_server = await self.get_server_by_id(session, server_id)
        if not existing_server:
            raise HTTPException(status_code=404, detail=f"Server with ID '{server_id}' not found")
        
        data_dict = update_data.model_dump()
        self._validate_server_data(data_dict, is_create=False)
        if "name" in data_dict and data_dict["name"] != existing_server.name:
            await self._check_server_name_exists(session, data_dict["name"], exclude_id=server_id)
        try:
            for key, value in data_dict.items():
                if value is not None:
                    setattr(existing_server, key, value)
            session.commit()
            session.refresh(existing_server)
            return MCPServerResponse(**existing_server.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update server: {e}")
