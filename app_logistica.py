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
# 2. ENLACES Y PROCESAMIENTO INTELIGENTE
# ==========================================
PUB_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h"

GID_RUTAS = "2020862153"
GID_SUCURSALES = "51773579"

URL_RUTAS = f"{PUB_BASE}/pub?single=true&gid={GID_RUTAS}&output=csv"
URL_SUCURSALES = f"{PUB_BASE}/pub?single=true&gid={GID_SUCURSALES}&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    # Cargar matriz completa raw sin encabezados fijos
    df_raw = pd.read_csv(URL_RUTAS, header=None)
    
    # ----------------------------------------------------
    # 1. TABLA DE RUTAS DE DISTRIBUCIÓN (Cols A a O)
    # ----------------------------------------------------
    df_rutas = df_raw.iloc[:, :15].copy()
    df_rutas.columns = df_rutas.iloc[0]
    df_rutas = df_rutas[1:].reset_index(drop=True)
    df_rutas = df_rutas.dropna(how="all")
    
    for col in df_rutas.columns:
        if pd.notna(col):
            df_rutas[col] = df_rutas[col].astype(str).str.strip().replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    df_rutas = df_rutas.loc[:, df_rutas.columns.notna()]
    df_rutas = df_rutas.loc[:, ~df_rutas.columns.str.startswith('Unnamed')]

    # Identificar columna Día
    col_dia = next((c for c in df_rutas.columns if 'Dí' in c or 'Di' in c or 'dí' in c), None)

    # ----------------------------------------------------
    # 2. TABLA DE MOVILIDADES ASOCIADA POR DÍA (Cols Q a T)
    # ----------------------------------------------------
    bloques_movilidades = []
    
    if df_raw.shape[1] >= 20:
        dia_actual = "General"
        
        for idx in range(1, len(df_raw)):
            # Detectar si en la columna A hay un día especificado
            val_dia = str(df_raw.iloc[idx, 0]).strip()
            if val_dia in ['Lunes', 'Martes', 'Miércoles', 'Miercoles', 'Jueves', 'Viernes', 'Sábado', 'Sabado', 'Domingo']:
                dia_actual = val_dia
            
            # Extraer valores de las columnas Q, R, S, T (16, 17, 18, 19)
            mov = str(df_raw.iloc[idx, 16]).strip()
            ingreso = str(df_raw.iloc[idx, 17]).strip()
            salida = str(df_raw.iloc[idx, 18]).strip()
            total = str(df_raw.iloc[idx, 19]).strip()

            # Guardar si es una fila de datos válida (número de movilidad)
            if mov in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                bloques_movilidades.append({
                    'Día': dia_actual,
                    'Movilidad': f"Movilidad {mov}",
                    'Ingreso': ingreso if ingreso not in ['nan', 'None'] else '',
                    'Salida': salida if salida not in ['nan', 'None'] else '',
                    'Total Horas': total if total not in ['nan', 'None'] else ''
                })

    df_movilidades = pd.DataFrame(bloques_movilidades)

    # ----------------------------------------------------
    # 3. DIRECTORIO DE SUCURSALES
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
# 3. FILTROS Y SIDEBAR
# ==========================================
if datos_cargados:
    st.sidebar.image("https://em-content.zobj.net/source/apple/354/delivery-truck_1f68a.png", width=45)
    st.sidebar.title("Logística Fridolin")
    st.sidebar.caption("Panel Operativo 2026")
    st.sidebar.divider()

    st.sidebar.subheader("🎯 Filtros Multiselección")

    df_filtrado = df_rutas_raw.copy()
    df_mov_filtrado = df_movilidades_raw.copy()

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
            if not df_mov_filtrado.empty:
                df_mov_filtrado = df_mov_filtrado[df_mov_filtrado['Día'].isin(dias_seleccionados)]

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

    # Buscador rápido
    busqueda = st.sidebar.text_input("🔍 Buscar Sucursal en Rutas:", placeholder="Ej. Hipermaxi...")
    if busqueda:
        mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]

    st.sidebar.divider()

    # Menú Principal
    menu_opcion = st.sidebar.radio(
        "📌 Menú Principal:",
        [
            "🚚 1. Planificación de Rutas",
            "⏱️ 2. Jornada de Movilidades por Día",
            "📊 3. Resumen y Estadísticas",
            "🏢 4. Directorio de Sucursales"
        ]
    )

# ==========================================
# 4. CONTENIDO PRINCIPAL
# ==========================================
if datos_cargados:
    
    # 1. PLANIFICACIÓN DE RUTAS
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

    # 2. JORNADA DE MOVILIDADES DESAGREGADA POR DÍA
    elif menu_opcion == "⏱️ 2. Jornada de Movilidades por Día":
        st.title("⏱️ Jornada de Trabajo por Movilidad")
        st.caption("Horarios de ingreso, salida y total de horas asignadas a cada unidad por día.")
        st.divider()

        if not df_mov_filtrado.empty:
            dias_unicos_mov = df_mov_filtrado['Día'].unique()
            
            # Selector de pestaña o vista por día
            tabs = st.tabs([f"📅 {d}" for d in dias_unicos_mov])
            
            for tab, dia in zip(tabs, dias_unicos_mov):
                with tab:
                    df_dia = df_mov_filtrado[df_mov_filtrado['Día'] == dia].drop(columns=['Día'])
                    
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.subheader(f"Horarios de Movilidades - {dia}")
                        st.dataframe(
                            df_dia,
                            use_container_width=True,
                            hide_index=True
                        )
                    with c2:
                        st.metric(f"Movilidades Activas ({dia})", len(df_dia))
                        st.info(f"Mostrando únicamente la planificación asignada para el día **{dia}**.")
        else:
            st.warning("No se encontraron registros de movilidades para los días seleccionados.")

    # 3. RESUMEN Y ESTADÍSTICAS
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

    # 4. DIRECTORIO DE SUCURSALES
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
