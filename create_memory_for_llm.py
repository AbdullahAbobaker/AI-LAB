import os
import json
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings

# ✅ Define Correct File Paths
DATA_JSON_PATH = "/Users/abdullahabobaker/Desktop/AI-LAB/medizinische_daten.json"  # Fix: Corrected to JSON file
DB_FAISS_PATH = "/Users/abdullahabobaker/Desktop/AI-LAB/vectorstore/db_faiss"

# ✅ Ensure FAISS Directory Exists
os.makedirs(DB_FAISS_PATH, exist_ok=True)

# ✅ Load Embedding Model
def get_embedding_model():
    """Loads HuggingFace Embedding Model."""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

embedding_model = get_embedding_model()
print("✅ Embedding model loaded successfully.")

# ✅ Load and Chunk Medical Data
def load_medical_data():
    """Loads and structures medical data for FAISS embedding."""
    
    # 🚨 Validate if the file exists and is a JSON file
    if not os.path.exists(DATA_JSON_PATH):
        print("❌ JSON file not found!")
        return []
    
    if not DATA_JSON_PATH.endswith(".json"):
        print("❌ Invalid file type! Expected a JSON file.")
        return []

    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)  # Fix: Properly loading JSON
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format!")
        return []

    documents = []
    
    # Extract sections dynamically
    for section, content in data.items():
        if isinstance(content, dict):  # Handle nested dictionaries
            for sub_section, sub_content in content.items():
                if isinstance(sub_content, str) and sub_content.strip():
                    documents.append(Document(
                        page_content=sub_content.strip(),
                        metadata={"source": "medizinische_daten.json", "section": f"{section} - {sub_section}"}
                    ))
                elif isinstance(sub_content, list):  # Handle lists
                    for item in sub_content:
                        if isinstance(item, str) and item.strip():
                            documents.append(Document(
                                page_content=item.strip(),
                                metadata={"source": "medizinische_daten.json", "section": f"{section} - {sub_section}"}
                            ))
        elif isinstance(content, str) and content.strip():
            documents.append(Document(
                page_content=content.strip(),
                metadata={"source": "medizinische_daten.json", "section": section}
            ))

    print(f"✅ Loaded {len(documents)} chunks from JSON.")
    return documents

medical_chunks = load_medical_data()

# ✅ Save FAISS Database
def save_faiss():
    """Saves FAISS vector database from structured medical data."""
    if medical_chunks:
        db = FAISS.from_documents(medical_chunks, embedding_model)
        
        # 🚨 Ensure FAISS is saved properly
        db.save_local(DB_FAISS_PATH)

        print(f"✅ FAISS Vectorstore successfully saved at: {DB_FAISS_PATH}")
    else:
        print("⚠️ No cleaned text available for FAISS.")

save_faiss()

# ✅ Load FAISS Database
def load_faiss():
    """Loads FAISS vector store if it exists."""
    index_path = os.path.join(DB_FAISS_PATH, "index.faiss")
    
    # 🚨 Check if FAISS exists before loading
    if os.path.exists(index_path):
        print("✅ FAISS database found. Loading...")
        return FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
    else:
        print("⚠️ FAISS database not found. Ensure it has been saved first.")
        return None

db = load_faiss()

# ✅ Query FAISS with improved ranking
def retrieve_answer(query, top_k=3):
    """Retrieves the most relevant answer from FAISS, ensuring correct score handling and prioritization."""
    if db is None:
        return "⚠️ FAISS database not loaded. Ensure it is saved and exists."

    query_embedding = embedding_model.embed_query(query)

    # Perform similarity search
    docs_with_scores = db.similarity_search_with_score_by_vector(query_embedding, k=top_k * 5)  

    print("🔍 Debugging FAISS Results:")
    for doc, score in docs_with_scores:
        print(f"Score: {score:.4f} | {doc.metadata['section']} → {doc.page_content[:100]}")

    # ✅ Normalize FAISS Scores (Fix: Ensure similarity-based sorting)
    corrected_docs = []
    for doc, score in docs_with_scores:
        corrected_score = 1 - score if score > 1.0 else score  # Ensure scores are in [0,1] range
        corrected_docs.append((doc, corrected_score))

    # ✅ Strictly Filter for "alternativen" Section or Related Content
    filtered_docs = [
        (doc, score) for doc, score in corrected_docs
        if "alternativen" in doc.metadata['section'].lower() or "alternative" in doc.metadata['section'].lower()
    ]

    # ✅ If no direct "alternativen" results, allow related sections
    if not filtered_docs:
        filtered_docs = [
            (doc, score) for doc, score in corrected_docs
            if len(doc.page_content) > 50  # Ensure the content is meaningful
            and not any(kw in doc.metadata['section'].lower() for kw in ["indikation", "verfahren", "risikokatalog", "metadaten"])
        ]

    # ✅ Sort by (1) Corrected Score and (2) Answer Length
    sorted_docs = sorted(filtered_docs, key=lambda d: (d[1], len(d[0].page_content)), reverse=True)[:top_k]

    if not sorted_docs:
        return "⚠️ Keine relevanten Antworten gefunden."

    response = []
    for doc, score in sorted_docs:
        response.append(
            f"📢 **Antwort:** {doc.page_content}\n"
            f"📖 **Quelle:** {doc.metadata['source']} - {doc.metadata['section']} (Score: {score:.4f})\n"
            f"{'-'*50}"
        )

    return "\n".join(response)




# ✅ Test with a Query
queries = [
    "Was sind die Alternativen zur Gewebeentnahme aus der Niere?"
]
for q in queries:
    print(f"\n🔎 Query: {q}")
    print(retrieve_answer(q))
