import streamlit as st
import google.generativeai as genai

# 1. Configuración principal de la página
st.set_page_config(
    page_title="Asistente Logístico Inteligente & Optimizador",
    page_icon="🚚",
    layout="wide"
)

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Filtros y Navegación")

# Filtros visuales (de tu interfaz)
categoria = st.sidebar.selectbox("📂 Categoría(s):", ["Todas las categorías", "Panadería", "Pastelería", "Insumos"])
horario = st.sidebar.selectbox("⏰ Horario de Salida:", ["Todas las rutas", "Mañana (06:00)", "Tarde (14:00)"])
buscar = st.sidebar.text_input("🔍 Buscar Sucursal:", placeholder="Ej. Hipermaxi, Urubó...")

st.sidebar.divider()

# Selector de módulo / Modo de Vista
modo_vista = st.sidebar.radio(
    "📌 Modo de Vista:",
    [
        "1. Tarjetas de Ruta y Horarios",
        "2. Comparador de Movilidades",
        "3. Jornada de Movilidades",
        "4. Enviar Rutas por WhatsApp",
        "5. Mapa de Sucursales",
        "6. Asistente & Optimizador IA"
    ],
    index=5  # Selecciona por defecto el asistente de IA
)

# --- LÓGICA DE LA API KEY ---
api_key = None

# Intentar leer desde secrets.toml de Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]


# --- CONTENIDO PRINCIPAL ---
if modo_vista == "6. Asistente & Optimizador IA":
    st.title("🤖 Asistente Logístico Inteligente & Optimizador")
    st.caption("Aprovecha la Inteligencia Artificial para analizar rutas, optimizar la secuencia de entrega y resolver dudas de operación.")
    
    st.divider()

    # Si no se encontró en secrets, pedirla en pantalla
    if not api_key:
        api_key_input = st.text_input(
            "🔑 Ingrese su API Key de Google Gemini para activar las funciones de IA:",
            type="password",
            help="Obtén tu clave gratuita en Google AI Studio"
        )
        if api_key_input:
            api_key = api_key_input
        else:
            st.warning("⚠️ Se requiere una API Key de Google Gemini válida para usar este módulo. Puedes configurarla en .streamlit/secrets.toml con el nombre GEMINI_API_KEY o ingresarla arriba.")

    # --- CHAT / PROCESAMIENTO DE IA ---
    if api_key:
        # Estructura try...except protegida correctamente
        try:
            # Configurar el modelo
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Inicializar historial de conversación
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Mostrar mensajes previos
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Entrada de texto para el chat
            if prompt := st.chat_input("Escribe tu consulta o pide una optimización de ruta..."):
                # Mostrar mensaje del usuario
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Generar respuesta con Gemini
                with st.chat_message("assistant"):
                    with st.spinner("Procesando consulta logística..."):
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            st.error(f"❌ Ocurrió un error al conectar con Gemini: {str(e)}")

else:
    # Vista para las otras opciones del menú
    st.title(modo_vista)
    st.info("Módulo de visualización de datos de logística activo.")
