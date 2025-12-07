import os
from google import genai
from google.genai import types
from typing import Optional # Giữ lại import này nếu có

class GeneralGenerator:
    """
    Tạo phản hồi chung (lời chào) hoặc phản hồi dự phòng (fallback)
    khi hệ thống RAG không tìm được câu trả lời cụ thể, có giới hạn độ dài.
    """
    def __init__(
        self, 
        api_key: str, 
        model_id: str = "gemini-2.5-flash-lite",
        max_output_tokens: int = 100
    ):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens 
        self.general_temperature = 0.7 
        self.fallback_temperature = 0.3 
        print(f"-> GeneralGenerator ready. Max output: {self.max_output_tokens} tokens.")

    async def generate_general(self, user_input: str) -> str:
        """
        Tạo phản hồi cho các ý định 'general' (chào hỏi, cảm ơn,...)
        """
        prompt = f"""Bạn là một trợ lý ảo thân thiện và lịch sự trong lĩnh vực y tế công cộng.
                    Hãy trả lời ngắn gọn (dưới 3 câu) câu hỏi hoặc lời chào sau của người dùng, sử dụng tiếng Việt.

                    Input: "{user_input}"
                    Response:"""
        try:
            response = await self._call_model(prompt, self.general_temperature)
            return response
        except Exception as e:
            print(f"Error in general generation: {e}")
            return "Tôi rất sẵn lòng giúp đỡ bạn!"


    async def generate_fallback(self, query: str) -> str:
        """
        Tạo phản hồi dự phòng (fallback) khi hệ thống không tìm thấy tài liệu.
        """
        prompt = f"""Bạn là Trợ lý ảo Hỗ trợ Y tế Công cộng.
                    Hãy trả lời một cách chuyên nghiệp và lịch sự, thừa nhận câu hỏi 
                    nhưng thông báo rằng bạn chưa tìm thấy thông tin chính xác trong cơ sở dữ liệu luật pháp.
                    KHÔNG cố gắng trả lời câu hỏi. KHÔNG sử dụng hơn 2 câu.

                    Câu hỏi chưa tìm được đáp án: "{query}"
                    Phản hồi dự phòng:"""
        try:
            response = await self._call_model(prompt, self.fallback_temperature)
            return response
        except Exception as e:
            print(f"Error in fallback generation: {e}")
            return "Xin lỗi, hiện tại tôi chưa thể tìm thấy thông tin phù hợp với yêu cầu này. Bạn vui lòng thử lại bằng cách diễn đạt khác hoặc đặt câu hỏi về một chủ đề khác nhé."
            
            
    async def _call_model(self, prompt: str, temperature: float) -> str:
        """Hàm nội bộ để gọi API Gemini bất đồng bộ."""
        response = await self.client.models.generate_content_async(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=self.max_output_tokens 
            ) 
        )
        return response.text.strip()