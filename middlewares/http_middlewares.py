from fastapi import FastAPI , HTTPException , Depends , Request , Response ,WebSocket, status
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware 
from db.models import *
from db.database import *
from sqlalchemy.orm import Session
from pydantic import BaseModel , Field
import auth
from jose import jwt , JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


class RateLimiterMiddleware(BaseHTTPMiddleware) :
    def __init__(self , app) :
        # hook the middlware with app
        super().__init__(app)

    async def dispatch(self, request : Request, call_next):
        current_ip_address = request.client.host
        request.state.ip_address = current_ip_address
        request.state.user = await self.getuser(request)
        response = await call_next(request)
        response.headers["X-IP-Address"] = current_ip_address
        return response
    
    # helper function to decode cookie and get the user
    async def getuser(self, request : Request) :
        token = request.cookies.get("access_token") 
        if token is None:
            return None
        try:
            user = jwt.decode(str(token), SECRET_KEY, algorithms=[ALGORITHM])
            username = user.get('sub')
            userid = user.get("id")

            if not username or not userid:
                return None
            return {"username": username, "id": userid}
        except Exception as e:
            print(str(e))
            return None
        
