import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. CONNESSIONE API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA ---
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
    """Filtra commenti IA e intestazioni inutili per mantenere il flusso logico."""
    linee = testo.split('\n')
    linee_pulite = []
    # Tag di cortesia e fasi in tutte le lingue richieste
    tag_proibiti = [
        "ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte",
        "here is", "sure", "i hope", "voilà", "aquí está", "hier ist", "iată", "вот", "这里是"
    ]
    for riga in linee:
        r_low = riga.strip().lower()
        if r_low and not any(r_low.startswith(tag) for tag in tag_proibiti):
            # Evita di ripetere "Capitolo X" all'interno del testo se l'IA lo aggiunge
            if not (r_low.startswith("capitolo") and len(r_low) < 60):
                linee_pulite.append(riga)
    
    testo_pulito = '\n'.join(linee_pulite).strip()
    return re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", testo_pulito).strip()

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
    """Sincronizzazione dinamica Indice -> Menu Scrittura."""
    indice_testo = st.session_state.get('indice', '')
    matches = re.findall(r'(?i)(?:Capitolo|Cap\.)\s*(\d+)', indice_testo)
    if matches:
        max_c = max([int(n) for n in numeri]) if 'numeri' in locals() else 0 # Fix sicurezza
        nums = [int(n) for n in matches]
        max_c = max(nums)
        st.session_state['lista_capitoli'] = [f"Capitolo {i}" for i in range(1, max_c + 1)]
    else:
        st.session_state['lista_capitoli'] = ["Capitolo 1"]

def reset_totale():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- SIDEBAR (FISSA E SEMPRE VISIBILE) ---
with st.sidebar:
    st.title("✍️ Studio Editoriale")
    titolo_libro = st.text_input("Titolo dell'opera")
    nome_autore = st.text_input("Nome Autore")
    
    # TUTTE LE LINGUE RICHIESTE INTEGRATE
    lingua_scelta = st.selectbox("Lingua / Language", [
        "Italiano", "English", "Deutsch", "Français", 
        "Español", "Română", "Русский", "中文"
    ])
    
    genere_libro = st.selectbox("Genere", [
        "Manuale Psicologico", "Thriller Psicologico", "Saggio", "Motivazionale", 
        "Noir", "Thriller", "Fantasy", "Romanzo Storico", "Romanzo Rosa"
    ])
    
    trama_base = st.text_area("Trama del libro", height=150)
    st.markdown("---")
    if st.button("🔄 RESET COMPLETO"):
        reset_totale()

if trama_base:
    # System prompt con istruzioni di coerenza e concatenazione logica
    GHOSTWRITER_PROMPT = f"Sei un Ghostwriter esperto in {genere_libro}. Scrivi in {lingua_scelta}. "
    GHOSTWRITER_PROMPT += "REGOLE: Solo testo narrativo/tecnico. NO saluti, NO commenti. "
    GHOSTWRITER_PROMPT += "COERENZA: Concatenazione logica totale con i capitoli precedenti."

    tab_ind, tab_scr, tab_mod, tab_esp = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "📝 3. Modifica", "📑 4. Esporta"])

    # --- 1. TAB INDICE (EDITABILE) ---
    with tab_ind:
        st.subheader("Pianificazione della Struttura")
        if st.button("Genera Indice Professionale"):
            prompt_i = f"Crea un indice editoriale per '{titolo_libro}'. Trama: {trama_base}. Usa 'Capitolo X: Titolo'."
            st.session_state['indice'] = chiedi_gpt(prompt_i, "Sei un Editor Senior.")
            sync_capitoli()

        if 'indice' not in st.session_state:
            st.session_state['indice'] = "Capitolo 1: Introduzione"
        
        # L'utente può modificare l'indice e i menu si aggiornano
        st.session_state['indice'] = st.text_area("Modifica Indice (Aggiungi 'Capitolo X' per nuovi menu):", 
                                                value=st.session_state['indice'], height=300)
        if st.button("🔄 Conferma Sincronizzazione"):
            sync_capitoli()
            st.rerun()

    if 'lista_capitoli' not in st.session_state:
        sync_capitoli()

    # --- 2. TAB SCRITTURA (COERENTE) ---
    with tab_scr:
        st.subheader("Stesura Capitoli")
        opzioni = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sez_scelta = st.selectbox("Seleziona sezione:", opzioni)
        chiave = sez_scelta.lower().replace(" ", "_")
        
        if st.button(f"Genera {sez_scelta}"):
            with st.spinner("L'IA sta scrivendo con coerenza logica..."):
                # Recupero memoria testi precedenti per concatenazione
                memoria = ""
                sez_scritte = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']]
                for s in sez_scritte:
                    if s in st.session_state:
                        memoria += f"RIASSUNTO {s.upper()}: {st.session_state[s][:500]}...\n\n"
                
                testo_finale = ""
                # Generazione in 3 fasi fuse insieme senza etichette
                for f in ["Inizio", "Sviluppo", "Conclusione"]:
                    p_scr = f"Memoria precedente:\n{memoria}\n\nScrivi {sez_scelta} (Fase: {f}). Trama: {trama_base}"
                    testo_finale += chiedi_gpt(p_scr, GHOSTWRITER_PROMPT) + "\n\n"
                st.session_state[chiave] = testo_finale
        
        if chiave in st.session_state:
            st.session_state[chiave] = st.text_area("Testo (modificabile):", value=st.session_state[chiave], height=400, key=f"s_{chiave}")

    # --- 3. TAB MODIFICA (STABILE) ---
    with tab_mod:
        st.subheader("Revisione Assistita")
        sez_mod = st.selectbox("Cosa vuoi modificare?", opzioni)
        k_mod = sez_mod.lower().replace(" ", "_")
        
        if k_mod in st.session_state:
            t_area = st.text_area("Contenuto attuale:", value=st.session_state[k_mod], height=350, key=f"m_{k_mod}")
            istr = st.text_input("Istruzione di modifica (es: 'Rendilo più cupo')")
            if st.button("Applica Ristrutturazione"):
                with st.spinner("Rielaborazione..."):
                    st.session_state[k_mod] = t_area # Salva buffer
                    nuovo = chiedi_gpt(f"Modifica questo testo seguendo: {istr}\n\nTesto:\n{t_area}", GHOSTWRITER_PROMPT + " Agisci come Senior Editor.")
                    st.session_state[k_mod] = nuovo
                    st.success("Modifica attuata!")
                    st.rerun()
        else: st.info("Genera prima la sezione.")

    # --- 4. TAB ESPORTAZIONE (PDF + WORD) ---
    with tab_esp:
        st.subheader("Esportazione Finale")
        lista_final = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Esporta in PDF"):
                pdf = PDF(nome_autore); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_libro.upper(), 0, 1, "C")
                pdf.set_font("Arial", "", 18); pdf.cell(0, 20, f"di {nome_autore}", 0, 1, "C")
                for s in lista_final:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 11)
                        # Codifica per caratteri speciali
                        txt_pdf = st.session_state[s].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 7, txt_pdf)
                st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_libro}.pdf")

        with c2:
            if st.button("Esporta in WORD"):
                doc = Document(); doc.add_heading(titolo_libro, 0); doc.add_paragraph(f"Autore: {nome_autore}")
                for s in lista_final:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO(); doc.save(buf); buf.seek(0)
                st.download_button("📥 Scarica WORD", buf, file_name=f"{titolo_libro}.docx")
