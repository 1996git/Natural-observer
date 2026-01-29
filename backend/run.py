"""
Natural Observer Backend API
自然観察 × LLM Web API のバックエンド
"""
import uvicorn
from app.main import app
from app.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
