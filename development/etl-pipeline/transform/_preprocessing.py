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


def preprocessing_batch_news(batch_documents: List[Dict]) -> List[Dict]:
    """
    Tiền xử lý một lô (batch) các văn bản bằng cách áp dụng hàm
    preprocessing_news() cho từng văn bản trong danh sách.

    Args:
        batch_documents (List[Dict]): Một danh sách các dictionary văn bản.

    Returns:
        List[Dict]: Danh sách các văn bản đã được tiền xử lý.
    """
    if not isinstance(batch_documents, list):
        raise TypeError("Đầu vào cho hàm xử lý batch phải là một list.")
        
    return [preprocessing_news(doc) for doc in batch_documents]


def save_preprocessed_data(data: List[Dict], output_filepath: str):
    """
    Lưu dữ liệu đã được tiền xử lý vào một file JSON.

    Args:
        data (List[Dict]): Danh sách các văn bản đã được xử lý.
        output_filepath (str): Đường dẫn đến file JSON để lưu kết quả.
    """
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            # ensure_ascii=False để lưu đúng ký tự tiếng Việt
            # indent=4 để file JSON dễ đọc hơn
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Dữ liệu đã được xử lý và lưu thành công vào file: '{output_filepath}'")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi khi lưu file: {e}")


# --- PHẦN THỰC THI CHÍNH ---
if __name__ == "__main__":
    # 1. Nạp dữ liệu từ file
    input_file = r'crawled_data\20251004-190918\metadata_law_giao_thông_đường_bộ.json'
    output_file = r'data\processed\preprocessed_data.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_documents = json.load(f)
        print(f"📂 Đã đọc thành công {len(all_documents)} văn bản từ file '{input_file}'.")
        
        # In ra một phần nội dung gốc để so sánh
        # Lấy văn bản đầu tiên có nội dung để làm ví dụ
        original_doc_example = next((doc for doc in all_documents if doc.get("Nội dung")), None)
        if original_doc_example:
            print("\n--- NỘI DUNG GỐC (VÍ DỤ) ---")
            print(original_doc_example["Nội dung"][:300] + "...")
            print("-" * 30)
        
        # 2. Tiền xử lý dữ liệu theo batch
        print("\n⏳ Bắt đầu tiền xử lý dữ liệu...")
        preprocessed_documents = preprocessing_batch_news(all_documents)
        print("✔️ Tiền xử lý hoàn tất.")

        # In ra nội dung sau khi xử lý để so sánh
        processed_doc_example = next((doc for doc in preprocessed_documents if doc.get("Nội dung")), None)
        if processed_doc_example:
            print("\n--- NỘI DUNG SAU KHI XỬ LÝ (VÍ DỤ) ---")
            print(processed_doc_example["Nội dung"][:300] + "...")
            print("-" * 30)

        # 3. Lưu kết quả ra file mới
        print("\n💾 Bắt đầu lưu kết quả...")
        save_preprocessed_data(preprocessed_documents, output_file)

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file '{input_file}'. Vui lòng đảm bảo file này nằm cùng thư mục.")
    except json.JSONDecodeError:
        print(f"❌ Lỗi: File '{input_file}' không phải là định dạng JSON hợp lệ.")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi không mong muốn: {e}")