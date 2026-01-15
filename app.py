import streamlit as st
import pdfplumber
import pandas as pd
import io

st.set_page_config(page_title="PDF a CSV", page_icon="📄")
st.title("📄 Procesador PDF Envios Full")

uploaded_file = st.file_uploader("Sube tu PDF", type="pdf")

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        data = []
        for page in pdf.pages:
            for table in page.extract_tables():
                data.extend([r for r in table if r and any(r)])
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            st.download_button("Descargar CSV", df.to_csv(index=False), "envios.csv", "text/csv")
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            st.download_button("Descargar Excel", buf.getvalue(), "envios.xlsx")
        else:
            st.warning("No se encontraron tablas")
