import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Control Logístico y Rutas | Fridolin",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 12px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y SEPARACIÓN DE DATOS
# ==========================================
PUB_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h"

GID_RUTAS = "2020862153"
GID_SUCURSALES = "51773579"

URL_RUTAS = f"{PUB_BASE}/pub?single=true&gid={GID_RUTAS}&output=csv"
URL_SUCURSALES = f"{PUB_BASE}/pub?single=true&gid={GID_SUCURSALES}&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    # Cargar matriz completa de Rutas
    df_raw = pd.read_csv(URL_RUTAS, header=None)
    
    # ----------------------------------------------------
    # SEPARACIÓN 1: Rutas de Distribución (Columnas A a O)
    # ----------------------------------------------------
    # Tomamos la primera fila como encabezado para rutas
    df_rutas = df_raw.iloc[:, :15].copy()
    df_rutas.columns = df_rutas.iloc[0]
    df_rutas = df_rutas[1:].reset_index(drop=True)
    df_rutas = df_rutas.dropna(how="all")
    
    # Limpieza de textos y valores nulos
    for col in df_rutas.columns:
        if pd.notna(col):
            df_rutas[col] = df_rutas[col].astype(str).str.strip().replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    # Eliminar columnas sin nombre o basura
    df_rutas = df_rutas.loc[:, df_rutas.columns.notna()]
    df_rutas = df_rutas.loc[:, ~df_rutas.columns.str.startswith('Unnamed')]

    # ----------------------------------------------------
    # SEPARACIÓN 2: Horarios de Movilidades (Columnas Q a T)
    # ----------------------------------------------------
    df_movilidades = pd.DataFrame()
    if df_raw.shape[1] >= 20:
        # Extraer columnas 16 a 19 (Q, R, S, T)
        df_mov = df_raw.iloc[:, 16:20].copy()
        
        # Filtrar filas donde la columna Q tenga datos válidos de Movilidad
        df_mov = df_mov.dropna(how="all")
        
        # Buscar encabezados 'Movilidad', 'Ingreso', 'Salida', 'Total'
        mov_headers = ['Movilidad', 'Ingreso', 'Salida', 'Total']
        
        # Filtrar filas numéricas o relevantes
        rows_mov = []
        for idx, row in df_mov.iterrows():
            vals = [str(v).strip() for v in row.values]
            if vals[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'] or vals[0] == 'Movilidad':
                rows_mov.append(vals)
                
        if rows_mov:
            df_movilidades = pd.DataFrame(rows_mov)
            if df_movilidades.iloc[0][0] == 'Movilidad':
                df_movilidades.columns = df_movilidades.iloc[0]
                df_movilidades = df_movilidades[1:].reset_index(drop=True)
            else:
                df_movilidades.columns = mov_headers
            
            # Quitar repetidos de encabezados si los hay
            df_movilidades = df_movilidades[df_movilidades['Movilidad'] != 'Movilidad']

    # ----------------------------------------------------
    # CARGA: Pestaña Sucursales
    # ----------------------------------------------------
    try:
        df_sucursales = pd.read_csv(URL_SUCURSALES)
        df_sucursales.columns = df_sucursales.columns.str.strip()
        df_sucursales = df_sucursales.dropna(how="all")
        for col in df_sucursales.columns:
            df_sucursales[col] = df_sucursales[col].astype(str).str.strip().replace({'nan': '', 'None': ''})
    except Exception:
        df_sucursales = pd.DataFrame()

    return df_rutas, df_movilidades, df_sucursales

try:
    df_rutas_raw, df_movilidades_raw, df_sucursales_raw = cargar_datos_logistica()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al procesar los datos de Google Sheets: {e}")
    datos_cargados = False

# ==========================================
# 3. FILTROS Y NAVEGACIÓN EN SIDEBAR
# ==========================================
if datos_cargados:
    st.sidebar.image("https://em-content.zobj.net/source/apple/354/delivery-truck_1f68a.png", width=45)
    st.sidebar.title("Logística Fridolin")
    st.sidebar.caption("Sistema de Control Operativo")
    st.sidebar.divider()

    st.sidebar.subheader("🎯 Filtros Multiselección")

    df_filtrado = df_rutas_raw.copy()

    col_dia = next((c for c in df_rutas_raw.columns if 'Dí' in c or 'Di' in c or 'dí' in c), None)
    col_cat = next((c for c in df_rutas_raw.columns if 'Cat' in c or 'cat' in c), None)

    # Filtro Días
    if col_dia and col_dia in df_rutas_raw.columns:
        dias_disponibles = [d for d in df_rutas_raw[col_dia].unique() if d and d != 'nan']
        dias_seleccionados = st.sidebar.multiselect(
            "📅 Seleccionar Día(s):",
            options=dias_disponibles,
            placeholder="Todos los días"
        )
        if dias_seleccionados:
            df_filtrado = df_filtrado[df_filtrado[col_dia].isin(dias_seleccionados)]

    # Filtro Categorías
    if col_cat and col_cat in df_rutas_raw.columns:
        cats_disponibles = [c for c in df_rutas_raw[col_cat].unique() if c and c != 'nan']
        cats_seleccionadas = st.sidebar.multiselect(
            "📦 Categoría(s):",
            options=cats_disponibles,
            placeholder="Todas las categorías"
        )
        if cats_seleccionadas:
            df_filtrado = df_filtrado[df_filtrado[col_cat].isin(cats_seleccionadas)]

    # Búsqueda rápida
    busqueda = st.sidebar.text_input("🔍 Buscar Sucursal en Rutas:", placeholder="Ej. Hipermaxi...")
    if busqueda:
        mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]

    st.sidebar.divider()

    # Menú ampliado
    menu_opcion = st.sidebar.radio(
        "📌 Menú Principal:",
        [
            "🚚 1. Planificación de Rutas",
            "⏱️ 2. Jornada de Movilidades (Q:T)",
            "📊 3. Resumen y Estadísticas",
            "🏢 4. Directorio de Sucursales"
        ]
    )

