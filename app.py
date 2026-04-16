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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
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

# --- PDF ---
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore

    def header(self):
        if self.page_no() > 1 and self.autore:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Autore: {self.autore}", 0, 0, 'C')
            self.ln(10)

# --- FUNZIONI ---
def pulisci_testo_ia(testo):
    tag_proibiti = ["ecco", "certamente", "spero", "ciao", "inizio", "sviluppo", "fine", "fase", "parte", "here is", "sure"]
    linee = testo.split("\n")
    pulito = [l for l in linee if not any(l.lower().startswith(t) for t in tag_proibiti)]
    return "\n".join(pulito).strip()

def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        return pulisci_testo_ia(response.choices[0].message.content)
    except Exception as e:
        return f"Errore: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice", "")
    mappa = {}
    for riga in testo.split("\n"):
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.)', riga)
        if match:
            key = match.group(0).strip().title()
            descr = riga.replace(match.group(0), "").strip(": -")
            mappa[key] = descr if descr else "Approfondimento"
    st.session_state["mappa_capitoli"] = mappa
    st.session_state["lista_capitoli"] = list(mappa.keys())

# --- UI HEADER ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")
    titolo_l = st.text_input("Titolo del Libro")
    autore = st.text_input("Nome Autore", value="")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere", ["Manuale Tecnico", "Manuale Psicologico", "Saggio", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    trama = st.text_area("Trama e Argomento Centrale", height=150)
    
    if st.button("🔄 RESET TOTALE"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- LOGICA ---
if titolo_l and trama:
    S_PROMPT = f"Sei un Ghostwriter professionista esperto in {genere}. Scrivi in {lingua}. Titolo: {titolo_l}. Trama: {trama}. REGOLE: Coerenza logica, niente ripetizioni, stile fluido."

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "🛠️ 3. Rielaborazione", "📑 4. Esportazione"])

    # --- 1. INDICE ---
    with tab1:
        if st.button("Genera Indice"):
            st.session_state["indice"] = chiedi_gpt(f"Crea indice per '{titolo_l}': {trama}", "Editor esperto.")
            sync_capitoli()
        
        # Modifica manuale dell'indice
        st.session_state["indice"] = st.text_area("Indice (Modificabile)", value=st.session_state.get("indice", ""), height=300)
        
        if st.button("Sincronizza"):
            sync_capitoli()
            st.rerun()

    if "lista_capitoli" not in st.session_state: sync_capitoli()

    # --- 2. SCRITTURA ---
    with tab2:
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        cap_sel = st.selectbox("Seleziona sezione", opzioni)
        key_sez = cap_sel.lower().replace(" ", "_").replace(".", "")

        if st.button(f"Genera {cap_sel}"):
            with st.spinner("Scrittura..."):
                arg = st.session_state.get("mappa_capitoli", {}).get(cap_sel, "")
                testo_ia = ""
                for fase in ["Inizio", "Sviluppo", "Fine"]:
                    testo_ia += chiedi_gpt(f"Scrivi {cap_sel} ({fase}). Argomento: {arg}", S_PROMPT) + "\n\n"
                st.session_state[key_sez] = testo_ia

        # EDIT MANUALE: Il testo nell'area aggiorna direttamente il session_state
        if key_sez in st.session_state:
            st.session_state[key_sez] = st.text_area("Testo della sezione (Modifica qui liberamente)", value=st.session_state[key_sez], height=450)

    # --- 3. RIELABORAZIONE ---
    with tab3:
        cap_rifare = st.selectbox("Sezione da rielaborare", opzioni)
        key_rifare = cap_rifare.lower().replace(" ", "_").replace(".", "")

        if key_rifare in st.session_state:
            # Versioning della chiave per forzare il refresh dopo il comando IA
            if f"ver_{key_rifare}" not in st.session_state: st.session_state[f"ver_{key_rifare}"] = 0
            
            istr = st.text_area("Istruzioni di rielaborazione", placeholder="Esempio: 'Usa il tu invece del voi', 'Rendilo più professionale'...")
            
            # Area di testo dinamica
            testo_attuale = st.text_area("Testo attuale", value=st.session_state[key_rifare], height=300, key=f"area_m_{key_rifare}_{st.session_state[f'ver_{key_rifare}']}")
            
            if st.button("🚀 APPLICA RIELABORAZIONE"):
                with st.spinner("Rielaborazione..."):
                    # Salviamo prima quello che l'utente ha scritto manualmente nel box
                    st.session_state[key_rifare] = testo_attuale
                    
                    p_riel = f"RIELABORA COMPLETAMENTE: {istr}. Testo originale:\n{testo_attuale}"
                    st.session_state[key_rifare] = chiedi_gpt(p_riel, S_PROMPT + " Editor Senior.")
                    st.session_state[f"ver_{key_rifare}"] += 1
                    st.rerun()
        else:
            st.info("Genera prima il testo nella scheda Scrittura.")

    # --- 4. EXPORT ---
    with tab4:
        col1, col2 = st.columns(2)
        lista_f = ["prefazione"] + [c.lower().replace(" ", "_").replace(".", "") for c in st.session_state.get("lista_capitoli", [])] + ["ringraziamenti"]
        
        with col1:
            if st.button("Esporta PDF"):
                pdf = PDF(autore)
                pdf.set_auto_page_break(True, 15)
                pdf.add_page()
                pdf.set_font("Arial", "B", 30)
                pdf.ln(80)
                pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in lista_f:
                    if s in st.session_state:
                        pdf.add_page()
                        pdf.set_font("Arial", "B", 18)
                        pdf.cell(0, 10, s.upper().replace("_", " "), 0, 1, "L")
                        pdf.ln(10)
                        pdf.set_font("Arial", "", 12)
                        pdf.multi_cell(0, 8, st.session_state[s].encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Scarica PDF", pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")

        with col2:
            if st.button("Esporta Word"):
                doc = Document()
                doc.add_heading(titolo_l, 0)
                for s in lista_f:
                    if s in st.session_state:
                        doc.add_page_break()
                        doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])
                buf = BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.download_button("📥 Scarica Word", buf, file_name=f"{titolo_l}.docx")
