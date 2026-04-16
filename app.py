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
    page_title="AI di Antonino: Crea il tuo Ebook", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS (UI PULITA, SIDEBAR BLOCCATA E TITOLO VISIBILE) ---
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

    .block-container { padding-top: 1rem; padding-bottom: 0rem; }

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

# --- FUNZIONI SUPPORTO ---

class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        # Se l'autore è vuoto, non scrive l'intestazione nelle pagine successive
        if self.page_no() > 1 and self.autore:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(20)

def pulisci_testo_ia(testo):
    linee = testo.split('\n')
    linee_pulite = []
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte", "here is", "sure"]
    for riga in linee:
        r_low = riga.strip().lower()
        if r_low and not any(r_low.startswith(tag) for tag in tag_proibiti):
            if not (r_low.startswith("capitolo") and len(r_low) < 60):
                linee_pulite.append(riga)
    return re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", '\n'.join(linee_pulite)).strip()

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
    testo_indice = st.session_state.get('indice', '')
    mappa = {}
    linee = testo_indice.split('\n')
    for l in linee:
        match = re.search(r'(?i)(Capitolo\s*\d+)', l)
        if match:
            cap_key = match.group(1).title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Approfondimento tematico"
    if mappa:
        st.session_state['mappa_capitoli'] = mappa
        st.session_state['lista_capitoli'] = list(mappa.keys())
    else:
        st.session_state['lista_capitoli'] = ["Capitolo 1"]
        st.session_state['mappa_capitoli'] = {"Capitolo 1": "Introduzione"}

