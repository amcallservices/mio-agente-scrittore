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
    page_title="AI di Antonino: Crea il tuo Ebook",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DIZIONARIO TRADUZIONI INTEGRALE ---
TRADUZIONI = {
    "Italiano": {
        "sidebar_tit": "⚙️ Configurazione Editor",
        "t_book": "Titolo del Libro", "t_auth": "Nome Autore", "t_lang": "Lingua", "t_gen": "Genere", "t_plot": "Trama o Argomento",
        "btn_res": "🔄 RESET PROGETTO", "tabs": ["📊 Indice", "✍️ Scrittura", "📖 Anteprima", "📑 Esporta"],
        "btn_idx": "Genera Indice Professionale", "btn_sync": "Sincronizza Capitoli", "lbl_sec": "Sezione:",
        "btn_write": "✨ SCRIVI SEZIONE (2000+ parole)", "btn_edit": "🚀 RIELABORA", "msg_run": "Scrittura in corso...",
        "preface": "Prefazione", "ack": "Ringraziamenti", "preview": "📖 Vista Lettura"
    },
    "English": {
        "sidebar_tit": "⚙️ Editor Setup",
        "t_book": "Book Title", "t_auth": "Author Name", "t_lang": "Language", "t_gen": "Genre", "t_plot": "Plot or Topic",
        "btn_res": "🔄 RESET PROJECT", "tabs": ["📊 Index", "✍️ Writing", "📖 Preview", "📑 Export"],
        "btn_idx": "Generate Professional Index", "btn_sync": "Sync Chapters", "lbl_sec": "Section:",
        "btn_write": "✨ WRITE SECTION (2000+ words)", "btn_edit": "🚀 REWRITE", "msg_run": "Writing in progress...",
        "preface": "Preface", "ack": "Acknowledgements", "preview": "📖 Reading View"
    },
    "Deutsch": {
        "sidebar_tit": "⚙️ Editor-Setup",
        "t_book": "Buchtitel", "t_auth": "Autor", "t_lang": "Sprache", "t_gen": "Genre", "t_plot": "Inhalt",
        "btn_res": "🔄 ZURÜCKSETZEN", "tabs": ["📊 Index", "✍️ Schreiben", "📖 Vorschau", "📑 Export"],
        "btn_idx": "Index generieren", "btn_sync": "Sync Kapitel", "lbl_sec": "Abschnitt:",
        "btn_write": "✨ ABSCHNITT SCHREIBEN", "btn_edit": "🚀 ÜBERARBEITEN", "msg_run": "Schreiben läuft...",
        "preface": "Vorwort", "ack": "Danksagungen", "preview": "📖 Leseansicht"
    },
    "Français": {
        "sidebar_tit": "⚙️ Configuration",
        "t_book": "Titre du livre", "t_auth": "Auteur", "t_lang": "Langue", "t_gen": "Genre", "t_plot": "Intrigue",
        "btn_res": "🔄 RÉINITIALISER", "tabs": ["📊 Index", "✍️ Écriture", "📖 Aperçu", "📑 Export"],
        "btn_idx": "Générer l'index", "btn_sync": "Sync Chapitres", "lbl_sec": "Section:",
        "btn_write": "✨ ÉCRIRE LA SECTION", "btn_edit": "🚀 REFORMULER", "msg_run": "Écriture...",
        "preface": "Préface", "ack": "Remerciements", "preview": "📖 Vue Lecture"
    },
    "Español": {
        "sidebar_tit": "⚙️ Configuración",
        "t_book": "Título del libro", "t_auth": "Autor", "t_lang": "Idioma", "t_gen": "Género", "t_plot": "Trama",
        "btn_res": "🔄 REINICIAR", "tabs": ["📊 Índice", "✍️ Escritura", "📖 Vista previa", "📑 Exportar"],
        "btn_idx": "Generar índice", "btn_sync": "Sync Capítulos", "lbl_sec": "Sección:",
        "btn_write": "✨ ESCRIBIR SECCIÓN", "btn_edit": "🚀 REESCRIBIR", "msg_run": "Escribiendo...",
        "preface": "Prefacio", "ack": "Agradecimientos", "preview": "📖 Vista de lectura"
    },
    "Română": {
        "sidebar_tit": "⚙️ Configurare",
        "t_book": "Titlul cărții", "t_auth": "Autor", "t_lang": "Limbă", "t_gen": "Gen", "t_plot": "Subiect",
        "btn_res": "🔄 RESETARE", "tabs": ["📊 Index", "✍️ Scriere", "📖 Previzualizare", "📑 Export"],
        "btn_idx": "Generează index", "btn_sync": "Sincronizează", "lbl_sec": "Secțiune:",
        "btn_write": "✨ SCRIE SECȚIUNEA", "btn_edit": "🚀 REFORMULEAZĂ", "msg_run": "Se scrie...",
        "preface": "Prefață", "ack": "Mulțumiri", "preview": "📖 Vizualizare lectură"
    },
    "Русский": {
        "sidebar_tit": "⚙️ Настройки",
        "t_book": "Название книги", "t_auth": "Автор", "t_lang": "Язык", "t_gen": "Жанр", "t_plot": "Сюжет",
        "btn_res": "🔄 СБРОС", "tabs": ["📊 Оглавление", "✍️ Написание", "📖 Предпросмотр", "📑 Экспорт"],
        "btn_idx": "Создать оглавление", "btn_sync": "Синхронизировать", "lbl_sec": "Раздел:",
        "btn_write": "✨ НАПИСАТЬ РАЗДЕЛ", "btn_edit": "🚀 ПЕРЕПИСАТЬ", "msg_run": "Пишем...",
        "preface": "Предисловие", "ack": "Благодарности", "preview": "📖 Режим чтения"
    },
    "中文": {
        "sidebar_tit": "⚙️ 设置",
        "t_book": "书名", "t_auth": "作者", "t_lang": "语言", "t_gen": "体裁", "t_plot": "情节",
        "btn_res": "🔄 重置", "tabs": ["📊 目录", "✍️ 写作", "📖 预览", "📑 导出"],
        "btn_idx": "生成目录", "btn_sync": "同步章节", "lbl_sec": "选择章节:",
        "btn_write": "✨ 编写章节", "btn_edit": "🚀 重写", "msg_run": "正在写作...",
        "preface": "前言", "ack": "致谢", "preview": "📖 阅读视图"
    }
}

