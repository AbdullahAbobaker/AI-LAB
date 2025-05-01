import requests
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from functools import lru_cache
from rank_bm25 import BM25Okapi

DB_DIR = "vectorstore"
EMBEDDING_MODEL_NAME = "NeuML/pubmedbert-base-embeddings"
MISTRAL_ENDPOINT = "http://localhost:11434/api/generate"

# Optional: Normalize and clean queries
def preprocess_query(query: str) -> str:
    return query.strip().lower()

# Load FAISS DB and embedding model once and reuse
@lru_cache(maxsize=1)
def get_vector_db():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    db = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
    return db

# Hybrid search combining vector search and BM25
def hybrid_search(query: str, db, k: int = 4) -> list:
    # Vektorsuche: Mehr Dokumente abrufen für Kombination
    vector_results = db.similarity_search_with_score(query, k=k*2)
    
    # BM25-Suche
    tokenized_corpus = [doc.page_content.split() for doc, _ in vector_results]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split()
    bm25_scores = bm25.get_scores(tokenized_query)
    
    # Kombinieren der Scores
    combined_results = []
    for i, (doc, vector_score) in enumerate(vector_results):
        # Normalisieren des Vektor-Scores (1 - vector_score, da kleinerer Score = relevanter)
        normalized_vector_score = 1 - vector_score
        combined_score = 0.7 * normalized_vector_score + 0.3 * bm25_scores[i]
        combined_results.append((doc, combined_score))
    
    # Sortieren nach kombiniertem Score und Top-k auswählen
    combined_results.sort(key=lambda x: x[1], reverse=True)
    return combined_results[:k]

# Query Mistral model with structured prompt
def ask_with_mistral(context: str, question: str, model: str = "mistral") -> str:
    prompt = f"""
Du bist ein medizinischer Assistent.

ANTWORTE AUSSCHLIESSLICH basierend auf dem untenstehenden Kontext.
Wenn du die Antwort nicht eindeutig aus dem Kontext ableiten kannst, sage:

„Diese Information steht nicht in den vorliegenden Aufklärungsdokumenten.“

---------------------
KONTEXT:
{context}

---------------------
FRAGE:
{question}

ANTWORT:"""

    try:
        res = requests.post(MISTRAL_ENDPOINT, json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 1.0,
                "max_tokens": 300
            }
        })
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except requests.RequestException as e:
        return f"❌ Fehler beim Modellaufruf: {str(e)}"
    except KeyError:
        return "❌ Fehler: Keine Antwort vom Modell erhalten."

# Main entry function to handle a user query
def ask_question(query: str, k: int = 4) -> dict:
    query = preprocess_query(query)
    db = get_vector_db()

    # Verwende Hybrid-Suche statt direkter Vektorsuche
    results = hybrid_search(query, db, k=k)

    context = "\n\n".join([doc.page_content for doc, _ in results])
    
    sources = []
    seen = set()
    for doc, score in results:
        file = doc.metadata.get("source", "Unbekannt")
        kapitel = doc.metadata.get("kapitel", "Unbekannt")
        snippet = doc.page_content[:200].strip().replace("\n", " ") + "..."
        key = (file, kapitel)
        if key not in seen:
            sources.append(f"{file} – Kapitel: {kapitel}\n🔹 Auszug: {snippet}")
            seen.add(key)

    answer = ask_with_mistral(context, query)

    return {
        "answer": answer,
        "sources": sources,
        "raw_context": context
    }