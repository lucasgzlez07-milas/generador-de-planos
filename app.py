import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from dataclasses import dataclass, field
from typing import List
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
                @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
                
                :root { --primary-blue: #3b82f6; }
                
                .stApp {
                    background-color: #f8fafc;
                    background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
                    background-size: 30px 30px;
                }

                /* Contenedor del Plano */
                .canvas-view {
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 24px;
                    padding: 60px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
                    min-height: 650px;
                }

                /* Tarjetas de Información */
                .info-card {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 16px;
                    border: 1px solid #f1f5f9;
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                }

                .metric-label { font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
                .metric-value { font-size: 1.5rem; font-weight: 800; color: #1e293b; }

                /* Estilo de la pieza */
                .glass-piece {
                    position: relative;
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                .glass-solid { background: var(--glass-color); border: 2px solid #0f172a; box-shadow: 20px 20px 60px #d1d1d1; }
                .glass-outline { background: rgba(255,255,255,0.8); border: 3px solid var(--glass-color); }

                /* Etiquetas de Medidas */
                .dim-label {
                    position: absolute;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 12px;
                    font-weight: 700;
                    background: #1e293b;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 4px;
                }
                .dim-w { bottom: -45px; left: 50%; transform: translateX(-50%); }
                .dim-h { left: -75px; top: 50%; transform: translateY(-50%) rotate(-90deg); }
            </style>
        """, unsafe_allow_html=True)

class HTMLRenderer:
    @staticmethod
    def render(glass: GlassSpecifications) -> str:
        # Escalado dinámico para que siempre quepa en pantalla
        scale = min(500 / glass.width, 500 / glass.height) if max(glass.width, glass.height) > 0 else 0.2
        w_px, h_px = glass.width * scale, glass.height * scale
        
        style_class = "glass-solid" if glass.style == VisualStyle.SOLIDO else "glass-outline"
        
        # Render de perforaciones
        perfs_html = ""
        for p in glass.perforations:
            px, py, pd = p.x * scale, p.y * scale, p.diameter * scale
            perfs_html += f'''
                <div style="position: absolute; left: {px-pd/2}px; top: {py-pd/2}px; width: {pd}px; height: {pd}px; 
                            border: 2px solid #ef4444; border-radius: 50%; background: white; z-index: 10;">
                    <div style="position: absolute; top: 50%; width: 100%; height: 1px; background: #ef4444; opacity: 0.3;"></div>
                    <div style="position: absolute; left: 50%; height: 100%; width: 1px; background: #ef4444; opacity: 0.3;"></div>
                </div>
            '''

        return f'''
            <div class="canvas-view">
                <div class="glass-piece {style_class}" style="width: {w_px}px; height: {h_px}px; --glass-color: {glass.color};">
                    {perfs_html}
                    <div class="dim-label dim-w">{glass.width} mm</div>
                    <div class="dim-label dim-h">{glass.height} mm</div>
                </div>
            </div>
        '''

# ==========================================
# 3. MAIN APP
# ==========================================

def main():
    st.set_page_config(page_title="GlassPro | Planos", layout="wide", page_icon="📐")
    CSSService.inject_styles()

    # Header con diseño limpio
    c_title, c_meta = st.columns([2, 1])
    with c_title:
        st.markdown('<h1 style="margin-bottom:0;">📐 GlassPro <span style="color:#3b82f6;">Studio</span></h1>', unsafe_allow_html=True)
        st.caption("Configurador técnico para cristales procesados")
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1067/1067256.png", width=60)
        st.title("Configuración")
        
        with st.expander("📝 Datos del Cliente", expanded=False):
            client = st.text_input("Solicitante")
            ref = st.text_input("Obra/Referencia")

        with st.expander("📏 Dimensiones Base", expanded=True):
            presets = {"Personalizado": (1200, 800), "Puerta": (900, 2100), "Mampara": (800, 1800)}
            sel = st.selectbox("Plantilla", list(presets.keys()))
            w_init, h_init = presets[sel]
            
            w = st.number_input("Ancho (mm)", 100, 3000, w_init, 10)
            h = st.number_input("Alto (mm)", 100, 4000, h_init, 10)
            
            thick_opts = {"6 mm": 6, "10 mm": 10, "12 mm": 12, "Laminado 5+5": 10}
            t_name = st.selectbox("Espesor", list(thick_opts.keys()))
            t_val = thick_opts[t_name]

        perforations = []
        with st.expander("🔘 Perforaciones", expanded=False):
            qty = st.number_input("Cantidad", 0, 20, 0)
            for i in range(qty):
                st.markdown(f"**Orificio {i+1}**")
                col1, col2, col3 = st.columns(3)
                px = col1.number_input("X", 0, w, 100, key=f"x{i}")
                py = col2.number_input("Y", 0, h, 100, key=f"y{i}")
                pd = col3.number_input("Ø", 10, 200, 50, key=f"d{i}")
                perforations.append(Perforation(i, px, py, pd))

        with st.expander("🎨 Apariencia", expanded=False):
            v_style = st.radio("Estilo", [s.value for s in VisualStyle], horizontal=True)
            v_color = st.color_picker("Color Vidrio", "#3b82f6")

    # Logica de Datos
    specs = GlassSpecifications(w, h, t_name, t_val, perforations, VisualStyle(v_style), v_color)
    meta = ProjectMetadata(client, ref)

    # Main Layout
    col_vis, col_data = st.columns([3, 1], gap="large")

    with col_vis:
        st.markdown(HTMLRenderer.render(specs), unsafe_allow_html=True)

    with col_data:
        st.markdown('<p class="metric-label">Resumen Técnico</p>', unsafe_allow_html=True)
        
        # Tarjetas de Info con CSS personalizado
        st.markdown(f'''
            <div class="info-card">
                <div class="metric-label">Superficie</div>
                <div class="metric-value">{specs.area_m2:.2f} m²</div>
            </div>
            <div class="info-card">
                <div class="metric-label">Peso Estimado</div>
                <div class="metric-value">{specs.weight_kg:.1f} kg</div>
            </div>
        ''', unsafe_allow_html=True)
        
        st.divider()
        
        from reportlab.lib.pagesizes import A4 # Re-import local si es necesario
        pdf_file = PDFService.generate(meta, specs)
        st.download_button(
            label="📄 Generar Documentación",
            data=pdf_file,
            file_name=f"Plano_{client or 'S_N'}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        if st.button("🗑️ Limpiar Todo", use_container_width=True):
            st.rerun()

if __name__ == "__main__":
    main()