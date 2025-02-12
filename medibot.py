import os
import streamlit as st

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint

DB_FAISS_PATH = "vectorstore/db_faiss"

# Ensure HF Token is set
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    st.error("Hugging Face API token is missing. Set HF_TOKEN as an environment variable.")

# Load FAISS Vector Store
@st.cache_resource
def get_vectorstore():
    """Loads FAISS vector store with error handling."""
    if not os.path.exists(DB_FAISS_PATH):
        st.error("FAISS database not found! Ensure it is built first.")
        return None  # Prevent crash

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    try:
        db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
        return db
    except Exception as e:
        st.error(f"Error loading FAISS database: {str(e)}")
        return None

# Load Hugging Face Model
def load_llm(huggingface_repo_id):
    """Load Hugging Face LLM model correctly."""
    llm = HuggingFaceEndpoint(
        repo_id=huggingface_repo_id,
        temperature=0.5,
        task="text-generation",  # Explicitly define the task
        model_kwargs={"max_length": 512},
        huggingfacehub_api_token=HF_TOKEN  # Correct token handling
    )
    return llm

# Set Custom Prompt
def set_custom_prompt(custom_prompt_template):
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])

# Streamlit UI
def main():
    st.title("Ask Chatbot!")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        st.chat_message(message["role"]).markdown(message["content"])

    prompt = st.chat_input("Ask your question here...")

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        CUSTOM_PROMPT_TEMPLATE = """
        Use the pieces of information provided in the context to answer the user's question.
        If you don't know the answer, just say that you don't know. Don't try to make up an answer.
        Don't provide anything out of the given context.

        Context: {context}
        Question: {question}

        Start the answer directly. No small talk, please.
        """

        HUGGINGFACE_REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"

        try:
            vectorstore = get_vectorstore()
            if vectorstore is None:
                st.error("Failed to load the vector store")
                return  # Stop execution if FAISS is missing

            qa_chain = RetrievalQA.from_chain_type(
                llm=load_llm(HUGGINGFACE_REPO_ID),
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
            )

            # Run Query
            response = qa_chain.invoke({"query": prompt})  # Corrected key

            result = response["result"]
            source_documents = response["source_documents"]
            result_to_show = result + "\n\n📚 **Source Docs:**\n" + str(source_documents)

            st.chat_message("assistant").markdown(result_to_show)
            st.session_state.messages.append({"role": "assistant", "content": result_to_show})

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
