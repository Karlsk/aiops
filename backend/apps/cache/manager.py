"""
缓存管理器
"""
from typing import Dict, Optional, Any
from ..utils.config import settings
from ..utils.logger import TerraLogUtil
from .base import BaseCache
from .memory import MemoryCache
from .redis import RedisCache


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.caches: Dict[str, BaseCache] = {}
        self._default_cache: Optional[BaseCache] = None

    async def initialize_default(self):
        """初始化缓存连接"""
        cache_config = settings.get_cache_config()
        cache_type = cache_config.get("type", "memory")

        if cache_type == "memory":
            self._default_cache = MemoryCache(
                max_size=cache_config.get("max_size", 1000)
            )
        elif cache_type == "redis":
            self._default_cache = RedisCache(cache_config, None)
            await self._default_cache.connect()
        else:
            TerraLogUtil.error(f"Unsupported cache type: {cache_type}")
            raise ValueError(f"Unsupported cache type: {cache_type}")

        self.caches["default"] = self._default_cache
        TerraLogUtil.info(f"Initialized default cache: {cache_type}")

    async def initialize(self, name: str, cache_config: Dict[str, Any]):
        cache_type = cache_config.get("type", "memory")
        if cache_type == "memory":
            cache = MemoryCache(
                max_size=cache_config.get("max_size", 1000)
            )
        elif cache_type == "redis":
            cache = RedisCache(cache_config, None)
            await cache.connect()
        else:
            TerraLogUtil.error(f"Unsupported cache type: {cache_type}")
            raise ValueError(f"Unsupported cache type: {cache_type}")

        self.caches[name] = cache
        if name == "default":
            self._default_cache = cache
        TerraLogUtil.info(f"Initialized cache connection: {name}")

    async def close(self):
        """关闭所有缓存连接"""
        for name, cache in self.caches.items():
            await cache.close()
            TerraLogUtil.info(f"Closed cache connection: {name}")

    def get_cache(self, name: str = "default") -> Optional[BaseCache]:
        """获取缓存实例"""
        return self.caches.get(name)

    @property
    def default(self) -> Optional[BaseCache]:
        """获取默认缓存实例"""
        return self._default_cache

    # 便捷方法，直接操作默认缓存
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self._default_cache:
            return await self._default_cache.get(key)
        return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        if self._default_cache:
            return await self._default_cache.set(key, value, expire)
        return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self._default_cache:
            return await self._default_cache.delete(key)
        return False

    async def clear(self) -> bool:
        """清空默认缓存"""
        if self._default_cache:
            return await self._default_cache.clear()
        return False
