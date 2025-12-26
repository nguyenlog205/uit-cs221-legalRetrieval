import pandas as pd
import re
import numpy as np
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import evaluate as hf_evaluate 

class RAGEvaluator:
    def __init__(self, openai_api_key: str = None, llm_model: str = "gpt-3.5-turbo"):
        """
        Khởi tạo Evaluator.
        - openai_api_key: Cần thiết nếu chạy evaluate_ragas.
        """
        self.openai_api_key = openai_api_key
        self.llm_model = llm_model
        
        # Load các metrics truyền thống từ HuggingFace
        print("Loading traditional metrics (ROUGE, BERTScore)...")
        self.rouge_metric = hf_evaluate.load('rouge')
        self.bert_metric = hf_evaluate.load('bertscore')

    def _clean_context(self, context_str: str) -> list[str]:
        """Chuyển đổi chuỗi Document object thành list string."""
        if not isinstance(context_str, str): return []
        # Regex lấy nội dung trong page_content='...'
        pattern = r"page_content=['\"](.*?)['\"](?:,|$|\))"
        matches = re.findall(pattern, context_str, re.DOTALL)
        return matches if matches else [context_str]

    def _prepare_ragas_data(self, df: pd.DataFrame) -> Dataset:
        """Chuẩn hóa dữ liệu cho Ragas."""
        eval_df = df.copy()
        
        # Mapping cột
        column_mapping = {
            'question': 'question',
            'model_output': 'answer',
            'answer': 'ground_truth'
        }
        eval_df = eval_df.rename(columns=column_mapping)
        
        # Xử lý context
        if 'context' in df.columns:
            eval_df['contexts'] = df['context'].apply(self._clean_context)
        
        # Chọn cột cần thiết
        req_cols = ['question', 'answer', 'contexts', 'ground_truth']
        # Lọc bỏ dòng nào bị NaN ở các cột quan trọng
        eval_df = eval_df[req_cols].dropna(subset=['question', 'answer'])
        
        return Dataset.from_pandas(eval_df)

    def evaluate_ragas(self, df: pd.DataFrame, metrics: list = None) -> pd.DataFrame:
        """
        Chấm điểm bằng Ragas (tốn phí API/Token).
        Trả về DataFrame gốc + các cột điểm Ragas.
        """
        if not self.openai_api_key:
            raise ValueError("Cần OpenAI API Key để chạy Ragas.")

        import os
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        
        # Cấu hình LLM
        llm = ChatOpenAI(model=self.llm_model)
        embeddings = OpenAIEmbeddings()
        
        # Mặc định dùng 5 metrics cơ bản
        if metrics is None:
            metrics = [
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy,
                answer_correctness
            ]
            
        dataset = self._prepare_ragas_data(df)
        
        print("--- Đang chạy Ragas Evaluation (LLM-based) ---")
        results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings
        )
        
        # Convert kết quả thành DF và merge vào DF gốc
        result_df = results.to_pandas()
        # Lưu ý: Ragas dataset có thể đã re-index, cẩn thận khi merge
        # Ở đây ta trả về result_df của Ragas (chứa đủ question/answer/score)
        return result_df

    def evaluate_traditional(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Chấm điểm bằng BERTScore và ROUGE (Chạy local).
        Trả về DataFrame gốc + các cột: rouge1, rouge2, rougeL, bert_f1.
        """
        print("--- Đang chạy Traditional Evaluation (BERTScore & ROUGE) ---")
        
        # Lấy list predictions và references
        # Fillna để tránh lỗi nếu có dòng trống
        preds = df['model_output'].fillna("").astype(str).tolist()
        refs = df['answer'].fillna("").astype(str).tolist()
        
        # 1. Tính ROUGE
        # rougeL: Longest Common Subsequence (quan trọng cho tóm tắt/câu dài)
        rouge_scores = self.rouge_metric.compute(predictions=preds, references=refs)
        
        # 2. Tính BERTScore
        # lang='vi' rất quan trọng để load đúng model tokenizer cho tiếng Việt
        bert_scores = self.bert_metric.compute(predictions=preds, references=refs, lang="vi")
        
        # Gán kết quả vào DataFrame copy
        result_df = df.copy()
        
        # Thêm cột ROUGE
        result_df['rouge1'] = rouge_scores['rouge1'] # Unigram overlap
        result_df['rougeL'] = rouge_scores['rougeL'] # Longest common subsequence
        
        # Thêm cột BERTScore (Lấy F1 là chỉ số cân bằng nhất)
        result_df['bert_f1'] = bert_scores['f1']
        result_df['bert_precision'] = bert_scores['precision']
        result_df['bert_recall'] = bert_scores['recall']
        
        return result_df

    def run_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chạy cả 2 loại đánh giá."""
        # 1. Chạy Traditional trước (nhanh, rẻ)
        df_trad = self.evaluate_traditional(df)
        
        # 2. Chạy Ragas
        # Lưu ý: Hàm evaluate_ragas trả về cấu trúc hơi khác, cần merge khéo
        # Để đơn giản, ta lấy output của evaluate_ragas và merge cột traditional vào
        df_ragas = self.evaluate_ragas(df)
        
        # Merge dựa trên index (giả sử thứ tự không đổi)
        # Cần cẩn thận: Ragas clean data có thể drop dòng lỗi.
        # Ở code production nên merge theo ID hoặc Question hash.
        
        # Lấy các cột traditional metrics từ df_trad gắn sang df_ragas
        trad_cols = ['rouge1', 'rougeL', 'bert_f1']
        
        # Reset index để đảm bảo concat đúng (giả định 2 bên số dòng bằng nhau sau khi clean)
        # Đây là cách ghép đơn giản nhất:
        final_df = pd.concat([df_ragas.reset_index(drop=True), df_trad[trad_cols].reset_index(drop=True)], axis=1)
        
        return final_df

# --- VÍ DỤ SỬ DỤNG ---
if __name__ == "__main__":
    # Giả lập dữ liệu từ file của bạn
    # data = pd.read_csv('llama_rag_result.csv') 
    
    # Dữ liệu mẫu để test
    data = pd.DataFrame({
        'question': ['Thủ tục gồm gì?'],
        'answer': ['Gồm CMND và Hộ khẩu.'], # Ground Truth
        'model_output': ['Hồ sơ bao gồm Chứng minh nhân dân và sổ hộ khẩu.'], # Bot trả lời
        'context': ["[Document(page_content='Hồ sơ gồm CMND, Hộ khẩu...', metadata={})]"]
    })

    evaluator = RAGEvaluator(openai_api_key="sk-proj-...") # Thay key của bạn vào
    
    # 1. Chỉ chạy BERT/ROUGE (Không tốn tiền)
    result_trad = evaluator.evaluate_traditional(data)
    print("Kết quả Traditional:")
    print(result_trad[['rougeL', 'bert_f1']])
    
    # 2. Chạy Ragas (Cần API Key)
    # result_ragas = evaluator.evaluate_ragas(data)
    # print(result_ragas[['faithfulness', 'answer_relevancy']])