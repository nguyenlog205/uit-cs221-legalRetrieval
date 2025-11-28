import json
import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils import extract_config

class IndexingPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        
        print(f"-> Init Embedding: {self.cfg['embedding']['model_name']}")

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.cfg['embedding']['model_name'],
            model_kwargs={'device': self.cfg['embedding'].get('device', 'cuda')},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 64} 
        )
        
        self.sub_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=200,
            separators=["\n", ";", ".", " "]
        )

    def load_and_split_json(self, json_path: str) -> List[Document]:
        """
        Hàm này làm 3 việc một lúc: 
        1. Đọc JSON.
        2. Tách Metadata.
        3. Cắt 'Nội dung' theo Điều luật.
        """
        print(f"-> Đang đọc file JSON từ: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON: {e}")
            return []

        final_docs = []

        # Duyệt qua từng văn bản trong file JSON (Luật, Nghị định...)
        for entry in data:
            # A. Tách Metadata (Thông tin nền)
            # Em muốn lưu cái gì vào DB thì nhặt ở đây
            base_metadata = {
                "source": entry.get("Tên văn bản", "Unknown"),
                "link": entry.get("Link chi tiết", ""),
                "status": entry.get("Trạng thái", ""),
                "effective_date": entry.get("Hiệu lực", ""),
                "type": "law_document"
            }
            
            full_text = entry.get("Nội dung", "")
            if not full_text: continue

            # B. Chiến thuật Cắt: Dựa vào "Điều"
            # Regex này tìm chữ "Điều" đứng đầu dòng hoặc sau ký tự xuống dòng
            # (?=...) là lookahead để giữ lại chữ "Điều"
            pattern = r"(?=\nĐiều \d+)" 
            
            # Tách thành các mảng lớn (Mỗi mảng là một Điều hoặc phần mở đầu)
            raw_chunks = re.split(pattern, full_text)

            for chunk_text in raw_chunks:
                chunk_text = chunk_text.strip()
                if not chunk_text: continue
                
                # Bỏ qua mấy đoạn rác ngắn ngủn (dưới 10 ký tự)
                if len(chunk_text) < 10: continue

                # C. Xử lý chunk quá dài (Recursive Splitter)
                if len(chunk_text) > 1500:
                    # Nếu 1 Điều dài quá -> Cắt nhỏ tiếp
                    sub_docs = self.sub_splitter.create_documents(
                        [chunk_text], 
                        metadatas=[base_metadata] # Gán metadata cho từng mảnh con
                    )
                    final_docs.extend(sub_docs)
                else:
                    # Nếu vừa miếng -> Tạo 1 Document
                    doc = Document(
                        page_content=chunk_text,
                        metadata=base_metadata
                    )
                    final_docs.append(doc)

        print(f"-> Xử lý xong {len(data)} văn bản gốc. Tạo ra {len(final_docs)} chunks (Điều luật).")
        
        # Preview thử 1 cái cho em xem nó trông thế nào
        if final_docs:
            print(f"   [Preview]: {final_docs[5].page_content[:100]}...")
            print(f"   [Metadata]: {final_docs[5].metadata}")

        return final_docs

    def run(
        self,
        list_of_keywords: List[str],
        pre_path = r'data\legal_documents\raw\metadata_law_'
    ):
        all_documents = [] # Tạo một cái túi lớn chứa toàn bộ data

        # BƯỚC 1: CHỈ ĐỌC VÀ CẮT (CPU làm việc)
        print("--- GIAI ĐOẠN 1: ĐỌC VÀ XỬ LÝ TEXT ---")
        for _keyword in list_of_keywords:
            keyword = "_".join(_keyword.split())
            json_file = f"{pre_path}{keyword}.json"
            
            # Gom hết docs lại
            docs = self.load_and_split_json(json_file)
            all_documents.extend(docs)

        if not all_documents:
            print("Không có dữ liệu để index.")
            return

        total_docs = len(all_documents)
        print(f"\n--- GIAI ĐOẠN 2: EMBEDDING VÀ LƯU DB (Tổng: {total_docs} chunks) ---")
        print("-> Đang đẩy vào Vector DB (GPU bắt đầu chạy nặng đoạn này)...")

        # BƯỚC 2: GHI VÀO DB THEO BATCH (Để tránh tràn RAM nếu data quá lớn)
        # Chroma xử lý tốt nhất khi ném vào khoảng 2000-5000 docs mỗi lần
        batch_size = 5000 
        
        # Khởi tạo DB client trước (nếu chưa có thì tạo mới)
        vector_db = Chroma(
            persist_directory=self.cfg['data']['persist_directory'],
            collection_name=self.cfg['data']['collection_name'],
            embedding_function=self.embedding_model
        )

        for i in range(0, total_docs, batch_size):
            batch = all_documents[i : i + batch_size]
            print(f"   -> Processing batch {i} đến {min(i + batch_size, total_docs)}...")
            
            # Hàm add_documents hiệu quả hơn from_documents khi loop
            vector_db.add_documents(documents=batch)

        print("-> DONE! Kiểm tra folder chroma_db đi.")


data_config = extract_config(
    './configs/indexing_pipeline.yml'
)
indexing_pipeline = IndexingPipeline(
    data_config
)

indexing_pipeline.run(
    list_of_keywords=[
        "khám chữa bệnh",
        "bảo hiểm y tế",
        "thanh toán bảo hiểm",
        "chuyển tuyến",
        "giấy chuyển tuyến",
        "đăng ký khám chữa bệnh ban đầu",
        "mã định danh y tế",
        "thẻ bảo hiểm y tế",
        "hồ sơ bệnh án",
        "quy trình khám bệnh",
        "xét nghiệm",
        "viện phí",
        "thuốc và vật tư y tế",
        "thanh toán trực tuyến",
        "đồng chi trả",
        "quyền lợi người bệnh",
    ]
)
