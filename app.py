import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- CONNESSIONE API ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA (SIDEBAR FISSA) ---
st.set_page_config(
    page_title="AI di Antonino: Editor Ebook Professionale",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLOCCO CSS (UI & SIDEBAR) ---
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
    """Estrae i capitoli dall'area di testo dell'indice e li mette nel selettore di scrittura"""
    testo_indice = st.session_state.get("indice_raw", "")
    if not testo_indice:
        st.session_state['lista_capitoli'] = []
        return

    # Trova linee che iniziano con numeri o parole chiave capitolo
    linee = testo_indice.split('\n')
    capitoli_trovati = []
    for l in linee:
        l = l.strip()
        # Regex per catturare "Capitolo X: Titolo" o "1. Titolo"
        if re.search(r'^(Capitolo|Chapter|Cap\.|Parte|\d+\.)', l, re.IGNORECASE):
            capitoli_trovati.append(l)
    
    st.session_state['lista_capitoli'] = capitoli_trovati

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurazione")
    titolo_l = st.text_input("Titolo del Libro", key="tit_input")
    autore_l = st.text_input("Nome Autore")
    lingua = st.selectbox("Lingua", ["Italiano", "English", "Deutsch", "Français", "Español", "Română", "Русский", "中文"])
    genere = st.selectbox("Genere", [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Finanza", "Motivazionale / Self-Help", "Libro di Quiz", 
        "Romanzo Storico", "Thriller", "Fantasy", "Fantascienza"
    ])
    modalita = st.selectbox("Stile", ["Standard", "Professionale Accademico"])
    trama = st.text_area("Trama/Argomento", height=150)
    
    if st.button("🔄 RESET"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- UI PRINCIPALE ---
st.markdown(f'<div class="custom-title">Editor AI di Antonino</div>', unsafe_allow_html=True)

if titolo_l and trama:
    # System Prompt per il filo logico
    S_PROMPT = f"Sei un autore esperto di {genere}. Scrivi in {lingua}. Stile: {modalita}. Obiettivo: coerenza totale tra i capitoli e 2000+ parole."

    t1, t2, t3, t4 = st.tabs(["📊 1. Genera Indice", "✍️ 2. Scrittura Coerente", "📖 3. Anteprima", "📑 4. Esporta"])

    with t1:
        st.subheader("Fase 1: Definizione dell'Indice")
        if st.button("🚀 GENERA INDICE AUTOMATICO"):
            prompt_indice = f"Crea un indice dettagliato e logico per un libro intitolato '{titolo_l}'. Argomento: {trama}. Lingua: {lingua}. Usa il formato 'Capitolo X: Titolo'."
            st.session_state["indice_raw"] = chiedi_gpt(prompt_indice, "Editor di ebook professionale.")
            sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area("Modifica il tuo Indice qui (una riga per capitolo):", 
                                                    value=st.session_state.get("indice_raw", ""), height=350)
        
        if st.button("✅ SALVA E SINCRONIZZA CAPITOLI"):
            sync_capitoli()
            st.success(f"Sincronizzati {len(st.session_state.get('lista_capitoli', []))} capitoli!")

    with t2:
        st.subheader("Fase 2: Scrittura con Filo Logico")
        lista_c = st.session_state.get("lista_capitoli", [])
        
        if not lista_c:
            st.warning("Torna nella Tab 1 e genera/salva l'indice prima di scrivere.")
        else:
            opzioni_scrittura = ["Prefazione"] + lista_c + ["Ringraziamenti"]
            cap_sel = st.selectbox("Seleziona cosa scrivere:", opzioni_scrittura)
            key_sez = f"txt_{cap_sel.replace(' ', '_')}"

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"✨ SCRIVI: {cap_sel}"):
                    with st.spinner("Scrittura in corso... Sto analizzando l'indice per mantenere il filo logico."):
                        # Recupero contesto per il filo logico
                        contesto_indice = st.session_state["indice_raw"]
                        prompt_scrittura = f"""
                        L'indice completo del libro è: {contesto_indice}.
                        Ora scrivi il capitolo: '{cap_sel}'.
                        Assicurati che si colleghi logicamente ai capitoli precedenti e che prepari il terreno per i successivi.
                        Scrivi almeno 2000 parole in modo tecnico e approfondito.
                        """
                        # Generazione in 3 blocchi per lunghezza
                        testo = ""
                        for fase in ["Inizio", "Corpo Centrale", "Conclusione"]:
                            testo += chiedi_gpt(f"{prompt_scrittura}. Parte: {fase}.", S_PROMPT) + "\n\n"
                        st.session_state[key_sez] = testo

            with col_b:
                if st.button("🧠 GENERA QUIZ / TEST"):
                    if key_sez in st.session_state:
                        prompt_q = f"Basandoti su questo testo, crea 10 domande a risposta multipla con soluzione:\n{st.session_state[key_sez]}"
                        st.session_state[f"quiz_{key_sez}"] = chiedi_gpt(prompt_q, "Esperto Quiz.")

            st.session_state[key_sez] = st.text_area("Contenuto Capitolo", value=st.session_state.get(key_sez, ""), height=450)
            if f"quiz_{key_sez}" in st.session_state:
                st.info(st.session_state[f"quiz_{key_sez}"])

    with t3:
        st.subheader("📖 Anteprima Libro")
        preview = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l}</h1>"
        for s in ["Prefazione"] + lista_c + ["Ringraziamenti"]:
            sk = f"txt_{s.replace(' ', '_')}"
            if sk in st.session_state and st.session_state[sk]:
                preview += f"<h2>{s}</h2><p>{st.session_state[sk].replace('\\n', '<br>')}</p><br>"
        st.markdown(preview + "</div>", unsafe_allow_html=True)

    with t4:
        st.subheader("📑 Esporta il tuo lavoro")
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
    st.info("👋 Inserisci Titolo e Trama nella sidebar per attivare l'indice e la scrittura.")
