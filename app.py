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

# --- BLOCCO CSS (UI PROFESSIONALE & ANTEPRIMA) ---
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
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
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.stButton>button {
    width: 100%;
    border-radius: 8px;
    height: 3.5em;
    font-weight: bold;
    background-color: #007BFF !important;
    color: white !important;
    transition: all 0.3s;
}

.stButton>button:hover {
    background-color: #0056b3 !important;
    transform: translateY(-2px);
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

# --- FUNZIONI ---
def pulisci_testo_ia(testo):
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "fase", "parte", "here is", "sure", "voilà"]
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
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.|Chapter\s*\d+|Capítulo\s*\d+)', l)
        if match:
            cap_key = match.group(0).strip().title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Deep Analysis"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- INTERFACCIA ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Editor Setup")
    titolo_l = st.text_input("Titolo del Libro")
    autore_l = st.text_input("Nome Autore", value="")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere", ["Manuale Tecnico", "Saggio Scientifico", "Manuale Psicologico", "Business", "Motivazionale", "Thriller", "Fantasy"])
    trama = st.text_area("Trama o Argomento", height=150)
    
    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if titolo_l and trama:
    # MAPPATURA LINGUISTICA PER GENERAZIONE A 3 FASI
    lingua_map = {
        "Italiano": ["Inizio", "Sviluppo", "Conclusione"],
        "English": ["Beginning", "Deep Development", "Conclusion"],
        "Deutsch": ["Einleitung", "Entwicklung", "Zusammenfassung"],
        "Français": ["Introduction", "Développement", "Conclusion"],
        "Español": ["Introducción", "Desarrollo profundo", "Conclusión"]
    }
    fasi = lingua_map.get(lingua, ["Part 1", "Part 2", "Part 3"])

    S_PROMPT = f"""
Sei un'autorità mondiale nel settore: {genere}. Scrivi esclusivamente in {lingua}.
Titolo: "{titolo_l}". Argomento: "{trama}".
REGOLE: Scrittura autoritaria, 2000+ parole per capitolo, fonti attendibili rielaborate, NO ripetizioni.
"""

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura & Modifica", "📖 3. Anteprima", "📑 4. Esporta"])

    # --- 1. INDICE ---
    with tab1:
        if st.button(f"Genera Indice in {lingua}"):
            st.session_state["indice_raw"] = chiedi_gpt(f"Crea un indice professionale e lungo per '{titolo_l}' in {lingua}.", f"Editor esperto.")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Modifica Indice", value=st.session_state.get("indice_raw", ""), height=300)
        if st.button("Sincronizza Capitoli"):
            sync_capitoli(); st.rerun()

    # --- 2. SCRITTURA & MODIFICA ---
    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        cap_sel = st.selectbox("Seleziona sezione:", opzioni)
        key_sez = f"txt_{cap_sel.lower().replace(' ', '_').replace('.', '')}"

        c_gen, c_edit = st.columns(2)
        with c_gen:
            if st.button(f"✨ SCRIVI: {cap_sel}"):
                with st.spinner(f"L'esperto sta scrivendo (Target 2000+ parole)..."):
                    testo_ia = ""
                    for f in fasi:
                        testo_ia += chiedi_gpt(f"Scrivi la parte '{f}' della sezione '{cap_sel}'. Sii estremamente prolisso e tecnico.", S_PROMPT) + "\n\n"
                    st.session_state[key_sez] = testo_ia

        with c_edit:
            istr_mod = st.text_input("Istruzione modifica IA", key=f"istr_{key_sez}")
            if st.button(f"🚀 RIELABORA SEZIONE"):
                if key_sez in st.session_state:
                    with st.spinner("Rielaborazione in corso..."):
                        p_riel = f"RISCRIVI E ESPANDI seguendo: {istr_mod}. Mantieni il target delle 2000 parole. Testo attuale:\n{st.session_state[key_sez]}"
                        st.session_state[key_sez] = chiedi_gpt(p_riel, S_PROMPT)
                        st.rerun()

        if key_sez in st.session_state:
            st.session_state[key_sez] = st.text_area("Editor Testuale:", value=st.session_state[key_sez], height=450, key=f"input_{key_sez}")

    # --- 3. ANTEPRIMA ---
    with tab3:
        st.subheader("📖 Vista Lettura")
        lista_f = ["txt_prefazione"] + [f"txt_{c.lower().replace(' ', '_').replace('.', '')}" for c in st.session_state.get("lista_capitoli", [])] + ["txt_ringraziamenti"]
        p_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: p_html += f"<h3 style='text-align:center;'>di {autore_l}</h3>"
        p_html += "<hr><br>"
        for s in lista_f:
            if s in st.session_state and st.session_state[s].strip():
                p_html += f"<h2>{s.replace('txt_', '').upper().replace('_', ' ')}</h2><p>{st.session_state[s].replace('\\n', '<br>')}</p><br>"
        st.markdown(p_html + "</div>", unsafe_allow_html=True)

    # --- 4. EXPORT ---
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
    st.info("👋 Inserisci Titolo e Trama a sinistra per iniziare.")
