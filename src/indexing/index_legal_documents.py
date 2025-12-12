import json
import re
import os 
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentIndexer:
    """
    Xử lý, nhúng (embedding) và lập chỉ mục (indexing) các văn bản luật pháp 
    từ file JSON vào Vector Database (Chroma) dựa trên cấu hình.
    """
    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        
        emb_cfg = self.cfg['embedding']
        print(f"-> Init Embedding: {emb_cfg['model_name']} on device: {emb_cfg['device']}")

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=emb_cfg['model_name'],
            model_kwargs={'device': emb_cfg.get('device', 'cpu')}, 
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 64} 
        )
        
        split_cfg = self.cfg['splitting']
        self.sub_splitter = RecursiveCharacterTextSplitter(
            chunk_size=split_cfg.get('chunk_size', 1024), 
            chunk_overlap=split_cfg.get('chunk_overlap', 200), 
            separators=split_cfg.get('separators', ["\n", ";", ".", " "]) 
        )

        self.batch_size = 5000 

    def _load_and_split_json(self, json_path: str) -> List[Document]:
        """
        Đọc JSON, tách Metadata, và cắt 'Nội dung' theo Điều luật, sau đó sử dụng
        sub_splitter để cắt các Điều luật quá dài.
        """
        print(f"-> Đang đọc file JSON từ: {json_path}")
        
        try:
            if not os.path.exists(json_path):
                print(f"Error: File không tồn tại tại đường dẫn: {json_path}")
                return []
                
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON: {e}")
            return []

        final_docs = []

        for entry in data:
            base_metadata = {
                "source": entry.get("Tên văn bản", "Unknown"),
                "link": entry.get("Link chi tiết", ""),
                "status": entry.get("Trạng thái", ""),
                "effective_date": entry.get("Hiệu lực", ""),
                "type": "law_document"
            }
            
            full_text = entry.get("Nội dung", "")
            if not full_text: continue

            pattern = r"(?=\nĐiều \d+)" 
            raw_chunks = re.split(pattern, full_text)

            for chunk_text in raw_chunks:
                chunk_text = chunk_text.strip()
                if not chunk_text or len(chunk_text) < 10: continue
                
                if len(chunk_text) > self.sub_splitter.chunk_size:
                    sub_docs = self.sub_splitter.create_documents(
                        [chunk_text], 
                        metadatas=[base_metadata]
                    )
                    final_docs.extend(sub_docs)
                else:
                    doc = Document(
                        page_content=chunk_text,
                        metadata=base_metadata
                    )
                    final_docs.append(doc)

        print(f"-> Xử lý xong {len(data)} văn bản gốc. Tạo ra {len(final_docs)} chunks (Điều luật).")

        if final_docs:
            print(f"   [Preview]: {final_docs[5].page_content[:100]}...")
            print(f"   [Metadata]: {final_docs[5].metadata}")

        return final_docs

    def run(
        self,
        list_of_keywords: List[str],
        base_pre_path: str = r'data\legal_documents\raw\metadata_law_' 
    ):
        all_documents = []
        
        print("--- [PHASE] PROCESSING DOCUMENT ---")
        for _keyword in list_of_keywords:
            print(f'Starting process document {_keyword}')
            keyword = "_".join(_keyword.split())

            json_file = f"{base_pre_path}{keyword}.json"
            docs = self._load_and_split_json(json_file)
            all_documents.extend(docs)

        if not all_documents:
            print("Warning: There are no documents for processing!")
            return

        total_docs = len(all_documents)
        print(f"\n--- EMBEDDING AND DATABASE LOADING")
        print(f'{total_docs} chunks in total')
        print("-> Start loading to Database")
        batch_size = self.batch_size 
        data_cfg = self.cfg['data']
        vector_db = Chroma(
            persist_directory=data_cfg['persist_directory'], 
            collection_name=data_cfg['collection_name'], 
            embedding_function=self.embedding_model
        )

        for i in range(0, total_docs, batch_size):
            batch = all_documents[i : i + batch_size]
            print(f"   -> Processing batch {i} to {min(i + batch_size, total_docs)}...")
            vector_db.add_documents(documents=batch)

        print("-> Loading data to Database completed!")