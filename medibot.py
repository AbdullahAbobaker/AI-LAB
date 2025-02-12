import os
import streamlit as st

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint

# ✅ Define FAISS Database Path
DB_FAISS_PATH = "vectorstore/db_faiss"

# ✅ Ensure Hugging Face API Token
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    st.error("⚠️ Hugging Face API token is missing. Please set HF_TOKEN as an environment variable.")

# ✅ Load FAISS Vector Store
@st.cache_resource
def get_vectorstore():
    """Loads FAISS vector store with error handling."""
    if not os.path.exists(DB_FAISS_PATH):
        st.error("⚠️ FAISS database not found! Ensure it is built first.")
        return None  # Prevents crashes

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    try:
        db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
        return db
    except Exception as e:
        st.error(f"⚠️ Error loading FAISS database: {str(e)}")
        return None

# ✅ Load Hugging Face Model
def load_llm(huggingface_repo_id):
    """Loads Hugging Face LLM model correctly."""
    return HuggingFaceEndpoint(
        repo_id=huggingface_repo_id,
        temperature=0.1,
        task="text-generation",
        model_kwargs={"max_length": 512},
        huggingfacehub_api_token=HF_TOKEN
    )

# ✅ Set Custom Prompt
def set_custom_prompt(custom_prompt_template):
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])

# ✅ Streamlit UI
def main():
    st.title("💬 Medizinischer Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        st.chat_message(message["role"]).markdown(message["content"])

    prompt = st.chat_input("💬 Stelle deine medizinische Frage hier...")

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # ✅ Custom Prompt for the AI Model
        CUSTOM_PROMPT_TEMPLATE = """
        Verwende ausschließlich die Informationen aus dem Kontext, um die Frage des Benutzers zu beantworten.
        Falls du die Antwort nicht kennst, sag einfach, dass du es nicht weißt. Erfinde keine Antwort.
        Liefere keine Informationen außerhalb des gegebenen Kontexts.

        **Kontext:** {context}  
        **Frage:** {question}  

        Beginne die Antwort direkt. Keine Smalltalk-Antworten.
        """

        HUGGINGFACE_REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"

        try:
            # ✅ Load FAISS Vector Store
            vectorstore = get_vectorstore()
            if vectorstore is None:
                st.error("⚠️ Fehler: FAISS-Datenbank nicht geladen.")
                return  # Stop execution if FAISS is missing

            # ✅ Set Up Retrieval-Based QA Chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=load_llm(HUGGINGFACE_REPO_ID),
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
            )

            # ✅ Run Query (FIXED: Pass "query" key instead of "context/question")
            response = qa_chain.invoke({"query": prompt})  # ✅ FIXED HERE

            # ✅ Extract Response & Source Documents
            result = response.get("result", "⚠️ Keine Antwort erhalten.")
            source_documents = response.get("source_documents", [])

            # ✅ Format Source Documents Properly
            source_docs_preview = "\n\n📚 **Quellen:**\n"
            unique_sources = set()
            for doc in source_documents:
                source = doc.metadata.get('source', 'Unbekannte Quelle')
                section = doc.metadata.get('section', 'Unbekannter Abschnitt')
                source_text = f"`{source}` → **{section}**"
                if source_text not in unique_sources:
                    unique_sources.add(source_text)
                    source_docs_preview += f"{source_text}\n"

            # ✅ Final Answer Formatting
            result_to_show = f"📢 **Antwort:** {result}{source_docs_preview}"

            # ✅ Display Response in Chat
            st.chat_message("assistant").markdown(result_to_show)
            st.session_state.messages.append({"role": "assistant", "content": result_to_show})

        except Exception as e:
            st.error(f"⚠️ Fehler: {str(e)}")

if __name__ == "__main__":
    main()
