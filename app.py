import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# =================================================================
# 1. CONNESSIONE API E CONFIGURAZIONE DI SISTEMA
# =================================================================
# La chiave API deve essere configurata nei secrets di Streamlit
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Errore: Chiave API OpenAI non trovata nei Secrets.")

# Configurazione della pagina Streamlit per massima visibilità
st.set_page_config(
    page_title="AI di Antonino: Ebook Mondiale Creator PRO",
    layout="wide",
    initial_sidebar_state="expanded" # Forza la sidebar a restare aperta
)

# =================================================================
# 2. DIZIONARIO TRADUZIONI INTEGRALE (INTERFACCIA COMPLETA)
# =================================================================
TRADUZIONI = {
    "Italiano": {
        "side_tit": "⚙️ Configurazione Editor",
        "lbl_tit": "Titolo del Libro", "lbl_auth": "Nome Autore", "lbl_lang": "Lingua", 
        "lbl_gen": "Genere", "lbl_style": "Tipologia Scrittura", "lbl_plot": "Trama o Argomento",
        "btn_res": "🔄 RESET PROGETTO", "tabs": ["📊 1. Indice", "✍️ 2. Scrittura & Quiz", "📖 3. Anteprima", "📑 4. Esporta"],
        "btn_idx": "🚀 Genera Indice Professionale", "btn_sync": "✅ Salva e Sincronizza Capitoli",
        "lbl_sec": "Seleziona sezione:", "btn_write": "✨ SCRIVI SEZIONE (2000+ parole)",
        "btn_quiz": "🧠 AGGIUNGI QUIZ AL LIBRO", "btn_edit": "🚀 RIELABORA CON IA",
        "msg_run": "L'autorità mondiale sta scrivendo...", "preface": "Prefazione", "ack": "Ringraziamenti",
        "preview_tit": "📖 Vista Lettura Professionale", "btn_word": "📥 Scarica Ebook (.docx)",
        "msg_err_idx": "Genera l'indice prima di procedere.", "msg_success_sync": "Capitoli sincronizzati!",
        "label_editor": "Editor di Testo Professionale", "label_quiz_area": "Area Quiz Generata"
    },
    "English": {
        "side_tit": "⚙️ Editor Setup",
        "lbl_tit": "Book Title", "lbl_auth": "Author Name", "lbl_lang": "Language", 
        "lbl_gen": "Genre", "lbl_style": "Writing Style", "lbl_plot": "Plot or Topic",
        "btn_res": "🔄 RESET PROJECT", "tabs": ["📊 1. Index", "✍️ 2. Write & Quiz", "📖 3. Preview", "📑 4. Export"],
        "btn_idx": "🚀 Generate Professional Index", "btn_sync": "✅ Save & Sync Chapters",
        "lbl_sec": "Select section:", "btn_write": "✨ WRITE SECTION (2000+ words)",
        "btn_quiz": "🧠 ADD QUIZ TO BOOK", "btn_edit": "🚀 REWRITE WITH AI",
        "msg_run": "The world authority is writing...", "preface": "Preface", "ack": "Acknowledgements",
        "preview_tit": "📖 Professional Reading View", "btn_word": "📥 Download Ebook (.docx)",
        "msg_err_idx": "Generate the index before proceeding.", "msg_success_sync": "Chapters synchronized!",
        "label_editor": "Professional Text Editor", "label_quiz_area": "Generated Quiz Area"
    },
    "Deutsch": {
        "side_tit": "⚙️ Editor-Setup",
        "lbl_tit": "Buchtitel", "lbl_auth": "Autor", "lbl_lang": "Sprache", 
        "lbl_gen": "Genre", "lbl_style": "Schreibstil", "lbl_plot": "Inhalt",
        "btn_res": "🔄 ZURÜCKSETZEN", "tabs": ["📊 1. Index", "✍️ 2. Schreiben & Quiz", "📖 3. Vorschau", "📑 4. Export"],
        "btn_idx": "🚀 Index generieren", "btn_sync": "✅ Kapitel synchronisieren",
        "lbl_sec": "Abschnitt wählen:", "btn_write": "✨ ABSCHNITT SCHREIBEN",
        "btn_quiz": "🧠 QUIZ HINZUFÜGEN", "btn_edit": "🚀 ÜBERARBEITEN",
        "msg_run": "Experte schreibt...", "preface": "Vorwort", "ack": "Danksagungen",
        "preview_tit": "📖 Leseansicht", "btn_word": "📥 Ebook herunterladen (.docx)",
        "msg_err_idx": "Generieren Sie zuerst den Index.", "msg_success_sync": "Kapitel synchronisiert!",
        "label_editor": "Text-Editor", "label_quiz_area": "Quiz-Bereich"
    },
    "Français": {
        "side_tit": "⚙️ Configuration",
        "lbl_tit": "Titre du livre", "lbl_auth": "Auteur", "lbl_lang": "Langue", 
        "lbl_gen": "Genre", "lbl_style": "Style", "lbl_plot": "Intrigue",
        "btn_res": "🔄 RÉINITIALISER", "tabs": ["📊 1. Index", "✍️ 2. Écriture & Quiz", "📖 3. Aperçu", "📑 4. Export"],
        "btn_idx": "🚀 Générer l'index", "btn_sync": "✅ Synchroniser",
        "lbl_sec": "Section:", "btn_write": "✨ ÉCRIRE LA SECTION",
        "btn_quiz": "🧠 AJOUTER UN QUIZ", "btn_edit": "🚀 REFORMULER",
        "msg_run": "L'expert écrit...", "preface": "Préface", "ack": "Remerciements",
        "preview_tit": "📖 Vue Lecture", "btn_word": "📥 Télécharger (.docx)",
        "msg_err_idx": "Générez d'abord l'index.", "msg_success_sync": "Chapitres synchronisés!"
    },
    "Español": {
        "side_tit": "⚙️ Configuración",
        "lbl_tit": "Título del libro", "lbl_auth": "Autor", "lbl_lang": "Idioma", 
        "lbl_gen": "Género", "lbl_style": "Estilo", "lbl_plot": "Trama",
        "btn_res": "🔄 REINICIAR", "tabs": ["📊 1. Índice", "✍️ 2. Escritura & Quiz", "📖 3. Vista previa", "📑 4. Exportar"],
        "btn_idx": "🚀 Generar índice", "btn_sync": "✅ Sincronizar capítulos",
        "lbl_sec": "Sección:", "btn_write": "✨ ESCRIBIR SECCIÓN",
        "btn_quiz": "🧠 AÑADIR CUESTIONARIO", "btn_edit": "🚀 REESCRIBIR",
        "msg_run": "El experto está escribiendo...", "preface": "Prefacio", "ack": "Agradecimientos",
        "preview_tit": "📖 Vista de lectura", "btn_word": "📥 Descargar (.docx)",
        "msg_err_idx": "Genere el índice primero.", "msg_success_sync": "Capítulos sincronizados!"
    },
    "Română": {
        "side_tit": "⚙️ Configurare",
        "lbl_tit": "Titlul cărții", "lbl_auth": "Autor", "lbl_lang": "Limbă", 
        "lbl_gen": "Gen", "lbl_style": "Stil", "lbl_plot": "Subiect",
        "btn_res": "🔄 RESETARE", "tabs": ["📊 1. Index", "✍️ 2. Scriere & Quiz", "📖 3. Previzualizare", "📑 4. Export"],
        "btn_idx": "🚀 Generează index", "btn_sync": "✅ Sincronizează",
        "lbl_sec": "Secțiune:", "btn_write": "✨ SCRIE SECȚIUNEA",
        "btn_quiz": "🧠 ADAUGĂ QUIZ", "btn_edit": "🚀 REFORMULEAZĂ",
        "msg_run": "Se scrie...", "preface": "Prefață", "ack": "Mulțumiri",
        "preview_tit": "📖 Vizualizare lectură", "btn_word": "📥 Descarcă (.docx)",
        "msg_err_idx": "Generați mai întâi indexul.", "msg_success_sync": "Capitole sincronizate!"
    },
    "Русский": {
        "side_tit": "⚙️ Настройки",
        "lbl_tit": "Название книги", "lbl_auth": "Автор", "lbl_lang": "Язык", 
        "lbl_gen": "Жанр", "lbl_style": "Стиль", "lbl_plot": "Сюжет",
        "btn_res": "🔄 СБРОС", "tabs": ["📊 1. Оглавление", "✍️ 2. Написание & Тест", "📖 3. Предпросмотр", "📑 4. Экспорт"],
        "btn_idx": "🚀 Создать оглавление", "btn_sync": "✅ Синхронизировать",
        "lbl_sec": "Раздел:", "btn_write": "✨ НАПИСАТЬ РАЗДЕЛ",
        "btn_quiz": "🧠 ДОБАВИТЬ ТЕСТ", "btn_edit": "🚀 ПЕРЕПИСАТЬ",
        "msg_run": "Пишем...", "preface": "Предисловие", "ack": "Благодарности",
        "preview_tit": "📖 Режим чтения", "btn_word": "📥 Скачать (.docx)"
    },
    "中文": {
        "side_tit": "⚙️ 设置",
        "lbl_tit": "书名", "lbl_auth": "作者", "lbl_lang": "语言", 
        "lbl_gen": "体裁", "lbl_style": "写作风格", "lbl_plot": "情节",
        "btn_res": "🔄 重置", "tabs": ["📊 1. 目录", "✍️ 2. 写作与测试", "📖 3. 预览", "📑 4. 导出"],
        "btn_idx": "🚀 生成目录", "btn_sync": "✅ 同步章节",
        "lbl_sec": "选择章节:", "btn_write": "✨ 编写章节",
        "btn_quiz": "🧠 添加测试", "btn_edit": "🚀 重写",
        "msg_run": "专家正在写作...", "preface": "前言", "ack": "致谢",
        "preview_tit": "📖 阅读视图", "btn_word": "📥 下载 (.docx)"
    }
}

