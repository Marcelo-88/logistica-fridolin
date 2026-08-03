import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS AVANZADOS
# ==========================================
st.set_page_config(
    page_title="Control Logístico | Fridolin",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    
    /* Contenedor de Tarjeta de Ruta */
    .route-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: all 0.2s ease-in-out;
    }
    .route-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    
    /* Badges / Etiquetas */
    .badge-day {
        background-color: #eff6ff;
        color: #1d4ed8;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-cat {
        background-color: #f0fdf4;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-mov {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-time {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 6px 12px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.88rem;
        display: inline-block;
        margin-top: 6px;
    }
    
    /* Secuencia de Paradas */
    .stop-chip {
        display: inline-block;
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 6px 12px;
        margin: 4px 2px;
        font-weight: 500;
        color: #334155;
    }
    .stop-arrow {
        color: #94a3b8;
        font-weight: bold;
        margin: 0 4px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# ==========================================
PUB_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTf5S9qltxreT6S6yCMv-OO8OHYSUCg6kkP8pcSWqKXfOv4ON0hm-7HlBm-hSe0cI2aUBvWVIA5P72h"
GID_RUTAS = "2020862153"
GID_SUCURSALES = "51773579"

URL_RUTAS = f"{PUB_BASE}/pub?single=true&gid={GID_RUTAS}&output=csv"
URL_SUCURSALES = f"{PUB_BASE}/pub?single=true&gid={GID_SUCURSALES}&output=csv"

@st.cache_data(ttl=60)
def cargar_datos_logistica():
    df_raw = pd.read_csv(URL_RUTAS, header=None)
    
    # --- RUTAS DE DISTRIBUCIÓN ---
    df_rutas = df_raw.iloc[:, :15].copy()
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
# 3. FILTROS Y SIDEBAR REDISEÑADO
# ==========================================
if datos_cargados:
    st.sidebar.image("https://em-content.zobj.net/source/apple/354/delivery-truck_1f68a.png", width=45)
    st.sidebar.title("Logística Fridolin")
    st.sidebar.caption("Panel de Control Operativo 2026")
    st.sidebar.divider()

    st.sidebar.subheader("🎯 Filtros Rápidos")

    df_filtrado = df_rutas_raw.copy()
    df_mov_filtrado = df_movilidades_raw.copy()

    col_dia = next((c for c in df_rutas_raw.columns if 'Dí' in c or 'Di' in c or 'dí' in c), None)
    col_cat = next((c for c in df_rutas_raw.columns if 'Cat' in c or 'cat' in c), None)

    # Filtro de Días
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

    # Buscador rápido por sucursal
    busqueda = st.sidebar.text_input("🔍 Buscar Sucursal:", placeholder="Ej. Hipermaxi, Urubó...")
    if busqueda:
        mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]

    st.sidebar.divider()

    # MENÚ REDISEÑADO SIN MÉTRICAS
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
    # VISTA 1: TARJETAS DE RUTA + HORARIO DE SALIDA / RETORNO
    # ----------------------------------------------------
    if menu_opcion == "🎴 1. Tarjetas de Ruta y Horarios":
        st.title("🚚 Planificación de Rutas y Horarios Estimados")
        st.caption("Secuencia visual de paradas junto con su hora de salida y retorno asignados.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rutas en Vista", f"{len(df_filtrado)}")
        col2.metric("Categorías", f"{df_filtrado[col_cat].nunique() if col_cat else 0}")
        col3.metric("Días Filtrados", f"{df_filtrado[col_dia].nunique() if col_dia else 0}")
        st.divider()

        cols_sucursales = [c for c in df_filtrado.columns if 'Sucursal' in c]
        col_mov = next((c for c in df_filtrado.columns if 'Movilidad' in c), None)
        col_frec = next((c for c in df_filtrado.columns if 'Frec' in c or 'frec' in c), None)
        col_com = next((c for c in df_filtrado.columns if 'Comentario' in c), None)

        if len(df_filtrado) == 0:
            st.info("No hay rutas que coincidan con los filtros seleccionados.")

        for idx, row in df_filtrado.iterrows():
            dia = row.get(col_dia, '')
            cat = row.get(col_cat, '')
            mov = row.get(col_mov, '')
            frec = row.get(col_frec, '')
            comentario = row.get(col_com, '')

            # Cruce de hora de salida y retorno desde la tabla de movilidades
            hora_salida = "Sin especificar"
            hora_retorno = "Sin especificar"

            if mov and not df_movilidades_raw.empty:
                # Buscar correspondencia por día y movilidad
                match = df_movilidades_raw[(df_movilidades_raw['Día'] == dia) & (df_movilidades_raw['Num_Mov'] == str(mov))]
                if not match.empty:
                    hora_salida = match.iloc[0]['Ingreso']
                    hora_retorno = match.iloc[0]['Salida']

            # Extraer sucursales reales
            paradas = [str(row[c]).strip() for c in cols_sucursales if str(row[c]).strip() not in ['', 'nan', 'None']]

            # Renderizado de Tarjeta
            with st.container():
                st.markdown(f"""
                    <div class="route-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                            <div>
                                <span class="badge-day">📅 {dia}</span>
                                <span class="badge-cat">📦 {cat}</span>
                                {f'<span class="badge-mov">🚚 Movilidad {mov}</span>' if mov else ''}
                            </div>
                            <small style="color: #64748b; font-weight: 500;">{frec}</small>
                        </div>
                        
                        <!-- BLOQUE DE HORARIOS DE SALIDA Y RETORNO -->
                        <div style="margin-bottom: 12px;">
                            <span class="badge-time">🚀 Salida Planta: <b>{hora_salida}</b> &nbsp;|&nbsp; 🏁 Retorno Estimado: <b>{hora_retorno}</b></span>
                        </div>

                        <!-- SECUENCIA DE PARADAS -->
                        <div style="margin-top: 8px;">
                            <strong style="color: #475569; font-size: 0.9rem;">Secuencia de Recorrido:</strong><br>
                            {' <span class="stop-arrow">➔</span> '.join([f'<span class="stop-chip">📍 {p}</span>' for p in paradas])}
                        </div>
                        
                        {f'<div style="margin-top: 10px; font-size: 0.85rem; color: #d97706; background-color: #fffbeb; padding: 6px 10px; border-radius: 6px;">💡 <b>Nota:</b> {comentario}</div>' if comentario else ''}
                    </div>
                """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # VISTA 2: JORNADA DE MOVILIDADES
    # ----------------------------------------------------
    elif menu_opcion == "⏱️ 2. Jornada de Movilidades":
        st.title("⏱️ Turnos y Horarios por Movilidad")
        st.caption("Detalle completo de turnos por día para los choferes y unidades.")
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
                            st.markdown(f"""
                                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; padding: 12px 16px; border-radius: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="color: #1e293b; font-size: 1.05rem;">🚛 {row['Movilidad']}</strong><br>
                                        <span style="color: #0284c7; font-size: 0.95rem;">🚀 Salida: <b>{row['Ingreso']}</b> &nbsp;|&nbsp; 🏁 Retorno: <b>{row['Salida']}</b></span>
                                    </div>
                                    <div style="background-color: #f1f5f9; padding: 6px 12px; border-radius: 8px; font-weight: 700; color: #0f172a;">
                                        ⏳ {row['Total Horas']} hrs
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    
                    with col_right:
                        st.metric("Movilidades en Servicio", len(df_dia))
                        st.info(f"Programación de salidas y retornos para el **{dia}**.")
        else:
            st.warning("No hay datos de movilidades para los días filtrados.")

    # ----------------------------------------------------
    # VISTA 3: MAPA DE SUCURSALES (EMBED GOOGLE MY MAPS)
    # ----------------------------------------------------
    elif menu_opcion == "🗺️ 3. Mapa de Sucursales":
        st.title("🗺️ Mapa Geográfico de Sucursales")
        st.caption("Ubicación interactiva con nombres, lista desplegable y cobertura de Montero y Santa Cruz.")
        st.divider()

        # Enlace directo al mapa original de Google My Maps
        mapa_url = "https://www.google.com/maps/d/u/0/embed?mid=1vBn4ggLZ2RCm3mSgRoBqMDI_CAlx6wA&ehbc=2E312F"

        # Contenedor iframe para renderizar el mapa idéntico al screenshot
        st.components.v1.iframe(
            src=mapa_url,
            width=1100,
            height=650,
            scrolling=True
        )

        st.caption("💡 *Puedes hacer zoom out para ver la sucursal de Montero o pulsar en la barra lateral izquierda del mapa para filtrar por sucursal.*")
