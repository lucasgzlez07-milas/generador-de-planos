import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import qrcode
from PIL import Image

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
            is_left, is_top, sep = p.x < (glass.width / 2), p.y < (glass.height / 2), 30 + (i * 22)
            h_line, y_cont, y_lab = (py_v if is_top else (h_vis - py_v)), ("bottom: 50%;" if is_top else "top: 50%;"), ("top: -24px;" if is_top else "bottom: -24px;")
            w_line, x_cont, x_trans, x_lab = (px_v if is_left else (w_vis - px_v)), ("right: 50%;" if is_left else "left: 50%;"), ("translateX(-100%)" if is_left else "translateX(100%)"), ("left: -10px;" if is_left else "right: -10px;")
            html_perf += f'<div style="position: absolute; left: {px_v-pd_v/2}px; top: {py_v-pd_v/2}px; width: {pd_v}px; height: {pd_v}px; z-index: {60-i}; background: white; border: 2px solid #ef4444; border-radius: 50%; display: flex; justify-content: center; align-items: center;"><div style="width: 1px; height: 100%; background: #ef4444; position: absolute; opacity: 0.5;"></div><div style="height: 1px; width: 100%; background: #ef4444; position: absolute; opacity: 0.5;"></div><div style="position: absolute; {y_cont} left: 50%; width: 1px; height: {h_line + sep}px; border-left: 1px dashed #ef4444;"><span style="position: absolute; {y_lab} left: 50%; transform: translateX(-50%); color: #ef4444; font-size: 10px; font-weight: 800; background: white; padding: 2px 6px; border: 1px solid #ef4444; border-radius: 4px;">{p.y}</span></div><div style="position: absolute; {x_cont} top: 50%; height: 1px; width: {w_line + sep + 40}px; border-top: 1px dashed #ef4444;"><span style="position: absolute; {x_lab} top: 50%; transform: translateY(-50%) {x_trans}; color: #ef4444; font-size: 10px; font-weight: 800; background: white; padding: 2px 6px; border: 1px solid #ef4444; border-radius: 4px;">{p.x}</span></div></div>'
        return f'<div class="canvas-container"><div class="pieza-base {css_class}" style="width: {w_vis}px; height: {h_vis}px; --color-pieza: {glass.color};">{html_perf}<div class="etiqueta-medida etiqueta-ancho">{glass.width} mm</div><div class="etiqueta-medida etiqueta-alto">{glass.height} mm</div></div></div>'

# ==========================================
# 3. UTILS
# ==========================================

def generate_qr_code(url: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ==========================================
# 4. MAIN APPLICATION
# ==========================================

def reset_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def main():
    st.set_page_config(page_title="Generador de Plano Estandarizado", layout="wide")
    CSSService.inject_styles()
    
    st.markdown('<h1 class="main-title">📐 Generador de Plano <span style="color:#3b82f6;">Estandarizado</span></h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b; margin-top:-10px;">Configuración técnica y visualización de perforaciones en tiempo real</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configuración")
        
        with st.expander("🗂️ Datos del Proyecto", expanded=True):
            client_name = st.text_input("Solicitante", key="cliente_input", placeholder="Nombre o Razón Social")
            reference = st.text_input("Referencia / Obra", key="obra_input", placeholder="Ej. Edificio Alvear - Piso 3")
        
        with st.expander("📏 Medidas y Espesor", expanded=False):
            presets = {"Personalizado": (1200, 800), "Puerta": (900, 2100), "Ventana": (1200, 1200), "Mampara": (800, 1800)}
            preset_selection = st.selectbox("Seleccionar Tipo", list(presets.keys()))
            w_def, h_def = presets[preset_selection]
            width = st.number_input("Ancho (mm)", 1, 2300, value=w_def, step=10, key="width_val")
            height = st.number_input("Alto (mm)", 1, 2300, value=h_def, step=10, key="height_val")
            st.divider()
            
            # --- MODIFICACIÓN SOLICITADA AQUÍ ---
            thickness_opts = {
                "4 mm": 4, 
                "5 mm": 5, 
                "6 mm": 6, 
                "8 mm": 8, 
                "10 mm": 10
            }
            # -------------------------------------
            
            thickness_name = st.selectbox("Espesor", list(thickness_opts.keys()), index=2, key="thickness_key") # index=2 apunta a 6mm por defecto
            thickness_val = thickness_opts[thickness_name]
            
            area = (width * height) / 1_000_000
            peso = area * thickness_val * 2.5
            c1, c2 = st.columns(2)
            c1.metric("Superficie", f"{round(area, 2)} m²")
            c2.metric("Peso", f"{round(peso, 1)} kg")

        perforations_list = []
        with st.expander("🔘 Perforaciones", expanded=False):
            qty_perf = st.number_input("Cantidad de orificios", 0, 50, key="qty_key")
            for i in range(int(qty_perf)):
                st.markdown(f"**📍 Orificio #{i+1}**")
                c1, c2, c3 = st.columns(3)
                px = c1.number_input(f"X (mm)", 0, width, 100 + (i*50), key=f"px{i}")
                py = c2.number_input(f"Y (mm)", 0, height, 100 + (i*50), key=f"py{i}")
                pd = c3.number_input(f"Ø (mm)", 1, 200, 50, key=f"pd{i}")
                perforations_list.append(Perforation(i+1, px, py, pd))
                if i < int(qty_perf) - 1:
                    st.divider()

        with st.expander("🎨 Estilo Visual", expanded=False):
            style_label = st.radio("Modo de visualización", [s.value for s in VisualStyle], horizontal=True, key="style_key")
            color = st.color_picker("Color de la pieza", "#1E3A8A", key="color_key")

        st.divider()
        if st.button("🗑️ Resetear Ficha", type="secondary", use_container_width=True):
            reset_state()
            
        st.markdown("### 📲 Compartir App")
        app_url = "https://001-generador-planos.streamlit.app/"
        qr_img = generate_qr_code(app_url)
        st.image(qr_img, caption="Escanea para trabajar desde el celular", use_container_width=True)

    # Lógica de renderizado
    project_meta = ProjectMetadata(client=client_name, reference=reference)
    glass_specs = GlassSpecifications(width, height, thickness_name, thickness_val, perforations_list, VisualStyle(style_label), color)

    col_canvas, col_details = st.columns([3, 1], gap="medium")
    with col_canvas:
        st.markdown(HTMLRenderer.render_canvas(glass_specs), unsafe_allow_html=True)
    with col_details:
        st.markdown("### 📋 Ficha Técnica")
        st.markdown(f'''<div class="metric-card" style="border-left: 5px solid {color};"><small>Medidas</small><h2>{width}x{height}</h2><small style="color: #64748b;">Solicitante: {client_name or "---"}</small><br><small style="color: #64748b;">Obra: {reference or "---"}</small><br><hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;"><small style="color: #64748b;">Espesor: <b>{thickness_name}</b></small><br><small style="color: #64748b;">Peso: <b>{round(peso, 1)} kg</b></small></div>''', unsafe_allow_html=True)
        pdf_bytes = PDFService.generate(project_meta, glass_specs)
        st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name=f"plano_{client_name or 'sin_nombre'}.pdf", mime="application/pdf", use_container_width=True)

if __name__ == "__main__":
    main()