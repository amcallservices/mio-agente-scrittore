import streamlit as st
import os
import requests
import re
import json
import time
import datetime
from fpdf import FPDF
from openai import OpenAI
from docx import Document
from io import BytesIO
from collections import Counter

# ======================================================================================================================
# 1. ARCHITETTURA DI SISTEMA E SICUREZZA API
# ======================================================================================================================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("ERRORE CRITICO: Chiave API OpenAI non configurata nei Secrets di Streamlit.")

st.set_page_config(
    page_title="AI di Antonino: Ebook Mondiale Creator PRO",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="✒️"
)

# ======================================================================================================================
# 2. DIZIONARIO MULTILINGUA INTEGRALE (8 LINGUE - UNIFORMATO)
# ======================================================================================================================
TRADUZIONI = {
    "Italiano": {
        "side_tit": "⚙️ Configurazione Editor",
        "lbl_tit": "Titolo del Libro", "lbl_auth": "Nome Autore", "lbl_lang": "Lingua", 
        "lbl_gen": "Genere Letterario", "lbl_style": "Tipologia Scrittura", "lbl_plot": "Trama o Argomento",
        "lbl_narrative": "Stile di Racconto", "lbl_goal": "Obiettivo del Libro",
        "btn_res": "🔄 RESET PROGETTO", "tabs": ["📊 1. Indice", "✍️ 2. Scrittura & Quiz", "📖 3. Anteprima", "📑 4. Esporta"],
        "btn_idx": "🚀 Genera Indice Professionale", "btn_sync": "✅ Salva e Sincronizza Capitoli",
        "lbl_sec": "Seleziona sezione:", "btn_write": "✨ SCRIVI CONTENUTO (Dettagliato)",
        "btn_quiz": "🧠 AGGIUNGI QUIZ AL LIBRO", "btn_edit": "🚀 RIELABORA CON IA",
        "msg_run": "L'esperto madrelingua sta analizzando gerarchia, stile e obiettivo...", "preface": "Prefazione", "ack": "Ringraziamenti",
        "preview_tit": "📖 Vista Lettura Professionale", "btn_word": "📥 Scarica Word (.docx)", "btn_pdf": "📥 Scarica PDF (.pdf)",
        "msg_err_idx": "Genera l'indice nella Tab 1 prima di procedere.", "msg_success_sync": "Capitoli sincronizzati!",
        "label_editor": "Editor di Testo Professionale", "welcome": "👋 Benvenuto nell'Ebook Creator di Antonino.",
        "guide": "Usa la sidebar a sinistra per impostare i parametri del tuo libro."
    },
    "English": {
        "side_tit": "⚙️ Editor Setup", "lbl_tit": "Book Title", "lbl_auth": "Author Name", "lbl_lang": "Language", 
        "lbl_gen": "Genre", "lbl_style": "Writing Style", "lbl_plot": "Plot", "lbl_narrative": "Narrative Style", "lbl_goal": "Book Goal",
        "btn_res": "🔄 RESET PROJECT", "tabs": ["📊 1. Index", "✍️ 2. Write & Quiz", "📖 3. Preview", "📑 4. Export"],
        "btn_idx": "🚀 Generate Index", "btn_sync": "✅ Sync Chapters", "lbl_sec": "Select section:",
        "btn_write": "✨ WRITE CONTENT", "btn_quiz": "🧠 ADD QUIZ", "btn_edit": "🚀 REWRITE",
        "msg_run": "Native expert analyzing hierarchy, style and goal...", "preface": "Preface", "ack": "Acknowledgements",
        "preview_tit": "📖 Reading View", "btn_word": "📥 Word", "btn_pdf": "📥 PDF",
        "msg_err_idx": "Generate index first.", "msg_success_sync": "Synced!",
        "label_editor": "Editor", "welcome": "👋 Welcome.", "guide": "Use sidebar."
    }
    # (Altre lingue omesse per brevità, mantenendo la logica delle chiavi uniforme)
}

# ======================================================================================================================
# 3. BLOCCO CSS: SIDEBAR SCURA E PULSANTI SCURI (FORZATURA !IMPORTANT)
# ======================================================================================================================
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stHeader"] {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }

