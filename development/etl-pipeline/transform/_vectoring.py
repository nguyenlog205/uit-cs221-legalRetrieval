import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os # Thêm thư viện os để kiểm tra file

def create_vector_store(
    input_data: list[dict], 
    metadata_filepath: str = "metadata.json", 
    faiss_index_filepath: str = "index.faiss",
    model_name: str = 'bkai-foundation-models/vietnamese-bi-encoder'
    ) -> tuple[str, str] | None:
    """
    Tạo và lưu file metadata và chỉ mục FAISS từ dữ liệu đầu vào.

    Hàm này thực hiện 3 bước chính:
    1. Lưu danh sách các dictionary (metadata) vào một file JSON.
    2. Tải mô hình Sentence Transformer để vector hóa trường 'content' của mỗi dictionary.
    3. Xây dựng một chỉ mục FAISS từ các vector đã tạo và lưu nó ra file.

    Args:
        input_data (list[dict]): Danh sách các dictionary chứa dữ liệu. 
                                 Mỗi dictionary phải có key 'content'.
        metadata_filepath (str, optional): Đường dẫn để lưu file metadata. 
                                           Mặc định là "metadata.json".
        faiss_index_filepath (str, optional): Đường dẫn để lưu file chỉ mục FAISS. 
                                              Mặc định là "index.faiss".
        model_name (str, optional): Tên của mô hình Sentence Transformer trên Hugging Face.
                                    Mặc định là 'bkai-foundation-models/vietnamese-bi-encoder'.

    Returns:
        tuple[str, str] | None: Một tuple chứa đường dẫn đến file metadata và file chỉ mục FAISS
                                nếu thành công, ngược lại trả về None.
    """
    if not input_data:
        print("Lỗi: input_data rỗng, không có gì để xử lý.")
        return None

    try:
        # 1. TẠO FILE METADATA.JSON
        print(f"Bắt đầu tạo file metadata tại: {metadata_filepath}")
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(input_data, f, ensure_ascii=False, indent=4)
        print(f"Đã tạo file metadata thành công.")

        # 2. TẠO FILE CHỈ MỤC FAISS
        # Tải mô hình embedding
        print(f"\nĐang tải mô hình embedding: '{model_name}'...")
        model = SentenceTransformer(model_name)
        print("Tải mô hình thành công.")

        # Trích xuất nội dung từ dữ liệu
        print("Trích xuất nội dung từ dữ liệu...")
        corpus_contents = [chunk['content'] for chunk in input_data]

        # Thực hiện vector hóa
        print("Đang tiến hành vector hóa văn bản...")
        embeddings = model.encode(corpus_contents, convert_to_tensor=False, show_progress_bar=True)
        print("Vector hóa hoàn tất.")

        # Chuyển đổi embeddings sang định dạng FAISS yêu cầu
        embeddings = np.array(embeddings).astype('float32')
        
        # Kiểm tra nếu không có embedding nào được tạo
        if embeddings.shape[0] == 0:
            print("Lỗi: Không có vector nào được tạo ra.")
            return None

        embedding_dim = embeddings.shape[1]

        # Khởi tạo và xây dựng chỉ mục FAISS
        print("Khởi tạo và xây dựng chỉ mục FAISS...")
        index = faiss.IndexFlatL2(embedding_dim)
        index.add(embeddings)

        print(f"Số lượng vector trong chỉ mục: {index.ntotal}")
        print(f"Số chiều của mỗi vector: {index.d}")

        # Lưu chỉ mục ra file
        faiss.write_index(index, faiss_index_filepath)
        print(f"Đã tạo file chỉ mục FAISS thành công tại: {faiss_index_filepath}")
        
        return metadata_filepath, faiss_index_filepath

    except KeyError:
        print("Lỗi: Một vài dictionary trong input_data thiếu key 'content'.")
        return None
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}")
        return None