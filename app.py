import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. INIZIALIZZAZIONE API (Prende la chiave dai Secrets di Streamlit)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE AMBIENTE E SIDEBAR ---
# initial_sidebar_state="expanded" assicura che il menu sia aperto al caricamento
st.set_page_config(
    page_title="AI di Antonino - Scrittore Professionale", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS AVANZATO (IFRAME & UI) ---
# Questo blocco nasconde tutto ciò che è superfluo e blocca la sidebar
st.markdown("""
    <style>
    /* Nasconde header, footer e tasti di sistema di Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display:none;}
    .stDeployButton {display:none;}

    /* Impedisce la chiusura della sidebar (Rimuove il tasto X e la freccetta) */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Blocca la larghezza della sidebar per stabilità su ogni schermo */
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    /* Ottimizzazione contenitore principale per eliminare spazi vuoti in alto */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }

    /* Stile personalizzato per i pulsanti: grandi e leggibili */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        font-weight: bold;
        background-color: #f0f2f6;
        transition: 0.3s;
    }
    
    /* Font più grande per le aree di testo (migliore per la scrittura) */
    .stTextArea textarea {
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGICA DI SUPPORTO ---

class PDF(FPDF):
    """Gestisce la creazione del PDF professionale."""
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(20)

def pulisci_testo_ia(testo):
    """Rimuove commenti, saluti e intestazioni inutili dell'IA."""
    linee = testo.split('\n')
    linee_pulite = []
    tag_proibiti = [
        "ecco", "certamente", "spero", "di seguito", "ciao", "va bene", "perfetto",
        "here is", "sure", "i hope", "voilà", "aquí está", "hier ist", "iată", "вот",
        "inizio", "sviluppo", "conclusione", "fine", "fase", "parte"
    ]
    for riga in linee:
        r_low = riga.strip().lower()
        if r_low and not any(r_low.startswith(tag) for tag in tag_proibiti):
            # Non ripetere il titolo del capitolo se è isolato
            if not (r_low.startswith("capitolo") and len(r_low) < 50):
                linee_pulite.append(riga)
    
    risultato = '\n'.join(linee_pulite).strip()
    # Rimuove frasi di cortesia finali
    risultato = re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", risultato).strip()
    return risultato

def chiedi_gpt(prompt, system_prompt):
    """Invia la richiesta a OpenAI e restituisce il testo pulito."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            temperature=0.7
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore di connessione: {str(e)}"

def ottieni_capitoli_da_indice():
    """Analizza l'indice (anche se modificato a mano) e crea la lista capitoli."""
    if 'indice' in st.session_state:
        numeri = re.findall(r'(?i)(?:Capitolo|Cap\.)\s*(\d+)', st.session_state['indice'])
        if numeri:
            max_c = max([int(n) for n in numeri])
            return [f"Capitolo {i}" for i in range(1, max_c + 1)]
    return ["Capitolo 1"]

def reset_totale():
    """Pulisce la memoria dell'app per un nuovo libro."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- INTERFACCIA BARRA LATERALE (FISSA) ---
with st.sidebar:
    st.title("✍️ Studio Editoriale")
    st.subheader("Configurazione Libro")
    
    titolo_libro = st.text_input("Titolo dell'opera", placeholder="Inserisci il titolo...")
    nome_autore = st.text_input("Nome Autore", placeholder="Tuo nome...")
    
    lingua_scelta = st.selectbox("Lingua di stesura", [
        "Italiano", "English", "Deutsch", "Français", 
        "Español", "Română", "Русский", "中文"
    ])
    
    genere_libro = st.selectbox("Genere / Tipologia", [
        "Manuale Psicologico", "Thriller Psicologico", "Saggio Psicologico",
        "Manuale Tecnico", "Noir", "Thriller", "Motivazionale", 
        "Fantasy", "Romanzo Storico", "Romanzo Rosa"
    ])
    
    trama_base = st.text_area("Di cosa parla il libro? (Trama)", height=150)
    
    st.markdown("---")
    if st.button("🔄 RICOMINCIA DA CAPO"):
        reset_totale()

# --- LOGICA PRINCIPALE ---
if not trama_base:
    st.info("👋 Benvenuto! Per iniziare, inserisci la trama o l'argomento del tuo libro nella barra a sinistra.")
else:
    # Definizione del System Prompt coerente
    GHOSTWRITER_PROMPT = f"Sei un Ghostwriter esperto in {genere_libro}. Scrivi in {lingua_scelta}. "
    GHOSTWRITER_PROMPT += "STILE: Narrativo, profondo, senza introduzioni o commenti personali. "
    GHOSTWRITER_PROMPT += "COERENZA: Assicura che i capitoli siano legati logicamente tra loro."

    # Tab di navigazione
    tab_ind, tab_scr, tab_mod, tab_esp = st.tabs([
        "📊 1. Struttura Indice", 
        "✍️ 2. Scrittura Capitoli", 
        "📝 3. Revisione & Modifica", 
        "📑 4. Esportazione"
    ])

    # --- 1. TAB INDICE (EDITABILE) ---
    with tab_ind:
        st.subheader("Pianificazione della Struttura")
        if st.button("Genera Indice Professionale con AI"):
            with st.spinner("L'IA sta strutturando il tuo libro..."):
                p_indice = f"Crea un indice per '{titolo_libro}'. Trama: {trama_base}. Elenca i capitoli come 'Capitolo 1: Titolo', ecc."
                st.session_state['indice'] = chiedi_gpt(p_indice, "Sei un Editor Senior.")
        
        if 'indice' not in st.session_state:
            st.session_state['indice'] = "Capitolo 1: Introduzione"
        
        # L'utente può modificare l'indice qui e i menu si aggiorneranno
        st.session_state['indice'] = st.text_area(
            "Modifica l'indice qui sotto (aggiungi capitoli manualmente se desideri):", 
            value=st.session_state['indice'], 
            height=300
        )
        st.caption("Nota: Scrivi 'Capitolo X' per attivare i menu di scrittura per quel capitolo.")

    # Calcolo dei capitoli disponibili
    lista_capitoli = ottieni_capitoli_da_indice()

    # --- 2. TAB SCRITTURA (COERENTE) ---
    with tab_scr:
        st.subheader("Stesura dei Contenuti")
        sezione_da_scrivere = st.selectbox("Cosa vuoi scrivere ora?", ["Prefazione"] + lista_capitoli + ["Ringraziamenti"])
        chiave_memoria = sezione_da_scrivere.lower().replace(" ", "_")
        
        if st.button(f"Scrivi {sezione_da_scrivere}"):
            with st.spinner(f"Scrittura in corso... l'IA sta analizzando la coerenza narrativa."):
                # Recupero memoria per concatenazione logica
                contesto_precedente = ""
                sezioni_possibili = ["prefazione"] + [c.lower().replace(" ", "_") for c in lista_capitoli]
                for s in sezioni_possibili:
                    if s in st.session_state:
                        contesto_precedente += f"Riferimento {s}: {st.session_state[s][:400]}...\n"
                
                testo_finale_sezione = ""
                # Scrittura in 3 blocchi per profondità, ma senza etichette
                istruzioni_fasi = ["Incipit", "Sviluppo narrativo/tecnico", "Chiusura della sezione"]
                for fase in istruzioni_fasi:
                    p_scrittura = f"Trama: {trama_base}\nContesto precedente: {contesto_precedente}\n\n"
                    p_scrittura += f"Scrivi la parte di {fase} per la sezione: {sezione_da_scrivere}. Lingua: {lingua_scelta}."
                    testo_finale_sezione += chiedi_gpt(p_scrittura, GHOSTWRITER_PROMPT) + "\n\n"
                
                st.session_state[chiave_memoria] = testo_finale_sezione

        if chiave_memoria in st.session_state:
            st.session_state[chiave_memoria] = st.text_area(
                "Contenuto generato (puoi anche scrivere manualmente qui):", 
                value=st.session_state[chiave_memoria], 
                height=450, 
                key=f"area_scrittura_{chiave_memoria}"
            )

    # --- 3. TAB MODIFICA (STABILE) ---
    with tab_mod:
        st.subheader("Revisione Professionale con AI")
        sezione_revisione = st.selectbox("Seleziona la parte da migliorare:", ["Prefazione"] + lista_capitoli + ["Ringraziamenti"])
        chiave_modifica = sezione_revisione.lower().replace(" ", "_")
        
        if chiave_modifica in st.session_state:
            # Buffer di testo: leggiamo ciò che è correntemente salvato
            testo_da_rivedere = st.text_area(
                "Testo attuale della sezione:", 
                value=st.session_state[chiave_modifica], 
                height=350, 
                key=f"area_revisione_{chiave_modifica}"
            )
            
            comando_modifica = st.text_input("Cosa vuoi che l'IA cambi o migliori? (es: 'Rendilo più drammatico', 'Aggiungi dettagli tecnici')")
            
            if st.button("Applica Modifica Strategica"):
                with st.spinner("Rielaborazione editoriale in corso..."):
                    # Salviamo prima eventuali modifiche manuali fatte nell'area
                    st.session_state[chiave_modifica] = testo_da_rivedere
                    
                    p_modifica = f"Testo originale:\n{testo_da_rivedere}\n\nIstruzione di modifica: {comando_modifica}\n"
                    nuovo_testo = chiedi_gpt(p_modifica, GHOSTWRITER_PROMPT + " Agisci come Senior Editor.")
                    
                    # Aggiorniamo la memoria e ricarichiamo per mostrare il risultato
                    st.session_state[chiave_modifica] = nuovo_testo
                    st.success("Testo aggiornato correttamente!")
                    st.rerun()
        else:
            st.info("Genera il testo di questa sezione nella scheda 'Scrittura' per poterlo modificare qui.")

    # --- 4. TAB ESPORTAZIONE ---
    with tab_esp:
        st.subheader("Produzione File Finale")
        nome_file_pulito = titolo_libro.replace(" ", "_") if titolo_libro else "mio_libro"
        lista_completa_ordine = ["prefazione"] + [c.lower().replace(" ", "_") for c in lista_capitoli] + ["ringraziamenti"]
        
        col_pdf, col_docx = st.columns(2)
        
        with col_pdf:
            if st.button("Esporta in PDF"):
                with st.spinner("Creazione PDF..."):
                    pdf = PDF(nome_autore if nome_autore else "Autore Professionale")
                    pdf.set_auto_page_break(True, 15)
                    pdf.add_page()
                    
                    # Copertina testuale (Dato che abbiamo tolto l'immagine copertina)
                    pdf.set_font("Arial", "B", 35); pdf.ln(80)
                    pdf.cell(0, 20, titolo_libro.upper() if titolo_libro else "TITOLO LIBRO", 0, 1, "C")
                    pdf.set_font("Arial", "", 20)
                    pdf.cell(0, 20, f"di {nome_autore}" if nome_autore else "", 0, 1, "C")
                    
                    # Contenuti
                    for sez in lista_completa_ordine:
                        if sez in st.session_state:
                            pdf.add_page()
                            pdf.set_font("Arial", "B", 18)
                            pdf.cell(0, 10, sez.upper().replace("_", " "), 0, 1, "L")
                            pdf.ln(10)
                            pdf.set_font("Arial", "", 12)
                            # Gestione codifica per caratteri speciali
                            testo_pdf = st.session_state[sez].encode('latin-1', 'replace').decode('latin-1')
                            pdf.multi_cell(0, 8, testo_pdf)
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button("📥 Scarica PDF", pdf_output, file_name=f"{nome_file_pulito}.pdf", mime="application/pdf")

        with col_docx:
            if st.button("Esporta in WORD (Docx)"):
                with st.spinner("Creazione Word..."):
                    doc = Document()
                    doc.add_heading(titolo_libro if titolo_libro else "Mio Libro", 0)
                    doc.add_paragraph(f"Autore: {nome_autore}")
                    
                    for sez in lista_completa_ordine:
                        if sez in st.session_state:
                            doc.add_page_break()
                            doc.add_heading(sez.upper().replace("_", " "), level=1)
                            doc.add_paragraph(st.session_state[sez])
                    
                    buffer_word = BytesIO()
                    doc.save(buffer_word)
                    buffer_word.seek(0)
                    st.download_button(
                        "📥 Scarica WORD", 
                        buffer_word, 
                        file_name=f"{nome_file_pulito}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
