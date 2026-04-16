import streamlit as st
import os, requests
from fpdf import FPDF
from openai import OpenAI

# Setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, 'Author Studio AI', 0, 0, 'C')

def gpt(p):
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"system","content":"Sei uno scrittore. Scrivi solo narrativa pura."},{"role":"user","content":p}]
    )
    return r.choices[0].message.content

st.title("🖋️ Author Studio Web")
t = st.text_input("Titolo")
a = st.text_input("Autore")
tr = st.text_area("Trama")

if tr:
    if st.button("📝 Genera Indice"):
        st.session_state['i'] = gpt("Crea indice per " + t + ": " + tr)
   
    if 'i' in st.session_state:
        st.text_area("Indice", st.session_state['i'], height=200)
       
    n = st.number_input("Capitolo", 1, 20)
    if st.button("✍️ Scrivi Capitolo"):
        with st.spinner("Scrivendo..."):
            testo = gpt("Scrivi il capitolo " + str(n) + " del libro " + t)
            st.session_state["c"+str(n)] = testo
        st.success("Capitolo pronto!")
        st.write(testo)

    if st.button("🚀 Scarica PDF"):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 50, t.upper(), 0, 1, "C")
        for i in range(1, 21):
            if ("c"+str(i)) in st.session_state:
                pdf.add_page()
                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, st.session_state["c"+str(i)].encode('latin-1', 'replace').decode('latin-1'))
        pdf.output("ebook.pdf")
        with open("ebook.pdf", "rb") as f:
            st.download_button("📥 Download", f, "libro.pdf")
