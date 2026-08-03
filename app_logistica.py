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

    html, body, [class*="css"], .stApp {
        font-family: 'Poppins', sans-serif !important;
        background-color: #fdfbf7 !important;
        color: #2c1e1e;
    }

    .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
    
    h1, h2, h3 {
        color: #800c14 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #f1e9df;
    }

    .route-card {
        background-color: #ffffff;
        border: 1px solid #eeddd0;
        border-left: 5px solid #800c14;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 10px rgba(128, 12, 20, 0.04);
    }

    .route-card-madrugada {
        background-color: #faf5f5;
        border: 1px solid #e5c3c6;
        border-left: 5px solid #4a070c;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(74, 7, 12, 0.08);
    }
    
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

# Función para determinar si una hora pertenece al turno de Madrugada/Noche
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
# 2. CARGA Y LIMPIEZA ROBUSTA DE DATOS
# ==========================================
PUB_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h"
GID_RUTAS = "2020862153"
GID_SUCURSALES = "51773579"

URL_RUTAS = f"{PUB_BASE}/pub?single=true&gid={GID_RUTAS}&output=csv"
URL_SUCURSALES = f"{PUB_BASE}/pub?single=true&gid={GID_SUCURSALES}&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    df_raw = pd.read_csv(URL_RUTAS, header=None)
    
    # --- RUTAS DE DISTRIBUCIÓN (Columnas A a N, incluyendo la Columna N de Movilidad) ---
    # Tomamos hasta la columna N (índice 13)
    df_rutas = df_raw.iloc[:, :14].copy()
    
    # Asignar encabezados desde la fila 0 del Excel
    df_rutas.columns = [str(c).strip() for c in df_rutas.iloc[0]]
    df_rutas = df_rutas[1:].reset_index(drop=True).dropna(how="all")
    
    # Limpieza general de texto en celdas
    for col in df_rutas.columns:
        if pd.notna(col):
            df_rutas[col] = df_rutas[col].astype(str).str.strip().replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    df_rutas = df_rutas.loc[:, df_rutas.columns.notna()]
    df_rutas = df_rutas.loc[:, ~df_rutas.columns.str.startswith('Unnamed')]

    # --- MOVILIDADES Y HORARIOS POR DÍA (Jornadas) ---
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
    st.error(f"⚠️ Error al cargar los datos: {e}")
    datos_cargados = False

# ==========================================
# 3. IDENTIFICACIÓN EXACTA DE COLUMNAS
# ==========================================
if datos_cargados:
    col_dia = next((c for c in df_rutas_raw.columns if any(k in str(c).lower() for k in ['dí', 'dia'])), df_rutas_raw.columns[0])
    col_cat = next((c for c in df_rutas_raw.columns if 'cat' in str(c).lower()), None)
    
    # Identificar la Columna N de Movilidad por nombre exacto o posición
    col_mov = None
    for c in df_rutas_raw.columns:
        if 'movilidad' in str(c).lower():
            col_mov = c
            break
            
    # Si no la encontró por nombre, asignamos por la última columna cargada de la tabla (Columna N)
    if not col_mov and len(df_rutas_raw.columns) >= 14:
        col_mov = df_rutas_raw.columns[13]

    col_h_salida = next((c for c in df_rutas_raw.columns if any(k in str(c).lower() for k in ['hora_sal', 'salida'])), None)
    col_h_retorno = next((c for c in df_rutas_raw.columns if any(k in str(c).lower() for k in ['hora_ret', 'retorno'])), None)

    # ==========================================
    # 4. FILTROS Y SIDEBAR
    # ==========================================
    try:
        st.sidebar.image("Fridolin_logo.jpg", use_container_width=True)
    except Exception:
        st.sidebar.markdown("<h2 style='color: #800c14; margin-bottom: 0;'>🧁 Fridolin</h2>", unsafe_allow_html=True)
        
    st.sidebar.caption("Sistema de Control Logístico y Distribución")
    st.sidebar.divider()

    st.sidebar.subheader("🎯 Filtros Rápidos")

    df_filtrado = df_rutas_raw.copy()
    df_mov_filtrado = df_movilidades_raw.copy()

    # 1. Filtro de Días
    if col_dia and col_dia in df_rutas_raw.columns:
        dias_disponibles = [d for d in df_rutas_raw[col_dia].unique() if d and str(d).strip() not in ['nan', 'None', '']]
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
        cats_disponibles = [c for c in df_rutas_raw[col_cat].unique() if c and str(c).strip() not in ['nan', 'None', '']]
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
            "⚖️ 2. Comparador de Movilidades",
            "⏱️ 3. Jornada de Movilidades",
            "🗺️ 4. Mapa de Sucursales"
        ]
    )

