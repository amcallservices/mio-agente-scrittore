import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- CONNESSIONE API ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="AI di Antonino: Crea il tuo Ebook",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DIZIONARIO TRADUZIONI INTERFACCIA ---
TRADUZIONI = {
    "Italiano": {
        "titolo_sidebar": "⚙️ Configurazione Editor",
        "label_titolo": "Titolo del Libro",
        "label_autore": "Nome Autore",
        "label_lingua": "Lingua",
        "label_genere": "Genere",
        "label_trama": "Trama o Argomento Principale",
        "btn_reset": "🔄 RESET PROGETTO",
        "tabs": ["📊 1. Indice", "✍️ 2. Scrittura & Modifica", "📖 3. Anteprima", "📑 4. Esporta"],
        "btn_gen_indice": "Genera Indice Professionale",
        "label_edit_indice": "Modifica Indice",
        "btn_sync": "Sincronizza Capitoli",
        "label_sez": "Seleziona sezione:",
        "btn_scrivi": "✨ SCRIVI SEZIONE",
        "label_istr": "Istruzioni modifica",
        "btn_rielabora": "🚀 RIELABORA SEZIONE",
        "msg_scrivendo": "L'esperto sta scrivendo...",
        "msg_rielaborando": "Rielaborazione in corso...",
        "anteprima_tit": "📖 Vista Lettura",
        "prefazione": "Prefazione",
        "ringraziamenti": "Ringraziamenti",
        "placeholder_trama": "Di cosa parla il tuo libro?"
    },
    "English": {
        "titolo_sidebar": "⚙️ Editor Setup",
        "label_titolo": "Book Title",
        "label_autore": "Author Name",
        "label_lingua": "Language",
        "label_genere": "Genre",
        "label_trama": "Plot or Main Topic",
        "btn_reset": "🔄 RESET PROJECT",
        "tabs": ["📊 1. Index", "✍️ 2. Write & Edit", "📖 3. Preview", "📑 4. Export"],
        "btn_gen_indice": "Generate Professional Index",
        "label_edit_indice": "Edit Index",
        "btn_sync": "Sync Chapters",
        "label_sez": "Select section:",
        "btn_scrivi": "✨ WRITE SECTION",
        "label_istr": "Edit instructions",
        "btn_rielabora": "🚀 REWRITE SECTION",
        "msg_scrivendo": "The expert is writing...",
        "msg_rielaborando": "Rewriting in progress...",
        "anteprima_tit": "📖 Reading View",
        "prefazione": "Preface",
        "ringraziamenti": "Acknowledgements",
        "placeholder_trama": "What is your book about?"
    },
    "Deutsch": {
        "titolo_sidebar": "⚙️ Editor-Setup",
        "label_titolo": "Buchtitel",
        "label_autore": "Name des Autors",
        "label_lingua": "Sprache",
        "label_genere": "Genre",
        "label_trama": "Handlung oder Hauptthema",
        "btn_reset": "🔄 PROJEKT ZURÜCKSETZEN",
        "tabs": ["📊 1. Index", "✍️ 2. Schreiben & Bearbeiten", "📖 3. Vorschau", "📑 4. Export"],
        "btn_gen_indice": "Professionellen Index generieren",
        "label_edit_indice": "Index bearbeiten",
        "btn_sync": "Kapitel synchronisieren",
        "label_sez": "Abschnitt auswählen:",
        "btn_scrivi": "✨ ABSCHNITT SCHREIBEN",
        "label_istr": "Bearbeitungsanweisungen",
        "btn_rielabora": "🚀 ABSCHNITT NEU SCHREIBEN",
        "msg_scrivendo": "Der Experte schreibt...",
        "msg_rielaborando": "Überarbeitung läuft...",
        "anteprima_tit": "📖 Leseansicht",
        "prefazione": "Vorwort",
        "ringraziamenti": "Danksagungen",
        "placeholder_trama": "Wovon handelt Ihr Buch?"
    }
    # È possibile aggiungere altre lingue seguendo lo stesso schema...
}

