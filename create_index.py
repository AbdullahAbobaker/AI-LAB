
import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from xml_parser import extract_text_chunks_from_xml

DATA_DIR = "data"
DB_DIR = "vectorstore"

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

docs = []
for file in os.listdir(DATA_DIR):
    if file.endswith(".xml"):
        path = os.path.join(DATA_DIR, file)
        print(f"🔍 Parsing {file}...")
        for chunk in extract_text_chunks_from_xml(path):
            metadata = {
                "source": chunk["file"],
                "kapitel": chunk["kapitel"]
            }
            docs.append(Document(page_content=chunk["text"], metadata=metadata))

# Build FAISS index
print("📦 Building vectorstore...")
db = FAISS.from_documents(docs, embedding_model)
db.save_local(DB_DIR)
print(f"✅ Index saved with {len(docs)} chunks to: {DB_DIR}")