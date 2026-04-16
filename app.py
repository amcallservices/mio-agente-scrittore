import streamlit as st
import os, requests, re
from fpdf import FPDF
from openai import OpenAI

# 1. Configurazione e Connessione
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- NASCONDI ICONA GITHUB E MENU ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# CLASSE PDF PROFESSIONALE
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"{self.autore} - AI di Antonino", 0, 0, 'C')
            self.ln(20)

def chiedi_gpt(p, s_p):
    r = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role":"system","content":s_p},{"role":"user","content":p}],
        temperature=0.7
    )
    risposta = r.choices[0].message.content
    
    # --- FILTRO ANTI-COMMENTI POTENZIATO ---
    linee = risposta.split('\n')
    linee_pulite = []
    tag_da_eliminare = [
        "ecco", "certamente", "spero", "di seguito", "questo è", "il capitolo", 
        "ciao", "ghostwriter", "va bene", "perfetto", "fammi sapere", 
        "buona lettura", "proseguiamo", "posso aiutarti", "scritto per te"
    ]
    for l in linee:
        testo_l = l.strip().lower()
        if testo_l and not any(testo_l.startswith(p) for p in tag_da_eliminare):
            linee_pulite.append(l)
    
    testo_finale = '\n'.join(linee_pulite).strip()
    testo_finale = re.sub(r"(?i)(spero che|fammi sapere se|ecco il testo|buona scrittura|fammi sapere cosa).*$", "", testo_finale).strip()
    return testo_finale

# --- INTERFACCIA ---
st.title("AI di Antonino: \"Crea il tuo EBook\"")

with st.sidebar:
    st.header("Configurazione Libro")
    titolo = st.text_input("Titolo Libro", "")
    autore = st.text_input("Inserisci il tuo nome (Autore)", "")
    
    modalita = st.selectbox("Modalità di scrittura", [
        "Thriller Psicologico (Analisi mentale e tensione)", 
        "Saggio Psicologico (Analitico e riflessivo)",
        "Manuale Tecnico (Pratico e chiaro)",
        "Noir (Cupo e descrittivo)", 
        "Thriller (Azione e suspense)",
        "Motivazionale (Ispirazione)",
        "Fantasy (Epico)",
        "Romanzo Storico",
        "Romanzo Rosa"
    ])
    trama = st.text_area("Di cosa parla il tuo libro? (Trama)")

if trama:
    S_P = f"Sei un Ghostwriter esperto in {modalita}. Scrivi per l'autore {autore if autore else 'utente'}. "
    S_P += "IMPORTANTE: Produci SOLO testo narrativo. NON aggiungere introduzioni o saluti finali. Inizia e finisci SOLO con il contenuto del libro."

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Struttura", "🎨 Copertina AI", "✍️ Scrittura", "📝 Modifica", "📑 Esporta PDF"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea l'indice per il libro '{titolo}'. Trama: {trama}", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice generato", st.session_state['indice'], height=250)

    with tab2:
        st.subheader("Generatore di Copertina Artistica")
        if st.button("Genera Immagine Copertina"):
            with st.spinner("L'IA sta creando la copertina..."):
                try:
                    prompt_img = f"Professional book cover for '{titolo}', genre: {modalita}, theme: {trama[:100]}. High resolution, cinematic, no text."
                    res_img = client.images.generate(model="dall-e-3", prompt=prompt_img, n=1, size="1024x1792")
                    st.session_state['cover_url'] = res_img.data[0].url
                except Exception as e:
                    st.error(f"Errore: {e}")
        if 'cover_url' in st.session_state:
            st.image(st.session_state['cover_url'], caption="Anteprima Copertina", width=350)

    with tab3:
        scelta = st.selectbox("Cosa scriviamo?", ["Prefazione", "Capitolo", "Ringraziamenti"])
        n_cap = st.number_input("Numero (se capitolo)", 1, 30) if scelta == "Capitolo" else 0
        key_attuale = f"{scelta.lower()}_{n_cap}" if n_cap > 0 else scelta.lower()

        if st.button("Avvia Scrittura"):
            with st.spinner(f"Scrittura di {scelta} in corso..."):
                testo_completo = ""
                fasi = ["Parte iniziale", "Sviluppo centrale", "Conclusione"]
                for f in fasi:
                    testo_completo += chiedi_gpt(f"Scrivi la '{f}' di: {scelta} {n_cap if n_cap>0 else ''}. Titolo: {titolo}.", S_P) + "\n\n"
                st.session_state[key_attuale] = testo_completo

        if key_attuale in st.session_state:
            st.text_area("Contenuto Generato", st.session_state[key_attuale], height=400)

    with tab4:
        st.subheader("Revisione e Modifica Testi")
        # Elenco dinamico delle sezioni generate
        sezioni_generate = ["Prefazione", "Ringraziamenti"] + [f"Capitolo {i}" for i in range(1, 31)]
        sezione_mod = st.selectbox("Seleziona sezione da modificare", sezioni_generate)
        chiave_mod = sezione_mod.lower().replace(" ", "_")
        
        if chiave_mod in st.session_state:
            # Mostriamo il testo attuale
            testo_vecchio = st.session_state[chiave_mod]
            st.text_area("Testo attuale", testo_vecchio, height=250)
            
            istruzione = st.text_input("Cosa vuoi cambiare? (es: 'Rendi il tono più drammatico' o 'Aggiungi un dialogo')")
            
            if st.button("Applica Modifica"):
                with st.spinner("Modifica in corso..."):
                    # Chiediamo all'IA di riscrivere basandosi sul vecchio testo
                    prompt_modifica = f"Testo originale: {testo_vecchio}\n\nRichiesta di modifica: {istruzione}"
                    nuovo_testo = chiedi_gpt(prompt_modifica, S_P)
                    
                    # SALVATAGGIO DEFINITIVO NELLA SESSIONE
                    st.session_state[chiave_mod] = nuovo_testo
                    st.success("Testo modificato con successo!")
                    st.rerun() # Forza il ricaricamento della pagina per mostrare il nuovo testo
        else:
            st.info("Genera prima questa sezione nella scheda 'Scrittura' per poterla modificare qui.")

    with tab5:
        if st.button("Genera EBook Finale (PDF)"):
            pdf = PDF(autore if autore else "Autore")
            pdf.set_auto_page_break(True, 15)
            pdf.add_page()
            if 'cover_url' in st.session_state:
                try:
                    img_data = requests.get(st.session_state['cover_url']).content
                    with open("cover_temp.jpg", "wb") as f: f.write(img_data)
                    pdf.image("cover_temp.jpg", 0, 0, 210, 297)
                except:
                    pdf.set_font("Arial", "B", 30); pdf.cell(0, 100, titolo.upper(), 0, 1, "C")
            else:
                pdf.set_font("Arial", "B", 30); pdf.cell(0, 100, titolo.upper(), 0, 1, "C")

            sezioni_ordine = ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]
            for s in sezioni_ordine:
                if s in st.session_state:
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 18)
                    pdf.cell(0, 10, s.replace("_", " ").upper(), 0, 1, "L")
                    pdf.ln(10)
                    pdf.set_font("Arial", "", 11)
                    testo_pdf = st.session_state[s].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, testo_pdf)
            
            pdf.output("ebook.pdf")
            with open("ebook.pdf", "rb") as f:
                st.download_button("📥 SCARICA PDF FINALE", f, file_name=f"{titolo if titolo else 'Ebook'}.pdf")
