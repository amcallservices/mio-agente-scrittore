import streamlit as st
import os, requests, re, json
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO

# =================================================================
# 1. CONNESSIONE API E SETUP DI SISTEMA
# =================================================================
# Collegamento sicuro tramite Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Errore critico: OpenAI API Key non trovata. Controlla i Secrets.")

# Configurazione Pagina con Sidebar bloccata e visibile
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
        "preview_tit": "📖 Leseansicht", "btn_word": "📥 Ebook herunterladen (.docx)",
        "msg_err_idx": "Generieren Sie zuerst den Index.", "msg_success_sync": "Kapitel synchronisiert!"
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
# 3. CSS CUSTOM: PULSANTI BLU E SIDEBAR BLOCCATA
# =================================================================
st.markdown("""
<style>
/* Reset Header e Footer Streamlit per pulizia totale */
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

/* Sidebar Larga e Sempre Attiva */
section[data-testid="stSidebar"] { 
    min-width: 400px !important; 
    max-width: 400px !important; 
    background-color: #f8f9fa;
    border-right: 2px solid #dee2e6;
}

/* Titolo Centrale Moderno */
.custom-title {
    font-size: 40px; 
    font-weight: bold; 
    color: #000000; 
    text-align: center;
    padding: 25px; 
    background-color: #f8f9fa;
    border-radius: 15px;
    margin-bottom: 30px; 
    border: 1px solid #dee2e6;
}

/* Anteprima Ebook: Effetto Carta Stampata Professionale */
.preview-box {
    background-color: #ffffff; 
    padding: 60px; 
    border: 1px solid #d3d6db;
    border-radius: 5px; 
    height: 800px; 
    overflow-y: scroll;
    font-family: 'Times New Roman', serif; 
    line-height: 1.8; 
    color: #1a1a1a;
    box-shadow: 0px 15px 35px rgba(0,0,0,0.1);
    margin: 0 auto;
}

/* PULSANTI BLU ANTONINO - Alta Visibilità */
.stButton>button {
    width: 100%; 
    border-radius: 12px; 
    height: 4em; 
    font-weight: bold;
    background-color: #007BFF !important; 
    color: white !important;
    font-size: 18px !important; 
    border: none; 
    box-shadow: 0px 4px 12px rgba(0, 123, 255, 0.3);
    transition: all 0.3s ease;
    cursor: pointer;
}

.stButton>button:hover { 
    background-color: #0056b3 !important; 
    transform: translateY(-2px); 
    box-shadow: 0px 6px 18px rgba(0, 86, 179, 0.4);
}

/* Stile Input */
.stTextInput>div>div>input {
    border-radius: 8px !important;
}

/* Scrollbar personalizzata per anteprima */
.preview-box::-webkit-scrollbar { width: 10px; }
.preview-box::-webkit-scrollbar-track { background: #f1f1f1; }
.preview-box::-webkit-scrollbar-thumb { background: #007BFF; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. FUNZIONI LOGICHE E GESTIONE TESTO
# =================================================================
def chiedi_gpt(prompt, system_prompt):
    """Interfaccia principale con il modello GPT-4o"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.75
        )
        testo_grezzo = response.choices[0].message.content.strip()
        # Pulizia rigorosa dei metadati IA
        tag_filtraggio = ["ecco", "certamente", "spero", "ciao", "fase", "parte", "here is", "sure", "ok"]
        righe = testo_grezzo.split("\n")
        risultato = [r for r in righe if not any(r.lower().startswith(t) for t in tag_filtraggio)]
        return "\n".join(risultato).strip()
    except Exception as e:
        return f"Errore Connessione: {str(e)}"

def sync_capitoli():
    """Analizza l'indice e popola la lista dei capitoli selezionabili"""
    testo = st.session_state.get("indice_raw", "")
    if not testo:
        st.session_state['lista_capitoli'] = []
        return
    righe = testo.split('\n')
    validi = []
    # Rilevamento capitoli tramite regex (compatibile con 8 lingue)
    for r in righe:
        if re.search(r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)', r.strip()):
            validi.append(r.strip())
    st.session_state['lista_capitoli'] = validi

