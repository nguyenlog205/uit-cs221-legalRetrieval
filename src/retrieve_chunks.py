import yaml
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Top - down
# Đang cần cái gì
# Cần embedding model -> Cần a, b, c ....

class RetrievalPipeline:
    def __init__(
        self, 
        config_path: str = "configs/indexing_pipeline.yml"
    ):
        print(f"-> Loading config từ {config_path}...")
        self.cfg = self._load_config(config_path)

        # 2. Re-load Embedding Model
        # (Bắt buộc phải giống hệt lúc Indexing)
        model_name = self.cfg['embedding']['model_name']
        device = self.cfg['embedding'].get('device', 'cpu')
        print(f"-> Khôi phục lại Embedding Model: {model_name} trên {device}...")
        
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )

        # 3. Kết nối vào ChromaDB đã có sẵn
        persist_dir = self.cfg['data']['persist_directory']
        collection = self.cfg['data']['collection_name']
        print(f"-> Kết nối vào Vector DB tại: {persist_dir} (Collection: {collection})")
        
        self.vector_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embedding_model,
            collection_name=collection
        )

    def retrieve(self, query: str, k: int = 5, filters: Dict = None) -> List[Document]:
        """
        Hàm đi săn tìm tài liệu.
        - query: Câu hỏi của người dùng.
        - k: Số lượng tài liệu muốn lấy.
        - filters: Bộ lọc metadata (Ví dụ: chỉ tìm văn bản còn hiệu lực).
        """
        print(f"\n[QUERY]: {query}")
        
        # Anh dùng search_type="mmr" (Maximal Marginal Relevance)
        # Để nó không trả về 5 đoạn văn giống hệt nhau, mà nó sẽ tìm những đoạn
        # vừa liên quan nhất, nhưng lại vừa khác biệt nhau.
        retriever = self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k, 
                "fetch_k": k * 2, # Lấy 10 thằng rồi lọc ra 5 thằng đa dạng nhất
                "lambda_mult": 0.7, # Độ đa dạng (0.5 là cân bằng, 0.7 thiên về chính xác)
                "filter": filters # Cái này quan trọng với luật nè
            }
        )
        
        docs = retriever.invoke(query)
        
        # In kết quả ra cho em dễ kiểm tra
        print(f"-> Tìm thấy {len(docs)} đoạn liên quan:")
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown')
            # Cắt ngắn nội dung hiển thị cho đỡ rác màn hình
            content_preview = doc.page_content[:5000].replace('\n', ' ')
            print(f"   {i+1}. [{source}]: {content_preview}...")
            
        return docs

    def _load_config(self, path):
        # Thêm encoding='utf-8' vào là hết lỗi.
        # Nhớ check kỹ xem file của em là .yaml hay .yml
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Anh thêm cái này để em biết đường mà mò file
            raise FileNotFoundError(f"Không tìm thấy file config tại: '{path}'. Em kiểm tra lại tên file và đường dẫn đi!")

# --- CHẠY THỬ (TEST) ---
import time
if __name__ == "__main__":
    # --- Khởi tạo ---
    start_time = time.perf_counter()
    retriever = RetrievalPipeline(config_path="configs/indexing_pipeline.yml")
    end_time = time.perf_counter()
    print(f'-> Thời gian khởi tạo: {end_time - start_time:.4f} giây')
    
    # --- Truy vấn 1 ---
    start_time = time.perf_counter()
    query_1 = "Người bệnh có những quyền lợi gì khi khám chữa bệnh?"
    results = retriever.retrieve(query_1, k=5)
    end_time = time.perf_counter()
    print(f'-> Thời gian khởi tạo: {end_time - start_time:.4f} giây')
    
    # --- Truy vấn 2 ---
    start_time = time.perf_counter()
    query_2 = "Quy định về nồng độ cồn"
    results_2 = retriever.retrieve(
        query_2, 
        k=3, 
        filters={
            "status": "Còn hiệu lực"
        }
    )
    end_time = time.perf_counter()
    print(f'-> Thời gian khởi tạo: {end_time - start_time:.4f} giây')