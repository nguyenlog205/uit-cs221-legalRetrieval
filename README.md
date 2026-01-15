# [UIT-CS221] Vietnamese Law Retrieval Application
> This repository serves as the version control platform for the final-semester project "Vietnamese Law Retrieval System" for subject **CS221 - Natural Language Processing** at University of Information Technology, Vietnam National University Ho Chi Minh city.

## 1. Prerequisite
- Python `3.10.x` (recommend `3.10.11`)
- `requirements.txt` (see more at **Project Structure**)

## 2. Repository Structure
```bash
uit-cs221-legalRetrieval/
│
├── app/                  # Source code for the web application
│   ├── backend/          # Backend server (API, business logic)
│   └── frontend/         # User interface (React)
│
├── data/                 # All project data
│   ├── faiss/            # Processed data for retrieval
│   │   ├── index.faiss   # FAISS index for vector search
│   │   └── metadata.json # Metadata for text chunks
│   └── raw/              # Raw data collected from sources
│
├── development/          # Scripts and notebooks for development and ETL pipeline
│   ├── etl-pipeline/     # Data ingestion and integration
│   │   ├── data-ingestion/
│   │   └── data-integration/
│   ├── rag-pipeline/     # RAG-architecture
│
├── evaluation/           # Notebooks for model evaluation
│   └── report.ipynb      # Evaluation results and analysis
│
├── models/               # Trained models (if any)
│
├── requirements.txt      # Necessary libraries
├── .gitignore            # Files and directories ignored by Git
└── README.md             # Main project documentation
```

## 3. Architecture and implementation
This system utilizes a multi-layered Retrieval-Augmented Generation (RAG) architecture designed to provide precise, context-aware responses to user queries by bridging raw data processing with advanced language modeling.
![Architecture](/img/architecture.png)

### 3.1. Data Pre-processing and Hybrid Chunking
The lifecycle of information begins in the Data Layer, where the raw dataset undergoes a meticulous Hybrid Chunking process. This strategy combines Semantic Chunking, which identifies natural transitions in meaning, with Recursive Splitting to maintain structural integrity. These refined data fragments are then processed by a `Vietnamese-bi-encoder` embedding model to transform text into high-dimensional vectors, which are subsequently stored in a ChromaDB vector database alongside their respective metadata. This preparation ensures that the system can efficiently navigate complex legal or domain-specific documents during the retrieval phase.
### 3.2. Retrieval Session
#### 3.2.1. Intent Classification and Intelligent Routing
When a user submits a query, the frontend sends a cURL with `session_id` and `query`, for example:
```bash
curl -X 'POST' \
  'http://localhost:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "Bảo hiểm y tế là gì?",
  "session_id": "string"
}'
```
After then, it enters the Business Logic Layer and is immediately processed by an Intent Classifier powered by the `Gemma-3-1b-it` model. The classifier's primary role is to determine the nature of the request, distinguishing between general conversational inquiries and specific queries requiring factual evidence. If the intent is classified as "`general`" the request is routed to a General Generator (`Gemma-1b`) to provide a direct response. However, if the query requires specific knowledge, the classifier returnsa `specific` and the system then initiates a sophisticated retrieval pipeline.

In the given example, it returns the following response:
```bash
INFO:main_api:Input: 'Bảo hiểm y tế là gì?' | Intent: specific
```
#### 3.2.2. Hybrid Search and Document Retrieval
For specific intents, the system executes a Hybrid Search that operates on two fronts: Semantic Search (Vector-based) and Lexical Search (BM25-based). The Semantic Search utilizes the same Vietnamese-bi-encoder to calculate Cosine Similarity between the query and stored vectors, while the Lexical Search ensures term-specific accuracy. These results are merged through a fusion algorithm that ranks and selects the top-k most relevant chunks. This ensures that the context provided to the generation model is both semantically deep and keyword-accurate.

