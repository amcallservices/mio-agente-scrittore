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

# --- CSS (UI PULITA E TITOLO VISIBILE) ---
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

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

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

def conta_parole(testo):
    return len(testo.split())

def sync_capitoli():
    testo = st.session_state.get("indice", "")
    mappa = {}
    for riga in testo.split("\n"):
        match = re.search(r'(?i)(Capitolo\s*\d+|Cap\.\s*\d+|\d+\.)', riga)
        if match:
            key = match.group(0).strip().title()
            descr = riga.replace(match.group(0), "").strip(": -")
            mappa[key] = descr if descr else "Approfondimento tematico"
    if mappa:
        st.session_state["mappa_capitoli"] = mappa
        st.session_state["lista_capitoli"] = list(mappa.keys())

# --- UI HEADER ---
st.markdown('<div class="custom-title">AI di Antonino: Crea il tuo Ebook</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")

    titolo_l = st.text_input("Titolo del Libro", placeholder="Inserisci il titolo...")
    autore = st.text_input("Nome Autore", value="") # Vuoto come richiesto
    
    # RIPRISTINO LINGUE
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    
    # RIPRISTINO GENERI
    genere = st.selectbox("Genere", ["Manuale Tecnico", "Manuale Psicologico", "Saggio", "Motivazionale", "Thriller", "Noir", "Fantasy", "Romanzo Rosa"])
    
    trama = st.text_area("Trama e Argomento Centrale", height=150)
    modalita_scrittura = st.selectbox("Livello di dettaglio", ["Standard", "Professionale"])

    st.markdown("---")
    if st.button("🔄 RESET TOTALE"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- LOGICA OPERATIVA ---
if titolo_l and trama:

    livello = "estremamente dettagliato, tecnico e approfondito" if modalita_scrittura == "Professionale" else "chiaro, fluido e semplice"

    S_PROMPT = f"""
Sei un Ghostwriter professionista esperto in {genere}.
Scrivi in {lingua}.
Titolo: {titolo_l}
Trama Centrale: {trama}

REGOLE MANDATORIE:
- Scrittura {livello}
- Evita assolutamente ripetizioni e ridondanze.
- Mantieni un filo logico ferreo tra i capitoli.
- Solo testo del libro, no commenti o saluti.
"""

    tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura", "🛠️ 3. Rielaborazione", "📑 4. Esportazione"])

    # --- TAB 1: INDICE ---
    with tab1:
        if st.button("Genera Indice Logico"):
            st.session_state["indice"] = chiedi_gpt(
                f"Crea un indice coerente per il libro '{titolo_l}' basato sulla trama: {trama}. Usa 'Capitolo X: Titolo'.",
                "Editor esperto in pianificazione editoriale."
            )
            sync_capitoli()

        if "indice" not in st.session_state:
            st.session_state["indice"] = "Capitolo 1: Introduzione"

        st.session_state["indice"] = st.text_area("Modifica Indice:", value=st.session_state["indice"], height=300)

        if st.button("Sincronizza Capitoli"):
            sync_capitoli()
            st.success("Sincronizzazione completata!")

    # --- TAB 2: SCRITTURA ---
    with tab2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        capitolo_sel = st.selectbox("Seleziona sezione da scrivere", opzioni)
        key_sez = capitolo_sel.lower().replace(" ", "_").replace(".", "")

        if st.button(f"Genera contenuto {capitolo_sel}"):
            with st.spinner("L'IA sta scrivendo..."):
                arg_specifico = st.session_state.get("mappa_capitoli", {}).get(capitolo_sel, "")
                testo_completo = ""
                for fase in ["Incipit", "Sviluppo centrale", "Conclusione"]:
                    testo_completo += chiedi_gpt(f"Scrivi {capitolo_sel} (Fase: {fase}). Argomento: {arg_specifico}", S_PROMPT) + "\n\n"
                st.session_state[key_sez] = testo_completo

        if key_sez in st.session_state:
            st.session_state[key_sez] = st.text_area("Contenuto Sezione:", st.session_state[key_sez], height=400, key=f"edit_{key_sez}")
            st.info(f"Conteggio parole: {conta_parole(st.session_state[key_sez])}")

    # --- TAB 3: RIELABORAZIONE (MIGLIORATA) ---
    with tab3:
        st.subheader("🛠️ Rielaborazione Totale")
        cap_da_rifare = st.selectbox("Sezione da rielaborare", opzioni)
        key_rifare = cap_da_rifare.lower().replace(" ", "_").replace(".", "")

        if key_rifare in st.session_state:
            if f"ver_{key_rifare}" not in st.session_state: st.session_state[f"ver_{key_rifare}"] = 0
            
            istr = st.text_area("Cosa vuoi cambiare? (es. 'Passa dal Voi al Tu', 'Riscrivi da zero in modo più cupo')", height=100)
            
            # Area di testo con chiave dinamica per forzare l'aggiornamento grafico
            testo_attuale = st.text_area("Testo attuale:", value=st.session_state[key_rifare], height=300, key=f"area_m_{key_rifare}_{st.session_state[f'ver_{key_rifare}']}")

            if st.button("🚀 APPLICA RIELABORAZIONE"):
                with st.spinner("Rielaborazione integrale in corso..."):
                    prompt_rielabora = f"""
ORDINE PRIORITARIO: Rielabora e riscrivi COMPLETAMENTE il testo seguente.
ISTRUZIONE UTENTE: {istr if istr else 'Riscrivi in modo totalmente nuovo e originale.'}
FOCUS LIBRO: {titolo_l}

TESTO DA RISCRIVERE:
{testo_attuale}
"""
                    nuovo_testo = chiedi_gpt(prompt_rielabora, S_PROMPT + " Editor Senior: Rewrite Totale.")
                    st.session_state[key_rifare] = nuovo_testo
                    st.session_state[f"ver_{key_rifare}"] += 1
                    st.rerun()
        else:
            st.info("Genera prima il testo nella scheda 'Scrittura'.")

    # --- TAB 4: EXPORT ---
    with tab4:
        col1, col2 = st.columns(2)
        lista_finale = ["prefazione"] + [c.lower().replace(" ", "_").replace(".", "") for c in st.session_state.get("lista_capitoli", [])] + ["ringraziamenti"]
        
        with col1:
            if st.button("Esporta PDF"):
                pdf = PDF(autore)
                pdf.set_auto_page_break(True, 15)
                pdf.add_page()
                pdf.set_font("Arial", "B", 30)
                pdf.ln(80)
                pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                if autore:
                    pdf.set_font("Arial", "", 20)
                    pdf.cell(0, 20, f"di {autore}", 0, 1, "C")
                
                for s in lista_finale:
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
                if autore: doc.add_paragraph(f"Autore: {autore}")

                for s in lista_finale:
                    if s in st.session_state:
                        doc.add_page_break()
                        doc.add_heading(s.upper().replace("_", " "), level=1)
                        doc.add_paragraph(st.session_state[s])

                buf = BytesIO()
                doc.save(buf)
                buf.seek(0)
                st.download_button("📥 Scarica Word", buf, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Benvenuto! Inserisci il Titolo e la Trama nella barra laterale per iniziare.")
