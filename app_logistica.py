import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

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
# 2. CONEXIÓN A GOOGLE SHEETS Y LIMPIEZA
# ==========================================
@st.cache_data(ttl=600)  # Recarga los datos cada 10 minutos automáticamente
def cargar_datos_logistica():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Cargar las pestañas de Google Sheets
    df_rutas = conn.read(worksheet="Rutas_Logistica")
    df_sucursales = conn.read(worksheet="Sucursales")

    # Limpieza de textos en Rutas
    df_rutas = df_rutas.dropna(how="all")
    for col in ['Día', 'Categoría', 'Sucursal_1', 'Sucursal_2', 'Sucursal_3', 'Sucursal 4', 'Movilidad']:
        if col in df_rutas.columns:
            df_rutas[col] = df_rutas[col].astype(str).str.strip()
    
    df_rutas['KM_Recorridos'] = pd.to_numeric(df_rutas['KM_Recorridos'], errors='coerce').fillna(0)
    
    # Extraer Latitud y Longitud GPS de Sucursales
    df_sucursales = df_sucursales.dropna(how="all")
    df_sucursales['SUCURSAL'] = df_sucursales['SUCURSAL'].astype(str).str.replace('SUC.', '', regex=False).str.strip()
    
    if 'LATITUD Y LONGT' in df_sucursales.columns:
        coords = df_sucursales['LATITUD Y LONGT'].astype(str).str.split(',', expand=True)
        if coords.shape[1] >= 2:
            df_sucursales['lat'] = pd.to_numeric(coords[0], errors='coerce')
            df_sucursales['lon'] = pd.to_numeric(coords[1], errors='coerce')

    return df_rutas, df_sucursales


# Cargar los datos
try:
    df_rutas_raw, df_sucursales_raw = cargar_datos_logistica()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    datos_cargados = False


# ==========================================
# 3. MENÚ LATERAL Y FILTROS
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

    # Filtros por Día, Categoría y Movilidad
    dias_disponibles = ["Todos"] + sorted(list(df_rutas_raw['Día'].dropna().unique()))
    filtro_dia = st.sidebar.selectbox("Filtrar por Día:", dias_disponibles)

    cats_disponibles = ["Todas"] + sorted(list(df_rutas_raw['Categoría'].dropna().unique()))
    filtro_cat = st.sidebar.selectbox("Filtrar por Categoría:", cats_disponibles)

    movs_disponibles = ["Todas"] + sorted([m for m in df_rutas_raw['Movilidad'].unique() if m not in ['nan', 'None']])
    filtro_mov = st.sidebar.selectbox("Filtrar por Movilidad:", movs_disponibles)

    # Filtrar el conjunto de datos
    df_filtrado = df_rutas_raw.copy()
    if filtro_dia != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Día'] == filtro_dia]
    if filtro_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Categoría'] == filtro_cat]
    if filtro_mov != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Movilidad'] == filtro_mov]


# ==========================================
# 4. PANTALLAS Y MÓDULOS
# ==========================================
if datos_cargados:
    st.title("🚛 Panel Operativo de Rutas y Logística")
    
    # Tarjetas de datos rápidos (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rutas", f"{len(df_filtrado)}")
    col2.metric("Kilómetros Totales", f"{df_filtrado['KM_Recorridos'].sum():,.0f} km")
    
    prom_km = df_filtrado['KM_Recorridos'].mean() if len(df_filtrado) > 0 else 0
    col3.metric("Promedio por Ruta", f"{prom_km:.1f} km")
    
    max_km = df_filtrado['KM_Recorridos'].max() if len(df_filtrado) > 0 else 0
    col4.metric("Ruta Más Larga", f"{max_km:.0f} km")

    st.divider()

    # Muestras según el menú
    if menu_opcion == "🚚 1. Control de Movilidades y Turnos":
        st.subheader("📋 Detalle Operativo de Rutas y Horarios")
        st.dataframe(
            df_filtrado[['Día', 'Categoría', 'Sucursal_1', 'Sucursal_2', 'Sucursal_3', 'Hora_Salida', 'Hora_Retorno', 'KM_Recorridos', 'Movilidad']],
            use_container_width=True,
            hide_index=True
        )

    elif menu_opcion == "🗺️ 2. Mapa Interactivo de Rutas":
        st.subheader("🗺️ Mapeo Geográfico de Sucursales")
        st.info("Módulo de mapa listo para activar en el siguiente paso.")

    elif menu_opcion == "📊 3. Dashboard KPI y Métricas":
        st.subheader("📊 Análisis de Rendimiento Logístico")
        st.info("Módulo de métricas listo para activar.")

    elif menu_opcion == "🏢 4. Directorio de Sucursales":
        st.subheader("🏢 Directorio de Sucursales y Coordenadas GPS")
        st.dataframe(df_sucursales_raw, use_container_width=True, hide_index=True)