# =================================================================
# 3. BLOCCO CSS (UI AVANZATA E STILE)
# =================================================================
st.markdown("""
<style>
/* Nascondi Header e Footer Streamlit */
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* Configurazione Sidebar Larga e Fissa */
section[data-testid="stSidebar"] { 
    min-width: 400px !important; 
    max-width: 400px !important; 
    background-color: #f4f7f9;
    border-right: 1px solid #d1d9e6;
}

/* Titolo Customizzato */
.custom-title {
    font-size: 42px; 
    font-weight: 800; 
    color: #002b5c; 
    text-align: center;
    padding: 25px; 
    background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
    border-radius: 20px;
    margin-bottom: 30px; 
    border: 1px solid #bccad6;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

/* Anteprima Ebook - Stile Pagina Reale */
.preview-box {
    background-color: #ffffff; 
    padding: 70px; 
    border: 1px solid #d3d6db;
    border-radius: 4px; 
    height: 800px; 
    overflow-y: scroll;
    font-family: 'Georgia', serif; 
    line-height: 1.8; 
    color: #1a1a1a;
    box-shadow: 0px 20px 40px rgba(0,0,0,0.1);
    margin: 0 auto;
    max-width: 900px;
}

/* Pulsanti Blu Antonino PRO */
.stButton>button {
    width: 100%; 
    border-radius: 12px; 
    height: 4em; 
    font-weight: 700;
    background-color: #007BFF !important; 
    color: white !important;
    font-size: 17px !important; 
    border: none; 
    box-shadow: 0px 6px 15px rgba(0, 123, 255, 0.25);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.stButton>button:hover { 
    background-color: #0056b3 !important; 
    transform: translateY(-3px); 
    box-shadow: 0px 10px 25px rgba(0, 86, 179, 0.35);
}

/* Input e Selectbox */
.stTextInput>div>div>input, .stSelectbox>div>div>div {
    border-radius: 10px !important;
}

h2 { color: #004a99; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. CLASSI E FUNZIONI CORE (PDF, GPT, LOGICA)
# =================================================================
class PDF(FPDF):
    """Gestore Esportazione PDF con supporto autore"""
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1 and self.autore:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Author: {self.autore}", 0, 0, 'C')
            self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def chiedi_gpt(prompt, system_prompt):
    """Funzione di comunicazione con OpenAI GPT-4o"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.75
        )
        testo = response.choices[0].message.content.strip()
        # Pulizia automatica tag IA
        tag_inutili = ["ecco", "certamente", "spero", "ciao", "fase", "parte", "here is", "sure"]
        linee = testo.split("\n")
        pulito = [l for l in linee if not any(l.lower().startswith(t) for t in tag_inutili)]
        return "\n".join(pulito).strip()
    except Exception as e:
        return f"Errore Tecnico API: {str(e)}"

