import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from qa_engine import ask_question
import torch
if torch.cuda.is_available():
    raise RuntimeError("CUDA is unexpectedly enabled!")

st.set_page_config(page_title="🧠 Medizinischer Aufklärungs-Bot")

st.title("🧠 Medizinischer Aufklärungs-Bot")
st.write("Stelle eine medizinische Frage basierend auf den Thieme-Aufklärungsbögen.")

query = st.text_input("❓ Was möchtest du wissen?")

if query:
    with st.spinner("Suche Antwort..."):
        answer, references = ask_question(query)
    st.markdown("### 💬 Antwort:")
    st.write(answer)
    st.markdown("### 📚 Quellen:")
    for ref in references:
        st.write(f"- {ref}")
