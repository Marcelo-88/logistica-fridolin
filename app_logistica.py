import streamlit as st
import pandas as pd
import urllib.parse

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Control Logístico y Rutas | Fridolin",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo visual
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stMetric { background-color: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENLACE DIRECTO A GOOGLE SHEETS
# ==========================================
SHEET_ID = "1vMrjVjM7575QlbgM19mpbQhrUxnC183hH3MDjC8AjfM"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    # Codificar nombres de pestañas para evitar errores de espacios/caracteres
    sheet_rutas = urllib.parse.quote("Rutas_Logistica")
    sheet_sucursales = urllib.parse.quote("Sucursales")
    
    url_rutas = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_rutas}"
    url_sucursales = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_sucursales}"
    
    df_rutas = pd.read_csv(url_rutas)
    df_sucursales = pd.read_csv(url_sucursales)

    # Limpieza: Rutas
    df_rutas = df_rutas.dropna(how="all")
    for col in ['Día', 'Categoría', 'Sucursal_1', 'Sucursal_2', 'Sucursal_3', 'Sucursal 4', 'Movilidad']:
        if col in df_rutas.columns:
            df_rutas[col] = df_rutas[col].astype(str).str.strip()
    
    if 'KM_Recorridos' in df_rutas.columns:
        df_rutas['KM_Recorridos'] = pd.to_numeric(df_rutas['KM_Recorridos'], errors='coerce').fillna(0)
    else:
        df_rutas['KM_Recorridos'] = 0
    
    # Limpieza: Sucursales
    df_sucursales = df_sucursales.dropna(how="all")
    if 'SUCURSAL' in df_sucursales.columns:
        df_sucursales['SUCURSAL'] = df_sucursales['SUCURSAL'].astype(str).str.replace('SUC.', '', regex=False).str.strip()
    
    if 'LATITUD Y LONGT' in df_sucursales.columns:
        coords = df_sucursales['LATITUD Y LONGT'].astype(str).str.split(',', expand=True)
        if coords.shape[1] >= 2:
            df_sucursales['lat'] = pd.to_numeric(coords[0], errors='coerce')
            df_sucursales['lon'] = pd.to_numeric(coords[1], errors='coerce')

    return df_rutas, df_sucursales

# Cargar datos
try:
    df_rutas_raw, df_sucursales_raw = cargar_datos_logistica()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    st.info("💡 Asegúrate de hacer 'Archivo ➔ Compartir ➔ Publicar en la web' en tu hoja de Google Sheets y que las pestañas se llamen 'Rutas_Logistica' y 'Sucursales'.")
    datos_cargados = False

# ==========================================
# 3. BARRA LATERAL Y FILTROS
# ==========================================
st.sidebar.image("https://em-content.zobj.net/source/apple/354/delivery-truck_1f68a.png", width=60)
st.sidebar.title("Logística Fridolin")
st.sidebar.caption("Panel Operativo de Rutas 2026")
st.sidebar.divider()

if datos_cargados:
    menu_opcion = st.sidebar.radio(
        "📌 Menú de Navegación:",
        [
            "🚚 1. Control de Movilidades y Turnos",
            "🗺️ 2. Mapa Interactivo de Rutas",
            "📊 3. Dashboard KPI y Métricas",
            "🏢 4. Directorio de Sucursales"
        ]
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Filtros Rápidos")

    # Filtros dinámicos
    col_dia = 'Día' if 'Día' in df_rutas_raw.columns else df_rutas_raw.columns[0]
    dias_disponibles = ["Todos"] + sorted(list(df_rutas_raw[col_dia].dropna().unique()))
    filtro_dia = st.sidebar.selectbox("Filtrar por Día:", dias_disponibles)

    col_cat = 'Categoría' if 'Categoría' in df_rutas_raw.columns else df_rutas_raw.columns[0]
    cats_disponibles = ["Todas"] + sorted(list(df_rutas_raw[col_cat].dropna().unique()))
    filtro_cat = st.sidebar.selectbox("Filtrar por Categoría:", cats_disponibles)

    col_mov = 'Movilidad' if 'Movilidad' in df_rutas_raw.columns else df_rutas_raw.columns[0]
    movs_disponibles = ["Todas"] + sorted([m for m in df_rutas_raw[col_mov].unique() if str(m) not in ['nan', 'None']])
    filtro_mov = st.sidebar.selectbox("Filtrar por Movilidad:", movs_disponibles)

    # Filtrar
    df_filtrado = df_rutas_raw.copy()
    if filtro_dia != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_dia] == filtro_dia]
    if filtro_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_cat] == filtro_cat]
    if filtro_mov != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_mov] == filtro_mov]

# ==========================================
# 4. CONTENIDO PRINCIPAL
# ==========================================
if datos_cargados:
    st.title("🚛 Panel Operativo de Rutas y Logística")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rutas", f"{len(df_filtrado)}")
    col2.metric("Kilómetros Totales", f"{df_filtrado['KM_Recorridos'].sum():,.0f} km")
    
    prom_km = df_filtrado['KM_Recorridos'].mean() if len(df_filtrado) > 0 else 0
    col3.metric("Promedio por Ruta", f"{prom_km:.1f} km")
    
    max_km = df_filtrado['KM_Recorridos'].max() if len(df_filtrado) > 0 else 0
    col4.metric("Ruta Más Larga", f"{max_km:.0f} km")

    st.divider()

    if menu_opcion == "🚚 1. Control de Movilidades y Turnos":
        st.subheader("📋 Detalle Operativo de Rutas y Horarios")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    elif menu_opcion == "🗺️ 2. Mapa Interactivo de Rutas":
        st.subheader("🗺️ Mapeo Geográfico de Sucursales")
        st.info("Módulo de mapa listo para desplegar.")

    elif menu_opcion == "📊 3. Dashboard KPI y Métricas":
        st.subheader("📊 Análisis de Rendimiento Logístico")
        st.info("Módulo de métricas listo para desplegar.")

    elif menu_opcion == "🏢 4. Directorio de Sucursales":
        st.subheader("🏢 Directorio de Sucursales y Coordenadas GPS")
        st.dataframe(df_sucursales_raw, use_container_width=True, hide_index=True)
