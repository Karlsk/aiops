import ipaddress
from datetime import datetime
from fastapi import HTTPException
from sqlmodel import Session
from sqlmodel import select, delete

from typing import Optional, Dict, Any, List
import re

from apps.models.service.graph_position_model import GraphNodePosition
from apps.models.service.topology_snapshot_model import TopologySnapshotDBModel
from apps.utils.deps import GraphDatabaseSessionDep
from apps.utils.logger import TerraLogUtil
from apps.models.service.sdn_models import SDNController, SDNControllerType, SDNControllerStatus, TopologySnapshot
from apps.models.service.api_schema import SDNControllerCreate, SDNControllerUpdate, ApiResponse
from apps.models.service.sdn_controller_model import SDNControllerDBModel
from apps.rca.collector.sdn_collector import sdn_collector_manager
from apps.service.graph_database_service import GraphDatabaseService


class SDNControllerService:
    def __init__(self):
        self.graph_database_service = GraphDatabaseService()

    async def create_controller(self, session: Session, controller_data: SDNControllerCreate) -> SDNController:
        """创建SDN控制器配置"""
        try:
            controller_dict = controller_data.model_dump()
            await self._validate_controller_data(controller_dict, is_create=True)
            await self._check_controller_type_exists(session, controller_dict["type"])
            # 检查控制器名称是否已存在
            name = controller_dict.get("name")
            if name:
                await self._check_controller_name_exists(session, name)
            # 检查控制器主机地址和端口是否已存在
            host = controller_dict.get("host")
            port = controller_dict.get("port")
            if host and port:
                await self._check_controller_host_port_exists(session, host, port)
            db_controller = SDNControllerDBModel()
            db_controller.name = controller_dict.get("name")
            db_controller.type = controller_dict.get("type")
            db_controller.host = controller_dict.get("host")
            db_controller.port = controller_dict.get("port")
            db_controller.username = controller_dict.get("username")
            db_controller.password = controller_dict.get("password")
            db_controller.api_token = controller_dict.get("api_token")
            db_controller.config = controller_dict.get("config")
            db_controller.status = controller_dict.get("status", SDNControllerStatus.UNKNOWN)
            db_controller.config = controller_dict.get("config", {})
            session.add(db_controller)
            sdn_collector_manager.register_collector(controller_dict["type"], controller_dict)
            session.commit()
            session.refresh(db_controller)
            return SDNController(**db_controller.to_dict(include_sensitive=True))
        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Error creating SDN controller: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create SDN controller")

    async def get_controller(self, session: Session, controller_id: int) -> Optional[SDNController]:
        """获取SDN控制器配置"""
        try:
            result = session.execute(
                select(SDNControllerDBModel).where(SDNControllerDBModel.id == controller_id)
            )
            db_controller = result.scalar_one_or_none()
            if db_controller:
                return SDNController(**db_controller.to_dict(include_sensitive=True))
            return None
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller by ID: {str(e)}")
            return None

    async def get_controller_by_name(self, session: Session, name: str):
        try:
            result = session.execute(
                select(SDNControllerDBModel).where(SDNControllerDBModel.name == name)
            )
            db_controller = result.scalar_one_or_none()
            if db_controller:
                return SDNController(**db_controller.to_dict(include_sensitive=True))
            return None
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller by name: {str(e)}")
            return None

    async def get_controller_by_host_port(self, session: Session, host: str, port: int):
        try:
            result = session.execute(
                select(SDNControllerDBModel).where(
                    SDNControllerDBModel.host == host,
                    SDNControllerDBModel.port == port
                )
            )
            db_controller = result.scalar_one_or_none()
            if db_controller:
                return SDNController(**db_controller.to_dict(include_sensitive=True))
            return None
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller by host and port: {str(e)}")
            return None

    async def get_controller_by_type(self, session: Session, type: str):
        try:
            result = session.execute(
                select(SDNControllerDBModel).where(
                    SDNControllerDBModel.type == type,
                )
            )
            db_controller = result.scalar_one_or_none()
            if db_controller:
                return SDNController(**db_controller.to_dict(include_sensitive=True))
            return None
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller by type: {str(e)}")
            return None

    async def list_controllers(self, session: Session) -> List[SDNController]:
        """列出所有SDN控制器配置"""
        try:
            result = session.execute(select(SDNControllerDBModel))
            db_controllers = result.scalars().all()
            controllers = [
                SDNController(**db_controller.to_dict(include_sensitive=True))
                for db_controller in db_controllers
            ]
            return controllers
        except Exception as e:
            TerraLogUtil.error(f"Error listing SDN controllers: {str(e)}")
            return []

    async def update_controller(self, session: Session, controller_id: int, update_data: SDNControllerUpdate) -> \
            Optional[SDNController]:
        """更新SDN控制器配置"""
        try:
            # 检查控制器是否存在
            existing_controller = await self.get_controller(session, controller_id)
            if not existing_controller:
                raise HTTPException(status_code=404, detail="Controller not found")
            update_dict = update_data.model_dump(exclude_unset=True)
            # 参数校验
            await self._validate_controller_data(update_dict, is_create=False)
            # 检查名称是否冲突
            if "name" in update_dict and update_dict["name"] != existing_controller.name:
                await self._check_controller_name_exists(session, update_dict["name"], exclude_id=controller_id)
            # 检查主机地址和端口是否冲突
            new_host = update_dict.get("host", existing_controller.host)
            new_port = update_dict.get("port", existing_controller.port)
            if (new_host != existing_controller.host) or (new_port != existing_controller.port):
                await self._check_controller_host_port_exists(session, new_host, new_port, exclude_id=controller_id)

            # 获取数据库模型进行更新
            result = session.execute(
                select(SDNControllerDBModel).where(SDNControllerDBModel.id == controller_id)
            )
            db_controller = result.scalar_one_or_none()
            if not db_controller:
                raise HTTPException(status_code=404, detail="Controller not found")

            # 执行更新
            for key, value in update_dict.items():
                if hasattr(db_controller, key) and value is not None:
                    setattr(db_controller, key, value)

            session.commit()
            session.refresh(db_controller)
            return SDNController(**db_controller.to_dict(include_sensitive=True))
        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Error updating SDN controller: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update SDN controller")

    async def delete_controller(self, session: Session, controller_id: int) -> bool:
        """删除SDN控制器配置"""
        try:
            existing_controller = await self.get_controller(session, controller_id)
            if existing_controller:
                stmt = delete(SDNControllerDBModel).where(SDNControllerDBModel.id == controller_id)
                session.execute(stmt)
                session.commit()
                return True
            else:
                raise HTTPException(status_code=404, detail="Controller not found")

        except HTTPException:
            raise
        except Exception as e:
            TerraLogUtil.error(f"Error deleting SDN controller: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete SDN controller")

    async def test_controller_connection(self, session: Session, controller_id: int) -> Dict[str, Any]:
        """测试SDN控制器连接"""
        try:
            controller = await self.get_controller(session, controller_id)
            if not controller:
                return {"status": "error", "message": "Controller not found"}

            collector = sdn_collector_manager.get_collector(controller.type)
            if not collector:
                return {"status": "error", "message": "Unsupported controller type"}
            result = await collector.test_connection(controller)
            if result.get("connected", False):
                return {"status": "success", "data": result}
            else:
                return {"status": "error", "message": result}
        except Exception as e:
            TerraLogUtil.error(f"Error testing SDN controller connection: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def update_controller_status(self, session: Session, controller_id: int, new_status: SDNControllerStatus) -> \
    Optional[SDNController]:
        """
        更新SDN控制器状态
        
        Args:
            session: 数据库会话
            controller_id: 控制器ID
            new_status: 新状态
            
        Returns:
            更新后的控制器信息，如果控制器不存在则返回None
        """
        try:
            # 获取数据库模型
            result = session.execute(
                select(SDNControllerDBModel).where(SDNControllerDBModel.id == controller_id)
            )
            db_controller = result.scalar_one_or_none()

            if not db_controller:
                TerraLogUtil.warning(f"Controller with ID {controller_id} not found")
                return None

            # 只有当状态不同时才更新
            if db_controller.status != new_status.value:
                old_status = db_controller.status
                db_controller.status = new_status.value
                session.commit()
                session.refresh(db_controller)
                TerraLogUtil.info(f"Controller {controller_id} status updated from {old_status} to {new_status.value}")
            else:
                TerraLogUtil.debug(f"Controller {controller_id} status is already {new_status.value}, no update needed")

            return SDNController(**db_controller.to_dict(include_sensitive=True))
        except Exception as e:
            TerraLogUtil.error(f"Error updating controller status: {str(e)}")
            session.rollback()
            return None

    async def get_topology(self, session: Session, controller_id: int) -> Dict[str, Any]:
        """获取SDN控制器网络拓扑"""
        try:
            controller = await self.get_controller(session, controller_id)
            if not controller:
                return {"status": "error", "message": "Controller not found"}

            collector = sdn_collector_manager.get_collector(controller.type)
            if not collector:
                return {"status": "error", "message": "Unsupported controller type"}

            topology = await collector.get_topology(controller)
            return {"status": "success", "data": topology}
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller topology: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def sync_topology(self, session: Session, graph_session: GraphDatabaseSessionDep, controller_id: int) -> Dict[str, Any]:
        """同步网络拓扑"""
        try:
            controller = await self.get_controller(session, controller_id)
            if not controller:
                return {"status": "error", "message": "Controller not found"}

            collector = sdn_collector_manager.get_collector(controller.type)
            if not collector:
                return {"status": "error", "message": "Unsupported controller type"}

            topology = await collector.get_topology(controller)
            nodes = topology.get("nodes", [])
            links = topology.get("links", [])
            timestamp = topology.get("timestamp", datetime.now().isoformat())
            TerraLogUtil.info(f"Syncing topology from controller {controller.name}:  {len(nodes)} nodes, {len(links)} links at {timestamp}")
            TerraLogUtil.info(f"nodes: {nodes}")
            TerraLogUtil.info(f"links: {links}")

            # 生成数据库名称，使用时间戳替换特殊字符
            snapshot_time_str = timestamp.replace(':', '').replace('-', '').replace('.', '').replace('T', '_')
            database_name = f"topology_snapshot_{snapshot_time_str}"

            # 创建 Neo4j 数据库并保存拓扑
            await self.graph_database_service.create_database(session, name=database_name)
            await self.graph_database_service.save_topology_to_database(
                session=session,
                graph_helper=graph_session,
                database_name=database_name,
                nodes=nodes,
                links=links
            )

            db_snapshot = TopologySnapshotDBModel(
                controller_id=controller_id,
                database_name=database_name,
                snapshot_time=datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if isinstance(timestamp,
                                                                                                     str) else timestamp,
                node_count=len(nodes),
                link_count=len(links),
                description=f"Topology snapshot from controller {controller.name}",
                extra_metadata={
                    "controller_type": controller.type,
                    "controller_name": controller.name
                }
            )
            session.add(db_snapshot)
            session.commit()
            session.refresh(db_snapshot)

            return {
                "status": "success",
                "data": {
                    "topology": topology,
                    "snapshot": db_snapshot.model_dump()
                }
            }
        except Exception as e:
            TerraLogUtil.error(f"Error syncing SDN controller topology: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def list_snapshots(self, session: Session, controller_id: Optional[int] = None) -> List[TopologySnapshot]:
        """列出拓扑快照"""
        try:
            if controller_id:
                stmt = select(TopologySnapshotDBModel).where(
                    TopologySnapshotDBModel.controller_id == controller_id
                ).order_by(TopologySnapshotDBModel.snapshot_time.desc())
            else:
                stmt = select(TopologySnapshotDBModel).order_by(TopologySnapshotDBModel.snapshot_time.desc())
            result = session.execute(stmt)
            db_snapshots = result.scalars().all()
            snapshots = [TopologySnapshot(**db_snapshot.model_dump()) for db_snapshot in db_snapshots]
            return snapshots
        except Exception as e:
            TerraLogUtil.error(f"Error listing topology snapshots: {str(e)}")
            return []

    async def get_snapshot(self, session: Session, snapshot_id: int) -> Optional[TopologySnapshot]:
        """获取拓扑快照"""
        try:
            result = session.execute(
                select(TopologySnapshotDBModel).where(TopologySnapshotDBModel.id == snapshot_id)
            )
            db_snapshot = result.scalar_one_or_none()
            if db_snapshot:
                return TopologySnapshot(**db_snapshot.model_dump())
            return None
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving topology snapshot by ID: {str(e)}")
            return None

    async def delete_snapshot(self, session: Session, snapshot_id: int) -> Dict[str, Any]:
        """删除拓扑快照"""
        try:
            snapshot = await self.get_snapshot(session, snapshot_id)
            if not snapshot:
                return {"status": "error", "message": "Snapshot not found"}

            # 删除 Neo4j 数据库
            await self.graph_database_service.delete_topology_to_database(snapshot.database_name)
            await self.graph_database_service.delete_database(snapshot.database_name)

            # 删除数据库记录
            result = session.execute(
                select(TopologySnapshotDBModel).where(TopologySnapshotDBModel.id == snapshot_id)
            )
            db_snapshot = result.scalar_one_or_none()
            if db_snapshot:
                session.delete(db_snapshot)

            # 删除所有相关的节点位置记录（可能有多条）
            result2 = session.execute(
                select(GraphNodePosition).where(GraphNodePosition.database_name == snapshot.database_name)
            )
            db_positions = result2.scalars().all()
            for db_position in db_positions:
                session.delete(db_position)

            session.commit()

            return {"status": "success", "message": "Snapshot deleted successfully"}
        except Exception as e:
            TerraLogUtil.error(f"Error deleting topology snapshot: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def delete_snapshots_by_controller(self, session: Session, controller_id: int) -> Dict[str, Any]:
        """删除指定控制器的所有拓扑快照"""
        try:
            snapshots = await self.list_snapshots(session, controller_id=controller_id)
            deleted_count = 0
            errors = []
            for snapshot in snapshots:
                if snapshot.id is not None:
                    result = await self.delete_snapshot(session, snapshot.id)
                    if result["status"] == "success":
                        deleted_count += 1
                    else:
                        errors.append(f"Failed to delete snapshot {snapshot.id}: {result['message']}")
            if errors:
                return {
                    "status": "partial",
                    "message": f"Deleted {deleted_count} snapshots with {len(errors)} errors",
                    "errors": errors
                }
            else:
                return {
                    "status": "success",
                    "message": f"Deleted {deleted_count} snapshots successfully"
                }
        except Exception as e:
            TerraLogUtil.error(f"Error deleting snapshots by controller: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_monitoring_data(self, session: Session, controller_id: int, metric_name: Optional[str] = None) -> \
            Dict[str, Any]:
        """获取SDN控制器监控数据"""
        try:
            controller = await self.get_controller(session, controller_id)
            if not controller:
                return {"status": "error", "message": "Controller not found"}

            collector = sdn_collector_manager.get_collector(controller.type)
            if not collector:
                return {"status": "error", "message": "Unsupported controller type"}

            monitoring_data = await collector.get_monitoring_data(controller, metric_name)
            return {"status": "success", "data": monitoring_data}
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller monitoring data: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_logs(self, session: Session, controller_id: int, level: Optional[str] = None, limit: int = 100) -> \
            Dict[str, Any]:
        """获取SDN控制器日志"""
        try:
            controller = await self.get_controller(session, controller_id)
            if not controller:
                return {"status": "error", "message": "Controller not found"}

            collector = sdn_collector_manager.get_collector(controller.type)
            if not collector:
                return {"status": "error", "message": "Unsupported controller type"}

            logs = await collector.get_logs(controller, level, limit)
            return {"status": "success", "data": logs}
        except Exception as e:
            TerraLogUtil.error(f"Error retrieving SDN controller logs: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _validate_controller_data(self, data: Dict[str, Any], is_create: bool = True) -> None:
        """校验控制器数据"""
        if is_create:
            # 创建时的必填字段检查
            required_fields = ["name", "type", "host", "port"]
            for field in required_fields:
                if field not in data or data[field] is None:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                if isinstance(data[field], str) and not data[field].strip():
                    raise HTTPException(status_code=400, detail=f"Field '{field}' cannot be empty")

        # 名称校验
        if "name" in data:
            name = data["name"]
            if not isinstance(name, str):
                raise HTTPException(status_code=400, detail="Controller name must be a string")
            if not name.strip():
                raise HTTPException(status_code=400, detail="Controller name cannot be empty")
            if len(name.strip()) > 100:
                raise HTTPException(status_code=400, detail="Controller name cannot exceed 100 characters")
            # 名称只能包含字母、数字、下划线、连字符
            if not re.match(r'^[a-zA-Z0-9_-]+$', name.strip()):
                raise HTTPException(status_code=400,
                                    detail="Controller name can only contain letters, numbers, underscores, and hyphens")

        # 控制器类型校验
        if "type" in data:
            controller_type = data["type"]
            if not isinstance(controller_type, str):
                raise HTTPException(status_code=400, detail="Controller type must be a string")
            try:
                SDNControllerType(controller_type)
            except ValueError:
                valid_types = [t.value for t in SDNControllerType]
                raise HTTPException(status_code=400, detail=f"Invalid controller type. Valid types: {valid_types}")

        # 主机地址校验
        if "host" in data:
            host = data["host"]
            if not isinstance(host, str):
                raise HTTPException(status_code=400, detail="Host must be a string")
            if not host.strip():
                raise HTTPException(status_code=400, detail="Host cannot be empty")

            # 校验IP地址或域名格式
            host = host.strip()
            if not self._is_valid_host(host):
                raise HTTPException(status_code=400,
                                    detail="Invalid host format. Must be a valid IP address or domain name")

        # 端口校验
        if "port" in data:
            port = data["port"]
            if not isinstance(port, int):
                raise HTTPException(status_code=400, detail="Port must be an integer")
            if not (1 <= port <= 65535):
                raise HTTPException(status_code=400, detail="Port must be between 1 and 65535")

        # 认证信息校验 - 必须配置 username/password 或 api_token
        has_username_password = data.get("username") and data.get("password")
        has_api_token = data.get("api_token")

        if is_create:
            # 创建时必须提供其中一种认证方式
            if not has_username_password and not has_api_token:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide either username/password or api_token for authentication"
                )

        # 如果提供了两种认证方式，给出警告（但不阻止）
        if has_username_password and has_api_token:
            # 可以选择记录警告日志或报错
            pass

        # 认证信息校验
        if "username" in data and data["username"] is not None:
            username = data["username"]
            if not isinstance(username, str):
                raise HTTPException(status_code=400, detail="Username must be a string")
            if len(username.strip()) > 50:
                raise HTTPException(status_code=400, detail="Username cannot exceed 50 characters")

        if "password" in data and data["password"] is not None:
            password = data["password"]
            if not isinstance(password, str):
                raise HTTPException(status_code=400, detail="Password must be a string")
            if len(password) > 200:
                raise HTTPException(status_code=400, detail="Password cannot exceed 200 characters")

        if "api_token" in data and data["api_token"] is not None:
            api_token = data["api_token"]
            if not isinstance(api_token, str):
                raise HTTPException(status_code=400, detail="API token must be a string")
            if len(api_token) > 500:
                raise HTTPException(status_code=400, detail="API token cannot exceed 500 characters")

        # 配置信息校验
        if "config" in data and data["config"] is not None:
            config = data["config"]
            if not isinstance(config, dict):
                raise HTTPException(status_code=400, detail="Config must be a dictionary")

        # 状态校验（仅更新时）
        if "status" in data:
            status = data["status"]
            if not isinstance(status, str):
                raise HTTPException(status_code=400, detail="Status must be a string")
            try:
                SDNControllerStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in SDNControllerStatus]
                raise HTTPException(status_code=400, detail=f"Invalid status. Valid statuses: {valid_statuses}")

    def _is_valid_host(self, host: str) -> bool:
        """校验主机地址格式"""
        # 尝试解析为IP地址
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            pass

        # 校验域名格式
        if self._is_valid_domain(host):
            return True

        return False

    def _is_valid_domain(self, domain: str) -> bool:
        """校验域名格式"""
        if len(domain) > 253:
            return False

        # 域名正则表达式
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        return bool(domain_pattern.match(domain))

    async def _check_controller_name_exists(self, session: Session, name: str,
                                            exclude_id: Optional[int] = None) -> None:
        """检查控制器名称是否已存在"""
        existing = await self.get_controller_by_name(session, name)
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise HTTPException(status_code=409, detail=f"Controller with name '{name}' already exists")

    async def _check_controller_host_port_exists(self, session: Session, host: str, port: int,
                                                 exclude_id: Optional[int] = None) -> None:
        """检查控制器主机地址和端口是否已存在"""
        existing = await self.get_controller_by_host_port(session, host, port)
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise HTTPException(status_code=409, detail=f"Controller with host '{host}:{port}' already exists")

    async def _check_controller_type_exists(self, session: Session, type: str,
                                            exclude_id: Optional[int] = None) -> None:
        """检查控制器类型是否已存在"""
        existing = await self.get_controller_by_type(session, type)
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise HTTPException(status_code=409, detail=f"Controller with type '{type}' already exists")
