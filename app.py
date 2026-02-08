import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# ==========================================
# 1. DOMAIN MODELS
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
# 2. SERVICES
# ==========================================

class CSSService:
    @staticmethod
    def inject_styles():
        st.markdown("""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Roboto+Mono:wght@400;700&display=swap');
                
                html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
                
                .stApp {
                    background-color: #f8fafc;
                    background-image: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)),
                    url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2670&auto=format&fit=crop');
                    background-size: cover; background-attachment: fixed;
                }

                /* MEJORA 1: Estilo Blueprint para el Canvas */
                .canvas-container {
                    background-color: #0f172a; /* Azul Marino Profundo */
                    background-image: 
                        linear-gradient(rgba(30, 58, 138, 0.5) 1px, transparent 1px),
                        linear-gradient(90, rgba(30, 58, 138, 0.5) 1px, transparent 1px);
                    background-size: 20px 20px;
                    border: 2px solid #334155;
                    border-radius: 12px;
                    display: flex; justify-content: center; align-items: center;
                    position: relative; padding: 100px; min-height: 750px;
                    box-shadow: inset 0 0 50px rgba(0,0,0,0.5), 0 10px 30px rgba(0,0,0,0.3);
                }

                .main-title { font-weight: 800; letter-spacing: -1px; color: #1e293b; margin: 0; }
                
                .metric-card {
                    background: #ffffff; border-radius: 12px; padding: 20px;
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-bottom: 15px;
                }

                /* Pieza en modo Blueprint */
                .pieza-base { position: relative; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
                
                .modo-solido { 
                    background-color: rgba(59, 130, 246, 0.2); 
                    border: 2px solid #60a5fa; 
                    box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
                }
                
                .modo-contorno { 
                    background-color: transparent; 
                    border: 2px solid #ffffff; 
                }

                /* Etiquetas técnicas estilo CAD */
                .etiqueta-medida {
                    position: absolute; font-family: 'Roboto Mono', monospace; font-weight: 700; 
                    color: #ffffff; font-size: 13px;
                    background: #2563eb; padding: 4px 10px; border-radius: 4px;
                    white-space: nowrap; z-index: 10;
                }
                .etiqueta-ancho { bottom: -45px; left: 50%; transform: translateX(-50%); }
                .etiqueta-alto { left: -75px; top: 50%; transform: translateY(-50%) rotate(-90deg); }

            </style>
        """, unsafe_allow_html=True)

class PDFService:
    @staticmethod
    def generate(project: ProjectMetadata, glass: GlassSpecifications) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width_a4, height_a4 = A4
        NEGRO, BLANCO, MARGIN = colors.black, colors.white, 20
        c.setStrokeColor(NEGRO); c.setLineWidth(3)
        c.rect(MARGIN, MARGIN, width_a4 - 2*MARGIN, height_a4 - 2*MARGIN)
        c.setFont("Helvetica-Bold", 22); c.setFillColor(NEGRO)
        c.drawCentredString(width_a4/2, height_a4 - 60, "PLANO ESTANDARIZADO")
        c.setLineWidth(1); c.line(MARGIN, height_a4 - 80, width_a4 - MARGIN, height_a4 - 80)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 15, height_a4 - 105, f"SOLICITANTE: {project.client or '---'}")
        c.drawString(MARGIN + 15, height_a4 - 120, f"OBRA: {project.reference or '---'}")
        c.drawRightString(width_a4 - MARGIN - 15, height_a4 - 105, f"ESPESOR: {glass.thickness_name}")
        c.drawRightString(width_a4 - MARGIN - 15, height_a4 - 120, f"PESO: {round(glass.weight_kg, 1)} kg")
        c.line(MARGIN, height_a4 - 130, width_a4 - MARGIN, height_a4 - 130)
        scale = min((width_a4 - 200) / glass.width, (height_a4 - 400) / glass.height)
        start_x, start_y = (width_a4 - (glass.width * scale)) / 2, height_a4 - 250 - (glass.height * scale)
        if glass.style == VisualStyle.SOLIDO:
            c.setFillColor(colors.lightgrey); c.rect(start_x, start_y, glass.width * scale, glass.height * scale, fill=1, stroke=1)
        else:
            c.setStrokeColor(NEGRO); c.setLineWidth(3); c.rect(start_x, start_y, glass.width * scale, glass.height * scale, fill=0, stroke=1)
        for p in glass.perforations:
            cx, cy, r = start_x + (p.x * scale), (start_y + (glass.height * scale)) - (p.y * scale), (p.diameter / 2) * scale
            c.setFillColor(BLANCO); c.setStrokeColor(NEGRO); c.setLineWidth(1.5); c.circle(cx, cy, r, fill=1, stroke=1)
            c.setLineWidth(0.5); c.line(cx - r + 2, cy, cx + r - 2, cy); c.line(cx, cy - r + 2, cx, cy + r - 2)
            c.setDash(2, 2)
            y_end = start_y + (glass.height * scale) if p.y < glass.height/2 else start_y
            c.line(cx, cy + (r if p.y < glass.height/2 else -r), cx, y_end)
            x_end = start_x if p.x < glass.width/2 else start_x + (glass.width * scale)
            c.line(cx + (-r if p.x < glass.width/2 else r), cy, x_end, cy)
            c.setDash()
            PDFService._draw_label(c, str(p.y), cx, (cy + (r if p.y < glass.height/2 else -r) + y_end)/2)
            PDFService._draw_label(c, str(p.x), (cx + (-r if p.x < glass.width/2 else r) + x_end)/2, cy)
        c.setFont("Helvetica-Bold", 12)
        ancho_txt = f"{glass.width} mm"
        w_txt = c.stringWidth(ancho_txt, "Helvetica-Bold", 12)
        c.roundRect(width_a4/2 - w_txt/2 - 10, start_y - 40, w_txt + 20, 20, 4, fill=0, stroke=1)
        c.drawCentredString(width_a4/2, start_y - 34, ancho_txt)
        c.saveState(); c.translate(start_x - 40, start_y + (glass.height * scale)/2); c.rotate(90)
        alto_txt = f"{glass.height} mm"; w_txt_h = c.stringWidth(alto_txt, "Helvetica-Bold", 12)
        c.roundRect(-w_txt_h/2 - 10, -10, w_txt_h + 20, 20, 4, fill=0, stroke=1); c.drawCentredString(0, -4, alto_txt); c.restoreState()
        c.save(); buffer.seek(0)
        return buffer

    @staticmethod
    def _draw_label(c, text, x, y):
        c.setFont("Helvetica-Bold", 8); w = c.stringWidth(text, "Helvetica-Bold", 8)
        c.setFillColor(colors.white); c.setStrokeColor(colors.black); c.setLineWidth(0.5)
        c.rect(x - w/2 - 2, y - 4, w + 4, 8, fill=1, stroke=1)
        c.setFillColor(colors.black); c.drawCentredString(x, y - 2.5, text)