# --- BLOCCO CSS ---
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
.stButton>button {
    width: 100%; border-radius: 12px; height: 3.8em; font-weight: bold; font-size: 18px !important;
    background-color: #007BFF !important; color: white !important; border: none;
    box-shadow: 0px 4px 15px rgba(0, 123, 255, 0.3); transition: all 0.3s ease;
}
.stButton>button:hover { background-color: #0056b3 !important; transform: translateY(-2px); }
.preview-box { background-color: white; padding: 50px; border: 1px solid #d3d6db; border-radius: 10px; height: 650px; overflow-y: scroll; font-family: 'Times New Roman', serif; line-height: 1.8; color: #222; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & LINGUA ---
with st.sidebar:
    # Selezione lingua prima di tutto per aggiornare l'interfaccia
    lingua_scelta = st.selectbox("🌐 Select Language / Seleziona Lingua", list(TRADUZIONI.keys()))
    lang = TRADUZIONI[lingua_scelta]
    
    st.title(lang["titolo_sidebar"])
    titolo_l = st.text_input(lang["label_titolo"])
    autore_l = st.text_input(lang["label_autore"])
    genere = st.selectbox(lang["label_genere"], ["Manuale Tecnico", "Saggio Scientifico", "Manuale Psicologico", "Business", "Motivazionale", "Thriller", "Fantasy"])
    trama = st.text_area(lang["label_trama"], placeholder=lang["placeholder_trama"], height=150)
    
    if st.button(lang["btn_reset"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- FUNZIONI DI SERVIZIO ---
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.75
        )
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Error: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    mappa = {}
    for l in testo.split('\n'):
        match = re.search(r'(?i)(Capitolo|Chapter|Kapitel|Capítulo)\s*\d+|^\d+\.', l)
        if match:
            cap_key = match.group(0).strip().title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Analysis"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- UI PRINCIPALE ---
st.markdown(f'<div class="custom-title">AI di Antonino: {titolo_l if titolo_l else "Ebook Creator"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    S_PROMPT = f"Authority in {genere}. Write ONLY in {lingua_scelta}. Style: Expert, no repetitions, chapters 2000+ words."
    t1, t2, t3, t4 = st.tabs(lang["tabs"])

    with t1:
        if st.button(lang["btn_gen_indice"]):
            st.session_state["indice_raw"] = chiedi_gpt(f"Create professional index for '{titolo_l}' based on: {trama} in {lingua_scelta}.", "Editor.")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area(lang["label_edit_indice"], value=st.session_state.get("indice_raw", ""), height=300)
        if st.button(lang["btn_sync"]): sync_capitoli(); st.rerun()

    with t2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = [lang["prefazione"]] + st.session_state.get("lista_capitoli", []) + [lang["ringraziamenti"]]
        cap_sel = st.selectbox(lang["label_sez"], opzioni)
        key_sez = f"txt_{cap_sel.replace(' ', '_')}"

        c_g, c_r = st.columns(2)
        with c_g:
            if st.button(lang["btn_scrivi"]):
                with st.spinner(lang["msg_scrivendo"]):
                    st.session_state[key_sez] = chiedi_gpt(f"Write the full section '{cap_sel}' (min 2000 words) for book '{titolo_l}'.", S_PROMPT)
        with c_r:
            istr_mod = st.text_input(lang["label_istr"], key=f"istr_{key_sez}")
            if st.button(lang["btn_rielabora"]):
                with st.spinner(lang["msg_rielaborando"]):
                    st.session_state[key_sez] = chiedi_gpt(f"Rewrite this following: {istr_mod}. Text:\n{st.session_state.get(key_sez, '')}", S_PROMPT)
        st.session_state[key_sez] = st.text_area("Editor:", value=st.session_state.get(key_sez, ""), height=400)

    with t3:
        st.subheader(lang["anteprima_tit"])
        preview_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        for s in [f"txt_{x.replace(' ', '_')}" for x in opzioni]:
            if s in st.session_state:
                preview_html += f"<h2>{s.replace('txt_', '').replace('_', ' ')}</h2><p>{st.session_state[s].replace('\\n', '<br>')}</p>"
        st.markdown(preview_html + "</div>", unsafe_allow_html=True)

    with t4:
        c1, c2 = st.columns(2)
        with c1: st.button("Download PDF") # Logica PDF precedente...
        with c2: st.button("Download Word") # Logica Word precedente...
else:
    st.info("👋 Setup Title and Topic to start.")
