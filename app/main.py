import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()
MODEL_STORE = os.path.join(os.path.dirname(__file__), "..", "models.json")

class ModelSpec(BaseModel):
    id: str
    name: str
    type: str
    path: str
    options: dict

class ModelResponse(BaseModel):
    id: str
    name: str
    type: str
    path: str
    options: dict

def load_store() -> dict:
    if not os.path.exists(MODEL_STORE):
        return {"models": []}
    with open(MODEL_STORE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_store(store: dict):
    with open(MODEL_STORE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

@app.get("/models", response_model=List[ModelResponse])
async def list_models():
    store = load_store()
    return [ModelResponse(**m) for m in store["models"]]

@app.post("/models", response_model=ModelResponse)
async def add_model(spec: ModelSpec):
    store = load_store()
    if any(m["id"] == spec.id for m in store["models"]):
        raise HTTPException(status_code=400, detail="Model ID already exists")
    store["models"].append(spec.dict())
    save_store(store)
    return ModelResponse(**spec.dict())

@app.delete("/models/{model_id}")
async def delete_model(model_id: str):
    store = load_store()
    if not any(m["id"] == model_id for m in store["models"]):
        raise HTTPException(status_code=404, detail="Model not found")
    store["models"] = [m for m in store["models"] if m["id"] != model_id]
    save_store(store)
    return {"detail": f"Model {model_id} deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)