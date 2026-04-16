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
# 1. ARCHITETTURA DI SISTEMA E SICUREZZA API
# ======================================================================================================================
# L'applicazione utilizza il modello GPT-4o di OpenAI per la generazione di contenuti ad alta fedeltà.
# La sicurezza è garantita dall'integrazione con Streamlit Secrets per la gestione della chiave API.

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("ERRORE DI CONFIGURAZIONE: Chiave API non trovata. Verifica il file secrets.toml.")

# Configurazione globale dell'interfaccia: Sidebar fissa e layout wide per editing professionale.
st.set_page_config(
    page_title="AI di Antonino: Ebook Mondiale Creator PRO",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="✒️"
)

# ======================================================================================================================
# 2. DIZIONARIO MULTILINGUA (SUPPORTO INTEGRALE PER 8 LINGUE)
# ======================================================================================================================
# Questa sezione gestisce la localizzazione completa di tutti i messaggi, pulsanti e placeholder.
TRADUZIONI = {
    "Italiano": {
        "side_tit": "⚙️ Configurazione Editor",
        "lbl_tit": "Titolo del Libro", "lbl_auth": "Nome Autore", "lbl_lang": "Lingua del Libro", 
        "lbl_gen": "Genere Letterario", "lbl_style": "Tipologia di Scrittura", "lbl_plot": "Trama o Argomento",
        "btn_res": "🔄 RESET PROGETTO", "tabs": ["📊 1. Indice", "✍️ 2. Scrittura & Quiz", "📖 3. Anteprima", "📑 4. Esporta"],
        "btn_idx": "🚀 Genera Indice Professionale", "btn_sync": "✅ Salva e Sincronizza Capitoli",
        "lbl_sec": "Seleziona sezione:", "btn_write": "✨ SCRIVI SEZIONE (2000+ parole)",
        "btn_quiz": "🧠 AGGIUNGI QUIZ AL LIBRO", "btn_edit": "🚀 RIELABORA CON IA",
        "msg_run": "L'autorità mondiale sta elaborando il testo...", "preface": "Prefazione", "ack": "Ringraziamenti",
        "preview_tit": "📖 Vista Lettura Professionale", "btn_word": "📥 Scarica Word (.docx)", "btn_pdf": "📥 Scarica PDF (.pdf)",
        "msg_err_idx": "Genera l'indice nella Tab 1 prima di procedere.", "msg_success_sync": "Capitoli sincronizzati!",
        "label_editor": "Editor di Testo Professionale", "welcome": "👋 Benvenuto nell'Ebook Creator di Antonino.",
        "guide": "Usa la sidebar a sinistra per impostare i parametri del tuo libro."
    },
    "English": {
        "side_tit": "⚙️ Editor Setup",
        "lbl_tit": "Book Title", "lbl_auth": "Author Name", "lbl_lang": "Language", 
        "lbl_gen": "Genre", "lbl_style": "Writing Style", "lbl_plot": "Plot or Topic",
        "btn_res": "🔄 FULL RESET", "tabs": ["📊 1. Index", "✍️ 2. Write & Quiz", "📖 3. Preview", "📑 4. Export"],
        "btn_idx": "🚀 Generate Professional Index", "btn_sync": "✅ Save & Sync Chapters",
        "lbl_sec": "Select section:", "btn_write": "✨ WRITE SECTION (2000+ words)",
        "btn_quiz": "🧠 ADD QUIZ TO BOOK", "btn_edit": "🚀 REWRITE WITH AI",
        "msg_run": "The world authority is processing...", "preface": "Preface", "ack": "Acknowledgements",
        "preview_tit": "📖 Professional Reading View", "btn_word": "📥 Download Word", "btn_pdf": "📥 Download PDF"
    },
    "Deutsch": {
        "side_tit": "⚙️ Editor-Setup",
        "lbl_tit": "Buchtitel", "lbl_auth": "Autor", "lbl_lang": "Sprache", 
        "lbl_gen": "Genre", "lbl_style": "Schreibstil", "lbl_plot": "Inhalt",
        "btn_res": "🔄 ZURÜCKSETZEN", "tabs": ["📊 1. Index", "✍️ 2. Schreiben & Quiz", "📖 3. Vorschau", "📑 4. Export"]
    },
    "Français": {
        "side_tit": "⚙️ Configuration",
        "lbl_tit": "Titre", "lbl_auth": "Auteur", "lbl_lang": "Langue", 
        "lbl_gen": "Genre", "lbl_style": "Style", "lbl_plot": "Intrigue",
        "btn_res": "🔄 RÉINITIALISER", "tabs": ["📊 1. Index", "✍️ 2. Écriture", "📖 3. Aperçu", "📑 4. Export"]
    },
    "Español": {
        "side_tit": "⚙️ Configuración",
        "lbl_tit": "Título", "lbl_auth": "Autor", "lbl_lang": "Idioma", 
        "lbl_gen": "Género", "lbl_style": "Estilo", "lbl_plot": "Trama",
        "btn_res": "🔄 REINICIAR", "tabs": ["📊 1. Índice", "✍️ 2. Escritura", "📖 3. Vista previa", "📑 4. Exportar"]
    },
    "Română": {
        "side_tit": "⚙️ Configurare",
        "lbl_tit": "Titlu", "lbl_auth": "Autor", "lbl_lang": "Limbă", 
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
# 3. BLOCCO CSS: PULSANTI SCURI E SIDEBAR ANTRACITE (ESTETICA RICHIESTA)
# ======================================================================================================================
st.markdown("""
<style>
/* Pulizia layout */
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* CONFIGURAZIONE SIDEBAR SCURA */
section[data-testid="stSidebar"] { 
    min-width: 420px !important; 
    max-width: 420px !important; 
    background-color: #121212 !important; /* Nero antracite */
    border-right: 1px solid #333;
}

/* Colore testi sidebar */
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* TITOLO HEADER PRO */
.custom-title {
    font-size: 38px; font-weight: 900; color: #111; text-align: center;
    padding: 30px; background-color: #ffffff; border-radius: 12px;
    margin-bottom: 30px; border-bottom: 6px solid #1e1e1e;
    box-shadow: 0px 10px 20px rgba(0,0,0,0.05);
}

/* ANTEPRIMA EBOOK: FOGLIO BIANCO */
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

/* PULSANTI SCURI (Stile Sidebar) */
.stButton>button {
    width: 100%; border-radius: 10px; height: 4em; font-weight: bold;
    background-color: #1e1e1e !important; /* Colore scuro sidebar */
    color: #ffffff !important;
    font-size: 18px !important; 
    border: 1px solid #444; 
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.stButton>button:hover { 
    background-color: #333333 !important; 
    border-color: #007BFF; /* Glow blu al passaggio */
    transform: translateY(-2px);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
    background-color: #f0f2f6;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
}
</style>
""", unsafe_allow_html=True)

# ======================================================================================================================
# 4. GESTIONE EXPORT PDF PROFESSIONALE
# ======================================================================================================================
class EbookPDF(FPDF):
    """Classe avanzata per la generazione di file PDF conformi agli standard editoriali."""
    def __init__(self, titolo, autore):
        super().__init__()
        self.titolo = titolo
        self.autore = autore

    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 9)
            self.set_text_color(150)
            self.cell(0, 10, f"{self.titolo} - {self.autore}", 0, 0, 'R')
            self.ln(15)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 9)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def cover_page(self):
        self.add_page()
        self.set_font('Arial', 'B', 32)
        self.ln(100)
        self.multi_cell(0, 15, self.titolo.upper(), 0, 'C')
        self.ln(20)
        self.set_font('Arial', 'I', 20)
        self.cell(0, 10, f"di {self.autore}", 0, 1, 'C')

    def add_content(self, title, content):
        self.add_page()
        self.ln(15)
        self.set_font('Arial', 'B', 22)
        self.cell(0, 15, title.upper(), 0, 1)
        self.ln(10)
        self.set_font('Arial', '', 12)
        try:
            clean_text = content.encode('latin-1', 'replace').decode('latin-1')
        except:
            clean_text = content
        self.multi_cell(0, 10, clean_text)

