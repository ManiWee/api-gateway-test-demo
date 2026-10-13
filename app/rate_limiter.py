import time
import redis.asyncio as redis

SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local clear_before = now - window

-- Remove old request records
redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)

-- Count requests in active window
local current_requests = redis.call('ZCARD', key)

if current_requests < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
    return 1 -- Allowed
else
    return 0 -- Blocked
end
"""

class RedisRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int = 5, window_seconds: int = 60) -> bool:
        now = time.time()
        redis_key = f"rate_limit:{key}"
        result = await self.redis.eval(
            SLIDING_WINDOW_LUA, 
            1, 
            redis_key, 
            now, 
            window_seconds, 
            limit
        )
        return result == 1