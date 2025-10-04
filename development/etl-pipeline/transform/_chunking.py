# File: chunking.py
# Mục đích: Đọc dữ liệu, sử dụng module preprocessing để làm sạch,
# sau đó thực hiện chunking và lưu mỗi chunk ra một file riêng.

import json
import re
import os
from typing import List, Dict

# Import hàm cần thiết từ file preprocessing.py
from _preprocessing import preprocessing_batch_news

def structural_chunking(document: Dict, chunk_level: str = 'khoan') -> List[Dict]:
    """
    Thực hiện chia nhỏ văn bản theo cấu trúc (Điều, Khoản).
    """
    if chunk_level not in ['dieu', 'khoan']:
        raise ValueError("chunk_level phải là 'dieu' hoặc 'khoan'.")

    text = document.get("Nội dung", "")
    if not text:
        return []

    base_metadata = {
        "source_doc_name": document.get("Tên văn bản"),
        "source_link": document.get("Link chi tiết"),
        "status": document.get("Trạng thái"),
        "effective_date": document.get("Hiệu lực"),
        "issued_date": document.get("Ban hành"),
    }

    chunks = []
    articles = re.split(r'(?=^Điều \w+.*)', text, flags=re.MULTILINE)

    for article_text in articles:
        article_text = article_text.strip()
        if not article_text:
            continue

        article_lines = article_text.split('\n')
        article_title = article_lines[0]
        match = re.match(r'Điều (\w+)', article_title)
        article_id_str = match.group(1) if match else 'unknown'

        if chunk_level == 'dieu':
            metadata = base_metadata.copy()
            metadata.update({
                "structure": f"Điều {article_id_str}",
                "chunk_id": f"{base_metadata['source_doc_name']}_dieu_{article_id_str}"
            })
            chunks.append({"content": article_text, "metadata": metadata})
            continue

        clauses = re.split(r'(?=^\d+\. )', article_text, flags=re.MULTILINE)
        article_header = clauses[0]
        
        if len(clauses) <= 1:
            metadata = base_metadata.copy()
            metadata.update({
                "structure": f"Điều {article_id_str}",
                "chunk_id": f"{base_metadata['source_doc_name']}_dieu_{article_id_str}"
            })
            chunks.append({"content": article_header, "metadata": metadata})
        else:
            for i, clause_text in enumerate(clauses):
                if i == 0: continue
                clause_text = clause_text.strip()
                if not clause_text: continue
                clause_match = re.match(r'(\d+)\.', clause_text)
                clause_id_str = clause_match.group(1) if clause_match else f"p{i}"
                chunk_content = f"{article_header.strip()}\n{clause_text}"
                metadata = base_metadata.copy()
                metadata.update({
                    "structure": f"Điều {article_id_str} - Khoản {clause_id_str}",
                    "chunk_id": f"{base_metadata['source_doc_name']}_dieu_{article_id_str}_khoan_{clause_id_str}"
                })
                chunks.append({"content": chunk_content, "metadata": metadata})
    return chunks

def sanitize_filename(name: str) -> str:
    """Làm sạch chuỗi để tạo tên file/thư mục hợp lệ."""
    # Thay thế dấu / bằng dấu -
    name = name.replace('/', '-')
    # Loại bỏ các ký tự không hợp lệ khác
    return re.sub(r'[\\?%*:|"<>]', '_', name)

def save_chunks_to_separate_files(all_chunks: List[Dict], base_output_dir: str):
    """
    Lưu mỗi chunk vào một file JSON riêng biệt, được tổ chức trong các
    thư mục con theo tên văn bản gốc.
    """
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
        print(f"📁 Đã tạo thư mục chính: '{base_output_dir}'")

    count = 0
    for chunk in all_chunks:
        try:
            metadata = chunk.get("metadata", {})
            doc_name = metadata.get("source_doc_name", "unknown_document")
            chunk_id = metadata.get("chunk_id", f"chunk_{count+1}")

            # Tạo tên thư mục và tên file hợp lệ
            sanitized_doc_name = sanitize_filename(doc_name)
            sanitized_chunk_id = sanitize_filename(chunk_id)

            # Tạo đường dẫn thư mục cho văn bản
            doc_dir = os.path.join(base_output_dir, sanitized_doc_name)
            if not os.path.exists(doc_dir):
                os.makedirs(doc_dir)

            # Tạo đường dẫn file cho chunk
            output_filepath = os.path.join(doc_dir, f"{sanitized_chunk_id}.json")

            # Lưu chunk vào file
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=4)
            
            count += 1
        except Exception as e:
            print(f"❌ Gặp lỗi khi lưu chunk: {chunk.get('metadata', {}).get('chunk_id')}. Lỗi: {e}")
            
    print(f"✅ Đã lưu thành công {count} chunk vào các file riêng trong thư mục '{base_output_dir}'.")

# ==============================================================================
# PHẦN THỰC THI CHÍNH
# ==============================================================================
if __name__ == "__main__":
    input_file = r'data\processed\preprocessed_data.json'
    chunks_output_dir = r'data\processed'
    
    try:
        # 1. Nạp dữ liệu
        with open(input_file, 'r', encoding='utf-8') as f:
            all_documents = json.load(f)
        print(f"📂 Đã đọc thành công {len(all_documents)} văn bản từ file '{input_file}'.")
        
        # 2. Tiền xử lý dữ liệu (sử dụng hàm từ file preprocessing.py)
        print("\n⏳ Bắt đầu tiền xử lý dữ liệu...")
        preprocessed_documents = preprocessing_batch_news(all_documents)
        print("✔️ Tiền xử lý hoàn tất.")

        # 3. Thực hiện chunking cho tất cả văn bản
        print("\n🔪 Bắt đầu chia nhỏ (chunking) văn bản...")
        all_chunks = []
        for doc in preprocessed_documents:
            if doc.get("Nội dung"):
                chunks = structural_chunking(doc, chunk_level='khoan')
                all_chunks.extend(chunks)
        
        print(f"✔️ Chia nhỏ hoàn tất: Tạo ra được tổng cộng {len(all_chunks)} chunks.")

        # 4. Lưu kết quả chunking ra các file riêng
        print("\n💾 Bắt đầu lưu các chunks ra file...")
        save_chunks_to_separate_files(all_chunks, chunks_output_dir)

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file '{input_file}'. Vui lòng đảm bảo file này nằm cùng thư mục.")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi không mong muốn: {e}")