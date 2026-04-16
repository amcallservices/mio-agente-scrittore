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

# --- CSS PER BLOCCARE LA SIDEBAR E NASCONDERE MENU ---
style_permanente = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}

    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
    }
    .stTextArea textarea {
        font-size: 16px !important;
    }
    </style>
    """
st.markdown(style_permanente, unsafe_allow_html=True)

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
    
    # FILTRO ANTI-COMMENTI AGGRESSIVO
    linee = risposta.split('\n')
    linee_pulite = []
    tag_da_eliminare = [
        "ecco", "certamente", "spero", "di seguito", "questo è", "il capitolo", "ciao", "va bene", 
        "here is", "sure", "i hope", "voilà", "aquí está", "hier ist", "iată", "вот", "这里是",
        "proseguiamo", "abbiamo scritto", "fammi sapere", "buona lettura", "capitolo"
    ]
    for l in linee:
        testo_l = l.strip().lower()
        if testo_l and not any(testo_l.startswith(p) for p in tag_da_eliminare):
            linee_pulite.append(l)
    
    testo_finale = '\n'.join(linee_pulite).strip()
    testo_finale = re.sub(r"(?i)(spero che|fammi sapere|ecco il|buona scrittura|fammi sapere cosa|spero sia di aiuto|spero ti piaccia).*$", "", testo_finale).strip()
    return testo_finale

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- INTERFACCIA ---
st.title("AI di Antonino: \"Crea il tuo EBook\"")

# Definizione ordine sezioni globale per coerenza
sezioni_totali = ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]

with st.sidebar:
    st.header("⚙️ Configurazione")
    titolo = st.text_input("Titolo Libro", "")
    autore = st.text_input("Nome Autore", "")
    
    lingua = st.selectbox("Lingua / Language", [
        "Italiano", "English", "Deutsch", "Français", 
        "Español", "Română", "Русский", "中文 (Chinese)"
    ])
    
    modalita = st.selectbox("Genere / Genre", [
        "Manuale Psicologico", "Thriller Psicologico", "Saggio Psicologico",
        "Manuale Tecnico", "Noir", "Thriller", "Motivazionale", 
        "Fantasy", "Romanzo Storico", "Romanzo Rosa"
    ])
    trama = st.text_area("Trama o Argomento")
    
    st.markdown("---")
    if st.button("🔄 RESET COMPLETO"):
        reset_app()

if trama:
    S_P = f"Sei un Ghostwriter professionista esperto in {modalita}. Scrivi rigorosamente in {lingua}. REGOLE: Scrivi SOLO il testo del libro. NO saluti, NO commenti. MANTENERE COERENZA LOGICA TOTALE con i testi precedenti."

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Struttura", "🎨 Copertina", "✍️ Scrittura", "📝 Modifica", "📑 Esporta"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea un indice logico e sequenziale in {lingua} per: {titolo}. Trama: {trama}", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice", st.session_state['indice'], height=200)

    with tab2:
        if st.button("Genera Copertina AI"):
            with st.spinner("Creazione immagine..."):
                try:
                    p_img = f"Professional book cover for '{titolo}', {modalita} style, no text, cinematic high quality."
                    res = client.images.generate(model="dall-e-3", prompt=p_img, n=1, size="1024x1792")
                    st.session_state['cover_url'] = res.data[0].url
                except Exception as e: st.error(f"Errore DALL-E: {e}")
        if 'cover_url' in st.session_state:
            st.image(st.session_state['cover_url'], use_container_width=True)

    with tab3:
        tipo = st.selectbox("Sezione da scrivere", ["Prefazione", "Capitolo", "Ringraziamenti"])
        n = st.number_input("Numero Capitolo", 1, 30) if tipo == "Capitolo" else 0
        chiave = f"{tipo.lower()}_{n}" if n > 0 else tipo.lower()
        
        if st.button("Scrivi Sezione"):
            with st.spinner(f"Scrittura in corso..."):
                # Recupero memoria per concatenazione logica
                memoria_testi = ""
                for s in sezioni_totali:
                    if s in st.session_state:
                        memoria_testi += f"--- {s.upper()} ---\n{st.session_state[s][:500]}\n\n"
                
                contesto_prompt = f"Titolo: {titolo}\nTrama: {trama}\n\nMEMORIA E CONCATENAZIONE:\n{memoria_testi}"
                
                testo_sez = ""
                parti = ["Inizio", "Sviluppo", "Conclusione"]
                for p_fase in parti:
                    testo_sez += chiedi_gpt(f"{contesto_prompt}\n\nScrivi {tipo} {n if n>0 else ''} (Parte: {p_fase}). Assicura che si colleghi perfettamente a quanto scritto sopra.", S_P) + "\n\n"
                st.session_state[chiave] = testo_sez
        
        if chiave in st.session_state:
            st.text_area("Testo", st.session_state[chiave], height=350)

    with tab4:
        st.subheader("Editor Professionale")
        s_mod = st.selectbox("Cosa modifichiamo?", ["Prefazione", "Ringraziamenti"] + [f"Capitolo {i}" for i in range(1, 31)])
        k_mod = s_mod.lower().replace(" ", "_")
        
        if k_mod in st.session_state:
            t_or = st.text_area("Testo attuale", st.session_state[k_mod], height=250)
            istr = st.text_input("Istruzione per ristrutturare il testo")
            if st.button("Applica Ristrutturazione"):
                with st.spinner("Rielaborazione..."):
                    st.session_state[k_mod] = t_or
                    nuovo = chiedi_gpt(f"Riorganizza e ristruttura profondamente seguendo: {istr}\n\nTesto:\n{t_or}", S_P + " Agisci come Senior Editor.")
                    st.session_state[k_mod] = nuovo
                    st.success("Modifica applicata con successo!")
                    st.rerun()
        else: st.info("Genera prima la sezione.")

    with tab5:
        st.subheader("Download Finale")
        nome_a = autore if autore else "Autore"
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Genera PDF"):
                pdf = PDF(nome_a)
                pdf.set_auto_page_break(True, 15); pdf.add_page()
                if 'cover_url' in st.session_state:
                    try:
                        img_res = requests.get(st.session_state['cover_url']).content
                        with open("temp.jpg", "wb") as f_img: f_img.write(img_res)
                        pdf.image("temp.jpg", 0, 0, 210, 297)
                    except: pdf.cell(0, 10, titolo)
                else: 
                    pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo.upper(), 0, 1, "C")
                
                for s in sezioni_totali:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper(), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 11)
                        pdf.multi_cell(0, 7, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                pdf.output("libro.pdf")
                with open("libro.pdf", "rb") as f_pdf: st.download_button("📥 Scarica PDF", f_pdf, file_name=f"{titolo}.pdf", use_container_width=True)
        
        with c2:
            if st.button("Genera WORD"):
                doc = Document()
                doc.add_heading(titolo, 0)
                doc.add_paragraph(f"Autore: {nome_a}")
                for s in sezioni_totali:
                    if s in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper(), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO(); doc.save(buf); buf.seek(0)
                st.download_button("📥 Scarica WORD", buf, file_name=f"{titolo}.docx", use_container_width=True)
