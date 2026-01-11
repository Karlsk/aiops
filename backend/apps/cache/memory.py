"""
内存缓存实现
"""
import time
import asyncio
import fnmatch
from typing import Any, Optional, Dict, List
from ..cache.base import BaseCache


class MemoryCache(BaseCache):
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Dict] = {}
        self._access_times: Dict[str, float] = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
            
        item = self._cache[key]
        
        # 检查是否过期
        if item['expire'] and time.time() > item['expire']:
            await self.delete(key)
            return None
            
        # 更新访问时间
        self._access_times[key] = time.time()
        return item['value']
        
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        # 如果缓存已满，删除最久未访问的项
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict_lru()
            
        expire_time = None
        if expire:
            expire_time = time.time() + expire
            
        self._cache[key] = {
            'value': value,
            'expire': expire_time,
            'created': time.time()
        }
        self._access_times[key] = time.time()
        return True
        
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return True
        return False
        
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if key not in self._cache:
            return False
            
        item = self._cache[key]
        if item['expire'] and time.time() > item['expire']:
            await self.delete(key)
            return False
            
        return True
        
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if key in self._cache:
            self._cache[key]['expire'] = time.time() + seconds
            return True
        return False
        
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if key not in self._cache:
            return -2
            
        item = self._cache[key]
        if not item['expire']:
            return -1
            
        remaining = item['expire'] - time.time()
        return int(remaining) if remaining > 0 else -2
        
    async def clear(self) -> bool:
        """清空所有缓存"""
        self._cache.clear()
        self._access_times.clear()
        return True
        
    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的键列表"""
        if pattern == "*":
            return list(self._cache.keys())
        return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
        
    async def close(self):
        """关闭缓存连接"""
        await self.clear()
        
    async def _evict_lru(self):
        """删除最久未访问的项"""
        if not self._access_times:
            return
            
        # 找到最久未访问的键
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        await self.delete(lru_key)
        
    async def cleanup_expired(self):
        """清理过期的缓存项"""
        current_time = time.time()
        expired_keys = []
        
        for key, item in self._cache.items():
            if item['expire'] and current_time > item['expire']:
                expired_keys.append(key)
                
        for key in expired_keys:
            await self.delete(key)
            
        return len(expired_keys)