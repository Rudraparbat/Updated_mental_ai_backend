from datetime import timedelta , datetime
from typing import Annotated
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from db.models import *
from db.database import Sessions
from sqlalchemy.orm import Session
from fastapi import FastAPI , Depends ,  HTTPException , Response , Request 
from starlette import status
from jose import jwt , JWTError
import os
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from dotenv import load_dotenv

load_dotenv()

# Add a router to seperate from mainpy file
router = APIRouter(
    prefix='/auth',
    tags = ['auth']
)

# added secret key and the algorithm
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# dependency for hashing password 
bcrypt_context = CryptContext(schemes=['bcrypt'] , deprecated = 'auto')


# dependency for token bearer like in which url we are getting the token
auth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class usermodel(BaseModel) :
    name : str
    email : EmailStr
    password : str


def get_db() :
    try :
        db = Sessions()
        yield db
    finally :
        db.close()

# Database dependency
db_dependency = Annotated[Session , Depends(get_db)]


# Writing the sign api endpoints 
@router.post('/' , status_code=status.HTTP_200_OK)
async def create_user(db : db_dependency , user : usermodel, response : Response) :
    usertable = MentalUser()
    usertable.username = user.name
    usertable.email = user.email
    usertable.set_password = bcrypt_context.hash(user.password)

    db.add(usertable)
    db.commit()
    db.refresh(usertable)

    token = CreateJwtTokenForLoginUser(usertable.id ,user.name , timedelta(days=7))

    response.set_cookie(
        key="access_token",
        value=str(token),
        httponly=True,          
        secure=True,           
        samesite="None",         
        max_age=60*60*24*7     
    )
    return {
        "data" : user,
        "user_id" : usertable.id,
        "message" : "Successfully created user"
    }

# For Authentication

@router.post('/token')
async def login_user(db : db_dependency , user : Annotated[OAuth2PasswordRequestForm  , Depends()] , response : Response) :
    try :
        username = db.query(MentalUser).filter(MentalUser.email == user.username).first()
        if username is None :
            raise  HTTPException(status_code=404, detail="User not found")
        if (bcrypt_context.verify(user.password , username.set_password)) :
            token = CreateJwtTokenForLoginUser(username.id ,username.username , timedelta(days = 7))

            response.set_cookie(
                key="access_token",
                value=str(token),
                httponly=True,      
                secure=True,           
                samesite="None",        
                max_age= 60*60*24*7    
            )
            return {
                "message" : "user Authenticated successfully",
                "authenticated" : True,
                "user_id" : username.id,
                "data" : username
            }
        else :
            raise HTTPException(status_code=404 , detail=f"{user.username} mismatched the password")
        
    except Exception as e :
        raise HTTPException(status_code=500 , detail=str(e))
    
def CreateJwtTokenForLoginUser(userid : str , name : str , expires : timedelta) -> dict :
    encode = {'sub' : name , 'id' : userid , 'exp' : datetime.now() + expires}
    value = jwt.encode(encode , SECRET_KEY , ALGORITHM)
    return str(value)

# after putting that dependency it actually search for that token in cookies and get the user information
async def GetcurrentUserFromCookie(request: Request):
    token = request.cookies.get("access_token")  
    print(token)
    if token is None:
        raise HTTPException(status_code=401, detail="Token not found in cookies")

    try:
        user = jwt.decode(str(token), SECRET_KEY, algorithms=[ALGORITHM])
        username = user.get('sub')
        userid = user.get("id")

        if not username or not userid:
            raise HTTPException(status_code=401, detail="Could not validate user")

        return {"username": username, "id": userid}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    

# This endpoint takes the token from the cookies decode it add extra lifespan and create new token

@router.get('/renew-token')
async def CreateNewToken(response : Response , user : dict = Depends(GetcurrentUserFromCookie)) :
    if user is None :
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST , detail= f"Your login session is over")
    
    username = str(user.get("username"))
    userid = str(user.get("id"))

    new_token = CreateJwtTokenForLoginUser( userid, username , timedelta(days=7))
    response.set_cookie(
            key="access_token",
            value=str(new_token),
            httponly=True,          
            secure=True,        
            samesite="None",     
            max_age=60*60*24*7     
        )
    return {"message" : "Token Generated with new timestamp is successfull" , "new_token" : str(new_token)}
        

# To Check Auth Status If The current user is logged in or not
@router.get('/authstatus/')
async def GetUserAuthStatus(user : dict = Depends(GetcurrentUserFromCookie)) :
    if user is None :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) 
    return {"authenticated" : True , "user_id"  : user.get("id") ,  "message" : "User is already loggedin"}


# To Logout ANy user 
@router.get('/logout/')
async def LogoutUser(response : Response) :
    response.delete_cookie(key="access_token")
    return {"User is Loogedout Successfully"}
