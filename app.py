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
    page_title="AI di Antonino: Crea il tuo Ebook Scientifico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS (UI PROFESSIONALE) ---
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
    color: #1E1E1E;
    text-align: center;
    padding: 20px;
    background-color: #f0f4f8;
    border-radius: 15px;
    margin-bottom: 25px;
    border: 1px solid #d1d9e6;
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
}

.stButton>button {
    width: 100%;
    border-radius: 8px;
    height: 3.5em;
    font-weight: bold;
    background-color: #0056b3 !important;
    color: white !important;
    transition: all 0.3s;
    border: none;
}

.stButton>button:hover {
    background-color: #003d80 !important;
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
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(10)

# --- FUNZIONI ---
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    mappa = {}
    linee = testo.split('\n')
    for l in linee:
        match = re.search(r'(?i)(Capitolo|Chapter|Kapitel|Capítulo)\s*\d+|^\d+\.', l)
        if match:
            cap_key = match.group(0).strip().title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Analisi Scientifica"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- INTERFACCIA ---
st.markdown('<div class="custom-title">AI di Antonino: Ebook & Quiz Scientifico</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Editor & Quiz Setup")
    titolo_l = st.text_input("Titolo dell'Opera")
    autore_l = st.text_input("Nome Autore")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español"])
    genere = st.selectbox("Genere", ["Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", "Business", "Saggio Breve"])
    modalita = st.selectbox("Stile di Scrittura", ["Standard", "Professionale Accademico"])
    trama = st.text_area("Argomento Scientifico Centrale", height=150)
    
    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if titolo_l and trama:
    livello = "estremamente tecnico, rigoroso e accademico" if modalita == "Professionale Accademico" else "chiaro e divulgativo"
    
    S_PROMPT = f"""
Sei un'autorità scientifica mondiale nel settore: {genere}. Scrivi in {lingua}.
Titolo: "{titolo_l}". Argomento: "{trama}".
STILE: {livello}.
REGOLE: Capitoli da 2000+ parole, rigore scientifico, NO ripetizioni, cita concetti basati su evidenze.
"""

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura & Quiz", "📖 3. Anteprima", "📑 4. Esporta"])

    # --- 1. INDICE ---
    with tab1:
        if st.button("Genera Indice Scientifico"):
            st.session_state["indice_raw"] = chiedi_gpt(f"Crea un indice per un saggio scientifico su '{titolo_l}' in {lingua}.", "Editor Scientifico.")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Modifica Indice", value=st.session_state.get("indice_raw", ""), height=300)
        if st.button("Sincronizza"): sync_capitoli(); st.rerun()

    # --- 2. SCRITTURA & QUIZ ---
    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        cap_sel = st.selectbox("Seleziona sezione:", opzioni)
        key_sez = f"txt_{cap_sel.replace(' ', '_')}"
        key_quiz = f"quiz_{cap_sel.replace(' ', '_')}"

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"✨ SCRIVI: {cap_sel}"):
                with st.spinner("Scrittura scientifica in corso..."):
                    testo_p1 = chiedi_gpt(f"Scrivi la prima parte dettagliata di '{cap_sel}'.", S_PROMPT)
                    testo_p2 = chiedi_gpt(f"Continua e approfondisci '{cap_sel}' con dati e analisi.", S_PROMPT)
                    st.session_state[key_sez] = testo_p1 + "\n\n" + testo_p2

        with col2:
            istr = st.text_input("Istruzione modifica", key=f"istr_{key_sez}")
            if st.button(f"🚀 RIELABORA"):
                if key_sez in st.session_state:
                    st.session_state[key_sez] = chiedi_gpt(f"Rielabora scientificamente: {istr}. Testo:\n{st.session_state[key_sez]}", S_PROMPT)
                    st.rerun()

        with col3:
            if st.button(f"🧠 GENERA QUIZ"):
                if key_sez in st.session_state:
                    with st.spinner("Generazione quiz scientifico..."):
                        prompt_quiz = f"Basandoti sul seguente testo, crea 10 domande a risposta multipla con 4 opzioni ciascuna. Indica la risposta corretta.\n\nTesto:\n{st.session_state[key_sez]}"
                        st.session_state[key_quiz] = chiedi_gpt(prompt_quiz, "Esperto in valutazione accademica.")
                        st.rerun()

        st.session_state[key_sez] = st.text_area("Testo Capitolo:", value=st.session_state.get(key_sez, ""), height=400)
        
        if key_quiz in st.session_state:
            st.markdown("---")
            st.subheader("📝 Quiz del Capitolo")
            st.info(st.session_state[key_quiz])

    # --- 3. ANTEPRIMA ---
    with tab3:
        p_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: p_html += f"<h3 style='text-align:center;'>di {autore_l}</h3>"
        p_html += "<hr><br>"
        for s in opzioni:
            s_key = f"txt_{s.replace(' ', '_')}"
            if s_key in st.session_state:
                p_html += f"<h2>{s.upper()}</h2><p>{st.session_state[s_key].replace('\\n', '<br>')}</p><br>"
        st.markdown(p_html + "</div>", unsafe_allow_html=True)

    # --- 4. EXPORT ---
    with tab4:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Download PDF"):
                pdf = PDF(autore_l); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in opzioni:
                    s_key = f"txt_{s.replace(' ', '_')}"
                    if s_key in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper(), 0, 1)
                        pdf.ln(10); pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 9, st.session_state[s_key].encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        with c2:
            if st.button("Download Word"):
                doc = Document(); doc.add_heading(titolo_l, 0)
                for s in opzioni:
                    s_key = f"txt_{s.replace(' ', '_')}"
                    if s_key in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper(), level=1); doc.add_paragraph(st.session_state[s_key])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 Word", buf_w, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Inserisci Titolo e Argomento Scientifico per iniziare.")
