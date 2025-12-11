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

# --- Data Models (Pydantic) ---
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    source_documents: Optional[List[str]] = None

# --- Global State ---
# Biến toàn cục để lưu trữ các instances của agents
agents = {}

# --- Lifespan Manager (Khởi tạo 1 lần khi chạy Server) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- KHỞI ĐỘNG HỆ THỐNG RAG ---")
    
    # 1. Load API Key
    api_key = load_env("GROQ_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: Không tìm thấy GROQ_API_KEY trong biến môi trường.")

    try:
        # 2. Khởi tạo Intent Classifier
        logger.info("Initializing Intent Classifier...")
        agents["classifier"] = IntentClassifier(api_key=api_key)

        # 3. Khởi tạo General Generator (Chat xã giao)
        logger.info("Initializing General Generator...")
        agents["general_gen"] = GeneralGenerator(api_key=api_key)

        # 4. Khởi tạo Specialized Generator (RAG Writer)
        logger.info("Initializing Specialized Generator...")
        agents["specific_gen"] = SpecificGenerator(api_key=api_key)

        # 5. Khởi tạo Database Retriever (Nặng nhất - Load Vector DB & Models)
        # Đường dẫn config trỏ tới file .yml của bạn
        config_path = "configs/indexing_pipeline.yml" 
        if os.path.exists(config_path):
            logger.info(f"Initializing Database Retriever from {config_path}...")
            # DatabaseRetriever có hàm factory method from_config
            agents["retriever"] = DatabaseRetriever.from_config(config_path=config_path)
        else:
            logger.warning(f"Warning: Không tìm thấy {config_path}. Chế độ Specific có thể bị lỗi.")
            agents["retriever"] = None
            
        logger.info("--- HỆ THỐNG ĐÃ SẴN SÀNG ---")
        
    except Exception as e:
        logger.error(f"Lỗi khởi tạo hệ thống: {e}")
        raise e

    yield # Server bắt đầu nhận request tại đây

    # Shutdown logic (nếu cần dọn dẹp tài nguyên)
    logger.info("Shutting down system...")
    agents.clear()

# --- Khởi tạo App FastAPI ---
app = FastAPI(title="Vietnam Public Health RAG API", lifespan=lifespan)

# --- API Endpoints ---

@app.get("/health")
async def health_check():
    """Kiểm tra trạng thái server"""
    return {"status": "ok", "components": list(agents.keys())}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint chính xử lý luồng hội thoại:
    Input -> Classifier -> (General Gen) OR (Retriever -> Specific Gen)
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    # 1. BƯỚC 1: Phân loại ý định (General vs Specific)
    intent = await agents["classifier"].classify(query)
    logger.info(f"Input: '{query}' | Intent detected: {intent}")

    # 2. XỬ LÝ NHÁNH 1: CÂU HỎI XÃ GIAO (GENERAL)
    if intent == "general":
        # GeneralGenerator dùng hàm sync, chạy trực tiếp
        response_text = agents["general_gen"].generate_general(query)
        return ChatResponse(
            response=response_text,
            intent="general",
            source_documents=[]
        )

    # 3. XỬ LÝ NHÁNH 2: CÂU HỎI CHUYÊN MÔN (SPECIFIC/RAG)
    if intent == "specific":
        retriever = agents.get("retriever")
        
        if not retriever:
            return ChatResponse(
                response="Hệ thống cơ sở dữ liệu đang bảo trì. Vui lòng thử lại sau.",
                intent="error"
            )

        # 3a. Truy vấn tài liệu (Retrieve)
        # Retrieve là hàm async trong file database_retriever.py của bạn
        retrieved_docs = await retriever.retrieve(query, k=5)
        
        # Logic: Nếu không tìm thấy tài liệu nào liên quan -> Fallback
        if not retrieved_docs:
            logger.info("Không tìm thấy tài liệu phù hợp -> Chuyển sang Fallback.")
            fallback_text = agents["general_gen"].generate_fallback(query)
            return ChatResponse(
                response=fallback_text,
                intent="specific_fallback",
                source_documents=[]
            )

        # 3b. Tổng hợp câu trả lời (Generate)
        # Generate là hàm async trong file specialized_generator.py
        answer = await agents["specific_gen"].generate_response(query, retrieved_docs)
        
        # Trích xuất nguồn để hiển thị cho User
        sources = [doc.metadata.get("source", "Unknown") for doc in retrieved_docs]
        
        return ChatResponse(
            response=answer,
            intent="specific",
            source_documents=list(set(sources)) # Loại bỏ trùng lặp tên nguồn
        )

# --- Entry Point ---
if __name__ == "__main__":
    # Chạy server tại localhost:8000
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)