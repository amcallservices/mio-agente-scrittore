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

# --- BLOCCO CSS (UI PULITA E SIDEBAR BLOCCATA) ---
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
            temperature=0.85 # Aumentata per favorire una riscrittura più creativa e meno ripetitiva
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore: {str(e)}"

def sync_capitoli():
    testo_indice = st.session_state.get('indice', '')
    mappa = {}
    linee = testo_indice.split('\n')
    for l in linee:
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.)', l)
        if match:
            cap_key = match.group(0).strip().title()
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
    nome_autore = st.text_input("Nome Autore", value="")
    lingua_l = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere_l = st.selectbox("Genere", ["Manuale Tecnico", "Manuale Psicologico", "Saggio", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    trama_l = st.text_area("Trama e Argomento Centrale", height=180)
    
    if st.button("🔄 RESET TOTALE"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if titolo_l and trama_l:
    S_PROMPT = (
        f"Sei un Ghostwriter esperto in {genere_l}. Scrivi in {lingua_l}.\n"
        f"Il libro è '{titolo_l}' e parla di '{trama_l}'.\n"
        "REGOLE: Sostituisci concetti ripetitivi con nuove prospettive. "
        "Mantieni un'eleganza stilistica costante e una logica ferrea tra i paragrafi."
    )

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Struttura Indice", "✍️ 2. Scrittura Capitoli", "📝 3. Rielaborazione Totale", "📑 4. Esporta"])

    with tab1:
        if st.button("GENERA INDICE LOGICO"):
            p_ind = f"Crea un indice coerente per '{titolo_l}' basato sulla trama '{trama_l}'. Usa 'Capitolo X: Titolo'."
            st.session_state['indice'] = chiedi_gpt(p_ind, "Editor esperto.")
            sync_capitoli()
        
        if 'indice' not in st.session_state: st.session_state['indice'] = "Capitolo 1: Introduzione"
        st.session_state['indice'] = st.text_area("Revisiona l'indice:", value=st.session_state['indice'], height=300)
        if st.button("🔄 SINCRONIZZA"):
            sync_capitoli(); st.rerun()

    if 'lista_capitoli' not in st.session_state: sync_capitoli()

    with tab2:
        opzioni = ["Prefazione"] + st.session_state['lista_capitoli'] + ["Ringraziamenti"]
        sez_s = st.selectbox("Seleziona sezione da scrivere:", opzioni)
        k_s = sez_s.lower().replace(" ", "_").replace(".", "")
        arg_cap = st.session_state.get('mappa_capitoli', {}).get(sez_s, "")

        if st.button(f"GENERA {sez_s.upper()}"):
            with st.spinner("Scrittura in corso..."):
                testo_cap = ""
                for fase in ["Inizio", "Sviluppo centrale", "Fine"]:
                    testo_cap += chiedi_gpt(f"Scrivi {sez_s} ({fase}) su: {arg_cap}.", S_PROMPT) + "\n\n"
                st.session_state[k_s] = testo_cap
        
        if k_s in st.session_state:
            st.session_state[k_s] = st.text_area("Contenuto:", value=st.session_state[k_s], height=400, key=f"v_{k_s}")

    with tab3:
        st.subheader("🛠️ Rielaborazione Totale e Sostituzione")
        sez_m = st.selectbox("Seleziona sezione da rifare:", opzioni)
        k_m = sez_m.lower().replace(" ", "_").replace(".", "")
        
        if k_m in st.session_state:
            if f"ver_{k_m}" not in st.session_state: st.session_state[f"ver_{k_m}"] = 0
            
            istr_mod = st.text_area("Istruzioni per l'IA (Es. 'Cambia persona', 'Usa un tono diverso'):", 
                                   placeholder="Se non scrivi nulla, l'IA riscriverà comunque il testo da zero in modo nuovo.")
            
            testo_vecchio = st.text_area("Testo attuale:", value=st.session_state[k_m], height=300, key=f"area_{k_m}_{st.session_state[f'ver_{k_m}']}")
            
            if st.button("🚀 AVVIA RIELABORAZIONE TOTALE"):
                with st.spinner("Riscrivendo interamente la sezione..."):
                    # ISTRUZIONE DI RISCRITTURA "DESTRUTTIVA"
                    p_rielabora = (
                        f"ORDINE: Riscrivi COMPLETAMENTE il testo che segue.\n"
                        f"REQUISITO: Non limitarti a correggere. Cambia le parole, la struttura delle frasi e il ritmo.\n"
                        f"ISTRUZIONE AGGIUNTIVA: {istr_mod if istr_mod else 'Riscrivi in modo totalmente originale e fluido.'}\n\n"
                        f"FOCUS EBOOK: '{titolo_l}' - '{trama_l}'\n\n"
                        f"TESTO DA CANCELLARE E SOSTITUIRE:\n{testo_vecchio}"
                    )
                    # Usiamo un system prompt ancora più autoritario per la Tab 3
                    nuovo_testo = chiedi_gpt(p_rielabora, "Sei un Senior Editor specializzato in Ghostwriting. Il tuo compito è distruggere il testo precedente e crearne uno nuovo, migliore e coerente.")
                    
                    st.session_state[k_m] = nuovo_testo
                    st.session_state[f"ver_{k_m}"] += 1
                    st.success("Il testo è stato completamente rielaborato!")
                    st.rerun()
        else:
            st.info("Genera prima il testo nella scheda 'Scrittura' per poterlo rielaborare qui.")

    with tab4:
        l_f = ["prefazione"] + [c.lower().replace(" ", "_").replace(".", "") for c in st.session_state['lista_capitoli']] + ["ringraziamenti"]
        c1, c2 = st.columns(2)
        with c1:
            if st.button("ESPORTA PDF"):
                pdf = PDF(nome_autore); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in l_f:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 12)
                        txt_p = st.session_state[s].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 8, txt_p)
                st.download_button("📥 PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        with c2:
            if st.button("ESPORTA WORD"):
                doc = Document(); doc.add_heading(titolo_l, 0)
                if nome_autore: doc.add_paragraph(f"Autore: {nome_autore}")
                for s in l_f:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button("📥 WORD", buf_w, file_name=f"{titolo_l}.docx")
