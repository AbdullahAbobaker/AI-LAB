
import os
import xml.etree.ElementTree as ET
import re


def clean_text(text):
    """
    Cleans extracted text by removing XML artifacts, redundant whitespace, and references.
    """
    text = re.sub(r'\s+', ' ', text)  # collapse whitespace
    text = re.sub(r'\(\d+\)', '', text)  # remove numbered references like (1)
    text = re.sub(r'\[[^\]]*\]', '', text)  # remove [references]
    return text.strip()


def extract_text_chunks_from_xml(xml_path, max_chunk_chars=1000):
    """
    Parses Thieme XML files and returns clean, structured chunks with accurate references.
    Covers all relevant sections (infoteil) and tags (a, risiko, verhaltenshinweis, etc.).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    chunks = []

    infoteil = root.find(".//infoteil")
    if infoteil is not None:
        for section in infoteil:
            kapitel_tag = section.tag
            kapitel_title = section.find("titel")
            kapitel = kapitel_title.text.strip() if kapitel_title is not None else kapitel_tag

            paragraphs = []
            for elem in section.iter():
                if elem.tag in ["a", "risiko", "verhaltenshinweis", "text", "p", "para", "absatz", "li", "subpara"]:
                    raw_text = ET.tostring(elem, encoding="unicode", method="text")
                    cleaned = clean_text(raw_text)
                    if cleaned and len(cleaned) > 60:
                        paragraphs.append(cleaned)

            full_text = "\n".join(paragraphs)

            # Final chunking
            for i in range(0, len(full_text), max_chunk_chars):
                chunk_text = full_text[i:i + max_chunk_chars].strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "kapitel": kapitel,
                        "file": os.path.basename(xml_path)
                    })

    return chunks