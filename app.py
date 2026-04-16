import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. Connessione API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="AI di Antonino", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS PER BLOCCARE LA SIDEBAR E OTTIMIZZARE IFRAME ---
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
    .stButton>button {width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold;}
    .stTextArea textarea {font-size: 16px !important;}
    </style>
""", unsafe_allow_html=True)

# CLASSE PDF PROFESSIONALE
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"{self.autore}", 0, 0, 'C')
            self.ln(20)

def chiedi_gpt(p, s_p):
    r = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role":"system","content":s_p},{"role":"user","content":p}],
        temperature=0.7
    )
    risposta = r.choices[0].message.content
    linee = risposta.split('\n')
    linee_pulite = []
    tag_da_eliminare = ["ecco", "certamente", "spero", "di seguito", "ciao", "here is", "sure", "voilà", "iată", "вот", "这里是", "inizio", "sviluppo", "fine", "fase"]
    for l in linee:
        testo_l = l.strip().lower()
        if testo_l and not any(testo_l.startswith(p) for p in tag_da_eliminare):
            if not testo_l.startswith("capitolo") or ":" in testo_l or "-" in testo_l:
                linee_pulite.append(l)
    testo_finale = '\n'.join(linee_pulite).strip()
    return re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", testo_finale).strip()

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def ottieni_lista_capitoli():
    if 'indice' in st.session_state:
        # Estrazione numerica precisa dei capitoli dall'indice
        numeri = re.findall(r'(?i)(?:Capitolo|Cap\.)\s*(\d+)', st.session_state['indice'])
        if numeri:
            max_c = max([int(n) for n in numeri])
            return [f"Capitolo {i}" for i in range(1, max_c + 1)]
    return ["Capitolo 1"]

# --- INTERFACCIA ---
st.title("AI di Antonino: \"Crea il tuo EBook\"")

with st.sidebar:
    st.header("⚙️ Configurazione")
    titolo = st.text_input("Titolo Libro", "")
    autore = st.text_input("Nome Autore", "")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    modalita = st.selectbox("Genere", ["Manuale Psicologico", "Thriller Psicologico", "Saggio Psicologico", "Manuale Tecnico", "Noir", "Thriller", "Motivazionale", "Fantasy", "Romanzo Storico", "Romanzo Rosa"])
    trama = st.text_area("Trama o Argomento")
    st.markdown("---")
    if st.button("🔄 RESET COMPLETO"):
        reset_app()

if trama:
    S_P = f"Sei un Ghostwriter esperto in {modalita}. Scrivi in {lingua}. REGOLE: Solo testo narrativo. NO saluti. NO titoli capitolo interni. Flusso continuo."
    
    # Rimosso il tab "Copertina"
    tab1, tab3, tab4, tab5 = st.tabs(["📊 Struttura Indice", "✍️ Scrittura", "📝 Revisione & Modifica", "📑 Esporta Finale"])

    with tab1:
        st.subheader("Indice Editoriale")
        if st.button("Genera Indice con AI"):
            p_ind = f"Crea un indice professionale per '{titolo}'. Trama: {trama}. Usa 'Capitolo X: Titolo'."
            st.session_state['indice'] = chiedi_gpt(p_ind, "Sei un Editor esperto.")
        
        if 'indice' not in st.session_state:
            st.session_state['indice'] = "Capitolo 1: Introduzione"
            
        st.session_state['indice'] = st.text_area("Puoi modificare l'indice manualmente (es. aggiungi 'Capitolo 2: ...'):", 
                                                value=st.session_state['indice'], 
                                                height=300)
        if st.button("🔄 Conferma e Aggiorna Capitoli"):
            st.rerun()

    elenco_capitoli = ottieni_lista_capitoli()

    with tab3:
        tipo = st.selectbox("Scegli cosa scrivere", ["Prefazione"] + elenco_capitoli + ["Ringraziamenti"])
        chiave = tipo.lower().replace(" ", "_")
        
        if st.button("Genera Testo Sezione"):
            with st.spinner("Scrittura in corso..."):
                memoria = "\n".join([st.session_state[k][:500] for k in st.session_state if "capitolo" in k or "prefazione" in k])
                testo_sez = ""
                for fase in ["Incipit", "Corpo centrale", "Finale"]:
                    testo_sez += chiedi_gpt(f"Memoria precedente: {memoria}\nScrivi {tipo} ({fase}). Trama: {trama}", S_P) + "\n\n"
                st.session_state[chiave] = testo_sez
        
        if chiave in st.session_state:
            # Salvataggio automatico durante l'editing manuale
            st.session_state[chiave] = st.text_area("Testo attuale (puoi scriverci dentro):", value=st.session_state[chiave], height=450, key=f"v_{chiave}")

    with tab4:
        st.subheader("Revisione Assistita")
        s_mod = st.selectbox("Seleziona sezione da migliorare", ["Prefazione"] + elenco_capitoli + ["Ringraziamenti"])
        k_mod = s_mod.lower().replace(" ", "_")
        
        if k_mod in st.session_state:
            # Sistema di modifica stabilizzato: legge dallo stato e sovrascrive
            testo_buffer = st.text_area("Contenuto da revisionare:", value=st.session_state[k_mod], height=350, key=f"e_{k_mod}")
            istr = st.text_input("Quale modifica vuoi apportare? (es: 'Espandi la descrizione', 'Cambia tono')")
            
            if st.button("Applica Modifica con IA"):
                with st.spinner("Riscrivendo..."):
                    # Salviamo il contenuto attuale dell'area di testo prima di inviare
                    st.session_state[k_mod] = testo_buffer
                    # Invio istruzioni
                    nuovo_testo = chiedi_gpt(f"Ristruttura seguendo questa istruzione: {istr}\n\nTesto:\n{testo_buffer}", S_P + " Senior Editor.")
                    st.session_state[k_mod] = nuovo_testo
                    st.success("Modifica completata!")
                    st.rerun()
        else: st.info("Genera prima il testo nella scheda 'Scrittura'.")

    with tab5:
        nome_a = autore if autore else "Autore"
        sez_f = ["prefazione"] + [c.lower().replace(" ", "_") for c in elenco_capitoli] + ["ringraziamenti"]
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Genera PDF"):
                pdf = PDF(nome_a); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo.upper(), 0, 1, "C")
                pdf.set_font("Arial", "", 18); pdf.cell(0, 20, f"di {nome_a}", 0, 1, "C")
                for s in sez_f:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 11)
                        pdf.multi_cell(0, 7, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                pdf.output("l.pdf")
                with open("l.pdf", "rb") as f: st.download_button("📥 Scarica PDF", f, file_name=f"{titolo}.pdf", use_container_width=True)
        with c2:
            if st.button("Genera WORD"):
                doc = Document(); doc.add_heading(titolo, 0); doc.add_paragraph(f"Autore: {nome_a}")
                for s in sez_f:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO(); doc.save(buf); buf.seek(0)
                st.download_button("📥 Scarica WORD", buf, file_name=f"{titolo}.docx", use_container_width=True)
