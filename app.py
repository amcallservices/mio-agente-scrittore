import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# --- API CONNECTION ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CONFIGURAZIONE PAGINA (SIDEBAR FISSA) ---
st.set_page_config(
    page_title="AI di Antonino: Crea il tuo Ebook",
    layout="wide",
    initial_sidebar_state="expanded" # Forza l'apertura del menu a sinistra
)

# --- DIZIONARIO TRADUZIONI INTEGRALE (8 LINGUE) ---
TRADUZIONI = {
    "Italiano": {
        "sidebar_tit": "⚙️ Configurazione Editor",
        "t_book": "Titolo del Libro", "t_auth": "Nome Autore", "t_lang": "Lingua", "t_gen": "Genere", "t_plot": "Trama o Argomento",
        "btn_res": "🔄 RESET PROGETTO", "tabs": ["📊 Indice", "✍️ Scrittura", "📖 Anteprima", "📑 Esporta"],
        "btn_idx": "Genera Indice Professionale", "btn_sync": "Sincronizza Capitoli", "lbl_sec": "Sezione:",
        "btn_write": "✨ SCRIVI SEZIONE (2000+ parole)", "btn_edit": "🚀 RIELABORA", "msg_run": "Scrittura in corso...",
        "preface": "Prefazione", "ack": "Ringraziamenti", "preview": "📖 Vista Lettura", "btn_pdf": "Scarica PDF", "btn_word": "Scarica Word"
    },
    "English": {
        "sidebar_tit": "⚙️ Editor Setup",
        "t_book": "Book Title", "t_auth": "Author Name", "t_lang": "Language", "t_gen": "Genre", "t_plot": "Plot or Topic",
        "btn_res": "🔄 RESET PROJECT", "tabs": ["📊 Index", "✍️ Writing", "📖 Preview", "📑 Export"],
        "btn_idx": "Generate Professional Index", "btn_sync": "Sync Chapters", "lbl_sec": "Section:",
        "btn_write": "✨ WRITE SECTION (2000+ words)", "btn_edit": "🚀 REWRITE", "msg_run": "Writing in progress...",
        "preface": "Preface", "ack": "Acknowledgements", "preview": "📖 Reading View", "btn_pdf": "Download PDF", "btn_word": "Download Word"
    },
    "Deutsch": {
        "sidebar_tit": "⚙️ Editor-Setup",
        "t_book": "Buchtitel", "t_auth": "Autor", "t_lang": "Sprache", "t_gen": "Genre", "t_plot": "Inhalt",
        "btn_res": "🔄 ZURÜCKSETZEN", "tabs": ["📊 Index", "✍️ Schreiben", "📖 Vorschau", "📑 Export"],
        "btn_idx": "Index generieren", "btn_sync": "Sync Kapitel", "lbl_sec": "Abschnitt:",
        "btn_write": "✨ ABSCHNITT SCHREIBEN", "btn_edit": "🚀 ÜBERARBEITEN", "msg_run": "Schreiben läuft...",
        "preface": "Vorwort", "ack": "Danksagungen", "preview": "📖 Leseansicht", "btn_pdf": "PDF herunterladen", "btn_word": "Word herunterladen"
    },
    "Français": {
        "sidebar_tit": "⚙️ Configuration",
        "t_book": "Titre du livre", "t_auth": "Auteur", "t_lang": "Langue", "t_gen": "Genre", "t_plot": "Intrigue",
        "btn_res": "🔄 RÉINITIALISER", "tabs": ["📊 Index", "✍️ Écriture", "📖 Aperçu", "📑 Export"],
        "btn_idx": "Générer l'index", "btn_sync": "Sync Chapitres", "lbl_sec": "Section:",
        "btn_write": "✨ ÉCRIRE LA SECTION", "btn_edit": "🚀 REFORMULER", "msg_run": "Écriture...",
        "preface": "Préface", "ack": "Remerciements", "preview": "📖 Vue Lecture", "btn_pdf": "Télécharger PDF", "btn_word": "Télécharger Word"
    },
    "Español": {
        "sidebar_tit": "⚙️ Configuración",
        "t_book": "Título del libro", "t_auth": "Autor", "t_lang": "Idioma", "t_gen": "Género", "t_plot": "Trama",
        "btn_res": "🔄 REINICIAR", "tabs": ["📊 Índice", "✍️ Escritura", "📖 Vista previa", "📑 Exportar"],
        "btn_idx": "Generar índice", "btn_sync": "Sync Capítulos", "lbl_sec": "Sección:",
        "btn_write": "✨ ESCRIBIR SECCIÓN", "btn_edit": "🚀 REESCRIBIR", "msg_run": "Escribiendo...",
        "preface": "Prefacio", "ack": "Agradecimientos", "preview": "📖 Vista de lectura", "btn_pdf": "Bajar PDF", "btn_word": "Bajar Word"
    },
    "Română": {
        "sidebar_tit": "⚙️ Configurare",
        "t_book": "Titlul cărții", "t_auth": "Autor", "t_lang": "Limbă", "t_gen": "Gen", "t_plot": "Subiect",
        "btn_res": "🔄 RESETARE", "tabs": ["📊 Index", "✍️ Scriere", "📖 Previzualizare", "📑 Export"],
        "btn_idx": "Generează index", "btn_sync": "Sincronizează", "lbl_sec": "Secțiune:",
        "btn_write": "✨ SCRIE SECȚIUNEA", "btn_edit": "🚀 REFORMULEAZĂ", "msg_run": "Se scrie...",
        "preface": "Prefață", "ack": "Mulțumiri", "preview": "📖 Vizualizare lectură", "btn_pdf": "Descarcă PDF", "btn_word": "Descarcă Word"
    },
    "Русский": {
        "sidebar_tit": "⚙️ Настройки",
        "t_book": "Название книги", "t_auth": "Автор", "t_lang": "Язык", "t_gen": "Жанр", "t_plot": "Сюжет",
        "btn_res": "🔄 СБРОС", "tabs": ["📊 Оглавление", "✍️ Написание", "📖 Предпросмотр", "📑 Экспорт"],
        "btn_idx": "Создать оглавление", "btn_sync": "Синхронизировать", "lbl_sec": "Раздел:",
        "btn_write": "✨ НАПИСАТЬ РАЗДЕЛ", "btn_edit": "🚀 ПЕРЕПИСАТЬ", "msg_run": "Пишем...",
        "preface": "Предисловие", "ack": "Благодарности", "preview": "📖 Режим чтения", "btn_pdf": "Скачать PDF", "btn_word": "Скачать Word"
    },
    "中文": {
        "sidebar_tit": "⚙️ 设置",
        "t_book": "书名", "t_auth": "作者", "t_lang": "语言", "t_gen": "体裁", "t_plot": "情节",
        "btn_res": "🔄 重置", "tabs": ["📊 目录", "✍️ 写作", "📖 预览", "📑 导出"],
        "btn_idx": "生成目录", "btn_sync": "同步章节", "lbl_sec": "选择章节:",
        "btn_write": "✨ 编写章节", "btn_edit": "🚀 重写", "msg_run": "正在写作...",
        "preface": "前言", "ack": "致谢", "preview": "📖 阅读视图", "btn_pdf": "下载 PDF", "btn_word": "下载 Word"
    }
}

