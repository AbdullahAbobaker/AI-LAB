import os
import glob
from xml_parser import extract_text_chunks_from_xml  # Adjust if your function is in a different file

DATA_DIR = "data"  # Your XML folder
MAX_CHARS = 1000   # Max characters per chunk

def load_all_xml_files(directory, pattern="*.xml"):
    return glob.glob(os.path.join(directory, "**", pattern), recursive=True)

if __name__ == "__main__":
    xml_files = load_all_xml_files(DATA_DIR)

    if not xml_files:
        print("❌ No XML files found in the data folder.")
        exit(1)

    print(f"📦 Found {len(xml_files)} XML files in '{DATA_DIR}'\n")

    total_chunks = 0
    for file_path in xml_files:
        print(f"🔍 Processing: {file_path}")
        chunks = extract_text_chunks_from_xml(file_path, max_chunk_chars=MAX_CHARS)
        total_chunks += len(chunks)

        for i, chunk in enumerate(chunks):
            print("=" * 80)
            print(f"📚 Chunk {i + 1}")
            print(f"File   : {chunk['file']}")
            print(f"Kapitel: {chunk['kapitel']}")
            print(f"Text   :\n{chunk['text'][:1000]}")
            print("=" * 80 + "\n")

    print(f"✅ Done. Total chunks extracted: {total_chunks}")
