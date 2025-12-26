import os
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# --- Import các Module Agents ---
# Giả sử IntentClassifier và GeneralGenerator vẫn dùng Groq (hoặc bạn có thể sửa sau)
from src.agents.intent_classifier import IntentClassifier 
from src.agents.database_retriever import DatabaseRetriever
from src.agents.specialized_generator import SpecificGenerator
from src.agents.general_generator import GeneralGenerator
from src.utils import load_env

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Data Models (Pydantic) ---
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    source_documents: Optional[List[str]] = None

# --- Global State ---
agents = {}

# --- Cấu hình URL ---
# URL của Local Model Server (Gemma/Llama mà bạn đang chạy ở cửa sổ kia)
LOCAL_LLM_URL = "http://localhost:8000/chat" 

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- KHỞI ĐỘNG HỆ THỐNG RAG ---")
    
    # 1. Load API Key (Vẫn cần cho Intent Classifier hoặc General Gen nếu chúng dùng Groq)
    api_key = load_env("GROQ_API_KEY") 
    
    # Nếu IntentClassifier cũng chuyển sang Local thì không cần check kỹ cái này, 
    # nhưng tạm thời giữ nguyên logic cũ cho an toàn.
    if not api_key:
        logger.warning("⚠️ Warning: Không thấy GROQ_API_KEY. Các module dùng Groq sẽ lỗi.")

    try:
        # 2. Khởi tạo Intent Classifier
        logger.info("Initializing Intent Classifier...")
        agents["classifier"] = IntentClassifier(api_key=api_key)

        # 3. Khởi tạo General Generator (Chat xã giao)
        logger.info("Initializing General Generator...")
        agents["general_gen"] = GeneralGenerator(api_key=api_key)

        # 4. Khởi tạo Specialized Generator (UPDATE: Dùng Local API)
        logger.info(f"Initializing Specialized Generator pointing to {LOCAL_LLM_URL}...")
        agents["specific_gen"] = SpecificGenerator(
            api_key="unused",       # Giữ tham số này để không lỗi code cũ (nếu class yêu cầu)
            api_url=LOCAL_LLM_URL,  # Trỏ vào server Gemma
            max_output_tokens=512
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

    yield # Server bắt đầu nhận request

    logger.info("Shutting down system...")
    agents.clear()

# --- Khởi tạo App FastAPI ---
app = FastAPI(title="Vietnam Public Health RAG API", lifespan=lifespan)

# --- API Endpoints ---

@app.get("/health")
async def health_check():
    """Kiểm tra trạng thái server"""
    return {
        "status": "ok", 
        "components": list(agents.keys()),
        "local_llm_target": LOCAL_LLM_URL
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    # 1. Phân loại ý định
    try:
        intent = await agents["classifier"].classify(query)
    except Exception as e:
        logger.error(f"Classifier Error: {e}")
        intent = "specific" # Fallback về specific nếu classifier lỗi
    
    logger.info(f"Input: '{query}' | Intent: {intent}")

    # 2. NHÁNH 1: GENERAL (Xã giao)
    if intent == "general":
        try:
            response_text = agents["general_gen"].generate_general(query)
            return ChatResponse(response=response_text, intent="general", source_documents=[])
        except Exception:
            intent = "specific" # Nếu lỗi thì thử đẩy sang RAG luôn

    # 3. NHÁNH 2: SPECIFIC (RAG với Local LLM)
    if intent == "specific":
        retriever = agents.get("retriever")
        
        if not retriever:
            return ChatResponse(
                response="Hệ thống cơ sở dữ liệu chưa sẵn sàng.", 
                intent="error"
            )

        # 3a. Retrieve
        retrieved_docs = await retriever.retrieve(query, k=5)
        
        # 3b. Fallback nếu không có tài liệu
        if not retrieved_docs:
            logger.info("No docs found -> Fallback.")
            fallback_text = agents["general_gen"].generate_fallback(query)
            return ChatResponse(
                response=fallback_text, 
                intent="specific_fallback", 
                source_documents=[]
            )

        # 3c. Generate (Gọi sang Local Server 8000)
        answer = await agents["specific_gen"].generate_response(query, retrieved_docs)
        
        sources = [doc.metadata.get("source", "Unknown") for doc in retrieved_docs]
        
        return ChatResponse(
            response=answer,
            intent="specific",
            source_documents=list(set(sources))
        )

# --- Entry Point ---
if __name__ == "__main__":
    # QUAN TRỌNG: Đổi port thành 8001 để tránh xung đột với Model Server (8000)
    print("🚀 Starting RAG API Server on port 8001...")
    uvicorn.run("main_api:app", host="0.0.0.0", port=8001, reload=True)