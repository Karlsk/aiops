"""
SDN控制器收集器管理器
"""

from typing import Dict, Optional, List, Any
from .base_collector import BaseSDNCollector
from .opendaylight_collector import OpenDaylightCollector
from .terra_collector import TerraCollector
from apps.models.service.sdn_models import SDNControllerType
from apps.utils.logger import TerraLogUtil


class SDNCollectorManager:
    """SDN控制器收集器管理器"""
    
    def __init__(self):
        self._collectors: Dict[str, BaseSDNCollector] = {}
    
    def get_collector(self, controller_type: str) -> Optional[BaseSDNCollector]:
        """根据控制器类型获取对应的收集器"""
        return self._collectors.get(controller_type, None)
    
    def register_collector(self, controller_type: str, config: Dict[str, Any], force: bool = False) -> None:
        """注册新的收集器
        
        Args:
            controller_type: 控制器类型
            config: 控制器配置
            force: 是否强制重新注册（覆盖已存在的收集器）
        """
        try:
            existing_collector = self._collectors.get(controller_type, None)
            if existing_collector is not None:
                if not force:
                    raise ValueError(f"Collector for type '{controller_type}' is already registered.")
                else:
                    TerraLogUtil.info(f"强制重新注册收集器: {controller_type}")

            collector = SDNFactory.create_collector(controller_type, config)
            self._collectors[controller_type] = collector
            TerraLogUtil.info(f"收集器注册成功: {controller_type}")
        except Exception as e:
            TerraLogUtil.error(f"SDNCollectorManager register_collector error: {e}")
            raise
    
    def unregister_collector(self, controller_type: str) -> None:
        """注销收集器
        
        Args:
            controller_type: 控制器类型
        """
        if controller_type in self._collectors:
            del self._collectors[controller_type]
            TerraLogUtil.info(f"收集器已注销: {controller_type}")
        else:
            TerraLogUtil.warning(f"收集器不存在，无法注销: {controller_type}")
    
    def list_supported_types(self) -> List[str]:
        """获取支持的控制器类型列表"""
        return list(self._collectors.keys())


class SDNFactory:
    """SDN控制器收集器工厂类"""

    @staticmethod
    def create_collector(controller_type: str, config: Dict[str, Any]) -> Optional[BaseSDNCollector]:
        """根据控制器类型创建对应的收集器实例"""
        if controller_type == SDNControllerType.OPENDAYLIGHT.value:
            return OpenDaylightCollector(config)
        elif controller_type == SDNControllerType.TERRA.value:
            return TerraCollector(config)
        else:
            raise ValueError(f"SDNFactory Unsupported SDN controller type: {controller_type}")


# 全局收集器管理器实例
sdn_collector_manager = SDNCollectorManager()