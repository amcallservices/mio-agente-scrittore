import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# =================================================================
# 1. CONNESSIONE API E SETUP DI SISTEMA
# =================================================================
# Configurazione chiave API tramite i secrets di Streamlit
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Errore critico: OpenAI API Key non trovata. Controlla i Secrets.")

# Configurazione Pagina: Sidebar larga e layout wide per l'editor
st.set_page_config(
    page_title="AI di Antonino: Ebook Mondiale Creator PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================================================================
# 2. DIZIONARIO TRADUZIONI INTEGRALE (8 LINGUE)
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
        "preview_tit": "📖 Vista Lettura Professionale", "btn_word": "📥 Scarica in Word (.docx)", "btn_pdf": "📥 Scarica in PDF (.pdf)",
        "msg_err_idx": "Genera l'indice prima di procedere.", "msg_success_sync": "Capitoli sincronizzati!",
        "label_editor": "Editor di Testo Professionale"
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
        "preview_tit": "📖 Professional Reading View", "btn_word": "📥 Download Word (.docx)", "btn_pdf": "📥 Download PDF (.pdf)"
    },
    "Deutsch": {
        "side_tit": "⚙️ Editor-Setup",
        "lbl_tit": "Buchtitel", "lbl_auth": "Autor", "lbl_lang": "Sprache", 
        "lbl_gen": "Genre", "lbl_style": "Schreibstil", "lbl_plot": "Inhalt",
        "btn_res": "🔄 ZURÜCKSETZEN", "tabs": ["📊 1. Index", "✍️ 2. Schreiben & Quiz", "📖 3. Vorschau", "📑 4. Export"],
        "btn_idx": "🚀 Index generieren", "btn_sync": "✅ Kapitel synchronisieren",
        "lbl_sec": "Abschnitt wählen:", "btn_write": "✨ ABSCHNITT SCHREIBEN",
        "btn_quiz": "🧠 QUIZ HINZUFÜGEN", "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    },
    "Français": {
        "side_tit": "⚙️ Configuration",
        "lbl_tit": "Titre", "lbl_auth": "Auteur", "lbl_lang": "Langue", 
        "lbl_gen": "Genre", "lbl_style": "Style", "lbl_plot": "Intrigue",
        "btn_res": "🔄 RÉINITIALISER", "tabs": ["📊 1. Index", "✍️ 2. Écriture", "📖 Aperçu", "📑 Export"],
        "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    },
    "Español": {
        "side_tit": "⚙️ Configuración",
        "lbl_tit": "Título", "lbl_auth": "Autor", "lbl_lang": "Idioma", 
        "lbl_gen": "Género", "lbl_style": "Estilo", "lbl_plot": "Trama",
        "btn_res": "🔄 REINICIAR", "tabs": ["📊 1. Índice", "✍️ 2. Escritura", "📖 Vista", "📑 Exportar"],
        "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    },
    "Română": {
        "side_tit": "⚙️ Configurare", "lbl_tit": "Titlu", "lbl_auth": "Autor", "lbl_lang": "Limbă", 
        "lbl_gen": "Gen", "lbl_style": "Stil", "lbl_plot": "Subiect", "btn_res": "🔄 RESETARE",
        "tabs": ["📊 Index", "✍️ Scriere", "📖 Previzualizare", "📑 Export"],
        "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    },
    "Русский": {
        "side_tit": "⚙️ Настройки", "lbl_tit": "Название", "lbl_auth": "Автор", "lbl_lang": "Язык", 
        "lbl_gen": "Жанр", "lbl_style": "Стиль", "lbl_plot": "Сюжет", "btn_res": "🔄 СБРОС",
        "tabs": ["📊 Оглавление", "✍️ Письмо", "📖 Просмотр", "📑 Экспорт"],
        "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    },
    "中文": {
        "side_tit": "⚙️ 设置", "lbl_tit": "书名", "lbl_auth": "作者", "lbl_lang": "语言", 
        "lbl_gen": "体裁", "lbl_style": "风格", "lbl_plot": "情节", "btn_res": "🔄 重置",
        "tabs": ["📊 目录", "✍️ 写作", "📖 预览", "📑 导出"],
        "btn_word": "📥 Word (.docx)", "btn_pdf": "📥 PDF (.pdf)"
    }
}

# =================================================================
# 3. CSS CUSTOM: SIDEBAR SCURA E PULSANTI BLU
# =================================================================
st.markdown("""
<style>
/* Pulizia layout */
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* SIDEBAR SCURA */
section[data-testid="stSidebar"] { 
    min-width: 400px !important; 
    max-width: 400px !important; 
    background-color: #121212 !important; 
    border-right: 1px solid #222;
}

/* Testi sidebar bianchi */
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f0f0f0 !important;
}

/* Titolo Header */
.custom-title {
    font-size: 38px; font-weight: 800; color: #111; text-align: center;
    padding: 20px; background-color: #ffffff; border-radius: 12px;
    margin-bottom: 25px; border-bottom: 5px solid #007BFF;
}

/* Anteprima Ebook */
.preview-box {
    background-color: #ffffff; padding: 60px; border: 1px solid #ddd;
    border-radius: 4px; height: 850px; overflow-y: scroll;
    font-family: 'Georgia', serif; line-height: 1.8; color: #111;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.1); margin: 0 auto;
}

/* PULSANTI BLU */
.stButton>button {
    width: 100%; border-radius: 12px; height: 4em; font-weight: bold;
    background-color: #007BFF !important; color: white !important;
    font-size: 18px !important; border: none; 
    box-shadow: 0px 5px 15px rgba(0, 123, 255, 0.3);
    transition: 0.3s;
}
.stButton>button:hover { background-color: #0056b3 !important; transform: scale(1.02); }

/* Selettori Sidebar */
.stSelectbox div[data-baseweb="select"] > div { background-color: #222 !important; color: white !important; border: 1px solid #444; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. CLASSE PDF PERSONALIZZATA
# =================================================================
class EbookPDF(FPDF):
    def __init__(self, titolo, autore):
        super().__init__()
        self.titolo = titolo
        self.autore = autore

    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"{self.titolo} - {self.autore}", 0, 0, 'R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def add_chapter(self, title, body):
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.multi_cell(0, 10, title.upper())
        self.ln(10)
        self.set_font('Arial', '', 12)
        # Sostituzione caratteri non standard per FPDF (latin-1 safe)
        body_clean = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 8, body_clean)

# =================================================================
# 5. FUNZIONI LOGICHE (GPT & SYNC)
# =================================================================
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7
        )
        testo = response.choices[0].message.content.strip()
        filtri = ["ecco", "certamente", "sicuramente", "ok", "here is", "sure"]
        righe = [l for l in testo.split("\n") if not any(l.lower().startswith(f) for f in filtri)]
        return "\n".join(righe).strip()
    except Exception as e:
        return f"Errore API: {str(e)}"

def sync_capitoli():
    testo = st.session_state.get("indice_raw", "")
    if not testo:
        st.session_state['lista_capitoli'] = []
        return
    validi = []
    pattern = r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)'
    for r in testo.split('\n'):
        if re.search(pattern, r.strip()):
            validi.append(r.strip())
    st.session_state['lista_capitoli'] = validi

# =================================================================
# 6. SIDEBAR SETUP (DARK)
# =================================================================
with st.sidebar:
    lang_choice = st.selectbox("🌐 Lingua / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lang_choice]
    
    st.title(L["side_tit"])
    titolo_l = st.text_input(L["lbl_tit"], placeholder="Titolo...")
    autore_l = st.text_input(L["lbl_auth"], placeholder="Autore...")
    
    generi = ["Saggio Scientifico", "Manuale Tecnico", "Psicologia", "Business", "Self-Help", "Biografia", "Quiz", "Rosa", "Thriller", "Fantasy", "Fantascienza"]
    genere = st.selectbox(L["lbl_gen"], generi)
    modalita = st.selectbox(L["lbl_style"], ["Standard", "Professionale"])
    trama = st.text_area(L["lbl_plot"], height=160, placeholder="Descrivi il tema...")
    
    st.markdown("---")
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# =================================================================
# 7. LOGICA DI SCRITTURA (FILO LOGICO)
# =================================================================
fasi_lavoro = ["Apertura e Concetti", "Analisi Profonda", "Chiusura e Sintesi"]

# =================================================================
# 8. UI PRINCIPALE (TAB SYSTEM)
# =================================================================
st.markdown(f'<div class="custom-title">Creator Ebook: {titolo_l if titolo_l else "Antonino PRO"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    S_PROMPT = f"Sei un'Autorità Mondiale in {genere}. Scrivi in {lang_choice}. Tono: {modalita}. Target: 2000 parole. Evita ripetizioni."

    tabs = st.tabs(L["tabs"])

    # TAB 1: INDICE
    with tabs[0]:
        if st.button(L["btn_idx"]):
            with st.spinner("Creazione indice..."):
                p = f"Crea un indice monumentale per '{titolo_l}' (Genere: {genere}) in {lang_choice}. Tema: {trama}."
                st.session_state["indice_raw"] = chiedi_gpt(p, "Editor Senior.")
                sync_capitoli()
        st.session_state["indice_raw"] = st.text_area("Indice", value=st.session_state.get("indice_raw", ""), height=400)
        if st.button(L["btn_sync"]):
            sync_capitoli(); st.success(L["msg_success_sync"])

    # TAB 2: SCRITTURA & QUIZ
    with tabs[1]:
        lista = st.session_state.get("lista_capitoli", [])
        if not lista:
            st.warning(L["msg_err_idx"])
        else:
            opzioni = [L["preface"]] + lista + [L["ack"]]
            cap_sel = st.selectbox(L["lbl_sec"], opzioni)
            key = f"txt_{cap_sel.replace(' ', '_').replace('.', '')}"

            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        testo_cap = ""
                        for fase in fasi_lavoro:
                            p_f = f"Indice: {st.session_state['indice_raw']}. Scrivi sezione '{cap_sel}', fase: {fase}."
                            testo_cap += chiedi_gpt(p_f, S_PROMPT) + "\n\n"
                        st.session_state[key] = testo_cap
            
            with c2:
                mod_in = st.text_input(L["btn_edit"], key=f"mod_{key}")
                if st.button(L["btn_edit"] + " 🪄"):
                    if key in st.session_state:
                        st.session_state[key] = chiedi_gpt(f"Modifica: {mod_in}. Testo:\n{st.session_state[key]}", S_PROMPT)
                        st.rerun()

            with c3:
                if st.button("🧠 QUIZ"):
                    if key in st.session_state:
                        with st.spinner("Creazione Quiz..."):
                            q = chiedi_gpt(f"Genera 10 quiz a risposta multipla sul capitolo {cap_sel}.", "Esperto Test.")
                            st.session_state[key] += f"\n\n---\n\n### TEST DI VALUTAZIONE\n\n" + q
                            st.rerun()

            if key in st.session_state:
                st.session_state[key] = st.text_area("Editor", value=st.session_state[key], height=500)

    # TAB 3: ANTEPRIMA
    with tabs[2]:
        html_p = f"<div class='preview-box'><h1 style='text-align:center;'>{titolo_l.upper()}</h1>"
        if autore_l: html_p += f"<h3 style='text-align:center;'>di {autore_l}</h3><hr><br>"
        for s_idx in [L["preface"]] + lista + [L["ack"]]:
            k_p = f"txt_{s_idx.replace(' ', '_').replace('.', '')}"
            if k_p in st.session_state and st.session_state[k_p].strip():
                html_p += f"<h2>{s_idx.upper()}</h2><p>{st.session_state[k_p].replace(chr(10), '<br>')}</p>"
        st.markdown(html_p + "</div>", unsafe_allow_html=True)

    # TAB 4: ESPORTAZIONE (WORD & PDF)
    with tabs[3]:
        st.subheader("📑 Scarica il tuo Ebook")
        
        # WORD EXPORT
        if st.button(L["btn_word"]):
            doc = Document()
            doc.add_heading(titolo_l, 0)
            for s_ex in [L["preface"]] + lista + [L["ack"]]:
                k_ex = f"txt_{s_ex.replace(' ', '_').replace('.', '')}"
                if k_ex in st.session_state:
                    doc.add_page_break()
                    doc.add_heading(s_ex.upper(), level=1)
                    doc.add_paragraph(st.session_state[k_ex])
            buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
            st.download_button("Salva Word (.docx)", buf_w, file_name=f"{titolo_l}.docx")
            
        # PDF EXPORT
        if st.button(L["btn_pdf"]):
            pdf = EbookPDF(titolo_l, autore_l)
            # Frontespizio
            pdf.add_page()
            pdf.set_font('Arial', 'B', 24)
            pdf.cell(0, 60, titolo_l.upper(), 0, 1, 'C')
            pdf.set_font('Arial', '', 16)
            pdf.cell(0, 20, f"Autore: {autore_l}", 0, 1, 'C')
            # Contenuti
            for s_ex in [L["preface"]] + lista + [L["ack"]]:
                k_ex = f"txt_{s_ex.replace(' ', '_').replace('.', '')}"
                if k_ex in st.session_state:
                    pdf.add_chapter(s_ex, st.session_state[k_ex])
            buf_p = BytesIO()
            pdf_out = pdf.output(dest='S').encode('latin-1')
            st.download_button("Salva PDF (.pdf)", pdf_out, file_name=f"{titolo_l}.pdf")

else:
    st.info("👋 Inserisci Titolo e Trama nella sidebar scura per iniziare.")

# =================================================================
# FINE CODICE - ARCHITETTURA PROGETTO EBOOK CREATOR MONDIALE
# =================================================================
