import pytest
import pytest_asyncio
import fakeredis.aioredis
from app.rate_limiter import RedisRateLimiter

@pytest_asyncio.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.aclose()

@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit(fake_redis):
    limiter = RedisRateLimiter(redis_client=fake_redis)
    client_ip = "127.0.0.1"

    # Make 5 requests (Limit is 5 per 60 seconds)
    for _ in range(5):
        allowed = await limiter.is_allowed(key=client_ip, limit=5, window_seconds=60)
        assert allowed is True

@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit(fake_redis):
    limiter = RedisRateLimiter(redis_client=fake_redis)
    client_ip = "127.0.0.1"

    # Fill capacity
    for _ in range(5):
        await limiter.is_allowed(key=client_ip, limit=5, window_seconds=60)

    # 6th request must be blocked
    allowed = await limiter.is_allowed(key=client_ip, limit=5, window_seconds=60)
    assert allowed is False