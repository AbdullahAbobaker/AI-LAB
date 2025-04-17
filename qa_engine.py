
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

DB_DIR = "vectorstore"


def ask_with_mistral(context, question):
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

    res = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": 300
        }
    })
    return res.json()["response"]


def ask_question(query, k=4):
    # Load the FAISS vector store
    embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"device": "cpu"}
)

    db = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
    results = db.similarity_search_with_score(query, k=k)

    context = "\n\n".join([doc.page_content for doc, _ in results])
    sources = []
    seen = set()
    for doc, _ in results:
        file = doc.metadata.get("source", "Unbekannt")
        kapitel = doc.metadata.get("kapitel", "Unbekannt")
        key = (file, kapitel)
        if key not in seen:
            sources.append(f"{file} – Kapitel: {kapitel}")
            seen.add(key)

    answer = ask_with_mistral(context, query)
    return answer.strip(), sources
