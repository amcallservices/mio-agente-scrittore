import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. CONNESSIONE API (Utilizza i Secrets di Streamlit)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA E SIDEBAR ---
st.set_page_config(
    page_title="AI di Antonino - Scrittore Professionale", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS AVANZATO (SIDEBAR FISSA E UI PULITA) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display:none;}
    .stDeployButton {display:none;}

    /* Blocca la sidebar: rimuove tasto chiusura e freccia */
    [data-testid="collapsedControl"] { display: none !important; }
    
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        font-weight: bold;
        background-color: #f0f2f6;
    }
    
    .stTextArea textarea {
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CLASSI E FUNZIONI DI SUPPORTO ---

class PDF(FPDF):
    """Gestione PDF professionale con intestazione autore."""
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(20)

def pulisci_testo_ia(testo):
    """Rimuove chiacchiere dell'IA e mantiene solo il contenuto editoriale."""
    linee = testo.split('\n')
    linee_pulite = []
    # Tag proibiti in tutte le lingue supportate
    tag_proibiti = [
        "ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte",
        "here is", "sure", "i hope", "voilà", "aquí está", "hier ist", "iată", "вот", "这里是"
    ]
    for riga in linee:
        r_low = riga.strip().lower()
        if r_low and not any(r_low.startswith(tag) for tag in tag_proibiti):
            # Evita di ripetere il titolo del capitolo se è corto
            if not (r_low.startswith("capitolo") and len(r_low) < 60):
                linee_pulite.append(riga)
    
    testo_finale = '\n'.join(linee_pulite).strip()
    return re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", testo_finale).strip()

def chiedi_gpt(prompt, system_prompt):
    """Interfaccia OpenAI con pulizia automatica."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            temperature=0.7
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore API: {str(e)}"

def sync_capitoli():
    """Analizza l'indice dinamico per aggiornare i menu di scrittura."""
    testo_indice = st.session_state.get('indice', '')
    # Trova tutti i riferimenti numerici ai capitoli
    matches = re.findall(r'(?i)(?:Capitolo|Cap\.)\s*(\d+)', testo_indice)
    if matches:
        nums = [int(n) for n in matches]
        max_c = max(nums)
        st.session_state['lista_capitoli'] = [f"Capitolo {i}" for i in range(1, max_c + 1)]
    else:
        st.session_state['lista_capitoli'] = ["Capitolo 1"]

def reset_app():
    """Pulisce tutto e ricomincia."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- SIDEBAR (FISSA E COMPLETA) ---
with st.sidebar:
    st.title("✍️ AI Studio Antonino")
    st.subheader("Impostazioni Opera")
    
    titolo_l = st.text_input("Titolo del Libro", placeholder="Inserisci titolo...")
    autore_l = st.text_input("Nome Autore", placeholder="Inserisci nome...")
    
    # TUTTE LE LINGUE RICHIESTE
    lingua_l = st.selectbox("Lingua di Scrittura", [
        "Italiano", "English", "Deutsch", "Français", 
        "Español", "Română", "Русский", "中文"
    ])
    
    # TUTTE LE TIPOLOGIE (MANUALE TECNICO INCLUSO)
    genere_l = st.selectbox("Genere / Tipologia", [
        "Manuale Tecnico (Pratico/Divulgativo)",
        "Manuale Psicologico", 
        "Thriller Psicologico", 
        "Saggio Psicologico",
        "Motivazionale", 
        "Noir", 
        "Thriller", 
        "Fantasy", 
        "Romanzo Storico", 
        "Romanzo Rosa"
    ])
    
    trama_l = st.text_area("Trama o Argomento dettagliato", height=150)
    
    st.markdown("---")
    if st.button("🔄 RESET COMPLETO"):
        reset_app()

# --- LOGICA APPLICATIVA ---
if trama_l:
    # Prompt di sistema per garantire coerenza e stile
    S_PROMPT = f"Sei un Ghostwriter esperto in {genere_l}. Scrivi in {lingua_l}. REGOLE: Solo testo narrativo/tecnico. NO saluti. NO titoli capitolo interni. Flusso continuo."

    # TAB DI NAVIGAZIONE (Tutte le funzioni richieste)
    tab_ind, tab_scr, tab_mod, tab_esp = st.tabs([
        "📊 1. Struttura Indice", 
        "✍️ 2. Scrittura Capitoli", 
        "📝 3. Modifica & Revisione", 
        "📑 4. Esportazione File"
    ])

    # --- TAB 1: INDICE (Editabile e Sincronizzato) ---
    with tab_ind:
        st.subheader("Definizione dell'Indice")
        if st.button("Genera Indice Ottimizzato con AI"):
            with st.spinner("Creazione struttura..."):
                p_ind = f"Crea un indice professionale per '{titolo_l}'. Trama: {trama_l}. Elenca i capitoli come 'Capitolo X: Titolo'."
                st.session_state['indice'] = chiedi_gpt(p_ind, "Sei un Editor esperto.")
                sync_capitoli()

        if 'indice' not in st.session_state:
            st.session_state['indice'] = "Capitolo 1: Introduzione"
        
        # Area testo editabile che aggiorna i capitoli
        st.session_state['indice'] = st.text_area("Modifica manualmente l'indice (scrivi 'Capitolo X' per aggiungere sezioni):", 
                                                value=st.session_state['indice'], height=300)
        
        if st.button("🔄 Aggiorna Menu Capitoli"):
            sync_capitoli()
            st.rerun()

    # Inizializzazione lista capitoli
    if 'lista_capitoli' not in st.session_state:
        sync_capitoli()

    # --- TAB 2: SCRITTURA (Coerenza Narrativa) ---
    with tab_scr:
        st.subheader("Generazione Contenuti")
        opzioni_s = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sezione_s = st.selectbox("Cosa vuoi scrivere?", opzioni_s)
        chiave_s = sezione_s.lower().replace(" ", "_")
        
        if st.button(f"Scrivi {sezione_s}"):
            with st.spinner(f"L'IA sta elaborando {sezione_s}..."):
                # Raccolta memoria per coerenza
                memoria_l = ""
                for k in ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']]:
                    if k in st.session_state:
                        memoria_l += f"RIASSUNTO {k.upper()}: {st.session_state[k][:400]}...\n\n"
                
                testo_sez = ""
                # Generazione in tre fasi per profondità
                for fase in ["Incipit", "Sviluppo", "Conclusione"]:
                    p_scr = f"Memoria: {memoria_l}\n\nScrivi la sezione {sezione_s} (Fase: {fase}). Trama: {trama_l}"
                    testo_sez += chiedi_gpt(p_scr, S_PROMPT) + "\n\n"
                st.session_state[chiave_s] = testo_sez
        
        if chiave_s in st.session_state:
            st.session_state[chiave_s] = st.text_area("Testo (puoi scrivere anche qui):", 
                                                    value=st.session_state[chiave_s], height=450, key=f"txt_{chiave_s}")

    # --- TAB 3: MODIFICA (Stabile e con Buffer) ---
    with tab_mod:
        st.subheader("Revisione Editoriale")
        sezione_m = st.selectbox("Seleziona sezione da migliorare:", opzioni_s)
        chiave_m = sezione_m.lower().replace(" ", "_")
        
        if chiave_m in st.session_state:
            # Buffer di stabilità
            testo_attuale = st.text_area("Contenuto attuale:", value=st.session_state[chiave_m], height=350, key=f"mod_{chiave_m}")
            istruzione_m = st.text_input("Cosa vuoi cambiare? (es. 'Rendilo più professionale', 'Aggiungi un dialogo')")
            
            if st.button("Applica Modifica con IA"):
                with st.spinner("Riscrivendo..."):
                    st.session_state[chiave_m] = testo_attuale # Salva manuale
                    p_mod = f"Modifica il seguente testo seguendo questa istruzione: {istruzione_m}\n\nTesto:\n{testo_attuale}"
                    nuovo_t = chiedi_gpt(p_mod, S_PROMPT + " Agisci come Editor Senior.")
                    st.session_state[chiave_m] = nuovo_t
                    st.success("Testo aggiornato!")
                    st.rerun()
        else:
            st.info("Genera prima il testo nella scheda 'Scrittura'.")

    # --- TAB 4: ESPORTAZIONE (PDF + WORD) ---
    with tab_esp:
        st.subheader("Scarica il tuo Libro")
        lista_f = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        
        col_pdf, col_word = st.columns(2)
        
        with col_pdf:
            if st.button("Esporta in PDF"):
                with st.spinner("Creazione PDF..."):
                    pdf = PDF(autore_l if autore_l else "Autore"); pdf.set_auto_page_break(True, 15); pdf.add_page()
                    # Pagina Titolo
                    pdf.set_font("Arial", "B", 35); pdf.ln(80)
                    pdf.cell(0, 20, titolo_l.upper() if titolo_l else "TITOLO LIBRO", 0, 1, "C")
                    pdf.set_font("Arial", "", 20)
                    pdf.cell(0, 20, f"di {autore_l}", 0, 1, "C")
                    
                    for sez in lista_f:
                        if sez in st.session_state:
                            pdf.add_page()
                            pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, sez.upper().replace("_", " "), 0, 1, "L")
                            pdf.ln(10); pdf.set_font("Arial", "", 12)
                            txt_pdf = st.session_state[sez].encode('latin-1', 'replace').decode('latin-1')
                            pdf.multi_cell(0, 8, txt_pdf)
                    
                    st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")

        with col_word:
            if st.button("Esporta in WORD"):
                with st.spinner("Creazione Word..."):
                    doc = Document()
                    doc.add_heading(titolo_l if titolo_l else "Libro", 0)
                    doc.add_paragraph(f"Autore: {autore_l}")
                    
                    for sez in lista_f:
                        if sez in st.session_state:
                            doc.add_page_break()
                            doc.add_heading(sez.upper().replace("_", " "), level=1)
                            doc.add_paragraph(st.session_state[sez])
                    
                    buf_w = BytesIO()
                    doc.save(buf_w); buf_w.seek(0)
                    st.download_button("📥 Scarica WORD", buf_w, file_name=f"{titolo_l}.docx")