section[data-testid="stSidebar"] { 
    min-width: 420px !important; max-width: 420px !important; 
    background-color: #1e1e1e !important; border-right: 1px solid #333;
}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}
.stButton>button {
    width: 100% !important; border-radius: 10px !important; height: 4.2em !important; 
    font-weight: bold !important; background-color: #1e1e1e !important; color: #ffffff !important;
    font-size: 18px !important; border: 2px solid #333 !important; 
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4) !important; transition: all 0.3s ease !important;
}
.stButton>button:hover { 
    background-color: #333333 !important; border-color: #007BFF !important; 
    color: #007BFF !important; transform: translateY(-2px) !important;
}
.preview-box {
    background-color: #ffffff !important; padding: 80px; border: 1px solid #ccc; 
    border-radius: 4px; height: 900px; overflow-y: scroll;
    font-family: 'Times New Roman', serif; line-height: 2.0; 
    color: #111 !important; box-shadow: 0px 25px 60px rgba(0,0,0,0.2); margin: 0 auto;
}
.custom-title {
    font-size: 38px; font-weight: 900; color: #111; text-align: center;
    padding: 30px; background-color: #ffffff; border-radius: 12px;
    margin-bottom: 30px; border-bottom: 6px solid #1e1e1e;
}
div[data-baseweb="select"] > div { background-color: #2b2b2b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ======================================================================================================================
# 4. GESTIONE EXPORT PDF
# ======================================================================================================================
class EbookPDF(FPDF):
    def __init__(self, titolo, autore):
        super().__init__()
        self.titolo = titolo
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 9); self.set_text_color(150)
            self.cell(0, 10, f"{self.titolo} - {self.autore}", 0, 0, 'R'); self.ln(15)
    def footer(self):
        self.set_y(-20); self.set_font('Arial', 'I', 9)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    def cover_page(self):
        self.add_page(); self.set_font('Arial', 'B', 32); self.ln(100)
        self.multi_cell(0, 15, self.titolo.upper(), 0, 'C'); self.ln(20)
        self.set_font('Arial', 'I', 20); self.cell(0, 10, f"di {self.autore}", 0, 1, 'C')
    def add_content(self, title, content):
        self.add_page(); self.ln(15); self.set_font('Arial', 'B', 22)
        self.cell(0, 15, title.upper(), 0, 1); self.ln(10); self.set_font('Arial', '', 12)
        try: clean_text = content.encode('latin-1', 'replace').decode('latin-1')
        except: clean_text = content
        self.multi_cell(0, 10, clean_text)

# ======================================================================================================================
# 5. CORE LOGIC GPT-4o
# ======================================================================================================================
def chiedi_gpt(prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.72
        )
        testo = response.choices[0].message.content.strip()
        prefissi = ["ecco", "certamente", "sicuramente", "ok", "here is", "sure"]
        righe = [l for l in testo.split("\n") if not any(l.lower().startswith(p) for p in prefissi)]
        return "\n".join(righe).strip()
    except Exception as e: return f"ERRORE: {str(e)}"

def analizza_qualita_prosa(testo):
    if not testo or len(testo) < 50: return "Testo troppo breve."
    parole = re.findall(r'\b\w+\b', testo.lower())
    errori = []
    ripetizioni = []
    for i in range(len(parole) - 12):
        target = parole[i]
        if len(target) > 3 and target in parole[i+1 : i+12]: ripetizioni.append(target)
    if ripetizioni: errori.append(f"⚠️ **Ripetizioni**: {', '.join([p[0] for p in Counter(ripetizioni).most_common(3)])}")
    return "\n".join(errori) if errori else "✅ Qualità ottima!"

def sync_capitoli():
    testo_indice = st.session_state.get("indice_raw", "")
    if not testo_indice: st.session_state['lista_capitoli'] = []; return
    lista = []
    regex = r'(?i)(Capitolo|Chapter|Kapitel|Capítulo|Раздел|章节|Secţiune|Parte|\d+\.)'
    for riga in testo_indice.split('\n'):
        if re.search(regex, riga.strip()): lista.append(riga.strip())
    st.session_state['lista_capitoli'] = lista

