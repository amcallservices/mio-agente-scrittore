import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. CONNESSIONE API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA E SIDEBAR ---
st.set_page_config(
    page_title="AI di Antonino - Crea il tuo Ebook", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS AVANZATO (PULSANTI VISIBILI E SIDEBAR FISSA) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display:none;}
    .stDeployButton {display:none;}
    [data-testid="collapsedControl"] { display: none !important; }
    
    /* Blocca Sidebar */
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
        background-color: #f8f9fa;
    }

    /* Contenitore principale */
    .block-container { padding-top: 0rem; padding-bottom: 0rem; }

    /* --- STILE PULSANTI ALTA VISIBILITÀ --- */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        font-weight: bold;
        font-size: 18px !important;
        background-color: #007BFF !important; /* Blu Acceso */
        color: white !important;
        border: none;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0056b3 !important; /* Blu scuro al passaggio */
        transform: translateY(-2px);
        box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.2);
    }

    /* Stile aree di testo */
    .stTextArea textarea { 
        font-size: 16px !important; 
        line-height: 1.6 !important;
        border-radius: 10px;
    }
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
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte", "here is", "sure", "voilà", "iată", "вот", "这里是"]
    for riga in linee:
        r_low = riga.strip().lower()
        if r_low and not any(r_low.startswith(tag) for tag in tag_proibiti):
            if not (r_low.startswith("capitolo") and len(r_low) < 60):
                linee_pulite.append(riga)
    testo_finale = '\n'.join(linee_pulite).strip()
    return re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", testo_finale).strip()

def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            temperature=0.7
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore API: {str(e)}"

def sync_capitoli_dettagliati():
    """Sincronizza titoli e argomenti dall'indice alla scrittura."""
    testo_indice = st.session_state.get('indice', '')
    linee = testo_indice.split('\n')
    mappa_capitoli = {}
    for linea in linee:
        match = re.search(r'(?i)(Capitolo\s*\d+)', linea)
        if match:
            chiave = match.group(1).title()
            argomento = linea.replace(match.group(0), "").strip(": -")
            mappa_capitoli[chiave] = argomento if argomento else "Approfondimento del tema"
            
    if mappa_capitoli:
        st.session_state['mappa_capitoli'] = mappa_capitoli
        st.session_state['lista_capitoli'] = list(mappa_capitoli.keys())
    else:
        st.session_state['lista_capitoli'] = ["Capitolo 1"]
        st.session_state['mappa_capitoli'] = {"Capitolo 1": "Introduzione"}

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- SIDEBAR (CONFIGURAZIONE) ---
with st.sidebar:
    st.title("✍️ AI Studio Antonino")
    titolo_l = st.text_input("Titolo del Libro")
    autore_l = st.text_input("Nome Autore")
    lingua_l = st.selectbox("Lingua / Language", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere_l = st.selectbox("Genere / Tipologia", ["Manuale Tecnico (Pratico/Divulgativo)", "Manuale Psicologico", "Thriller Psicologico", "Saggio", "Motivazionale", "Noir", "Thriller", "Fantasy", "Romanzo Storico", "Romanzo Rosa"])
    trama_l = st.text_area("Trama o Argomento principale", height=150)
    st.markdown("---")
    if st.button("🔄 RESET COMPLETO"):
        reset_app()

if trama_l:
    S_PROMPT = f"Sei un Ghostwriter esperto in {genere_l}. Scrivi in {lingua_l}. REGOLE: Attieniti rigorosamente all'argomento del capitolo."

    tab_ind, tab_scr, tab_mod, tab_esp = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "📝 3. Modifica", "📑 4. Esporta"])

    # --- TAB 1: INDICE ---
    with tab_ind:
        st.subheader("Pianificazione Struttura")
        if st.button("GENERA INDICE PROFESSIONALE"):
            p_ind = f"Crea un indice dettagliato per '{titolo_l}'. Trama: {trama_l}. Usa 'Capitolo X: Titolo - Descrizione'."
            st.session_state['indice'] = chiedi_gpt(p_ind, "Sei un Editor esperto.")
            sync_capitoli_dettagliati()

        if 'indice' not in st.session_state:
            st.session_state['indice'] = "Capitolo 1: Introduzione"
        
        st.session_state['indice'] = st.text_area("Modifica Indice (Sincronizza i capitoli con la scrittura):", value=st.session_state['indice'], height=300)
        
        if st.button("🔄 AGGIORNA E SINCRONIZZA ARGOMENTI"):
            sync_capitoli_dettagliati()
            st.rerun()

    if 'lista_capitoli' not in st.session_state:
        sync_capitoli_dettagliati()

    # --- TAB 2: SCRITTURA ---
    with tab_scr:
        st.subheader("Scrittura Capitoli")
        opzioni_s = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sezione_s = st.selectbox("Cosa vuoi scrivere?", opzioni_s)
        chiave_s = sezione_s.lower().replace(" ", "_")
        argomento_specifico = st.session_state.get('mappa_capitoli', {}).get(sezione_s, "")

        if st.button(f"AVVIA SCRITTURA: {sezione_s.upper()}"):
            with st.spinner(f"Scrittura in corso basata sull'indice..."):
                testo_sez = ""
                for fase in ["Inizio", "Sviluppo centrale", "Conclusione"]:
                    p_scr = f"Trama: {trama_l}\nArgomento Specifico: {argomento_specifico}\n\nScrivi {sezione_s} ({fase})."
                    testo_sez += chiedi_gpt(p_scr, S_PROMPT) + "\n\n"
                st.session_state[chiave_s] = testo_sez
        
        if chiave_s in st.session_state:
            st.session_state[chiave_s] = st.text_area("Contenuto Generato:", value=st.session_state[chiave_s], height=450, key=f"txt_{chiave_s}")

    # --- TAB 3: MODIFICA ---
    with tab_mod:
        st.subheader("Editor Assistito")
        sezione_m = st.selectbox("Seleziona da migliorare:", opzioni_s)
        chiave_m = sezione_m.lower().replace(" ", "_")
        if chiave_m in st.session_state:
            testo_attuale = st.text_area("Testo attuale:", value=st.session_state[chiave_m], height=350, key=f"mod_{chiave_m}")
            istruzione_m = st.text_input("Quale modifica vuoi fare?")
            if st.button("APPLICA MODIFICA IA"):
                st.session_state[chiave_m] = testo_attuale
                nuovo_t = chiedi_gpt(f"Modifica: {istruzione_m}\nTesto:\n{testo_attuale}", S_PROMPT + " Editor Senior.")
                st.session_state[chiave_m] = nuovo_t
                st.rerun()
        else: st.info("Genera prima il testo.")

    # --- TAB 4: ESPORTAZIONE ---
    with tab_esp:
        st.subheader("Download Finale")
        lista_f = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        c1, c2 = st.columns(2)
        with c1:
            if st.button("SCARICA IN PDF"):
                pdf = PDF(autore_l); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                pdf.set_font("Arial", "", 20); pdf.cell(0, 20, f"di {autore_l}", 0, 1, "C")
                for sez in lista_f:
                    if sez in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, sez.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 12)
                        txt_pdf = st.session_state[sez].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 8, txt_pdf)
                st.download_button("📥 SALVA PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        with c2:
            if st.button("SCARICA IN WORD"):
                doc = Document(); doc.add_heading(titolo_l, 0); doc.add_paragraph(f"Autore: {autore_l}")
                for sez in lista_f:
                    if sez in st.session_state:
                        doc.add_page_break(); doc.add_heading(sez.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[sez])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 SALVA WORD", buf_w, file_name=f"{titolo_l}.docx")
