import streamlit as st
import pandas as pd
import google.generativeai as genai

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control Logístico - Fridolin",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Control y Optimización de Rutas Logísticas")

# ---------------------------------------------------------
# LECTURA DE SECRETOS Y CONFIGURACIÓN DE IA
# ---------------------------------------------------------
api_key_secret = st.secrets.get("GEMINI_API_KEY", None)

# ---------------------------------------------------------
# CARGA DE DATOS DESDE GOOGLE SHEETS
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        # Conexión nativa de Streamlit para Google Sheets
        conn = st.connection("gsheets", type="gsheets")
        df = conn.read()
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

df_rutas = cargar_datos()
st.session_state["df_rutas"] = df_rutas

# ---------------------------------------------------------
# SIDEBAR / PANEL LATERAL (FILTROS Y NAVEGACIÓN)
# ---------------------------------------------------------
st.sidebar.header("📋 Filtros de Consulta")

dias_disponibles = ["Todos los días"]
categorias_disponibles = ["Todas las categorías"]

if not df_rutas.empty:
    if "Día" in df_rutas.columns:
        dias_disponibles += list(df_rutas["Día"].dropna().unique())
    if "Categoría" in df_rutas.columns:
        categorias_disponibles += list(df_rutas["Categoría"].dropna().unique())

dia_sel = st.sidebar.selectbox("📅 Seleccionar Día(s):", dias_disponibles)
cat_sel = st.sidebar.selectbox("📦 Categoría(s):", categorias_disponibles)
hora_sel = st.sidebar.selectbox("⏰ Horario de Salida:", ["Todas las rutas", "Mañana", "Tarde", "Noche/Madrugada"])
buscar_sucursal = st.sidebar.text_input("🔍 Buscar Sucursal:", placeholder="Ej. Hipermaxi, Urubó...")

st.sidebar.markdown("---")
st.sidebar.header("📌 Modo de Vista:")

opcion_vista = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "🎴 1. Tarjetas de Ruta y Horarios",
        "🚐 2. Comparador de Movilidades",
        "⏱️ 3. Jornada de Movilidades",
        "📲 4. Enviar Rutas por WhatsApp",
        "🗺️ 5. Mapa de Sucursales",
        "🤖 6. Asistente & Optimizador IA"
    ]
)

# Aplicar filtros al DataFrame
df_filtrado = df_rutas.copy()
if not df_filtrado.empty:
    if dia_sel != "Todos los días" and "Día" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Día"] == dia_sel]
    if cat_sel != "Todas las categorías" and "Categoría" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Categoría"] == cat_sel]
    if buscar_sucursal.strip() and "Sucursal" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Sucursal"].str.contains(buscar_sucursal, case=False, na=False)]

# ---------------------------------------------------------
# CONTENIDO PRINCIPAL SEGÚN LA VISTA SELECCIONADA
# ---------------------------------------------------------

if "1. Tarjetas" in opcion_vista:
    st.header("🎴 Tarjetas de Ruta y Horarios")
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("No hay datos que coincidan con los filtros seleccionados.")

elif "2. Comparador" in opcion_vista:
    st.header("🚐 Comparador de Movilidades")
    if not df_filtrado.empty and "Movilidad" in df_filtrado.columns:
        movilidades = df_filtrado["Movilidad"].dropna().unique()
        mov_sel = st.multiselect("Selecciona las movilidades a comparar:", movilidades, default=list(movilidades[:2]))
        st.dataframe(df_filtrado[df_filtrado["Movilidad"].isin(mov_sel)], use_container_width=True)
    else:
        st.info("Carga datos de movilidades para comparar.")

elif "3. Jornada" in opcion_vista:
    st.header("⏱️ Jornada y Tiempos de Movilidades")
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("No hay datos disponibles para mostrar la jornada.")

elif "4. Enviar" in opcion_vista:
    st.header("📲 Enviar Rutas por WhatsApp")
    st.write("Genera resúmenes listos para enviar a los choferes de cada movilidad.")
    if not df_filtrado.empty and "Movilidad" in df_filtrado.columns:
        mov_wa = st.selectbox("Selecciona la Movilidad:", df_filtrado["Movilidad"].dropna().unique())
        df_wa = df_filtrado[df_filtrado["Movilidad"] == mov_wa]
        
        texto_wa = f"*Ruta Asignada - {mov_wa}*\n"
        for _, row in df_wa.iterrows():
            texto_wa += f"• {row.get('Día', '')} | {row.get('Sucursal', '')} | Salida: {row.get('Hora Salida', '')}\n"
        
        st.text_area("Copia este mensaje:", texto_wa, height=180)
    else:
        st.info("Selecciona una movilidad válida para generar el mensaje.")

