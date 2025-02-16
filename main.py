from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import asyncio
import logging

# Determine the environment (default: development)
ENV = os.getenv("ENVIRONMENT", "development").lower()

# Load the appropriate .env file
if ENV == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.development")

# Read API keys and secrets from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Set OPENAI_API_KEY in your environment variables.")
if not JWT_SECRET_KEY:
    raise ValueError("Set JWT_SECRET_KEY in your environment variables.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Configure logging
LOG_LEVEL = logging.DEBUG if ENV == "development" else logging.INFO
logging.basicConfig(level=LOG_LEVEL)
logging.info(f"Starting API in {ENV} mode...")

# FastAPI app setup
app = FastAPI(title="GenAI SaaS API", version="1.2")

# CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Authentication Config (Read secret from env)
class Settings(BaseModel):
    authjwt_secret_key: str = JWT_SECRET_KEY

@AuthJWT.load_config
def get_config():
    return Settings()

# Authentication Model
class LoginModel(BaseModel):
    username: str
    password: str

# Login Route (Mock Auth)
@app.post("/login")
def login(user: LoginModel, Authorize: AuthJWT = Depends()):
    access_token = Authorize.create_access_token(subject=user.username)
    return {"access_token": access_token}

# AI Prompt Model
class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

# Async Streaming Response for OpenAI
async def stream_ai_response(prompt: str, max_tokens: int):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stream=True  # Enable streaming
        )
        for chunk in response:
            if chunk.choices:
                yield chunk.choices[0].delta.content
            await asyncio.sleep(0.1)  # Non-blocking wait
    except Exception as e:
        logging.error(f"Error in streaming response: {e}")
        raise HTTPException(status_code=500, detail="AI Streaming Error")

# AI Generation Route (Streaming)
@app.post("/generate")
async def generate_ai_text(request: PromptRequest, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require authentication
    return StreamingResponse(stream_ai_response(request.prompt, request.max_tokens), media_type="text/event-stream")

# AI Generation Route (Non-Streaming)
@app.post("/generate_sync")
async def generate_ai_text_sync(request: PromptRequest, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require authentication
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": request.prompt}],
            max_tokens=request.max_tokens
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        logging.error(f"Error in non-streaming response: {e}")
        raise HTTPException(status_code=500, detail="AI Response Error")

# Root Route
@app.get("/")
def root():
    return {"message": f"Welcome to GenAI SaaS API! Running in {ENV} mode."}
