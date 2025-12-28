from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import config

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        response = await call_next(request)
        return response 