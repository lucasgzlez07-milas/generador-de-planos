import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# 1. Configuración de la página
st.set_page_config(page_title="Generador de Plano Estandarizado", layout="wide")

# ==========================================
# 2. ESTILO CSS (Modificado para subir todo al máximo)
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        /* AJUSTE CLAVE: Reducir padding superior al mínimo y subir el bloque */
        .block-container { 
            padding-top: 0.5rem; 
            padding-bottom: 1rem;
            margin-top: -40px; /* Margen negativo para subir contra el header */
        }
        
        .canvas-container {
            background-color: #f8f9fa;
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
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.02);
        }

        /* AJUSTE CLAVE: Eliminar margen superior del título */
        .main-title { 
            font-weight: 800; 
            letter-spacing: -1px; 
            color: #1e293b; 
            margin-bottom: 0px; 
            margin-top: 0px !important;
            padding-top: 0px;
        }
        
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

        /* Etiquetas de Medida */
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

st.markdown('<h1 class="main-title">📐 Generador de Plano <span style="color:#3b82f6;">Estandarizado</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748b; margin-top:-5px;">Configuración técnica y visualización de perforaciones en tiempo real</p>', unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2312/2312444.png", width=80)
    st.header("Dimensiones Base")
    val_ancho = st.number_input("Ancho Total (mm)", 1, 5000, 1200, 10, key="ancho_input")
    val_alto = st.number_input("Alto Total (mm)", 1, 5000, 800, 10, key="alto_input")
    
    st.divider()
    st.header("Configurar Perforaciones")
    num_perf = st.number_input("Cantidad de orificios", 0, 20, 1, key="num_perf_input")
    
    lista_perforaciones = []
    for i in range(int(num_perf)):
        with st.expander(f"📍 Perforación #{i+1}", expanded=(i == num_perf-1)):
            c1, c2 = st.columns(2)
            px = c1.number_input(f"X (mm)", 0, val_ancho, 100 + (i*150), key=f"x{i}")
            py = c2.number_input(f"Y (mm)", 0, val_alto, 100 + (i*150), key=f"y{i}")
            pd = st.number_input(f"Diámetro Ø (mm)", 1, val_ancho, 50, key=f"d{i}")
            lista_perforaciones.append({"id": i+1, "x": px, "y": py, "diam": pd})
    
    st.divider()
    st.header("Apariencia")
    tipo_fig = st.select_slider("Estilo de Plano", options=["Solo Contorno", "Sólida"])
    color_p = st.color_picker("Color de la pieza", "#1E3A8A")

# 4. Lógica Backend
esc = 0.20 
w_vis = val_ancho * esc
h_vis = val_alto * esc

# Lógica de apariencia (Control manual por slider)
if tipo_fig == "Sólida":
    clase_visual = "modo-solido"
else:
    clase_visual = "modo-contorno"

# Construcción del HTML (Minificado)
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
    c.setStrokeColorRGB(0.9, 0.9, 0.9)
    for x in range(0, int(width), 20): c.line(x, 0, x, height)
    for y in range(0, int(height), 20): c.line(0, y, width, y)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.black)
    c.drawString(50, height - 50, "PLANO TÉCNICO DE FABRICACIÓN")
    margen = 100
    scale = min((width - margen*2) / ancho_mm, (height - 300) / alto_mm)
    start_x = (width - (ancho_mm * scale)) / 2
    start_y = height - 150 - (alto_mm * scale)

    if tipo == "Sólida":
        c.setFillColor(color_hex)
        c.rect(start_x, start_y, ancho_mm * scale, alto_mm * scale, fill=1, stroke=1)
    else:
        c.setStrokeColor(color_hex)
        c.setLineWidth(2)
        c.rect(start_x, start_y, ancho_mm * scale, alto_mm * scale, fill=0, stroke=1)

    for i, p in enumerate(perforaciones):
        cx = start_x + (p["x"] * scale)
        cy = (start_y + (alto_mm * scale)) - (p["y"] * scale)
        radio = (p["diam"] / 2) * scale
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.red)
        c.setLineWidth(1)
        c.circle(cx, cy, radio, fill=1, stroke=1)
        c.setDash(3, 3)
        c.setStrokeColor(colors.red)
        c.line(cx, cy, cx, cy + (p["y"] * scale if p["y"] < alto_mm/2 else -(alto_mm - p["y"]) * scale))
        c.line(cx, cy, cx + (p["x"] * scale if p["x"] < ancho_mm/2 else -(ancho_mm - p["x"]) * scale), cy)
        c.setDash()
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.red)
        c.drawString(cx + 2, cy + 2, f"X:{p['x']} Y:{p['y']}")

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, start_y - 20, f"ANCHO: {ancho_mm} mm")
    c.saveState()
    c.translate(start_x - 20, start_y + (alto_mm*scale)/2)
    c.rotate(90)
    c.drawCentredString(0, 0, f"ALTO: {alto_mm} mm")
    c.restoreState()
    c.save()
    buffer.seek(0)
    return buffer

with col_ficha:
    st.markdown("### 📋 Ficha Técnica")
    st.markdown(f'<div class="metric-card" style="border-left: 5px solid {color_p};"><small>Medidas</small><h2>{val_ancho}x{val_alto}</h2></div>', unsafe_allow_html=True)
    pdf_file = create_pdf(val_ancho, val_alto, lista_perforaciones, color_p, tipo_fig, num_perf)
    st.download_button(label="📥 Descargar Plano PDF", data=pdf_file, file_name="plano_visual.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.caption("🚀 Generador de Planos v3.3 | Diseño Compacto")