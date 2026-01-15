import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

st.set_page_config(page_title="PDF a CSV - Envios Full", page_icon="\ud83d\udce6")
st.title("\ud83d\udce6 Procesador PDF Envios Full")

uploaded_file = st.file_uploader("Sube tu PDF", type="pdf")

def parse_envios(pdf):
    productos = []
    guia_actual = ""
    
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        
        # Buscar numero de envio/guia
        envio_match = re.search(r'Envio\s*#?\s*(\d+)', text, re.IGNORECASE)
        if envio_match:
            guia_actual = envio_match.group(1)
        
        # Buscar productos con patron: Codigo ML, Codigo universal, SKU, etc
        pattern = r'Codigo\s*ML[:\s]*([A-Z0-9]+)\s*Codigo\s*universal[:\s]*(\d+)\s*SKU[:\s]*([^\s]+)\s+(.+?)\s+(\d+)\s'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            codigo_ml, codigo_universal, sku, nombre, unidades = match
            nombre_limpio = nombre.replace(',', ' ').strip()
            productos.append({
                'Codigo ML': codigo_ml,
                'Codigo Universal': codigo_universal,
                'SKU': sku,
                'Nombre': nombre_limpio,
                'Unidades': unidades,
                'Identificacion': '',
                'Instrucciones de preparacion': '',
                'Guia': guia_actual
            })
    
    return productos

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        productos = parse_envios(pdf)
        
        if productos:
            df = pd.DataFrame(productos)
            st.success(f"Se encontraron {len(df)} productos")
            st.dataframe(df)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("Descargar CSV", csv, "envios_full.csv", "text/csv")
            
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            st.download_button("Descargar Excel", buf.getvalue(), "envios_full.xlsx")
        else:
            st.warning("No se encontraron productos. Verifica el formato del PDF.")
