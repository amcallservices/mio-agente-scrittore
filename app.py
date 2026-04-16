import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- CONNESSIONE API ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="AI di Antonino: Ebook & Quiz Professionale",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS (UI PROFESSIONALE) ---
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

section[data-testid="stSidebar"] {
    min-width: 380px !important;
    max-width: 380px !important;
}

.custom-title {
    font-size: 38px; font-weight: bold; color: #1E1E1E; text-align: center;
    padding: 20px; background-color: #f0f4f8; border-radius: 15px;
    margin-bottom: 25px; border: 1px solid #d1d9e6;
}

.preview-box {
    background-color: white; padding: 50px; border: 1px solid #d3d6db;
    border-radius: 10px; height: 700px; overflow-y: scroll;
    font-family: 'Times New Roman', serif; line-height: 1.8; color: #222;
}

.stButton>button {
    width: 100%; border-radius: 10px; height: 3.8em; font-weight: bold;
    background-color: #007BFF !important; color: white !important;
    font-size: 16px; border: none; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI CORE ---
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Error: {str(e)}"

def sync_capitoli():
    testo_indice = st.session_state.get("indice_raw", "")
    if not testo_indice:
        st.session_state['lista_capitoli'] = []
        return
    linee = testo_indice.split('\n')
    capitoli_trovati = []
    for l in linee:
        l = l.strip()
        if re.search(r'^(Capitolo|Chapter|Cap\.|Parte|\d+\.)', l, re.IGNORECASE):
            capitoli_trovati.append(l)
    st.session_state['lista_capitoli'] = capitoli_trovati

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")
    titolo_l = st.text_input("Titolo del Libro")
    autore_l = st.text_input("Nome Autore")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere", [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Finanza", "Motivazionale / Self-Help", "Libro di Quiz", 
        "Romanzo Storico", "Thriller", "Noir", "Fantasy", "Fantascienza"
    ])
    modalita = st.selectbox("Stile", ["Standard", "Professionale Accademico"])
    trama = st.text_area("Trama/Argomento", height=150)
    
    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- UI PRINCIPALE ---
st.markdown(f'<div class="custom-title">Editor Ebook & Quiz di Antonino</div>', unsafe_allow_html=True)

if titolo_l and trama:
    S_PROMPT = f"Esperto mondiale in {genere}. Scrittura in {lingua}. Stile: {modalita}. Obiettivo: 2000+ parole e coerenza logica."

    t1, t2, t3, t4 = st.tabs(["📊 1. Indice", "✍️ 2. Scrittura & Quiz", "📖 3. Anteprima", "📑 4. Esporta"])

    with t1:
        if st.button("🚀 GENERA INDICE"):
            prompt_idx = f"Crea un indice professionale per un libro su '{titolo_l}'. Argomento: {trama}. Lingua: {lingua}."
            st.session_state["indice_raw"] = chiedi_gpt(prompt_idx, "Editor professionale.")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Modifica Indice:", value=st.session_state.get("indice_raw", ""), height=350)
        if st.button("✅ SALVA E SINCRONIZZA"):
            sync_capitoli()
            st.success("Capitoli sincronizzati correttamente!")

    with t2:
        lista_c = st.session_state.get("lista_capitoli", [])
        if not lista_c:
            st.warning("Genera e salva l'indice nella Tab 1 prima di procedere.")
        else:
            opzioni = ["Prefazione"] + lista_c + ["Ringraziamenti"]
            cap_sel = st.selectbox("Seleziona sezione:", opzioni)
            key_sez = f"txt_{cap_sel.replace(' ', '_')}"
            key_quiz = f"quiz_{cap_sel.replace(' ', '_')}"

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"✨ SCRIVI: {cap_sel}"):
                    with st.spinner("Generazione testo (Target 2000+ parole)..."):
                        contesto = f"Indice: {st.session_state['indice_raw']}. Capitolo attuale: {cap_sel}."
                        testo = ""
                        for fase in ["Inizio", "Corpo", "Fine"]:
                            testo += chiedi_gpt(f"{contesto}\nScrivi la parte: {fase}.", S_PROMPT) + "\n\n"
                        st.session_state[key_sez] = testo
            
            with col_b:
                if st.button("🧠 GENERA TEST/QUIZ"):
                    if key_sez in st.session_state and st.session_state[key_sez]:
                        with st.spinner("Creazione test in corso..."):
                            prompt_q = f"Basandoti sul testo di '{cap_sel}', genera un quiz di 10 domande a risposta multipla con soluzioni.\n\nTesto:\n{st.session_state[key_sez]}"
                            st.session_state[key_quiz] = chiedi_gpt(prompt_q, "Esperto in creazione test.")
                    else:
                        st.error("Genera prima il testo del capitolo!")

            st.session_state[key_sez] = st.text_area("Editor Capitolo:", value=st.session_state.get(key_sez, ""), height=400)
            
            if key_quiz in st.session_state:
                st.markdown("---")
                st.subheader(f"📝 Quiz per: {cap_sel}")
                st.write(st.session_state[key_quiz])

    with t3:
        preview = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l}</h1>"
        if autore_l: preview += f"<h3 style='text-align:center;'>di {autore_l}</h3>"
        preview += "<hr><br>"
        for s in ["Prefazione"] + lista_c + ["Ringraziamenti"]:
            sk = f"txt_{s.replace(' ', '_')}"
            if sk in st.session_state and st.session_state[sk]:
                preview += f"<h2>{s}</h2><p>{st.session_state[sk].replace('\\n', '<br>')}</p><br>"
        st.markdown(preview + "</div>", unsafe_allow_html=True)

    with t4:
        if st.button("Scarica file Word (.docx)"):
            doc = Document()
            doc.add_heading(titolo_l, 0)
            for s in ["Prefazione"] + lista_c + ["Ringraziamenti"]:
                sk = f"txt_{s.replace(' ', '_')}"
                if sk in st.session_state:
                    doc.add_heading(s, level=1)
                    doc.add_paragraph(st.session_state[sk])
            buf = BytesIO(); doc.save(buf); buf.seek(0)
            st.download_button("Salva Ebook", buf, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Inserisci Titolo e Trama a sinistra per iniziare.")
