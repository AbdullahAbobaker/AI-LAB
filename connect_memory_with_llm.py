import pickle
import faiss
import numpy as np
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from openai import OpenAI  # or whatever you're using

DB_FAISS_PATH = "AI-LAB/vectorstore/db_faiss"
INDEX_PATH = f"{DB_FAISS_PATH}/index.faiss"
CHUNKS_PATH = f"{DB_FAISS_PATH}/index.pkl"

def load_index_and_chunks():
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, 'rb') as f:
        chunks = pickle.load(f)
    return index, chunks

def retrieve_context(query, model, index, chunks, top_k=5):
    query_embedding = model.embed_query(query)
    D, I = index.search(np.array([query_embedding]).astype('float32'), top_k)
    return ' '.join([chunks[i] for i in I[0]])

def ask_llm(context, question):
    # Use your API (like OpenAI, HuggingFace or local model)
    response = OpenAI().chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a medical assistant."},
            {"role": "user", "content": f"{context}\n\nQuestion: {question}"}
        ]
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    index, chunks = load_index_and_chunks()

    question = input("🩺 Ask a medical question: ")
    context = retrieve_context(question, embeddings, index, chunks)
    answer = ask_llm(context, question)
    print("\n🤖 Answer:", answer)
