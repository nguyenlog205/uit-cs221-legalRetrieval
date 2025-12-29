import os
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# --- Import các Module Agents ---
from src.agents.intent_classifier import IntentClassifier 
from src.agents.database_retriever import DatabaseRetriever
from src.agents.specialized_generator import SpecificGenerator
from src.agents.general_generator import GeneralGenerator
from src.utils import load_env

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Data Models ---
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    source_documents: Optional[List[str]] = None

# --- Global State ---
agents = {}

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- KHỞI ĐỘNG HỆ THỐNG RAG (CLOUD API MODE) ---")
    
    # 1. Load Config từ biến môi trường
    groq_api_key = load_env("GROQ_API_KEY")
    
    # Config cho Model trả lời chính
    llm_api_key = load_env("LLM_API_KEY")
    llm_api_url = load_env("LLM_API_URL")
    llm_model_name = load_env("LLM_MODEL_NAME")

    # --- SỬA Ở ĐÂY: Bắt buộc phải có URL API, không fallback về localhost nữa ---
    if not llm_api_url:
        # Nếu thiếu config, mặc định dùng Groq luôn chứ không dùng Local
        logger.warning("⚠️ Chưa cấu hình LLM_API_URL. Tự động set về Groq API.")
        llm_api_url = "https://api.groq.com/openai/v1/chat/completions"
        if not llm_model_name:
            llm_model_name = "llama-3.1-8b-instant"

    try:
        # 2. Khởi tạo Intent Classifier
        logger.info("Initializing Intent Classifier...")
        agents["classifier"] = IntentClassifier(api_key=groq_api_key)

        # 3. Khởi tạo General Generator
        logger.info("Initializing General Generator...")
        agents["general_gen"] = GeneralGenerator(api_key=groq_api_key)

        # 4. Khởi tạo Specialized Generator
        logger.info(f"Initializing Specialized Generator pointing to: {llm_api_url} | Model: {llm_model_name}")
        
        agents["specific_gen"] = SpecificGenerator(
            api_key=llm_api_key,       
            api_url=llm_api_url,       
            model_id=llm_model_name,      
            max_output_tokens=1024
        )

        # 5. Khởi tạo Database Retriever
        config_path = "configs/indexing_pipeline.yml" 
        if os.path.exists(config_path):
            logger.info(f"Initializing Database Retriever from {config_path}...")
            agents["retriever"] = DatabaseRetriever.from_config(config_path=config_path)
        else:
            logger.warning(f"Warning: Không tìm thấy {config_path}. Chế độ Specific có thể bị lỗi.")
            agents["retriever"] = None
            
        logger.info("--- HỆ THỐNG ĐÃ SẴN SÀNG ---")
        
    except Exception as e:
        logger.error(f"Lỗi khởi tạo hệ thống: {e}")
        raise e

    yield 

    logger.info("Shutting down system...")
    agents.clear()

# --- Khởi tạo App FastAPI ---
app = FastAPI(title="Vietnam Public Health RAG API", lifespan=lifespan)

# --- API Endpoints ---
@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "components": list(agents.keys()),
        # Chỉ hiển thị tên Model đang dùng trên Cloud
        "current_model": os.getenv("LLM_MODEL_NAME", "Unknown Cloud Model") 
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    # 1. Phân loại
    try:
        intent = await agents["classifier"].classify(query)
    except Exception as e:
        logger.error(f"Classifier Error: {e}")
        intent = "specific"
    
    logger.info(f"Input: '{query}' | Intent: {intent}")

    # 2. General Chat
    if intent == "general":
        try:
            response_text = agents["general_gen"].generate_general(query)
            return ChatResponse(response=response_text, intent="general", source_documents=[])
        except Exception:
            intent = "specific"

    # 3. RAG Chat
    if intent == "specific":
        retriever = agents.get("retriever")
        
        if not retriever:
            return ChatResponse(response="DB chưa sẵn sàng.", intent="error")

        # 3a. Retrieve
        retrieved_docs = await retriever.retrieve(query, k=5)
        
        # 3b. Fallback
        if not retrieved_docs:
            fallback_text = agents["general_gen"].generate_fallback(query)
            return ChatResponse(response=fallback_text, intent="specific_fallback", source_documents=[])

        # 3c. Generate (API Call)
        answer = await agents["specific_gen"].generate_response(query, retrieved_docs)
        
        sources = [doc.metadata.get("source", "Unknown") for doc in retrieved_docs]
        
        return ChatResponse(
            response=answer,
            intent="specific",
            source_documents=list(set(sources))
        )

if __name__ == "__main__":
    print("🚀 Starting RAG API Server...")
    # Port này là port của cái code Python này (nó phải chạy thì mới có API mà gọi)
    # Chứ không phải port của Model LLM (Model LLM nằm trên server Groq rồi)
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)