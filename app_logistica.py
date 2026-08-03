import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="Control Logístico y Rutas | Fridolin",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados para modernizar la interfaz
st.markdown("""
    <style>
    /* Ajustes generales */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    /* Métricas estilizadas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #1e293b;
        font-weight: 700;
    }

    /* Rediseño del Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Contenedor de filtros en sidebar */
    .filter-box {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENLACES Y CARGA DE DATOS (GOOGLE SHEETS)
# ==========================================
PUB_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h"

GID_RUTAS = "2020862153"
GID_SUCURSALES = "51773579"

URL_RUTAS = f"{PUB_BASE}/pub?single=true&gid={GID_RUTAS}&output=csv"
URL_SUCURSALES = f"{PUB_BASE}/pub?single=true&gid={GID_SUCURSALES}&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    # Cargar Rutas
    df_rutas = pd.read_csv(URL_RUTAS)
    df_rutas.columns = df_rutas.columns.str.strip()
    df_rutas = df_rutas.dropna(how="all")

    # Cargar Sucursales
    try:
        df_sucursales = pd.read_csv(URL_SUCURSALES)
        df_sucursales.columns = df_sucursales.columns.str.strip()
        df_sucursales = df_sucursales.dropna(how="all")
    except Exception:
        df_sucursales = pd.DataFrame()

    # Limpieza de textos y None
    for col in df_rutas.columns:
        df_rutas[col] = df_rutas[col].astype(str).str.strip()
        df_rutas[col] = df_rutas[col].replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    if not df_sucursales.empty:
        for col in df_sucursales.columns:
            df_sucursales[col] = df_sucursales[col].astype(str).str.strip()
            df_sucursales[col] = df_sucursales[col].replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    return df_rutas, df_sucursales

try:
    df_rutas_raw, df_sucursales_raw = cargar_datos_logistica()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    datos_cargados = False

# ==========================================
# 3. BARRA LATERAL REDISEÑADA (FILTROS ARRIBA)
# ==========================================
if datos_cargados:
    st.sidebar.image("https://em-content.zobj.net/source/apple/354/delivery-truck_1f68a.png", width=50)
    st.sidebar.title("Logística Fridolin")
    st.sidebar.caption("Panel de Control Operativo 2026")
    st.sidebar.divider()

    # --- FILTROS RÁPIDOS ARRIBA PARA EVITAR SCROLL ---
    st.sidebar.subheader("🎯 Filtros Multiselección")

    df_filtrado = df_rutas_raw.copy()

    # Identificar columnas principales
    col_dia = next((c for c in df_rutas_raw.columns if 'Dí' in c or 'Di' in c or 'dí' in c), None)
    col_cat = next((c for c in df_rutas_raw.columns if 'Cat' in c or 'cat' in c), None)

    # 1. Filtro Multiselección de Días
    if col_dia and col_dia in df_rutas_raw.columns:
        dias_disponibles = [d for d in df_rutas_raw[col_dia].unique() if d]
        dias_seleccionados = st.sidebar.multiselect(
            "📅 Seleccionar Día(s):",
            options=dias_disponibles,
            default=[],
            placeholder="Todos los días"
        )
        if dias_seleccionados:
            df_filtrado = df_filtrado[df_filtrado[col_dia].isin(dias_seleccionados)]

    # 2. Filtro Multiselección de Categoría
    if col_cat and col_cat in df_rutas_raw.columns:
        cats_disponibles = [c for c in df_rutas_raw[col_cat].unique() if c]
        cats_seleccionadas = st.sidebar.multiselect(
            "📦 Categoría(s):",
            options=cats_disponibles,
            default=[],
            placeholder="Todas las categorías"
        )
        if cats_seleccionadas:
            df_filtrado = df_filtrado[df_filtrado[col_cat].isin(cats_seleccionadas)]

    # 3. Buscador por Sucursal
    busqueda_sucursal = st.sidebar.text_input("🔍 Buscar Sucursal en Rutas:", placeholder="Ej. Hipermaxi, Urubó...")
    if busqueda_sucursal:
        # Busca la palabra en cualquier columna de la tabla
        mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busqueda_sucursal, case=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]

    st.sidebar.divider()

    # Menú de Navegación Abajo de los Filtros
    menu_opcion = st.sidebar.radio(
        "📌 Menú de Secciones:",
        [
            "🚚 1. Control de Rutas y Horarios",
            "📊 2. Resumen por Categoría y Frecuencia",
            "🏢 3. Directorio de Sucursales"
        ]
    )

# ==========================================
# 4. CONTENIDO PRINCIPAL
# ==========================================
if datos_cargados:
    st.title("🚛 Planificación Logística y Despachos")
    
    # KPi Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Rutas Activas (Filtradas)", f"{len(df_filtrado)}")
    
    cat_count = df_filtrado[col_cat].nunique() if col_cat and col_cat in df_filtrado.columns else 0
    col2.metric("Categorías en Vista", f"{cat_count}")
    
    dia_count = df_filtrado[col_dia].nunique() if col_dia and col_dia in df_filtrado.columns else 0
    col3.metric("Días Abarcados", f"{dia_count}")

    st.divider()

    # VISTA 1: CONTROL DE RUTAS
    if menu_opcion == "🚚 1. Control de Rutas y Horarios":
        st.subheader("📋 Matriz de Entregas por Ruta")
        
        # Ocultar columnas sin nombre o vacías
        cols_mostrar = [c for c in df_filtrado.columns if not c.startswith('Unnamed')]
        df_vista = df_filtrado[cols_mostrar].copy()

        # Configuración visual de columnas con st.column_config
        column_config = {
            col_dia: st.column_config.TextColumn("Día", width="small"),
            col_cat: st.column_config.TextColumn("Categoría", width="medium"),
        }

        # Aplicar formato a columnas Sucursal y Comentario si existen
        for col in df_vista.columns:
            if 'Sucursal' in col:
                column_config[col] = st.column_config.TextColumn(col.replace('_', ' '), width="medium")
            elif 'Comentario' in col:
                column_config[col] = st.column_config.TextColumn("Comentario", width="large")
            elif 'Frecuencia' in col:
                column_config[col] = st.column_config.TextColumn("Frecuencia", width="large")

        st.dataframe(
            df_vista,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=500  # Permite scroll interno cómodo
        )

    # VISTA 2: RESUMEN Y GRÁFICOS
    elif menu_opcion == "📊 2. Resumen por Categoría y Frecuencia":
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Distribución por Categoría")
            if col_cat and col_cat in df_filtrado.columns:
                st.bar_chart(df_filtrado[col_cat].value_counts(), color="#2563eb")
        
        with col_right:
            st.subheader("📌 Rutas por Día de la Semana")
            if col_dia and col_dia in df_filtrado.columns:
                st.bar_chart(df_filtrado[col_dia].value_counts(), color="#0d9488")

    # VISTA 3: DIRECTORIO DE SUCURSALES
    elif menu_opcion == "🏢 3. Directorio de Sucursales":
        st.subheader("🏢 Coordenadas y Ubicación de Sucursales")
        if not df_sucursales_raw.empty:
            cols_suc = [c for c in df_sucursales_raw.columns if not c.startswith('Unnamed')]
            st.dataframe(
                df_sucursales_raw[cols_suc], 
                use_container_width=True, 
                hide_index=True,
                height=500
            )
        else:
            st.info("No se encontraron datos en la pestaña 'Sucursales'.")
