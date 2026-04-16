import streamlit as st
import os
import requests
import re
import json
import time
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# ======================================================================================================================
# 1. SETUP INIZIALE E CONNESSIONE API
# ======================================================================================================================
# Inizializzazione del client OpenAI utilizzando i secrets di Streamlit.
# Questa architettura garantisce che la chiave API non sia mai esposta nel codice sorgente.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("ERRORE CRITICO: La chiave API OpenAI non è configurata correttamente nei Secrets di Streamlit.")

# Configurazione della pagina Streamlit: Layout Wide e Sidebar Espansa (Richiesta specifica Antonino)
st.set_page_config(
    page_title="AI di Antonino: Ebook Mondiale Creator PRO",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📚"
)

# ======================================================================================================================
# 2. DIZIONARIO MULTILINGUA INTEGRALE (8 LINGUE)
# ======================================================================================================================
# Il sistema traduce dinamicamente l'intera interfaccia utente in base alla selezione della lingua nella sidebar.
TRADUZIONI = {
    "Italiano": {
        "side_tit": "⚙️ Configurazione Editor",
        "lbl_tit": "Titolo del Libro", "lbl_auth": "Nome Autore", "lbl_lang": "Lingua del Libro", 
        "lbl_gen": "Genere Letterario/Tecnico", "lbl_style": "Tipologia di Scrittura", "lbl_plot": "Trama o Argomento Centrale",
        "btn_res": "🔄 RESET TOTALE PROGETTO", "tabs": ["📊 1. Indice", "✍️ 2. Scrittura & Quiz", "📖 3. Anteprima", "📑 4. Esporta"],
        "btn_idx": "🚀 Genera Indice Professionale", "btn_sync": "✅ Salva e Sincronizza Capitoli",
        "lbl_sec": "Seleziona sezione su cui lavorare:", "btn_write": "✨ SCRIVI SEZIONE (2000+ parole)",
        "btn_quiz": "🧠 AGGIUNGI QUIZ AL LIBRO", "btn_edit": "🚀 RIELABORA CON IA",
        "msg_run": "L'autorità mondiale sta elaborando il contenuto...", "preface": "Prefazione", "ack": "Ringraziamenti",
        "preview_tit": "📖 Vista Lettura Professionale", "btn_word": "📥 Scarica in Word (.docx)", "btn_pdf": "📥 Scarica in PDF (.pdf)",
        "msg_err_idx": "Devi generare l'indice nella Tab 1 prima di procedere alla scrittura.", 
        "msg_success_sync": "Capitoli sincronizzati con successo nell'editor!",
        "label_editor": "Editor di Testo Professionale (Modifiche Manuali)",
        "label_quiz_gen": "Quiz generato basato sul capitolo selezionato",
        "welcome": "👋 Benvenuto nell'Ebook Creator di Antonino.",
        "guide": "Configura la sidebar a sinistra per sbloccare le funzioni IA."
    },
    "English": {
        "side_tit": "⚙️ Editor Setup",
        "lbl_tit": "Book Title", "lbl_auth": "Author Name", "lbl_lang": "Language", 
        "lbl_gen": "Genre", "lbl_style": "Writing Style", "lbl_plot": "Plot or Main Topic",
        "btn_res": "🔄 FULL PROJECT RESET", "tabs": ["📊 1. Index", "✍️ 2. Writing & Quiz", "📖 3. Preview", "📑 4. Export"],
        "btn_idx": "🚀 Generate Professional Index", "btn_sync": "✅ Save & Sync Chapters",
        "lbl_sec": "Select section:", "btn_write": "✨ WRITE SECTION (2000+ words)",
        "btn_quiz": "🧠 ADD QUIZ TO BOOK", "btn_edit": "🚀 REWRITE WITH AI",
        "msg_run": "The world authority is processing the content...", "preface": "Preface", "ack": "Acknowledgements",
        "preview_tit": "📖 Professional Reading View", "btn_word": "📥 Download Word (.docx)", "btn_pdf": "📥 Download PDF (.pdf)",
        "msg_err_idx": "You must generate the index in Tab 1 before writing.", "msg_success_sync": "Chapters synchronized!",
        "label_editor": "Professional Text Editor", "label_quiz_gen": "Generated Quiz",
        "welcome": "👋 Welcome to Antonino's Ebook Creator.", "guide": "Setup the sidebar to unlock AI features."
    },
    "Deutsch": {
        "side_tit": "⚙️ Editor-Setup",
        "lbl_tit": "Buchtitel", "lbl_auth": "Autor", "lbl_lang": "Sprache", 
        "lbl_gen": "Genre", "lbl_style": "Schreibstil", "lbl_plot": "Inhalt",
        "btn_res": "🔄 PROJEKT ZURÜCKSETZEN", "tabs": ["📊 1. Index", "✍️ 2. Schreiben & Quiz", "📖 3. Vorschau", "📑 4. Export"],
        "btn_idx": "🚀 Index generieren", "btn_sync": "✅ Kapitel synchronisieren",
        "lbl_sec": "Abschnitt wählen:", "btn_write": "✨ ABSCHNITT SCHREIBEN",
        "btn_quiz": "🧠 QUIZ HINZUFÜGEN", "btn_edit": "🚀 ÜBERARBEITEN",
        "msg_run": "Experte schreibt...", "preface": "Vorwort", "ack": "Danksagungen",
        "preview_tit": "📖 Leseansicht", "btn_word": "📥 Word herunterladen", "btn_pdf": "📥 PDF herunterladen"
    },
    "Français": {
        "side_tit": "⚙️ Configuration",
        "lbl_tit": "Titre", "lbl_auth": "Auteur", "lbl_lang": "Langue", 
        "lbl_gen": "Genre", "lbl_style": "Style", "lbl_plot": "Intrigue",
        "btn_res": "🔄 RÉINITIALISER", "tabs": ["📊 1. Index", "✍️ 2. Écriture", "📖 3. Aperçu", "📑 4. Export"],
        "btn_idx": "🚀 Générer l'index", "btn_sync": "✅ Synchroniser",
        "lbl_sec": "Section:", "btn_write": "✨ ÉCRIRE LA SECTION",
        "btn_quiz": "🧠 AJOUTER UN QUIZ", "btn_edit": "🚀 REFORMULER",
        "msg_run": "L'expert écrit...", "preface": "Préface", "ack": "Remerciements",
        "preview_tit": "📖 Vue Lecture", "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    },
    "Español": {
        "side_tit": "⚙️ Configuración",
        "lbl_tit": "Título del libro", "lbl_auth": "Autor", "lbl_lang": "Idioma", 
        "lbl_gen": "Género", "lbl_style": "Estilo", "lbl_plot": "Trama",
        "btn_res": "🔄 REINICIAR", "tabs": ["📊 1. Índice", "✍️ 2. Escritura", "📖 3. Vista previa", "📑 4. Exportar"],
        "btn_idx": "🚀 Generar índice", "btn_sync": "✅ Sincronizar",
        "lbl_sec": "Sección:", "btn_write": "✨ ESCRIBIR SECCIÓN",
        "btn_quiz": "🧠 AÑADIR CUESTIONARIO", "btn_edit": "🚀 REESCRIBIR"
    },
    "Română": {
        "side_tit": "⚙️ Configurare",
        "lbl_tit": "Titlul cărții", "lbl_auth": "Autor", "lbl_lang": "Limbă", 
        "lbl_gen": "Gen", "lbl_style": "Stil", "lbl_plot": "Subiect",
        "btn_res": "🔄 RESETARE", "tabs": ["📊 1. Index", "✍️ 2. Scriere", "📖 3. Previzualizare", "📑 4. Export"]
    },
    "Русский": {
        "side_tit": "⚙️ Настройки",
        "lbl_tit": "Название", "lbl_auth": "Автор", "lbl_lang": "Язык", 
        "lbl_gen": "Жанр", "lbl_style": "Стиль", "lbl_plot": "Сюжет",
        "btn_res": "🔄 СБРОС", "tabs": ["📊 Оглавление", "✍️ Написание", "📖 Просмотр", "📑 Экспорт"]
    },
    "中文": {
        "side_tit": "⚙️ 设置",
        "lbl_tit": "书名", "lbl_auth": "作者", "lbl_lang": "语言", 
        "lbl_gen": "体裁", "lbl_style": "风格", "lbl_plot": "情节",
        "btn_res": "🔄 重置", "tabs": ["📊 目录", "✍️ 写作", "📖 预览", "📑 导出"]
    }
}

# ======================================================================================================================
# 3. BLOCCO CSS CUSTOM (SIDEBAR SCURA, PULSANTI BLU, ANTEPRIMA BIANCA)
# ======================================================================================================================
st.markdown("""
<style>
/* Pulizia layout Streamlit */
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* CONFIGURAZIONE SIDEBAR SCURA (Richiesta specifica Antonino) */
section[data-testid="stSidebar"] { 
    min-width: 420px !important; 
    max-width: 420px !important; 
    background-color: #121212 !important; /* Antracite Profondo */
    border-right: 1px solid #333;
}

/* Colore testi e label nella sidebar scura */
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* Input e Selettori nella sidebar scura */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: #222 !important;
    color: white !important;
    border: 1px solid #444 !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background-color: #222 !important;
    color: white !important;
    border: 1px solid #444 !important;
}

/* TITOLO CENTRALE PRO */
.custom-title {
    font-size: 38px; font-weight: 900; color: #111; text-align: center;
    padding: 30px; background-color: #ffffff; border-radius: 12px;
    margin-bottom: 30px; border-bottom: 8px solid #007BFF;
    box-shadow: 0px 10px 20px rgba(0,0,0,0.05);
}

/* ANTEPRIMA EBOOK: FOGLIO BIANCO PROFESSIONALE */
.preview-box {
    background-color: #ffffff; 
    padding: 80px; 
    border: 1px solid #ccc;
    border-radius: 4px; 
    height: 900px; 
    overflow-y: scroll;
    font-family: 'Times New Roman', serif; 
    line-height: 2.0; 
    color: #111;
    box-shadow: 0px 25px 60px rgba(0,0,0,0.2);
    margin: 0 auto;
}

/* PULSANTI BLU ANTONINO - ALTA VISIBILITÀ (Richiesta specifica Antonino) */
.stButton>button {
    width: 100%; border-radius: 12px; height: 4.5em; font-weight: bold;
    background-color: #007BFF !important; color: white !important;
    font-size: 19px !important; border: 2px solid #0056b3; 
    box-shadow: 0px 6px 18px rgba(0, 123, 255, 0.45);
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stButton>button:hover { 
    background-color: #0056b3 !important; 
    transform: scale(1.03); 
    box-shadow: 0px 10px 25px rgba(0, 86, 179, 0.6);
}

/* Tabs personalizzati */
.stTabs [data-baseweb="tab-list"] {
    gap: 15px;
}

.stTabs [data-baseweb="tab"] {
    height: 60px;
    background-color: #f8f9fa;
    border-radius: 10px 10px 0px 0px;
    padding: 10px 25px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ======================================================================================================================
# 4. CLASSE PDF PERSONALIZZATA (GESTIONE EXPORT)
# ======================================================================================================================
class EbookPDF(FPDF):
    """Classe avanzata per la generazione del file PDF finale del libro."""
    def __init__(self, titolo, autore):
        super().__init__()
        self.titolo = titolo
        self.autore = autore

    def header(self):
        """Header visualizzato in ogni pagina tranne la prima."""
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f"{self.titolo} - {self.autore}", 0, 0, 'R')
            self.ln(15)

    def footer(self):
        """Footer con numero di pagina."""
        self.set_y(-20)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def front_page(self):
        """Genera il frontespizio del libro."""
        self.add_page()
        self.set_font('Arial', 'B', 32)
        self.ln(100)
        self.multi_cell(0, 15, self.titolo.upper(), 0, 'C')
        self.ln(20)
        self.set_font('Arial', 'I', 20)
        self.cell(0, 10, f"di {self.autore}", 0, 1, 'C')

    def add_chapter(self, title, body):
        """Aggiunge un capitolo completo al PDF."""
        self.add_page()
        self.ln(20)
        self.set_font('Arial', 'B', 22)
        self.set_text_color(0, 43, 92)
        self.multi_cell(0, 15, title.upper())
        self.ln(15)
        self.set_font('Arial', '', 12)
        self.set_text_color(30, 30, 30)
        # Pulizia caratteri per FPDF latin-1
        try:
            body_clean = body.encode('latin-1', 'replace').decode('latin-1')
        except:
            body_clean = body
        self.multi_cell(0, 10, body_clean)

# ======================================================================================================================
# 5. FUNZIONI LOGICHE DI ELABORAZIONE (IA & SYNC)
# ======================================================================================================================
def chiedi_gpt(prompt, system_prompt):
    """
    Interfaccia principale con il modello GPT-4o.
    Gestisce il prompt di sistema e il prompt utente, ripulendo l'output dai tag IA ridondanti.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.72
        )
        testo_raw = response.choices[0].message.content.strip()
        
        # Filtro Anti-Metadati IA
        metadati = ["ecco", "certamente", "sicuramente", "ok", "here is", "sure", "of course", "biensur"]
        linee = testo_raw.split("\n")
        output_filtrato = [l for l in linee if not any(l.lower().startswith(m) for m in metadati)]
        
        return "\n".join(output_filtrato).strip()
    except Exception as e:
        return f"ERRORE API OPENAI: {str(e)}"

def sync_capitoli():
    """
    Analizza l'indice grezzo inserito dall'utente e popola la lista dei capitoli sincronizzati.
    Riconosce i capitoli in tutte le 8 lingue supportate tramite Regex.
    """
    testo_indice = st.session_state.get("indice_raw", "")
    if not testo_indice:
        st.session_state['lista_capitoli'] = []
        return
    
    lista_validata = []
    # Pattern regex universale per capitoli e sezioni numerate
    regex_capitolo = r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)'
    
    for riga in testo_indice.split('\n'):
        if re.search(regex_capitolo, riga.strip()):
            lista_validata.append(riga.strip())
            
    st.session_state['lista_capitoli'] = lista_validata

