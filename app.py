import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# 1. Configuración de la página
st.set_page_config(page_title="Generador de Plano Estandarizado", layout="wide")

# ==========================================
# 2. ESTILO CSS
# ==========================================
st.markdown("""
    <style>
        /* =========================================
           FONDO DE EDIFICIO VIDRIADO (MODERNO)
           ========================================= */
        .stApp {
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.70), rgba(255, 255, 255, 0.70)),
                url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2670&auto=format&fit=crop');
            background-size: cover;
            background-attachment: fixed;
            background-position: center center;
        }

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        .block-container { 
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        .canvas-container {
            background-color: #ffffff;
            background-image: radial-gradient(#d1d5db 1px, transparent 1px);
            background-size: 20px 20px;
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            padding: 80px;
            min-height: 750px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }

        .main-title { font-weight: 800; letter-spacing: -1px; color: #1e293b; margin-bottom: 0px; }
        
        .metric-card {
            background: #ffffff;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border: 1px solid #f0f2f6;
            margin-bottom: 15px;
        }

        /* Clases para la pieza */
        .pieza-base {
            position: relative;
            transition: all 0.3s ease;
        }

        .modo-solido {
            background-color: var(--color-pieza);
            border: 2px solid #0f172a;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }

        .modo-contorno {
            background-color: rgba(255,255,255,0.5);
            border: 4px solid var(--color-pieza);
        }

        .etiqueta-medida {
            position: absolute;
            font-weight: 800;
            color: #1e293b;
            font-size: 14px;
            background: #f8f9fa;
            padding: 5px 15px;
            border: 2px solid #1e293b;
            border-radius: 5px;
            white-space: nowrap;
            z-index: 10;
            pointer-events: none;
        }
        
        .etiqueta-ancho { bottom: -50px; left: 50%; transform: translateX(-50%); }
        .etiqueta-alto { left: -80px; top: 50%; transform: translateY(-50%) rotate(-90deg); transform-origin: center; }

    </style>
""", unsafe_allow_html=True)

# Título
st.markdown('<h1 class="main-title">📐 Generador de Plano <span style="color:#3b82f6;">Estandarizado</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748b; margin-top:-10px;">Configuración técnica y visualización de perforaciones en tiempo real</p>', unsafe_allow_html=True)

# ==============================================================================
# 3. SIDEBAR MEJORADO (AQUÍ ESTÁN LOS CAMBIOS SOLICITADOS)
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2312/2312444.png", width=70)
    st.markdown("### Configuración del Vidrio")
    
    # MEJORA 1: Organización por Pestañas para limpiar la interfaz
    tab_medidas, tab_perf, tab_estilo = st.tabs(["📏 Medidas", "🔘 Perforaciones", "🎨 Estilo"])
    
    # --- PESTAÑA 1: MEDIDAS ---
    with tab_medidas:
        # MEJORA 2: Presets de medidas estándar
        opciones_medidas = {
            "Personalizado": (1200, 800),
            "Puerta Estándar (2100x900)": (900, 2100),
            "Hoja Ventana (1200x1200)": (1200, 1200),
            "Mampara Baño (1800x800)": (800, 1800),
            "Plancha Jumbo (2500x3600)": (3600, 2500)
        }
        seleccion = st.selectbox("Seleccionar Tipo", list(opciones_medidas.keys()))
        
        # Lógica para usar preset o manual
        ancho_default, alto_default = opciones_medidas[seleccion]
        disabled_inputs = (seleccion != "Personalizado")
        
        c1, c2 = st.columns(2)
        val_ancho = c1.number_input("Ancho (mm)", 1, 6000, ancho_default, 10, disabled=disabled_inputs, key="ancho_input")
        val_alto = c2.number_input("Alto (mm)", 1, 6000, alto_default, 10, disabled=disabled_inputs, key="alto_input")
        
        st.info(f"Superficie: {round((val_ancho*val_alto)/1000000, 2)} m²")

    # --- PESTAÑA 2: PERFORACIONES ---
    with tab_perf:
        num_perf = st.number_input("Cantidad de orificios", 0, 50, 1)
        
        lista_perforaciones = []
        if num_perf > 0:
            st.markdown("---")
            for i in range(int(num_perf)):
                with st.expander(f"📍 Perforación #{i+1}", expanded=(i == 0)):
                    c1, c2, c3 = st.columns([1, 1, 1])
                    px = c1.number_input(f"X (mm)", 0, val_ancho, 100 + (i*150), key=f"x{i}")
                    py = c2.number_input(f"Y (mm)", 0, val_alto, 100 + (i*150), key=f"y{i}")
                    pd = c3.number_input(f"Ø (mm)", 1, 200, 50, key=f"d{i}")
                    
                    # MEJORA 3: Validación visual en tiempo real
                    fuera_rango = False
                    if px > val_ancho or px < 0:
                        st.warning(f"⚠️ 'X' fuera del vidrio (Max: {val_ancho})")
                        fuera_rango = True
                    if py > val_alto or py < 0:
                        st.warning(f"⚠️ 'Y' fuera del vidrio (Max: {val_alto})")
                        fuera_rango = True
                    
                    # Solo agregamos a la lista, la advertencia es visual para el usuario
                    lista_perforaciones.append({"id": i+1, "x": px, "y": py, "diam": pd})
        else:
            st.caption("Sin perforaciones seleccionadas.")

    # --- PESTAÑA 3: ESTILO ---
    with tab_estilo:
        tipo_fig = st.radio("Estilo de Visualización", ["Solo Contorno", "Sólida"], horizontal=True)
        color_p = st.color_picker("Color del Vidrio", "#1E3A8A")
        st.caption("Este color se usará en la visualización web.")

