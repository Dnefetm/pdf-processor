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
    
    # Mostrar texto extraido para debugging
    with st.expander("Ver texto extraido del PDF"):
        st.text(full_text)
    
    # Extraer numero de envio/guia (buscar patron como 59438449)
    guia_match = re.search(r'Inbound[:\s-]*(\d+)', full_text, re.IGNORECASE)
    if not guia_match:
        guia_match = re.search(r'Env[ií]o[:\s]*(\d+)', full_text, re.IGNORECASE)
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
    
    # Mostrar tablas para debugging
    with st.expander("Ver tablas extraidas"):
        for i, row in enumerate(all_tables):
            st.write(f"Fila {i}: {row}")
    
    # Buscar filas con datos de productos
    for row in all_tables:
        if row and len(row) >= 4:
            # Verificar si es una fila de datos (no encabezado)
            row_text = ' '.join([str(cell) for cell in row if cell])
            
            # Buscar codigo ML en la fila
            ml_match = re.search(r'ML[A-Z]?\d+', row_text)
            if ml_match:
                codigo_ml = ml_match.group(0)
                
                # Extraer otros campos de la fila
                sku = ""
                nombre = ""
                unidades = "1"
                codigo_universal = ""
                
                for cell in row:
                    if cell:
                        cell_str = str(cell).strip()
                        # Detectar SKU (patron alfanumerico corto)
                        if re.match(r'^[A-Z0-9-]{4,20}$', cell_str) and cell_str != codigo_ml:
                            if not sku:
                                sku = cell_str
                            elif not codigo_universal and len(cell_str) >= 10:
                                codigo_universal = cell_str
                        # Detectar unidades (numero solo)
                        elif re.match(r'^\d{1,3}$', cell_str):
                            unidades = cell_str
                        # Detectar nombre (texto largo)
                        elif len(cell_str) > 20 and not re.match(r'^[A-Z0-9-]+$', cell_str):
                            nombre = cell_str
                
                productos.append({
                    'Guia': guia,
                    'Codigo ML': codigo_ml,
                    'Codigo Universal': codigo_universal,
                    'SKU': sku,
                    'Nombre': nombre,
                    'Unidades': unidades,
                })
    
    return productos, guia

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        productos, guia = parse_envios_full(pdf)
        
        if productos:
            df = pd.DataFrame(productos)
            # Asegurar que la guia este en todas las filas
            if guia:
                df['Guia'] = guia
            st.success(f"Se encontraron {len(df)} productos")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("Descargar CSV", csv, "envios_full.csv", "text/csv")
            
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            st.download_button("Descargar Excel", buf.getvalue(), "envios_full.xlsx")
        else:
            st.warning("No se encontraron productos. Revisa el texto extraido arriba para ver el formato del PDF.")