# --- CSS PERSONALIZZATO ---
st.markdown("""
<style>
/* Sidebar bloccata e visibile */
section[data-testid="stSidebar"] { min-width: 350px !important; }
.custom-title { font-size: 38px; font-weight: bold; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 15px; border: 1px solid #dee2e6; margin-bottom: 20px; color: #1E1E1E; }
/* Pulsanti ad alta visibilità */
.stButton>button { width: 100%; border-radius: 12px; height: 3.8em; font-weight: bold; background-color: #007BFF !important; color: white !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.15); border: none; font-size: 16px !important; }
.stButton>button:hover { background-color: #0056b3 !important; transform: translateY(-2px); }
/* Anteprima Ebook */
.preview-box { background-color: white; padding: 40px; border: 1px solid #d3d6db; border-radius: 10px; height: 600px; overflow-y: scroll; font-family: 'Times New Roman', serif; line-height: 1.8; color: #222; }
</style>
""", unsafe_allow_html=True)

# --- PDF CLASS ---
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1 and self.autore:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"Author: {self.autore}", 0, 0, 'C')
            self.ln(10)

# --- FUNZIONI CORE ---
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

# --- SIDEBAR (SEMPRE ATTIVA) ---
with st.sidebar:
    lang_choice = st.selectbox("🌐 Lingua / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lang_choice]
    st.title(L["sidebar_tit"])
    titolo_l = st.text_input(L["t_book"])
    autore_l = st.text_input(L["t_auth"])
    genere = st.selectbox(L["t_gen"], ["Manuale Tecnico", "Saggio", "Psicologia", "Business", "Motivazionale", "Thriller", "Fantasy"])
    trama = st.text_area(L["t_plot"], height=150)
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.markdown(f'<div class="custom-title">AI: {titolo_l if titolo_l else "Ebook Creator"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    S_PROMPT = f"World-class Authority in {genere}. Write ONLY in {lang_choice}. Focus: {titolo_l}. Topic: {trama}. Aim for 2000+ words per chapter with deep analytical detail."
    t1, t2, t3, t4 = st.tabs(L["tabs"])

    with t1:
        if st.button(L["btn_idx"]):
            st.session_state["indice_raw"] = chiedi_gpt(f"Create a very long and professional index for '{titolo_l}' in {lang_choice} based on: {trama}.", "Professional Editor.")
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
                    st.session_state[key_sez] = chiedi_gpt(f"Write a massive, 2000-word authoritative chapter on '{cap_sel}' for the book '{titolo_l}'. Include technical details and subheadings. Language: {lang_choice}.", S_PROMPT)
        with c2:
            istr = st.text_input("Istruzione Modifica / Edit Instruction", key=f"istr_{key_sez}")
            if st.button(L["btn_edit"]):
                with st.spinner(L["msg_run"]):
                    st.session_state[key_sez] = chiedi_gpt(f"Rewrite and expand the following text based on this instruction: {istr}. Text:\n{st.session_state.get(key_sez, '')}", S_PROMPT)
        
        # Editor Manuale Sempre Salvato
        st.session_state[key_sez] = st.text_area("Text Editor", value=st.session_state.get(key_sez, ""), height=400, key=f"area_{key_sez}")

    with t3:
        st.subheader(L["preview"])
        p_html = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: p_html += f"<h3 style='text-align:center; font-style:italic;'>di {autore_l}</h3>"
        p_html += "<hr><br>"
        for s in [L["preface"]] + st.session_state.get("lista_capitoli", []) + [L["ack"]]:
            s_key = f"txt_{s.replace(' ', '_')}"
            if s_key in st.session_state:
                p_html += f"<h2>{s.upper()}</h2><p>{st.session_state[s_key].replace('\\n', '<br>')}</p><br>"
        st.markdown(p_html + "</div>", unsafe_allow_html=True)

    with t4:
        col_pdf, col_word = st.columns(2)
        lista_export = [L["preface"]] + st.session_state.get("lista_capitoli", []) + [L["ack"]]
        
        with col_pdf:
            if st.button(L["btn_pdf"]):
                pdf = PDF(autore_l); pdf.set_auto_page_break(True, 15); pdf.add_page()
                pdf.set_font("Arial", "B", 30); pdf.ln(80); pdf.cell(0, 20, titolo_l.upper(), 0, 1, "C")
                for s in lista_export:
                    s_key = f"txt_{s.replace(' ', '_')}"
                    if s_key in st.session_state:
                        pdf.add_page(); pdf.set_font("Arial", "B", 18); pdf.cell(0, 10, s.upper(), 0, 1)
                        pdf.ln(10); pdf.set_font("Arial", "", 12)
                        pdf.multi_cell(0, 8, st.session_state[s_key].encode('latin-1', 'replace').decode('latin-1'))
                st.download_button(L["btn_pdf"], pdf.output(dest='S').encode('latin-1'), file_name=f"{titolo_l}.pdf")
        
        with col_word:
            if st.button(L["btn_word"]):
                doc = Document(); doc.add_heading(titolo_l, 0)
                if autore_l: doc.add_paragraph(f"Author: {autore_l}")
                for s in lista_export:
                    s_key = f"txt_{s.replace(' ', '_')}"
                    if s_key in st.session_state:
                        doc.add_page_break(); doc.add_heading(s.upper(), level=1); doc.add_paragraph(st.session_state[s_key])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button(L["btn_word"], buf_w, file_name=f"{titolo_l}.docx")
else:
    st.info("👋 Compila Titolo e Trama a sinistra per iniziare.")
