import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- API ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIG PAGINA ---
st.set_page_config(
    page_title="AI di Antonino: Crea il tuo Ebook",
    layout="wide"
)

# --- CSS ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

section[data-testid="stSidebar"] {
    min-width: 350px !important;
    max-width: 350px !important;
}

.custom-title {
    font-size: 38px;
    font-weight: bold;
    text-align: center;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 15px;
    margin-bottom: 25px;
}
</style>
""", unsafe_allow_html=True)

# --- PDF ---
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore

    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- FUNZIONI ---

def pulisci_testo_ia(testo):
    tag_proibiti = ["ecco", "certamente", "sure", "here is"]
    linee = testo.split("\n")
    pulito = [l for l in linee if not any(l.lower().startswith(t) for t in tag_proibiti)]
    return "\n".join(pulito).strip()

def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore: {str(e)}"

def conta_parole(testo):
    return len(testo.split())

def salva_progetto():
    with open("progetto.json", "w") as f:
        json.dump(dict(st.session_state), f)

def carica_progetto():
    if os.path.exists("progetto.json"):
        with open("progetto.json", "r") as f:
            st.session_state.update(json.load(f))

def sync_capitoli():
    testo = st.session_state.get("indice", "")
    mappa = {}
    for riga in testo.split("\n"):
        match = re.search(r'Capitolo\s*\d+', riga, re.I)
        if match:
            key = match.group(0).title()
            descr = riga.replace(match.group(0), "").strip(": -")
            mappa[key] = descr if descr else "Approfondimento"
    if mappa:
        st.session_state["mappa_capitoli"] = mappa
        st.session_state["lista_capitoli"] = list(mappa.keys())

# --- UI ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Configurazione")

    titolo_l = st.text_input("Titolo")
    autore = st.text_input("Autore")
    lingua = st.selectbox("Lingua", ["Italiano", "English"])
    genere = st.selectbox("Genere", ["Manuale", "Romanzo", "Motivazionale"])
    trama = st.text_area("Trama")

    modalita = st.selectbox("Modalità", ["Standard", "Professionale"])

    if st.button("💾 Salva progetto"):
        salva_progetto()

    if st.button("📂 Carica progetto"):
        carica_progetto()
        st.rerun()

# --- PROMPT ---
if titolo_l and trama:

    livello = "molto dettagliato, approfondito e professionale" if modalita == "Professionale" else "chiaro e semplice"

    S_PROMPT = f"""
Sei un Ghostwriter professionista.

Scrivi in {lingua}.
Libro: {titolo_l}
Tema: {trama}

REGOLE:
- Scrittura {livello}
- Fluida e naturale
- Evita ripetizioni
- Paragrafi ben strutturati
- Stile umano e coinvolgente
"""

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Indice",
        "✍️ Scrittura",
        "🛠️ Riscrittura",
        "📑 Export"
    ])

    # --- INDICE ---
    with tab1:
        if st.button("Genera indice"):
            st.session_state["indice"] = chiedi_gpt(
                f"Crea indice libro '{titolo_l}'",
                "Esperto editoriale"
            )
            sync_capitoli()

        st.session_state["indice"] = st.text_area(
            "Indice",
            value=st.session_state.get("indice", "")
        )

        if st.button("Sincronizza"):
            sync_capitoli()

    # --- SCRITTURA ---
    with tab2:
        if "lista_capitoli" not in st.session_state:
            sync_capitoli()

        capitolo = st.selectbox(
            "Sezione",
            ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        )

        key = capitolo.lower().replace(" ", "_")

        if st.button("Genera contenuto"):
            testo = chiedi_gpt(
                f"Scrivi un capitolo completo '{capitolo}'",
                S_PROMPT
            )
            st.session_state[key] = testo

        if key in st.session_state:
            testo = st.text_area("Testo", st.session_state[key], height=300)
            st.session_state[key] = testo

            st.info(f"Parole: {conta_parole(testo)}")

    # --- RISCRITTURA ---
    with tab3:
        capitolo = st.selectbox("Sezione da riscrivere", st.session_state.get("lista_capitoli", []))
        key = capitolo.lower().replace(" ", "_")

        if key in st.session_state:
            istr = st.text_input("Istruzioni")

            if st.button("Riscrivi"):
                nuovo = chiedi_gpt(
                    f"Riscrivi completamente:\n{st.session_state[key]}\nIstruzioni: {istr}",
                    "Editor professionista"
                )
                st.session_state[key] = nuovo
                st.rerun()

    # --- EXPORT ---
    with tab4:
        if st.button("PDF"):
            pdf = PDF(autore)
            pdf.add_page()
            pdf.set_font("Arial", "B", 24)
            pdf.cell(0, 20, titolo_l, 0, 1, "C")

            for k, v in st.session_state.items():
                if isinstance(v, str):
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, k.upper(), 0, 1)
                    pdf.set_font("Arial", "", 12)
                    pdf.multi_cell(0, 8, v)

            st.download_button("Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name="ebook.pdf")

        if st.button("Word"):
            doc = Document()
            doc.add_heading(titolo_l, 0)

            for k, v in st.session_state.items():
                if isinstance(v, str):
                    doc.add_heading(k, level=1)
                    doc.add_paragraph(v)

            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)

            st.download_button("Scarica Word", buf, file_name="ebook.docx")
