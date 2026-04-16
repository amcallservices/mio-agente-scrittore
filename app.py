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

# --- BLOCCO CSS (PULSANTI VISIBILI E UI) ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stHeader"] {display:none;}
.stDeployButton {display:none;}
[data-testid="collapsedControl"] { display: none !important; }

section[data-testid="stSidebar"] {
    min-width: 350px !important;
    max-width: 350px !important;
}

.custom-title {
    font-size: 38px;
    font-weight: bold;
    color: #1E1E1E;
    text-align: center;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 15px;
    margin-bottom: 25px;
    border: 1px solid #dee2e6;
}

/* --- STILE PULSANTI AD ALTA VISIBILITÀ --- */
.stButton>button {
    width: 100%;
    border-radius: 12px;
    height: 3.8em;
    font-weight: bold;
    font-size: 18px !important;
    background-color: #007BFF !important; /* Blu Acceso */
    color: white !important; /* Testo Bianco */
    border: none;
    box-shadow: 0px 4px 15px rgba(0, 123, 255, 0.3); /* Ombra blu */
    transition: all 0.3s ease;
    cursor: pointer;
    display: block;
    margin-top: 10px;
}

.stButton>button:hover {
    background-color: #0056b3 !important; /* Blu più scuro al passaggio */
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0px 6px 20px rgba(0, 86, 179, 0.4);
}

/* Stile Box Anteprima */
.preview-box {
    background-color: white;
    padding: 50px;
    border: 1px solid #d3d6db;
    border-radius: 10px;
    height: 650px;
    overflow-y: scroll;
    font-family: 'Times New Roman', serif;
    line-height: 1.8;
    color: #222;
}
</style>
""", unsafe_allow_html=True)

# --- GESTIONE PDF ---
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1 and self.autore:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Author: {self.autore}", 0, 0, 'C')
            self.ln(10)

# --- FUNZIONI DI SERVIZIO ---
def pulisci_testo_ia(testo):
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "fase", "parte", "here is", "sure"]
    linee = testo.split("\n")
    pulito = [l for l in linee if not any(l.lower().startswith(t) for t in tag_proibiti)]
    return "\n".join(pulito).strip()

def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.75
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Error: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    mappa = {}
    linee = testo.split('\n')
    for l in linee:
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.|Chapter\s*\d+)', l)
        if match:
            cap_key = match.group(0).strip().title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Analysis"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- INTERFACCIA ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Editor Setup")
    titolo_l = st.text_input("Titolo del Libro")
    autore_l = st.text_input("Nome Autore", value="")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere", ["Manuale Tecnico", "Saggio Scientifico", "Manuale Psicologico", "Business & Marketing", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    trama = st.text_area("Trama o Argomento Principale", height=150)
    
    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if titolo_l and trama:
    lingua_map = {
        "Italiano": ["Inizio", "Sviluppo", "Conclusione"],
        "English": ["Introduction", "Development", "Synthesis"],
        "Deutsch": ["Einleitung", "Entwicklung", "Zusammenfassung"],
        "Français": ["Introduction", "Développement", "Conclusion"],
        "Español": ["Introducción", "Desarrollo", "Conclusión"]
    }
    fasi = lingua_map.get(lingua, ["Part 1", "Part 2", "Part 3"])

    S_PROMPT = f"""
Sei un'autorità mondiale nel settore: {genere}. Scrivi in {lingua}.
Titolo: "{titolo_l}". Argomento: "{trama}".
REGOLE: Capitoli da 2000+ parole, stile esperto, NO ripetizioni, linguaggio tecnico e fluido.
"""

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura & Modifica", "📖 3. Anteprima", "📑 4. Esporta"])

    with tab1:
        if st.button(f"Genera Indice in {lingua}"):
            st.session_state["indice_raw"] = chiedi_gpt(f"Crea un indice professionale per '{titolo_l}' in {lingua}.", f"Editor in {lingua}")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Modifica Indice", value=st.session_state.get("indice_raw", ""), height=300)
        if st.button("Sincronizza Capitoli"):
            sync_capitoli()
            st.rerun()

    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        cap_sel = st.selectbox("Seleziona sezione:", opzioni)
        key_sez = f"txt_{cap_sel.lower().replace(' ', '_').replace('.', '')}"

        col_g, col_r = st.columns([1, 1])
        with col_g:
            if st.button(f"✨ SCRIVI: {cap_sel}"):
                with st.spinner(f"Scrittura in corso..."):
                    testo_ia = ""
                    for f in fasi:
                        testo_ia += chiedi_gpt(f"Scrivi la parte '{f}' di '{cap_sel}'. Sii estremamente dettagliato.", S_PROMPT) + "\n\n"
                    st.session_state[key_sez] = testo_ia

        with col_r:
            istr_mod = st.text_input("Istruzioni modifica", key=f"istr_{key_sez}")
            if st.button(f"🚀 RIELABORA SEZIONE"):
                if key_sez in st.session_state:
                    with st.spinner("Rielaborazione..."):
                        p_riel = f"RISCRIVI E ESPANDI in {lingua}: {istr_mod}. Testo attuale:\n{st.session_state[key_sez]}"
                        st.session_state[key_sez] = chiedi_gpt(p_riel, S_PROMPT)
                        st.rerun()

        if key_sez in st.session_state:
            st.session_state[key_sez] = st.text_area("Editor:", value=st.session_state[key_sez], height=450, key=f"input_{key_sez}")

    with tab3:
        lista_f = ["txt_prefazione"] + [f"txt_{c.lower().replace(' ', '_').replace('.', '')}" for c in st.session_state.get("lista_capitoli", [])] + ["txt_ringraziamenti"]
        preview_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: preview_html += f"<h3 style='text-align:center;'>{autore_l}</h3>"
        preview_html += "<hr><br>"
        for s in lista_f:
            if s in st.session_state and st.session_state[s].strip():
                preview_html += f"<h2>{s.replace('txt_', '').upper().replace('_', ' ')}</h2><p>{st.session_state[s].replace('\\n', '<br>')}</p><br>"
        preview_html += "</div>"
        st.markdown(preview_html, unsafe_allow_html=True)

    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download PDF"):
                pdf = PDF(autore_l); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in lista_f:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.replace("txt_", "").upper().replace("_", " "), 0, 1)
                        pdf.ln(10); pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 9, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        with col2:
            if st.button("Download Word"):
                doc = Document(); doc.add_heading(titolo_l, 0)
                if autore_l: doc.add_paragraph(f"Author: {autore_l}")
                for s in lista_f:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.replace("txt_", "").upper().replace("_", " "), level=1); doc.add_paragraph(st.session_state[s])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 Word", buf_w, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Inserisci Titolo e Trama a sinistra per visualizzare i comandi.")
