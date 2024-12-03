from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
import bcrypt
from datetime import datetime, timedelta
from utils import add_user, get_user_by_email, create_connection, hash_password, verify_password
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],  # Or specify allowed methods
    allow_headers=["*"],  # Or specify allowed headers
)

app = FastAPI()


# JWT configuration
SECRET_KEY = "c7@7#24a14!jdf&5d94c8f1d07f2e5f745f728293febfa7384b8d4e1"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Function to verify JWT token
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ConnectionCreate(BaseModel):
    friend_id: int

@app.post("/signup", status_code=201)
async def register_user(user: UserCreate):
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user.password = hash_password(user.password)  # Hash password before storing
    created_user = await add_user(user.dict())
    return {"message": "User registered successfully", "user": created_user}

@app.post("/login")
async def login_user(user: UserLogin):
    db_user = await get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token with expiration time (1 hour in this example)
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode({"sub": db_user["id"], "exp": expiration_time}, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"message": "Login successful", "token": token}

@app.post("/connections")
async def create_connection_request(connection: ConnectionCreate, user_id: int = Depends(verify_token)):
    friend_id = connection.friend_id
    new_connection = await create_connection(user_id, friend_id)
    return {"message": "Connection request sent", "connection": new_connection}