elif "5. Mapa" in opcion_vista:
    st.header("🗺️ Mapa de Sucursales")
    st.info("Vista de ubicación geográfica de sucursales en desarrollo.")

# ---------------------------------------------------------
# VISTA 6: ASISTENTE & OPTIMIZADOR IA
# ---------------------------------------------------------
elif "6. Asistente" in opcion_vista:
    st.header("🤖 Asistente & Optimizador IA")
    
    api_key = api_key_secret
    
    if not api_key:
        api_key = st.text_input(
            "🔑 Ingrese su API Key de Google Gemini para activar las funciones de IA:",
            type="password",
            help="Obtén tu clave desde https://aistudio.google.com/app/apikey"
        )
    
    st.markdown("---")
    
    tab_chat, tab_opt = st.tabs(["💬 Chat Logístico", "🚀 Optimizador de Rutas"])
    
    with tab_chat:
        st.subheader("💬 Consulta Rápida a la Operación")
        st.write("Realiza cualquier pregunta sobre los datos cargados de rutas, horarios o movilidades.")
        
        user_prompt = st.text_area(
            "Pregunta sobre la logística:",
            placeholder="Ej: ¿Cuáles son todas las sucursales que visita la Movilidad 1 el día Lunes y en qué horarios sale y retorna a Planta?",
            key="chat_prompt_input"
        )
        
        if st.button("🔍 Consultar IA", key="btn_chat"):
            if not api_key or not api_key.strip():
                st.error("⚠️ No se encontró una API Key válida. Ingrésala arriba o configúrala en Secrets.")
            elif not user_prompt.strip():
                st.warning("⚠️ Escribe una consulta antes de presionar el botón.")
            else:
                try:
                    genai.configure(api_key=api_key.strip())
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    datos_csv = ""
                    if not df_rutas.empty:
                        datos_csv = df_rutas.to_csv(index=False)
                    
                    prompt_completo = f"""
                    Eres un asistente logístico de alto nivel para la empresa Fridolin.
                    Responde a la consulta basándote estricta y únicamente en la siguiente tabla de datos de la operación:

                    DATOS DE LA OPERACIÓN:
                    {datos_csv}

                    PREGUNTA DE LA OPERACIÓN:
                    {user_prompt}
                    """
                    
                    with st.spinner("Procesando respuesta con Gemini IA..."):
                        respuesta = model.generate_content(prompt_completo)
                        
                        st.markdown("### 🤖 Respuesta del Asistente:")
                        st.write(respuesta.text)
                        
                except Exception as e:
                    st.error(f"Error al conectar con el servicio de IA: {e}")

    with tab_opt:
        st.subheader("🚀 Diagnóstico y Optimización de Rutas")
        st.write("Analiza cuellos de botella, traslapes de horario e ineficiencias en las entregas.")
        
        if st.button("📊 Analizar Eficiencia Global", key="btn_opt"):
            if not api_key or not api_key.strip():
                st.error("⚠️ Ingresa una API Key válida para ejecutar el diagnóstico.")
            else:
                try:
                    genai.configure(api_key=api_key.strip())
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    datos_csv = df_rutas.to_csv(index=False) if not df_rutas.empty else "No hay datos."
                    
                    prompt_opt = f"""
                    Analiza la siguiente tabla de rutas y movilidades de Fridolin:
                    {datos_csv}

                    Por favor, entrega un informe breve con:
                    1. Movilidades con mayor carga de trabajo semanal.
                    2. Posibles solapamientos u horarios ajustados entre retornos y salidas.
                    3. 3 recomendaciones concretas para optimizar combustible y tiempos.
                    """
                    
                    with st.spinner("Generando diagnóstico de rutas..."):
                        respuesta_opt = model.generate_content(prompt_opt)
                        st.markdown(respuesta_opt.text)
                        
                except Exception as e:
                    st.error(f"Error durante el análisis: {e}")