# 4. Lógica Backend
esc = 0.20 
w_vis = val_ancho * esc
h_vis = val_alto * esc

if tipo_fig == "Sólida":
    clase_visual = "modo-solido"
else:
    clase_visual = "modo-contorno"

# Construcción del HTML
html_p = ""
for i, p in enumerate(lista_perforaciones):
    px_v, py_v, pd_v = p["x"] * esc, p["y"] * esc, p["diam"] * esc
    c_izq, c_arr = p["x"] < (val_ancho / 2), p["y"] < (val_alto / 2)
    sep = 30 + (i * 22)
    
    left_pos = px_v - (pd_v/2)
    top_pos = py_v - (pd_v/2)
    
    # 1. Cota Y
    altura_linea = py_v if c_arr else (h_vis - py_v)
    pos_y_container = "bottom: 50%;" if c_arr else "top: 50%;"
    pos_y_label = "top: -24px;" if c_arr else "bottom: -24px;"
    html_cota_y = f'<div style="position: absolute; {pos_y_container} left: 50%; width: 1px; height: {altura_linea + sep}px; border-left: 1px dashed #ef4444;"><span style="position: absolute; {pos_y_label} left: 50%; transform: translateX(-50%); color: #ef4444; font-size: 10px; font-weight: 800; background: white; padding: 2px 6px; border: 1px solid #ef4444; border-radius: 4px;">{p["y"]}</span></div>'

    # 2. Cota X
    ancho_linea = px_v if c_izq else (w_vis - px_v)
    pos_x_container = "right: 50%;" if c_izq else "left: 50%;"
    trans_x_label = "translateX(-100%)" if c_izq else "translateX(100%)"
    pos_x_label = "left: -10px;" if c_izq else "right: -10px;"
    html_cota_x = f'<div style="position: absolute; {pos_x_container} top: 50%; height: 1px; width: {ancho_linea + sep + 40}px; border-top: 1px dashed #ef4444;"><span style="position: absolute; {pos_x_label} top: 50%; transform: translateY(-50%) {trans_x_label}; color: #ef4444; font-size: 10px; font-weight: 800; background: white; padding: 2px 6px; border: 1px solid #ef4444; border-radius: 4px;">{p["x"]}</span></div>'

    # 3. Ensamblaje
    html_p += f'<div style="position: absolute; left: {left_pos}px; top: {top_pos}px; width: {pd_v}px; height: {pd_v}px; z-index: {60-i}; background: white; border: 2px solid #ef4444; border-radius: 50%; display: flex; justify-content: center; align-items: center;"><div style="width: 1px; height: 100%; background: #ef4444; position: absolute; opacity: 0.5;"></div><div style="height: 1px; width: 100%; background: #ef4444; position: absolute; opacity: 0.5;"></div>{html_cota_y}{html_cota_x}</div>'

# 5. Renderizado Principal
col_canvas, col_ficha = st.columns([3, 1], gap="medium")
with col_canvas:
    canvas_html = f"""
    <div class="canvas-container">
        <div class="pieza-base {clase_visual}" style="width: {w_vis}px; height: {h_vis}px; --color-pieza: {color_p};">
            {html_p}
            <div class="etiqueta-medida etiqueta-ancho">{val_ancho} mm</div>
            <div class="etiqueta-medida etiqueta-alto">{val_alto} mm</div>
        </div>
    </div>
    """
    st.markdown(canvas_html.replace("\n", ""), unsafe_allow_html=True)

