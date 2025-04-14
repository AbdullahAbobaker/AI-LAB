# universal_parser.py
import os
import re
import xml.etree.ElementTree as ET

def clean_text(text: str) -> str:
    """
    Remove redundant whitespace, references like (1), [bla], etc.
    """
    # Safely handle None
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)              # collapse whitespace
    text = re.sub(r"\(\d+\)", "", text)           # remove numbered references like (1)
    text = re.sub(r"\[[^\]]*\]", "", text)        # remove [refs]
    return text.strip()

def is_meaningful(text: str) -> bool:
    """
    Filter out lines that are too short or appear code-like.
    """
    if len(text) < 40:
        return False
    # If it has code patterns like 'rule ', 'SetSeverity', 'questProc', etc.
    # skip them
    text_lower = text.lower()
    code_words = ["rule ", "questproc", "setseverity", "insertquestion"]
    if any(kw in text_lower for kw in code_words):
        return False
    return True

def extract_text_chunks_from_xml(xml_path: str, max_chunk_chars=1000):
    """
    A universal parser that:
     1) Checks for known structures <infoteil> or <document>/<part>/<section> or fallback
     2) Extracts text from typical paragraph tags (<para>, <p>, <a>, <li>, etc.)
     3) Splits into ~max_chunk_chars
     4) Returns a list of { 'file':..., 'kapitel':..., 'text':... }
    """

    tree = ET.parse(xml_path)
    root = tree.getroot()
    chunks = []

    # We'll try to unify two possible structures:
    #  - <t0-dokument> with <infoteil> child
    #  - <document> with <part> or <section> child (like in cs_7857800_gekürzt.xml)
    # In either case, we need to gather text from typical tags.

    # Strategy:
    # 1) If <infoteil> is found -> parse like your old approach
    # 2) Otherwise, parse for <document> or <part> or <section>
    #    We'll treat <title> or <section> as 'chapter' triggers.

    def chunk_and_store(buffer, kapitel):
        combined = "\n".join(buffer).strip()
        buffer.clear()
        for i in range(0, len(combined), max_chunk_chars):
            piece = combined[i:i+max_chunk_chars].strip()
            if piece:
                chunks.append({
                    "file": os.path.basename(xml_path),
                    "kapitel": kapitel,
                    "text": piece
                })

    # -------------- Case 1: If <infoteil> exists --------------
    infoteil = root.find(".//infoteil")
    if infoteil is not None:
        for section in infoteil:
            # e.g. <massnahme>, <risikokatalog> ...
            kapitel_tag = section.tag
            kapitel_title_elem = section.find("titel")
            kapitel = kapitel_title_elem.text.strip() if kapitel_title_elem is not None else kapitel_tag

            paragraphs = []
            for elem in section.iter():
                if elem.tag in ["a", "risiko", "verhaltenshinweis", "text", "p", "para", "absatz", "li", "subpara"]:
                    raw_text = clean_text(ET.tostring(elem, encoding="unicode", method="text"))
                    if raw_text and is_meaningful(raw_text):
                        paragraphs.append(raw_text)

            full_text = "\n".join(paragraphs)
            for i in range(0, len(full_text), max_chunk_chars):
                chunk_text = full_text[i:i + max_chunk_chars].strip()
                if chunk_text:
                    chunks.append({
                        "file": os.path.basename(xml_path),
                        "kapitel": kapitel,
                        "text": chunk_text
                    })

        return chunks

    # -------------- Case 2: No <infoteil>: parse <document>, <part>, <section> --------------
    # We will do a DFS over all <section>, <title> or <para>, etc.

    results = []
    buffer = []
    current_chapter = "Einleitung"  # fallback

    def flush_buffer():
        nonlocal buffer, current_chapter
        if not buffer:
            return
        chunk_and_store(buffer, current_chapter)

    for elem in root.iter():
        tag = elem.tag.lower()
        text_raw = elem.text if elem.text else ""
        text_clean = clean_text(text_raw)

        # If it's a 'chapter' or 'title' or 'section' => flush old buffer, new chapter name
        if tag in ("title","chapter","kapitel","headline"):
            flush_buffer()
            if text_clean:
                current_chapter = text_clean
        elif tag in ("para","p","a","absatz","li","subpara","text","box","listing"):
            if text_clean and is_meaningful(text_clean):
                buffer.append(text_clean)
        # If <section> is encountered with an attribute e.g. <section level="1"> => maybe flush?
        # We'll treat them similarly.
        if tag == "section":
            # If it has an attribute like level=... or id=..., we might flush
            # But let's keep it simple:
            # if it's a new <section> with a 'title' child, we already catch that
            pass

    # flush the leftover buffer
    flush_buffer()
    return chunks + results
