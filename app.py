import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# =================================================================
# 1. CONNESSIONE API E SETUP DI SISTEMA
# =================================================================
# Gestione sicura della chiave API tramite Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Errore critico: OpenAI API Key non trovata. Controlla i Secrets.")

# Configurazione Pagina: Sidebar sempre espansa e layout wide
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

# =================================================================
# 3. CSS CUSTOM: SIDEBAR SCURA E PULSANTI BLU
# =================================================================
st.markdown("""
<style>
/* Pulizia interfaccia Streamlit */
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* SIDEBAR SCURA (DARK MODE MANUALE) */
section[data-testid="stSidebar"] { 
    min-width: 400px !important; 
    max-width: 400px !important; 
    background-color: #1e1e1e !important; /* Nero/Antracite */
    border-right: 1px solid #333;
}

/* Colore testi e labels nella sidebar scura */
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* Titolo Centrale */
.custom-title {
    font-size: 40px; 
    font-weight: bold; 
    color: #111; 
    text-align: center;
    padding: 25px; 
    background-color: #fcfcfc;
    border-radius: 15px;
    margin-bottom: 30px; 
    border: 1px solid #eee;
}

/* Anteprima Ebook: Foglio Bianco */
.preview-box {
    background-color: #ffffff; 
    padding: 65px; 
    border: 1px solid #ccc;
    border-radius: 4px; 
    height: 800px; 
    overflow-y: scroll;
    font-family: 'Times New Roman', serif; 
    line-height: 1.8; 
    color: #111;
    box-shadow: 0px 20px 45px rgba(0,0,0,0.15);
    margin: 0 auto;
}

/* PULSANTI BLU ANTONINO - ULTRA VISIBILI */
.stButton>button {
    width: 100%; 
    border-radius: 10px; 
    height: 4.2em; 
    font-weight: bold;
    background-color: #007BFF !important; 
    color: #ffffff !important;
    font-size: 19px !important; 
    border: 2px solid #0056b3; 
    box-shadow: 0px 5px 15px rgba(0, 123, 255, 0.4);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.stButton>button:hover { 
    background-color: #0056b3 !important; 
    transform: scale(1.02); 
    box-shadow: 0px 8px 20px rgba(0, 86, 179, 0.5);
}

/* Fix per i selettori nella sidebar scura */
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #333 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. FUNZIONI DI ELABORAZIONE E GESTIONE
# =================================================================
def chiedi_gpt(prompt, system_prompt):
    """Interazione avanzata con GPT-4o"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.72
        )
        testo_pulito = response.choices[0].message.content.strip()
        # Rimozione automatica prefissi IA colloquiali
        filtri = ["ecco", "certamente", "spero", "ciao", "fase", "parte", "sure", "here"]
        linee = testo_pulito.split("\n")
        output = [l for l in linee if not any(l.lower().startswith(f) for f in filtri)]
        return "\n".join(output).strip()
    except Exception as e:
        return f"Errore Connessione API: {str(e)}"

def sync_capitoli():
    """Analisi indice per generazione selettore capitoli"""
    testo = st.session_state.get("indice_raw", "")
    if not testo:
        st.session_state['lista_capitoli'] = []
        return
    linee_indice = testo.split('\n')
    lista_finale = []
    # Regex per intercettare i capitoli in tutte le lingue
    pattern_cap = r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)'
    for r in linee_indice:
        if re.search(pattern_cap, r.strip()):
            lista_finale.append(r.strip())
    st.session_state['lista_capitoli'] = lista_finale

