from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jwt import decode,ExpiredSignatureError,InvalidTokenError
from dotenv import load_dotenv
from dbModule import User
import os
from bson import ObjectId
load_dotenv()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(request.headers)
        # token = request.headers.get("Authorization")
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY5Nzg1MGU2Y2RmNTI0NTk0ZDk0MWVhZCIsImlhdCI6MTc3MDI5ODM1MiwiZXhwIjoxNzcwMzAxOTUyfQ.QaJXM3m6pEGx9RXvwY_DByJ7AHyvjrS7q1zXeHjLdts"
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        try:
            token_data = decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            if not token_data.get("id"):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            user = User.find_by_id(ObjectId(token_data["id"]))
            if not user:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            request.state.user = user
        except ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"detail": "Token expired"})
        except InvalidTokenError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        response = await call_next(request)
        return response 