# --- UI ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Configurazione")
    titolo_l = st.text_input("Titolo del Libro", placeholder="Inserisci il titolo...")
    # CAMPO AUTORE VUOTO
    nome_autore = st.text_input("Nome Autore", value="")
    
    lingua_l = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere_l = st.selectbox("Genere", ["Manuale Tecnico", "Manuale Psicologico", "Saggio", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    trama_l = st.text_area("Trama e Argomento Centrale", height=180, placeholder="Descrivi chiaramente di cosa parla il libro...")
    
    st.markdown("---")
    if st.button("🔄 RESET TUTTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if titolo_l and trama_l:
    S_PROMPT = (
        f"Sei un Ghostwriter esperto in {genere_l}. Scrivi in {lingua_l}.\n"
        f"RIFERIMENTO FISSO: Il libro si intitola '{titolo_l}' e tratta di: '{trama_l}'.\n"
        "REGOLE: \n"
        "- Ogni parola deve essere coerente con il titolo e la trama forniti.\n"
        "- Evita ripetizioni e mantieni un senso logico rigoroso tra i capitoli.\n"
        "- Non uscire mai fuori traccia rispetto all'argomento principale."
    )

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Struttura Indice", "✍️ 2. Scrittura Capitoli", "📝 3. Modifica Professionale", "📑 4. Esportazione"])

    with tab1:
        st.subheader("Pianificazione dell'Indice")
        if st.button("GENERA INDICE LOGICO"):
            p_ind = f"In base al titolo '{titolo_l}' e alla trama '{trama_l}', crea un indice coerente e sequenziale. Usa 'Capitolo X: Titolo'."
            st.session_state['indice'] = chiedi_gpt(p_ind, "Editor esperto in pianificazione editoriale.")
            sync_capitoli()
        
        if 'indice' not in st.session_state: st.session_state['indice'] = "Capitolo 1: Introduzione"
        st.session_state['indice'] = st.text_area("Revisiona l'indice qui:", value=st.session_state['indice'], height=300)
        
        if st.button("🔄 CONFERMA E SINCRONIZZA"):
            sync_capitoli()
            st.rerun()

    if 'lista_capitoli' not in st.session_state: sync_capitoli()

    with tab2:
        opzioni = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sez_s = st.selectbox("Seleziona sezione da generare:", opzioni)
        k_s = sez_s.lower().replace(" ", "_")
        arg_cap = st.session_state.get('mappa_capitoli', {}).get(sez_s, "")

        if st.button(f"SCRIVI {sez_s.upper()}"):
            with st.spinner(f"Scrittura in corso... (Focus: {titolo_l})"):
                testo_cap = ""
                # Analisi memoria precedente per evitare ripetizioni
                memoria = ""
                percorso_memoria = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']]
                for m_k in percorso_memoria:
                    if m_k in st.session_state:
                        memoria += f"RIASSUNTO {m_k.upper()}: {st.session_state[m_k][:400]}...\n"

                for fase in ["Incipit", "Sviluppo centrale", "Sintesi e chiusura"]:
                    p_scr = (
                        f"CONTESTO EBOOK: {memoria}\n"
                        f"Sezione attuale: {sez_s}.\n"
                        f"Argomento specifico: {arg_cap}.\n"
                        f"Fase: {fase}.\n"
                        "Assicurati che il contenuto sia originale e strettamente legato al tema centrale senza ripetere quanto già scritto."
                    )
                    testo_cap += chiedi_gpt(p_scr, S_PROMPT) + "\n\n"
                st.session_state[k_s] = testo_cap
        
        if k_s in st.session_state:
            st.session_state[k_s] = st.text_area("Contenuto Generato:", value=st.session_state[k_s], height=400, key=f"v_{k_s}")

    with tab3:
        st.subheader("🛠️ Modifiche Mirate")
        sez_m = st.selectbox("Cosa vuoi rifinire?", opzioni)
        k_m = sez_m.lower().replace(" ", "_")
        
        if k_m in st.session_state:
            if f"ver_{k_m}" not in st.session_state: st.session_state[f"ver_{k_m}"] = 0
            
            c_mod1, c_mod2 = st.columns([1, 2])
            with c_mod1:
                intervento = st.radio("Azione suggerita:", [
                    "✨ Migliora fluidità",
                    "📈 Espandi concetti",
                    "✂️ Rendi più conciso",
                    "🧐 Correzione grammaticale",
                    "🛠️ Istruzione personalizzata"
                ])
            with c_mod2:
                dettagli = st.text_area("Dettagli per la modifica:", placeholder="Cosa deve cambiare esattamente?", height=150)
            
            testo_input = st.text_area("Testo attuale da modificare:", 
                                      value=st.session_state[k_m], 
                                      height=350, 
                                      key=f"area_{k_m}_{st.session_state[f'ver_{k_m}']}")
            
            if st.button("🚀 ESEGUI MODIFICA CONCRETA"):
                with st.spinner("L'IA sta rielaborando il testo..."):
                    p_mod = (
                        f"Modifica il seguente testo della sezione {sez_m}.\n"
                        f"Azione: {intervento}. Dettagli: {dettagli}.\n"
                        f"Mantieni focus su: {titolo_l}.\n\n"
                        f"Testo:\n{testo_input}"
                    )
                    nuovo_t = chiedi_gpt(p_mod, S_PROMPT + " Revisione Editoriale.")
                    st.session_state[k_m] = nuovo_t
                    st.session_state[f"ver_{k_m}"] += 1
                    st.success("Testo modificato!")
                    st.rerun()
        else:
            st.info("Genera prima il contenuto nella scheda 'Scrittura Capitoli'.")

    with tab4:
        st.subheader("Download Finale")
        l_f = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("ESPORTA PDF PROFESSIONALE"):
                pdf = PDF(nome_autore); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80)
                pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                if nome_autore:
                    pdf.set_font("Arial", "", 18); pdf.cell(0, 20, f"di {nome_autore}", 0, 1, "C")
                for s in l_f:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18)
                        pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 12)
                        t_pdf = st.session_state[s].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 8, t_pdf)
                st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        
        with c2:
            if st.button("ESPORTA DOCX (WORD)"):
                doc = Document(); doc.add_heading(titolo_l, 0)
                if nome_autore: doc.add_paragraph(f"Autore: {nome_autore}")
                for s in l_f:
                    if s in st.session_state:
                        doc.add_page_break()
                        doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 Scarica Word", buf_w, file_name=f"{titolo_l}.docx")
else:
    st.warning("⚠️ Per iniziare, inserisci il Titolo e la Trama nella barra laterale sinistra.")