class HTMLRenderer:
    @staticmethod
    def render_canvas(glass: GlassSpecifications) -> str:
        scale = 0.20
        w_vis, h_vis = glass.width * scale, glass.height * scale
        css_class = "modo-solido" if glass.style == VisualStyle.SOLIDO else "modo-contorno"
        html_perf = ""
        for i, p in enumerate(glass.perforations):
            px_v, py_v, pd_v = p.x * scale, p.y * scale, p.diameter * scale
            is_left, is_top, sep = p.x < (glass.width / 2), p.y < (glass.height / 2), 35 + (i * 25)
            h_line, y_cont, y_lab = (py_v if is_top else (h_vis - py_v)), ("bottom: 50%;" if is_top else "top: 50%;"), ("top: -24px;" if is_top else "bottom: -24px;")
            w_line, x_cont, x_trans, x_lab = (px_v if is_left else (w_vis - px_v)), ("right: 50%;" if is_left else "left: 50%;"), ("translateX(-100%)" if is_left else "translateX(100%)"), ("left: -10px;" if is_left else "right: -10px;")
            
            # Color Neon para cotas Blueprint
            color_cota = "#38bdf8" 
            
            html_perf += f"""
                <div style="position: absolute; left: {px_v-pd_v/2}px; top: {py_v-pd_v/2}px; width: {pd_v}px; height: {pd_v}px; z-index: {60-i}; background: rgba(255,255,255,0.9); border: 2px solid #ffffff; border-radius: 50%; display: flex; justify-content: center; align-items: center; box-shadow: 0 0 10px rgba(56,189,248,0.5);">
                    <div style="width: 1px; height: 100%; background: {color_cota}; position: absolute; opacity: 0.6;"></div>
                    <div style="height: 1px; width: 100%; background: {color_cota}; position: absolute; opacity: 0.6;"></div>
                    <div style="position: absolute; {y_cont} left: 50%; width: 1px; height: {h_line + sep}px; border-left: 1px dashed {color_cota};">
                        <span style="position: absolute; {y_lab} left: 50%; transform: translateX(-50%); color: {color_cota}; font-size: 10px; font-weight: 800; background: #0f172a; padding: 2px 6px; border: 1px solid {color_cota}; border-radius: 4px; font-family: 'Roboto Mono';">
                            {p.y}
                        </span>
                    </div>
                    <div style="position: absolute; {x_cont} top: 50%; height: 1px; width: {w_line + sep + 40}px; border-top: 1px dashed {color_cota};">
                        <span style="position: absolute; {x_lab} top: 50%; transform: translateY(-50%) {x_trans}; color: {color_cota}; font-size: 10px; font-weight: 800; background: #0f172a; padding: 2px 6px; border: 1px solid {color_cota}; border-radius: 4px; font-family: 'Roboto Mono';">
                            {p.x}
                        </span>
                    </div>
                </div>"""
        return f'<div class="canvas-container"><div class="pieza-base {css_class}" style="width: {w_vis}px; height: {h_vis}px;">{html_perf}<div class="etiqueta-medida etiqueta-ancho">{glass.width} mm</div><div class="etiqueta-medida etiqueta-alto">{glass.height} mm</div></div></div>'

