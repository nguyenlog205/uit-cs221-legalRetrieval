import yaml
import time
from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# IMPORT CÁC THƯ VIỆN CẦN THIẾT
from langchain_community.retrievers import BM25Retriever
# ĐÃ BỎ IMPORT EnsembleRetriever

class DatabaseRetriever:
    """
    Công cụ truy vấn tài liệu sử dụng BM25 và Vector Search, 
    kết quả được hợp nhất thủ công và áp dụng MMR sau cùng (nếu có).
    """
    
    def __init__(
        self,
        vector_db: Chroma,
        embedding_model: Embeddings,
        all_documents: List[Document], # Danh sách TẤT CẢ Documents cho BM25
        mmr_lambda_mult: float = 0.7,
        k: int = 5, # Số lượng tài liệu top-k cuối cùng
        bm25_k: int = 10, # k cho BM25
        vector_k: int = 10, # k cho Vector Search
    ):
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.mmr_lambda_mult = mmr_lambda_mult
        self.k = k
        self.vector_k = vector_k # Giữ lại để dùng trong retrieve
        self.bm25_k = bm25_k # Giữ lại để dùng trong retrieve
        
        # --- 1. Khởi tạo BM25 Retriever (Lexical Search) ---
        self.bm25_retriever = BM25Retriever.from_documents(all_documents)
        self.bm25_retriever.k = bm25_k
        print(f"-> Khởi tạo BM25Retriever thành công ({len(all_documents)} docs).")

        # --- 2. Khởi tạo Vector Retriever (Semantic Search) ---
        # Vẫn dùng Similarity Search để có thể hợp nhất kết quả
        self.vector_retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": vector_k}
        )

        # --- 3. ĐÃ BỎ EnsembleRetriever ---
        # Lưu ý: Hybrid Search (RRF) đã bị loại bỏ
        print("-> Đã loại bỏ EnsembleRetriever (RRF).")
        print("-> DatabaseRetriever đã được khởi tạo thành công (Chế độ BM25 + Vector Riêng biệt).")

    @classmethod
    def from_config(cls, config_path: str = "configs/indexing_pipeline.yml") -> 'DatabaseRetriever':
        print(f"-> Loading config từ {config_path}...")
        cfg = cls._load_config(config_path)

        # --- Khởi tạo Embedding Model ---
        model_name = cfg['embedding']['model_name']
        device = cfg['embedding'].get('device', 'cpu')
        print(f"-> Khôi phục lại Embedding Model: {model_name} trên {device}...")
        
        embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True} 
        )

        # --- Kết nối vào DB ---
        persist_dir = cfg['data']['persist_directory']
        collection = cfg['data']['collection_name']
        print(f"-> Kết nối vào Vector DB tại: {persist_dir} (Collection: {collection})")
        
        vector_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding_model,
            collection_name=collection
        )
        
        # --- Tải TẤT CẢ documents cho BM25 Index ---
        try:
            db_client = vector_db.get() 
            all_documents = []
            if db_client['documents']:
                for content, metadata in zip(db_client['documents'], db_client['metadatas']):
                    all_documents.append(Document(page_content=content, metadata=metadata))
            
            if not all_documents:
                raise ValueError("ChromaDB không chứa Documents nào để xây dựng BM25 index.")
            
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tải Documents cho BM25: {e}")
        
        mmr_cfg = cfg.get('retrieval', {})
        
        return cls(
            vector_db=vector_db,
            embedding_model=embedding_model,
            all_documents=all_documents, 
            mmr_lambda_mult=mmr_cfg.get('lambda_mult', 0.7),
            k=mmr_cfg.get('k_final', 5), 
            bm25_k=mmr_cfg.get('bm25_k', 10),
            vector_k=mmr_cfg.get('vector_k', 10),
        )

    def retrieve(self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Hàm đi săn tìm tài liệu, sử dụng BM25 và Vector Search, sau đó hợp nhất thủ công.
        """
        print(f"\n[QUERY]: {query}")
        
        # --- BƯỚC 1: Thực hiện BM25 (Lexical) và Vector Search (Semantic) riêng biệt ---
        
        # LƯU Ý: Nếu dùng filters, bạn cần áp dụng filters cho cả hai retriever nếu chúng hỗ trợ.
        # Hiện tại BM25Retriever trong LangChain không hỗ trợ filter dễ dàng như Vector Retriever.
        
        bm25_docs = self.bm25_retriever.invoke(query)
        print(f"-> BM25 Search tìm thấy {len(bm25_docs)} đoạn.")

        # Vector Retriever: Vẫn dùng Similarity Search như ban đầu
        vector_docs = self.vector_retriever.invoke(query)
        print(f"-> Vector Search tìm thấy {len(vector_docs)} đoạn.")

        # --- BƯỚC 2: Hợp nhất Thủ công và Loại bỏ Trùng lặp ---
        
        # Tạo set chứa nội dung/source để kiểm tra trùng lặp
        combined_docs = {}
        for doc in bm25_docs + vector_docs:
            # Dùng page_content làm key để loại bỏ trùng lặp
            if doc.page_content not in combined_docs:
                combined_docs[doc.page_content] = doc

        # Chuyển đổi về List[Document]
        initial_docs = list(combined_docs.values())
        print(f"-> Hợp nhất thủ công (Loại trùng lặp) còn {len(initial_docs)} đoạn.")

        # --- BƯỚC 3: Lọc kết quả cuối cùng ---
        # Vì đã bỏ MMR và RRF, ta chỉ lấy top k đầu tiên của tập hợp nhất
        
        final_docs = initial_docs[:k] 
        
        print(f"-> Trả về {len(final_docs)} đoạn cuối cùng (top-k của tập hợp nhất).")
        
        for i, doc in enumerate(final_docs):
            source = doc.metadata.get('source', 'Unknown')
            content_preview = doc.page_content.replace('\n', ' ')
            print(f"   {i+1}. [{source}]: {content_preview[:80]}...")
            
        return final_docs

    @staticmethod
    def _load_config(path: str) -> Dict[str, Any]:
        """ Tải nội dung từ file cấu hình YAML. """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Không tìm thấy file config tại: '{path}'. Kiểm tra lại tên file và đường dẫn!")


# --- CHẠY THỬ (TEST) ---
if __name__ == "__main__":
    
    print("\n--- TEST: Khởi tạo ---")
    start_time = time.perf_counter()
    try:
        # File config phải tồn tại và đúng đường dẫn DB
        retriever = DatabaseRetriever.from_config(config_path="configs/indexing_pipeline.yml")
    except Exception as e:
        print(f"LỖI KHỞI TẠO: {e}.")
        print("Lưu ý: Không thể chạy block __main__ mà không có file config và DB.")
        exit()
        
    end_time = time.perf_counter()
    print(f'-> Thời gian khởi tạo: {end_time - start_time:.4f} giây')
    
    query_1 = r"Quy định về trách nhiệm của bệnh viện trong việc tiếp nhận người bệnh?"
    retriever.retrieve(query_1, k=5)

    query_2 = r"Trường hợp nào được hưởng 100% chi phí khi đi khám bảo hiểm?"
    retriever.retrieve(query_2, k=5)