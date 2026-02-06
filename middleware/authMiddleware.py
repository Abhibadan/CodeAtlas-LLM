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
        # Get authorization header
        token = request.headers.get("authorization")
        
        # Check if token exists
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        
        # Extract token from "Bearer <token>" format
        try:
            token = token.split(" ")[1]
        except IndexError:
            return JSONResponse(status_code=401, content={"detail": "Invalid authorization format"})
        
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