import yaml
import time
from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


class DatabaseRetriever:
    """
    Công cụ truy vấn tài liệu (Retriever) từ Vector Database (ChromaDB), 
    sử dụng cơ chế tìm kiếm MMR (Maximal Marginal Relevance) để đa dạng hóa kết quả.
    """
    
    def __init__(
        self,
        vector_db: Chroma,
        embedding_model: Embeddings,
        mmr_lambda_mult: float = 0.7,
        mmr_fetch_k_multiplier: int = 2
    ):
        """
        Khởi tạo DatabaseRetriever.
        
        Args:
            vector_db: Instance của Chroma đã được kết nối.
            embedding_model: Instance của Embedding Model đã được tải.
            mmr_lambda_mult: Tham số lambda_mult cho MMR (0.0 đến 1.0).
            mmr_fetch_k_multiplier: Hệ số nhân để xác định fetch_k (fetch_k = k * multiplier).
        """
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        
        self.mmr_lambda_mult = mmr_lambda_mult
        self.mmr_fetch_k_multiplier = mmr_fetch_k_multiplier
        print("-> DatabaseRetriever đã được khởi tạo thành công.")


    @classmethod
    def from_config(cls, config_path: str = "configs/indexing_pipeline.yml") -> 'DatabaseRetriever':
        """
        Phương thức factory để khởi tạo DatabaseRetriever từ file cấu hình YAML.
        """
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

        mmr_cfg = cfg.get('retrieval', {})
        
        return cls(
            vector_db=vector_db,
            embedding_model=embedding_model,
            mmr_lambda_mult=mmr_cfg.get('lambda_mult', 0.7),
            mmr_fetch_k_multiplier=mmr_cfg.get('fetch_k_multiplier', 2)
        )

    def retrieve(self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Hàm đi săn tìm tài liệu, sử dụng cơ chế MMR.

        Args:
            query: Câu hỏi của người dùng.
            k: Số lượng tài liệu muốn lấy (top-k).
            filters: Bộ lọc metadata.

        Returns:
            List[Document]: Danh sách các tài liệu liên quan.
        """
        print(f"\n[QUERY]: {query}")
        fetch_k = k * self.mmr_fetch_k_multiplier
        retriever = self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k, 
                "fetch_k": fetch_k, 
                "lambda_mult": self.mmr_lambda_mult, 
                "filter": filters
            }
        )
        
        docs = retriever.invoke(query)
        
        print(f"-> Tìm thấy {len(docs)} đoạn liên quan:")
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown')
            content_preview = doc.page_content.replace('\n', ' ')
            print(f"   {i+1}. [{source}]: {content_preview[:80]}...")
            
        return docs

    @staticmethod
    def _load_config(path: str) -> Dict[str, Any]:
        """ Tải nội dung từ file cấu hình YAML. """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Không tìm thấy file config tại: '{path}'. Em kiểm tra lại tên file và đường dẫn đi!")


# --- CHẠY THỬ (TEST) ---
if __name__ == "__main__":
    print("\n--- TEST: Khởi tạo ---")
    start_time = time.perf_counter()
    try:
        retriever = DatabaseRetriever.from_config(config_path="configs/indexing_pipeline.yml")
    except Exception as e:
        print(f"LỖI KHỞI TẠO: {e}. Vui lòng kiểm tra file config và thư mục DB.")
        print("Lưu ý: Không thể chạy block __main__ mà không có file config và DB.")
        exit()
        
    end_time = time.perf_counter()
    print(f'-> Thời gian khởi tạo: {end_time - start_time:.4f} giây')
    
    query_1 = "Người bệnh có những quyền lợi gì khi khám chữa bệnh?"
    retriever.retrieve(query_1, k=5)