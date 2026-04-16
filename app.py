import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. Connessione API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA E SIDEBAR FISSA ---
st.set_page_config(
    page_title="AI di Antonino", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS PER BLOCCARE LA SIDEBAR E NASCONDERE MENU (OTTIMIZZATO IFRAME) ---
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
    
    # FILTRO ANTI-COMMENTI E ANTI-INTESTAZIONI
    linee = risposta.split('\n')
    linee_pulite = []
    tag_da_eliminare = [
        "ecco", "certamente", "spero", "di seguito", "ciao", "here is", "sure", "voilà", "iată", "вот", "这里是",
        "inizio", "sviluppo", "conclusione", "fine", "parte 1", "parte 2", "parte 3"
    ]
    
    for l in linee:
        testo_l = l.strip().lower()
        # Non aggiunge la riga se è un saluto o se è solo un'etichetta di fase (es. "Inizio:")
        if testo_l and not any(testo_l.startswith(p) for p in tag_da_eliminare):
            # Ulteriore controllo per evitare che scriva il nome del capitolo nel corpo del testo
            if not testo_l.startswith("capitolo"):
                linee_pulite.append(l)
    
    testo_finale = '\n'.join(linee_pulite).strip()
    # Rimuove frasi di cortesia finali
    testo_finale = re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|spero ti piaccia).*$", "", testo_finale).strip()
    return testo_finale

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def get_max_chapters():
    if 'indice' in st.session_state:
        matches = re.findall(r'(?i)Capitolo\s*(\d+)', st.session_state['indice'])
        if matches:
            return max([int(m) for m in matches])
    return 1

# --- INTERFACCIA ---
st.title("AI di Antonino: \"Crea il tuo EBook\"")

sezioni_totali_base = ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]

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
    S_P = f"Sei un Ghostwriter esperto in {modalita}. Scrivi in {lingua}. REGOLE: Solo testo narrativo. NO saluti, NO titoli di capitolo, NO etichette come 'Inizio' o 'Fine'. Produci un flusso di testo continuo e coerente."
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Struttura", "🎨 Copertina", "✍️ Scrittura", "📝 Modifica", "📑 Esporta"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea indice in {lingua} per: {titolo}. Trama: {trama}. Elenca i capitoli chiaramente.", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice", st.session_state['indice'], height=200)

    with tab2:
        if st.button("Genera Copertina AI"):
            with st.spinner("Creazione..."):
                try:
                    res = client.images.generate(model="dall-e-3", prompt=f"Book cover: {titolo}, {modalita}.", n=1, size="1024x1792")
                    st.session_state['cover_url'] = res.data[0].url
                except Exception as e: st.error(e)
        if 'cover_url' in st.session_state:
            st.image(st.session_state['cover_url'], use_container_width=True)

    max_cap = get_max_chapters()
    elenco_capitoli = [f"Capitolo {i}" for i in range(1, max_cap + 1)]

    with tab3:
        tipo = st.selectbox("Cosa vuoi scrivere?", ["Prefazione"] + elenco_capitoli + ["Ringraziamenti"])
        chiave = tipo.lower().replace(" ", "_")
        
        if st.button("Avvia Scrittura Sezione"):
            with st.spinner("Scrittura pulita in corso..."):
                memoria = "\n".join([st.session_state[k][:500] for k in st.session_state if "capitolo" in k or "prefazione" in k])
                testo_sez = ""
                # Scriviamo le 3 fasi ma senza etichette nel prompt finale
                parti_prompt = [
                    "Scrivi l'introduzione della sezione, immergendo il lettore.",
                    "Prosegui con lo sviluppo centrale, mantenendo alta l'attenzione.",
                    "Concludi la sezione in modo logico per preparare il seguito."
                ]
                for p_istruzione in parti_prompt:
                    testo_sez += chiedi_gpt(f"Trama: {trama}\nMemoria: {memoria}\nIstruzione: {p_istruzione}\nStai scrivendo: {tipo}", S_P) + "\n\n"
                st.session_state[chiave] = testo_sez
        
        if chiave in st.session_state:
            st.text_area("Testo Generato", st.session_state[chiave], height=350)

    with tab4:
        st.subheader("Editor Professionale")
        s_mod = st.selectbox("Sezione da modificare", ["Prefazione"] + elenco_capitoli + ["Ringraziamenti"])
        k_mod = s_mod.lower().replace(" ", "_")
        if k_mod in st.session_state:
            t_or = st.text_area("Testo attuale", st.session_state[k_mod], height=250)
            istr = st.text_input("Istruzioni per la ristrutturazione")
            if st.button("Applica Ristrutturazione"):
                st.session_state[k_mod] = chiedi_gpt(f"Ristruttura seguendo: {istr}\n\nTesto:\n{t_or}", S_P + " Agisci come Senior Editor.")
                st.success("Modificato!")
                st.rerun()
        else: st.info("Genera prima la sezione.")

    with tab5:
        nome_a = autore if autore else "Autore"
        sezioni_finali = ["prefazione"] + [c.lower().replace(" ", "_") for c in elenco_capitoli] + ["ringraziamenti"]
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Genera PDF"):
                pdf = PDF(nome_a); pdf.set_auto_page_break(True, 15); pdf.add_page()
                if 'cover_url' in st.session_state:
                    try:
                        img = requests.get(st.session_state['cover_url']).content
                        with open("temp.jpg", "wb") as f: f.write(img)
                        pdf.image("temp.jpg", 0, 0, 210, 297)
                    except: pdf.cell(0, 10, titolo)
                for s in sezioni_finali:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 11)
                        pdf.multi_cell(0, 7, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                pdf.output("libro.pdf")
                with open("libro.pdf", "rb") as f: st.download_button("📥 PDF", f, file_name=f"{titolo}.pdf", use_container_width=True)
        with c2:
            if st.button("Genera WORD"):
                doc = Document(); doc.add_heading(titolo, 0)
                for s in sezioni_finali:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO(); doc.save(buf); buf.seek(0)
                st.download_button("📥 WORD", buf, file_name=f"{titolo}.docx", use_container_width=True)