In this example, the `top-k` parameter is seted by `5`. The database then returns 5 best result as below:
```bash
[QUERY]: Bảo hiểm y tế là gì?
-> BM25 Search tìm thấy 10 đoạn.
-> Vector Search tìm thấy 1 đoạn.
-> Hợp nhất thủ công (Loại trùng lặp) còn 10 đoạn.
-> Trả về 5 đoạn cuối cùng (top-k của tập hợp nhất).
   1. [Nghị quyết 02/2024/NQ-HĐND]: Điều 1. Quy định giá dịch vụ khám bệnh, chữa bệnh không thuộc phạm vi thanh toán...
   2. [Nghị quyết 78/2024/NQ-HĐND]: Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng 1. Phạm vi điều chỉnh Nghị quyết...
   3. [Thông tư 36/2021/TT-BYT]: Điều 1. Phạm vi điều chỉnh Thông tư này quy định về: 1. Khám bệnh, chữa bệnh và ...
   4. [Thông tư liên tịch 39/2011/TTLT-BYT-BTC]: Điều 4. Thanh toán chi phí khám bệnh, chữa bệnh trong trường hợp có vi phạm pháp...
   5. [Thông tư 31/2011/TT-BYT]: THÔNG TƯ Ban hành và hướng dẫn thực hiện Danh mục thuốc chủ yếu sử dụng tại các ...
```
#### 3.2.3. Generation 
The final stage involves the Specific Generator, which utilizes the `Qwen2.5-3B-Instruct` model, optimized through `LoRA` and `Quantization` for high performance and low latency. This generator receives the user's query integrated with the retrieved document chunks to synthesize a comprehensive answer. The system culminates in a structured JSON response that includes the generated answer, the classified intent, and a list of source documents used for the retrieval. This format guarantees transparency, allowing users to verify the synthesized information against the original legal or technical references provided by the system.

```tex
{
  "response": "### Định Nghĩa Bảo Hiểm Y Tế\n\nBảo hiểm y tế là một loại hình bảo hiểm xã hội, nhằm cung cấp tài chính để chi trả cho các dịch vụ y tế khi người tham gia bảo hiểm gặp phải tình trạng bệnh tật, tai nạn hoặc các vấn đề sức khỏe khác.\n\n### Cơ Sở Pháp Lý\n\nTheo **Luật Bảo hiểm y tế ngày 14 tháng 11 năm 2008**, bảo hiểm y tế là một phần quan trọng của hệ thống an sinh xã hội, giúp đảm bảo quyền được bảo vệ sức khỏe của công dân.\n\n### Phạm Vi Áp Dụng\n\nBảo hiểm y tế áp dụng cho các đối tượng sau:\n* Người tham gia bảo hiểm y tế bắt buộc\n* Người tham gia bảo hiểm y tế tự nguyện\n\n### Mục Đích\n\nMục đích của bảo hiểm y tế là giúp người tham gia giảm bớt gánh nặng tài chính khi phải chi trả cho các dịch vụ y tế, đồng thời đảm bảo quyền được tiếp cận các dịch vụ y tế chất lượng cao.\n\n### Thông Tin Liên Quan\n\nTheo **Thông tư liên tịch 39/2011/TTLT-BYT-BTC**, bảo hiểm y tế cũng quy định về việc thanh toán chi phí khám bệnh, chữa bệnh trong trường hợp có vi phạm pháp luật về tai nạn giao thông.\n\nTuy nhiên, trong cơ sở dữ liệu hiện tại, không có thông tin chi tiết về định nghĩa và phạm vi áp dụng của bảo hiểm y tế. Để có thông tin chính xác và đầy đủ, bạn có thể tham khảo **Luật Bảo hiểm y tế** và các văn bản pháp luật liên quan.",
  "intent": "specific",
  "source_documents": [
    "Nghị quyết 78/2024/NQ-HĐND",
    "Nghị quyết 02/2024/NQ-HĐND",
    "Thông tư 31/2011/TT-BYT",
    "Thông tư 36/2021/TT-BYT",
    "Thông tư liên tịch 39/2011/TTLT-BYT-BTC"
  ]
}
```
#### 3.2.4. User interface
![Demo](img/demo.png)

## Acknowledgement
The whole project team would like to express our sincere gratitude to our supervisor, [Mr. Nguyễn Trọng Chỉnh (MSc)](https://cs.uit.edu.vn/featured_item/ths-nguyen-trong-chinh/), from the Faculty of Computer Science at the University of Information Technology (UIT), VNU-HCM. His invaluable guidance, insightful feedback, and unwavering support were instrumental in the completion of this project.
