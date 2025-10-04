"""
Module cung cấp một class để vector hóa văn bản Tiếng Việt sử dụng PhoBERT.
Phiên bản này sử dụng TensorFlow và sẽ tự động chạy trên GPU nếu có.
"""

import tensorflow as tf
import numpy as np
from transformers import AutoTokenizer, TFAutoModel
from typing import List, Union

class PhoBERTVectorizerTF:
    """
    Một class để chuyển đổi câu/văn bản Tiếng Việt thành vector embedding
    sử dụng mô hình PhoBERT với backend là TensorFlow.
    """
    def __init__(self, model_name: str = "vinai/phobert-base"):
        """
        Khởi tạo Vectorizer.

        Args:
            model_name (str): Tên của mô hình trên Hugging Face Hub.
        """
        self.physical_devices = tf.config.list_physical_devices('GPU')
        if len(self.physical_devices) > 0:
            self.device_name = "/GPU:0"
            print(f"Tìm thấy thiết bị GPU: {self.physical_devices[0].name}")
        else:
            self.device_name = "/CPU:0"
            print("Không tìm thấy GPU, sử dụng CPU.")

        try:
            print("Đang tải Tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            print("Đang tải Model (phiên bản TensorFlow)...")
            # Sử dụng TFAutoModel để tải model tương thích với TensorFlow
            self.model = TFAutoModel.from_pretrained(model_name)
            print("Tải mô hình thành công!")

        except Exception as e:
            print(f"Lỗi trong quá trình tải mô hình: {e}")
            raise

    def _mean_pooling(self, model_output, attention_mask):
        """Thực hiện Mean Pooling để lấy vector đại diện cho câu."""
        token_embeddings = model_output # model_output là last_hidden_state
        
        # Mở rộng attention_mask để có cùng shape với token_embeddings
        input_mask_expanded = tf.cast(
            tf.expand_dims(attention_mask, axis=-1), 
            dtype=token_embeddings.dtype
        )
        
        # Nhân token_embeddings với mask để các token padding có giá trị 0
        sum_embeddings = tf.reduce_sum(token_embeddings * input_mask_expanded, axis=1)
        
        # Tính tổng của attention_mask để có số lượng token thực sự
        sum_mask = tf.clip_by_value(tf.reduce_sum(input_mask_expanded, axis=1), 1e-9, float('inf'))
        
        return sum_embeddings / sum_mask

    def encode(self, 
               sentences: Union[str, List[str]], 
               batch_size: int = 32, 
               pooling_strategy: str = "cls") -> np.ndarray:
        """
        Tạo vector embedding cho một hoặc nhiều câu.

        Args:
            sentences (Union[str, List[str]]): Một câu hoặc một danh sách các câu.
            batch_size (int): Số lượng câu xử lý trong một batch.
            pooling_strategy (str): Cách lấy vector của câu từ vector của các token.
                                    Chấp nhận 'cls' hoặc 'mean'.
                                    'cls': Lấy vector của token [CLS].
                                    'mean': Lấy trung bình vector của các token trong câu.

        Returns:
            np.ndarray: Một mảng NumPy chứa các vector embedding.
        """
        if isinstance(sentences, str):
            sentences = [sentences]

        all_embeddings = []
        
        # Chạy các phép tính trên thiết bị đã chọn (GPU/CPU)
        with tf.device(self.device_name):
            for i in range(0, len(sentences), batch_size):
                batch_sentences = sentences[i:i+batch_size]
                
                # Tokenize a batch of sentences, yêu cầu trả về TensorFlow tensors ('tf')
                encoded_input = self.tokenizer(
                    batch_sentences, 
                    padding=True, 
                    truncation=True, 
                    return_tensors='tf'
                )

                # Lấy embeddings từ model
                # Trong TensorFlow, ta truyền `training=False` khi suy luận
                model_output = self.model(**encoded_input, training=False)
                last_hidden_state = model_output.last_hidden_state

                # Áp dụng pooling strategy
                if pooling_strategy == "cls":
                    # Lấy vector của token [CLS] (token đầu tiên)
                    sentence_embeddings = last_hidden_state[:, 0, :]
                elif pooling_strategy == "mean":
                    sentence_embeddings = self._mean_pooling(last_hidden_state, encoded_input['attention_mask'])
                else:
                    raise ValueError("pooling_strategy phải là 'cls' hoặc 'mean'")
                
                # Chuyển TF Tensor sang NumPy array
                all_embeddings.append(sentence_embeddings.numpy())

        # Nối tất cả các embedding từ các batch lại
        return np.vstack(all_embeddings)

# --- Phần ví dụ sử dụng ---
if __name__ == '__main__':
    print("--- Chạy ví dụ cho PhoBERTVectorizerTF ---")
    
    # 1. Cài đặt các thư viện cần thiết
    # pip install transformers tensorflow numpy scipy
    
    # 2. Khởi tạo vectorizer
    vectorizer_tf = PhoBERTVectorizerTF()
    
    # 3. Chuẩn bị câu ví dụ
    sample_sentences = [
        "Trường Đại học Công nghệ Thông tin là một trường đại học hàng đầu.",
        "Phở là món ăn đặc trưng của ẩm thực Việt Nam.",
        "Làm thế nào để học tốt môn trí tuệ nhân tạo?",
        "Thủ đô của Việt Nam là Hà Nội."
    ]

    # 4. Vector hóa sử dụng chiến lược [CLS] pooling
    print("\nVector hóa sử dụng [CLS] pooling...")
    cls_embeddings_tf = vectorizer_tf.encode(sample_sentences, pooling_strategy="cls")
    print("Kích thước mảng vector:", cls_embeddings_tf.shape)
    print("Vector đầu tiên (5 chiều đầu):", cls_embeddings_tf[0][:5])
    
    # 5. Vector hóa sử dụng chiến lược Mean pooling
    print("\nVector hóa sử dụng Mean pooling...")
    mean_embeddings_tf = vectorizer_tf.encode(sample_sentences, pooling_strategy="mean")
    print("Kích thước mảng vector:", mean_embeddings_tf.shape)
    print("Vector đầu tiên (5 chiều đầu):", mean_embeddings_tf[0][:5])
