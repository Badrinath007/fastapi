from supabase import create_client, Client
from hashlib import sha256
import bcrypt
from fastapi import HTTPException,FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

# Load sentiment-analysis pipeline from Hugging Face
sentiment_analyzer = pipeline("sentiment-analysis")
# Load text generation model (GPT-2)
text_generator = pipeline("text-generation", model="gpt2")

# Request body model for sentiment analysis
class TextInput(BaseModel):
    text: str

# Endpoint for Sentiment Analysis
@app.post("/sentiment")
async def analyze_sentiment(input: TextInput):
    result = sentiment_analyzer(input.text)
    return {"sentiment": result}

# Request body model for text generation
class TextInputForGeneration(BaseModel):
    prompt: str

# Endpoint for Text Generation (GPT-2)
@app.post("/generate")
async def generate_text(input: TextInputForGeneration):
    result = text_generator(input.prompt, max_length=50)
    return {"generated_text": result[0]["generated_text"]}

# Supabase credentials (replace with your actual credentials)
SUPABASE_URL = "https://delnumpenjcexaieyand.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRlbG51bXBlbmpjZXhhaWV5YW5kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMxNTI5NjEsImV4cCI6MjA0ODcyODk2MX0.8jwnCV1xaD62wc7aennEnG8oUBcY6lyJS1zDotiHPzI"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Hashing the password before storing it
def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Verifying the password during login
def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies if the given password matches the hashed password.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Utility to add a new user to Supabase
async def add_user(user: dict) -> dict:
    """
    Adds a new user to the Supabase database after hashing their password.
    """
    hashed_password = hash_password(user['password'])
    
    # Insert new user into the 'users' table
    response = supabase.table("users").insert({
        "name": user['name'],
        "email": user['email'],
        "password_hash": hashed_password
    }).execute()
    
    # Check if the user was added successfully
    if response.status_code != 201:
        raise HTTPException(status_code=400, detail="Failed to create user")
    
    return response.data[0]

# Utility to fetch user by email from Supabase
async def get_user_by_email(email: str) -> dict:
    """
    Fetches a user from the Supabase database based on their email address.
    """
    response = supabase.table("users").select("*").eq("email", email).execute()
    
    # If no user is found or the request failed
    if response.status_code != 200 or len(response.data) == 0:
        return None
    
    return response.data[0]

# Utility to create a connection between two users
async def create_connection(user_id: int, friend_id: int) -> dict:
    """
    Creates a new connection between two users in the Supabase database.
    """
    # Insert a new connection request
    response = supabase.table("connections").insert({
        "user_id": user_id,
        "friend_id": friend_id,
        "status": "pending"
    }).execute()
    
    # Check if the connection request was sent successfully
    if response.status_code != 201:
        raise HTTPException(status_code=400, detail="Failed to create connection")
    
    return response.data[0]

