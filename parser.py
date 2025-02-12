import xml.etree.ElementTree as ET
import json

# ✅ XML-Datei laden und parsen
def parse_medical_xml(xml_datei):
    baum = ET.parse(xml_datei)
    wurzel = baum.getroot()

    extrahierte_daten = {
        "metadaten": {
            "titel": "",
            "dokument_id": "",
            "verlag": "Thieme Compliance GmbH",
            "autoren": [],
            "veröffentlichungsdatum": "",
            "sprache": "de-DE",
            "länder_codes": []
        },
        "einleitung": "",
        "indikation": "",
        "verfahren": "",
        "alternativen": "",
        "risikokatalog": {
            "titel": "Risiken und mögliche Komplikationen",
            "einleitung": "",
            "risikogruppen": [],
            "schlussbemerkungen": "",
            "referenzen": []
        },
        "verhaltenshinweise": {
            "titel": "Verhaltenshinweise",
            "richtlinien": {
                "vor_der_behandlung": [],
                "nach_der_behandlung": []
            }
        },
        "erfolgsaussichten": {
            "titel": "Erfolgsaussichten",
            "inhalt": ""
        }
    }

    # ✅ Metadaten extrahieren
    metadaten_bereich = wurzel.find("metadaten")
    if metadaten_bereich is not None:
        extrahierte_daten["metadaten"]["dokument_id"] = metadaten_bereich.findtext("metadaten-allgemein/metadatum-bogencode", "").strip()
        extrahierte_daten["metadaten"]["veröffentlichungsdatum"] = metadaten_bereich.findtext("metadaten-impressum/metadatum-red-datum", "").strip()

        # Länder-Codes extrahieren
        extrahierte_daten["metadaten"]["länder_codes"] = [
            land.get("laender-id") for land in metadaten_bereich.findall("metadaten-allgemein/metadatum-laender-id")
        ]

        # Autoreninformationen extrahieren
        autoren = metadaten_bereich.findall("metadaten-impressum/metadatum-autoren/person")
        extrahierte_daten["metadaten"]["autoren"] = [
            f"{autor.findtext('akgrad', '').strip()} {autor.findtext('vname', '').strip()} {autor.findtext('nname', '').strip()}".strip()
            for autor in autoren if autor.findtext("nname") is not None
        ]

    # ✅ Dokumenttitel extrahieren
    kopfdaten = wurzel.find("kopfdaten")
    if kopfdaten is not None:
        titel = kopfdaten.findtext("titel", "").strip()
        untertitel = kopfdaten.findtext("untertitel", "").strip()
        extrahierte_daten["metadaten"]["titel"] = f"{titel} {untertitel}" if untertitel else titel

    # ✅ Einleitung extrahieren
    extrahierte_daten["einleitung"] = wurzel.findtext("infoteil/einleitung/a", "").strip()

    # ✅ Indikation extrahieren
    indikation_bereich = wurzel.find("infoteil/indikation")
    if indikation_bereich is not None:
        titel = indikation_bereich.find("titel")
        inhalt = indikation_bereich.find("a")

        extrahierte_daten["indikation"] = {
            "titel": titel.text.strip() if titel is not None else "",
            "inhalt": inhalt.text.strip() if inhalt is not None else ""
        }

    # ✅ Verfahren extrahieren
    extrahierte_daten["verfahren"] = wurzel.findtext("infoteil/massnahme/a", "").strip()

    # ✅ Alternativen extrahieren
    extrahierte_daten["alternativen"] = wurzel.findtext("infoteil/alternativen/a", "").strip()

    # ✅ Risiken (Risikokatalog) extrahieren
    risikokatalog = wurzel.find("infoteil/risikokatalog")
    if risikokatalog is not None:
        extrahierte_daten["risikokatalog"]["einleitung"] = risikokatalog.findtext("vorspann/a", "").strip()

        # ✅ Schlussbemerkungen aus <nachspann> extrahieren
        nachspann = risikokatalog.find("nachspann/a")
        if nachspann is not None:
            extrahierte_daten["risikokatalog"]["schlussbemerkungen"] = formatierten_text_extrahieren(nachspann)

        # ✅ Literaturverweise aus <vorspann>/literatur extrahieren
        referenzen = [
            ref.text.strip() for ref in risikokatalog.findall("vorspann/a/literatur") if ref.text and ref.text.strip()
        ]
        extrahierte_daten["risikokatalog"]["referenzen"] = referenzen

        # ✅ Risikogruppen extrahieren
        for risikogruppe in risikokatalog.findall("risikogruppe"):
            gruppe = {
                "kompakt": risikogruppe.get("kompakt", "undefiniert"),
                "risiken": []
            }

            for risiko in risikogruppe.findall("risiko"):
                häufigkeit = risiko.get("haeufigkeit", "undefiniert")
                beschreibung = formatierten_text_extrahieren(risiko)
                gruppe["risiken"].append({"häufigkeit": häufigkeit, "beschreibung": beschreibung})

            # Referenzierte Risiken verarbeiten
            for risiko_ref in risikogruppe.findall("risiko-ref/risiko"):
                häufigkeit = risiko_ref.get("haeufigkeit", "undefiniert")
                beschreibung = formatierten_text_extrahieren(risiko_ref)
                gruppe["risiken"].append({"häufigkeit": häufigkeit, "beschreibung": beschreibung})

            extrahierte_daten["risikokatalog"]["risikogruppen"].append(gruppe)

    # ✅ Verhaltenshinweise extrahieren
    richtlinien = wurzel.find("infoteil/verhaltenshinweise")
    if richtlinien is not None:
        for gruppe in richtlinien.findall("verhaltenshinweisgruppe"):
            titel = gruppe.findtext("titel", "").strip().lower()
            anweisungen = [formatierten_text_extrahieren(hinweis) for hinweis in gruppe.findall("verhaltenshinweis")]

            if "vor" in titel:
                extrahierte_daten["verhaltenshinweise"]["richtlinien"]["vor_der_behandlung"].extend(anweisungen)
            elif "nach" in titel:
                extrahierte_daten["verhaltenshinweise"]["richtlinien"]["nach_der_behandlung"].extend(anweisungen)

    # ✅ Erfolgsaussichten extrahieren
    extrahierte_daten["erfolgsaussichten"]["inhalt"] = wurzel.findtext("infoteil/erfolgsaussichten/a", "").strip()

    return extrahierte_daten

# ✅ Formatierten Text extrahieren, einschließlich <b> und <medikament> für fette Schrift
def formatierten_text_extrahieren(element):
    text = ""
    for knoten in element.iter():
        if knoten.tag in ["b", "medikament"]:
            text += f"**{knoten.text.strip()}** " if knoten.text else ""
        elif knoten.text:
            text += knoten.text.strip() + " "
    return text.strip()

# ✅ Extrahierte Daten als JSON speichern
def speichere_json(daten, ausgabe_datei):
    with open(ausgabe_datei, "w", encoding="utf-8") as datei:
        json.dump(daten, datei, ensure_ascii=False, indent=4)

# ✅ Parser ausführen
xml_datei = "data/IP07.xml"
ausgabe_json = "medizinische_daten.json"

extrahierte_daten = parse_medical_xml(xml_datei)
speichere_json(extrahierte_daten, ausgabe_json)

print(f"✅ Parsing abgeschlossen! Daten gespeichert in {ausgabe_json}")
