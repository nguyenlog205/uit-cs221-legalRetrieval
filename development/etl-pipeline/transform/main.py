import _preprocessing, _chunking, _vectoring
import json

def transform(
        data,
        metadata_filepath: str = "data/faiss/metadata.json",
        faiss_filepath: str = 'data/faiss/index.faiss'
):
    transformed = []
    for idx, document in enumerate(data, 1):
        preprocessed_data = _preprocessing.preprocessing_news(document=document)
        chunked_data = _chunking.structural_chunking(document=preprocessed_data)
        transformed.extend(chunked_data)
    print(transformed)
    _vectoring.create_vector_store(
        input_data = transformed,
        metadata_filepath=metadata_filepath,
        faiss_index_filepath=faiss_filepath
    )
    

if __name__ == '__main__':
    import pandas as pd

    file_path = r'data\raw\metadata_law_giao_thông_đường_bộ.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    transform(data)