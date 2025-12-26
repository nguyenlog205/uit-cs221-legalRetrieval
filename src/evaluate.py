import pandas as pd
import re
import os
import argparse
import sys
from datasets import Dataset

# Import các thư viện Ragas và LangChain
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness
    )
    # THAY ĐỔI: Dùng Groq cho LLM và HuggingFace cho Embeddings
    from langchain_groq import ChatGroq
    from langchain_huggingface import HuggingFaceEmbeddings
    import evaluate as hf_evaluate
except ImportError as e:
    print(f"Lỗi: Thiếu thư viện. Hãy chạy: pip install langchain-groq langchain-huggingface sentence-transformers ragas pandas datasets evaluate rouge_score bert_score")
    print(f"Chi tiết: {e}")
    sys.exit(1)

class RAGEvaluator:
    def __init__(self, groq_api_key: str = None, llm_model: str = "llama3-70b-8192"):
        """
        Khởi tạo Evaluator với Groq.
        Mặc định dùng model Llama 3 70B (Rất mạnh cho việc chấm điểm).
        """
        self.groq_api_key = groq_api_key
        self.llm_model = llm_model
        
        # Load metrics truyền thống (BERTScore, ROUGE)
        self.rouge_metric = None
        self.bert_metric = None

        # Cấu hình Embeddings (Chạy local miễn phí)
        # model_name='keepitreal/vietnamese-sbert' hoặc 'BAAI/bge-m3' rất tốt cho tiếng Việt
        print("⏳ Đang tải model Embeddings (HuggingFace)...")
        self.embeddings = HuggingFaceEmbeddings(model_name="keepitreal/vietnamese-sbert")

    def _load_trad_metrics(self):
        if self.rouge_metric is None:
            print("⏳ Đang tải ROUGE metric...")
            self.rouge_metric = hf_evaluate.load('rouge')
        if self.bert_metric is None:
            print("⏳ Đang tải BERTScore metric (có thể tốn thời gian lần đầu)...")
            self.bert_metric = hf_evaluate.load('bertscore')

    def _clean_context(self, context_str: str) -> list[str]:
        """Chuyển đổi chuỗi Document object thành list string."""
        if not isinstance(context_str, str): return []
        pattern = r"page_content=['\"](.*?)['\"](?:,|$|\))"
        matches = re.findall(pattern, context_str, re.DOTALL)
        return matches if matches else [context_str]

    def _prepare_ragas_data(self, df: pd.DataFrame) -> Dataset:
        eval_df = df.copy()
        
        # Mapping cột cho khớp với chuẩn Ragas
        column_mapping = {
            'question': 'question',
            'model_output': 'answer',
            'answer': 'ground_truth'
        }
        actual_mapping = {k: v for k, v in column_mapping.items() if k in eval_df.columns}
        eval_df = eval_df.rename(columns=actual_mapping)
        
        # Xử lý context
        if 'context' in df.columns:
            eval_df['contexts'] = df['context'].apply(self._clean_context)
        elif 'contexts' not in eval_df.columns:
             print("⚠️ Cảnh báo: Không tìm thấy cột 'context'. Điểm Context Precision/Recall sẽ lỗi.")
        
        req_cols = [c for c in ['question', 'answer'] if c in eval_df.columns]
        eval_df = eval_df.dropna(subset=req_cols)
        
        return Dataset.from_pandas(eval_df)

    def evaluate_ragas(self, df: pd.DataFrame, api_key: str = None) -> pd.DataFrame:
        """Chạy đánh giá bằng Groq LLM"""
        final_key = api_key if api_key else self.groq_api_key
        
        if not final_key:
            raise ValueError("❌ Lỗi: Cần Groq API Key để chạy mode Ragas.")

        # Khởi tạo ChatGroq
        llm = ChatGroq(
            groq_api_key=final_key,
            model_name=self.llm_model,
            temperature=0 # Để chấm điểm ổn định nhất
        )
        
        dataset = self._prepare_ragas_data(df)
        
        metrics = [
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
            answer_correctness
        ]
        
        print(f"🚀 Đang chạy Ragas Evaluation với model {self.llm_model}...")
        results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=self.embeddings # Dùng HF embeddings đã load ở init
        )
        
        return results.to_pandas()

    def evaluate_traditional(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chạy đánh giá bằng thuật toán (BERTScore, ROUGE)"""
        self._load_trad_metrics()
        print("🚀 Đang chạy Traditional Evaluation...")
        
        preds = df['model_output'].fillna("").astype(str).tolist()
        refs = df['answer'].fillna("").astype(str).tolist()
        
        rouge_scores = self.rouge_metric.compute(predictions=preds, references=refs)
        # lang='vi' rất quan trọng
        bert_scores = self.bert_metric.compute(predictions=preds, references=refs, lang="vi")
        
        result_df = df.copy()
        result_df['rouge1'] = rouge_scores['rouge1']
        result_df['rougeL'] = rouge_scores['rougeL']
        result_df['bert_f1'] = bert_scores['f1']
        
        return result_df

    def run_all(self, df: pd.DataFrame, api_key: str = None) -> pd.DataFrame:
        df_trad = self.evaluate_traditional(df)
        df_ragas = self.evaluate_ragas(df, api_key=api_key)
        
        trad_cols = ['rouge1', 'rougeL', 'bert_f1']
        final_df = pd.concat([df_ragas.reset_index(drop=True), df_trad[trad_cols].reset_index(drop=True)], axis=1)
        return final_df

# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description="Tool đánh giá RAG System (Groq + Traditional)")
    
    parser.add_argument('--input', type=str, required=True, help="Input CSV file")
    parser.add_argument('--output', type=str, default="groq_eval_result.csv", help="Output CSV file")
    # Đổi tên tham số thành groq_api_key
    parser.add_argument('--api_key', type=str, default=None, help="Groq API Key (bắt buộc nếu mode ragas/all)")
    parser.add_argument('--mode', type=str, default="all", choices=['all', 'ragas', 'traditional'])
    # Default model đổi sang Llama 3 trên Groq
    parser.add_argument('--model', type=str, default="llama3-70b-8192", help="Groq Model ID (vd: llama3-70b-8192, mixtral-8x7b-32768)")

    args = parser.parse_args()

    print(f"📂 Đang đọc file: {args.input}")
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return

    # Khởi tạo Evaluator
    evaluator = RAGEvaluator(llm_model=args.model)

    try:
        if args.mode == 'traditional':
            result_df = evaluator.evaluate_traditional(df)
        
        elif args.mode == 'ragas':
            result_df = evaluator.evaluate_ragas(df, api_key=args.api_key)
            
        elif args.mode == 'all':
            result_df = evaluator.run_all(df, api_key=args.api_key)
            
        result_df.to_csv(args.output, index=False)
        print(f"✅ Đã hoàn tất! Kết quả lưu tại: {args.output}")
        
        cols_to_show = [c for c in ['question', 'faithfulness', 'bert_f1', 'rougeL'] if c in result_df.columns]
        if cols_to_show:
            print("\n--- Preview kết quả ---")
            print(result_df[cols_to_show].head(3))

    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    main()