# ======================================================================================================================
# 6. SIDEBAR: SETUP EDITORIALE AVANZATO (DARK MODE)
# ======================================================================================================================
with st.sidebar:
    # Selezione Lingua: Caricamento del dizionario di traduzione
    lingua_selezionata = st.selectbox("🌐 Lingua dell'Interfaccia / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lingua_selezionata]
    
    st.title(L["side_tit"])
    
    # Input Dati Libro
    val_titolo = st.text_input(L["lbl_tit"], placeholder="Inserisci il titolo del tuo capolavoro...")
    val_autore = st.text_input(L["lbl_auth"], placeholder="Inserisci il nome dell'autore...")
    
    # Generi Completi (Richiesti: Scientifico, Quiz, Rosa, Fantasy, ecc.)
    lista_generi = [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Marketing", "Motivazionale / Self-Help", "Biografia / Autobiografia", 
        "Libro di Quiz / Didattica", "Saggio Breve", "Romanzo Rosa", 
        "Romanzo Storico", "Thriller / Noir", "Fantasy", "Fantascienza"
    ]
    val_genere = st.selectbox(L["lbl_gen"], lista_generi)
    
    # Tipologia Scrittura
    val_stile = st.selectbox(L["lbl_style"], ["Standard", "Professionale (Accademica/Analitica)"])
    
    # Trama / Argomento Centrale
    val_trama = st.text_area(L["lbl_plot"], height=180, placeholder="Descrivi qui la trama o l'argomento centrale del libro...")
    
    st.markdown("---")
    
    # Pulsante Reset Globale
    if st.button(L["btn_res"]):
        for key in list(st.session_state.keys()): 
            del st.session_state[key]
        st.rerun()

# ======================================================================================================================
# 7. LOGICA DI SCRITTURA A 3 FASI (COERENZA E LUNGHEZZA)
# ======================================================================================================================
# Definiamo le fasi per obbligare l'IA a generare testi lunghi senza interruzioni.
mappa_fasi = {
    "Italiano": ["Introduzione e Contesto", "Analisi Tecnica e Sviluppo", "Conclusioni e Sintesi"],
    "English": ["Deep Introduction", "Technical Analysis & Body", "Synthesis & Conclusion"],
    "Deutsch": ["Einleitung", "Hauptteil", "Zusammenfassung"],
    "Français": ["Introduction", "Développement", "Conclusion"],
    "Español": ["Introducción", "Desarrollo", "Conclusión"]
}
fasi_scrittura = mappa_fasi.get(lingua_selezionata, ["Phase 1", "Phase 2", "Phase 3"])

# ======================================================================================================================
# 8. INTERFACCIA UTENTE PRINCIPALE (MODULARE)
# ======================================================================================================================
st.markdown(f'<div class="custom-title">AI Editor: {val_titolo if val_titolo else "Creatore Ebook Mondiale PRO"}</div>', unsafe_allow_html=True)

if val_titolo and val_trama:
    # DEFINIZIONE DEL PROMPT AUTORITÀ MONDIALE (Richiesta specifica Antonino)
    tono_scrittura = "estremamente formale, tecnico e accademico" if val_stile == "Professionale (Accademica/Analitica)" else "fluido, coinvolgente e narrativo"
    
    # Gestione del Filo Logico: Controllo delle sezioni già esistenti
    chiavi_esistenti = [k for k in st.session_state.keys() if k.startswith("txt_")]
    istruzione_coerenza = "Mantieni un filo logico ferreo con quanto scritto nei capitoli precedenti. Non ripetere mai gli stessi concetti." if chiavi_esistenti else ""

    PROMPT_SISTEMA = f"""
Sei un'Autorità Mondiale, un luminare o un autore di bestseller nel settore {val_genere}. Scrivi solo in {lingua_selezionata}.
Stile di scrittura: {tono_scrittura}. Target per capitolo: 2000 parole complessive.

REGOLE DI SCRITTURA INDEROGABILI:
1. ANTI-RIPETIZIONE: {istruzione_coerenza} Ogni paragrafo deve essere unico e aggiungere valore.
2. FILO LOGICO: Devi seguire rigorosamente l'indice del libro e l'argomento centrale: {val_trama}.
3. LUNGHEZZA: Sviluppa ogni concetto con dati tecnici, esempi reali, analisi approfondite e sottotitoli.
4. COERENZA: Il lessico deve essere appropriato al genere selezionato ({val_genere}).
5. NO INTRODUZIONE: Non rispondere mai come una chat. Produci direttamente il contenuto editoriale.
"""

    tabs_ebook = st.tabs(L["tabs"])

    # --- TAB 1: INDICE E ARCHITETTURA DEL LIBRO ---
    with tabs_ebook[0]:
        st.subheader("📊 Pianificazione della Struttura Editoriale")
        if st.button(L["btn_idx"]):
            with st.spinner("L'Architetto Editoriale sta strutturando il libro..."):
                prompt_per_indice = f"Genera un indice monumentale, dettagliato e logico per un libro '{val_genere}' intitolato '{val_titolo}' in {lingua_selezionata}. Focus: {val_trama}. Evita capitoli ridondanti."
                st.session_state["indice_raw"] = chiedi_gpt(prompt_per_indice, "Senior Book Editor & Architect.")
                sync_capitoli()
        
        # Area testo indice modificabile manualmente
        st.session_state["indice_raw"] = st.text_area("Revisione Indice (Un capitolo per riga):", value=st.session_state.get("indice_raw", ""), height=450)
        
        if st.button(L["btn_sync"]):
            sync_capitoli()
            st.success(L["msg_success_sync"])

    # --- TAB 2: SCRITTURA PROFESSIONALE E QUIZ INTEGRATO ---
    with tabs_ebook[1]:
        capitoli_disponibili = st.session_state.get("lista_capitoli", [])
        if not capitoli_disponibili:
            st.warning(L["msg_err_idx"])
        else:
            # Selezione della sezione corrente
            menu_sezioni = [L["preface"]] + capitoli_disponibili + [L["ack"]]
            sezione_attiva = st.selectbox(L["lbl_sec"], menu_sezioni)
            chiave_sessione = f"txt_{sezione_attiva.replace(' ', '_').replace('.', '')}"

            # Layout Comandi: Scrittura, Rielaborazione e Quiz
            col_scrittura, col_modifica, col_quiz_btn = st.columns([2, 2, 1])
            
            with col_scrittura:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        testo_accumulato = ""
                        # Generazione segmentata per garantire 2000+ parole (Anti-timeout e Anti-ripetizione)
                        for fase_nome in fasi_scrittura:
                            p_fase = f"L'indice del libro è: {st.session_state['indice_raw']}. Ora scrivi la sezione '{sezione_attiva}', parte specifica: {fase_nome}. Sii estremamente prolisso e dettagliato."
                            testo_accumulato += chiedi_gpt(p_fase, PROMPT_SISTEMA) + "\n\n"
                        st.session_state[chiave_sessione] = testo_accumulato
            
            with col_modifica:
                istruzione_ia = st.text_input(L["btn_edit"], key=f"in_mod_{chiave_sessione}", placeholder="Es: Rendilo più accademico / Più drammatico...")
                if st.button(L["btn_edit"] + " 🪄"):
                    if chiave_sessione in st.session_state:
                        with st.spinner("Rielaborazione professionale in corso..."):
                            p_edit = f"Riscrivi integralmente la sezione basandoti su questa istruzione: {istruzione_ia}.\n\nTesto attuale:\n{st.session_state[chiave_sessione]}"
                            st.session_state[chiave_sessione] = chiedi_gpt(p_edit, PROMPT_SISTEMA)
                            st.rerun()

            with col_quiz_btn:
                if st.button("🧠 QUIZ"):
                    if chiave_sessione in st.session_state:
                        with st.spinner("Generando Test di Valutazione..."):
                            p_quiz_prompt = f"Genera un quiz di 10 domande a risposta multipla basato sul capitolo '{sezione_attiva}'. Includi le soluzioni commentate. Lingua: {lingua_selezionata}."
                            test_risultato = chiedi_gpt(p_quiz_prompt, "Professore esperto in didattica.")
                            # Inserimento automatico del quiz in fondo al testo del capitolo
                            st.session_state[chiave_sessione] += f"\n\n---\n\n### TEST DI VALUTAZIONE E QUIZ: {sezione_attiva}\n\n" + test_risultato
                            st.success("Quiz integrato con successo!")
                            st.rerun()

            # Area di Editing Manuale con persistenza dello stato
            if chiave_sessione in st.session_state:
                st.markdown(f"#### {L['label_editor']}")
                st.session_state[chiave_sessione] = st.text_area("Editor Live", value=st.session_state[chiave_sessione], height=550, key=f"editor_{chiave_sessione}")

    # --- TAB 3: ANTEPRIMA PROFESSIONALE E FILO LOGICO ---
    with tabs_ebook[2]:
        st.subheader(L["preview_tit"])
        # Simulazione del libro fisico tramite HTML e CSS
        html_ebook = f"<div class='preview-box'>"
        html_ebook += f"<h1 style='text-align:center; font-size:52px; color:#000;'>{val_titolo.upper()}</h1>"
        if val_autore:
            html_ebook += f"<h3 style='text-align:center; font-style:italic; font-size:28px;'>di {val_autore}</h3>"
        html_ebook += "<div style='height:300px'></div>" # Spazio frontespizio
        
        contenuto_presente = False
        for s_idx in menu_sezioni:
            k_preview = f"txt_{s_idx.replace(' ', '_').replace('.', '')}"
            if k_preview in st.session_state and st.session_state[k_preview].strip():
                html_ebook += f"<h2 style='page-break-before:always; color:#000; font-size:36px; border:none;'>{s_idx.upper()}</h2>"
                # Formattazione per la corretta visualizzazione degli a capo in HTML
                testo_formattato_html = st.session_state[k_preview].replace(chr(10), '<br>')
                html_ebook += f"<p style='text-align:justify; font-size:19px;'>{testo_formattato_html}</p>"
                contenuto_presente = True
        
        if not contenuto_presente:
            html_ebook += f"<p style='text-align:center; color:#999; font-size:22px;'>Nessun contenuto disponibile. Avvia la generazione nella Tab 2.</p>"
        
        html_ebook += "</div>"
        st.markdown(html_ebook, unsafe_allow_html=True)

    # --- TAB 4: ESPORTAZIONE MULTIFORMATO (WORD & PDF) ---
    with tabs_ebook[3]:
        st.subheader("📑 Finalizzazione del Progetto")
        st.info("Il sistema genererà un documento completo che include l'indice, il testo e tutti i quiz generati.")
        
        col_word, col_pdf = st.columns(2)
        
        with col_word:
            if st.button(L["btn_word"]):
                doc_file = Document()
                doc_file.add_heading(val_titolo, 0)
                if val_autore: 
                    doc_file.add_paragraph(f"Autore: {val_autore}")
                
                # Aggiunta Indice
                doc_file.add_page_break()
                doc_file.add_heading("INDICE / TABLE OF CONTENTS", level=1)
                doc_file.add_paragraph(st.session_state.get("indice_raw", ""))
                
                # Loop su tutte le sezioni per l'esportazione
                for s_export in menu_sezioni:
                    k_export = f"txt_{s_export.replace(' ', '_').replace('.', '')}"
                    if k_export in st.session_state:
                        doc_file.add_page_break()
                        doc_file.add_heading(s_export.upper(), level=1)
                        doc_file.add_paragraph(st.session_state[k_export])
                
                # Creazione buffer e download
                buf_word_final = BytesIO()
                doc_file.save(buf_word_final)
                buf_word_final.seek(0)
                st.download_button(L["btn_word"], buf_word_final, file_name=f"{val_titolo.replace(' ','_')}.docx")
                
        with col_pdf:
            if st.button(L["btn_pdf"]):
                pdf_generator = EbookPDF(val_titolo, val_autore)
                pdf_generator.front_page()
                
                # Aggiunta capitoli al PDF
                for s_pdf in menu_sezioni:
                    k_pdf = f"txt_{s_pdf.replace(' ', '_').replace('.', '')}"
                    if k_pdf in st.session_state:
                        pdf_generator.add_chapter(s_pdf, st.session_state[k_pdf])
                
                # Generazione output binario PDF
                out_pdf = pdf_generator.output(dest='S').encode('latin-1', 'replace')
                st.download_button(L["btn_pdf"], out_pdf, file_name=f"{val_titolo.replace(' ','_')}.pdf")

else:
    # SCHERMATA DI BENVENUTO E GUIDA (Richiesta specifica Antonino)
    st.info(L["welcome"])
    st.markdown(f"""
    ### {L['guide']}
    
    1. **CONFIGURAZIONE**: Definisci il titolo, l'autore e il genere (dal **Romanzo Rosa** al **Saggio Scientifico**).
    2. **INDICE (Tab 1)**: Crea l'ossatura logica del libro. Senza un indice sincronizzato, l'IA non può scrivere.
    3. **SCRITTURA (Tab 2)**: L'IA genererà capitoli da **2000 parole** ciascuno, garantendo un filo logico impeccabile tra le sezioni.
    4. **QUIZ**: Al termine di ogni capitolo, puoi generare e integrare test di autovalutazione direttamente nel libro.
    5. **ANTEPRIMA (Tab 3)**: Leggi il tuo lavoro con un'impaginazione professionale.
    6. **ESPORTAZIONE (Tab 4)**: Scarica l'opera finita in formato **Word o PDF**.
    """)

# ======================================================================================================================
# FINE CODICE - ARCHITETTURA SOFTWARE EBOOK CREATOR MONDIALE PRO
# ======================================================================================================================
