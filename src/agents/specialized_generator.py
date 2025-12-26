import httpx
from typing import List, Optional
from langchain_core.documents import Document

class SpecificGenerator:
    """
    Tạo phản hồi chi tiết bằng cách gọi vào Local API Server (FastAPI).
    Giữ nguyên tên class để tương thích với code cũ.
    """
    def __init__(
        self, 
        api_key: str = "unused", # Giữ lại để code cũ không bị lỗi tham số
        model_id: str = "local-model", # Giữ lại, có thể dùng để log
        max_output_tokens: int = 512,
        api_url: str = "http://localhost:8000/chat", # Thêm tham số URL của server local
        timeout: float = 60.0
    ):
        self.api_url = api_url
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        
        # Không khởi tạo AsyncGroq nữa
        print(f"-> SpecificGenerator (Local API) ready. Target: {self.api_url}")

    async def generate_response(self, query: str, documents: List[Document]) -> str:
        """
        Tổng hợp câu trả lời từ Local API.
        Signature hàm giữ nguyên: (query, documents) -> str
        """
        
        # 1. Chuẩn bị Context
        context_texts = [
            f"--- Tài liệu: {doc.metadata.get('source', 'Văn bản Luật')}\n"
            f"Nội dung: {doc.page_content}\n"
            for doc in documents
        ]
        context_block = "\n\n".join(context_texts)

        # 2. Tạo Prompt (Gộp context vào để gửi cho Server)
        # Vì Server kia đã có System Prompt, ta gửi nội dung này như User Prompt
        final_user_content = f"""Dựa vào các thông tin dưới đây để trả lời câu hỏi.

--- CONTEXT (Nguồn tài liệu) ---
{context_block}

--- CÂU HỎI NGƯỜI DÙNG ---
{query}
"""

        # 3. Tạo Payload đúng chuẩn API Server bạn đã viết
        payload = {
            "question": final_user_content,
            "max_tokens": self.max_output_tokens
        }

        # 4. Gọi API (Thay thế đoạn Groq cũ)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url, 
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status() 
                result_json = response.json()
                
                # Trả về kết quả
                return result_json.get("answer", "Không tìm thấy câu trả lời.")

        except httpx.ConnectError:
            return "❌ Lỗi: Không kết nối được Local Server (localhost:8000). Hãy kiểm tra xem đã chạy server chưa."
        except Exception as e:
            print(f"Error in specific generation: {e}")
            return f"Xin lỗi, có lỗi kỹ thuật khi gọi model nội bộ: {str(e)}"