# --- CSS ---
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
.custom-title { font-size: 38px; font-weight: bold; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 15px; border: 1px solid #dee2e6; margin-bottom: 20px; }
.stButton>button { width: 100%; border-radius: 12px; height: 3.8em; font-weight: bold; background-color: #007BFF !important; color: white !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.15); }
.preview-box { background-color: white; padding: 40px; border: 1px solid #d3d6db; border-radius: 10px; height: 600px; overflow-y: scroll; font-family: 'Times New Roman', serif; line-height: 1.8; color: #222; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    lingua_scelta = st.selectbox("🌐 Choose Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lingua_scelta]
    st.title(L["sidebar_tit"])
    titolo_l = st.text_input(L["t_book"])
    autore_l = st.text_input(L["t_auth"])
    genere = st.selectbox(L["t_gen"], ["Manuale Tecnico", "Saggio", "Psicologia", "Business", "Motivazionale", "Thriller", "Fantasy"])
    trama = st.text_area(L["t_plot"], height=150)
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- FUNZIONI ---
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
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
            mappa[cap_key] = descr
    st.session_state['mappa_capitoli'] = mappa
    st.session_state['lista_capitoli'] = list(mappa.keys())

# --- UI PRINCIPALE ---
st.markdown(f'<div class="custom-title">AI: {titolo_l if titolo_l else "Ebook Creator"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    S_PROMPT = f"World Authority in {genere}. Write ONLY in {lingua_scelta}. 2000+ words per chapter. Deep technical detail, zero repetition."
    t1, t2, t3, t4 = st.tabs(L["tabs"])

    with t1:
        if st.button(L["btn_idx"]):
            st.session_state["indice_raw"] = chiedi_gpt(f"Create long index for '{titolo_l}' in {lingua_scelta}.", "Editor.")
            sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Index Editor", value=st.session_state.get("indice_raw", ""), height=300)
        if st.button(L["btn_sync"]): sync_capitoli(); st.rerun()

    with t2:
        if "lista_capitoli" not in st.session_state: sync_capitoli()
        opzioni = [L["preface"]] + st.session_state.get("lista_capitoli", []) + [L["ack"]]
        cap_sel = st.selectbox(L["lbl_sec"], opzioni)
        key_sez = f"txt_{cap_sel.replace(' ', '_')}"
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button(L["btn_write"]):
                with st.spinner(L["msg_run"]):
                    st.session_state[key_sez] = chiedi_gpt(f"Write a massive 2000-word chapter on '{cap_sel}' for '{titolo_l}'. In {lingua_scelta}.", S_PROMPT)
        with c2:
            istr = st.text_input("Edit Instruction", key=f"istr_{key_sez}")
            if st.button(L["btn_edit"]):
                with st.spinner(L["msg_run"]):
                    st.session_state[key_sez] = chiedi_gpt(f"Rewrite/Expand based on: {istr}. Text:\n{st.session_state.get(key_sez, '')}", S_PROMPT)
        st.session_state[key_sez] = st.text_area("Text Editor", value=st.session_state.get(key_sez, ""), height=400)

    with t3:
        p_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        for s in [f"txt_{x.replace(' ', '_')}" for x in opzioni]:
            if s in st.session_state:
                p_html += f"<h2>{s.replace('txt_', '').replace('_', ' ')}</h2><p>{st.session_state[s].replace('\\n', '<br>')}</p>"
        st.markdown(p_html + "</div>", unsafe_allow_html=True)

    with t4:
        # Codice export PDF/Word (come versioni precedenti)
        st.write("Ready for export.")
else:
    st.info("👋 Setup Sidebar to start.")
