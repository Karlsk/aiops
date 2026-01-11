"""
Redis缓存实现 - 修复Python 3.12兼容性
"""
import json
import pickle
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as aioredis
from ..cache.base import BaseCache
from ..utils.logger import TerraLogUtil


class RedisCache(BaseCache):
    """Redis缓存实现"""
    
    def __init__(self, config: Dict[str, Any], logger = None):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        self.serializer = config.get('serializer', 'json')  # json, pickle
        
    async def connect(self):
        """连接Redis"""
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 6379)
        db = self.config.get('db', 0)
        password = self.config.get('password')
        
        # 构建Redis URL
        if password:
            redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            redis_url = f"redis://{host}:{port}/{db}"
            
        # 连接配置
        connection_kwargs = {
            'socket_timeout': self.config.get('socket_timeout', 5),
            'socket_connect_timeout': self.config.get('socket_connect_timeout', 5),
            'retry_on_timeout': True,
            'health_check_interval': 30,
            'decode_responses': False  # 我们自己处理序列化
        }
        
        self.redis = aioredis.from_url(redis_url, **connection_kwargs)
        
        # 测试连接
        await self.redis.ping()
        TerraLogUtil.info(f"Connected to Redis: {host}:{port}/{db}")
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            TerraLogUtil.error(f"Redis get error for key {key}: {e}")
            return None
            
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            serialized_value = self._serialize(value)
            if expire:
                await self.redis.setex(key, expire, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            return True
        except Exception as e:
            TerraLogUtil.error(f"Redis set error for key {key}: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            TerraLogUtil.error(f"Redis delete error for key {key}: {e}")
            return False
            
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            TerraLogUtil.error(f"Redis exists error for key {key}: {e}")
            return False
            
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            result = await self.redis.expire(key, seconds)
            return result
        except Exception as e:
            TerraLogUtil.error(f"Redis expire error for key {key}: {e}")
            return False
            
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            TerraLogUtil.error(f"Redis ttl error for key {key}: {e}")
            return -2
            
    async def clear(self) -> bool:
        """清空所有缓存"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            TerraLogUtil.error(f"Redis clear error: {e}")
            return False
            
    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的键列表"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
            
        try:
            keys = await self.redis.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            TerraLogUtil.error(f"Redis keys error: {e}")
            return []
            
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.aclose()
            TerraLogUtil.info("Redis connection closed")
            
    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        if self.serializer == 'pickle':
            return pickle.dumps(value)
        else:  # json
            return json.dumps(value, ensure_ascii=False).encode('utf-8')
            
    def _deserialize(self, value: bytes) -> Any:
        """反序列化值"""
        if self.serializer == 'pickle':
            return pickle.loads(value)
        else:  # json
            return json.loads(value.decode('utf-8'))
            
    # Redis特有方法
    async def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.incrby(key, amount)
        
    async def decrement(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        return await self.increment(key, -amount)
        
    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        """获取哈希字段值"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        value = await self.redis.hget(key, field)
        return self._deserialize(value) if value else None
        
    async def hash_set(self, key: str, field: str, value: Any) -> bool:
        """设置哈希字段值"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        serialized_value = self._serialize(value)
        result = await self.redis.hset(key, field, serialized_value)
        return result
        
    async def list_push(self, key: str, *values) -> int:
        """向列表推入值"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        serialized_values = [self._serialize(v) for v in values]
        return await self.redis.lpush(key, *serialized_values)
        
    async def list_pop(self, key: str) -> Optional[Any]:
        """从列表弹出值"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        value = await self.redis.rpop(key)
        return self._deserialize(value) if value else None