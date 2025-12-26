from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .database import get_db
from .models import Order, ServiceRequest
from .agents import manager

app = FastAPI(title="Resort Agent System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class ChatRequest(BaseModel):
    history: List[Dict[str, str]] # List of {"role": "user", "content": "..."}

class ChatResponse(BaseModel):
    response: str

# --- Endpoints ---

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = manager.chat(request.history)
        return {"response": response_text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return orders

@app.get("/requests")
def get_requests(db: Session = Depends(get_db)):
    requests = db.query(ServiceRequest).all()
    return requests

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
