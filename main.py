from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY in your environment variables.")

# Initialize OpenAI client with the new API format
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Request model
class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

# OpenAI API call function (New format for OpenAI >=1.0.0)
def generate_text(prompt: str, max_tokens: int):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI route for AI text generation
@app.post("/generate")
async def generate_ai_text(request: PromptRequest):
    output = generate_text(request.prompt, request.max_tokens)
    return {"response": output}
