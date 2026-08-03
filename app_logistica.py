import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Control Logístico y Rutas | Fridolin",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stMetric { background-color: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENLACE PÚBLICO DE GOOGLE SHEETS
# ==========================================
# URL de exportación publicada
URL_RUTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h/pub?sheet=Rutas_Logistica&output=csv"
URL_SUCURSALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h/pub?sheet=Sucursales&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    df_rutas = pd.read_csv(URL_RUTAS)
    
    # Intentar cargar sucursales si existe la pestaña
    try:
        df_sucursales = pd.read_csv(URL_SUCURSALES)
    except Exception:
        df_sucursales = pd.DataFrame()

    # --- Limpieza Rutas ---
    df_rutas = df_rutas.dropna(how="all")
    
    # Asegurar texto limpio en columnas clave
    cols_texto = ['Día', 'Categoría', 'Sucursal_1', 'Sucursal_2', 'Sucursal_3', 'Sucursal 4', 'Comentario', 'Frecuencia']
    for c in cols_texto:
        if c in df_rutas.columns:
            df_rutas[c] = df_rutas[c].astype(str).str.strip().replace({'nan': '', 'None': ''})

    # --- Limpieza Sucursales ---
    if not df_sucursales.empty:
        df_sucursales = df_sucursales.dropna(how="all")
        if 'SUCURSAL' in df_sucursales.columns:
            df_sucursales['SUCURSAL'] = df_sucursales['SUCURSAL'].astype(str).str.replace('SUC.', '', regex=False).str.strip()
        
        if 'LATITUD Y LONGT' in df_sucursales.columns:
            coords = df_sucursales['LATITUD Y LONGT'].astype(str).str.split(',', expand=True)
            if coords.shape[1] >= 2:
                df_sucursales['lat'] = pd.to_numeric(coords[0], errors='coerce')
                df_sucursales['lon'] = pd.to_numeric(coords[1], errors='coerce')

    return df_rutas, df_sucursales

# Cargar Datos
try:
    df_rutas_raw, df_sucursales_raw = cargar_datos_logistica()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    datos_cargados = False

# ==========================================
# 3. BARRA LATERAL Y FILTROS
# ==========================================
st.sidebar.image("https://em-content.zobj.net/source/apple/354/delivery-truck_1f68a.png", width=60)
st.sidebar.title("Logística Fridolin")
st.sidebar.caption("Panel Operativo 2026")
st.sidebar.divider()

if datos_cargados:
    menu_opcion = st.sidebar.radio(
        "📌 Menú de Navegación:",
        [
            "🚚 1. Control de Rutas y Horarios",
            "📊 2. Resumen por Categoría y Frecuencia",
            "🏢 3. Directorio de Sucursales"
        ]
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Filtros Rápidos")

    # Filtro Día
    dias_unicos = ["Todos"] + [d for d in df_rutas_raw['Día'].unique() if d and d != 'nan']
    filtro_dia = st.sidebar.selectbox("Filtrar por Día:", dias_unicos)

    # Filtro Categoría
    cats_unicas = ["Todas"] + [c for c in df_rutas_raw['Categoría'].unique() if c and c != 'nan']
    filtro_cat = st.sidebar.selectbox("Filtrar por Categoría:", cats_unicas)

    # Aplicar Filtros
    df_filtrado = df_rutas_raw.copy()
    if filtro_dia != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Día'] == filtro_dia]
    if filtro_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Categoría'] == filtro_cat]

# ==========================================
# 4. CONTENIDO PRINCIPAL
# ==========================================
if datos_cargados:
    st.title("🚛 Panel Operativo de Logística Fridolin")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros de Rutas", f"{len(df_filtrado)}")
    col2.metric("Categorías Activas", f"{df_filtrado['Categoría'].nunique()}")
    col3.metric("Días Operativos", f"{df_filtrado['Día'].nunique()}")

    st.divider()

    if menu_opcion == "🚚 1. Control de Rutas y Horarios":
        st.subheader("📋 Planificación de Rutas por Sucursal")
        
        # Seleccionar columnas visibles que realmente existen en el Excel
        cols_mostrar = [c for c in ['Día', 'Categoría', 'Sucursal_1', 'Sucursal_2', 'Sucursal_3', 'Sucursal 4', 'Comentario', 'Frecuencia'] if c in df_filtrado.columns]
        
        st.dataframe(
            df_filtrado[cols_mostrar],
            use_container_width=True,
            hide_index=True
        )

    elif menu_opcion == "📊 2. Resumen por Categoría y Frecuencia":
        st.subheader("📊 Distribución de Rutas por Categoría")
        st.bar_chart(df_filtrado['Categoría'].value_counts())
        
        st.subheader("📌 Frecuencia de Distribución")
        st.dataframe(df_filtrado['Frecuencia'].value_counts().reset_index(), use_container_width=True)

    elif menu_opcion == "🏢 3. Directorio de Sucursales":
        st.subheader("🏢 Base de Datos de Sucursales")
        if not df_sucursales_raw.empty:
            st.dataframe(df_sucursales_raw, use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron datos en la pestaña 'Sucursales'.")
