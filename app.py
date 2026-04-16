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

# --- CSS (UI PULITA E ANTEPRIMA) ---
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

.preview-box {
    background-color: white;
    padding: 40px;
    border: 1px solid #ddd;
    border-radius: 10px;
    height: 600px;
    overflow-y: scroll;
    font-family: 'Georgia', serif;
    line-height: 1.6;
    color: #333;
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
            self.cell(0, 10, f"Author: {self.autore}", 0, 0, 'C')
            self.ln(10)

# --- FUNZIONI ---
def pulisci_testo_ia(testo):
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "here is", "sure", "voilà"]
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
            mappa[cap_key] = descr if descr else "Topic analysis"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- UI HEADER ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Setup")
    titolo_l = st.text_input("Book Title")
    autore_l = st.text_input("Author Name", value="")
    lingua = st.selectbox("Language", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genre/Field", ["Manuale Tecnico", "Saggio Scientifico", "Manuale Psicologico", "Business & Marketing", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    trama = st.text_area("Plot or Main Topic", height=150)
    
    if st.button("🔄 RESET PROJECT"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if titolo_l and trama:
    # DEFINIZIONE DELLE FASI IN BASE ALLA LINGUA
    lingua_map = {
        "Italiano": ["Inizio", "Sviluppo", "Fine"],
        "English": ["Beginning", "Development", "Conclusion"],
        "Deutsch": ["Anfang", "Entwicklung", "Ende"],
        "Français": ["Début", "Développement", "Fin"],
        "Español": ["Inicio", "Desarrollo", "Fin"],
        "Română": ["Început", "Dezvoltare", "Sfârșit"],
        "Русский": ["Начало", "Развитие", "Конец"],
        "中文": ["开始", "发展", "结束"]
    }
    fasi = lingua_map.get(lingua, ["Beginning", "Development", "Conclusion"])

    S_PROMPT = f"""
You are a world-leading expert in the field of {genere}. 
MANDATORY: You must write EVERYTHING exclusively in {lingua}.
Book Title: "{titolo_l}". Topic: "{trama}".

CRITICAL WRITING RULES:
1. LANGUAGE: Write 100% in {lingua}. Never use other languages.
2. LENGTH: Each chapter must be extremely detailed, deep, and long. Aim for at least 2000 words per section.
3. QUALITY: Highest expertise, use professional terminology of the chosen language, no repetitions.
4. CONTENT: Use subheadings, case studies, and extensive analysis to reach the word count.
"""

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Index", "✍️ 2. Write & Edit", "📖 3. Preview", "📑 4. Export"])

    # --- 1. INDICE ---
    with tab1:
        if st.button(f"Generate Index in {lingua}"):
            st.session_state["indice_raw"] = chiedi_gpt(f"Create a logical index for '{titolo_l}' based on: {trama}. Write in {lingua}.", f"Expert Editor in {lingua}")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Edit Index", value=st.session_state.get("indice_raw", ""), height=300)
        if st.button("Sync Chapters"):
            sync_capitoli()
            st.rerun()

    # --- 2. SCRITTURA E MODIFICA ---
    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = ["Preface/Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Acknowledgements/Ringraziamenti"]
        cap_sel = st.selectbox("Select section:", opzioni)
        key_sez = f"txt_{cap_sel.lower().replace(' ', '_').replace('.', '')}"

        col_g, col_r = st.columns([1, 1])
        with col_g:
            if st.button(f"✨ Generate {cap_sel} in {lingua}"):
                with st.spinner(f"Writing in {lingua} (Target: 2000 words)..."):
                    testo_ia = ""
                    for f in fasi:
                        testo_ia += chiedi_gpt(f"Write the part '{f}' of the section '{cap_sel}'. Expand as much as possible.", S_PROMPT) + "\n\n"
                    st.session_state[key_sez] = testo_ia

        with col_r:
            istr_mod = st.text_input("Edit instructions (e.g. 'Make it more technical')", key=f"istr_{key_sez}")
            if st.button(f"🚀 Rewrite with AI"):
                if key_sez in st.session_state:
                    with st.spinner("Expanding text..."):
                        p_riel = f"REWRITE COMPLETELY in {lingua} following this: {istr_mod}. Aim for maximum length. Current text:\n{st.session_state[key_sez]}"
                        st.session_state[key_sez] = chiedi_gpt(p_riel, S_PROMPT)
                        st.rerun()

        if key_sez in st.session_state:
            st.session_state[key_sez] = st.text_area("Manual Editor:", value=st.session_state[key_sez], height=450, key=f"input_{key_sez}")

    # --- 3. ANTEPRIMA ---
    with tab3:
        st.subheader("📖 Book Preview")
        lista_f = ["txt_preface/prefazione"] + [f"txt_{c.lower().replace(' ', '_').replace('.', '')}" for c in st.session_state.get("lista_capitoli", [])] + ["txt_acknowledgements/ringraziamenti"]
        anteprima_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: anteprima_html += f"<h3 style='text-align:center;'>by {autore_l}</h3>"
        anteprima_html += "<hr><br>"
        for s in lista_f:
            if s in st.session_state and st.session_state[s].strip():
                anteprima_html += f"<h2>{s.replace('txt_', '').upper().replace('_', ' ')}</h2><p>{st.session_state[s].replace('\\n', '<br>')}</p><br>"
        anteprima_html += "</div>"
        st.markdown(anteprima_html, unsafe_allow_html=True)

    # --- 4. EXPORT ---
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download PDF"):
                pdf = PDF(autore_l)
                pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in lista_f:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.replace("txt_", "").upper().replace("_", " "), 0, 1)
                        pdf.ln(10); pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
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
    st.info("👋 Setup Title and Topic to start.")