# =================================================================
# 5. SIDEBAR: SETUP EDITORIALE COMPLETO
# =================================================================
with st.sidebar:
    # Selettore Lingua: Determina tutte le etichette dell'app
    lingua_selezionata = st.selectbox("🌐 Lingua Interfaccia / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI[lingua_selezionata]
    
    st.title(L["side_tit"])
    titolo_l = st.text_input(L["lbl_tit"], placeholder="Inserisci titolo...")
    autore_l = st.text_input(L["lbl_auth"], placeholder="Nome dell'autore")
    
    # Lista Generi Completa (Scientifico, Rosa, Quiz inclusi)
    elenco_generi = [
        "Saggio Scientifico", "Manuale Tecnico", "Manuale Psicologico", 
        "Business & Marketing", "Motivazionale / Self-Help", "Biografia / Autobiografia", 
        "Libro di Quiz / Test Didattico", "Saggio Breve", "Romanzo Rosa", 
        "Romanzo Storico", "Thriller / Noir", "Fantasy", "Fantascienza"
    ]
    genere = st.selectbox(L["lbl_gen"], elenco_generi)
    
    # Selezione Tipologia Scrittura
    modalita = st.selectbox(L["lbl_style"], ["Standard", "Professionale (Accademica/Tecnica)"])
    
    # Trama / Descrizione Argomento
    trama = st.text_area(L["lbl_plot"], height=150, placeholder="Descrivi il tema centrale...")
    
    st.markdown("---")
    # Tasto Reset Progetto
    if st.button(L["btn_res"]):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# =================================================================
# 6. LOGICA DI SCRITTURA INTEGRATA E ANTI-RIPETIZIONE
# =================================================================
# Mappatura fasi per forzare la lunghezza (Target 2000 parole)
mappa_fasi = {
    "Italiano": ["Esposizione e Introduzione", "Corpo Centrale Analitico", "Conclusioni e Prospettive"],
    "English": ["Deep Introduction", "Analytical Core", "Conclusions & Perspectives"],
    "Deutsch": ["Einleitung", "Hauptteil", "Fazit"],
    "Français": ["Introduction", "Développement", "Conclusion"],
    "Español": ["Introducción", "Desarrollo", "Conclusión"]
}
fasi_lavoro = mappa_fasi.get(lingua_selezionata, ["Phase 1", "Phase 2", "Phase 3"])

# =================================================================
# 7. UI PRINCIPALE: TAB NAVIGATION
# =================================================================
st.markdown(f'<div class="custom-title">AI Editor: {titolo_l if titolo_l else "Creatore Ebook Mondiale"}</div>', unsafe_allow_html=True)

if titolo_l and trama:
    # Configurazione Prompt IA Autorità Mondiale
    tono = "formale, accademico e tecnico" if modalita == "Professionale (Accademica/Tecnica)" else "creativo, fluido e naturale"
    
    # Gestione Filo Logico: controllo capitoli precedenti
    sezioni_salvate = [k for k in st.session_state.keys() if k.startswith("txt_")]
    memoria_testo = "Assicurati di non ripetere dati o concetti già espressi nelle altre sezioni del libro." if sezioni_salvate else ""

    S_PROMPT = f"""
Sei un'Autorità Mondiale nel settore {genere}. Scrivi in {lingua_selezionata}.
Stile: {tono}. Target: 2000 parole per ogni capitolo.

REGOLE MANDATORIE:
1. ANTI-RIPETIZIONE: {memoria_testo} Varia il lessico e gli esempi.
2. FILO LOGICO: Ogni capitolo deve essere collegato all'indice e alla trama generale: {trama}.
3. DETTAGLIO: Fornisci analisi profonde, dati tecnici e descrizioni esaustive.
4. STRUTTURA: Utilizza titoli interni, paragrafi ben spaziati e sezioni logiche.
5. NO DIALOGO IA: Scrivi solo il testo finale del libro, senza preamboli.
"""

    tabs = st.tabs(L["tabs"])

    # --- TAB 1: INDICE E ARCHITETTURA ---
    with tabs[0]:
        st.subheader("📊 Architettura dell'Opera")
        if st.button(L["btn_idx"]):
            with st.spinner("L'IA sta organizzando la struttura logica..."):
                p_idx = f"Genera un indice monumentale, logico e progressivo per un libro '{genere}' intitolato '{titolo_l}' in {lingua_selezionata}. Argomento: {trama}. Assicurati che non ci siano ripetizioni tra i capitoli."
                st.session_state["indice_raw"] = chiedi_gpt(p_idx, "Professional Book Architect.")
                sync_capitoli()
        
        st.session_state["indice_raw"] = st.text_area(L["lbl_tit"], value=st.session_state.get("indice_raw", ""), height=400)
        
        if st.button(L["btn_sync"]):
            sync_capitoli()
            st.success(L["msg_success_sync"])

    # --- TAB 2: SCRITTURA, EDITING E QUIZ INTEGRATO ---
    with tabs[1]:
        capitoli_sincronizzati = st.session_state.get("lista_capitoli", [])
        if not capitoli_sincronizzati:
            st.warning(L["msg_err_idx"])
        else:
            # Menu Sezioni
            menu_sez = [L["preface"]] + capitoli_sincronizzati + [L["ack"]]
            sez_corrente = st.selectbox(L["lbl_sec"], menu_sez)
            chiave_testo = f"txt_{sez_corrente.replace(' ', '_').replace('.', '')}"

            # Griglia Comandi (Scrittura, Rielaborazione, Quiz)
            c_write, c_rewrite, c_quiz = st.columns([2, 2, 1])
            
            with c_write:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        testo_finale = ""
                        # Generazione in 3 fasi per garantire le 2000 parole senza tagli
                        for fase_n in fasi_lavoro:
                            p_fase = f"L'indice del libro è: {st.session_state['indice_raw']}. Scrivi la sezione '{sez_corrente}', fase specifica: {fase_n}. Espandi ogni dettaglio."
                            testo_finale += chiedi_gpt(p_fase, S_PROMPT) + "\n\n"
                        st.session_state[chiave_testo] = testo_finale
            
            with c_rewrite:
                istr_ia = st.text_input(L["btn_edit"], key=f"istr_{chiave_testo}", placeholder="Es: Più cupo, più tecnico...")
                if st.button(L["btn_edit"] + " 🪄"):
                    if chiave_testo in st.session_state:
                        with st.spinner("Rielaborazione in corso..."):
                            p_edit = f"Riscrivi il testo seguendo questa direttiva: {istr_ia}. Mantieni la coerenza. Testo:\n{st.session_state[chiave_testo]}"
                            st.session_state[chiave_testo] = chiedi_gpt(p_edit, S_PROMPT)
                            st.rerun()

            with c_quiz:
                if st.button(L["btn_quiz"]):
                    if chiave_testo in st.session_state:
                        with st.spinner("Generando Quiz..."):
                            p_quiz = f"Crea un test di 10 domande a risposta multipla basato sul capitolo '{sez_corrente}'. Includi soluzioni spiegate. Lingua: {lingua_selezionata}."
                            test_ia = chiedi_gpt(p_quiz, "Specialista in valutazione didattica.")
                            # Il quiz viene iniettato nel testo per essere esportato
                            st.session_state[chiave_testo] += f"\n\n---\n\n### TEST DI VALUTAZIONE: {sez_corrente}\n\n" + test_ia
                            st.success("Quiz integrato!")
                            st.rerun()

            # Editor Testuale con persistenza dati
            if chiave_testo in st.session_state:
                st.markdown(f"#### {L['label_editor']}")
                st.session_state[chiave_testo] = st.text_area("Live Editor", value=st.session_state[chiave_testo], height=500, key=f"area_{chiave_testo}")

    # --- TAB 3: ANTEPRIMA PROFESSIONALE ---
    with tabs[2]:
        st.subheader(L["preview_tit"])
        # Costruzione dinamica della visualizzazione libro
        html_libro = f"<div class='preview-box'>"
        html_libro += f"<h1 style='text-align:center; font-size:50px; color:#000;'>{titolo_l.upper()}</h1>"
        if autore_l:
            html_libro += f"<h3 style='text-align:center; font-style:italic; font-size:26px;'>di {autore_l}</h3>"
        html_libro += "<div style='height:250px'></div>" # Spazio frontespizio
        
        testo_trovato = False
        for s_idx in menu_sez:
            k_sez = f"txt_{s_idx.replace(' ', '_').replace('.', '')}"
            if k_sez in st.session_state and st.session_state[k_sez].strip():
                html_libro += f"<h2 style='page-break-before:always; color:#000; font-size:32px; border:none;'>{s_idx.upper()}</h2>"
                # Pulizia per HTML
                txt_html = st.session_state[k_sez].replace('\n', '<br>')
                html_libro += f"<p style='text-align:justify; font-size:18px;'>{txt_html}</p>"
                testo_trovato = True
        
        if not testo_trovato:
            html_libro += f"<p style='text-align:center; color:#888;'>Nessun contenuto disponibile. Inizia la scrittura nella Tab 2.</p>"
        
        html_libro += "</div>"
        st.markdown(html_libro, unsafe_allow_html=True)

    # --- TAB 4: ESPORTAZIONE E DOWNLOAD ---
    with tabs[3]:
        st.subheader("📑 Esportazione Documento")
        st.info("Il file generato conterrà l'indice, il testo completo dei capitoli e tutti i quiz inseriti.")
        
        if st.button(L["btn_word"]):
            documento = Document()
            # Impostazione frontespizio
            documento.add_heading(titolo_l, 0)
            if autore_l: documento.add_paragraph(f"Autore: {autore_l}")
            
            # Aggiunta Indice
            documento.add_page_break()
            documento.add_heading("INDICE", level=1)
            documento.add_paragraph(st.session_state.get("indice_raw", ""))
            
            # Ciclo su tutte le sezioni compilate
            for s_export in menu_sez:
                chiave_export = f"txt_{s_export.replace(' ', '_').replace('.', '')}"
                if chiave_export in st.session_state:
                    documento.add_page_break()
                    documento.add_heading(s_export.upper(), level=1)
                    documento.add_paragraph(st.session_state[chiave_export])
            
            # Generazione Buffer per download Word
            memoria_file = BytesIO()
            documento.save(memoria_file)
            memoria_file.seek(0)
            st.download_button(L["btn_word"], memoria_file, file_name=f"{titolo_l.replace(' ','_')}.docx")

else:
    # Schermata Iniziale: Guida Rapida
    st.info("👋 Benvenuto nell'Ebook Creator di Antonino. Configura la sidebar a sinistra per sbloccare le funzioni.")
    st.markdown("""
    ### Istruzioni d'uso:
    1. **Configurazione**: Scegli lingua, genere (Scientifico, Rosa, Quiz, ecc.) e tipologia di scrittura.
    2. **Indice (Tab 1)**: Genera la struttura del libro. È fondamentale sincronizzare l'indice per abilitare la scrittura.
    3. **Scrittura (Tab 2)**: L'IA scriverà capitoli monumentali evitando ripetizioni e mantenendo il filo logico.
    4. **Quiz**: Puoi aggiungere test di autovalutazione alla fine di ogni capitolo con un solo click.
    5. **Anteprima (Tab 3)**: Leggi il tuo libro in formato cartaceo virtuale.
    6. **Download (Tab 4)**: Scarica il file Word completo e pronto per la stampa o pubblicazione.
    """)

# =================================================================
# FINE DEL CODICE - ARCHITETTURA PROGETTO EBOOK CREATOR
# =================================================================