# 6. Función PDF
def create_pdf(ancho_mm, alto_mm, perforaciones, color_hex, tipo, n_perf):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Configuramos el color Negro para todo el plano técnico
    NEGRO = colors.black
    BLANCO = colors.white
    
    # 1. Marco de la Página
    margen_marco = 20
    c.setStrokeColor(NEGRO)
    c.setLineWidth(3)
    c.rect(margen_marco, margen_marco, width - (2*margen_marco), height - (2*margen_marco))
    
    # 2. Encabezado
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(NEGRO)
    c.drawCentredString(width/2, height - 70, "PLANO ESTANDARIZADO")
    c.setLineWidth(1)
    c.line(margen_marco, height - 90, width - margen_marco, height - 90)

    # 3. Lógica de Escala
    margen = 100
    scale = min((width - margen*2) / ancho_mm, (height - 350) / alto_mm)
    start_x = (width - (ancho_mm * scale)) / 2
    start_y = height - 200 - (alto_mm * scale)

    # 4. Dibujo de la Pieza (Estilo Técnico)
    if tipo == "Sólida":
        c.setFillColor(colors.lightgrey) 
        c.setStrokeColor(NEGRO)
        c.setLineWidth(2)
        c.rect(start_x, start_y, ancho_mm * scale, alto_mm * scale, fill=1, stroke=1)
    else:
        c.setStrokeColor(NEGRO)
        c.setLineWidth(3)
        c.rect(start_x, start_y, ancho_mm * scale, alto_mm * scale, fill=0, stroke=1)

    # 5. Dibujo de Perforaciones y Cotas
    for i, p in enumerate(perforaciones):
        cx = start_x + (p["x"] * scale)
        cy = (start_y + (alto_mm * scale)) - (p["y"] * scale)
        radio = (p["diam"] / 2) * scale
        
        c.setFillColor(BLANCO)
        c.setStrokeColor(NEGRO)
        c.setLineWidth(1.5)
        c.circle(cx, cy, radio, fill=1, stroke=1)
        
        c.setLineWidth(0.5)
        c.line(cx - radio + 2, cy, cx + radio - 2, cy)
        c.line(cx, cy - radio + 2, cx, cy + radio - 2)
        
        c.setDash(2, 2)
        c.setStrokeColor(NEGRO)
        c.setLineWidth(0.8)
        
        # Cota Y
        dist_y_texto = p['y']
        if p["y"] < alto_mm/2: 
            y_dest = start_y + (alto_mm * scale)
            c.line(cx, cy + radio, cx, y_dest)
            label_y_pos = (cy + radio + y_dest) / 2
        else:
            y_dest = start_y
            c.line(cx, cy - radio, cx, y_dest)
            label_y_pos = (cy - radio + y_dest) / 2

        c.setDash()
        text_y = str(p['y'])
        c.setFont("Helvetica-Bold", 8)
        w_text_y = c.stringWidth(text_y, "Helvetica-Bold", 8)
        
        c.setFillColor(BLANCO)
        c.setStrokeColor(NEGRO)
        c.setLineWidth(0.5)
        c.rect(cx - w_text_y/2 - 2, label_y_pos - 4, w_text_y + 4, 8, fill=1, stroke=1)
        c.setFillColor(NEGRO)
        c.drawCentredString(cx, label_y_pos - 2.5, text_y)
        c.setDash(2, 2)

        # Cota X
        if p["x"] < ancho_mm/2:
            x_dest = start_x
            c.line(cx - radio, cy, x_dest, cy)
            label_x_pos = (cx - radio + x_dest) / 2
        else:
            x_dest = start_x + (ancho_mm * scale)
            c.line(cx + radio, cy, x_dest, cy)
            label_x_pos = (cx + radio + x_dest) / 2

        c.setDash()
        text_x = str(p['x'])
        w_text_x = c.stringWidth(text_x, "Helvetica-Bold", 8)
        
        c.setFillColor(BLANCO)
        c.setStrokeColor(NEGRO)
        c.rect(label_x_pos - w_text_x/2 - 2, cy - 4, w_text_x + 4, 8, fill=1, stroke=1)
        c.setFillColor(NEGRO)
        c.drawCentredString(label_x_pos, cy - 2.5, text_x)

    # 6. Cotas Generales
    c.setDash()
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(NEGRO)
    
    ancho_txt = f"{ancho_mm} mm"
    w_txt = c.stringWidth(ancho_txt, "Helvetica-Bold", 12)
    c.setStrokeColor(NEGRO)
    c.setLineWidth(1)
    c.roundRect(width/2 - w_txt/2 - 10, start_y - 40, w_txt + 20, 20, 4, fill=0, stroke=1)
    c.drawCentredString(width/2, start_y - 34, ancho_txt)
    
    c.saveState()
    c.translate(start_x - 40, start_y + (alto_mm*scale)/2)
    c.rotate(90)
    alto_txt = f"{alto_mm} mm"
    w_txt_h = c.stringWidth(alto_txt, "Helvetica-Bold", 12)
    c.roundRect(-w_txt_h/2 - 10, -10, w_txt_h + 20, 20, 4, fill=0, stroke=1)
    c.drawCentredString(0, -4, alto_txt)
    c.restoreState()

    c.save()
    buffer.seek(0)
    return buffer

with col_ficha:
    st.markdown("### 📋 Ficha Técnica")
    st.markdown(f'<div class="metric-card" style="border-left: 5px solid {color_p};"><small>Medidas</small><h2>{val_ancho}x{val_alto}</h2></div>', unsafe_allow_html=True)
    pdf_file = create_pdf(val_ancho, val_alto, lista_perforaciones, color_p, tipo_fig, num_perf)
    st.download_button(label="📥 Descargar Plano PDF", data=pdf_file, file_name="plano_tecnico_bn.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.caption("🚀 Generador de Planos v4.0 | Sidebar Renovado")