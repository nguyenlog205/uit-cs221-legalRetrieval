import os
from groq import Groq
from typing import Optional

from src.utils import load_env


class GeneralGenerator:
    """
    Tạo phản hồi chung (lời chào) hoặc phản hồi dự phòng (fallback)
    khi hệ thống RAG không tìm được câu trả lời cụ thể, có giới hạn độ dài.
    (Đã chuyển sang dùng Groq API - Đồng bộ)
    """
    def __init__(
        self, 
        api_key: str, 
        model_id: str = "llama-3.1-8b-instant",
        max_output_tokens: int = 100
    ):
        self.client = Groq(api_key=api_key) 
        self.model_id = model_id
        self.max_output_tokens = max_output_tokens 
        self.general_temperature = 0.7 
        self.fallback_temperature = 0.3 
        print(f"-> GeneralGenerator (Groq) ready. Model: {self.model_id}. Max output: {self.max_output_tokens} tokens.")

    def generate_general(self, user_input: str) -> str:
        prompt = f"""Bạn là một trợ lý ảo thân thiện và lịch sự trong lĩnh vực thủ tục hành chính trong y tế công.
                    Hãy trả lời ngắn gọn (dưới 3 câu) câu hỏi hoặc lời chào sau của người dùng, sử dụng tiếng Việt.

                    Input: "{user_input}"
                    Response:"""
        try:
            response = self._call_model(prompt, self.general_temperature) 
            return response
        except Exception as e:
            print(f"Error in general generation: {e}")
            return "Tôi rất sẵn lòng giúp đỡ bạn!"

    def generate_fallback(self, query: str) -> str:
        prompt = f"""Bạn là Trợ lý ảo Hỗ trợ thủ tục hành chính trong Y tế Công.
                    Hãy trả lời một cách chuyên nghiệp và lịch sự, thừa nhận câu hỏi 
                    nhưng thông báo rằng bạn chưa tìm thấy thông tin chính xác trong cơ sở dữ liệu luật pháp.
                    KHÔNG cố gắng trả lời câu hỏi. KHÔNG sử dụng hơn 2 câu.

                    Câu hỏi chưa tìm được đáp án: "{query}"
                    Phản hồi dự phòng:"""
        try:
            response = self._call_model(prompt, self.fallback_temperature)
            return response
        except Exception as e:
            print(f"Error in fallback generation: {e}")
            return "Xin lỗi, hiện tại tôi chưa thể tìm thấy thông tin phù hợp với yêu cầu này. Bạn vui lòng thử lại bằng cách diễn đạt khác hoặc đặt câu hỏi về một chủ đề khác nhé."
            
    def _call_model(self, prompt: str, temperature: float) -> str:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=self.max_output_tokens
        )
        
        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    api_key = load_env("GROQ_API_KEY")
    if not api_key:
        print("Vui lòng đặt GROQ_API_KEY để chạy thử.")
        exit()

    general_generator = GeneralGenerator(api_key=api_key)

    while True:
        user_input = input("Nhập câu hỏi (hoặc 'exit' để thoát): ")
        if user_input == 'exit':
            break
        general_response = general_generator.generate_general(user_input)
        print(f"\nGeneral Response: {general_response}")
        print("-" * 60)