# =================================================================
# 5. SIDEBAR: SETUP EDITORIALE (MODALITÀ SCURA)
# =================================================================
with st.sidebar:
    # Selettore Lingua: Caricamento dizionario
    lingua_app = st.selectbox("🌐 Lingua / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lingua_app]
    
    st.title(L["side_tit"])
    tit_val = st.text_input(L["lbl_tit"], placeholder="Titolo...")
    aut_val = st.text_input(L["lbl_auth"], placeholder="Autore...")
    
    # Generi Completi (Scientifico, Rosa, Quiz inclusi)
    genere_opt = [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Marketing", "Motivazionale / Self-Help", "Biografia", 
        "Libro di Quiz / Test", "Saggio Breve", "Romanzo Rosa", 
        "Romanzo Storico", "Thriller", "Fantasy", "Fantascienza"
    ]
    gen_val = st.selectbox(L["lbl_gen"], genere_opt)
    
    mod_val = st.selectbox(L["lbl_style"], ["Standard", "Professionale (Accademica)"])
    trama_val = st.text_area(L["lbl_plot"], height=160, placeholder="Descrizione...")
    
    st.markdown("---")
    if st.button(L["btn_res"]):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# =================================================================
# 6. LOGICA DI SCRITTURA MONUMENTALE (ANTI-RIPETIZIONE)
# =================================================================
fasi_lavoro = {
    "Italiano": ["Introduzione Analitica", "Espansione Tecnica", "Sintesi Conclusiva"],
    "English": ["Analytical Intro", "Technical Expansion", "Conclusion"],
    "Deutsch": ["Einleitung", "Entwicklung", "Fazit"],
    "Français": ["Introduction", "Développement", "Conclusion"],
    "Español": ["Introducción", "Desarrollo", "Conclusión"]
}
passaggi = fasi_lavoro.get(lingua_app, ["Phase 1", "Phase 2", "Phase 3"])

# =================================================================
# 7. UI PRINCIPALE: TAB NAVIGATION
# =================================================================
st.markdown(f'<div class="custom-title">AI Editor: {tit_val if tit_val else "Creatore Ebook Mondiale"}</div>', unsafe_allow_html=True)

if tit_val and trama_val:
    # Prompt Autorità Mondiale con Filo Logico
    stile_selezionato = "accademico e rigoroso" if mod_val == "Professionale (Accademica)" else "fluido e discorsivo"
    
    # Controllo Coerenza: verifica sezioni già scritte
    txt_keys = [k for k in st.session_state.keys() if k.startswith("txt_")]
    warning_rep = "Evita rigorosamente di ripetere frasi o dati già inseriti nelle altre sezioni." if txt_keys else ""

    S_PROMPT = f"""
Sei un'Autorità Mondiale nel settore {gen_val}. Scrivi solo in {lingua_app}.
Tono: {stile_selezionato}. Target: 2000 parole.

REGOLE CRITICHE:
1. ANTI-RIPETIZIONE: {warning_rep} Sii originale in ogni paragrafo.
2. FILO LOGICO: Collega questo contenuto alla trama generale: {trama_val}.
3. DETTAGLIO: Fornisci dati, analisi e approfondimenti estesi.
4. NO META: Scrivi solo il testo del libro.
"""

    tabs = st.tabs(L["tabs"])

    # --- TAB 1: INDICE ---
    with tabs[0]:
        st.subheader("📊 Pianificazione Strutturale")
        if st.button(L["btn_idx"]):
            with st.spinner("Creazione struttura logica..."):
                p_idx = f"Genera un indice monumentale per un libro '{gen_val}' intitolato '{tit_val}' in {lingua_app}. Focus: {trama_val}. Evita ridondanze."
                st.session_state["indice_raw"] = chiedi_gpt(p_idx, "Professional Book Architect.")
                sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area(L["lbl_tit"], value=st.session_state.get("indice_raw", ""), height=400)
        if st.button(L["btn_sync"]):
            sync_capitoli(); st.success(L["msg_success_sync"])

    # --- TAB 2: SCRITTURA, EDITING E QUIZ ---
    with tabs[1]:
        lista_cap = st.session_state.get("lista_capitoli", [])
        if not lista_cap:
            st.warning(L["msg_err_idx"])
        else:
            menu_opzioni = [L["preface"]] + lista_cap + [L["ack"]]
            sez_attiva = st.selectbox(L["lbl_sec"], menu_opzioni)
            k_sez = f"txt_{sez_attiva.replace(' ', '_').replace('.', '')}"

            col_w, col_e, col_q = st.columns([2, 2, 1])
            with col_w:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        testo_cap = ""
                        # Tripla generazione per raggiungere le 2000 parole
                        for f_n in passaggi:
                            p_f = f"Indice: {st.session_state['indice_raw']}. Scrivi sezione '{sez_attiva}', parte: {f_n}."
                            testo_cap += chiedi_gpt(p_f, S_PROMPT) + "\n\n"
                        st.session_state[k_sez] = testo_cap
            
            with col_e:
                input_mod = st.text_input(L["btn_edit"], key=f"in_{k_sez}", placeholder="Modifica tono...")
                if st.button(L["btn_edit"] + " 🪄"):
                    if k_sez in st.session_state:
                        with st.spinner("Rielaborazione..."):
                            p_mod = f"Riscrivi questo testo seguendo: {input_mod}.\n\nTesto:\n{st.session_state[k_sez]}"
                            st.session_state[k_sez] = chiedi_gpt(p_mod, S_PROMPT)
                            st.rerun()

            with col_q:
                if st.button("🧠 QUIZ"):
                    if k_sez in st.session_state:
                        with st.spinner("Creazione Quiz..."):
                            p_q = f"Genera 10 quiz a risposta multipla con soluzioni basati su questo capitolo: {sez_attiva}."
                            quiz_txt = chiedi_gpt(p_q, "Accademico Senior.")
                            st.session_state[k_sez] += f"\n\n---\n\n### TEST DI VALUTAZIONE: {sez_attiva}\n\n" + quiz_txt
                            st.success("Quiz Integrato!")
                            st.rerun()

            if k_sez in st.session_state:
                st.session_state[k_sez] = st.text_area("Editor", value=st.session_state[k_sez], height=500, key=f"area_{k_sez}")

    # --- TAB 3: ANTEPRIMA ---
    with tabs[2]:
        st.subheader(L["preview_tit"])
        html_preview = f"<div class='preview-box'>"
        html_preview += f"<h1 style='text-align:center; font-size:45px; color:#000;'>{tit_val.upper()}</h1>"
        if aut_val: html_preview += f"<h3 style='text-align:center; font-style:italic;'>di {aut_val}</h3>"
        html_preview += "<div style='height:200px'></div>"
        
        cont_found = False
        for s_idx in menu_opzioni:
            key_preview = f"txt_{s_idx.replace(' ', '_').replace('.', '')}"
            if key_preview in st.session_state and st.session_state[key_preview].strip():
                html_preview += f"<h2 style='page-break-before:always; color:#000;'>{s_idx.upper()}</h2>"
                html_preview += f"<p style='text-align:justify;'>{st.session_state[key_preview].replace(chr(10), '<br>')}</p>"
                cont_found = True
        
        if not cont_found:
            html_preview += "<p style='text-align:center; color:#999;'>Inizia a scrivere per visualizzare l'anteprima.</p>"
        
        st.markdown(html_preview + "</div>", unsafe_allow_html=True)

    # --- TAB 4: EXPORT ---
    with tabs[3]:
        st.subheader("📑 Download Ebook")
        if st.button(L["btn_word"]):
            doc_final = Document()
            doc_final.add_heading(tit_val, 0)
            if aut_val: doc_final.add_paragraph(f"Autore: {aut_val}")
            
            for s_exp in menu_opzioni:
                key_exp = f"txt_{s_exp.replace(' ', '_').replace('.', '')}"
                if key_exp in st.session_state:
                    doc_final.add_page_break()
                    doc_final.add_heading(s_exp.upper(), level=1)
                    doc_final.add_paragraph(st.session_state[key_exp])
            
            buf_final = BytesIO()
            doc_final.save(buf_final)
            buf_final.seek(0)
            st.download_button(L["btn_word"], buf_final, file_name=f"{tit_val.replace(' ','_')}.docx")

else:
    st.info("👋 Configura la sidebar (ora scura) per sbloccare l'Editor IA.")
    st.markdown("""
    ### Guida Rapida:
    1. **Setup**: Definisci genere (rosa, scientifico, ecc.) e stile.
    2. **Indice**: Crea l'ossatura del libro.
    3. **Scrittura**: Genera capitoli da 2000 parole con filo logico.
    4. **Quiz**: Inserisci test automatici.
    5. **Export**: Scarica il file Word pronto per la pubblicazione.
    """)
# =================================================================
# FINE CODICE - EBOOK CREATOR MONDIALE PRO
# =================================================================

# =================================================================
# FINE DEL CODICE - ARCHITETTURA PROGETTO EBOOK CREATOR
# =================================================================
