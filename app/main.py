import os
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from app.auth import verify_token
from app.rate_limiter import RedisRateLimiter

SECRET_KEY = os.getenv("SECRET_KEY", "gateway-secret-key")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

app = FastAPI(title="Secure API Gateway")

# Dependency to yield Redis connection
async def get_redis():
    client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

@app.get("/api/v1/resource")
async def protected_resource(
    request: Request, 
    redis_client: redis.Redis = Depends(get_redis)
):
    # 1. Validate JWT Header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token, SECRET_KEY)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")

    # 2. Apply Rate Limiting
    limiter = RedisRateLimiter(redis_client)
    allowed = await limiter.is_allowed(key=user_id, limit=5, window_seconds=60)
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Maximum 5 requests per minute allowed."}
        )

    # 3. Successful Gateway Response
    return {"status": "success", "message": f"Hello User {user_id}, access granted!"}