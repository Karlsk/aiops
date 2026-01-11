"""
告警数据收集器
负责解析不同告警系统的webhook数据
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseAlertCollector(ABC):
    """告警收集器基类"""
    
    def __init__(self, system_name: str):
        self.system_name = system_name
    
    @abstractmethod
    def can_handle(self, webhook_data: Dict[str, Any]) -> bool:
        """判断是否能处理该webhook数据"""
        pass
    
    @abstractmethod
    def parse_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析webhook数据为标准格式"""
        pass
    
    @abstractmethod
    def identify_controller(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """从webhook数据中识别控制器标识符（如IP、名称等）"""
        pass


class TickAlertCollector(BaseAlertCollector):
    """Tick告警系统收集器"""
    
    def __init__(self):
        super().__init__("tick")
    
    def can_handle(self, webhook_data: Dict[str, Any]) -> bool:
        """判断是否为Tick系统的数据"""
        return "task" in webhook_data or "level" in webhook_data
    
    def parse_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析Tick告警数据"""
        alert_name = webhook_data.get("name") or webhook_data.get("alert_name", "Unknown Alert")
        severity = self._map_tick_severity(webhook_data.get("level", "medium"))
        message = webhook_data.get("message") or webhook_data.get("details", "")
        
        timestamp_str = webhook_data.get("time") or webhook_data.get("timestamp")
        starts_at = self._parse_timestamp(timestamp_str) if timestamp_str else datetime.now()
        
        tags = webhook_data.get("tags", {})
        data = webhook_data.get("data", {})
        
        return {
            "alert_name": alert_name,
            "severity": severity,
            "message": message,
            "description": webhook_data.get("description", ""),
            "source": "tick",
            "labels": {
                **tags,
                "tick_id": webhook_data.get("id", ""),
                "tick_task": webhook_data.get("task", ""),
            },
            "annotations": {
                "tick_data": data,
                "raw_webhook": webhook_data,
            },
            "starts_at": starts_at,
        }
    
    def identify_controller(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """从Tick数据中识别控制器"""
        tags = webhook_data.get("tags", {})
        
        # 优先级顺序：host -> controller -> device -> task名称
        identifiers = [
            tags.get("host"),
            tags.get("hostname"),
            tags.get("controller"),
            tags.get("sdn_controller"),
            tags.get("device"),
            tags.get("instance"),
        ]
        
        for identifier in identifiers:
            if identifier:
                return str(identifier)
        
        # 从任务名称推断
        task_name = webhook_data.get("task", "")
        if task_name:
            # 例如: "opendaylight_monitor" -> "opendaylight"
            if "_" in task_name:
                return task_name.split("_")[0]
        
        return None
    
    def _map_tick_severity(self, tick_level: str) -> str:
        """映射Tick告警级别"""
        level_mapping = {
            "CRITICAL": "critical",
            "WARNING": "high",
            "INFO": "info",
            "OK": "low",
        }
        return level_mapping.get(str(tick_level).upper(), "medium")
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析Tick时间戳"""
        try:
            if timestamp_str.isdigit():
                return datetime.fromtimestamp(int(timestamp_str))
            else:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.now()


class PrometheusAlertCollector(BaseAlertCollector):
    """Prometheus告警系统收集器"""
    
    def __init__(self):
        super().__init__("prometheus")
    
    def can_handle(self, webhook_data: Dict[str, Any]) -> bool:
        """判断是否为Prometheus系统的数据"""
        return "alerts" in webhook_data or "alertname" in webhook_data
    
    def parse_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析Prometheus告警数据"""
        alerts = webhook_data.get("alerts", [webhook_data])
        first_alert = alerts[0] if alerts else webhook_data
        
        return {
            "alert_name": first_alert.get("alertname", "Unknown Alert"),
            "severity": self._map_prometheus_severity(first_alert.get("severity", "medium")),
            "message": first_alert.get("summary", ""),
            "description": first_alert.get("description", ""),
            "source": "prometheus",
            "labels": first_alert.get("labels", {}),
            "annotations": first_alert.get("annotations", {}),
            "starts_at": self._parse_timestamp(first_alert.get("startsAt")) if first_alert.get("startsAt") else datetime.now(),
        }
    
    def identify_controller(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """从Prometheus数据中识别控制器"""
        alerts = webhook_data.get("alerts", [webhook_data])
        first_alert = alerts[0] if alerts else webhook_data
        
        labels = first_alert.get("labels", {})
        
        identifiers = [
            labels.get("instance"),
            labels.get("host"),
            labels.get("controller"),
            labels.get("job"),
        ]
        
        for identifier in identifiers:
            if identifier:
                return str(identifier)
        
        return None
    
    def _map_prometheus_severity(self, severity: str) -> str:
        """映射Prometheus告警级别"""
        level_mapping = {
            "CRITICAL": "critical",
            "WARNING": "high",
            "INFO": "info",
            "LOW": "low",
        }
        return level_mapping.get(str(severity).upper(), "medium")
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析Prometheus时间戳"""
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.now()


class GenericAlertCollector(BaseAlertCollector):
    """通用告警收集器"""
    
    def __init__(self):
        super().__init__("generic")
    
    def can_handle(self, webhook_data: Dict[str, Any]) -> bool:
        """通用收集器总是可以处理"""
        return True
    
    def parse_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析通用格式数据"""
        alert_name = (webhook_data.get("name") or 
                     webhook_data.get("alert_name") or 
                     webhook_data.get("alertname") or 
                     "Unknown Alert")
        
        severity = (webhook_data.get("severity") or 
                   webhook_data.get("level") or 
                   webhook_data.get("priority") or 
                   "medium")
        
        message = (webhook_data.get("message") or 
                  webhook_data.get("summary") or 
                  webhook_data.get("description") or 
                  "")
        
        return {
            "alert_name": alert_name,
            "severity": self._map_generic_severity(severity),
            "message": message,
            "description": webhook_data.get("description", ""),
            "source": "generic",
            "labels": webhook_data.get("labels") or webhook_data.get("tags", {}),
            "annotations": {"raw_webhook": webhook_data},
            "starts_at": datetime.now(),
        }
    
    def identify_controller(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """从通用数据中识别控制器"""
        # 尝试从多个可能的字段中获取控制器标识
        possible_fields = ["host", "hostname", "controller", "instance", "device", "source"]
        
        for field in possible_fields:
            value = webhook_data.get(field)
            if value:
                return str(value)
        
        # 从labels或tags中查找
        labels = webhook_data.get("labels") or webhook_data.get("tags", {})
        for field in possible_fields:
            value = labels.get(field)
            if value:
                return str(value)
        
        return None
    
    def _map_generic_severity(self, severity: str) -> str:
        """映射通用告警级别"""
        level_mapping = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "WARNING": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "INFO": "info",
        }
        return level_mapping.get(str(severity).upper(), "medium")


class AlertCollectorManager:
    """告警收集器管理器"""
    
    def __init__(self):
        self.collectors = [
            TickAlertCollector(),
            PrometheusAlertCollector(),
            GenericAlertCollector(),  # 通用收集器放在最后
        ]
    
    def get_collector(self, webhook_data: Dict[str, Any]) -> BaseAlertCollector:
        """根据webhook数据获取合适的收集器"""
        for collector in self.collectors:
            if collector.can_handle(webhook_data):
                return collector
        
        # 理论上不会到这里，因为GenericAlertCollector总是返回True
        return self.collectors[-1]
    
    def parse_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析webhook数据"""
        collector = self.get_collector(webhook_data)
        return collector.parse_webhook_data(webhook_data)
    
    def identify_controller(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """识别控制器标识符"""
        collector = self.get_collector(webhook_data)
        return collector.identify_controller(webhook_data)