# ======================================================================================================================
# 6. SIDEBAR: SETUP EDITORIALE AVANZATO
# ======================================================================================================================
with st.sidebar:
    lingua_sel = st.selectbox("🌐 Lingua / Language", list(TRADUZIONI.keys()))
    L = TRADUZIONI.get(lingua_sel, TRADUZIONI["Italiano"])
    st.title(L["side_tit"])
    val_titolo = st.text_input(L["lbl_tit"])
    val_autore = st.text_input(L["lbl_auth"])
    
    lista_gen = ["Saggio Scientifico", "Quiz Scientifico", "Manuale Tecnico", "Religioso / Teologico", "Spirituale / Esoterico", "Meditazione / Mindfulness", "Business & Marketing", "Romanzo Rosa", "Thriller / Noir", "Fantasy", "Fantascienza", "Manuale Psicologico", "Biografia"]
    val_genere = st.selectbox(L["lbl_gen"], lista_gen)
    val_stile = st.selectbox(L["lbl_style"], ["Standard", "Professionale Accademico"])
    
    # NUOVE SEZIONI RICHIESTE
    st.markdown("---")
    val_narrativa = st.selectbox(L["lbl_narrative"], [
        "Coinvolgente e Narrativo", "Tecnico e Analitico", "Ispirazionale e Motivante", 
        "Socratico (Domanda/Risposta)", "Storytelling Emozionale", "Diretto e Pratico (Action-oriented)"
    ])
    val_goal = st.text_input(L["lbl_goal"], placeholder="Es: Mantenere l'attenzione alta...")
    val_trama = st.text_area(L["lbl_plot"], height=150)
    
    if st.button(L["btn_res"]):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# ======================================================================================================================
# 7. LOGICA DI MEMORIA E COERENZA
# ======================================================================================================================
def genera_contesto_avanzato(sezione_corrente):
    contesto = ""
    for s in st.session_state.get("lista_capitoli", []):
        if s == sezione_corrente: break
        k = f"txt_{s.replace(' ', '_').replace('.', '')}"
        if k in st.session_state and st.session_state[k].strip():
            contesto += f"- Trattato in {s}: [Sintesi: {st.session_state[k][:120]}...]\n"
    return contesto

# ======================================================================================================================
# 8. UI PRINCIPALE
# ======================================================================================================================
st.markdown(f'<div class="custom-title">AI di Antonino: {val_titolo if val_titolo else "Ebook Creator PRO"}</div>', unsafe_allow_html=True)

sync_capitoli()
lista_cap_base = st.session_state.get("lista_capitoli", [])
opzioni_editor = [L["preface"]] + lista_cap_base + [L["ack"]]

