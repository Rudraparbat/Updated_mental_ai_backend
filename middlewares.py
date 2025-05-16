from fastapi import FastAPI , HTTPException , Depends , Request , Response ,WebSocket, status
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware 
from models import *
from database import *
from sqlalchemy.orm import Session
from pydantic import BaseModel , Field
import auth
from jose import jwt , JWTError
from passlib.context import CryptContext
SECRET_KEY = "RUDRAANASUYASAYANANTIKAANUSHKA82762"
ALGORITHM = 'HS256'


# This middleware helps to implement rate limiting

class RateLimiterMiddleware(BaseHTTPMiddleware) :
    def __init__(self , app) :
        # hook the middlware with app
        super().__init__(app)

    async def dispatch(self, request : Request, call_next):
        current_ip_address = request.client.host
        request.state.ip_address = current_ip_address
        request.state.user = await self.getuser(request)
        print(request.state.user)
        response = await call_next(request)
        response.headers["X-IP-Address"] = current_ip_address
        return response
    
    # helper function to decode cookie and get the user
    async def getuser(self, request : Request) :
        token = request.cookies.get("access_token") 
        print(token) 
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
        

# For websocktes
def get_token_from_cookies(headers: list[tuple[bytes, bytes]]) -> str | None:
    for name, value in headers:
        if name == b"cookie":
            cookies = value.decode().split("; ")
            for cookie in cookies:
                if cookie.startswith("access_token="):
                    return cookie.split("=", 1)[1]
    return None
async def verfiy_user(token : str) -> dict | None :
    try:
        user = jwt.decode(str(token), SECRET_KEY, algorithms=[ALGORITHM])
        username = user.get('sub')
        userid = user.get("id")

        if not username or not userid:
            raise HTTPException(status_code=401, detail="Could not validate user")

        return {"username": username, "id": userid}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    

def websocket_auth(handler):
    @wraps(handler)
    async def wrapper(websocket: WebSocket, *args, **kwargs):
        token = get_token_from_cookies(websocket.scope["headers"])
        if not token:
            await websocket.close()
            return

        user_data = await verfiy_user(token)
        if not user_data:
            await websocket.close()
            return

        websocket.state.user = user_data  
        return await handler(websocket, *args, **kwargs)

    return wrapper
        
        