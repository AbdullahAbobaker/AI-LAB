# create_index.py

import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from xml_parser import extract_text_chunks_from_xml

DATA_DIR = "data"
DB_DIR = "vectorstore"
os.makedirs(DB_DIR, exist_ok=True)

def build_faiss_index():
    docs = []
    for fname in os.listdir(DATA_DIR):
        if not fname.lower().endswith(".xml"):
            continue
        path = os.path.join(DATA_DIR, fname)
        try:
            all_chunks = extract_text_chunks_from_xml(path, max_chunk_chars=1000)
            for ch in all_chunks:
                doc = Document(
                    page_content=ch["text"],
                    metadata={
                        "source": ch["file"],
                        "kapitel": ch["kapitel"]
                    }
                )
                docs.append(doc)
        except Exception as e:
            print(f"❌ Error reading {fname}: {e}")

    if not docs:
        print("No chunks found, aborting.")
        return

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(DB_DIR)
    print(f"✅ Indexed {len(docs)} chunks into {DB_DIR}.")

if __name__ == "__main__":
    build_faiss_index()
