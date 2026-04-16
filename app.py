import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# 1. Connessione API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- PRIVACY, MOBILE E OTTIMIZZAZIONE INTERFACCIA ---
st.set_page_config(page_title="AI di Antonino", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
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
st.markdown(hide_st_style, unsafe_allow_html=True)

# CLASSE PDF PROFESSIONALE (Mostra solo il nome dell'autore)
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
    
    # Filtro anti-commenti IA (Italiano + Internazionale)
    linee = risposta.split('\n')
    linee_pulite = []
    tag_da_eliminare = [
        "ecco", "certamente", "spero", "di seguito", "questo è", "il capitolo", "ciao", "va bene", 
        "here is", "sure", "i hope", "voilà", "aquí está", "hier ist", "iată", "вот", "这里是"
    ]
    for l in linee:
        testo_l = l.strip().lower()
        if testo_l and not any(testo_l.startswith(p) for p in tag_da_eliminare):
            linee_pulite.append(l)
    return '\n'.join(linee_pulite).strip()

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- INTERFACCIA ---
st.title("AI di Antonino: \"Crea il tuo EBook\"")

with st.sidebar:
    st.header("Configurazione")
    titolo = st.text_input("Titolo Libro", "")
    autore = st.text_input("Nome Autore (per il PDF)", "")
    
    # LINGUE AGGIORNATE
    lingua = st.selectbox("Lingua / Language", [
        "Italiano", "English", "Deutsch", "Français", 
        "Español", "Română", "Русский", "中文 (Chinese)"
    ])
    
    modalita = st.selectbox("Modalità / Genre", [
        "Manuale Psicologico (Guida pratica e clinica)",
        "Thriller Psicologico (Analisi mentale e tensione)", 
        "Saggio Psicologico (Analitico e riflessivo)",
        "Manuale Tecnico (Pratico e chiaro)",
        "Noir (Cupo e descrittivo)", 
        "Thriller (Azione e suspense)",
        "Motivazionale (Ispirazione)",
        "Fantasy (Epico)",
        "Romanzo Storico",
        "Romanzo Rosa"
    ])
    trama = st.text_area("Trama o Argomento principale")
    
    st.markdown("---")
    if st.button("🔄 RICOMINCIA NUOVO EBOOK"):
        reset_app()

if trama:
    # SYSTEM PROMPT CON COERENZA E MULTILINGUA
    S_P = f"Sei un Ghostwriter esperto in {modalita}. Scrivi rigorosamente in lingua {lingua}. "
    S_P += f"Autore: {autore if autore else 'utente'}. "
    S_P += "REGOLE: Produci SOLO testo finale. NO saluti, NO commenti. "
    S_P += "COERENZA: Assicura che ogni parte sia legata logicamente a quanto scritto in precedenza."

    # Riferimento alla struttura per l'IA
    contesto_base = f"Titolo: {titolo}. Trama: {trama}. \n"
    if 'indice' in st.session_state:
        contesto_base += f"Indice di riferimento: {st.session_state['indice']}\n"

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Struttura", "🎨 Copertina AI", "✍️ Scrittura", "📝 Modifica", "📑 Esporta"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea l'indice dettagliato in {lingua} per: {titolo}. Trama: {trama}", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice", st.session_state['indice'], height=250)

    with tab2:
        if st.button("Genera Copertina"):
            with st.spinner("Creazione immagine..."):
                try:
                    prompt_img = f"Professional book cover for '{titolo}', genre: {modalita}, artistic style, no text."
                    res_img = client.images.generate(model="dall-e-3", prompt=prompt_img, n=1, size="1024x1792")
                    st.session_state['cover_url'] = res_img.data[0].url
                except Exception as e:
                    st.error(f"Errore: {e}")
        if 'cover_url' in st.session_state:
            st.image(st.session_state['cover_url'], use_container_width=True)

    with tab3:
        scelta = st.selectbox("Sezione", ["Prefazione", "Capitolo", "Ringraziamenti"])
        n_cap = st.number_input("N° Capitolo", 1, 30) if scelta == "Capitolo" else 0
        key_attuale = f"{scelta.lower()}_{n_cap}" if n_cap > 0 else scelta.lower()
        
        if st.button("Avvia Scrittura"):
            with st.spinner(f"Scrittura in {lingua}..."):
                # Recupero testi precedenti per coerenza
                testi_prec = "\n".join([st.session_state[k][:400] for k in st.session_state if "capitolo" in k or "prefazione" in k])
                prompt_full = f"{contesto_base}\nTesti già scritti: {testi_prec}\n\nScrivi la sezione completa: {scelta} {n_cap if n_cap>0 else ''}."
                
                testo_completo = ""
                for f in ["Inizio", "Sviluppo", "Conclusione"]:
                    testo_completo += chiedi_gpt(f"{prompt_full} - Parte: {f}", S_P) + "\n\n"
                st.session_state[key_attuale] = testo_completo
        
        if key_attuale in st.session_state:
            st.text_area("Testo Generato", st.session_state[key_attuale], height=350)

    with tab4:
        st.subheader("Modifica Strutturante")
        sez_mod = st.selectbox("Seleziona sezione", ["Prefazione", "Ringraziamenti"] + [f"Capitolo {i}" for i in range(1, 31)])
        k_mod = sez_mod.lower().replace(" ", "_")
        if k_mod in st.session_state:
            t_attuale = st.text_area("Testo attuale", st.session_state[k_mod], height=250)
            st.session_state[k_mod] = t_attuale
            istr = st.text_input(f"Richiesta di ristrutturazione in {lingua}")
            if st.button("Applica Ristrutturazione Profonda"):
                with st.spinner("Rielaborazione..."):
                    S_P_EDITOR = S_P + " Agisci come un Senior Editor. Ristruttura profondamente il testo."
                    st.session_state[k_mod] = chiedi_gpt(f"Riorganizza questo testo:\n{t_attuale}\nRichiesta: {istr}", S_P_EDITOR)
                    st.rerun()
        else:
            st.info("Genera prima questa sezione.")

    with tab5:
        st.subheader("Esportazione Finale")
        n_pdf = autore if autore else "Autore"
        sez_ordine = ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Crea PDF"):
                pdf = PDF(n_pdf)
                pdf.set_auto_page_break(True, 15)
                pdf.add_page()
                if 'cover_url' in st.session_state:
                    try:
                        img_data = requests.get(st.session_state['cover_url']).content
                        with open("c_temp.jpg", "wb") as f: f.write(img_data)
                        pdf.image("c_temp.jpg", 0, 0, 210, 297)
                    except:
                        pdf.set_font("Arial", "B", 25); pdf.cell(0, 100, titolo.upper(), 0, 1, "C")
                else:
                    pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo.upper(), 0, 1, "C")
                    pdf.set_font("Arial", "", 20); pdf.cell(0, 20, f"di {n_pdf}", 0, 1, "C")
                
                for s in sez_ordine:
                    if s in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper(), 0, 1, "L")
                        pdf.ln(10); pdf.set_font("Arial", "", 11)
                        pdf.multi_cell(0, 7, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                pdf.output("e.pdf")
                with open("e.pdf", "rb") as f:
                    st.download_button("📥 PDF", f, file_name=f"{titolo}.pdf", use_container_width=True)

        with col2:
            if st.button("Crea WORD"):
                doc = Document()
                doc.add_heading(titolo, 0)
                doc.add_paragraph(f"Autore: {n_pdf}")
                for s in sez_ordine:
                    if s in st.session_state:
                        doc.add_page_break()
                        doc.add_heading(s.upper(), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.download_button("📥 WORD", buf, file_name=f"{titolo}.docx", use_container_width=True)
