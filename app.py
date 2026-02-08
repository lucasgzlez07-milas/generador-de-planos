import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# ==========================================
# 1. DOMAIN MODELS (Estructura de Datos)
# ==========================================

class VisualStyle(Enum):
    CONTORNO = "Solo Contorno"
    SOLIDO = "Sólida"

@dataclass
class Perforation:
    id: int
    x: float
    y: float
    diameter: float

@dataclass
class ProjectMetadata:
    client: str
    reference: str

@dataclass
class GlassSpecifications:
    width: float
    height: float
    thickness_name: str
    thickness_value: float
    perforations: List[Perforation] = field(default_factory=list)
    style: VisualStyle = VisualStyle.CONTORNO
    color: str = "#1E3A8A"

    @property
    def area_m2(self) -> float:
        return (self.width * self.height) / 1_000_000

    @property
    def weight_kg(self) -> float:
        return self.area_m2 * self.thickness_value * 2.5

# ==========================================
# 2. SERVICES (Lógica de Negocio y UI)
# ==========================================

class CSSService:
    @staticmethod
    def inject_styles():
        st.markdown("""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
                html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
                
                .stApp {
                    background-image: linear-gradient(rgba(255, 255, 255, 0.70), rgba(255, 255, 255, 0.70)),
                    url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2670&auto=format&fit=crop');
                    background-size: cover; background-attachment: fixed; background-position: center center;
                }
                .block-container { padding-top: 1rem; padding-bottom: 1rem; }
                
                .canvas-container {
                    background-color: #ffffff;
                    background-image: radial-gradient(#d1d5db 1px, transparent 1px);
                    background-size: 20px 20px;
                    border: 1px solid #e5e7eb; border-radius: 20px;
                    display: flex; justify-content: center; align-items: center;
                    position: relative; padding: 80px; min-height: 750px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }
                .main-title { font-weight: 800; letter-spacing: -1px; color: #1e293b; margin: 0; }
                
                .metric-card {
                    background: #ffffff; border-radius: 15px; padding: 20px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #f0f2f6; margin-bottom: 15px;
                }
                
                .pieza-base { position: relative; transition: all 0.3s ease; }
                .modo-solido { background-color: var(--color-pieza); border: 2px solid #0f172a; box-shadow: 0 10px 30px rgba(0,0,0,0.15); }
                .modo-contorno { background-color: rgba(255,255,255,0.5); border: 4px solid var(--color-pieza); }
                
                .etiqueta-medida {
                    position: absolute; font-weight: 800; color: #1e293b; font-size: 14px;
                    background: #f8f9fa; padding: 5px 15px; border: 2px solid #1e293b;
                    border-radius: 5px; white-space: nowrap; z-index: 10; pointer-events: none;
                }
                .etiqueta-ancho { bottom: -50px; left: 50%; transform: translateX(-50%); }
                .etiqueta-alto { left: -80px; top: 50%; transform: translateY(-50%) rotate(-90deg); transform-origin: center; }
            </style>
        """, unsafe_allow_html=True)