# ==========================================
# 4. CONTENIDO SEGÚN SECCIÓN
# ==========================================
if datos_cargados:
    
    # OP 1: PLANIFICACIÓN DE RUTAS
    if menu_opcion == "🚚 1. Planificación de Rutas":
        st.title("🚛 Planificación de Rutas y Salidas")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Registros en Vista", f"{len(df_filtrado)}")
        col2.metric("Categorías", f"{df_filtrado[col_cat].nunique() if col_cat else 0}")
        col3.metric("Días Operativos", f"{df_filtrado[col_dia].nunique() if col_dia else 0}")
        
        st.divider()
        st.subheader("📋 Detalle de Paradas y Recorridos")
        
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            height=520
        )

    # OP 2: JORNADA DE MOVILIDADES (DATOS Q:T)
    elif menu_opcion == "⏱️ 2. Jornada de Movilidades (Q:T)":
        st.title("⏱️ Control de Jornada Laboral por Movilidad")
        st.caption("Información extraída independientemente de las columnas Q a T del documento.")
        st.divider()

        if not df_movilidades_raw.empty:
            col_m1, col_m2 = st.columns([2, 1])
            
            with col_m1:
                st.subheader("📋 Horarios de Ingreso y Salida de Choferes / Vehículos")
                st.dataframe(
                    df_movilidades_raw,
                    use_container_width=True,
                    hide_index=True
                )
            
            with col_m2:
                st.subheader("💡 Resumen de Movilidades")
                st.metric("Total Movilidades Registradas", len(df_movilidades_raw))
                st.info("Esta sección refleja exclusivamente el tiempo total de trabajo asignado a cada unidad movilizada.")
        else:
            st.warning("No se detectaron registros de movilidades en las columnas Q:T.")

    # OP 3: RESUMEN Y ESTADÍSTICAS
    elif menu_opcion == "📊 3. Resumen y Estadísticas":
        st.title("📊 Resumen Operativo")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Distribución por Categoría")
            if col_cat and col_cat in df_filtrado.columns:
                st.bar_chart(df_filtrado[col_cat].value_counts(), color="#2563eb")

        with col_b:
            st.subheader("Distribución por Día")
            if col_dia and col_dia in df_filtrado.columns:
                st.bar_chart(df_filtrado[col_dia].value_counts(), color="#0d9488")

    # OP 4: DIRECTORIO DE SUCURSALES
    elif menu_opcion == "🏢 4. Directorio de Sucursales":
        st.title("🏢 Directorio de Sucursales")
        st.divider()
        if not df_sucursales_raw.empty:
            st.dataframe(
                df_sucursales_raw,
                use_container_width=True,
                hide_index=True,
                height=500
            )
        else:
            st.info("No hay datos disponibles en la pestaña de Sucursales.")
