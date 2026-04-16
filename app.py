import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- CONNESSIONE API ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA (SIDEBAR SEMPRE APERTA) ---
st.set_page_config(
    page_title="AI di Antonino: Editor Ebook Mondiale",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS (UI PROFESSIONALE & SIDEBAR BLOCCATA) ---
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

.stButton>button:hover {
    background-color: #0056b3 !important; transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI CORE ---
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.75
        )
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Error: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    mappa = {}
    for l in testo.split('\n'):
        match = re.search(r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune)\s*\d+|^\d+\.', l)
        if match:
            cap_key = match.group(0).strip().title()
            descr = l.replace(match.group(0), "").strip(": -")
            mappa[cap_key] = descr if descr else "Approfondimento"
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- SIDEBAR (CONFIGURAZIONE COMPLETA) ---
with st.sidebar:
    st.title("⚙️ Configurazione Ebook")
    titolo_l = st.text_input("Titolo del Libro")
    autore_l = st.text_input("Nome Autore")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    
    # TUTTI I GENERI RIPRISTINATI
    genere = st.selectbox("Genere", [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Finanza", "Motivazionale / Self-Help", "Biografia", 
        "Libro di Quiz / Test", "Saggio Breve", "Romanzo Storico", 
        "Thriller", "Noir", "Fantasy", "Fantascienza"
    ])
    
    modalita = st.selectbox("Tipologia di Scrittura", ["Standard", "Professionale (Accademica/Tecnica)"])
    trama = st.text_area("Trama o Argomento Centrale", height=150)
    
    if st.button("🔄 RESET PROGETTO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- LOGICA DI SCRITTURA A 3 FASI ---
lingua_map = {
    "Italiano": ["Introduzione dettagliata", "Sviluppo centrale profondo", "Conclusione e analisi finale"],
    "English": ["Detailed Introduction", "Deep Central Development", "Final Analysis"],
    "Deutsch": ["Einleitung", "Zentrale Entwicklung", "Schlussfolgerung"],
    "Français": ["Introduction", "Développement", "Conclusion"],
    "Español": ["Introducción", "Desarrollo", "Conclusión"]
}
fasi = lingua_map.get(lingua, ["Part 1", "Part 2", "Part 3"])

# --- UI PRINCIPALE ---
st.markdown(f'<div class="custom-title">AI: {titolo_l if titolo_l else "Ebook Creator"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    livello = "estremamente tecnico e accademico" if modalita == "Professionale (Accademica/Tecnica)" else "chiaro e divulgativo"
    S_PROMPT = f"Autorità mondiale in {genere}. Scrivi in {lingua}. Stile: {livello}. Target: 2000+ parole per capitolo. Rigore assoluto."

    t1, t2, t3, t4 = st.tabs(["📊 Indice", "✍️ Scrittura & Quiz", "📖 Anteprima", "📑 Esporta"])

    with t1:
        if st.button("Genera Indice Professionale"):
            st.session_state["indice_raw"] = chiedi_gpt(f"Crea un indice lungo per un libro '{genere}' intitolato '{titolo_l}' in {lingua}.", "Editor.")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Modifica Indice", value=st.session_state.get("indice_raw", ""), height=300)
        if st.button("Sincronizza Capitoli"): sync_capitoli(); st.rerun()

    with t2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = ["Prefazione"] + st.session_state.get("lista_capitoli", []) + ["Ringraziamenti"]
        cap_sel = st.selectbox("Seleziona sezione:", opzioni)
        key_sez = f"txt_{cap_sel.replace(' ', '_')}"
        
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            if st.button(f"✨ SCRIVI: {cap_sel}"):
                with st.spinner("L'IA sta scrivendo 2000+ parole..."):
                    testo_completo = ""
                    for f in fasi:
                        testo_completo += chiedi_gpt(f"Scrivi la fase '{f}' per la sezione '{cap_sel}'. Sii prolisso e tecnico.", S_PROMPT) + "\n\n"
                    st.session_state[key_sez] = testo_completo
        with c2:
            istr = st.text_input("Istruzione modifica", key=f"istr_{key_sez}")
            if st.button("🚀 RIELABORA"):
                st.session_state[key_sez] = chiedi_gpt(f"Rielabora secondo: {istr}. Testo:\n{st.session_state.get(key_sez,'')}", S_PROMPT)
        with c3:
            if st.button("🧠 QUIZ"):
                prompt_q = f"Crea 10 quiz a risposta multipla su questo testo:\n{st.session_state.get(key_sez,'')}"
                st.session_state[f"quiz_{key_sez}"] = chiedi_gpt(prompt_q, "Esperto Quiz.")

        st.session_state[key_sez] = st.text_area("Editor Testo", value=st.session_state.get(key_sez, ""), height=450)
        if f"quiz_{key_sez}" in st.session_state:
            st.info(st.session_state[f"quiz_{key_sez}"])

    with t3:
        p_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: p_html += f"<h3 style='text-align:center;'>di {autore_l}</h3>"
        p_html += "<hr><br>"
        for s in opzioni:
            sk = f"txt_{s.replace(' ', '_')}"
            if sk in st.session_state:
                p_html += f"<h2>{s.upper()}</h2><p>{st.session_state[sk].replace('\\n', '<br>')}</p><br>"
        st.markdown(p_html + "</div>", unsafe_allow_html=True)

    with t4:
        # Codice export (PDF/Word) abbreviato per brevità ma funzionale
        st.write("Seleziona il formato per scaricare l'intero libro.")
        if st.button("Scarica Word"):
            doc = Document(); doc.add_heading(titolo_l, 0)
            for s in opzioni:
                sk = f"txt_{s.replace(' ', '_')}"
                if sk in st.session_state:
                    doc.add_heading(s, level=1); doc.add_paragraph(st.session_state[sk])
            buf = BytesIO(); doc.save(buf); buf.seek(0)
            st.download_button("Salva file .docx", buf, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Compila i dati nella sidebar a sinistra per iniziare.")
