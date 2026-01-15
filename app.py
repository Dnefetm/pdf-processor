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
    
    # Extraer numero de guia del texto
    guia_match = re.search(r'Inbound[:\s-]*(\d+)', full_text, re.IGNORECASE)
    if not guia_match:
        guia_match = re.search(r'(\d{8,})', full_text)
    if guia_match:
        guia = guia_match.group(1)
    
    # Extraer tablas del PDF
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            all_tables.extend(table)
    
    # Procesar cada fila de la tabla
    for row in all_tables:
        if not row or len(row) < 2:
            continue
        
        # Saltar filas de encabezado
        primera_celda = str(row[0]) if row[0] else ""
        if 'PRODUCTO' in primera_celda.upper() and 'UNIDADES' in str(row):
            continue
        
        # Verificar si contiene datos de producto (Codigo ML)
        if 'digo ML' not in primera_celda:
            continue
        
        # Extraer datos de la primera celda
        texto_producto = primera_celda
        
        # Extraer Codigo ML
        ml_match = re.search(r'digo\s*ML[:\s]*([A-Z0-9]+)', texto_producto, re.IGNORECASE)
        codigo_ml = ml_match.group(1) if ml_match else ""
        
        # Extraer Codigo Universal
        universal_match = re.search(r'digo\s*universal[:\s]*([A-Z0-9]+|N/?A)', texto_producto, re.IGNORECASE)
        codigo_universal = universal_match.group(1) if universal_match else ""
        
        # Extraer SKU
        sku_match = re.search(r'SKU[:\s]*([^\n]+)', texto_producto, re.IGNORECASE)
        sku = sku_match.group(1).strip() if sku_match else ""
        
        # Extraer Nombre (lineas despues del SKU)
        nombre = ""
        lines = texto_producto.split('\n')
        encontro_sku = False
        for line in lines:
            if 'SKU' in line.upper():
                encontro_sku = True
                continue
            if encontro_sku and line.strip():
                nombre = line.strip()
                break
        
        # Extraer Unidades (segunda celda)
        unidades = str(row[1]).strip() if len(row) > 1 and row[1] else "1"
        
        # Extraer Identificacion (tercera celda)
        identificacion = str(row[2]).replace('\n', ' ').strip() if len(row) > 2 and row[2] else ""
        
        # Extraer Instrucciones (cuarta celda)
        instrucciones = str(row[3]).replace('\n', ' ').strip() if len(row) > 3 and row[3] else ""
        
        productos.append({
            'Guia': guia,
            'Codigo ML': codigo_ml,
            'Codigo Universal': codigo_universal,
            'SKU': sku,
            'Nombre': nombre,
            'Unidades': unidades,
            'Identificacion': identificacion,
            'Instrucciones': instrucciones
        })
    
    return productos, guia

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        productos, guia = parse_envios_full(pdf)
        
        if productos:
            df = pd.DataFrame(productos)
            if guia:
                df['Guia'] = guia
            
            st.success(f"Se encontraron {len(df)} productos. Guia: {guia}")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("Descargar CSV", csv, f"envios_full_{guia}.csv", "text/csv")
            
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            st.download_button("Descargar Excel", buf.getvalue(), f"envios_full_{guia}.xlsx")
        else:
            st.warning("No se encontraron productos.")
