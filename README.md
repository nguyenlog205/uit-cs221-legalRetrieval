# [UIT-CS221] Vietnamese Law Retrieval System
> This repository serves as the version control platform for the final-semester project "Vietnamese Law Retrieval System" for subject **CS221 - Natural Language Processing** at University of Information Technology, Vietnam National University Ho Chi Minh city.

## Prerequisite
- Python `3.10.x` (recommend `3.10.11`)
- `requirements.txt` (see more at **Project Structure**)

## Repository Structure
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
## Acknowledgement
The whole project team would like to express our sincere gratitude to our supervisor, [Mr. Nguyễn Trọng Chỉnh (MSc)](https://cs.uit.edu.vn/featured_item/ths-nguyen-trong-chinh/), from the Faculty of Computer Science at the University of Information Technology (UIT), VNU-HCM. His invaluable guidance, insightful feedback, and unwavering support were instrumental in the completion of this project.
