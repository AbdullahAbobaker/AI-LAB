import os
import glob
import json
from xml_parser import parse_thieme_xml
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

DATA_DIR = "data"
DB_DIR = "vectorstore"
os.makedirs(DB_DIR, exist_ok=True)

def parse_all_files():
    all_docs = []
    for path in glob.glob(f"{DATA_DIR}/**/*.xml", recursive=True):
        try:
            entries = parse_thieme_xml(path)
            for e in entries:
                doc = Document(
                    page_content=e["text"],
                    metadata={"source": e["source"], "section": e["section"]}
                )
                all_docs.append(doc)
        except Exception as err:
            print(f"Error in {path}: {err}")
    return all_docs

def split_and_store(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(chunks, model)
    db.save_local(DB_DIR)
    print(f"✅ Saved {len(chunks)} chunks to vectorstore")

if __name__ == '__main__':
    docs = parse_all_files()
    split_and_store(docs)
