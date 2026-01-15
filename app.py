import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

st.set_page_config(page_title="PDF a CSV - Envios Full")
st.title("Procesador PDF Envios Full")
uploaded_file = st.file_uploader("Sube tu PDF de Mercado Libre", type="pdf")

def parse_envios_full(pdf):
    productos = []
    guia = ""
    
    full_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    # Extraer numero de envio
    envio_match = re.search(r'Env[ií]o\s*(\d+)', full_text)
    if envio_match:
        guia = envio_match.group(1)
    
    # Patron para extraer productos
    pattern = r'C[oó]digo\s*ML\s*([A-Z0-9]+)\s*C[oó]digo\s*universal\s*([A-Z0-9]+|NA)\s*SKU\s*([^\n]+?)\s+([A-Z][^C]+?)(?=C[oó]digo\s*ML|PRODUCTO|$)'
    
    matches = re.findall(pattern, full_text, re.IGNORECASE | re.DOTALL)
    
    # Extraer unidades de la tabla PRODUCTO UNIDADES
    unidades_pattern = r'PRODUCTO\s+UNIDADES\s+IDENTIFICACI[OÓ]N\s+INSTRUCCIONES[^\d]*([\d\s]+)'
    unidades_matches = re.findall(unidades_pattern, full_text, re.IGNORECASE)
    
    unidades_list = []
    for um in unidades_matches:
        nums = re.findall(r'\d+', um)
        unidades_list.extend(nums)
    
    for i, match in enumerate(matches):
        codigo_ml = match[0].strip()
        codigo_universal = match[1].strip()
        sku_nombre = match[2].strip() + " " + match[3].strip()
        
        # Separar SKU del nombre
        parts = sku_nombre.split(" ", 1)
        sku = parts[0] if parts else ""
        nombre = parts[1] if len(parts) > 1 else ""
        nombre = nombre.replace(",", " ").strip()
        nombre = re.sub(r'\s+', ' ', nombre)
        nombre = re.sub(r'Etiquetado obligatorio.*', '', nombre, flags=re.IGNORECASE).strip()
        
        unidades = unidades_list[i] if i < len(unidades_list) else "1"
        
        productos.append({
            'Codigo ML': codigo_ml,
            'Codigo Universal': codigo_universal,
            'SKU': sku,
            'Nombre': nombre,
            'Unidades': unidades,
            'Identificacion': 'Etiquetado obligatorio',
            'Instrucciones de preparacion': '',
            'Guia': guia
        })
    
    return productos

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        productos = parse_envios_full(pdf)
        
        if productos:
            df = pd.DataFrame(productos)
            st.success(f"Se encontraron {len(df)} productos")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("Descargar CSV", csv, "envios_full.csv", "text/csv")
            
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            st.download_button("Descargar Excel", buf.getvalue(), "envios_full.xlsx")
        else:
            st.warning("No se encontraron productos.")
