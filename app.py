import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- API ---
# Assicurati che la chiave sia configurata correttamente in .streamlit/secrets.toml
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
        # CORREZIONE: Utilizzo di gpt-4o (modello esistente)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore di connessione: {str(e)}"

def conta_parole(testo):
    if not testo: return 0
    return len(testo.split())

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    mappa = {}
    for riga in testo.split("\n"):
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.)', riga)
        if match:
            key = match.group(0).strip().title()
            descr = riga.replace(match.group(0), "").strip(": -")
            mappa[key] = descr if descr else "Approfondimento tematico"
    if mappa:
        st.session_state["mappa_capitoli"] = mappa
        st.session_state["lista_capitoli"] = list(mappa.keys())

# --- UI HEADER ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")

    titolo_l = st.text_input("Titolo del Libro", placeholder="Inserisci il titolo...")
    autore_l = st.text_input("Nome Autore (opzionale)", value="")
    
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere", ["Manuale Tecnico", "Manuale Psicologico", "Saggio", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    
    trama = st.text_area("Trama e Argomento Centrale", height=150)
    modalita = st.selectbox("Modalità di scrittura", ["Standard", "Professionale"])

    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- CORE LOGIC ---
if titolo_l and trama:
    livello = "estremamente dettagliato e professionale" if modalita == "Professionale" else "chiaro e semplice"
    S_PROMPT = f"Sei un Ghostwriter esperto in {genere}. Scrivi in {lingua}. Focus: {titolo_l}. Trama: {trama}. Regole: stile {livello}, evita ripetizioni, fluente."

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "🛠️ 3. Rielaborazione", "📑 4. Esportazione"])

    # --- TAB 1: INDICE ---
    with tab1:
        if st.button("Genera Indice Automatico"):
            st.session_state["indice_raw"] = chiedi_gpt(f"Crea un indice per '{titolo_l}' basato su: {trama}", "Editor esperto.")
            sync_capitoli()

        st.session_state["indice_raw"] = st.text_area("Revisiona l'indice (Modifica manuale permessa):", 
                                                    value=st.session_state.get("indice_raw", "Capitolo 1: Introduzione"), 
                                                    height=300)
        
        if st.button("Sincronizza Capitoli"):
            sync_capitoli()
            st.success("Sincronizzato!")

    # --- TAB 2: SCRITTURA ---
    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        capitolo_sel = st.selectbox("Seleziona sezione", opzioni)
        key_sez = f"txt_{capitolo_sel.lower().replace(' ', '_').replace('.', '')}"

        if st.button(f"Genera contenuto per {capitolo_sel}"):
            with st.spinner("L'IA sta scrivendo..."):
                arg = st.session_state.get("mappa_capitoli", {}).get(capitolo_sel, "")
                # Generazione in un unico blocco coerente
                testo_ia = chiedi_gpt(f"Scrivi la sezione '{capitolo_sel}'. Argomento: {arg}.", S_PROMPT)
                st.session_state[key_sez] = testo_ia

        # EDIT MANUALE: Il testo scritto qui viene salvato direttamente
        valore_corrente = st.session_state.get(key_sez, "")
        nuovo_testo = st.text_area("Contenuto della sezione (Modifica manuale):", value=valore_corrente, height=450, key=f"area_{key_sez}")
        st.session_state[key_sez] = nuovo_testo
        
        st.info(f"Parole: {conta_parole(st.session_state[key_sez])}")

    # --- TAB 3: RIELABORAZIONE ---
    with tab3:
        st.subheader("🛠️ Rielaborazione Totale")
        cap_da_rifare = st.selectbox("Sezione da rielaborare", opzioni, key="rifare_sel")
        key_rifare = f"txt_{cap_da_rifare.lower().replace(' ', '_').replace('.', '')}"

        if key_rifare in st.session_state and st.session_state[key_rifare]:
            if f"ver_{key_rifare}" not in st.session_state: st.session_state[f"ver_{key_rifare}"] = 0
            
            istr = st.text_area("Istruzioni (es. 'Passa dal Voi al Tu'):", placeholder="Cosa vuoi cambiare?")
            
            if st.button("🚀 APPLICA RIELABORAZIONE"):
                with st.spinner("Riscrivendo..."):
                    # Forziamo una riscrittura integrale
                    p_riel = f"RISCRIVI COMPLETAMENTE il testo seguente seguendo questa istruzione: {istr}.\n\nTesto attuale:\n{st.session_state[key_rifare]}"
                    nuovo_t = chiedi_gpt(p_riel, S_PROMPT + " Editor Senior.")
                    st.session_state[key_rifare] = nuovo_t
                    st.session_state[f"ver_{key_rifare}"] += 1 # Reset widget
                    st.rerun()
        else:
            st.info("Genera prima del testo nella scheda 'Scrittura'.")

    # --- TAB 4: EXPORT ---
    with tab4:
        col1, col2 = st.columns(2)
        sezioni_finali = ["txt_prefazione"] + [f"txt_{c.lower().replace(' ', '_').replace('.', '')}" for c in st.session_state.get("lista_capitoli", [])] + ["txt_ringraziamenti"]
        
        with col1:
            if st.button("Esporta PDF"):
                pdf = PDF(autore_l)
                pdf.set_auto_page_break(True, 15)
                pdf.add_page()
                pdf.set_font("Arial", "B", 30)
                pdf.ln(80)
                pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                if autore_l:
                    pdf.set_font("Arial", "", 18); pdf.cell(0, 20, f"di {autore_l}", 0, 1, "C")
                
                for s_key in sezioni_finali:
                    if s_key in st.session_state and st.session_state[s_key]:
                        pdf.add_page()
                        pdf.set_font("Arial", "B", 18)
                        pdf.cell(0, 10, s_key.replace("txt_", "").upper().replace("_", " "), 0, 1)
                        pdf.ln(10)
                        pdf.set_font("Arial", "", 12)
                        # Gestione codifica latin-1 per caratteri speciali
                        txt_pdf = st.session_state[s_key].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 8, txt_pdf)
                st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")

        with col2:
            if st.button("Esporta Word"):
                doc = Document()
                doc.add_heading(titolo_l, 0)
                if autore_l: doc.add_paragraph(f"Autore: {autore_l}")
                for s_key in sezioni_finali:
                    if s_key in st.session_state and st.session_state[s_key]:
                        doc.add_page_break()
                        doc.add_heading(s_key.replace("txt_", "").upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s_key])
                buf = BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.download_button("📥 Scarica Word", buf, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Inserisci Titolo e Trama nella barra laterale per sbloccare lo studio editoriale.")