class PDFService:
    @staticmethod
    def generate(project: ProjectMetadata, glass: GlassSpecifications) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width_a4, height_a4 = A4
        
        NEGRO = colors.black
        BLANCO = colors.white
        MARGIN = 20
        
        # Marco
        c.setStrokeColor(NEGRO)
        c.setLineWidth(3)
        c.rect(MARGIN, MARGIN, width_a4 - 2*MARGIN, height_a4 - 2*MARGIN)
        
        # Encabezado
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(NEGRO)
        c.drawCentredString(width_a4/2, height_a4 - 60, "PLANO ESTANDARIZADO")
        c.setLineWidth(1)
        c.line(MARGIN, height_a4 - 80, width_a4 - MARGIN, height_a4 - 80)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 15, height_a4 - 105, f"SOLICITANTE: {project.client or '---'}")
        c.drawString(MARGIN + 15, height_a4 - 120, f"OBRA: {project.reference or '---'}")
        
        c.drawRightString(width_a4 - MARGIN - 15, height_a4 - 105, f"ESPESOR: {glass.thickness_name}")
        c.drawRightString(width_a4 - MARGIN - 15, height_a4 - 120, f"PESO: {round(glass.weight_kg, 1)} kg")
        
        c.line(MARGIN, height_a4 - 130, width_a4 - MARGIN, height_a4 - 130)

        # Escala
        draw_margin = 100
        available_w = width_a4 - draw_margin * 2
        available_h = height_a4 - 400
        scale = min(available_w / glass.width, available_h / glass.height)
        
        start_x = (width_a4 - (glass.width * scale)) / 2
        start_y = height_a4 - 250 - (glass.height * scale)

        # Pieza
        if glass.style == VisualStyle.SOLIDO:
            c.setFillColor(colors.lightgrey) 
            c.setStrokeColor(NEGRO)
            c.setLineWidth(2)
            c.rect(start_x, start_y, glass.width * scale, glass.height * scale, fill=1, stroke=1)
        else:
            c.setStrokeColor(NEGRO)
            c.setLineWidth(3)
            c.rect(start_x, start_y, glass.width * scale, glass.height * scale, fill=0, stroke=1)

        # Perforaciones
        for p in glass.perforations:
            cx = start_x + (p.x * scale)
            cy = (start_y + (glass.height * scale)) - (p.y * scale)
            r = (p.diameter / 2) * scale
            
            c.setFillColor(BLANCO)
            c.setStrokeColor(NEGRO)
            c.setLineWidth(1.5)
            c.circle(cx, cy, r, fill=1, stroke=1)
            
            c.setLineWidth(0.5)
            c.line(cx - r + 2, cy, cx + r - 2, cy)
            c.line(cx, cy - r + 2, cx, cy + r - 2)
            
            c.setDash(2, 2)
            c.setStrokeColor(NEGRO)
            
            # Cota Y
            is_top_half = p.y >= glass.height / 2
            line_y_endpoint = start_y + (glass.height * scale) if not is_top_half else start_y
            
            if not is_top_half: 
                 c.line(cx, cy - r, cx, line_y_endpoint)
                 label_y_pos = (cy - r + line_y_endpoint) / 2
            else: 
                 c.line(cx, cy + r, cx, line_y_endpoint)
                 label_y_pos = (cy + r + line_y_endpoint) / 2

            c.setDash()
            PDFService._draw_label(c, str(p.y), cx, label_y_pos)
            c.setDash(2, 2)

            # Cota X
            is_left_half = p.x < glass.width / 2
            line_x_endpoint = start_x if is_left_half else start_x + (glass.width * scale)
            
            if is_left_half:
                 c.line(cx - r, cy, line_x_endpoint, cy)
                 label_x_pos = (cx - r + line_x_endpoint) / 2
            else:
                 c.line(cx + r, cy, line_x_endpoint, cy)
                 label_x_pos = (cx + r + line_x_endpoint) / 2
            
            c.setDash()
            PDFService._draw_label(c, str(p.x), label_x_pos, cy)

        # Cotas Generales
        c.setDash()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(NEGRO)
        
        # Ancho
        ancho_txt = f"{glass.width} mm"
        w_txt = c.stringWidth(ancho_txt, "Helvetica-Bold", 12)
        c.roundRect(width_a4/2 - w_txt/2 - 10, start_y - 40, w_txt + 20, 20, 4, fill=0, stroke=1)
        c.drawCentredString(width_a4/2, start_y - 34, ancho_txt)
        
        # Alto
        c.saveState()
        c.translate(start_x - 40, start_y + (glass.height * scale)/2)
        c.rotate(90)
        alto_txt = f"{glass.height} mm"
        w_txt_h = c.stringWidth(alto_txt, "Helvetica-Bold", 12)
        c.roundRect(-w_txt_h/2 - 10, -10, w_txt_h + 20, 20, 4, fill=0, stroke=1)
        c.drawCentredString(0, -4, alto_txt)
        c.restoreState()

        c.save()
        buffer.seek(0)
        return buffer

    @staticmethod
    def _draw_label(c, text, x, y):
        c.setFont("Helvetica-Bold", 8)
        w = c.stringWidth(text, "Helvetica-Bold", 8)
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(x - w/2 - 2, y - 4, w + 4, 8, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawCentredString(x, y - 2.5, text)

class HTMLRenderer:
    @staticmethod
    def render_canvas(glass: GlassSpecifications) -> str:
        scale = 0.20
        w_vis = glass.width * scale
        h_vis = glass.height * scale
        css_class = "modo-solido" if glass.style == VisualStyle.SOLIDO else "modo-contorno"
        
        html_perf = ""
        for i, p in enumerate(glass.perforations):
            px_v, py_v, pd_v = p.x * scale, p.y * scale, p.diameter * scale
            is_left = p.x < (glass.width / 2)
            is_top = p.y < (glass.height / 2)
            sep = 30 + (i * 22)
            
            left_pos = px_v - (pd_v/2)
            top_pos = py_v - (pd_v/2)
            
            h_line = py_v if is_top else (h_vis - py_v)
            y_container = "bottom: 50%;" if is_top else "top: 50%;"
            y_label_pos = "top: -24px;" if is_top else "bottom: -24px;"
            
            html_cota_y = f"""<div style="position: absolute; {y_container} left: 50%; width: 1px; height: {h_line + sep}px; border-left: 1px dashed #ef4444;"><span style="position: absolute; {y_label_pos} left: 50%; transform: translateX(-50%); color: #ef4444; font-size: 10px; font-weight: 800; background: white; padding: 2px 6px; border: 1px solid #ef4444; border-radius: 4px;">{p.y}</span></div>"""

            w_line = px_v if is_left else (w_vis - px_v)
            x_container = "right: 50%;" if is_left else "left: 50%;"
            x_trans = "translateX(-100%)" if is_left else "translateX(100%)"
            x_label_pos = "left: -10px;" if is_left else "right: -10px;"
            
            html_cota_x = f"""<div style="position: absolute; {x_container} top: 50%; height: 1px; width: {w_line + sep + 40}px; border-top: 1px dashed #ef4444;"><span style="position: absolute; {x_label_pos} top: 50%; transform: translateY(-50%) {x_trans}; color: #ef4444; font-size: 10px; font-weight: 800; background: white; padding: 2px 6px; border: 1px solid #ef4444; border-radius: 4px;">{p.x}</span></div>"""
            
            html_perf += f"""<div style="position: absolute; left: {left_pos}px; top: {top_pos}px; width: {pd_v}px; height: {pd_v}px; z-index: {60-i}; background: white; border: 2px solid #ef4444; border-radius: 50%; display: flex; justify-content: center; align-items: center;"><div style="width: 1px; height: 100%; background: #ef4444; position: absolute; opacity: 0.5;"></div><div style="height: 1px; width: 100%; background: #ef4444; position: absolute; opacity: 0.5;"></div>{html_cota_y}{html_cota_x}</div>"""

        return f"""<div class="canvas-container"><div class="pieza-base {css_class}" style="width: {w_vis}px; height: {h_vis}px; --color-pieza: {glass.color};">{html_perf}<div class="etiqueta-medida etiqueta-ancho">{glass.width} mm</div><div class="etiqueta-medida etiqueta-alto">{glass.height} mm</div></div></div>""".replace("\n", "")

# ==========================================
# 3. MAIN APPLICATION CONTROLLER
# ==========================================

def init_session():
    if "ancho_input" not in st.session_state:
        reset_state()

def reset_state():
    st.session_state.cliente_input = ""
    st.session_state.obra_input = ""
    st.session_state.ancho_input = 1200
    st.session_state.alto_input = 800
    st.session_state.num_perf_input = 0

def main():
    st.set_page_config(page_title="Generador de Plano Estandarizado", layout="wide")
    CSSService.inject_styles()
    init_session()

    st.markdown('<h1 class="main-title">📐 Generador de Plano <span style="color:#3b82f6;">Estandarizado</span></h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b; margin-top:-10px;">Configuración técnica y visualización de perforaciones en tiempo real</p>', unsafe_allow_html=True)

    # Inicialización de la lista de perforaciones (CORRECCIÓN NameError)
    perforations_list = []

    with st.sidebar:
        st.header("🗂️ Datos del Proyecto")
        client_name = st.text_input("Solicitante", key="cliente_input", placeholder="Nombre o Razón Social")
        reference = st.text_input("Referencia / Obra", key="obra_input", placeholder="Ej. Edificio Alvear - Piso 3")
        project_meta = ProjectMetadata(client=client_name, reference=reference)

        st.divider()
        tab_dim, tab_perf, tab_style = st.tabs(["📏 Medidas", "🔘 Perforaciones", "🎨 Estilo"])
        
        with tab_dim:
            presets = {"Personalizado": (1200, 800), "Puerta Estándar (2100x900)": (900, 2100), "Hoja Ventana (1200x1200)": (1200, 1200), "Mampara Baño (1800x800)": (800, 1800)}
            preset_selection = st.selectbox("Seleccionar Tipo", list(presets.keys()))
            if preset_selection != "Personalizado":
                w_def, h_def = presets[preset_selection]
                width = st.number_input("Ancho (mm)", 1, 2300, value=w_def, step=10, key="ancho_preset")
                height = st.number_input("Alto (mm)", 1, 2300, value=h_def, step=10, key="alto_preset")
            else:
                width = st.number_input("Ancho (mm)", 1, 2300, key="ancho_input", step=10)
                height = st.number_input("Alto (mm)", 1, 2300, key="alto_input", step=10)
            
            st.markdown("---")
            thickness_opts = {"4 mm": 4, "5 mm": 5, "6 mm": 6, "8 mm": 8, "10 mm": 10, "12 mm": 12, "Laminado 3+3 (6mm)": 6, "Laminado 4+4 (8mm)": 8, "Laminado 5+5 (10mm)": 10}
            thickness_name = st.selectbox("Espesor del Vidrio", list(thickness_opts.keys()), index=2)
            thickness_val = thickness_opts[thickness_name]

            temp_glass = GlassSpecifications(width, height, thickness_name, thickness_val)
            c1, c2 = st.columns(2)
            c1.metric("Superficie", f"{round(temp_glass.area_m2, 2)} m²")
            c2.metric("Peso", f"{round(temp_glass.weight_kg, 1)} kg")

        with tab_perf:
            qty_perf = st.number_input("Cantidad de orificios", 0, 50, key="num_perf_input")
            if qty_perf > 0:
                st.markdown("---")
                for i in range(int(qty_perf)):
                    with st.expander(f"📍 Perforación #{i+1}", expanded=(i == 0)):
                        c1, c2, c3 = st.columns([1,1,1])
                        px = c1.number_input(f"X (mm)", 0, width, 100 + (i*150), key=f"x{i}")
                        py = c2.number_input(f"Y (mm)", 0, height, 100 + (i*150), key=f"y{i}")
                        pd = c3.number_input(f"Ø (mm)", 1, 200, 50, key=f"d{i}")
                        if px > width or px < 0: st.warning("⚠️ X fuera de rango")
                        if py > height or py < 0: st.warning("⚠️ Y fuera de rango")
                        perforations_list.append(Perforation(i+1, px, py, pd))
            else:
                st.caption("Sin perforaciones seleccionadas.")

        with tab_style:
            style_label = st.radio("Estilo de Visualización", [s.value for s in VisualStyle], horizontal=True)
            sel_style = VisualStyle(style_label)
            color = st.color_picker("Color del Vidrio", "#1E3A8A")

        st.divider()
        if st.button("🗑️ Resetear Ficha", type="secondary", use_container_width=True):
            reset_state()
            st.rerun()

    glass_specs = GlassSpecifications(width, height, thickness_name, thickness_val, perforations_list, sel_style, color)

    col_canvas, col_details = st.columns([3, 1], gap="medium")
    with col_canvas:
        st.markdown(HTMLRenderer.render_canvas(glass_specs), unsafe_allow_html=True)
    with col_details:
        st.markdown("### 📋 Ficha Técnica")
        st.markdown(f'''<div class="metric-card" style="border-left: 5px solid {color};"><small>Medidas</small><h2>{width}x{height}</h2><small style="color: #64748b;">Solicitante: {project_meta.client or "---"}</small><br><small style="color: #64748b;">Obra: {project_meta.reference or "---"}</small><br><hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;"><small style="color: #64748b;">Espesor: <b>{thickness_name}</b></small><br><small style="color: #64748b;">Peso: <b>{round(glass_specs.weight_kg, 1)} kg</b></small></div>''', unsafe_allow_html=True)
        pdf_bytes = PDFService.generate(project_meta, glass_specs)
        st.download_button(label="📥 Descargar Plano PDF", data=pdf_bytes, file_name=f"plano_{project_meta.client or 'sin_nombre'}.pdf", mime="application/pdf", use_container_width=True)

if __name__ == "__main__":
    main()