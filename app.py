import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- API CONNECTION ---
# Assicurati che la tua chiave sia nei secrets di Streamlit
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="AI di Antonino: Ebook Mondiale Creator",
    layout="wide",
    initial_sidebar_state="expanded" # Sidebar sempre aperta
)

# --- DIZIONARIO TRADUZIONI INTERFACCIA (8 LINGUE) ---
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
        "preview_tit": "📖 Vista Lettura Professionale", "btn_word": "📥 Scarica Ebook (.docx)"
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
        "preview_tit": "📖 Professional Reading View", "btn_word": "📥 Download Ebook (.docx)"
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
        "preview_tit": "📖 Leseansicht", "btn_word": "📥 Ebook herunterladen (.docx)"
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
        "preview_tit": "📖 Vue Lecture", "btn_word": "📥 Télécharger (.docx)"
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
        "preview_tit": "📖 Vista de lectura", "btn_word": "📥 Descargar (.docx)"
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
        "preview_tit": "📖 Vizualizare lectură", "btn_word": "📥 Descarcă (.docx)"
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

# --- BLOCCO CSS (UI PROFESSIONALE & SIDEBAR) ---
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* Sidebar larga e bloccata */
section[data-testid="stSidebar"] { min-width: 380px !important; max-width: 380px !important; }

.custom-title {
    font-size: 38px; font-weight: bold; color: #1E1E1E; text-align: center;
    padding: 20px; background-color: #f0f4f8; border-radius: 15px;
    margin-bottom: 25px; border: 1px solid #d1d9e6;
}

/* Anteprima Ebook foglio bianco */
.preview-box {
    background-color: white; padding: 60px; border: 1px solid #d3d6db;
    border-radius: 5px; height: 750px; overflow-y: scroll;
    font-family: 'Times New Roman', serif; line-height: 1.8; color: #222;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
}

