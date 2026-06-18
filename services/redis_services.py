import redis.asyncio as redis
import os
import json
from typing import Optional, Any

class RedisService:
    def init(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', ''),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[str]:
        return await self.redis.get(key)
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        await self.redis.delete(key)
    
    async def incr(self, key: str) -> int:
        return await self.redis.incr(key)
    
    async def cache_search(self, query: str, results: list, expire: int = 600):
        key = f"search:{query.lower().strip()}"
        await self.set(key, results, expire)
    
    async def get_cached_search(self, query: str) -> Optional[list]:
        data = await self.get(f"search:{query.lower().strip()}")
        return json.loads(data) if data else None
    
    async def increment_stat(self, stat_name: str):
        await self.incr(f"stat:{stat_name}")