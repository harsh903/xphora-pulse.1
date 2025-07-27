from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI
from app.api import router
from app.chatbot import chatbot_router  # Import the chatbot router

app = FastAPI(title="Bengaluru Services and Chatbot")

# Include the existing API routes
app.include_router(router)

# Include the chatbot routes
app.include_router(chatbot_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)