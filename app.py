import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. INIZIALIZZAZIONE API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE AMBIENTE ---
st.set_page_config(
    page_title="AI di Antonino - Scrittore Professionale", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS PER BLOCCO SIDEBAR E UI (OTTIMIZZATO PER SCRITTORE.SITE) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display:none;}
    .stDeployButton {display:none;}
    [data-testid="collapsedControl"] {display: none !important;}
    section[data-testid="stSidebar"] {min-width: 350px !important; max-width: 350px !important;}
    .block-container {padding-top: 0rem; padding-bottom: 0rem;}
    .stButton>button {width: 100%; border-radius: 12px; height: 3.8em; font-weight: bold;}
    .stTextArea textarea {font-size: 16px !important; line-height: 1.6 !important;}
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---

class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(20)

def pulisci_testo_ia(testo):
    linee = testo.split('\n')
    linee_pulite = []
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte", "capitolo"]
    for riga in linee:
        r_low = riga.strip().lower()
        if r_low and not any(r_low.startswith(tag) for tag in tag_proibiti):
            linee_pulite.append(riga)
        elif r_low.startswith("capitolo") and (":" in r_low or "-" in r_low):
            # Mantieni solo se sembra un titolo lungo, altrimenti scarta per evitare ripetizioni
            if len(r_low) > 60:
                linee_pulite.append(riga)
    return '\n'.join(linee_pulite).strip()

def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            temperature=0.7
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore: {str(e)}"

def sync_capitoli():
    """Estrae i capitoli dall'indice e aggiorna la lista in session_state."""
    indice_testo = st.session_state.get('indice', '')
    matches = re.findall(r'(?i)(?:Capitolo|Cap\.)\s*(\d+)', indice_testo)
    if matches:
        max_c = max([int(n) for n in matches])
        st.session_state['lista_capitoli'] = [f"Capitolo {i}" for i in range(1, max_c + 1)]
    else:
        st.session_state['lista_capitoli'] = ["Capitolo 1"]

def reset_totale():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.title("✍️ Studio Editoriale")
    titolo_libro = st.text_input("Titolo dell'opera")
    nome_autore = st.text_input("Nome Autore")
    lingua_scelta = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română"])
    genere_libro = st.selectbox("Genere", ["Manuale Psicologico", "Thriller", "Saggio", "Motivazionale", "Romanzo"])
    trama_base = st.text_area("Trama", height=150)
    st.markdown("---")
    if st.button("🔄 RESET TOTALE"):
        reset_totale()

if trama_base:
    GHOSTWRITER_PROMPT = f"Sei un Ghostwriter esperto in {genere_libro}. Scrivi in {lingua_scelta}. Solo testo narrativo. NO titoli."

    tab_ind, tab_scr, tab_mod, tab_esp = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "📝 3. Modifica", "📑 4. Esporta"])

    # --- 1. TAB INDICE ---
    with tab_ind:
        st.subheader("Pianificazione Struttura")
        if st.button("Genera Indice Ottimizzato"):
            st.session_state['indice'] = chiedi_gpt(f"Crea indice per '{titolo_libro}'. Trama: {trama_base}. Capitoli numerati.", "Sei un Editor.")
            sync_capitoli()

        if 'indice' not in st.session_state:
            st.session_state['indice'] = "Capitolo 1: Introduzione"
        
        testo_ind = st.text_area("Modifica Indice (cambia i numeri per aggiornare i menu):", value=st.session_state['indice'], height=300)
        if testo_ind != st.session_state['indice']:
            st.session_state['indice'] = testo_ind
            sync_capitoli()

    if 'lista_capitoli' not in st.session_state:
        sync_capitoli()

    # --- 2. TAB SCRITTURA ---
    with tab_scr:
        st.subheader("Stesura Contenuti")
        opzioni = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sez_scelta = st.selectbox("Cosa vuoi scrivere?", opzioni)
        chiave = sez_scelta.lower().replace(" ", "_")
        
        if st.button(f"Genera {sez_scelta}"):
            with st.spinner("Scrittura..."):
                testo = ""
                for f in ["Inizio", "Sviluppo", "Fine"]:
                    testo += chiedi_gpt(f"Scrivi {sez_scelta} ({f}). Trama: {trama_base}", GHOSTWRITER_PROMPT) + "\n\n"
                st.session_state[chiave] = testo
        
        if chiave in st.session_state:
            st.session_state[chiave] = st.text_area("Testo generato:", value=st.session_state[chiave], height=400, key=f"s_{chiave}")

    # --- 3. TAB MODIFICA ---
    with tab_mod:
        st.subheader("Revisione assistita")
        sez_mod = st.selectbox("Seleziona sezione da rivedere:", ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"])
        k_mod = sez_mod.lower().replace(" ", "_")
        
        if k_mod in st.session_state:
            testo_area = st.text_area("Testo attuale:", value=st.session_state[k_mod], height=300, key=f"m_{k_mod}")
            istr = st.text_input("Istruzione per l'IA:")
            if st.button("Esegui Modifica"):
                st.session_state[k_mod] = testo_area
                st.session_state[k_mod] = chiedi_gpt(f"Istruzione: {istr}\nTesto:\n{testo_area}", GHOSTWRITER_PROMPT)
                st.rerun()
        else: st.info("Genera prima la sezione.")

    # --- 4. TAB ESPORTAZIONE (PDF + WORD) ---
    with tab_esp:
        st.subheader("Download Finale")
        lista_final = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Esporta PDF"):
                pdf = PDF(nome_autore); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_libro.upper(), 0, 1, "C")
                pdf.set_font("Arial", "", 18); pdf.cell(0, 20, f"di {nome_autore}", 0, 1, "C")
                for s in lista_final:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 11)
                        pdf.multi_cell(0, 7, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_libro}.pdf")

        with col2:
            if st.button("Esporta WORD"):
                doc = Document()
                doc.add_heading(titolo_libro, 0)
                doc.add_paragraph(f"Autore: {nome_autore}")
                for s in lista_final:
                    if s in st.session_state:
                        doc.add_page_break()
                        doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.download_button("📥 Scarica WORD", buf, file_name=f"{titolo_libro}.docx")