# Función auxiliar para renderizar una tarjeta de ruta
def renderizar_tarjeta_ruta(row, col_dia, col_cat, col_mov, col_frec, col_com, col_h_salida, col_h_retorno, cols_sucursales):
    dia = row.get(col_dia, '')
    cat = row.get(col_cat, '')
    mov = row.get(col_mov, '')
    frec = row.get(col_frec, '')
    comentario = str(row.get(col_com, '')).strip()

    hora_salida = row.get(col_h_salida, 'Sin especificar') if col_h_salida else 'Sin especificar'
    hora_retorno = row.get(col_h_retorno, 'Sin especificar') if col_h_retorno else 'Sin especificar'

    if not hora_salida or hora_salida in ['nan', 'None']:
        hora_salida = "Sin especificar"
    if not hora_retorno or hora_retorno in ['nan', 'None']:
        hora_retorno = "Sin especificar"

    es_madrugada = es_salida_madrugada(hora_salida)

    card_class = "route-card-madrugada" if es_madrugada else "route-card"
    badge_time_class = "badge-time-madrugada" if es_madrugada else "badge-time"
    icono_salida = "🌙 Salida Planta" if es_madrugada else "🚀 Salida Planta"

    paradas = [str(row[c]).strip() for c in cols_sucursales if str(row[c]).strip() not in ['', 'nan', 'None']]
    html_paradas = ' <span class="stop-arrow">➔</span> '.join([f'<span class="stop-chip">📍 {p}</span>' for p in paradas])

    txt_mov = f"Movilidad {mov}" if not str(mov).lower().startswith("movilidad") else mov
    badge_mov_html = f'<span class="badge-mov">🚚 {txt_mov}</span>' if mov and mov not in ['nan', 'None'] else ''
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

