import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- API ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIG PAGINA ---
st.set_page_config(
    page_title="AI di Antonino: Crea il tuo Ebook",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS (UI PULITA E TITOLO VISIBILE) ---
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
    color: #31333F;
    text-align: center;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 15px;
    margin-bottom: 25px;
    border: 1px solid #e6e9ef;
}

.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3.5em;
    font-weight: bold;
    background-color: #f0f2f6 !important;
    color: #31333F !important;
    border: 1px solid #d3d6db;
}

.stButton>button:hover {
    border-color: #ff4b4b;
    color: #ff4b4b !important;
}
</style>
""", unsafe_allow_html=True)

# --- PDF ---
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore

    def header(self):
        if self.page_no() > 1 and self.autore:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(10)

# --- FUNZIONI ---

def pulisci_testo_ia(testo):
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte", "here is", "sure"]
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
            temperature=0.7
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    mappa = {}
    linee = testo.split('\n')
    for l in linee:
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.)', l)
        if match:
            cap_key = match.group(0).strip().title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Analisi tematica"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- UI HEADER ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")
    titolo_l = st.text_input("Titolo Libro")
    autore_l = st.text_input("Nome Autore", value="")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere/Settore", ["Manuale Tecnico", "Saggio Scientifico", "Manuale Psicologico", "Business & Marketing", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    trama = st.text_area("Trama o Argomento Principale", height=150)
    
    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- LOGICA ---
if titolo_l and trama:
    S_PROMPT = f"""
Sei un'autorità mondiale nel settore: {genere}. Scrivi in {lingua}.
Titolo: "{titolo_l}". Argomento: "{trama}".
REGOLE: Expertise di massimo livello, fonti attendibili, stile fluido, NO ripetizioni.
"""

    tab1, tab2, tab3 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura e Modifica", "📑 3. Esportazione"])

    # --- 1. INDICE ---
    with tab1:
        if st.button("Genera Indice Autorevole"):
            p_ind = f"Crea un indice logico per '{titolo_l}' basato su: {trama}."
            st.session_state["indice_raw"] = chiedi_gpt(p_ind, "Editor esperto.")
            sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area("Modifica Indice", value=st.session_state.get("indice_raw", ""), height=300)
        
        if st.button("Sincronizza Capitoli"):
            sync_capitoli()
            st.rerun()

    # --- 2. SCRITTURA E MODIFICA INTEGRATA ---
    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        cap_sel = st.selectbox("Seleziona la sezione su cui lavorare:", opzioni)
        key_sez = f"txt_{cap_sel.lower().replace(' ', '_').replace('.', '')}"

        col_generazione, col_rielaborazione = st.columns([1, 1])

        with col_generazione:
            if st.button(f"✨ Genera da Zero: {cap_sel}"):
                with st.spinner("L'esperto sta scrivendo..."):
                    testo_ia = chiedi_gpt(f"Sviluppa la sezione completa: '{cap_sel}'.", S_PROMPT)
                    st.session_state[key_sez] = testo_ia

        with col_rielaborazione:
            istr_mod = st.text_input("Istruzioni per rielaborare (es: 'Rendilo più tecnico')", key=f"istr_{key_sez}")
            if st.button(f"🚀 Rielabora con IA: {cap_sel}"):
                if key_sez in st.session_state and st.session_state[key_sez]:
                    with st.spinner("Rielaborazione in corso..."):
                        p_riel = f"RISCRIVI COMPLETAMENTE seguendo questa istruzione: {istr_mod}. Testo originale:\n{st.session_state[key_sez]}"
                        st.session_state[key_sez] = chiedi_gpt(p_riel, S_PROMPT + " Editor Senior.")
                        st.rerun()
                else:
                    st.warning("Genera prima il testo per poterlo rielaborare.")

        # Editor Manuale Sempre Visibile
        if key_sez in st.session_state:
            st.session_state[key_sez] = st.text_area("Editor Testuale (Modifica qui manualmente):", 
                                                    value=st.session_state[key_sez], 
                                                    height=450, 
                                                    key=f"input_{key_sez}")

    # --- 3. EXPORT ---
    with tab3:
        col1, col2 = st.columns(2)
        lista_f = ["txt_prefazione"] + [f"txt_{c.lower().replace(' ', '_').replace('.', '')}" for c in st.session_state.get("lista_capitoli", [])] + ["txt_ringraziamenti"]
        
        with col1:
            if st.button("Download PDF"):
                pdf = PDF(autore_l)
                pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in lista_f:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.replace("txt_", "").upper().replace("_", " "), 0, 1)
                        pdf.ln(10); pdf.set_font("Arial", "", 12)
                        pdf.multi_cell(0, 8, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")

        with col2:
            if st.button("Download Word"):
                doc = Document(); doc.add_heading(titolo_l, 0)
                if autore_l: doc.add_paragraph(f"Autore: {autore_l}")
                for s in lista_f:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.replace("txt_", "").upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 Scarica Word", buf_w, file_name=f"{titolo_l}.docx")
