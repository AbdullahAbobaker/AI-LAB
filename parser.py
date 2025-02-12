import xml.etree.ElementTree as ET
import json

# Load and parse the XML file
def parse_medical_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    parsed_data = {
        "metadata": {
            "title": "",
            "document_id": "",
            "publisher": "Thieme Compliance GmbH",
            "authors": [],
            "publication_date": "",
            "language": "de-DE",
            "country_codes": []
        },
        "introduction": "",
        "indication": "",
        "procedure": "",
        "alternatives": "",
        "risikokatalog": {
            "title": "Risiken und mögliche Komplikationen",
            "introduction": "",
            "risk_groups": [],
            "closing_remarks": "",
            "references": []
        },
        "verhaltenshinweise": {
            "title": "Verhaltenshinweise",
            "guidelines": {
                "before_procedure": [],
                "after_procedure": []
            }
        },
        "erfolgsaussichten": {
            "title": "Erfolgsaussichten",
            "content": ""
        }
    }

    # ✅ Extract metadata
    metadata_section = root.find("metadaten")
    if metadata_section is not None:
        parsed_data["metadata"]["document_id"] = metadata_section.findtext("metadaten-allgemein/metadatum-bogencode", "").strip()
        parsed_data["metadata"]["publication_date"] = metadata_section.findtext("metadaten-impressum/metadatum-red-datum", "").strip()

        # Extract country codes
        parsed_data["metadata"]["country_codes"] = [
            country.get("laender-id") for country in metadata_section.findall("metadaten-allgemein/metadatum-laender-id")
        ]

        # Extract author information
        authors = metadata_section.findall("metadaten-impressum/metadatum-autoren/person")
        parsed_data["metadata"]["authors"] = [
            f"{author.findtext('akgrad', '').strip()} {author.findtext('vname', '').strip()} {author.findtext('nname', '').strip()}".strip()
            for author in authors if author.findtext("nname") is not None
        ]

    # ✅ Extract document title
    kopfdaten = root.find("kopfdaten")
    if kopfdaten is not None:
        title = kopfdaten.findtext("titel", "").strip()
        subtitle = kopfdaten.findtext("untertitel", "").strip()
        parsed_data["metadata"]["title"] = f"{title} {subtitle}" if subtitle else title

  
    # ✅ Extract introduction
    parsed_data["introduction"] = root.findtext("infoteil/einleitung/a", "").strip()


   # ✅ Extract "Indikation"
    indikation_section = root.find("infoteil/indikation")
    if indikation_section is not None:
        title = indikation_section.find("titel")
        content = indikation_section.find("a")

        parsed_data["indication"] = {
        "title": title.text.strip() if title is not None else "",
        "content": content.text.strip() if content is not None else ""
        }
        


    # ✅ Extract procedure
    parsed_data["procedure"] = root.findtext("infoteil/massnahme/a", "").strip()

    # ✅ Extract alternatives
    parsed_data["alternatives"] = root.findtext("infoteil/alternativen/a", "").strip()

    # ✅ Extract risks (Risikokatalog)
    risk_catalog = root.find("infoteil/risikokatalog")
    if risk_catalog is not None:
        parsed_data["risikokatalog"]["introduction"] = risk_catalog.findtext("vorspann/a", "").strip()

        # ✅ Extract "closing_remarks" from <nachspann>
        nachspann = risk_catalog.find("nachspann/a")
        if nachspann is not None:
            parsed_data["risikokatalog"]["closing_remarks"] = extract_formatted_text(nachspann)

        # ✅ Extract literature references from <vorspann>/literatur
        references = [
            ref.text.strip() for ref in risk_catalog.findall("vorspann/a/literatur") if ref.text and ref.text.strip()
        ]
        parsed_data["risikokatalog"]["references"] = references

        # ✅ Extract risk groups
        for risk_group in risk_catalog.findall("risikogruppe"):
            group = {
                "compact": risk_group.get("kompakt", "undefiniert"),
                "risks": []
            }

            for risiko in risk_group.findall("risiko"):
                severity = risiko.get("haeufigkeit", "undefiniert")
                description = extract_formatted_text(risiko)
                group["risks"].append({"severity": severity, "description": description})

            # Handle referenced risks
            for risiko_ref in risk_group.findall("risiko-ref/risiko"):
                severity = risiko_ref.get("haeufigkeit", "undefiniert")
                description = extract_formatted_text(risiko_ref)
                group["risks"].append({"severity": severity, "description": description})

            parsed_data["risikokatalog"]["risk_groups"].append(group)

    # ✅ Extract behavioral guidelines
    guidelines = root.find("infoteil/verhaltenshinweise")
    if guidelines is not None:
        for group in guidelines.findall("verhaltenshinweisgruppe"):
            title = group.findtext("titel", "").strip().lower()
            instructions = [extract_formatted_text(hint) for hint in group.findall("verhaltenshinweis")]

            if "vor" in title:
                parsed_data["verhaltenshinweise"]["guidelines"]["before_procedure"].extend(instructions)
            elif "nach" in title:
                parsed_data["verhaltenshinweise"]["guidelines"]["after_procedure"].extend(instructions)

    # ✅ Extract success prospects
    parsed_data["erfolgsaussichten"]["content"] = root.findtext("infoteil/erfolgsaussichten/a", "").strip()

    return parsed_data

# ✅ Extract formatted text, handling <b> and <medikament> for bold formatting
def extract_formatted_text(element):
    text = ""
    for node in element.iter():
        if node.tag in ["b", "medikament"]:
            text += f"**{node.text.strip()}** " if node.text else ""
        elif node.text:
            text += node.text.strip() + " "
    return text.strip()

# ✅ Save extracted data as JSON
def save_json(data, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# ✅ Run the parser
xml_file = "data/IP07.xml"
output_json = "medical_data.json"

parsed_data = parse_medical_xml(xml_file)
save_json(parsed_data, output_json)

print(f"✅ Parsing completed! Data saved in {output_json}")
