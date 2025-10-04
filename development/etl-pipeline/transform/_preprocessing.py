import re
import json
from typing import List, Dict, Union

def preprocessing_news(document: Dict) -> Dict:
    """
    Tiền xử lý nội dung cho một văn bản (dictionary) duy nhất.
    Hàm này làm sạch trường "Nội dung" bằng cách loại bỏ khoảng trắng thừa,
    các dòng không cần thiết và chuẩn hóa định dạng.

    Args:
        document (Dict): Một dictionary chứa thông tin văn bản, có key "Nội dung".

    Returns:
        Dict: Dictionary đã được xử lý với nội dung gọn gàng hơn.
    """
    if not isinstance(document, dict):
        return document

    # Tạo một bản sao để không làm thay đổi đối tượng gốc
    processed_doc = document.copy()
    
    noi_dung = processed_doc.get("Nội dung", "")

    # Trả về ngay nếu không có nội dung hoặc nội dung không phải là chuỗi
    if not noi_dung or not isinstance(noi_dung, str):
        return processed_doc

    # 1. Xóa các dòng gạch ngang trang trí
    noi_dung = re.sub(r'_{2,}', '', noi_dung)

    # 2. Tách văn bản thành các dòng
    lines = noi_dung.split('\n')
    
    cleaned_lines = []
    for line in lines:
        # 3. Xóa khoảng trắng thừa ở đầu/cuối mỗi dòng
        stripped_line = line.strip()
        
        # 4. Thay thế nhiều khoảng trắng liên tiếp bằng một khoảng trắng duy nhất
        normalized_line = re.sub(r'\s+', ' ', stripped_line)
        
        # Chỉ thêm các dòng có nội dung vào danh sách
        if normalized_line:
            cleaned_lines.append(normalized_line)
            
    # 5. Ghép các dòng lại và chuẩn hóa ngắt dòng (loại bỏ các dòng trống thừa)
    full_text = "\n".join(cleaned_lines)
    processed_text = re.sub(r'\n{3,}', '\n\n', full_text)

    # 6. Cập nhật lại nội dung đã xử lý
    processed_doc["Nội dung"] = processed_text.strip()
    
    return processed_doc