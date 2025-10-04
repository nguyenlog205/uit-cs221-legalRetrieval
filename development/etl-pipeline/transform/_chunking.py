import re
from typing import List, Dict

def structural_chunking(document: Dict) -> List[Dict]:
    """
    Phân chia văn bản của một tài liệu pháp lý thành các chunk nhỏ hơn
    dựa trên cấu trúc theo từng "Điều".
    
    Mỗi chunk sẽ kế thừa toàn bộ metadata từ document gốc và có thêm
    chunk_id và content riêng.

    Args:
        document (Dict): Một dictionary chứa thông tin của văn bản gốc.

    Returns:
        List[Dict]: Một danh sách các chunk.
    """
    text = document.get("Nội dung", "")
    source_name = document.get("Tên văn bản", "Không rõ")
    
    # Regex để tìm "Điều X" và nội dung của nó cho đến "Điều" tiếp theo hoặc hết file
    pattern = re.compile(r"(Điều \d+.*?)(?=\nĐiều \d+|$)", re.DOTALL)
    parts = pattern.findall(text)
    
    chunks = []
    
    # Lấy tất cả metadata gốc ngoại trừ "Nội dung"
    base_metadata = {key: value for key, value in document.items() if key != "Nội dung"}

    if not parts:
        # Nếu không có "Điều" nào, coi cả văn bản là một chunk
        chunk_data = base_metadata.copy() # Bắt đầu với metadata gốc
        chunk_data["chunk_id"] = f"{source_name}_full_content"
        chunk_data["content"] = text.strip()
        chunks.append(chunk_data)
        return chunks

    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Lấy tên của "Điều" làm ID
        chunk_id_match = re.match(r"(Điều \d+)", part)
        chunk_id_str = chunk_id_match.group(1) if chunk_id_match else "Unknown_Article"

        # Tạo một chunk mới bằng cách sao chép metadata gốc
        chunk_data = base_metadata.copy()
        
        # Thêm thông tin riêng của chunk
        chunk_data["chunk_id"] = f"{source_name}_{chunk_id_str.replace(' ', '_')}"
        chunk_data["content"] = part
        
        chunks.append(chunk_data)
        
    return chunks