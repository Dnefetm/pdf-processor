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
    
    # Extraer numero de guia
    guia_match = re.search(r'Inbound[:\s-]*(\d+)', full_text, re.IGNORECASE)
    if not guia_match:
        guia_match = re.search(r'(\d{8,})', full_text)
    if guia_match:
        guia = guia_match.group(1)
    
    # Extraer tablas del PDF
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                primera_celda = str(row[0]) if row[0] else ""
                
                # Saltar encabezados
                if 'PRODUCTO' in primera_celda.upper():
                    continue
                
                # Buscar filas con Codigo ML
                if 'digo ML' not in primera_celda and 'Codigo ML' not in primera_celda:
                    continue
                
                # Extraer Codigo ML
                ml_match = re.search(r'digo\s*ML[:\s]*([A-Z0-9]+)', primera_celda, re.IGNORECASE)
                codigo_ml = ml_match.group(1) if ml_match else ""
                
                # Extraer Codigo Universal
                univ_match = re.search(r'digo\s*universal[:\s]*([A-Z0-9/]+)', primera_celda, re.IGNORECASE)
                codigo_universal = univ_match.group(1) if univ_match else ""
                
                # Extraer SKU y Nombre con logica mejorada
                sku = ""
                nombre = ""
                lines = primera_celda.split('\n')
                
                # Encontrar la linea del SKU
                sku_line_idx = -1
                for i, line in enumerate(lines):
                    if 'SKU' in line.upper():
                        sku_match = re.search(r'SKU[:\s]*(.+)', line, re.IGNORECASE)
                        if sku_match:
                            sku = sku_match.group(1).strip()
                        sku_line_idx = i
                        break
                
                # Procesar lineas despues del SKU
                if sku_line_idx >= 0:
                    remaining_lines = lines[sku_line_idx + 1:]
                    nombre_parts = []
                    
                    for line in remaining_lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Si la linea es solo numeros/espacios cortos, es parte del SKU
                        if re.match(r'^[\d\s]+$', line) and len(line) <= 15:
                            sku = sku + " " + line
                        else:
                            # Es el nombre del producto
                            nombre_parts.append(line)
                    
                    nombre = ' '.join(nombre_parts)
                
                # Limpiar SKU (remover espacios extra)
                sku = re.sub(r'\s+', ' ', sku).strip()
                
                # Unidades (segunda celda)
                unidades = str(row[1]).strip() if len(row) > 1 and row[1] else "1"
                
                # Identificacion (tercera celda)
                identificacion = ""
                if len(row) > 2 and row[2]:
                    identificacion = str(row[2]).replace('\n', ' ').strip()
                
                # Instrucciones (cuarta celda)
                instrucciones = ""
                if len(row) > 3 and row[3]:
                    instrucciones = str(row[3]).replace('\n', ' ').strip()
                
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
            st.warning("No se encontraron productos en el PDF.")
