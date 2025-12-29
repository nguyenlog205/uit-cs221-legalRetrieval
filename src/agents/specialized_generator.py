import httpx
from typing import List, Optional
from langchain_core.documents import Document

class SpecificGenerator:
    """
    Tạo phản hồi chi tiết bằng cách gọi vào Groq API.
    Giữ nguyên logic và flow xử lý, chỉ thay đổi đích đến (Endpoint) và format payload.
    """
    def __init__(
        self, 
        api_key: str,  # Bắt buộc phải có API Key
        model_id: str = "llama-3.1-8b-instant", # Tên model của Groq
        max_output_tokens: int = 1024,
        api_url: str = "https://api.groq.com/openai/v1/chat/completions", # URL chuẩn của Groq
        timeout: float = 60.0
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        
        print(f"-> SpecificGenerator (Groq API) ready. Target: {self.api_url} | Model: {self.model_id}")

    async def generate_response(self, query: str, documents: List[Document]) -> str:
        """
        Tổng hợp câu trả lời từ Groq API.
        Signature hàm giữ nguyên: (query, documents) -> str
        """
        
        # 1. Chuẩn bị Context (Giữ nguyên logic cũ)
        context_texts = [
            f"--- Tài liệu: {doc.metadata.get('source', 'Văn bản Luật')}\n"
            f"Nội dung: {doc.page_content}\n"
            for doc in documents
        ]
        context_block = "\n\n".join(context_texts)

        # 2. Tạo Prompt (Giữ nguyên logic gộp context)
        final_user_content = f"""Dựa vào các thông tin dưới đây để trả lời câu hỏi.

--- CONTEXT (Nguồn tài liệu) ---
{context_block}

--- CÂU HỎI NGƯỜI DÙNG ---
{query}
"""

        # 3. Tạo Payload (Thay đổi format JSON để khớp chuẩn OpenAI/Groq)
        # Logic không đổi: vẫn gửi final_user_content đi
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": final_user_content}
            ],
            "max_tokens": self.max_output_tokens,
            "temperature": 0.1 # Thêm tham số này để câu trả lời ổn định hơn (optional)
        }

        # Header bắt buộc cho Groq
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 4. Gọi API
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url, 
                    json=payload,
                    headers=headers
                )
                
                # Ném lỗi nếu status code không phải 200
                response.raise_for_status() 
                result_json = response.json()
                
                # Trả về kết quả (Parse theo chuẩn OpenAI output mà Groq trả về)
                # Thay vì .get("answer"), ta lấy đường dẫn chuẩn: choices[0].message.content
                if "choices" in result_json and len(result_json["choices"]) > 0:
                    return result_json["choices"][0]["message"]["content"]
                else:
                    return "Không tìm thấy câu trả lời từ Groq."

        except httpx.ConnectError:
            return "❌ Lỗi: Không kết nối được tới Server Groq. Vui lòng kiểm tra internet hoặc API URL."
        except httpx.HTTPStatusError as e:
             return f"❌ Lỗi API Groq ({e.response.status_code}): {e.response.text}"
        except Exception as e:
            print(f"Error in specific generation: {e}")
            return f"Xin lỗi, có lỗi kỹ thuật khi gọi model: {str(e)}"