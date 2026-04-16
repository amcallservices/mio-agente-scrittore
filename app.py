import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI

# 1. Configurazione API
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- OTTIMIZZAZIONE MOBILE E PRIVACY ---
st.set_page_config(page_title="AI di Antonino", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* Ottimizzazione Mobile: Pulsanti più grandi e margini ridotti */
            .stButton>button {
                width: 100%;
                border-radius: 10px;
                height: 3em;
                background-color: #f0f2f6;
            }
            .stTextArea textarea {
                font-size: 16px !important;
            }
            /* Rende i Tabs più leggibili su schermi piccoli */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                font-size: 14px;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# CLASSE PDF PROFESSIONALE (Solo Autore)
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
    tag_da_eliminare = ["ecco", "certamente", "spero", "di seguito", "questo è", "il capitolo", "ciao", "va bene", "perfetto", "fammi sapere"]
    for l in linee:
        testo_l = l.strip().lower()
        if testo_l and not any(testo_l.startswith(p) for p in tag_da_eliminare):
            linee_pulite.append(l)
    testo_finale = '\n'.join(linee_pulite).strip()
    testo_finale = re.sub(r"(?i)(spero che|fammi sapere se|ecco il testo|buona scrittura|fammi sapere cosa|spero sia utile).*$", "", testo_finale).strip()
    return testo_finale

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- INTERFACCIA ---
st.title("AI di Antonino: \"Crea il tuo EBook\"")

with st.sidebar:
    st.header("Configurazione")
    titolo = st.text_input("Titolo Libro", "")
    autore = st.text_input("Inserisci il tuo nome (Autore)", "")
    
    modalita = st.selectbox("Modalità di scrittura", [
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
    trama = st.text_area("Trama/Argomento")
    st.markdown("---")
    if st.button("🔄 RICOMINCIA NUOVO"):
        reset_app()

if trama:
    S_P = f"Sei un Ghostwriter esperto in {modalita}. Scrivi per l'autore {autore if autore else 'utente'}. "
    S_P += "REGOLE: Produci SOLO testo narrativo. NON aggiungere introduzioni o saluti. Inizia e finisci SOLO con il contenuto."

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Struttura", "🎨 Copertina", "✍️ Scrittura", "📝 Modifica", "📑 Esporta"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea l'indice per il libro '{titolo}'. Trama: {trama}", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice", st.session_state['indice'], height=250)

    with tab2:
        if st.button("Genera Copertina"):
            with st.spinner("Creazione..."):
                try:
                    prompt_img = f"Professional book cover for '{titolo}', style: {modalita}, no text."
                    res_img = client.images.generate(model="dall-e-3", prompt=prompt_img, n=1, size="1024x1792")
                    st.session_state['cover_url'] = res_img.data[0].url
                except Exception as e:
                    st.error(f"Errore: {e}")
        if 'cover_url' in st.session_state:
            st.image(st.session_state['cover_url'], use_container_width=True)

    with tab3:
        scelta = st.selectbox("Sezione", ["Prefazione", "Capitolo", "Ringraziamenti"])
        n_cap = st.number_input("N°", 1, 30) if scelta == "Capitolo" else 0
        key_attuale = f"{scelta.lower()}_{n_cap}" if n_cap > 0 else scelta.lower()
        if st.button("Avvia Scrittura"):
            with st.spinner("In corso..."):
                testo_completo = ""
                for f in ["Inizio", "Centro", "Fine"]:
                    testo_completo += chiedi_gpt(f"Scrivi la parte {f} di {scelta} {n_cap if n_cap>0 else ''}.", S_P) + "\n\n"
                st.session_state[key_attuale] = testo_completo
        if key_attuale in st.session_state:
            st.text_area("Testo", st.session_state[key_attuale], height=350)

    with tab4:
        st.subheader("Editor Strutturante")
        sezione_mod = st.selectbox("Cosa modificare?", ["Prefazione", "Ringraziamenti"] + [f"Capitolo {i}" for i in range(1, 31)])
        chiave_mod = sezione_mod.lower().replace(" ", "_")
        if chiave_mod in st.session_state:
            testo_in = st.text_area("Contenuto", st.session_state[chiave_mod], height=250)
            st.session_state[chiave_mod] = testo_in
            istr = st.text_input("Istruzione Editor")
            if st.button("Applica Ristrutturazione"):
                with st.spinner("Rielaborazione..."):
                    S_P_MOD = S_P + " Agisci come Senior Editor. Ristruttura profondamente."
                    st.session_state[chiave_mod] = chiedi_gpt(f"Originale:\n{testo_in}\nRichiesta: {istr}", S_P_MOD)
                    st.rerun()
        else:
            st.info("Genera prima la sezione.")

    with tab5:
        if st.button("Crea PDF"):
            nome_p = autore if autore else "Autore"
            pdf = PDF(nome_p)
            pdf.set_auto_page_break(True, 15)
            pdf.add_page()
            if 'cover_url' in st.session_state:
                try:
                    img_data = requests.get(st.session_state['cover_url']).content
                    with open("cover_temp.jpg", "wb") as f: f.write(img_data)
                    pdf.image("cover_temp.jpg", 0, 0, 210, 297)
                except:
                    pdf.set_font("Arial", "B", 25); pdf.cell(0, 100, titolo.upper(), 0, 1, "C")
            else:
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo.upper(), 0, 1, "C")
                pdf.set_font("Arial", "", 20); pdf.cell(0, 20, f"di {nome_p}", 0, 1, "C")
            for s in ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]:
                if s in st.session_state:
                    pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper(), 0, 1, "L")
                    pdf.ln(10); pdf.set_font("Arial", "", 11)
                    pdf.multi_cell(0, 7, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
            pdf.output("ebook.pdf")
            with open("ebook.pdf", "rb") as f:
                st.download_button("📥 SCARICA PDF", f, file_name=f"{titolo}.pdf", use_container_width=True)
