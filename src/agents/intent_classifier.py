import os
import asyncio
from groq import AsyncGroq
from groq.types.chat import ChatCompletionMessageParam
from src.utils import load_env 


class IntentClassifier:
    def __init__(
        self,
        api_key,
        model_id: str = "llama-3.1-8b-instant",
    ):
        if not api_key:
            raise ValueError(f"API Key for {model_id} not found.")
            
        self.client = AsyncGroq(api_key=api_key)
        self.model_id = model_id
        print(f'>> Intention Classifier has been established successfully.')
        print('--- Model Details ---')
        print(f'Model ID: {self.model_id}')
        print()
    
    async def classify(self, user_input: str) -> str:
        prompt = f"""You are an Intent Classifier for a Public Health Support Bot in Vietnam.

Classification Rules:
- general: Greetings, small talk, gratitude, identity questions. (NO database search).
- specific: Public health questions, procedures, laws, medical practice, documents. (REQUIRES database search).
- WARNINGH: ONLY RETURN EITHER "general" OR "specific"!

Few-Shot Examples:
Input: "Xin chào, bạn có khỏe không?"
Class: general

Input: "Làm thế nào để xin giấy phép mở nhà thuốc?"
Class: specific

Input: "Nghị định 109 có còn hiệu lực không?"
Class: specific

Input: "Alo admin ơi."
Class: general

Input: "Thủ tục hành chính."
Class: specific

Current Task:
Input: "{user_input}"
Class:"""

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": "You are an expert Intent Classifier. Your output must be ONLY 'general' or 'specific'."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=0.0,
                max_tokens=10
            )
            
            result_text = response.choices[0].message.content.strip().lower()
            
            if "general" in result_text:
                return "general"
            elif "specific" in result_text:
                return "specific"
            else:
                return "specific"

        except Exception as e:
            return "specific"


def main():
    
    async def run_classifier_test():
        api_key = load_env("GROQ_API_KEY")
        if not api_key:
            print("Vui lòng đặt biến môi trường GROQ_API_KEY để chạy thử.")
            return

        try:
            classifier = IntentClassifier(api_key=api_key)

            test_queries = [
                "Bạn có phải là bot không?", 
                "Tôi muốn biết về quy trình cấp chứng chỉ hành nghề y.", 
                "Cảm ơn bạn nhiều.", 
                "Ai là bộ trưởng bộ y tế?",
            ]

            print("\n--- Running Classification Tests ---")
            for query in test_queries:
                intent = await classifier.classify(query)
                print(f"Input: '{query}' -> Intent: {intent}")

        except Exception as e:
            print(f"Failed to run test: {e}")

    asyncio.run(run_classifier_test())

# main()
# src.agents.intent_classifier