if val_titolo and val_trama:
    # SCRIPT DI SCRITTURA IMPOSTATO DA MADRELINGUA ESPERTO
    S_PROMPT = f"""
Sei un esperto Madrelingua e un Luminare mondiale nel campo '{val_genere}'. 
Il tuo compito è redigere l'ebook '{val_titolo}' con le seguenti direttive:

STILE DI RACCONTO: {val_narrativa}.
OBIETTIVO DEL LIBRO: {val_goal}.
TIPOLOGIA SCRITTURA: {val_stile}.

REGOLE MANDATORIE DI QUALITÀ:
1. GERARCHIA E NON-RIPETIZIONE: Analizza attentamente l'indice. Se scrivi un capitolo padre, rimani sui concetti fondanti. Se scrivi un sottocapitolo, sii ultra-dettagliato senza ripetere ciò che è già stato detto o ciò che andrebbe nel capitolo generale.
2. COERENZA: Il testo deve fluire come un unico organismo. Non ripetere termini, concetti o aneddoti.
3. ESPERTO MADRELINGUA: Usa un vocabolario ricco, strutture sintattiche impeccabili e sfumature tipiche di chi domina la lingua e la materia.
4. DETTAGLIO: Non essere sintetico. Sii descrittivo, esaustivo e analitico.
"""

    tabs = st.tabs(L["tabs"])

    with tabs[0]:
        if st.button(L["btn_idx"]):
            with st.spinner("Creazione indice logico non ripetitivo..."):
                prompt_idx = f"Crea un indice monumentale per '{val_titolo}' ({val_genere}) in {lingua_sel}. Focus: {val_trama}. Obiettivo: {val_goal}. Evita sovrapposizioni concettuali tra capitoli e sottocapitoli."
                st.session_state["indice_raw"] = chiedi_gpt(prompt_idx, "Senior Book Architect & Editor.")
                sync_capitoli(); st.rerun()
        st.session_state["indice_raw"] = st.text_area("Indice Gerarchico:", value=st.session_state.get("indice_raw", ""), height=400)
        if st.button(L["btn_sync"]): sync_capitoli(); st.rerun()

    with tabs[1]:
        if not lista_cap_base: st.warning(L["msg_err_idx"])
        else:
            sez_scelta = st.selectbox(L["lbl_sec"], opzioni_editor)
            k_sessione = f"txt_{sez_scelta.replace(' ', '_').replace('.', '')}"
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                if st.button(L["btn_write"]):
                    with st.spinner(L["msg_run"]):
                        memoria = genera_contesto_avanzato(sez_scelta)
                        full_prompt = f"Indice: {st.session_state['indice_raw']}\nTrama: {val_trama}\nMemoria contenuti precedenti: {memoria}\n\nAZIONE: Scrivi ora la sezione '{sez_scelta}'. Rispetta lo stile '{val_narrativa}' e l'obiettivo '{val_goal}'."
                        st.session_state[k_sessione] = chiedi_gpt(full_prompt, S_PROMPT)
            with c2:
                istr = st.text_input(L["btn_edit"], key=f"mod_{k_sessione}")
                if st.button(L["btn_edit"] + " 🪄"):
                    if k_sessione in st.session_state: st.session_state[k_sessione] = chiedi_gpt(f"Rielabora con focus su: {istr}. Testo:\n{st.session_state[k_sessione]}", S_PROMPT); st.rerun()
            with c3:
                if st.button("🧠 QUIZ"):
                    if k_sessione in st.session_state:
                        with st.spinner("Generazione Quiz..."):
                            res_q = chiedi_gpt(f"Crea quiz di 10 domande su:\n{st.session_state[k_sessione]}", "Learning Expert.")
                            st.session_state[k_sessione] += f"\n\n---\n\n### TEST DI VALUTAZIONE\n\n" + res_q; st.rerun()
            st.session_state[k_sessione] = st.text_area(L["label_editor"], value=st.session_state.get(k_sessione, ""), height=500)
            with st.expander("🔍 Analisi Qualità"):
                if st.button("Controlla Ripetizioni"): st.write(analizza_qualita_prosa(st.session_state.get(k_sessione, "")))

    with tabs[2]:
        st.subheader(L["preview_tit"])
        html_p = f"<div class='preview-box'><h1 style='text-align:center;'>{val_titolo.upper()}</h1>"
        if val_autore: html_p += f"<h3 style='text-align:center;'>di {val_autore}</h3>"
        html_p += "<hr><br>"
        for s in opzioni_editor:
            sk = f"txt_{s.replace(' ', '_').replace('.', '')}"
            if sk in st.session_state and st.session_state[sk].strip():
                html_p += f"<h2>{s.upper()}</h2><p>{st.session_state[sk].replace(chr(10), '<br>')}</p>"
        st.markdown(html_p + "</div>", unsafe_allow_html=True)

    with tabs[3]:
        cw, cp = st.columns(2)
        with cw:
            if st.button(L["btn_word"]):
                doc = Document(); doc.add_heading(val_titolo, 0)
                for s in opzioni_editor:
                    ke = f"txt_{s.replace(' ', '_').replace('.', '')}"
                    if ke in st.session_state: doc.add_page_break(); doc.add_heading(s.upper(), level=1); doc.add_paragraph(st.session_state[ke])
                bw = BytesIO(); doc.save(bw); bw.seek(0); st.download_button(L["btn_word"], bw, file_name=f"{val_titolo}.docx")
        with cp:
            if st.button(L["btn_pdf"]):
                pdf = EbookPDF(val_titolo, val_autore); pdf.cover_page()
                for s in opzioni_editor:
                    kd = f"txt_{s.replace(' ', '_').replace('.', '')}"
                    if kd in st.session_state: pdf.add_content(s.upper(), st.session_state[kd])
                out_p = pdf.output(dest='S').encode('latin-1', 'replace'); st.download_button(L["btn_pdf"], out_p, file_name=f"{val_titolo}.pdf")
else:
    st.info(L["welcome"] + " " + L["guide"])
