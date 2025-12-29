import pandas as pd
import re
import os
import argparse
import sys
from datasets import Dataset
import warnings

# Tắt warning
warnings.filterwarnings("ignore")

try:
    # Import Ragas metrics
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness
    )
    from ragas import evaluate, RunConfig
    
    # --- THAY ĐỔI: Dùng Google Gemini thay vì Groq ---
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # Vẫn giữ BGE-M3 để làm Embeddings (Retrieval chấm điểm)
    from langchain_community.embeddings import HuggingFaceEmbeddings

except ImportError as e:
    print(f"Lỗi thiếu thư viện: {e}")
    print("👉 Hãy chạy: pip install langchain-google-genai")
    sys.exit(1)

class RAGEvaluator:
    # Đổi tên tham số key cho rõ ràng, mặc định model là gemini-1.5-flash (Ngon-Bổ-Rẻ)
    def __init__(self, google_api_key: str = None, llm_model: str = "gemini-3-flash-preview"):
        self.google_api_key = google_api_key
        self.llm_model = llm_model
        
        print("⏳ Đang khởi tạo Embeddings (BGE-M3)...")
        # Embeddings vẫn chạy local bằng GPU của ông cho nhanh
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cuda', 'trust_remote_code': True}, 
            encode_kwargs={'normalize_embeddings': True}
        )

    def _prepare_ragas_data(self, df: pd.DataFrame) -> Dataset:
        eval_df = df.copy()
        
        def clean_context(ctx):
            if not isinstance(ctx, str): return []
            pattern = r"page_content=['\"](.*?)['\"](?:,|$|\))"
            matches = re.findall(pattern, ctx, re.DOTALL)
            return matches if matches else [ctx]

        if 'context' in eval_df.columns:
            eval_df['contexts'] = eval_df['context'].apply(clean_context)
        
        rename_map = {
            'question': 'question', 
            'model_output': 'answer', 
            'answer': 'ground_truth'
        }
        actual_map = {k: v for k, v in rename_map.items() if k in eval_df.columns}
        eval_df = eval_df.rename(columns=actual_map)
        
        req = [c for c in ['question', 'answer', 'contexts', 'ground_truth'] if c in eval_df.columns]
        return Dataset.from_pandas(eval_df.dropna(subset=req))

    def evaluate_ragas(self, df: pd.DataFrame, api_key: str = None) -> pd.DataFrame:
        final_key = api_key if api_key else self.google_api_key
        if not final_key: raise ValueError("Cần Google API Key!")

        # --- CẤU HÌNH GOOGLE GEMINI ---
        llm = ChatGoogleGenerativeAI(
            google_api_key=final_key,
            model=self.llm_model,
            temperature=0, # Nhiệt độ 0 để chấm điểm khách quan nhất
            convert_system_message_to_human=True # Fix lỗi format tin nhắn cũ
        )
        
        dataset = self._prepare_ragas_data(df)
        
        metrics = [context_precision, context_recall, faithfulness, answer_relevancy, answer_correctness]
        
        # Cấu hình chạy: Google cho phép 15 requests/phút (RPM) ở gói Free
        # Để an toàn tuyệt đối, ta chạy max_workers=1 hoặc 2.
        # Nếu ông muốn nhanh hơn xíu có thể chỉnh lên 2, nhưng 1 là an toàn nhất.
        run_config = RunConfig(
            max_workers=1,  
            timeout=120,
            max_retries=10,
            max_wait=30
        )

        print(f"🚀 Đang chấm điểm bằng Ragas (Model: {self.llm_model})...")
        print("⚠️ Đang dùng Google Gemini. Chế độ chạy tuần tự để né Rate Limit.")
        
        results = evaluate(
            dataset=dataset, 
            metrics=metrics, 
            llm=llm, 
            embeddings=self.embeddings,
            run_config=run_config
        )
        return results.to_pandas()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True)
    
    # Đổi tên tham số CLI cho khớp context
    parser.add_argument('--api_key', type=str, required=True, help="Google AI Studio API Key")
    
    parser.add_argument('--mode', type=str, default="ragas") 
    parser.add_argument('--model', type=str, default="gemini-3-flash-preview")
    args = parser.parse_args()

    filename = os.path.basename(args.input)
    out_dir = "data/evaluation"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    print(f"📂 Đọc file: {args.input}")
    df = pd.read_csv(args.input)

    try:
        evaluator = RAGEvaluator(llm_model=args.model)
        
        print("--- Bắt đầu chế độ Ragas (Gemini Powered) ---")
        result_df = evaluator.evaluate_ragas(df, api_key=args.api_key)
            
        result_df.to_csv(out_path, index=False)
        print(f"✅ Xong! Kết quả lưu tại: {out_path}")

    except Exception as e:
        print(f"\n❌ LỖI: {e}")

if __name__ == "__main__":
    main()