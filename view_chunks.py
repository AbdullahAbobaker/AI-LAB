import streamlit as st
import pandas as pd
import os
from xml_parser import extract_text_chunks_from_xml

st.title("📚 XML Chunk Explorer")

data_dir = "processed_files"
xml_files = [f for f in os.listdir(data_dir) if f.endswith(".xml")]

selected_file = st.selectbox("📂 Wähle eine Datei", xml_files)
if selected_file:
    chunks = extract_text_chunks_from_xml(os.path.join(data_dir, selected_file))
    df = pd.DataFrame(chunks)
    kapitel_list = sorted(df["kapitel"].unique())

    selected_kapitel = st.multiselect("🔍 Kapitel filtern", kapitel_list, default=kapitel_list)

    filtered = df[df["kapitel"].isin(selected_kapitel)]

    for idx, row in filtered.iterrows():
        st.markdown(f"### 📖 Kapitel: {row['kapitel']}")
        st.text_area("📄 Textchunk", row['text'], height=200)
        st.markdown("---")
