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
    page_title="AI di Antonino: Crea il tuo Ebook", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS (COLORI ORIGINALI, SIDEBAR FISSA E TITOLO) ---
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
    }

    /* Contenitore principale */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }

    /* Titolo Grande e Visibile */
    .main-title {
        font-size: 42px;
        font-weight: bold;
        color: #31333F;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 10px;
    }

    /* Pulsanti Originali */
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

    .stTextArea textarea { 
        font-size: 16px !important; 
        line-height: 1.6 !important;
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
        return f"Errore API: {str(e)}"

def sync_capitoli_dettagliati():
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

# --- TITOLO VISIBILE ---
st.markdown('<div class="main-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")
    titolo_l = st.text_input("Titolo dell'opera")
    nome_autore = st.text_input("Nome Autore")
    lingua_l = st.selectbox("Lingua / Language", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere_l = st.selectbox("Genere / Tipologia", ["Manuale Tecnico (Pratico/Divulgativo)", "Manuale Psicologico", "Thriller Psicologico", "Saggio", "Motivazionale", "Noir", "Thriller", "Fantasy", "Romanzo Storico", "Romanzo Rosa"])
    trama_l = st.text_area("Trama o Argomento principale", height=150)
    st.markdown("---")
    if st.button("🔄 RESET COMPLETO"):
        reset_app()

if trama_l:
    S_PROMPT = f"Sei un Ghostwriter esperto in {genere_l}. Scrivi in {lingua_l}. REGOLE: Attieniti all'argomento del capitolo fornito."

    tab_ind, tab_scr, tab_mod, tab_esp = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "📝 3. Modifica", "📑 4. Esporta"])

    # --- TAB 1: INDICE ---
    with tab_ind:
        if st.button("Genera Indice Professionale"):
            p_ind = f"Crea un indice per '{titolo_l}'. Trama: {trama_l}. Usa 'Capitolo X: Titolo'."
            st.session_state['indice'] = chiedi_gpt(p_ind, "Editor Senior.")
            sync_capitoli_dettagliati()

        if 'indice' not in st.session_state: st.session_state['indice'] = "Capitolo 1: Introduzione"
        
        st.session_state['indice'] = st.text_area("Modifica Indice:", value=st.session_state['indice'], height=300)
        
        if st.button("🔄 Sincronizza Capitoli"):
            sync_capitoli_dettagliati()
            st.rerun()

    if 'lista_capitoli' not in st.session_state: sync_capitoli_dettagliati()

    # --- TAB 2: SCRITTURA ---
    with tab_scr:
        opzioni_s = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sez_scelta = st.selectbox("Cosa vuoi scrivere?", opzioni_s)
        chiave_s = sez_scelta.lower().replace(" ", "_")
        arg_sp = st.session_state.get('mappa_capitoli', {}).get(sez_scelta, "")

        if st.button(f"Genera {sez_scelta}"):
            with st.spinner("Scrittura in corso..."):
                t_sez = ""
                for fase in ["Inizio", "Sviluppo", "Fine"]:
                    p_scr = f"Argomento: {arg_sp}\nScrivi {sez_scelta} ({fase})."
                    t_sez += chiedi_gpt(p_scr, S_PROMPT) + "\n\n"
                st.session_state[chiave_s] = t_sez
        
        if chiave_s in st.session_state:
            st.session_state[chiave_s] = st.text_area("Contenuto:", value=st.session_state[chiave_s], height=400, key=f"v_{chiave_s}")

    # --- TAB 3: MODIFICA (STABILIZZATA) ---
    with tab_mod:
        sez_mod = st.selectbox("Seleziona da migliorare:", opzioni_s)
        k_mod = sez_mod.lower().replace(" ", "_")
        
        if k_mod in st.session_state:
            # Buffer per stabilità
            if f"buf_{k_mod}" not in st.session_state:
                st.session_state[f"buf_{k_mod}"] = st.session_state[k_mod]

            t_area = st.text_area("Testo attuale:", value=st.session_state[k_mod], height=350, key=f"area_{k_mod}")
            istr_m = st.text_input("Cosa vuoi cambiare?")
            
            if st.button("Applica Modifica con IA"):
                with st.spinner("Modifica in corso..."):
                    # 1. Aggiorna lo stato col testo nell'area
                    st.session_state[k_mod] = t_area
                    # 2. Richiesta IA
                    nuovo_t = chiedi_gpt(f"Modifica: {istr_m}\nTesto:\n{t_area}", S_PROMPT + " Editor Senior.")
                    # 3. Sovrascrittura forzata
                    st.session_state[k_mod] = nuovo_t
                    st.success("Testo modificato!")
                    st.rerun()
        else: st.info("Genera prima la sezione.")

    # --- TAB 4: ESPORTAZIONE ---
    with tab_esp:
        lista_f = ["prefazione"] + [c.lower().replace(" ", "_") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Esporta PDF"):
                pdf = PDF(nome_autore); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper() if titolo_l else "LIBRO", 0, 1, "C")
                for sez in lista_f:
                    if sez in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, sez.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 12)
                        txt_p = st.session_state[sez].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 8, txt_p)
                st.download_button("📥 PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        with c2:
            if st.button("Esporta WORD"):
                doc = Document(); doc.add_heading(titolo_l if titolo_l else "Libro", 0)
                for sez in lista_f:
                    if sez in st.session_state:
                        doc.add_page_break(); doc.add_heading(sez.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[sez])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 WORD", buf_w, file_name=f"{titolo_l}.docx")