/* Pulsanti Blu Antonino */
.stButton>button {
    width: 100%; border-radius: 10px; height: 3.8em; font-weight: bold;
    background-color: #007BFF !important; color: white !important;
    font-size: 16px; border: none; box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
}
.stButton>button:hover { background-color: #0056b3 !important; transform: translateY(-2px); }
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
    if not testo:
        st.session_state['lista_capitoli'] = []
        return
    linee = testo.split('\n')
    trovati = []
    for l in linee:
        if re.search(r'^(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|\d+\.)', l.strip(), re.I):
            trovati.append(l.strip())
    st.session_state['lista_capitoli'] = trovati

# --- SIDEBAR (CONFIGURAZIONE TOTALE) ---
with st.sidebar:
    lang_choice = st.selectbox("🌐 Select Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lang_choice]
    
    st.title(L["side_tit"])
    titolo_l = st.text_input(L["lbl_tit"])
    autore_l = st.text_input(L["lbl_auth"])
    
    # TUTTI I GENERI RICHIESTI
    genere = st.selectbox(L["lbl_gen"], [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Marketing", "Motivazionale / Self-Help", "Biografia", 
        "Libro di Quiz / Test", "Saggio Breve", "Romanzo Rosa", "Romanzo Storico", 
        "Thriller", "Noir", "Fantasy", "Fantascienza"
    ])
    
    modalita = st.selectbox(L["lbl_style"], ["Standard", "Professionale (Accademica/Tecnica)"])
    trama = st.text_area(L["lbl_plot"], height=150)
    
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- LOGICA FILO LOGICO E FASI ---
fasi_map = {
    "Italiano": ["Introduzione e Setup", "Sviluppo Analitico", "Conclusione e Sintesi"],
    "English": ["Intro & Setup", "Analytical Development", "Summary & Conclusion"]
}
fasi = fasi_map.get(lang_choice, ["Part 1", "Part 2", "Part 3"])

# --- UI PRINCIPALE ---
st.markdown(f'<div class="custom-title">AI: {titolo_l if titolo_l else "Ebook Creator Professional"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    # System Prompt Autorità Mondiale
    livello = "tecnico e accademico" if modalita == "Professionale (Accademica/Tecnica)" else "fluido e narrativo"
    S_PROMPT = f"World Authority in {genere}. Language: {lang_choice}. Style: {livello}. Target: 2000+ words. Logical coherence is mandatory."

    tabs = st.tabs(L["tabs"])

    # --- TAB 1: INDICE ---
    with tabs[0]:
        if st.button(L["btn_idx"]):
            p_idx = f"Create a long, logical index for a '{genere}' book titled '{titolo_l}' in {lang_choice}. Based on: {trama}."
            st.session_state["indice_raw"] = chiedi_gpt(p_idx, "Professional Book Editor.")
            sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area(L["lbl_tit"], value=st.session_state.get("indice_raw", ""), height=350)
        
        if st.button(L["btn_sync"]):
            sync_capitoli()
            st.success("OK!")

    # --- TAB 2: SCRITTURA & QUIZ ---
    with tabs[1]:
        lista_c = st.session_state.get("lista_capitoli", [])
        if not lista_c:
            st.warning("Generate Index first.")
        else:
            opzioni = [L["preface"]] + lista_c + [L["ack"]]
            cap_sel = st.selectbox(L["lbl_sec"], opzioni)
            key_sez = f"txt_{cap_sel.replace(' ', '_')}"

            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        # Filo Logico: Passiamo l'indice come contesto
                        ctx = f"Full Index: {st.session_state['indice_raw']}. Current Chapter: {cap_sel}."
                        full_txt = ""
                        for f in fasi:
                            full_txt += chiedi_gpt(f"{ctx}\nWrite part: {f}. Be extremely detailed (2000+ words total).", S_PROMPT) + "\n\n"
                        st.session_state[key_sez] = full_txt
            
            with c2:
                istr = st.text_input(L["lbl_istr"] if "lbl_istr" in L else "IA Instruction", key=f"istr_{key_sez}")
                if st.button(L["btn_edit"]):
                    with st.spinner("Processing..."):
                        st.session_state[key_sez] = chiedi_gpt(f"Modify this text: {istr}. Text:\n{st.session_state.get(key_sez,'')}", S_PROMPT)

            with c3:
                if st.button(L["btn_quiz"]):
                    if key_sez in st.session_state:
                        with st.spinner("Generating Quiz..."):
                            p_q = f"Create a 10-question multiple choice quiz with answers based on this text:\n{st.session_state[key_sez]}"
                            quiz = chiedi_gpt(p_q, "Quiz Expert.")
                            st.session_state[key_sez] += f"\n\n---\n\n### QUIZ / TEST\n\n" + quiz
                            st.rerun()

            st.session_state[key_sez] = st.text_area("Editor", value=st.session_state.get(key_sez, ""), height=450)

    # --- TAB 3: ANTEPRIMA ---
    with tabs[2]:
        st.subheader(L["preview_tit"])
        preview = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: preview += f"<h3 style='text-align:center;'>{autore_l}</h3>"
        preview += "<hr><br>"
        for s in [L["preface"]] + lista_c + [L["ack"]]:
            sk = f"txt_{s.replace(' ', '_')}"
            if sk in st.session_state:
                preview += f"<h2>{s.upper()}</h2><p>{st.session_state[sk].replace('\\n', '<br>')}</p><br>"
        st.markdown(preview + "</div>", unsafe_allow_html=True)

    # --- TAB 4: ESPORTA ---
    with tabs[3]:
        if st.button(L["btn_word"]):
            doc = Document()
            doc.add_heading(titolo_l, 0)
            if autore_l: doc.add_paragraph(f"Author: {autore_l}")
            for s in [L["preface"]] + lista_c + [L["ack"]]:
                sk = f"txt_{s.replace(' ', '_')}"
                if sk in st.session_state:
                    doc.add_page_break()
                    doc.add_heading(s, level=1)
                    doc.add_paragraph(st.session_state[sk])
            buf = BytesIO(); doc.save(buf); buf.seek(0)
            st.download_button("💾 Save .docx", buf, file_name=f"{titolo_l}.docx")

else:
    st.info("👋 Setup Title and Topic in the sidebar to begin.")
