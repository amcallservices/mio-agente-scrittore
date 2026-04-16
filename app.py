import streamlit as st
import os, requests
from fpdf import FPDF
from openai import OpenAI

# 1. Configurazione
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"{self.autore} - Ultimate Author Studio", 0, 0, 'C')
            self.ln(20)

def chiedi_gpt(p, s_p):
    r = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role":"system","content":s_p},{"role":"user","content":p}],
        temperature=0.8
    )
    risposta = r.choices[0].message.content
    # Filtro anti-commenti: rimuove righe che iniziano con saluti o introduzioni tipiche
    linee = risposta.split('\n')
    pulite = [l for l in linee if not l.strip().lower().startswith(("ecco", "certamente", "spero", "di seguito", "questo è", "il capitolo", "ciao"))]
    return '\n'.join(pulite).strip()

# --- INTERFACCIA ---
st.title("🖋️ Ultimate Author Studio AI")

with st.sidebar:
    st.header("Configurazione Libro")
    titolo = st.text_input("Titolo Libro", "Titolo")
    autore = st.text_input("Autore", "Antonino")
    modalita = st.selectbox("Modalità di scrittura", [
        "Thriller (Suspense e colpi di scena)", 
        "Manuale Tecnico (Pratico e chiaro)", 
        "Noir (Cupo e descrittivo)", 
        "Motivazionale (Energico)",
        "Fantasy (Epico)"
    ])
    trama = st.text_area("Trama/Argomento")

if trama:
    # Prompt di sistema ultra-rigido per evitare commenti
    S_P = f"Sei un Ghostwriter professionista esperto in {modalita}. Scrivi per l'autore {autore}. "
    S_P += "REGOLE CRITICHE: 1. Scrivi SOLO il testo del libro. 2. NON salutare, NON spiegare cosa hai scritto, NON fare commenti. 3. Produci narrativa pura o contenuti tecnici diretti."

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Struttura", "🎨 Copertina AI", "✍️ Scrittura", "📝 Modifica", "📑 Esporta PDF"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea l'indice per il libro '{titolo}'. Trama: {trama}", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice", st.session_state['indice'], height=250)

    with tab2:
        st.subheader("Generatore di Copertina Artistica")
        if st.button("Genera Immagine Copertina"):
            with st.spinner("DALL-E 3 sta dipingendo la tua copertina..."):
                try:
                    prompt_img = f"Professional book cover for '{titolo}', style: {modalita}, theme: {trama[:100]}. High resolution, cinematic lighting, no text."
                    res_img = client.images.generate(model="dall-e-3", prompt=prompt_img, n=1, size="1024x1792")
                    st.session_state['cover_url'] = res_img.data[0].url
                except Exception as e:
                    st.error(f"Errore generazione immagine: {e}")
        
        if 'cover_url' in st.session_state:
            st.image(st.session_state['cover_url'], caption="Copertina Generata", width=350)

    with tab3:
        scelta = st.selectbox("Cosa scriviamo?", ["Prefazione", "Capitolo", "Ringraziamenti"])
        n_cap = st.number_input("Numero (se capitolo)", 1, 30) if scelta == "Capitolo" else 0
        
        if st.button("Avvia Scrittura"):
            with st.spinner("Scrittura in corso (Fase tripla per massima lunghezza)..."):
                testo_completo = ""
                fasi = ["Parte iniziale", "Sviluppo centrale", "Conclusione"]
                for f in fasi:
                    testo_completo += chiedi_gpt(f"Scrivi la '{f}' di: {scelta} {n_cap if n_cap>0 else ''}. Titolo: {titolo}. Trama: {trama}.", S_P) + "\n\n"
                
                key = f"{scelta.lower()}_{n_cap}" if n_cap > 0 else scelta.lower()
                st.session_state[key] = testo_completo
                st.success("Testo generato senza commenti!")
                st.text_area("Risultato", testo_completo, height=300)

    with tab4:
        st.subheader("Revisione e Modifica")
        sezione_mod = st.selectbox("Seleziona sezione da modificare", ["Prefazione", "Ringraziamenti"] + [f"Capitolo {i}" for i in range(1, 31)])
        chiave_mod = sezione_mod.lower().replace(" ", "_")
        
        if chiave_mod in st.session_state:
            modifica_richiesta = st.text_input("Cosa vuoi cambiare? (es: 'Rendilo più triste')")
            if st.button("Applica Revisione"):
                testo_aggiornato = chiedi_gpt(f"Modifica questo testo: {st.session_state[chiave_mod]}. Richiesta: {modifica_richiesta}", S_P)
                st.session_state[chiave_mod] = testo_aggiornato
                st.success("Testo modificato correttamente!")
        else:
            st.info("Genera prima questa sezione per poterla modificare.")

    with tab5:
        if st.button("Genera PDF Finale"):
            pdf = PDF(autore)
            pdf.set_auto_page_break(True, 15)
            
            # --- PAGINA COPERTINA ---
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

            # --- PAGINE CONTENUTO ---
            sezioni_ordine = ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]
            for s in sezioni_ordine:
                if s in st.session_state:
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 18)
                    pdf.cell(0, 10, s.replace("_", " ").upper(), 0, 1, "L")
                    pdf.ln(10)
                    pdf.set_font("Arial", "", 11)
                    testo_pdf = st.session_state[s].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, testo_pdf) # 0 = Larghezza automatica corretta
            
            pdf.output("ebook_finale.pdf")
            with open("ebook_finale.pdf", "rb") as f:
                st.download_button("📥 SCARICA EBOOK PDF", f, file_name=f"{titolo}.pdf")
