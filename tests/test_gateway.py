import pytest
import pytest_asyncio
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from app.main import app, get_redis
from app.auth import create_access_token

SECRET_KEY = "gateway-secret-key"

@pytest_asyncio.fixture
async def async_client():
    fake_redis_client = fakeredis.aioredis.FakeRedis()
    
    # Override app redis dependency with fake_redis
    app.dependency_overrides[get_redis] = lambda: fake_redis_client
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()
    await fake_redis_client.aclose()

@pytest.mark.asyncio
async def test_unauthorized_without_jwt(async_client):
    response = await async_client.get("/api/v1/resource")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid authorization header"}

@pytest.mark.asyncio
async def test_rate_limiting_flow(async_client):
    token = create_access_token({"sub": "user_1"}, secret_key=SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Send 5 valid requests -> 200 OK
    for _ in range(5):
        response = await async_client.get("/api/v1/resource", headers=headers)
        assert response.status_code == 200

    # 6th request -> 429 Too Many Requests
    response = await async_client.get("/api/v1/resource", headers=headers)
    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded. Maximum 5 requests per minute allowed."}