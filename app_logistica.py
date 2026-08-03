import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN Y PALETA DE COLOR FRIDOLIN
# ==========================================
st.set_page_config(
    page_title="Control Logístico | Fridolin",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados con la línea gráfica oficial de Fridolin
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Tipografía Global y Fondo de Aplicación */
    html, body, [class*="css"], .stApp {
        font-family: 'Poppins', sans-serif !important;
        background-color: #fdfbf7 !important;
        color: #2c1e1e;
    }

    .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
    
    /* Headers / Títulos Principales */
    h1, h2, h3 {
        color: #800c14 !important;
        font-weight: 700 !important;
    }

    /* Estilo del Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #f1e9df;
    }

    /* Contenedor de Tarjeta Estándar (Fridolin) */
    .route-card {
        background-color: #ffffff;
        border: 1px solid #eeddd0;
        border-left: 5px solid #800c14;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 10px rgba(128, 12, 20, 0.04);
    }

    /* Contenedor de Tarjeta Madrugada / Turno Noche */
    .route-card-madrugada {
        background-color: #faf5f5;
        border: 1px solid #e5c3c6;
        border-left: 5px solid #4a070c;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(74, 7, 12, 0.08);
    }
    
    /* Badges / Etiquetas con estilo Fridolin */
    .badge-day {
        background-color: #fce8e9;
        color: #800c14;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-cat {
        background-color: #fef7e7;
        color: #8a6411;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #f5e4b8;
    }
    .badge-mov {
        background-color: #f4efe9;
        color: #5c4436;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    /* Badges de Horarios */
    .badge-time {
        background-color: #800c14;
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .badge-time-madrugada {
        background-color: #3b0609;
        color: #f7dcdb;
        padding: 6px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
        margin-top: 8px;
        margin-bottom: 8px;
        border: 1px solid #6e1016;
    }
    
    /* Chips de Paradas/Sucursales */
    .stop-chip {
        display: inline-block;
        background-color: #fdfbf7;
        border: 1px solid #e3d5c5;
        border-radius: 8px;
        padding: 6px 12px;
        margin: 4px 2px;
        font-weight: 500;
        color: #2c1e1e;
    }
    .stop-arrow {
        color: #c89b3c;
        font-weight: bold;
        margin: 0 4px;
    }

    /* Personalización de Métricas y Botones Streamlit */
    [data-testid="stMetricValue"] {
        color: #800c14 !important;
        font-weight: 700 !important;
    }

    .stButton>button {
        background-color: #800c14 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover {
        background-color: #63080e !important;
    }
    </style>
""", unsafe_allow_html=True)

# Función para determinar si una hora pertenece al turno de Madrugada/Noche (< 07:00 AM o >= 22:00)
def es_salida_madrugada(hora_str):
    if not hora_str or str(hora_str).strip() in ["Sin especificar", "nan", "None", ""]:
        return False
    try:
        hora_clean = str(hora_str).strip()
        partes = hora_clean.split(":")
        hora_num = int(partes[0])
        return hora_num < 7 or hora_num >= 22
    except Exception:
        return False

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
PUB_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h"
GID_RUTAS = "2020862153"
GID_SUCURSALES = "51773579"

URL_RUTAS = f"{PUB_BASE}/pub?single=true&gid={GID_RUTAS}&output=csv"
URL_SUCURSALES = f"{PUB_BASE}/pub?single=true&gid={GID_SUCURSALES}&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    df_raw = pd.read_csv(URL_RUTAS, header=None)
    
    # --- RUTAS DE DISTRIBUCIÓN (Columnas A a M) ---
    df_rutas = df_raw.iloc[:, :13].copy()
    df_rutas.columns = df_rutas.iloc[0]
    df_rutas = df_rutas[1:].reset_index(drop=True).dropna(how="all")
    
    for col in df_rutas.columns:
        if pd.notna(col):
            df_rutas[col] = df_rutas[col].astype(str).str.strip().replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    df_rutas = df_rutas.loc[:, df_rutas.columns.notna()]
    df_rutas = df_rutas.loc[:, ~df_rutas.columns.str.startswith('Unnamed')]

    # --- MOVILIDADES Y HORARIOS POR DÍA ---
    bloques_movilidades = []
    if df_raw.shape[1] >= 20:
        dia_actual = "Lunes"
        for idx in range(1, len(df_raw)):
            val_dia = str(df_raw.iloc[idx, 0]).strip()
            if val_dia in ['Lunes', 'Martes', 'Miércoles', 'Miercoles', 'Jueves', 'Viernes', 'Sábado', 'Sabado', 'Domingo']:
                dia_actual = val_dia
            
            mov = str(df_raw.iloc[idx, 16]).strip()
            ingreso = str(df_raw.iloc[idx, 17]).strip()
            salida = str(df_raw.iloc[idx, 18]).strip()
            total = str(df_raw.iloc[idx, 19]).strip()

            if mov in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                bloques_movilidades.append({
                    'Día': dia_actual,
                    'Movilidad': f"Movilidad {mov}",
                    'Num_Mov': mov,
                    'Ingreso': ingreso if ingreso not in ['nan', 'None'] else '',
                    'Salida': salida if salida not in ['nan', 'None'] else '',
                    'Total Horas': total if total not in ['nan', 'None'] else ''
                })

    df_movilidades = pd.DataFrame(bloques_movilidades)

    # --- SUCURSALES ---
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
    st.error(f"⚠️ Error al procesar los datos: {e}")
    datos_cargados = False

# ==========================================
# 3. FILTROS Y SIDEBAR (ESTILO FRIDOLIN)
# ==========================================
if datos_cargados:
    # Carga del Logo oficial o Título alternativo
    try:
        st.sidebar.image("Fridolin_logo.jpg", use_container_width=True)
    except Exception:
        st.sidebar.markdown("<h2 style='color: #800c14; margin-bottom: 0;'>🧁 Fridolin</h2>", unsafe_allow_html=True)
        
    st.sidebar.caption("Sistema de Control Logístico y Distribución")
    st.sidebar.divider()

    st.sidebar.subheader("🎯 Filtros Rápidos")

    df_filtrado = df_rutas_raw.copy()
    df_mov_filtrado = df_movilidades_raw.copy()

    col_dia = next((c for c in df_rutas_raw.columns if 'Dí' in c or 'Di' in c or 'dí' in c), None)
    col_cat = next((c for c in df_rutas_raw.columns if 'Cat' in c or 'cat' in c), None)
    col_mov = next((c for c in df_rutas_raw.columns if 'Movilidad' in c), None)
    col_h_salida = next((c for c in df_rutas_raw.columns if 'Hora_Sal' in c or 'Salida' in c or 'Hora_sal' in c), None)
    col_h_retorno = next((c for c in df_rutas_raw.columns if 'Hora_Ret' in c or 'Retorno' in c or 'Hora_ret' in c), None)

    # 1. Filtro de Días
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

    # 2. Filtro Categorías
    if col_cat and col_cat in df_rutas_raw.columns:
        cats_disponibles = [c for c in df_rutas_raw[col_cat].unique() if c and c != 'nan']
        cats_seleccionadas = st.sidebar.multiselect(
            "📦 Categoría(s):",
            options=cats_disponibles,
            placeholder="Todas las categorías"
        )
        if cats_seleccionadas:
            df_filtrado = df_filtrado[df_filtrado[col_cat].isin(cats_seleccionadas)]

    # 3. Filtro Horario
    filtro_horario = st.sidebar.selectbox(
        "⏰ Horario de Salida:",
        options=["Todas las rutas", "🌙 Madrugada / Noche (22:00 - 07:00 AM)", "☀️ Mañana / Día (07:00 AM - 21:59)"]
    )

    if filtro_horario != "Todas las rutas" and col_h_salida:
        if filtro_horario == "🌙 Madrugada / Noche (22:00 - 07:00 AM)":
            df_filtrado = df_filtrado[df_filtrado[col_h_salida].apply(es_salida_madrugada)]
            if not df_mov_filtrado.empty:
                df_mov_filtrado = df_mov_filtrado[df_mov_filtrado['Ingreso'].apply(es_salida_madrugada)]
        else:
            df_filtrado = df_filtrado[~df_filtrado[col_h_salida].apply(es_salida_madrugada)]
            if not df_mov_filtrado.empty:
                df_mov_filtrado = df_mov_filtrado[~df_mov_filtrado['Ingreso'].apply(es_salida_madrugada)]

    # 4. Buscador por sucursal
    busqueda = st.sidebar.text_input("🔍 Buscar Sucursal:", placeholder="Ej. Hipermaxi, Urubó...")
    if busqueda:
        mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]

    st.sidebar.divider()

    menu_opcion = st.sidebar.radio(
        "📌 Modo de Vista:",
        [
            "🎴 1. Tarjetas de Ruta y Horarios",
            "⏱️ 2. Jornada de Movilidades",
            "🗺️ 3. Mapa de Sucursales"
        ]
    )

# ==========================================
# 4. VISTAS INTERACTIVAS
# ==========================================
if datos_cargados:

    # ----------------------------------------------------
    # VISTA 1: TARJETAS DE RUTA Y HORARIOS (ESTILO FRIDOLIN)
    # ----------------------------------------------------
    if menu_opcion == "🎴 1. Tarjetas de Ruta y Horarios":
        st.title("🚚 Planificación de Rutas y Horarios")
        st.caption("Gestión operativa de despachos desde Planta hacia Sucursales.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rutas Activas", f"{len(df_filtrado)}")
        col2.metric("Categorías", f"{df_filtrado[col_cat].nunique() if col_cat else 0}")
        col3.metric("Días Visibles", f"{df_filtrado[col_dia].nunique() if col_dia else 0}")
        st.divider()

        cols_sucursales = [c for c in df_filtrado.columns if 'Sucursal' in c]
        col_frec = next((c for c in df_filtrado.columns if 'Frec' in c or 'frec' in c), None)
        col_com = next((c for c in df_filtrado.columns if 'Comentario' in c), None)

        if len(df_filtrado) == 0:
            st.info("No se encontraron rutas para los filtros seleccionados.")

        for idx, row in df_filtrado.iterrows():
            dia = row.get(col_dia, '')
            cat = row.get(col_cat, '')
            mov = row.get(col_mov, '')
            frec = row.get(col_frec, '')
            comentario = str(row.get(col_com, '')).strip()

            # Extracción desde Columnas K y L
            hora_salida = row.get(col_h_salida, 'Sin especificar') if col_h_salida else 'Sin especificar'
            hora_retorno = row.get(col_h_retorno, 'Sin especificar') if col_h_retorno else 'Sin especificar'

            if not hora_salida or hora_salida in ['nan', 'None']:
                hora_salida = "Sin especificar"
            if not hora_retorno or hora_retorno in ['nan', 'None']:
                hora_retorno = "Sin especificar"

            # Madrugada / Noche (< 7:00 AM o >= 22:00)
            es_madrugada = es_salida_madrugada(hora_salida)

            card_class = "route-card-madrugada" if es_madrugada else "route-card"
            badge_time_class = "badge-time-madrugada" if es_madrugada else "badge-time"
            icono_salida = "🌙 Salida Planta" if es_madrugada else "🚀 Salida Planta"

            paradas = [str(row[c]).strip() for c in cols_sucursales if str(row[c]).strip() not in ['', 'nan', 'None']]
            html_paradas = ' <span class="stop-arrow">➔</span> '.join([f'<span class="stop-chip">📍 {p}</span>' for p in paradas])

            badge_mov_html = f'<span class="badge-mov">🚚 Movilidad {mov}</span>' if mov and mov not in ['nan', 'None'] else ''
            nota_html = f'<div style="margin-top:10px; font-size:0.85rem; color:#8a6411; background-color:#fef7e7; padding:6px 12px; border-radius:6px; border:1px solid #f5e4b8;">💡 <b>Nota:</b> {comentario}</div>' if comentario and comentario not in ['nan', 'None'] else ''

            card_html = (
                f'<div class="{card_class}">'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<div><span class="badge-day">📅 {dia}</span> <span class="badge-cat">📦 {cat}</span> {badge_mov_html}</div>'
                f'<small style="color:#786565; font-weight:500;">{frec}</small>'
                f'</div>'
                f'<div><span class="{badge_time_class}">{icono_salida}: <b>{hora_salida}</b> &nbsp;|&nbsp; 🏁 Retorno Estimado: <b>{hora_retorno}</b></span></div>'
                f'<div style="margin-top:8px;"><strong style="color:#523e3e; font-size:0.9rem;">Secuencia de Recorrido:</strong><br>{html_paradas}</div>'
                f'{nota_html}'
                f'</div>'
            )

            st.markdown(card_html, unsafe_allow_html=True)

    # ----------------------------------------------------
    # VISTA 2: JORNADA DE MOVILIDADES
    # ----------------------------------------------------
    elif menu_opcion == "⏱️ 2. Jornada de Movilidades":
        st.title("⏱️ Turnos y Horarios por Movilidad")
        st.caption("Programación de choferes y unidades de transporte.")
        st.divider()

        if not df_mov_filtrado.empty:
            dias_mov = df_mov_filtrado['Día'].unique()
            tabs = st.tabs([f"📅 {d}" for d in dias_mov])

            for tab, dia in zip(tabs, dias_mov):
                with tab:
                    df_dia = df_mov_filtrado[df_mov_filtrado['Día'] == dia]
                    
                    col_left, col_right = st.columns([2, 1])
                    
                    with col_left:
                        for _, row in df_dia.iterrows():
                            es_mad = es_salida_madrugada(row["Ingreso"])
                            ico = "🌙 Madrugada" if es_mad else "🚀 Salida"
                            col_txt = "#4a070c" if es_mad else "#800c14"
                            
                            mov_item_html = (
                                f'<div style="background-color:#ffffff; border:1px solid #eeddd0; border-left:4px solid #800c14; padding:12px 16px; border-radius:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">'
                                f'<div><strong style="color:#2c1e1e; font-size:1.05rem;">🚛 {row["Movilidad"]}</strong><br>'
                                f'<span style="color:{col_txt}; font-size:0.95rem;">{ico}: <b>{row["Ingreso"]}</b> &nbsp;|&nbsp; 🏁 Retorno: <b>{row["Salida"]}</b></span></div>'
                                f'<div style="background-color:#fce8e9; color:#800c14; padding:6px 14px; border-radius:8px; font-weight:700;">⏳ {row["Total Horas"]} hrs</div>'
                                f'</div>'
                            )
                            st.markdown(mov_item_html, unsafe_allow_html=True)
                    
                    with col_right:
                        st.metric("Movilidades en Servicio", len(df_dia))
                        st.info(f"Programación diaria de transporte para el **{dia}**.")
        else:
            st.warning("No hay datos de movilidades disponibles para los filtros actuales.")

    # ----------------------------------------------------
    # VISTA 3: MAPA DE SUCURSALES
    # ----------------------------------------------------
    elif menu_opcion == "🗺️ 3. Mapa de Sucursales":
        st.title("🗺️ Mapa Geográfico de Sucursales")
        st.caption("Ubicación e interacción espacial con la red de sucursales Fridolin.")
        st.divider()

        MAP_ID = "1vBn4ggLZ2RCm3mSgRoBqMDI_CAlx6wA"
        mapa_embed_url = f"https://www.google.com/maps/d/embed?mid={MAP_ID}&ehbc=2E312F"
        mapa_directo_url = f"https://www.google.com/maps/d/viewer?mid={MAP_ID}"

        col_map1, col_map2 = st.columns([3, 1])
        with col_map1:
            st.info("💡 Una vez que el propietario te transfiera el mapa o habilite el permiso 'Público / Cualquier persona con el enlace', se desplegará en este espacio.")
        with col_map2:
            st.link_button("↗️ Abrir en Google Maps", mapa_directo_url, use_container_width=True)

        html_iframe = f"""
            <iframe 
                src="{mapa_embed_url}" 
                width="100%" 
                height="600" 
                style="border:0; border-radius:12px;" 
                allowfullscreen="" 
                loading="lazy">
            </iframe>
        """
        st.components.v1.html(html_iframe, height=620)
