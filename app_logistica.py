import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Fridolin - Control Logístico",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para adaptar los colores a Fridolin
st.markdown("""
    <style>
        .main-header {
            color: #800c14;
            font-weight: bold;
            font-size: 2.2rem;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            color: #555555;
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }
        div[data-testid="stMetricValue"] {
            color: #800c14;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGO Y SIDEBAR
# ==========================================
try:
    # Carga el archivo Fridolin_logo.jpg subido al repositorio
    st.sidebar.image("Fridolin_logo.jpg", use_container_width=True)
except Exception:
    # Alternativa si por alguna razón no localiza la imagen
    st.sidebar.markdown("<h2 style='color: #800c14;'>🧁 Fridolin</h2>", unsafe_allow_html=True)

st.sidebar.caption("Sistema de Control Logístico y Distribución")
st.sidebar.divider()

# ==========================================
# 3. CARGA Y PROCESAMIENTO DE DATOS
# ==========================================
st.sidebar.subheader("📂 Cargar Datos")
uploaded_file = st.sidebar.file_uploader(
    "Sube el archivo Excel o CSV de Logística",
    type=["xlsx", "xls", "csv"]
)

@st.cache_data
def cargar_datos(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    return df

# ==========================================
# 4. CUERPO PRINCIPAL DE LA APLICACIÓN
# ==========================================
st.markdown("<div class='main-header'>Control y Distribución Logística</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Panel General de Monitoreo de Despachos y Envíos</div>", unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        df = cargar_datos(uploaded_file)
        
        # --- FILTROS DINÁMICOS ---
        st.sidebar.divider()
        st.sidebar.subheader("🎯 Filtros")
        
        # Filtro por Sucursal/Sucursales si la columna existe
        columnas = df.columns.tolist()
        col_sucursal = [c for c in columnas if 'sucursal' in c.lower() or 'destino' in c.lower() or 'tienda' in c.lower()]
        
        if col_sucursal:
            sucursales = ["Todas"] + sorted(df[col_sucursal[0]].dropna().unique().tolist())
            sucursal_sel = st.sidebar.selectbox("Seleccionar Sucursal:", sucursales)
            if sucursal_sel != "Todas":
                df = df[df[col_sucursal[0]] == sucursal_sel]

        # --- METRICAS CLAVE (KPIs) ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_registros = len(df)
        kpi1.metric("Total Pedidos / Registros", f"{total_registros:,}")

        col_cant = [c for c in columnas if 'cantidad' in c.lower() or 'cant' in c.lower() or 'unidades' in c.lower()]
        if col_cant:
            total_unidades = df[col_cant[0]].sum()
            kpi2.metric("Total Unidades Despachadas", f"{total_unidades:,.0f}")
        else:
            kpi2.metric("Total Unidades Despachadas", "N/A")

        col_estado = [c for c in columnas if 'estado' in c.lower() or 'estatus' in c.lower()]
        if col_estado:
            entregados = len(df[df[col_estado[0]].str.lower().str.contains('entregado|completado|ok', na=False)])
            pct_efectividad = (entregados / total_registros) * 100 if total_registros > 0 else 0
            kpi3.metric("Efectividad Entregas", f"{pct_efectividad:.1f}%")
        else:
            kpi3.metric("Efectividad Entregas", "N/A")

        kpi4.metric("Estado del Sistema", "Activo", delta="Operativo")

        st.divider()

        # --- TABLAS Y GRÁFICOS ---
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("📊 Distribución de Registros")
            if col_sucursal:
                df_graf = df[col_sucursal[0]].value_counts().reset_index()
                df_graf.columns = ['Destino', 'Cantidad']
                fig1 = px.bar(
                    df_graf.head(10), 
                    x='Destino', 
                    y='Cantidad', 
                    title="Top Destinos / Sucursales",
                    color_discrete_sequence=['#800c14']
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No se identificó una columna de Sucursal/Destino para graficar.")

        with col_graf2:
            st.subheader("🍩 Estado de Despachos")
            if col_estado:
                df_est = df[col_estado[0]].value_counts().reset_index()
                df_est.columns = ['Estado', 'Total']
                fig2 = px.pie(
                    df_est, 
                    names='Estado', 
                    values='Total', 
                    title="Proporción por Estado",
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No se identificó una columna de Estado para graficar.")

        # --- VISTA DETALLADA DE DATOS ---
        with st.expander("👀 Ver Tabla Completa de Datos Cargados"):
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👈 Por favor, carga tu archivo de datos en el panel lateral para empezar a visualizar las métricas de Fridolin.")