def sync_capitoli():
    """Analizza l'indice testuale e aggiorna la lista capitoli nel session_state"""
    testo = st.session_state.get("indice_raw", "")
    if not testo:
        st.session_state['lista_capitoli'] = []
        return
    linee = testo.split('\n')
    trovati = []
    # Pattern per riconoscere capitoli: Numerati, "Capitolo X", "Chapter X", ecc.
    pattern = r'^(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)'
    for l in linee:
        if re.search(pattern, l.strip(), re.I):
            trovati.append(l.strip())
    st.session_state['lista_capitoli'] = trovati

# =================================================================
# 5. SIDEBAR: CONFIGURAZIONE PROGETTO
# =================================================================
with st.sidebar:
    # Scelta Lingua (Determina tutto il dizionario)
    lang_choice = st.selectbox("🌐 Seleziona Lingua / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lang_choice]
    
    st.title(L["side_tit"])
    titolo_l = st.text_input(L["lbl_tit"], placeholder="Es: I Segreti della Scienza")
    autore_l = st.text_input(L["lbl_auth"], placeholder="Nome dell'Autore")
    
    # Elenco Generi Completo (Richiesto: Scientifico, Quiz, Rosa, ecc.)
    genere_list = [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Marketing", "Motivazionale / Self-Help", "Biografia / Autobiografia", 
        "Libro di Quiz / Test Didattico", "Saggio Breve", "Romanzo Rosa", 
        "Romanzo Storico", "Thriller / Noir", "Fantasy", "Fantascienza"
    ]
    genere = st.selectbox(L["lbl_gen"], genere_list)
    
    # Modalità di Scrittura
    modalita = st.selectbox(L["lbl_style"], ["Standard", "Professionale (Accademica/Tecnica)"])
    
    # Trama/Prompt Centrale
    trama = st.text_area(L["lbl_plot"], height=150, placeholder="Descrivi l'argomento centrale...")
    
    st.markdown("---")
    # Pulsante Reset
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# =================================================================
# 6. LOGICA DI SCRITTURA E COERENZA (FILO LOGICO)
# =================================================================
# Mappatura fasi per forzare la lunghezza (2000 parole)
fasi_map = {
    "Italiano": ["Introduzione Sistematica", "Analisi dei Dati e Sviluppo", "Sintesi e Conclusioni"],
    "English": ["Systematic Introduction", "Data Analysis & Development", "Synthesis & Conclusions"],
    "Deutsch": ["Einleitung", "Entwicklung", "Zusammenfassung"],
    "Français": ["Introduction", "Développement", "Synthèse"],
    "Español": ["Introducción", "Desarrollo", "Síntesis"]
}
fasi = fasi_map.get(lang_choice, ["Part 1", "Part 2", "Part 3"])

# =================================================================
# 7. UI PRINCIPALE (TAB SYSTEM)
# =================================================================
st.markdown(f'<div class="custom-title">AI: {titolo_l if titolo_l else "Ebook Creator Professional"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    # Definizione Prompt di Sistema Avanzato (Anti-Ripetizione e Filo Logico)
    stile_ia = "altamente tecnico e accademico" if modalita == "Professionale (Accademica/Tecnica)" else "fluido e coinvolgente"
    
    # Costruiamo un "Context Summary" basato sui capitoli già scritti per evitare ripetizioni
    context_keys = [k for k in st.session_state.keys() if k.startswith("txt_")]
    context_brief = "Evita di ripetere concetti già trattati nelle sezioni precedenti." if context_keys else ""

    S_PROMPT = f"""
Sei un'Autorità Mondiale nel settore {genere}. Scrivi esclusivamente in {lang_choice}.
Stile richiesto: {stile_ia}. Target: Capitoli monumentali (minimo 2000 parole).

REGOLE DI COERENZA E UNICITÀ:
1. FILO LOGICO: Ogni capitolo deve essere una prosecuzione logica del precedente.
2. ANTI-RIPETIZIONE: {context_brief} Non usare gli stessi esempi, dati o citazioni in capitoli diversi.
3. DETTAGLIO: Espandi ogni paragrafo con analisi, casi studio e approfondimenti tecnici.
4. STRUTTURA: Usa sottotitoli interni e liste puntate dove necessario.
5. NO META-DATA: Scrivi solo il testo del libro.
"""

    tabs = st.tabs(L["tabs"])

    # --- TAB 1: INDICE E STRUTTURA ---
    with tabs[0]:
        st.subheader("📊 Pianificazione della Struttura")
        if st.button(L["btn_idx"]):
            with st.spinner("L'Editor sta strutturando il libro..."):
                p_idx = f"Crea un indice completo, logico e sequenziale per un libro di {genere} intitolato '{titolo_l}' in {lang_choice}. Argomento: {trama}. Assicura un'evoluzione coerente tra i capitoli."
                st.session_state["indice_raw"] = chiedi_gpt(p_idx, "Professional Book Planner & Architect.")
                sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area(L["lbl_tit"], value=st.session_state.get("indice_raw", ""), height=400)
        
        if st.button(L["btn_sync"]):
            sync_capitoli()
            st.success(L["msg_success_sync"])

    # --- TAB 2: SCRITTURA, RIELABORAZIONE E QUIZ ---
    with tabs[1]:
        lista_c = st.session_state.get("lista_capitoli", [])
        if not lista_c:
            st.warning(L["msg_err_idx"])
        else:
            opzioni_finali = [L["preface"]] + lista_c + [L["ack"]]
            cap_sel = st.selectbox(L["lbl_sec"], opzioni_finali)
            key_sez = f"txt_{cap_sel.replace(' ', '_').replace('.', '')}"

            # Layout 3 Colonne per i Comandi
            col_w, col_e, col_q = st.columns([2, 2, 1])
            
            with col_w:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        # Logica a 3 fasi per forzare 2000 parole
                        testo_capitolo = ""
                        for f_nome in fasi:
                            prompt_fase = f"L'indice del libro è: {st.session_state['indice_raw']}. Scrivi la sezione '{cap_sel}', focalizzandoti sulla fase: {f_nome}. Espandi al massimo."
                            testo_capitolo += chiedi_gpt(prompt_fase, S_PROMPT) + "\n\n"
                        st.session_state[key_sez] = testo_capitolo
            
            with col_e:
                istr_m = st.text_input(L["btn_edit"], key=f"istr_{key_sez}", placeholder="Esempio: Rendi più drammatico...")
                if st.button(L["btn_edit"] + " 🚀"):
                    if key_sez in st.session_state:
                        with st.spinner("Rielaborazione..."):
                            p_edit = f"Rielabora il seguente testo seguendo questa istruzione: {istr_m}. Mantieni lo stile autoritario.\n\nTesto attuale:\n{st.session_state[key_sez]}"
                            st.session_state[key_sez] = chiedi_gpt(p_edit, S_PROMPT)
                            st.rerun()

            with col_q:
                if st.button("🧠 QUIZ"):
                    if key_sez in st.session_state:
                        with st.spinner("Creazione Quiz..."):
                            p_quiz = f"Basandoti sul capitolo '{cap_sel}', genera 10 domande a risposta multipla con soluzioni corrette spiegate. Scrivi in {lang_choice}."
                            quiz_res = chiedi_gpt(p_quiz, "Accademico esperto in valutazione.")
                            # Integrazione del Quiz nel testo del libro
                            st.session_state[key_sez] += f"\n\n---\n\n### TEST DI AUTOVALUTAZIONE: {cap_sel}\n\n" + quiz_res
                            st.success("Quiz Aggiunto!")
                            st.rerun()

            # Editor di Testo Manuale (Session State Persistence)
            if key_sez in st.session_state:
                st.markdown(f"### {L['label_editor'] if 'label_editor' in L else 'Editor'}")
                st.session_state[key_sez] = st.text_area("Edit", value=st.session_state[key_sez], height=500, key=f"area_{key_sez}")

    # --- TAB 3: ANTEPRIMA REALISTICA ---
    with tabs[2]:
        st.subheader(L["preview_tit"])
        # Costruzione dell'HTML per l'anteprima
        preview_html = f"<div class='preview-box'>"
        preview_html += f"<h1 style='text-align:center; font-size:48px; color:#000;'>{titolo_l.upper()}</h1>"
        if autore_l:
            preview_html += f"<h3 style='text-align:center; font-style:italic; font-size:24px;'>{autore_l}</h3>"
        preview_html += "<div style='height:300px'></div>" # Spazio per frontespizio
        
        # Iterazione su tutte le sezioni salvate
        for s in opzioni_finali:
            sk = f"txt_{s.replace(' ', '_').replace('.', '')}"
            if sk in st.session_state and st.session_state[sk].strip():
                preview_html += f"<h2 style='page-break-before:always; color:#000; font-size:32px;'>{s.upper()}</h2>"
                # Trasformazione newline in <br> per HTML
                testo_formattato = st.session_state[sk].replace('\n', '<br>')
                preview_html += f"<p style='text-align:justify;'>{testo_formattato}</p>"
        
        preview_html += "</div>"
        st.markdown(preview_html, unsafe_allow_html=True)

    # --- TAB 4: ESPORTAZIONE PROFESSIONALE ---
    with tabs[3]:
        st.subheader("📑 Finalizzazione ed Esportazione")
        st.write("Puoi scaricare il tuo libro in formato Word professionale. Il file conterrà l'indice, tutti i capitoli e i quiz generati.")
        
        if st.button(L["btn_word"]):
            doc = Document()
            # Impostazioni Titolo
            doc.add_heading(titolo_l, 0)
            if autore_l: doc.add_paragraph(f"Autore: {autore_l}")
            
            # Aggiunta Indice nel documento
            doc.add_page_break()
            doc.add_heading("INDICE", level=1)
            doc.add_paragraph(st.session_state.get("indice_raw", ""))
            
            # Aggiunta Capitoli
            for s in opzioni_finali:
                sk = f"txt_{s.replace(' ', '_').replace('.', '')}"
                if sk in st.session_state:
                    doc.add_page_break()
                    doc.add_heading(s.upper(), level=1)
                    doc.add_paragraph(st.session_state[sk])
            
            # Gestione del buffer di memoria per il download
            buf_word = BytesIO()
            doc.save(buf_word)
            buf_word.seek(0)
            st.download_button(L["btn_word"], buf_word, file_name=f"{titolo_l.replace(' ','_')}.docx")

else:
    # Pagina di Benvenuto
    st.info("👋 Benvenuto nell'Ebook Creator di Antonino. Inserisci Titolo e Trama nella sidebar per sbloccare l'IA.")
    st.markdown("""
    ### Come Funziona:
    1. **Configura**: Scegli lingua, genere e stile.
    2. **Indice**: Lascia che l'IA crei una struttura logica coerente.
    3. **Scrittura**: Genera ogni capitolo con un focus sull'analisi profonda (min 2000 parole).
    4. **Quiz**: Aggiungi test di valutazione direttamente nel testo.
    5. **Esporta**: Scarica il tuo libro pronto per la pubblicazione!
    """)
