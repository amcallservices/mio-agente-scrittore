import streamlit as st
import os, requests
from fpdf import FPDF
from openai import OpenAI

# 1. Configurazione e Connessione
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CLASSE PDF CORRETTA (Sistemata per evitare testo verticale)
class PDF(FPDF):
    def __init__(self, autore):
        super().__init__()
        self.autore = autore
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f"{self.autore} - Author Studio AI", 0, 0, 'C')
            self.ln(20)

def chiedi_gpt(p, s_p):
    r = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role":"system","content":s_p},{"role":"user","content":p}],
        temperature=0.8
    )
    return r.choices[0].message.content

# --- INTERFACCIA ---
st.title("🖋️ Ultimate Author Studio V2")

with st.sidebar:
    st.header("Configurazione")
    titolo = st.text_input("Titolo Libro", "Le Ombre di Ravenwood")
    autore = st.text_input("Nome Autore", "Antonino")
    
    # NUOVA FUNZIONE: SCELTA MODALITÀ
    modalita = st.selectbox("Tipo di Libro", [
        "Thriller (Tensione e colpi di scena)", 
        "Manuale/Saggio (Tecnico e formativo)", 
        "Noir (Atmosfere cupe e mistero)", 
        "Motivazionale (Ispirazione e azione)",
        "Romanzo Rosa (Emozioni e relazioni)"
    ])
    
    trama = st.text_area("Trama o Argomento principale")

if trama:
    # Prompt di sistema dinamico in base alla modalità scelta
    S_P = f"Sei un Ghostwriter esperto in {modalita}. Scrivi per l'autore {autore}. "
    if "Thriller" in modalita:
        S_P += "Usa frasi brevi, crea suspense e focalizzati sui dettagli sensoriali inquietanti."
    elif "Manuale" in modalita:
        S_P += "Usa un tono autorevole, elenchi puntati discorsivi e spiega i concetti in modo chiaro e pratico."
    else:
        S_P += "Usa uno stile narrativo coinvolgente e profondo."

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Struttura", "✍️ Scrittura", "🎨 Modifica", "📑 Esporta PDF"])

    with tab1:
        if st.button("Genera Indice"):
            st.session_state['indice'] = chiedi_gpt(f"Crea un indice dettagliato per un libro {modalita} intitolato '{titolo}'. Trama: {trama}", S_P)
        if 'indice' in st.session_state:
            st.text_area("Indice", st.session_state['indice'], height=250)

    with tab2:
        tipo_scrittura = st.selectbox("Cosa vuoi scrivere?", ["Prefazione", "Capitolo", "Ringraziamenti"])
        n_cap = st.number_input("Se è un capitolo, quale numero?", 1, 30) if tipo_scrittura == "Capitolo" else 0
        
        if st.button("Avvia Scrittura Profonda"):
            with st.spinner("L'IA sta elaborando (fase 1 di 3)..."):
                testo_finale = ""
                fasi = ["Inizio e ambientazione", "Sviluppo centrale", "Conclusione e gancio"]
                for fase in fasi:
                    prompt = f"Scrivi la parte '{fase}' del {tipo_scrittura} {n_cap if n_cap > 0 else ''}. Genere: {modalita}."
                    testo_finale += chiedi_gpt(prompt, S_P) + "\n\n"
                
                chiave = f"{tipo_scrittura.lower()}_{n_cap}" if n_cap > 0 else tipo_scrittura.lower()
                st.session_state[chiave] = testo_finale
                st.success("Scrittura completata!")
                st.text_area("Anteprima", testo_finale, height=300)

    with tab3:
        st.subheader("Modifica Testi Esistenti")
        file_da_mod = st.selectbox("Scegli cosa modificare", ["Prefazione", "Ringraziamenti"] + [f"Capitolo {i}" for i in range(1, 31)])
        testo_vecchio = st.session_state.get(file_da_mod.lower().replace(" ", "_"), "")
        
        if testo_vecchio:
            modifica = st.text_input("Cosa vuoi cambiare in questo testo?")
            if st.button("Applica Modifica"):
                nuovo_testo = chiedi_gpt(f"Testo originale: {testo_vecchio}\n\nApplica questa modifica: {modifica}", S_P)
                st.session_state[file_da_mod.lower().replace(" ", "_")] = nuovo_testo
                st.success("Testo aggiornato!")
        else:
            st.warning("Scrivi prima questa sezione per poterla modificare.")

    with tab4:
        if st.button("Genera e Scarica PDF"):
            pdf = PDF(autore)
            pdf.set_auto_page_break(True, 15)
            
            # Copertina semplice
            pdf.add_page()
            pdf.set_font("Arial", "B", 30)
            pdf.ln(80)
            pdf.cell(0, 10, titolo.upper(), 0, 1, "C")
            pdf.set_font("Arial", "", 18)
            pdf.cell(0, 20, f"di {autore}", 0, 1, "C")
            pdf.cell(0, 10, f"Genere: {modalita}", 0, 1, "C")

            # Aggiunta Sezioni
            sezioni = ["prefazione"] + [f"capitolo_{i}" for i in range(1, 31)] + ["ringraziamenti"]
            for s in sezioni:
                if s in st.session_state:
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, s.replace("_", " ").upper(), 0, 1, "L")
                    pdf.ln(5)
                    pdf.set_font("Arial", "", 11)
                    
                    # CORREZIONE PDF: multi_cell con larghezza 0 (tutta pagina) e altezza riga 7
                    t_pulito = st.session_state[s].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, t_pulito) 
            
            pdf.output("libro_corretto.pdf")
            with open("libro_corretto.pdf", "rb") as f:
                st.download_button("📥 SCARICA EBOOK CORRETTO", f, file_name=f"{titolo}.pdf")