# ==========================================
# 3. MAIN APPLICATION
# ==========================================

def reset_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def main():
    st.set_page_config(page_title="Blueprint Glass Designer", layout="wide")
    CSSService.inject_styles()
    
    st.markdown('<h1 class="main-title">📐 Blueprint <span style="color:#3b82f6;">Glass Designer</span></h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b; margin-top:-10px;">Entorno de precisión industrial para manufactura de vidrio</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("🗂️ Datos del Proyecto")
        client_name = st.text_input("Solicitante", key="cliente_input", placeholder="Nombre o Razón Social")
        reference = st.text_input("Referencia / Obra", key="obra_input", placeholder="Ej. Edificio Alvear")
        
        st.divider()
        tab_dim, tab_perf, tab_style = st.tabs(["📏 Medidas", "🔘 Perforaciones", "🎨 Estilo"])
        
        with tab_dim:
            presets = {"Personalizado": (1200, 800), "Puerta": (900, 2100), "Ventana": (1200, 1200), "Mampara": (800, 1800)}
            preset_selection = st.selectbox("Tipo de Pieza", list(presets.keys()))
            w_def, h_def = presets[preset_selection]
            width = st.number_input("Ancho (mm)", 1, 2300, value=w_def, step=10, key="width_val")
            height = st.number_input("Alto (mm)", 1, 2300, value=h_def, step=10, key="height_val")
            st.divider()
            thickness_opts = {"4 mm": 4, "6 mm": 6, "10 mm": 10, "12 mm": 12, "Laminado 5+5": 10}
            thickness_name = st.selectbox("Espesor", list(thickness_opts.keys()), index=2, key="thickness_key")
            thickness_val = thickness_opts[thickness_name]
            area = (width * height) / 1_000_000
            peso = area * thickness_val * 2.5
            c1, c2 = st.columns(2)
            c1.metric("Área", f"{round(area, 2)} m²")
            c2.metric("Peso", f"{round(peso, 1)} kg")

        perforations_list = []
        with tab_perf:
            qty_perf = st.number_input("Cantidad orificios", 0, 50, key="qty_key")
            for i in range(int(qty_perf)):
                with st.expander(f"📍 Perforación #{i+1}"):
                    c1, c2, c3 = st.columns(3)
                    px = c1.number_input(f"X", 0, width, 100 + (i*100), key=f"px{i}")
                    py = c2.number_input(f"Y", 0, height, 100 + (i*100), key=f"py{i}")
                    pd = c3.number_input(f"Ø", 1, 200, 50, key=f"pd{i}")
                    perforations_list.append(Perforation(i+1, px, py, pd))

        with tab_style:
            style_label = st.radio("Acabado Visual", [s.value for s in VisualStyle], horizontal=True, key="style_key")
            color = st.color_picker("Tinte de Vidrio (Web)", "#1E3A8A", key="color_key")

        st.divider()
        if st.button("🗑️ Resetear Diseño", use_container_width=True):
            reset_state()

    project_meta = ProjectMetadata(client=client_name, reference=reference)
    glass_specs = GlassSpecifications(width, height, thickness_name, thickness_val, perforations_list, VisualStyle(style_label), color)

    col_canvas, col_details = st.columns([3, 1], gap="medium")
    with col_canvas:
        st.markdown(HTMLRenderer.render_canvas(glass_specs), unsafe_allow_html=True)
    with col_details:
        st.markdown("### 📋 Especificaciones")
        st.markdown(f'''<div class="metric-card" style="border-left: 5px solid #2563eb;"><small>DIMENSIONES</small><h2>{width}x{height}</h2><small>SOLICITANTE</small><br><b>{client_name or "---"}</b><br><br><small>REFERENCIA</small><br><b>{reference or "---"}</b><hr style="margin: 15px 0; border: 0; border-top: 1px solid #e2e8f0;"><small>ESPESOR</small><br><b>{thickness_name}</b><br><br><small>PESO ESTIMADO</small><br><b>{round(peso, 1)} kg</b></div>''', unsafe_allow_html=True)
        pdf_bytes = PDFService.generate(project_meta, glass_specs)
        st.download_button("📥 Exportar Plano Técnico", data=pdf_bytes, file_name=f"blueprint_{client_name or 'plano'}.pdf", mime="application/pdf", use_container_width=True)

if __name__ == "__main__":
    main()