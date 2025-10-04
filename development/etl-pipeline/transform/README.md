# ETL Pipeline - Transform Stage
> *This directory contains the scripts responsible for the "Transform" stage of the ETL (Extract, Transform, Load) pipeline. The primary goal of this stage is to take the raw, extracted data, clean it, structure it, and finally, convert it into a numerical format that can be used for semantic retrieval.*

## 1. Overview
The transformation process involves three main steps:
- **Preprocessing**: Cleaning the raw text content of the legal documents to remove noise and standardize formatting.
- **Chunking**: Breaking down the cleaned documents into smaller, more manageable, and meaningful pieces of text.
- **Vectorization**: Converting the text chunks into high-dimensional semantic vectors (embeddings) that capture their meaning.

The whole stage will be wrapped in `transform.py`.

## 2. Scripts
`transform.py`, the main entry point for the entire transformation stage. It sequentially executes the preprocessing, chunking, and vectorization steps, creating a seamless pipeline from raw text to semantic vectors. The script is designed to be configurable, allowing you to specify input and output paths for each stage of the process.

The core logic from the following helper scripts is integrated into the transform.py pipeline:
- `_preprocessing.py`: Contains the functions for cleaning and normalizing the text.
- `_chunking.py`: Provides the logic for structural chunking of the documents.
- `_vectorize.py`: Handles the conversion of text chunks into vector embeddings using a pre-trained model.