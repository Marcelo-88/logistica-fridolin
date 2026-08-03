import streamlit as st
import pandas as pd
import unicodedata
import urllib.parse
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

# ==========================================
# 1. CONFIGURACIÓN Y PALETA DE COLOR FRIDOLIN
# ==========================================
st.set_page_config(
    page_title="Control Logístico | Fridolin",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
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

    /* Tarjetas individuales de rutas */
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

    /* Tarjeta General Comparador */
    .general-mov-card {
        background-color: #ffffff;
        border: 1px solid #e0cfc2;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* Tarjeta Resumen Semanal de Jornada */
    .weekly-summary-card {
        background-color: #ffffff;
        border: 1px solid #e2d1c3;
        border-top: 4px solid #800c14;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 16px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.04);
    }

    .salida-block {
        background-color: #fcf9f5;
        border-left: 4px solid #800c14;
        border-radius: 8px;
        padding: 12px 14px;
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .salida-block-madrugada {
        background-color: #f7ebeb;
        border-left: 4px solid #4a070c;
        border-radius: 8px;
        padding: 12px 14px;
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .badge-day {
        background-color: #fce8e9;
        color: #800c14;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.82rem;
    }
    .badge-cat {
        background-color: #fef7e7;
        color: #8a6411;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.82rem;
        border: 1px solid #f5e4b8;
    }
    .badge-mov {
        background-color: #f4efe9;
        color: #5c4436;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.82rem;
    }
    
    .badge-time {
        background-color: #800c14;
        color: #ffffff;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 4px;
        margin-bottom: 6px;
    }

    .badge-time-madrugada {
        background-color: #3b0609;
        color: #f7dcdb;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 4px;
        margin-bottom: 6px;
        border: 1px solid #6e1016;
    }
    
    .stop-chip {
        display: inline-block;
        background-color: #ffffff;
        border: 1px solid #e3d5c5;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 3px 2px;
        font-weight: 500;
        font-size: 0.85rem;
        color: #2c1e1e;
    }
    .stop-arrow {
        color: #c89b3c;
        font-weight: bold;
        margin: 0 4px;
    }

    .day-hour-pill {
        display: inline-block;
        background-color: #f8f1eb;
        border: 1px solid #ebd3c2;
        border-radius: 6px;
        padding: 4px 8px;
        margin: 3px 2px;
        font-size: 0.8rem;
        color: #422d2d;
    }

    [data-testid="stMetricValue"] {
        color: #800c14 !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Normalizador de días
def normalizar_dia(dia_str):
    if not dia_str or pd.isna(dia_str):
        return ""
    txt = str(dia_str).strip()
    txt_nfkd = unicodedata.normalize('NFKD', txt)
    txt_sin_acento = "".join([c for c in txt_nfkd if not unicodedata.combining(c)])
    txt_clean = txt_sin_acento.capitalize()
    
    mapeo = {
        "Lunes": "Lunes",
        "Martes": "Martes",
        "Miercoles": "Miércoles",
        "Jueves": "Jueves",
        "Viernes": "Viernes",
        "Sabado": "Sábado",
        "Domingo": "Domingo"
    }
    return mapeo.get(txt_clean, txt_clean)

# Determina si una hora pertenece al turno de Madrugada/Noche
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

# Convierte texto de horas tipo "12:15:00 hrs" a decimal
def parse_horas_a_decimal(cadena_horas):
    if not cadena_horas or pd.isna(cadena_horas):
        return 0.0
    txt = str(cadena_horas).lower().replace('hrs', '').replace('hr', '').replace('h', '').strip()
    try:
        partes = txt.split(':')
        h = float(partes[0])
        m = float(partes[1]) if len(partes) > 1 else 0.0
        return h + (m / 60.0)
    except Exception:
        return 0.0

# Formatea flotante a string (ej. 7.66 -> "7:40:00")
def decimal_a_horas_str(horas_dec):
    if horas_dec <= 0:
        return "0:00:00"
    h = int(horas_dec)
    m = int(round((horas_dec - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h}:{m:02d}:00"

# Función Robusta para Consultar IA (Resuelve 404 y 429)
def generar_respuesta_ia(prompt):
    modelos_candidatos = [
        'models/gemini-2.0-flash',
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-8b',
        'gemini-2.0-flash',
        'gemini-1.5-flash'
    ]
    
    # Intenta obtener la lista activa desde la API
    try:
        modelos_api = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        if modelos_api:
            # Priorizar modelos Flash
            modelos_flash = [m for m in modelos_api if 'flash' in m.lower()]
            modelos_candidatos = modelos_flash + [m for m in modelos_api if m not in modelos_flash]
    except Exception:
        pass  # Si falla list_models usa la lista estática candidatos

    ultimo_error = None
    for mod in modelos_candidatos:
        try:
            m = genai.GenerativeModel(mod)
            res = m.generate_content(prompt)
            return res.text
        except ResourceExhausted:
            continue
        except GoogleAPIError as e:
            if "404" in str(e) or "429" in str(e) or "not found" in str(e).lower():
                ultimo_error = e
                continue
            else:
                raise e
        except Exception as e:
            ultimo_error = e
            continue
            
    raise Exception(f"No fue posible conectar con los modelos de IA. Detalle: {ultimo_error}")

# ==========================================
# 2. CARGA Y LIMPIEZA DE DATOS
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
    df_rutas = df_raw.iloc[:, :14].copy()
    df_rutas.columns = [str(c).strip() for c in df_rutas.iloc[0]]
    df_rutas = df_rutas[1:].reset_index(drop=True).dropna(how="all")
    
    for col in df_rutas.columns:
        if pd.notna(col):
            df_rutas[col] = df_rutas[col].astype(str).str.strip().replace({'nan': '', 'None': '', 'NaN': '', '<NA>': ''})

    df_rutas = df_rutas.loc[:, df_rutas.columns.notna()]
    df_rutas = df_rutas.loc[:, ~df_rutas.columns.str.startswith('Unnamed')]

    col_d = next((c for c in df_rutas.columns if any(k in str(c).lower() for k in ['dí', 'dia'])), df_rutas.columns[0])
    df_rutas[col_d] = df_rutas[col_d].apply(normalizar_dia)

    # --- JORNADAS Y HORARIOS DE MOVILIDADES ---
    bloques_movilidades = []
    if df_raw.shape[1] >= 20:
        dia_actual = "Lunes"
        for idx in range(1, len(df_raw)):
            val_dia_raw = str(df_raw.iloc[idx, 0]).strip()
            dia_norm = normalizar_dia(val_dia_raw)
            if dia_norm in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']:
                dia_actual = dia_norm
            
            mov = str(df_raw.iloc[idx, 16]).strip()
            ingreso = str(df_raw.iloc[idx, 17]).strip()
            salida = str(df_raw.iloc[idx, 18]).strip()
            total = str(df_raw.iloc[idx, 19]).strip()

            if mov in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                dia_asignado = dia_actual
                
                if mov == '1' and dia_actual == 'Domingo' and ingreso.startswith('22:'):
                    dia_asignado = 'Lunes'
                elif mov == '1' and dia_actual == 'Viernes' and ingreso.startswith('22:'):
                    dia_asignado = 'Sábado'

                bloques_movilidades.append({
                    'Día': dia_asignado,
                    'Día_Original': dia_actual,
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
# 3. IDENTIFICACIÓN DE COLUMNAS
# ==========================================
if datos_cargados:
    col_dia = next((c for c in df_rutas_raw.columns if any(k in str(c).lower() for k in ['dí', 'dia'])), df_rutas_raw.columns[0])
    col_cat = next((c for c in df_rutas_raw.columns if 'cat' in str(c).lower()), None)
    
    col_mov = None
    for c in df_rutas_raw.columns:
        if 'movilidad' in str(c).lower():
            col_mov = c
            break
            
    if not col_mov and len(df_rutas_raw.columns) >= 14:
        col_mov = df_rutas_raw.columns[13]

    col_h_salida = next((c for c in df_rutas_raw.columns if any(k in str(c).lower() for k in ['hora_sal', 'salida'])), None)
    col_h_retorno = next((c for c in df_rutas_raw.columns if any(k in str(c).lower() for k in ['hora_ret', 'retorno'])), None)

    def obtener_jornada_flexible(df_mov_raw, dia_filtro, num_movidad):
        if df_mov_raw.empty:
            return None
            
        num_str = str(num_movidad).strip()
        match = df_mov_raw[(df_mov_raw['Día'] == dia_filtro) & (df_mov_raw['Num_Mov'].astype(str).str.strip() == num_str)]
        if not match.empty and match.iloc[0]['Ingreso'] != "":
            return match.iloc[0]

        dias_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        if dia_filtro in dias_orden:
            idx_dia = dias_orden.index(dia_filtro)
            dia_previo = dias_orden[idx_dia - 1]
            match_prev = df_mov_raw[(df_mov_raw['Día'] == dia_previo) & (df_mov_raw['Num_Mov'].astype(str).str.strip() == num_str)]
            if not match_prev.empty and match_prev.iloc[0]['Ingreso'] != "":
                return match_prev.iloc[0]

        return None

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

    dias_ordenados = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dias_en_datos = [d for d in df_rutas_raw[col_dia].unique() if d and str(d).strip() not in ['nan', 'None', '']]
    dias_disponibles = [d for d in dias_ordenados if d in dias_en_datos]

    dias_seleccionados = st.sidebar.multiselect(
        "📅 Seleccionar Día(s):",
        options=dias_disponibles,
        placeholder="Todos los días"
    )
    if dias_seleccionados:
        df_filtrado = df_filtrado[df_filtrado[col_dia].isin(dias_seleccionados)]
        if not df_mov_filtrado.empty:
            df_mov_filtrado = df_mov_filtrado[df_mov_filtrado['Día'].isin(dias_seleccionados)]

    if col_cat and col_cat in df_rutas_raw.columns:
        cats_disponibles = sorted([c for c in df_rutas_raw[col_cat].unique() if c and str(c).strip() not in ['nan', 'None']])
        cats_seleccionadas = st.sidebar.multiselect(
            "📦 Categoría(s):",
            options=cats_disponibles,
            placeholder="Todas las categorías"
        )
        if cats_seleccionadas:
            df_filtrado = df_filtrado[df_filtrado[col_cat].isin(cats_seleccionadas)]

    filtro_horario = st.sidebar.selectbox(
        "⏰ Horario de Salida:",
        options=["Todas las rutas", "🌙 Madrugada / Noche (22:00 - 07:00 AM)", "☀️ Mañana / Día (07:00 AM - 21:59)"]
    )

    if filtro_horario != "Todas las rutas" and col_h_salida:
        if filtro_horario == "🌙 Madrugada / Noche (22:00 - 07:00 AM)":
            df_filtrado = df_filtrado[df_filtrado[col_h_salida].apply(es_salida_madrugada)]
        else:
            df_filtrado = df_filtrado[~df_filtrado[col_h_salida].apply(es_salida_madrugada)]

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
            "📱 4. Enviar Rutas por WhatsApp",
            "🗺️ 5. Mapa de Sucursales",
            "🤖 6. Asistente & Optimizador IA"
        ]
    )

# Renderizador individual
def renderizar_tarjeta_individual(row, col_dia, col_cat, col_mov, col_frec, col_com, col_h_salida, col_h_retorno, cols_sucursales):
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
    nota_html = f'<div style="margin-top:8px; font-size:0.83rem; color:#8a6411; background-color:#fef7e7; padding:5px 10px; border-radius:6px; border:1px solid #f5e4b8;">💡 <b>Nota:</b> {comentario}</div>' if comentario and comentario not in ['nan', 'None'] else ''

    card_html = (
        f'<div class="{card_class}">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div><span class="badge-day">📅 {dia}</span> <span class="badge-cat">📦 {cat}</span> {badge_mov_html}</div>'
        f'<small style="color:#786565; font-weight:500;">{frec}</small>'
        f'</div>'
        f'<div><span class="{badge_time_class}">{icono_salida}: <b>{hora_salida}</b> &nbsp;|&nbsp; 🏁 Retorno Estimado: <b>{hora_retorno}</b></span></div>'
        f'<div style="margin-top:6px;"><strong style="color:#523e3e; font-size:0.85rem;">Secuencia de Recorrido:</strong><br>{html_paradas}</div>'
        f'{nota_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

# Renderizador comparador
def renderizar_tarjeta_unica_movilidad(df_mov_rutas, jornada_info, mov_label, dia_nombre, cols_sucursales, col_cat, col_frec, col_com, col_h_salida, col_h_retorno):
    if jornada_info is not None and jornada_info['Ingreso'] != '':
        jornada_html = (
            f'<div style="background-color:#eef5fc; border:1px solid #c9dfed; padding:10px 14px; border-radius:8px; margin-bottom:14px; color:#1c4966; font-size:0.88rem;">'
            f'⏱️ <b>Jornada en Planta ({jornada_info["Día"]}):</b> {jornada_info["Ingreso"]} a {jornada_info["Salida"]} &nbsp;•&nbsp; <b>Total:</b> {jornada_info["Total Horas"]} hrs'
            f'</div>'
        )
    else:
        jornada_html = (
            f'<div style="background-color:#fef8ec; border:1px solid #f2e3c6; padding:10px 14px; border-radius:8px; margin-bottom:14px; color:#855a15; font-size:0.88rem;">'
            f'⚠️ <i>Sin registro explícito de jornada para esta fecha.</i>'
            f'</div>'
        )

    salidas_html_list = []
    for idx, row in df_mov_rutas.iterrows():
        cat = row.get(col_cat, '')
        frec = row.get(col_frec, '')
        comentario = str(row.get(col_com, '')).strip()

        hora_salida = row.get(col_h_salida, 'Sin especificar') if col_h_salida else 'Sin especificar'
        hora_retorno = row.get(col_h_retorno, 'Sin especificar') if col_h_retorno else 'Sin especificar'

        if not hora_salida or hora_salida in ['nan', 'None']:
            hora_salida = "Sin especificar"
        if not hora_retorno or hora_retorno in ['nan', 'None']:
            hora_retorno = "Sin especificar"

        es_mad = es_salida_madrugada(hora_salida)
        block_class = "salida-block-madrugada" if es_mad else "salida-block"
        badge_time_class = "badge-time-madrugada" if es_mad else "badge-time"
        icono = "🌙 Salida" if es_mad else "🚀 Salida"

        paradas = [str(row[c]).strip() for c in cols_sucursales if str(row[c]).strip() not in ['', 'nan', 'None']]
        html_paradas = ' <span class="stop-arrow">➔</span> '.join([f'<span class="stop-chip">📍 {p}</span>' for p in paradas])

        nota_html = f'<div style="margin-top:6px; font-size:0.8rem; color:#8a6411;">💡 <b>Nota:</b> {comentario}</div>' if comentario and comentario not in ['nan', 'None'] else ''

        salida_html = (
            f'<div class="{block_class}">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<div><span class="badge-cat">📦 {cat}</span></div>'
            f'<small style="color:#786565; font-size:0.8rem;">{frec}</small>'
            f'</div>'
            f'<div style="margin-top:4px;"><span class="{badge_time_class}">{icono}: <b>{hora_salida}</b> &nbsp;|&nbsp; Retorno: <b>{hora_retorno}</b></span></div>'
            f'<div style="margin-top:6px;"><strong style="color:#423232; font-size:0.83rem;">Secuencia:</strong><br>{html_paradas}</div>'
            f'{nota_html}'
            f'</div>'
        )
        salidas_html_list.append(salida_html)

    salidas_combinadas = "".join(salidas_html_list)

    tarjeta_general_html = (
        f'<div class="general-mov-card">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid #f0e6dd; padding-bottom:8px;">'
        f'<h3 style="margin:0; font-size:1.2rem; color:#800c14;">🚚 {mov_label}</h3>'
        f'<span style="background-color:#800c14; color:#fff; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;">{len(df_mov_rutas)} Salida(s)</span>'
        f'</div>'
        f'{jornada_html}'
        f'<h4 style="font-size:0.92rem; color:#5c4436; margin-bottom:6px; margin-top:10px;">📋 Programación de Recorridos ({dia_nombre}):</h4>'
        f'{salidas_combinadas}'
        f'</div>'
    )
    st.markdown(tarjeta_general_html, unsafe_allow_html=True)

# Renderizador Tarjetas Semanales Resumen Vista 3
def renderizar_tarjeta_resumen_semanal_movilidad(df_movilidades_all, num_mov):
    df_unit = df_movilidades_all[df_movilidades_all['Num_Mov'].astype(str).str.strip() == str(num_mov)]
    
    if df_unit.empty:
        return

    mov_nombre = f"Movilidad {num_mov}"
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    pills_html = []
    total_horas_num = 0.0

    for d in dias_semana:
        rows_d = df_unit[df_unit['Día'] == d]
        
        horas_dia_dec = 0.0
        hrs_str_display = ""
        
        if not rows_d.empty:
            valid_rows = rows_d[rows_d['Ingreso'] != '']
            if not valid_rows.empty:
                for _, r in valid_rows.iterrows():
                    hrs_str = r['Total Horas']
                    horas_dia_dec += parse_horas_a_decimal(hrs_str)
                
                hrs_str_display = decimal_a_horas_str(horas_dia_dec)

        if horas_dia_dec > 0:
            total_horas_num += horas_dia_dec
            pills_html.append(f'<span class="day-hour-pill"><b>{d[:3]}:</b> {hrs_str_display}</span>')
        else:
            pills_html.append(f'<span class="day-hour-pill" style="opacity:0.5; background:#f5f5f5;"><b>{d[:3]}:</b> Descanso</span>')

    pills_joined = "".join(pills_html)
    total_formatted = decimal_a_horas_str(total_horas_num)

    card_html = (
        f'<div class="weekly-summary-card">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #f2e6dc; padding-bottom:8px; margin-bottom:10px;">'
        f'<span style="font-size:1.05rem; font-weight:700; color:#800c14;">🚚 {mov_nombre}</span>'
        f'<span style="background-color:#800c14; color:#ffffff; padding:4px 12px; border-radius:20px; font-weight:700; font-size:0.85rem;">⏱️ Total: {total_formatted} hrs/sem</span>'
        f'</div>'
        f'<div>{pills_joined}</div>'
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
            renderizar_tarjeta_individual(row, col_dia, col_cat, col_mov, col_frec, col_com, col_h_salida, col_h_retorno, cols_sucursales)

    # ----------------------------------------------------
    # VISTA 2: COMPARADOR DE MOVILIDADES
    # ----------------------------------------------------
    elif menu_opcion == "⚖️ 2. Comparador de Movilidades":
        st.title("⚖️ Comparador Lado a Lado de Movilidades")
        st.caption("Compara la jornada general y todas las salidas de dos unidades en una sola vista consolidada.")

        cols_sucursales = [c for c in df_rutas_raw.columns if 'Sucursal' in str(c)]
        col_frec = next((c for c in df_rutas_raw.columns if 'frec' in str(c).lower()), None)
        col_com = next((c for c in df_rutas_raw.columns if 'comentario' in str(c).lower()), None)
        
        movs_valores = df_rutas_raw[col_mov].dropna().astype(str).str.strip().unique()
        movs_validas = sorted([m for m in movs_valores if m in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']])

        if not movs_validas:
            st.warning("⚠️ No se encontraron números de movilidad válidos en la columna N.")
        else:
            opciones_mov = [f"Movilidad {m}" for m in movs_validas]
            mapa_mov_original = {f"Movilidad {m}": m for m in movs_validas}

            dia_comp = st.selectbox("📅 Selecciona el Día a Analizar:", options=dias_disponibles)
            df_dia_base = df_rutas_raw[df_rutas_raw[col_dia] == dia_comp]

            st.divider()

            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("🚛 Movilidad A")
                mov_a_label = st.selectbox("Selecciona Movilidad A:", options=opciones_mov, index=0, key="mov_a")
                
                if mov_a_label:
                    val_orig_a = mapa_mov_original[mov_a_label]
                    df_mov_a = df_dia_base[df_dia_base[col_mov].astype(str).str.strip() == str(val_orig_a)]
                    jornada_a = obtener_jornada_flexible(df_movilidades_raw, dia_comp, val_orig_a)

                    if len(df_mov_a) == 0:
                        st.warning(f"No hay rutas asignadas para {mov_a_label} el día {dia_comp}.")
                    else:
                        renderizar_tarjeta_unica_movilidad(df_mov_a, jornada_a, mov_a_label, dia_comp, cols_sucursales, col_cat, col_frec, col_com, col_h_salida, col_h_retorno)

            with col_right:
                st.subheader("🚛 Movilidad B")
                idx_b = 1 if len(opciones_mov) > 1 else 0
                mov_b_label = st.selectbox("Selecciona Movilidad B:", options=opciones_mov, index=idx_b, key="mov_b")
                
                if mov_b_label:
                    val_orig_b = mapa_mov_original[mov_b_label]
                    df_mov_b = df_dia_base[df_dia_base[col_mov].astype(str).str.strip() == str(val_orig_b)]
                    jornada_b = obtener_jornada_flexible(df_movilidades_raw, dia_comp, val_orig_b)

                    if len(df_mov_b) == 0:
                        st.warning(f"No hay rutas asignadas para {mov_b_label} el día {dia_comp}.")
                    else:
                        renderizar_tarjeta_unica_movilidad(df_mov_b, jornada_b, mov_b_label, dia_comp, cols_sucursales, col_cat, col_frec, col_com, col_h_salida, col_h_retorno)

    # ----------------------------------------------------
    # VISTA 3: JORNADA Y TURNOS POR MOVILIDAD
    # ----------------------------------------------------
    elif menu_opcion == "⏱️ 3. Jornada de Movilidades":
        st.title("⏱️ Turnos y Horarios por Movilidad")
        st.caption("Programación de choferes, horas acumuladas semanales y detalle de turnos.")

        st.subheader("📊 Resumen Horario Semanal por Movilidad")
        
        movs_en_jornadas = sorted(list(df_movilidades_raw['Num_Mov'].unique()), key=lambda x: int(x) if str(x).isdigit() else 99)

        if movs_en_jornadas:
            col_grid1, col_grid2 = st.columns(2)
            for idx, num_m in enumerate(movs_en_jornadas):
                if idx % 2 == 0:
                    with col_grid1:
                        renderizar_tarjeta_resumen_semanal_movilidad(df_movilidades_raw, num_m)
                else:
                    with col_grid2:
                        renderizar_tarjeta_resumen_semanal_movilidad(df_movilidades_raw, num_m)

        st.divider()

        st.subheader("📅 Programación de Turnos por Día")

        if not df_mov_filtrado.empty:
            dias_mov = [d for d in dias_ordenados if d in df_mov_filtrado['Día'].unique()]
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
    # VISTA 4: ENVIAR RUTAS POR WHATSAPP
    # ----------------------------------------------------
    elif menu_opcion == "📱 4. Enviar Rutas por WhatsApp":
        st.title("📱 Enviar Rutas por WhatsApp")
        st.caption("Genera mensajes con la orden de salida simplificada para los conductores o encargados.")
        st.divider()

        col_ws1, col_ws2 = st.columns(2)
        with col_ws1:
            dia_ws = st.selectbox("📅 Selecciona el Día a Enviar:", options=dias_disponibles, index=1 if "Martes" in dias_disponibles else 0)
        with col_ws2:
            num_telefono = st.text_input("📱 Número de WhatsApp (con código de país):", value="591", help="Ejemplo para Bolivia: 59170000000")

        df_dia_ws = df_rutas_raw[df_rutas_raw[col_dia] == dia_ws]

        if df_dia_ws.empty:
            st.warning(f"No hay rutas registradas para el día {dia_ws}.")
        else:
            cols_sucursales = [c for c in df_dia_ws.columns if 'Sucursal' in str(c)]

            mensaje_texto = f"📋 *PROGRAMACIÓN DE RUTAS - {dia_ws.upper()}*\n\n"
            movs_dia = sorted([m for m in df_dia_ws[col_mov].dropna().astype(str).str.strip().unique() if m in ['1','2','3','4','5','6','7','8','9','10']], key=lambda x: int(x))

            for m in movs_dia:
                df_m = df_dia_ws[df_dia_ws[col_mov].astype(str).str.strip() == str(m)]
                mensaje_texto += f"🚚 *MOVILIDAD {m}*\n"

                for idx, r in df_m.iterrows():
                    cat = r.get(col_cat, 'Ruta')
                    h_sal = r.get(col_h_salida, 'N/A')
                    h_ret = r.get(col_h_retorno, 'N/A')

                    paradas = [str(r[c]).strip() for c in cols_sucursales if str(r[c]).strip() not in ['', 'nan', 'None']]
                    cadena_paradas = " ➔ ".join(paradas)

                    mensaje_texto += f"• *{cat}:* {cadena_paradas}\n"
                    mensaje_texto += f"  ⏰ Salida: {h_sal} | Retorno: {h_ret}\n"
                
                mensaje_texto += "\n"

            st.subheader("📝 Vista Previa del Mensaje:")
            st.text_area("Texto a enviar:", value=mensaje_texto, height=220)

            num_clean = num_telefono.replace("+", "").replace(" ", "").strip()
            mensaje_url = urllib.parse.quote(mensaje_texto)
            wa_link = f"https://wa.me/{num_clean}?text={mensaje_url}"

            st.link_button("🚀 Abrir WhatsApp y Enviar Mensaje", wa_link, use_container_width=True)

    # ----------------------------------------------------
    # VISTA 5: MAPA DE SUCURSALES
    # ----------------------------------------------------
    elif menu_opcion == "🗺️ 5. Mapa de Sucursales":
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

    # ----------------------------------------------------
    # VISTA 6: ASISTENTE & OPTIMIZADOR IA (PROTEGIDO POR PIN)
    # ----------------------------------------------------
    elif menu_opcion == "🤖 6. Asistente & Optimizador IA":
        st.title("🤖 Asistente Logístico Inteligente & Optimizador")
        st.caption("Aprovecha la Inteligencia Artificial para analizar rutas, optimizar la secuencia de entrega y resolver dudas de operación.")
        st.divider()

        api_key_secret = st.secrets.get("GEMINI_API_KEY", "")
        pin_secret = str(st.secrets.get("ADMIN_PIN", "")).strip()

        if not api_key_secret:
            st.error("⚠️ La clave `GEMINI_API_KEY` no está configurada en los Secrets de la aplicación.")
        else:
            col_pin, _ = st.columns([1, 2])
            with col_pin:
                pin_ingresado = st.text_input("🔑 Ingrese el PIN de Acceso Autorizado:", type="password", placeholder="****")

            if pin_ingresado:
                if str(pin_ingresado).strip() == pin_secret:
                    st.success("✅ Acceso autorizado correctamente.")
                    st.divider()

                    try:
                        genai.configure(api_key=api_key_secret)

                        tab_opt, tab_chat = st.tabs(["🚀 Optimizador de Rutas", "💬 Chat Logístico"])

                        with tab_opt:
                            st.subheader("💡 Diagnóstico y Optimización de Recorrido")
                            col_ia1, col_ia2 = st.columns(2)
                            
                            with col_ia1:
                                dia_ia = st.selectbox("📅 Día a analizar:", options=dias_disponibles, key="dia_ia")
                            with col_ia2:
                                movs_num = sorted([m for m in df_rutas_raw[col_mov].dropna().astype(str).str.strip().unique() if m in ['1','2','3','4','5','6','7','8','9','10']])
                                mov_ia = st.selectbox("🚛 Movilidad a analizar:", options=[f"Movilidad {m}" for m in movs_num], key="mov_ia")

                            num_mov_ia = mov_ia.replace("Movilidad ", "").strip()
                            df_rutas_ia = df_rutas_raw[(df_rutas_raw[col_dia] == dia_ia) & (df_rutas_raw[col_mov].astype(str).str.strip() == num_mov_ia)]

                            if df_rutas_ia.empty:
                                st.info(f"No hay rutas programadas para {mov_ia} el día {dia_ia}.")
                            else:
                                st.write(f"**Rutas encontradas:** {len(df_rutas_ia)}")
                                if st.button("🪄 Generar Recomendación de Optimización con IA", use_container_width=True):
                                    with st.spinner("Analizando secuencia y tiempos con IA..."):
                                        cols_suck = [c for c in df_rutas_ia.columns if 'Sucursal' in str(c)]
                                        resumen_lineas = []
                                        for _, r in df_rutas_ia.iterrows():
                                            p = [str(r[c]).strip() for c in cols_suck if str(r[c]).strip() not in ['', 'nan', 'None']]
                                            resumen_lineas.append(f"Cat: {r.get(col_cat,'')}, Salida: {r.get(col_h_salida,'')}, Retorno: {r.get(col_h_retorno,'')}, Paradas: {' -> '.join(p)}")
                                        
                                        datos_txt = "\n".join(resumen_lineas)

                                        prompt_opt = f"""
                                        Eres un experto en logística de entregas para la empresa Fridolin en Bolivia.
                                        Analiza estas salidas de la {mov_ia} para el día {dia_ia}:

                                        {datos_txt}

                                        Genera:
                                        1. Evaluación breve de horarios y secuencia de paradas.
                                        2. Recomendaciones concisas para reducir tiempos y combustible.
                                        Responde en formato punto por punto.
                                        """
                                        
                                        respuesta = generar_respuesta_ia(prompt_opt)
                                        st.markdown("---")
                                        st.markdown("### 📋 Recomendación Generada:")
                                        st.markdown(respuesta)

                        with tab_chat:
                            st.subheader("💬 Consulta Rápida a la Operación")
                            st.caption("Realiza cualquier pregunta sobre los datos cargados de rutas o movilidades.")

                            query_ia = st.text_area("Pregunta sobre la logística:", placeholder="Ej: ¿Qué movilidades salen los martes de día y qué llevan?")

                            if st.button("🔍 Consultar IA", use_container_width=True):
                                if not query_ia.strip():
                                    st.warning("Escribe una consulta antes de enviar.")
                                else:
                                    with st.spinner("Consultando con IA..."):
                                        cols_suck = [c for c in df_rutas_raw.columns if 'Sucursal' in str(c)]
                                        rutas_resumidas = []
                                        for _, r in df_rutas_raw.head(100).iterrows():
                                            p = [str(r[c]).strip() for c in cols_suck if str(r[c]).strip() not in ['', 'nan', 'None']]
                                            if p:
                                                rutas_resumidas.append(f"Día:{r.get(col_dia,'')} | Mov:{r.get(col_mov,'')} | Cat:{r.get(col_cat,'')} | Sal:{r.get(col_h_salida,'')} | Ret:{r.get(col_h_retorno,'')} | Ruta:{'->'.join(p)}")

                                        txt_rutas = "\n".join(rutas_resumidas)
                                        jornadas_txt = "\n".join([f"Día:{r['Día']} | Mov:{r['Movilidad']} | Ent:{r['Ingreso']} | Sal:{r['Salida']}" for _, r in df_movilidades_raw.iterrows() if r['Ingreso'] != ''])

                                        prompt_chat = f"""
                                        Eres el asistente de logística de la pastelería Fridolin.
                                        Responde la consulta basándote en los siguientes datos operacionales:

                                        [DESPACHOS Y RUTAS]
                                        {txt_rutas}

                                        [JORNADAS DE CHOFERES]
                                        {jornadas_txt}

                                        Consulta del usuario: {query_ia}
                                        Responde de forma clara, directa, puntual y estructurada.
                                        """
                                        
                                        respuesta_chat = generar_respuesta_ia(prompt_chat)
                                        st.markdown("---")
                                        st.markdown("### 🤖 Respuesta del Asistente:")
                                        st.markdown(respuesta_chat)

                    except Exception as e_ia:
                        st.error(f"⚠️ Ocurrió un inconveniente al procesar la solicitud: {e_ia}")
                else:
                    st.error("❌ PIN incorrecto. Ingrese el PIN de autorización para acceder al Asistente e IA.")
            else:
                st.info("🔒 Ingrese el PIN de 4 dígitos para habilitar las funciones del Asistente Inteligente.")
