import os
from typing import List, Dict, Any
from google import genai
from google.genai import types
from langchain_core.documents import Document

class SpecificGenerator:
    """
    Tạo phản hồi chi tiết (specific) bằng cách tổng hợp thông tin 
    từ câu hỏi của người dùng và các đoạn văn bản luật pháp được trích xuất.
    """
    def __init__(
        self, 
        api_key: str, 
        model_id: str = "gemini-2.5-flash",
        max_output_tokens: int = 512
    ):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens
        self.temperature = 0.1
        print(f"-> SpecificGenerator ready. Model: {self.model_id}.")

    async def generate_response(self, query: str, documents: List[Document]) -> str:
        """
        Tổng hợp câu trả lời dựa trên câu hỏi và các đoạn tài liệu luật pháp.

        Args:
            query: Câu hỏi ban đầu của người dùng.
            documents: Danh sách các đối tượng Document được trả về từ DatabaseRetriever.

        Returns:
            str: Câu trả lời tổng hợp và chính xác.
        """
        # --- Định dạng nguồn tài liệu ---
        context_texts = [
            f"--- Tài liệu: {doc.metadata.get('source', 'Văn bản Luật')}\n"
            f"Nội dung: {doc.page_content}\n"
            for doc in documents
        ]
        context = "\n\n".join(context_texts)
        
        # --- Xây dựng Prompt tổng hợp (RAG Prompting) ---
        prompt = f"""Bạn là một chuyên gia hỗ trợ tìm hiểu Luật Y tế và Sức khỏe Công cộng tại Việt Nam.
                     Nhiệm vụ của bạn là trả lời câu hỏi của người dùng dựa trên CHỈ các tài liệu pháp luật được cung cấp dưới đây.
                     
                     Yêu cầu:
                     1. Chỉ sử dụng thông tin từ phần CONTEXT (Nguồn tài liệu). KHÔNG sử dụng kiến thức bên ngoài.
                     2. Trích dẫn Tên văn bản luật (Source) mà bạn sử dụng để trả lời vào cuối câu trả lời.
                     3. Trả lời chi tiết, đầy đủ, và dễ hiểu bằng tiếng Việt.
                     4. Nếu các tài liệu không chứa đủ thông tin để trả lời, hãy báo rằng không thể tìm thấy thông tin cụ thể trong nguồn.

                     --- CONTEXT (Nguồn tài liệu) ---
                     {context}

                     --- CÂU HỎI NGƯỜI DÙNG ---
                     {query}
                     
                     --- TRẢ LỜI CỦA CHUYÊN GIA ---"""

        try:
            response = await self.client.models.generate_content_async(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens 
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error in specific generation: {e}")
            return "Xin lỗi, đã xảy ra lỗi trong quá trình tổng hợp câu trả lời từ nguồn. Vui lòng thử lại sau."