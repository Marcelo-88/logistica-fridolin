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
URL_RUTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h/pub?sheet=Rutas_Logistica&output=csv"
URL_SUCURSALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h/pub?sheet=Sucursales&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    df_rutas = pd.read_csv(URL_RUTAS)
    
    # Limpiar espacios invisibles en nombres de columnas
    df_rutas.columns = df_rutas.columns.str.strip()
    
    # Intentar cargar sucursales si existe
    try:
        df_sucursales = pd.read_csv(URL_SUCURSALES)
        df_sucursales.columns = df_sucursales.columns.str.strip()
    except Exception:
        df_sucursales = pd.DataFrame()

    # --- Limpieza Rutas ---
    df_rutas = df_rutas.dropna(how="all")
    
    # Identificar columna Día
    col_dia = next((c for c in df_rutas.columns if 'Dí' in c or 'Di' in c or 'dí' in c or 'di' in c), None)
    col_cat = next((c for c in df_rutas.columns if 'Cat' in c or 'cat' in c), None)
    
    # Limpieza de textos
    for col in df_rutas.columns:
        df_rutas[col] = df_rutas[col].astype(str).str.strip().replace({'nan': '', 'None': ''})

    return df_rutas, df_sucursales, col_dia, col_cat

# Cargar Datos
try:
    df_rutas_raw, df_sucursales_raw, col_dia, col_cat = cargar_datos_logistica()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al procesar los datos de Google Sheets: {e}")
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

    df_filtrado = df_rutas_raw.copy()

    # Filtro Día seguro
    if col_dia and col_dia in df_rutas_raw.columns:
        dias_unicos = ["Todos"] + sorted([d for d in df_rutas_raw[col_dia].unique() if d])
        filtro_dia = st.sidebar.selectbox("Filtrar por Día:", dias_unicos)
        if filtro_dia != "Todos":
            df_filtrado = df_filtrado[df_filtrado[col_dia] == filtro_dia]

    # Filtro Categoría seguro
    if col_cat and col_cat in df_rutas_raw.columns:
        cats_unicas = ["Todas"] + sorted([c for c in df_rutas_raw[col_cat].unique() if c])
        filtro_cat = st.sidebar.selectbox("Filtrar por Categoría:", cats_unicas)
        if filtro_cat != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col_cat] == filtro_cat]

# ==========================================
# 4. CONTENIDO PRINCIPAL
# ==========================================
if datos_cargados:
    st.title("🚛 Panel Operativo de Logística Fridolin")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros", f"{len(df_filtrado)}")
    
    cat_count = df_filtrado[col_cat].nunique() if col_cat and col_cat in df_filtrado.columns else 0
    col2.metric("Categorías Activas", f"{cat_count}")
    
    dia_count = df_filtrado[col_dia].nunique() if col_dia and col_dia in df_filtrado.columns else 0
    col3.metric("Días Operativos", f"{dia_count}")

    st.divider()

    if menu_opcion == "🚚 1. Control de Rutas y Horarios":
        st.subheader("📋 Planificación de Rutas por Sucursal")
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True
        )

    elif menu_opcion == "📊 2. Resumen por Categoría y Frecuencia":
        st.subheader("📊 Distribución de Rutas por Categoría")
        if col_cat and col_cat in df_filtrado.columns:
            st.bar_chart(df_filtrado[col_cat].value_counts())
        else:
            st.info("No se encontró la columna Categoría para graficar.")

    elif menu_opcion == "🏢 3. Directorio de Sucursales":
        st.subheader("🏢 Base de Datos de Sucursales")
        if not df_sucursales_raw.empty:
            st.dataframe(df_sucursales_raw, use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron datos en la pestaña 'Sucursales'.")
