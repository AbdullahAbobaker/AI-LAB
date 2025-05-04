import streamlit as st
import sys
sys.path.insert(0, '/Users/abdullahabobaker/Documents/AI-LAB')
from qa_engine import ask_question
import os
from datetime import datetime

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="🧠 Medizinischer Aufklärungs-Bot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Path setup - uncomment if needed
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your QA engine - replace with actual implementation


# Custom CSS for better styling
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4e8cff;
    }
    .resource-btn {
        width: 100%;
        text-align: left;
        margin-bottom: 0.5rem;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'resource_content' not in st.session_state:
    st.session_state.resource_content = {}
    # Sample resource content (to be replaced with actual content)
    st.session_state.resource_content = {
        "Gewebeentnahme aus der Niere": {
            "description": "Informationen zur Nierenbiopsie, einem diagnostischen Verfahren zur Entnahme von Nierengewebe für weitere Untersuchungen.",
            "risks": ["Blutung", "Infektion", "Schmerzen"],
            "procedure": "Ein kleines Stück Nierengewebe wird mit einer speziellen Nadel unter lokaler Betäubung entnommen."
        },
        "Renale Denervierung mittels Katheterablation zur Behandlung arterieller Hypertonie": {
            "description": "Ein minimalinvasives Verfahren zur Behandlung von schwer einstellbarem Bluthochdruck.",
            "risks": ["Gefäßverletzung", "Nierenarterienstenose", "Unzureichende Wirkung"],
            "procedure": "Über einen Katheter werden die Nerven der Nierenarterien verödet, um den Blutdruck zu senken."
        },
        "Hämodialyse/Hämofiltration/Hämodiafiltration": {
            "description": "Verfahren zur Blutreinigung bei Nierenversagen.",
            "risks": ["Blutdruckabfall", "Krämpfe", "Infektionen am Gefäßzugang"],
            "procedure": "Das Blut wird außerhalb des Körpers gefiltert und gereinigt, bevor es zurückgeführt wird."
        },
        "Nierentransplantation": {
            "description": "Chirurgischer Eingriff zur Implantation einer Spenderniere.",
            "risks": ["Abstoßungsreaktionen", "Infektionen", "Komplikationen durch Immunsuppression"],
            "procedure": "Eine gesunde Niere eines Spenders wird chirurgisch in den Körper des Empfängers eingesetzt."
        }
    }

# Create three columns - chat history, main content, and resources
col1, col2, col3 = st.columns([3, 4, 3])

# Left column - Chat History
with col1:
    st.markdown("### 💬 Chat-Verlauf")
    
    # Search in chat history
    search_query = st.text_input("🔍 Suche im Chatverlauf", key="search_history")
    
    # Display chat history with filtering
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.info("Noch keine Unterhaltung. Stelle eine Frage, um zu beginnen.")
        else:
            filtered_history = st.session_state.chat_history
            if search_query:
                filtered_history = [(q, a, refs, ts) for q, a, refs, ts in st.session_state.chat_history 
                                   if search_query.lower() in q.lower() or search_query.lower() in a.lower()]
                
                if not filtered_history:
                    st.warning(f"Keine Ergebnisse für '{search_query}'")
            
            for i, (q, a, refs, timestamp) in enumerate(filtered_history):
                with st.container():
                    st.markdown(f"<div class='chat-message'>", unsafe_allow_html=True)
                    col_time, col_actions = st.columns([3, 1])
                    with col_time:
                        st.markdown(f"**{timestamp}**")
                    with col_actions:
                        if st.button("↻", key=f"retry_{i}", help="Diese Frage erneut stellen"):
                            st.session_state.retry_query = q
                            st.rerun()
                    
                    st.markdown(f"**Frage:** {q}")
                    with st.expander("Antwort anzeigen"):
                        st.markdown(f"**Antwort:** {a}")
                        st.markdown("**Quellen:**")
                        for ref in refs:
                            st.markdown(f"- {ref}")
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # Control buttons
    col_clear, col_export = st.columns(2)
    with col_clear:
        if st.button("🗑️ Verlauf löschen", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col_export:
        if st.button("📥 Exportieren", use_container_width=True, help="Chatverlauf als Text herunterladen"):
            # Create export text
            export_text = "# Medizinischer Aufklärungs-Bot - Chatverlauf\n\n"
            for q, a, refs, ts in st.session_state.chat_history:
                export_text += f"## {ts}\n\n"
                export_text += f"**Frage:** {q}\n\n"
                export_text += f"**Antwort:** {a}\n\n"
                export_text += "**Quellen:**\n"
                for ref in refs:
                    export_text += f"- {ref}\n"
                export_text += "\n---\n\n"
            
            # Provide download link
            st.download_button(
                label="Download als Text",
                data=export_text,
                file_name=f"med_bot_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# Middle column - Main Q&A Interface
with col2:
    st.title("🧠 Medizinischer Aufklärungs-Bot")
    st.write("Stelle eine medizinische Frage basierend auf den Thieme-Aufklärungsbögen.")
    
    # Check if there's a retry query
    query = ""
    if 'retry_query' in st.session_state and st.session_state.retry_query:
        query = st.session_state.retry_query
        st.session_state.retry_query = ""
    
    # User input with prefilled value if retrying
    query = st.text_input("❓ Was möchtest du wissen?", value=query)
    
    # Example questions for guidance
    with st.expander("🔍 Beispielfragen"):
        example_questions = [
            "Was ist eine Nierenbiopsie?",
            "Welche Risiken bestehen bei einer Nierentransplantation?",
            "Warum ist die Dialysebehandlung notwendig?",
            "Gibt es Alternativen zur renalen Denervierung?"
        ]
        for eq in example_questions:
            if st.button(eq, key=f"ex_{eq}"):
                st.session_state.retry_query = eq
                st.rerun()
    
    if query:
        with st.spinner("Suche Antwort..."):
            response = ask_question(query)
            answer = response["answer"]
            references = response["sources"]
            # optional: context = response["raw_context"]

        
        st.markdown("### 💬 Antwort:")
        st.markdown(f"<div class='chat-message'>{answer}</div>", unsafe_allow_html=True)
        
        st.markdown("### 📚 Quellen:")
        if references:
            for ref in references:
                st.markdown(f"- {ref}")
        else:
            st.info("Keine spezifischen Quellen identifiziert.")
        
        # Feedback buttons
        col_helpful, col_not_helpful = st.columns(2)
        with col_helpful:
            st.button("👍 Hilfreich", use_container_width=True)
        with col_not_helpful:
            st.button("👎 Nicht hilfreich", use_container_width=True)
        
        # Add to chat history if not already from retry
        if 'retry_query' not in st.session_state or not st.session_state.retry_query:
            timestamp = datetime.now().strftime("%d.%m.%Y, %H:%M")
            st.session_state.chat_history.append((query, answer, references, timestamp))

# Right column - Resources
with col3:
    st.markdown("### 📋 Liste der Ressourcen")
    
    resources = [
        "Gewebeentnahme aus der Niere",
        "Renale Denervierung mittels Katheterablation zur Behandlung arterieller Hypertonie",
        "Hämodialyse/Hämofiltration/Hämodiafiltration",
        "Nierentransplantation"
    ]
    
    # Resource filter
    resource_filter = st.text_input("🔍 Ressourcen filtern", key="filter_resources")
    
    # Display filtered resources
    filtered_resources = [r for r in resources if resource_filter.lower() in r.lower()] if resource_filter else resources
    
    for resource in filtered_resources:
        if st.button(resource, key=resource):
            st.session_state.selected_resource = resource
    
    # Display selected resource if any
    if 'selected_resource' in st.session_state:
        resource = st.session_state.selected_resource
        st.markdown(f"### {resource}")
        
        if resource in st.session_state.resource_content:
            content = st.session_state.resource_content[resource]
            st.markdown(f"**Beschreibung:** {content['description']}")
            
            st.markdown("**Risiken:**")
            for risk in content['risks']:
                st.markdown(f"- {risk}")
                
            st.markdown(f"**Verfahren:** {content['procedure']}")
            
            # Related questions
            st.markdown("**Häufige Fragen:**")
            related_questions = [
                f"Was ist {resource}?",
                f"Wie läuft {resource} ab?",
                f"Welche Risiken hat {resource}?"
            ]
            
            for question in related_questions:
                if st.button(question, key=f"q_{question}"):
                    st.session_state.retry_query = question
                    st.rerun()
        else:
            st.warning("Detaillierte Informationen zu dieser Ressource sind noch nicht verfügbar.")
        
        # Clear selection button
        if st.button("Ressource schließen", key="clear_resource"):
            del st.session_state.selected_resource
            st.rerun()

# Add footer with app info
st.markdown("---")
col_info, col_version = st.columns(2)
with col_info:
    st.markdown("**🧠 Medizinischer Aufklärungs-Bot** | Basierend auf Thieme-Aufklärungsbögen")
with col_version:
    st.markdown("**Version:** 1.0.0 | Letzte Aktualisierung: April 2025")