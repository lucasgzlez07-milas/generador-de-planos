import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor # Importante para usar los colores exactos de la web

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

# 6. Función PDF REINGENIERIZADA (Visualización "Gemela")
def create_pdf(ancho_mm, alto_mm, perforaciones, color_hex, tipo, n_perf):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Colores CSS exactos traducidos a ReportLab
    rojo_css = HexColor('#ef4444')
    borde_oscuro = HexColor('#0f172a')
    color_pieza = HexColor(color_hex)
    
    # 1. Marco de la Página
    margen_marco = 20
    c.setStrokeColor(colors.black)
    c.setLineWidth(3)
    c.rect(margen_marco, margen_marco, width - (2*margen_marco), height - (2*margen_marco))
    
    # 2. Encabezado
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height - 70, "PLANO ESTANDARIZADO")
    c.setLineWidth(1)
    c.line(margen_marco, height - 90, width - margen_marco, height - 90)

    # 3. Lógica de Escala
    margen = 100
    scale = min((width - margen*2) / ancho_mm, (height - 350) / alto_mm)
    start_x = (width - (ancho_mm * scale)) / 2
    start_y = height - 200 - (alto_mm * scale)

    # 4. Dibujo de la Pieza (Estilo Web)
    if tipo == "Sólida":
        # Relleno de color + Borde fino oscuro (Igual a .modo-solido)
        c.setFillColor(color_pieza)
        c.setStrokeColor(borde_oscuro)
        c.setLineWidth(2) # Grosor del borde sólido en CSS
        c.rect(start_x, start_y, ancho_mm * scale, alto_mm * scale, fill=1, stroke=1)
    else:
        # Sin relleno + Borde grueso del color (Igual a .modo-contorno)
        c.setStrokeColor(color_pieza)
        c.setLineWidth(4) # Grosor del borde contorno en CSS
        c.rect(start_x, start_y, ancho_mm * scale, alto_mm * scale, fill=0, stroke=1)

    # 5. Dibujo de Perforaciones (Estilo Web)
    for i, p in enumerate(perforaciones):
        cx = start_x + (p["x"] * scale)
        cy = (start_y + (alto_mm * scale)) - (p["y"] * scale)
        radio = (p["diam"] / 2) * scale
        
        # Círculo blanco con borde rojo
        c.setFillColor(colors.white)
        c.setStrokeColor(rojo_css)
        c.setLineWidth(2) # Borde del círculo
        c.circle(cx, cy, radio, fill=1, stroke=1)
        
        # Cruces internas (Mirilla)
        c.setLineWidth(1)
        c.setStrokeColor(rojo_css) # Rojo semitransparente visualmente es rojo fino aquí
        c.line(cx - radio, cy, cx + radio, cy) # Horizontal
        c.line(cx, cy - radio, cx, cy + radio) # Vertical
        
        # Líneas de cotas punteadas (Rojas)
        c.setDash(3, 3) # Efecto dashed
        c.setStrokeColor(rojo_css)
        
        # Línea hacia borde Y (Arriba/Abajo)
        if p["y"] < alto_mm/2: # Cota hacia abajo
             c.line(cx, cy - radio, cx, start_y)
        else: # Cota hacia arriba
             c.line(cx, cy + radio, cx, start_y + alto_mm*scale)
             
        # Línea hacia borde X (Izq/Der)
        if p["x"] < ancho_mm/2: # Cota hacia izq
            c.line(cx - radio, cy, start_x, cy)
        else: # Cota hacia der
            c.line(cx + radio, cy, start_x + ancho_mm*scale, cy)
            
        c.setDash() # Reset dash
        
        # Etiquetas de coordenadas (Texto rojo pequeño)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(rojo_css)
        # Dibujamos un pequeño fondo blanco para que el texto se lea sobre las líneas
        label_text = f"X:{p['x']} Y:{p['y']}"
        text_width = c.stringWidth(label_text, "Helvetica-Bold", 8)
        
        c.setFillColor(colors.white)
        c.rect(cx + 2, cy + 2, text_width + 2, 10, fill=1, stroke=0) # Fondo etiqueta
        c.setFillColor(rojo_css)
        c.drawString(cx + 3, cy + 4, label_text)

    # 6. Cotas Generales (Estilo Web)
    # Etiqueta Ancho (Abajo)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black) # Color texto general #1e293b (aprox negro)
    
    # Caja fondo etiqueta ancho
    ancho_txt = f"{ancho_mm} mm"
    w_txt = c.stringWidth(ancho_txt, "Helvetica-Bold", 12)
    # Dibujamos "caja" simulando el estilo de la web
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.roundRect(width/2 - w_txt/2 - 10, start_y - 40, w_txt + 20, 20, 4, fill=0, stroke=1)
    c.drawCentredString(width/2, start_y - 34, ancho_txt)
    
    # Etiqueta Alto (Izquierda rotada)
    c.saveState()
    # Posicionamos al centro izquierda
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
    st.download_button(label="📥 Descargar Plano PDF", data=pdf_file, file_name="plano_visual.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.caption("🚀 Generador de Planos v3.8 | PDF Gemelo a la App")