# ==========================================
# 5. VISTAS INTERACTIVAS
# ==========================================
if datos_cargados:

    # ----------------------------------------------------
    # VISTA 1: TARJETAS DE RUTA Y HORARIOS
    # ----------------------------------------------------
    if menu_opcion == "🎴 1. Tarjetas de Ruta y Horarios":
        st.title("🚚 Planificación de Rutas y Horarios")
        st.caption("Gestión operativa de despachos desde Planta hacia Sucursales.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rutas Activas", f"{len(df_filtrado)}")
        col2.metric("Categorías", f"{df_filtrado[col_cat].nunique() if col_cat else 0}")
        col3.metric("Días Visibles", f"{df_filtrado[col_dia].nunique() if col_dia else 0}")
        st.divider()

        cols_sucursales = [c for c in df_filtrado.columns if 'Sucursal' in str(c)]
        col_frec = next((c for c in df_filtrado.columns if 'frec' in str(c).lower()), None)
        col_com = next((c for c in df_filtrado.columns if 'comentario' in str(c).lower()), None)

        if len(df_filtrado) == 0:
            st.info("No se encontraron rutas para los filtros seleccionados.")

        for idx, row in df_filtrado.iterrows():
            renderizar_tarjeta_ruta(row, col_dia, col_cat, col_mov, col_frec, col_com, col_h_salida, col_h_retorno, cols_sucursales)

    # ----------------------------------------------------
    # VISTA 2: COMPARADOR DE MOVILIDADES (CORREGIDO Y AGRUPADO)
    # ----------------------------------------------------
    elif menu_opcion == "⚖️ 2. Comparador de Movilidades":
        st.title("⚖️ Comparador Lado a Lado de Movilidades")
        st.caption("Compara el itinerario de dos unidades para evaluar fusión, reasignación o combinación de rutas.")

        cols_sucursales = [c for c in df_rutas_raw.columns if 'Sucursal' in str(c)]
        col_frec = next((c for c in df_rutas_raw.columns if 'frec' in str(c).lower()), None)
        col_com = next((c for c in df_rutas_raw.columns if 'comentario' in str(c).lower()), None)
        
        # Obtenemos todos los números de movilidad únicos válidos desde la Columna N
        movs_valores = df_rutas_raw[col_mov].dropna().astype(str).str.strip().unique()
        movs_validas = sorted([m for m in movs_valores if m in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']])

        if not movs_validas:
            st.warning("⚠️ No se encontraron números de movilidad en la columna N.")
        else:
            # Construir opciones del dropdown (Ej: "Movilidad 1", "Movilidad 2"...)
            opciones_mov = [f"Movilidad {m}" for m in movs_validas]
            mapa_mov_original = {f"Movilidad {m}": m for m in movs_validas}

            # Selección de Día
            dias_lista = [d for d in df_rutas_raw[col_dia].unique() if d and str(d).strip() not in ['nan', 'None', '']]
            dia_comp = st.selectbox("📅 Selecciona el Día a Analizar:", options=dias_lista)

            # Filtrar por el día seleccionado
            df_dia_base = df_rutas_raw[df_rutas_raw[col_dia] == dia_comp]

            st.divider()

            col_left, col_right = st.columns(2)

            # --- COLUMNA IZQUIERDA: MOVILIDAD A ---
            with col_left:
                st.subheader("🚛 Movilidad A")
                mov_a_label = st.selectbox("Selecciona Movilidad A:", options=opciones_mov, index=0, key="mov_a")
                
                if mov_a_label:
                    val_orig_a = mapa_mov_original[mov_a_label]
                    df_mov_a = df_dia_base[df_dia_base[col_mov].astype(str).str.strip() == str(val_orig_a)]
                    
                    # Cargar info de jornada (Vista 3)
                    if not df_movilidades_raw.empty:
                        jornada_a = df_movilidades_raw[(df_movilidades_raw['Día'] == dia_comp) & (df_movilidades_raw['Num_Mov'].astype(str).str.strip() == str(val_orig_a))]
                        if not jornada_a.empty:
                            ing_a = jornada_a.iloc[0]['Ingreso']
                            sal_a = jornada_a.iloc[0]['Salida']
                            tot_a = jornada_a.iloc[0]['Total Horas']
                            st.info(f"⏱️ **Jornada en Planta:** {ing_a} a {sal_a} ({tot_a} hrs)")

                    st.metric("Rutas Programadas", len(df_mov_a))

                    if len(df_mov_a) == 0:
                        st.warning(f"No hay rutas asignadas para {mov_a_label} el día {dia_comp}.")
                    else:
                        for _, row in df_mov_a.iterrows():
                            renderizar_tarjeta_ruta(row, col_dia, col_cat, col_mov, col_frec, col_com, col_h_salida, col_h_retorno, cols_sucursales)

            # --- COLUMNA DERECHA: MOVILIDAD B ---
            with col_right:
                st.subheader("🚛 Movilidad B")
                idx_b = 1 if len(opciones_mov) > 1 else 0
                mov_b_label = st.selectbox("Selecciona Movilidad B:", options=opciones_mov, index=idx_b, key="mov_b")
                
                if mov_b_label:
                    val_orig_b = mapa_mov_original[mov_b_label]
                    df_mov_b = df_dia_base[df_dia_base[col_mov].astype(str).str.strip() == str(val_orig_b)]
                    
                    # Cargar info de jornada (Vista 3)
                    if not df_movilidades_raw.empty:
                        jornada_b = df_movilidades_raw[(df_movilidades_raw['Día'] == dia_comp) & (df_movilidades_raw['Num_Mov'].astype(str).str.strip() == str(val_orig_b))]
                        if not jornada_b.empty:
                            ing_b = jornada_b.iloc[0]['Ingreso']
                            sal_b = jornada_b.iloc[0]['Salida']
                            tot_b = jornada_b.iloc[0]['Total Horas']
                            st.info(f"⏱️ **Jornada en Planta:** {ing_b} a {sal_b} ({tot_b} hrs)")

                    st.metric("Rutas Programadas", len(df_mov_b))

                    if len(df_mov_b) == 0:
                        st.warning(f"No hay rutas asignadas para {mov_b_label} el día {dia_comp}.")
                    else:
                        for _, row in df_mov_b.iterrows():
                            renderizar_tarjeta_ruta(row, col_dia, col_cat, col_mov, col_frec, col_com, col_h_salida, col_h_retorno, cols_sucursales)

    # ----------------------------------------------------
    # VISTA 3: JORNADA DE MOVILIDADES
    # ----------------------------------------------------
    elif menu_opcion == "⏱️ 3. Jornada de Movilidades":
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
    # VISTA 4: MAPA DE SUCURSALES
    # ----------------------------------------------------
    elif menu_opcion == "🗺️ 4. Mapa de Sucursales":
        st.title("🗺️ Mapa Geográfico de Sucursales")
        st.caption("Ubicación e interacción espacial con la red de sucursales Fridolin.")
        st.divider()

        MAP_ID = "1vBn4ggLZ2RCm3mSgRoBqMDI_CAlx6wA"
        mapa_embed_url = f"https://www.google.com/maps/d/embed?mid={MAP_ID}&ehbc=2E312F"
        mapa_directo_url = f"https://www.google.com/maps/d/viewer?mid={MAP_ID}"

        col_map1, col_map2 = st.columns([3, 1])
        with col_map1:
            st.info("💡 Mapa interactivo de la red logística de Fridolin.")
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
