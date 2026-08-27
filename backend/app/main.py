from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.ai.openrouter import ask_gemma
from app.routes.discovery import router as discovery_router
from app.api.export import router as export_router
from app.api.projects import router as projects_router


app = FastAPI(
    title="ContextForge AI",
    description="AI Context Engineering Platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(discovery_router)
app.include_router(export_router)
app.include_router(projects_router)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "message": "ContextForge AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/ai/chat")
async def ai_chat(request: ChatRequest):

    try:
        response = await ask_gemma(request.message)

        return {
            "response": response
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )