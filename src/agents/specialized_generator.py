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
        # 1. Chuẩn bị Context
        context_texts = []
        for doc in documents:
            source = doc.metadata.get("source", "Văn bản Luật")
            content = doc.page_content.replace("\n", " ") # Dọn sạch xuống dòng thừa
            context_texts.append(f"- Nguồn: {source}\n  Nội dung: {content}")
            
        context_block = "\n\n".join(context_texts)

        # 2. Tạo Prompt "Chuyên Gia"
        # Ép AI trả lời chi tiết, có trích dẫn và giọng văn chuyên nghiệp
        final_user_content = f"""
Bạn là một Trợ lý Luật sư AI chuyên về Y tế và Sức khỏe cộng đồng tại Việt Nam.
Nhiệm vụ của bạn là giải đáp thắc mắc dựa trên các trích dẫn luật được cung cấp.

--- DỮ LIỆU LUẬT ĐƯỢC CUNG CẤP ---
{context_block}

--- YÊU CẦU CÂU TRẢ LỜI ---
1. Trả lời CHÍNH XÁC dựa vào dữ liệu trên. Tuyệt đối không bịa đặt thông tin không có trong văn bản.
2. Giọng văn: Chuyên nghiệp, khách quan, dễ hiểu nhưng chặt chẽ về pháp lý.
3. Trích dẫn: Khi đưa ra thông tin, hãy nhắc đến tên văn bản nguồn (ví dụ: "Theo Luật Khám chữa bệnh...").
4. Định dạng: Sử dụng Markdown (xuống dòng, gạch đầu dòng) để trình bày rõ ràng.
5. Nếu dữ liệu không đủ để trả lời, hãy nói: "Xin lỗi, trong cơ sở dữ liệu hiện tại không có thông tin cụ thể về vấn đề này."

--- CÂU HỎI CỦA NGƯỜI DÙNG ---
{query}
"""

        # 3. Payload (Giữ nguyên, chỉ cần prompt xịn là đủ)
        payload = {
            "model": self.model_id,
            "messages": [
                # Thêm System Role để định hình nhân cách ngay từ đầu
                {"role": "system", "content": "Bạn là chuyên gia tư vấn pháp luật y tế Việt Nam tin cậy và chính xác."},
                {"role": "user", "content": final_user_content}
            ],
            "max_tokens": self.max_output_tokens,
            "temperature": 0.3 # Giữ thấp để AI ít "chém gió", bám sát luật hơn
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