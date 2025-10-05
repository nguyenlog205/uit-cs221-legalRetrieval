import faiss
import numpy as np
import json
import os

def query_faiss(query_vector, k, index_path="index.faiss", metadata_path="metadata.json"):
    """
    Truy vấn top-k vector tương tự nhất từ một index Faiss.

    Args:
        query_vector (np.array): Vector dùng để truy vấn.
        k (int): Số lượng kết quả gần nhất cần tìm.
        index_path (str): Đường dẫn đến file index Faiss.
        metadata_path (str): Đường dẫn đến file metadata JSON.

    Returns:
        list: Danh sách các kết quả, mỗi kết quả là một dictionary
              chứa metadata, khoảng cách và index.
    """
    # Kiểm tra file tồn tại
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError("Không tìm thấy file index hoặc metadata. Hãy chắc chắn chúng tồn tại.")

    # 1. Tải index và metadata
    try:
        index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Lỗi khi tải file: {e}")
        return []

    # 2. Chuẩn bị vector truy vấn
    # Faiss yêu cầu vector truy vấn phải là một mảng 2D (n_queries, dim)
    # và có kiểu float32.
    if query_vector.ndim == 1:
        query_vector = np.array([query_vector]).astype('float32')
    else:
        query_vector = query_vector.astype('float32')
        
    vector_dim = index.d
    if query_vector.shape[1] != vector_dim:
        raise ValueError(f"Chiều của vector truy vấn ({query_vector.shape[1]}) không khớp với chiều của index ({vector_dim})")


    # 3. Thực hiện tìm kiếm
    # index.search trả về 2 giá trị:
    # - D: distances (khoảng cách) của các vector tìm được
    # - I: indices (chỉ số) của các vector tìm được
    distances, indices = index.search(query_vector, k)

    # 4. Xử lý kết quả
    results = []
    # indices[0] và distances[0] chứa kết quả cho truy vấn đầu tiên (và duy nhất)
    for i, idx in enumerate(indices[0]):
        # idx = -1 nghĩa là không tìm thấy kết quả hợp lệ (thường xảy ra với các index phức tạp)
        if idx != -1:
            result = {
                "metadata": metadata[idx],
                "distance": float(distances[0][i]),
                "index": int(idx)
            }
            results.append(result)
            
    return results