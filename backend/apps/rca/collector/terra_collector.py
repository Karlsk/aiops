"""
OpenDaylight控制器数据收集器
"""
import time, threading
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_collector import BaseSDNCollector
from apps.models.service.sdn_models import SDNController, MonitoringData, LogEntry
from apps.utils.http_request import do_post, authorized_post, authorized_get, do_get
from apps.utils.logger import TerraLogUtil


class TerraCollector(BaseSDNCollector):
    """OpenDaylight控制器数据收集器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("terra", config)
        self.JUMPER_BASE_URL = f"https://{self.controller_config.get('host', "192.168.118.176")}:{self.controller_config.get('port', 8080)}"
        self.User = self.controller_config.get("username", "zhangsan")
        self.Password = self.controller_config.get("password", "tgb.258")
        self._token = None
        self._token_expire_time = 0  # 可选，如果你支持 expires_in

    def get_auth_token(self, force_refresh=False):
        if not force_refresh and self._token and time.time() < self._token_expire_time:
            return self._token

        url = (f"{self.JUMPER_BASE_URL}/oauth/token?client_id=SampleClientId"
               f"&client_secret={self.Password}&grant_type=password"
               f"&scope=user_info&username={self.User}&password={self.Password}")
        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer your_token"  # 如果需要 Token 验证
        }
        response = do_post(url, {}, headers)
        if response.status_code != 200:
            TerraLogUtil.error(response)
            return None
        token_data = response.json()
        self._token = token_data["access_token"]
        self._token_expire_time = time.time() + token_data.get("expires_in", 3600) - 60  # 提前60秒过期
        return self._token

    async def test_connection(self, controller: SDNController = None) -> Dict[str, Any]:
        """测试与OpenDaylight控制器的连接"""
        url = f"{self.JUMPER_BASE_URL}/gateway/version"
        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer your_token"  # 如果需要 Token 验证
        }
        response = do_get(url, {}, headers)
        if response.status_code != 200:
            TerraLogUtil.error(response)
            return {"connected": False, "version": "unknown"}
        version = response.json().get("terra-no", {}).get("version", "unknown")
        return {"connected": True, "version": version}

    async def sync_device(self):
        device_infos = []
        try:
            url = self.JUMPER_BASE_URL + "/api/no/config/terra-pe:peInfos/peInfos"
            headers = {
                "Content-Type": "application/json",
                # "Authorization": "Bearer your_token"  # 如果需要 Token 验证
            }
            response = authorized_get(url, headers, self.get_auth_token)
            if response.status_code != 200:
                TerraLogUtil.error(response)
                return None
            devices = response.json()["peInfo"]
            TerraLogUtil.debug(devices)
            for device in devices:
                device_name = device.get("name", "")
                device_name_alias = device.get("pe-alias", "")
                vendor = device.get("vendor-id", "")
                platform_id = device.get("platform-id", "")
                node_type = device.get("node-type", "")
                management_ip = device.get("management-ip", "")
                device_info = {
                    "device_name": device_name,
                    "device_name_alias": device_name_alias,
                    "vendor": vendor,
                    "series": platform_id,
                    "node_type": node_type,
                    "management_ip": management_ip
                }
                device_infos.append(device_info)
            return device_infos
        except Exception as e:
            TerraLogUtil.error(f"同步设备失败: {e}")
            return None

    async def sync_links(self):
        link_infos = []
        try:
            url = self.JUMPER_BASE_URL + "/api/sr/config/network-topology:network-topology/topology/linksInfo"
            headers = {
                "Content-Type": "application/json",
                # "Authorization": "Bearer your_token"  # 如果需要 Token 验证
            }
            response = authorized_get(url, headers, self.get_auth_token)
            if response.status_code != 200:
                TerraLogUtil.error(response)
                return None
            links = response.json()
            TerraLogUtil.debug(links)
            for link in links:
                source = link.get("source", {})
                destination = link.get("destination", {})
                link_id = link.get("link-id", "")
                status = link.get("link-status", "")
                source_ip = source.get("source-ip", "")
                dest_ip = destination.get("dest-ip", "")
                link_info = {
                    "link_id": link_id,
                    "status": status,
                    "source_node": source.get("source-node", ""),
                    "source_tp": source.get("source-tp", ""),
                    "dest_node": destination.get("dest-node", ""),
                    "dest_tp": destination.get("dest-tp", ""),
                    "source_ip": source_ip,
                    "dest_ip": dest_ip
                }
                link_infos.append(link_info)
            return link_infos
        except Exception as e:
            TerraLogUtil.error(f"同步链路失败: {e}")
            return None

    async def get_topology(self, controller: SDNController = None) -> Dict[str, Any]:
        """获取OpenDaylight网络拓扑"""
        nodes = await self.sync_device()
        links = await self.sync_links()
        now = datetime.now().isoformat()
        if nodes is not None and links is not None:
            TerraLogUtil.info(f"成功同步拓扑：{len(nodes)} 个节点，{len(links)} 条链路")
            return {
                "nodes": nodes,
                "links": links,
                "message": f"success sync {len(nodes)} nodes and {len(links)} links",
                "timestamp": now
            }
        else:
            return {
                "nodes": [],
                "links": [],
                "message": "failed to sync topology",
                "timestamp": now
            }

    async def get_monitoring_data(self, controller: SDNController, metric_name: Optional[str] = None) -> List[
        MonitoringData]:
        """获取OpenDaylight监控数据"""
        # TODO: 实现监控数据获取
        # 可能需要访问多个API端点获取不同的监控指标
        return []

    async def get_logs(self, controller: SDNController, level: Optional[str] = None, limit: int = 100) -> List[
        LogEntry]:
        """获取OpenDaylight日志"""
        # TODO: 实现日志获取
        # 可能需要通过SSH或日志API获取
        return []

    async def get_flows(self, controller: SDNController, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取OpenDaylight流表"""
        # TODO: 实现流表获取
        # API: /restconf/operational/opendaylight-inventory:nodes/node/{node-id}/flow-node-inventory:table/{table-id}/flow/{flow-id}
        return []

    async def get_statistics(self, controller: SDNController) -> Dict[str, Any]:
        """获取OpenDaylight统计信息"""
        # TODO: 实现统计信息获取
        return {
            "node_count": 0,
            "link_count": 0,
            "flow_count": 0,
            "timestamp": datetime.now().isoformat()
        }