# ======================================================================================================================
# 5. CORE ENGINE: INTELLIGENZA ARTIFICIALE & COERENZA
# ======================================================================================================================
def chiedi_gpt(prompt, system_prompt):
    """Esegue la chiamata al modello GPT-4o e pulisce l'output dai tag colloquiali."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.72
        )
        testo = response.choices[0].message.content.strip()
        # Filtro per evitare prefissi tipo "Certamente, ecco il capitolo..."
        metadati = ["ecco", "certamente", "sicuramente", "ok", "here is", "sure"]
        linee = testo.split("\n")
        output = [l for l in linee if not any(l.lower().startswith(m) for m in metadati)]
        return "\n".join(output).strip()
    except Exception as e:
        return f"ERRORE API: {str(e)}"

def sync_capitoli():
    """Analizza l'indice grezzo e popola il database dei capitoli."""
    indice_raw = st.session_state.get("indice_raw", "")
    if not indice_raw:
        st.session_state['lista_capitoli'] = []
        return
    
    lista = []
    regex_universal = r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)'
    for riga in indice_raw.split('\n'):
        if re.search(regex_universal, riga.strip()):
            lista.append(riga.strip())
    st.session_state['lista_capitoli'] = lista

# ======================================================================================================================
# 6. SIDEBAR: SETUP EDITORIALE (MODALITÀ DARK)
# ======================================================================================================================
with st.sidebar:
    lang_val = st.selectbox("🌐 Lingua / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lang_val]
    
    st.title(L["side_tit"])
    in_tit = st.text_input(L["lbl_tit"], placeholder="Titolo...")
    in_aut = st.text_input(L["lbl_auth"], placeholder="Nome...")
    
    # Generi Completi
    gen_list = ["Saggio Scientifico", "Manuale Tecnico", "Psicologia", "Business", "Self-Help", "Biografia", "Quiz Scientifico", "Romanzo Rosa", "Romanzo Storico", "Thriller", "Fantasy", "Fantascienza"]
    in_gen = st.selectbox(L["lbl_gen"], gen_list)
    
    in_style = st.selectbox(L["lbl_style"], ["Standard", "Professionale Accademico"])
    in_trama = st.text_area(L["lbl_plot"], height=150, placeholder="Descrivi il tema...")
    
    st.markdown("---")
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ======================================================================================================================
# 7. LOGICA DI SCRITTURA E FILO LOGICO
# ======================================================================================================================
fasi_map = {
    "Italiano": ["Esposizione", "Analisi Profonda", "Sintesi"],
    "English": ["Introduction", "Deep Analysis", "Synthesis"]
}
fasi = fasi_map.get(lang_val, ["Phase 1", "Phase 2", "Phase 3"])

# ======================================================================================================================
# 8. UI PRINCIPALE: TABS
# ======================================================================================================================
st.markdown(f'<div class="custom-title">AI Editor: {in_tit if in_tit else "Ebook Mondiale Creator PRO"}</div>', unsafe_allow_html=True)

if in_tit and in_trama:
    stile_ia = "tecnico, rigoroso e accademico" if in_style == "Professionale Accademico" else "fluido e narrativo"
    
    # Anti-Ripetizione e Filo Logico
    memoria_chiavi = [k for k in st.session_state.keys() if k.startswith("txt_")]
    istr_rep = "Evita di ripetere concetti già espressi nelle sezioni precedenti." if memoria_chiavi else ""

    S_PROMPT = f"""
Sei un'Autorità Mondiale nel settore {in_gen}. Scrivi in {lang_val}.
Stile: {stile_ia}. Target: 2000 parole.

REGOLE MANDATORIE:
1. ANTI-RIPETIZIONE: {istr_rep} Ogni capitolo deve essere originale.
2. FILO LOGICO: Collega il contenuto all'indice e alla trama: {in_trama}.
3. DETTAGLIO: Espandi ogni punto con analisi e dati tecnici.
4. NO META: Scrivi solo il testo del libro.
"""

    tabs = st.tabs(L["tabs"])

    # --- TAB 1: INDICE ---
    with tabs[0]:
        st.subheader("📊 Struttura dell'Ebook")
        if st.button(L["btn_idx"]):
            with st.spinner("Pianificazione indice..."):
                p_idx = f"Crea un indice logico e monumentale per un libro '{in_gen}' intitolato '{in_tit}' in {lang_val}. Focus: {in_trama}."
                st.session_state["indice_raw"] = chiedi_gpt(p_idx, "Professional Book Architect.")
                sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area("Indice:", value=st.session_state.get("indice_raw", ""), height=400)
        if st.button(L["btn_sync"]):
            sync_capitoli(); st.success(L["msg_success_sync"])

    # --- TAB 2: SCRITTURA & QUIZ ---
    with tabs[1]:
        lista_c = st.session_state.get("lista_capitoli", [])
        if not lista_c:
            st.warning(L["msg_err_idx"])
        else:
            opzioni = [L["preface"]] + lista_c + [L["ack"]]
            cap_sel = st.selectbox(L["lbl_sec"], opzioni)
            key_sez = f"txt_{cap_sel.replace(' ', '_').replace('.', '')}"

            col_w, col_e, col_q = st.columns([2, 2, 1])
            with col_w:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        testo_p = ""
                        for f_n in fasi:
                            p_f = f"Indice: {st.session_state['indice_raw']}. Scrivi sezione '{cap_sel}', fase: {f_n}."
                            testo_p += chiedi_gpt(p_f, S_PROMPT) + "\n\n"
                        st.session_state[key_sez] = testo_p
            
            with col_e:
                i_mod = st.text_input(L["btn_edit"], key=f"in_mod_{key_sez}")
                if st.button(L["btn_edit"] + " 🪄"):
                    if key_sez in st.session_state:
                        with st.spinner("Rielaborazione..."):
                            p_e = f"Riscrivi il testo seguendo: {i_mod}.\n\nTesto:\n{st.session_state[key_sez]}"
                            st.session_state[key_sez] = chiedi_gpt(p_e, S_PROMPT)
                            st.rerun()

            with col_q:
                if st.button(L["btn_quiz"]):
                    if key_sez in st.session_state:
                        with st.spinner("Generando Quiz..."):
                            p_q = f"Crea un quiz di 10 domande a scelta multipla con soluzioni basato su questo capitolo: {cap_sel}."
                            res_q = chiedi_gpt(p_q, "Professore Universitario.")
                            st.session_state[key_sez] += f"\n\n---\n\n### QUIZ E TEST DI VALUTAZIONE\n\n" + res_q
                            st.rerun()

            if key_sez in st.session_state:
                st.session_state[key_sez] = st.text_area("Editor", value=st.session_state[key_sez], height=500, key=f"ed_{key_sez}")

    # --- TAB 3: ANTEPRIMA ---
    with tabs[2]:
        st.subheader(L["preview_tit"])
        html_p = f"<div class='preview-box'><h1 style='text-align:center;'>{in_tit.upper()}</h1>"
        if in_aut: html_p += f"<h3 style='text-align:center;'>di {in_aut}</h3>"
        html_p += "<hr><br>"
        for s in opzioni:
            sk = f"txt_{s.replace(' ', '_').replace('.', '')}"
            if sk in st.session_state and st.session_state[sk].strip():
                html_p += f"<h2>{s.upper()}</h2><p>{st.session_state[sk].replace(chr(10), '<br>')}</p><br>"
        st.markdown(html_p + "</div>", unsafe_allow_html=True)

    # --- TAB 4: ESPORTAZIONE ---
    with tabs[3]:
        col_w_ex, col_p_ex = st.columns(2)
        with col_w_ex:
            if st.button(L["btn_word"]):
                doc = Document()
                doc.add_heading(in_tit, 0)
                for s in opzioni:
                    sk = f"txt_{s.replace(' ', '_').replace('.', '')}"
                    if sk in st.session_state:
                        doc.add_page_break()
                        doc.add_heading(s, level=1)
                        doc.add_paragraph(st.session_state[sk])
                buf_w = BytesIO(); doc.save(buf_w); buf_w.seek(0)
                st.download_button(L["btn_word"], buf_w, file_name=f"{in_tit}.docx")
                
        with col_p_ex:
            if st.button(L["btn_pdf"]):
                pdf = EbookPDF(in_tit, in_aut)
                pdf.cover_page()
                for s in opzioni:
                    sk = f"txt_{s.replace(' ', '_').replace('.', '')}"
                    if sk in st.session_state:
                        pdf.add_content(s, st.session_state[sk])
                out_p = pdf.output(dest='S').encode('latin-1', 'replace')
                st.download_button(L["btn_pdf"], out_p, file_name=f"{in_tit}.pdf")
else:
    st.info(L["welcome"] + " " + L["guide"])
