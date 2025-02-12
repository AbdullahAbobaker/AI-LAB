import json
import os
import re
from langchain_community.document_loaders import UnstructuredXMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Define file paths
DATA_PATH = "/Users/abdullahabobaker/Documents/test/data/book.xml"
CHUNKS_PATH = "/Users/abdullahabobaker/Documents/test/data/book_chunks.txt"
CLEANED_JSON_PATH = "/Users/abdullahabobaker/Documents/test/data/book_chunks_cleaned.json"
DB_FAISS_PATH = "/Users/abdullahabobaker/Documents/test/vectorstore/db_faiss"

# Ensure directory exists for FAISS storage
os.makedirs(DB_FAISS_PATH, exist_ok=True)

# Step 1: Load and Save XML
def load_and_save_xml(file_path):
    """Loads XML and saves extracted content."""
    loader = UnstructuredXMLLoader(file_path)
    documents = loader.load()

    output_file = os.path.splitext(file_path)[0] + "_extracted.json"

    data = [{"content": doc.page_content, "metadata": doc.metadata} for doc in documents]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Extracted data saved to: {output_file}")
    return documents

documents = load_and_save_xml(DATA_PATH)

# Step 2: Create Chunks
def create_chunks(extracted_data):
    """Splits documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks

if documents:
    text_chunks = create_chunks(documents)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(text_chunks):
            f.write(f"Chunk {i+1}:\n{chunk.page_content}\n{'-'*50}\n")

    print(f"Text chunks saved to: {CHUNKS_PATH}")
else:
    print("No documents extracted. Please check the XML file.")

# Step 3: Clean Text and Preserve Metadata
def clean_text_with_metadata(text):
    """Cleans text while keeping metadata for citation tracking."""
    chunks = re.split(r"Chunk \d+:", text)
    cleaned_chunks = []

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        
        first_sentence = chunk.split(".")[0] if "." in chunk else chunk[:50]
        
        chunk = re.sub(r"\bDE\d+\b", "", chunk)
        chunk = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*", "", chunk)
        chunk = re.sub(r"[-]{5,}", "", chunk)
        chunk = re.sub(r"\s+", " ", chunk).strip()
        
        cleaned_chunks.append({
            "content": chunk,
            "source": "Book: Nierenbiopsie",
            "section": first_sentence
        })

    return cleaned_chunks

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    text = f.read()

cleaned_chunks = clean_text_with_metadata(text)

with open(CLEANED_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(cleaned_chunks, f, indent=4, ensure_ascii=False)

print(f"Cleaned text with metadata saved to: {CLEANED_JSON_PATH}")

# Step 4: Load Embedding Model
def get_embedding_model():
    """Loads HuggingFace Embedding Model."""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

embedding_model = get_embedding_model()
print("Embedding model loaded successfully.")

# Step 5: Convert Cleaned Chunks to Documents and Store in FAISS
if cleaned_chunks:
    documents_for_faiss = [
        Document(page_content=chunk["content"], metadata={"source": chunk["source"], "section": chunk["section"]})
        for chunk in cleaned_chunks
    ]

    db = FAISS.from_documents(documents_for_faiss, embedding_model)
    db.save_local(DB_FAISS_PATH)

    print(f"FAISS Vectorstore saved at: {DB_FAISS_PATH}")
else:
    print("No cleaned text available for FAISS.")

def retrieve_answer(query, top_k=3):
    """Retrieves the most relevant answer from FAISS."""
    query_embedding = embedding_model.embed_query(query)
    
    docs = db.similarity_search_by_vector(query_embedding, k=top_k)
    
    response = []
    for doc in docs:
        response.append(f"📢 **Antwort:** {doc.page_content}\n📖 **Quelle:** {doc.metadata['source']} - {doc.metadata['section']}\n{'-'*50}")

    return "\n".join(response)


