"""
缓存基础接口
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, List
import asyncio


class BaseCache(ABC):
    """缓存基础接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
        
    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass
        
    @abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        pass
        
    @abstractmethod
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        pass
        
    @abstractmethod
    async def clear(self) -> bool:
        """清空所有缓存"""
        pass
        
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的键列表"""
        pass
        
    @abstractmethod
    async def close(self):
        """关闭缓存连接"""
        pass
        
    # 便捷方法
    async def get_or_set(self, key: str, func, expire: Optional[int] = None) -> Any:
        """获取缓存，如果不存在则执行函数并设置缓存"""
        value = await self.get(key)
        if value is None:
            if asyncio.iscoroutinefunction(func):
                value = await func()
            else:
                value = func()
            await self.set(key, value, expire)
        return value
        
    async def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        current = await self.get(key) or 0
        new_value = int(current) + amount
        await self.set(key, new_value)
        return new_value
        
    async def decrement(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        return await self.increment(key, -amount)