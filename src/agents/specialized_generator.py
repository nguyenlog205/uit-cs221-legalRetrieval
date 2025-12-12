import os
from typing import List, Dict, Any

# SỬA: Thay thế google.genai bằng groq và AsyncGroq
from groq import AsyncGroq 
from groq.types.chat import ChatCompletionMessageParam # Để định nghĩa Messages
from langchain_core.documents import Document

# Giả sử src.utils.load_env được xử lý ở ngoài hoặc đã import

class SpecificGenerator:
    """
    Tạo phản hồi chi tiết (specific) bằng cách tổng hợp thông tin 
    từ câu hỏi của người dùng và các đoạn văn bản luật pháp được trích xuất (Sử dụng Groq).

    """
    def __init__(
        self, 
        api_key: str, 

        # SỬA: Sử dụng mô hình Groq. Mixtral 8x22b hoặc Llama 3.1 70B thường tốt cho RAG.
        model_id: str = "llama-3.1-8b-instant",
        max_output_tokens: int = 512
    ):
        # SỬA: Khởi tạo AsyncGroq Client
        self.client = AsyncGroq(api_key=api_key)
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens
        self.temperature = 0.1 # Nhiệt độ thấp cho RAG để tăng tính xác thực
        print(f"-> SpecificGenerator (Groq) ready. Model: {self.model_id}. Max output: {self.max_output_tokens} tokens.")


    async def generate_response(self, query: str, documents: List[Document]) -> str:
        """
        Tổng hợp câu trả lời dựa trên câu hỏi và các đoạn tài liệu luật pháp.


        Args:
            query: Câu hỏi ban đầu của người dùng.
            documents: Danh sách các đối tượng Document được trả về từ DatabaseRetriever.

        Returns:
            str: Câu trả lời tổng hợp và chính xác.
        """
        
        context_texts = [
            f"--- Tài liệu: {doc.metadata.get('source', 'Văn bản Luật')}\n"
            f"Nội dung: {doc.page_content}\n"
            for doc in documents
        ]
        context = "\n\n".join(context_texts)
        

        # --- Xây dựng System Prompt và User Prompt (RAG Prompting) ---
        
        # Sử dụng System Prompt để định vị vai trò của AI
        system_prompt = f"""Bạn là một chuyên gia hỗ trợ tìm hiểu Luật Y tế và Sức khỏe Công cộng tại Việt Nam.
                         Nhiệm vụ của bạn là trả lời câu hỏi của người dùng dựa trên CHỈ các tài liệu pháp luật được cung cấp.

                         Quy tắc trả lời:
                         1. Chỉ sử dụng thông tin từ phần CONTEXT (Nguồn tài liệu). KHÔNG sử dụng kiến thức bên ngoài.
                         2. Trích dẫn Tên văn bản luật (Source) mà bạn sử dụng để trả lời vào cuối câu trả lời (ví dụ: [Nguồn: Nghị định 15/2023/NĐ-CP]).
                         3. Trả lời chi tiết, đầy đủ, và dễ hiểu bằng tiếng Việt.
                         4. Nếu các tài liệu không chứa đủ thông tin để trả lời, hãy báo rằng không thể tìm thấy thông tin cụ thể trong nguồn."""

        # Sử dụng User Prompt chứa context và query
        user_prompt = f"""--- CONTEXT (Nguồn tài liệu) ---
                         {context}

                         --- CÂU HỎI NGƯỜI DÙNG ---
                         {query}
                         
                         --- TRẢ LỜI CỦA CHUYÊN GIA ---"""

        # Định dạng thành Chat Messages cho Groq
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # SỬA: Thay thế generate_content_async bằng await client.chat.completions.create
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens # max_output_tokens đổi thành max_tokens
            )
            
            # Trích xuất nội dung từ phản hồi Groq
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in specific generation: {e}")
            return "Xin lỗi, đã xảy ra lỗi trong quá trình tổng hợp câu trả lời từ nguồn. Vui lòng thử lại sau."