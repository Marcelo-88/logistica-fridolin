import streamlit as st
import pandas as pd

# ==========================================
# 1. FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data(ttl=300)
def cargar_y_preparar_datos():
    # Sustituye con tu método de carga de Google Sheets actual
    # (por ejemplo: st.connection("gsheets"), gspread o pd.read_csv)
    # df = ... 
    
    # ---------------------------------------------------------
    # NORMALIZACIÓN DE COLUMNAS (Resuelve el error de la imagen 1)
    # ---------------------------------------------------------
    # 1. Elimina espacios en blanco al inicio/final de los encabezados (ej: "Movilidad " -> "Movilidad")
    df.columns = df.columns.astype(str).str.strip()
    
    # 2. Buscar y estandarizar el nombre de la columna Movilidad (Columna N en tu Sheet)
    col_movilidad_real = None
    for col in df.columns:
        if 'movilidad' in col.lower():
            col_movilidad_real = col
            break
            
    if col_movilidad_real:
        df.rename(columns={col_movilidad_real: 'Movilidad'}, inplace=True)
        # Limpiar datos de la columna movilidad: convertir a entero/string limpio
        df['Movilidad'] = pd.to_numeric(df['Movilidad'], errors='coerce').fillna(0).astype(int)
    else:
        st.error("⚠️ No se encontró ninguna columna que contenga la palabra 'Movilidad' en el archivo.")
        
    return df

# ==========================================
# 2. INTERFAZ PRINCIPAL Y NAVEGACIÓN
# ==========================================
df_rutas = cargar_y_preparar_datos()

# Sidebar: Filtros y Modo de Vista
st.sidebar.title("📌 Filtros Rápidos")

modo_vista = st.sidebar.radio(
    "Modo de Vista:",
    [
        "1. Tarjetas de Ruta y Horarios",
        "2. Comparador de Movilidades",
        "3. Jornada de Movilidades",
        "4. Mapa de Sucursales"
    ],
    index=1 # Selección por defecto para probar el comparador
)

# ==========================================
# 3. MÓDULO: COMPARADOR DE MOVILIDADES
# ==========================================
if modo_vista == "2. Comparador de Movilidades":
    st.header("⚖️ Comparador Lado a Lado de Movilidades")
    st.caption("Compara el itinerario de dos unidades para evaluar fusión, reasignación o combinación de rutas.")
    st.markdown("---")

    if 'Movilidad' not in df_rutas.columns:
        st.error("⚠️ No se pudo identificar la columna de Movilidad en la tabla de rutas.")
    else:
        # Obtener lista única de movilidades activas (excluyendo 0 o nulos)
        movilidades_disponibles = sorted([m for m in df_rutas['Movilidad'].unique() if m > 0])
        
        if not movilidades_disponibles:
            st.warning("No se encontraron números de movilidad válidos en los datos.")
        else:
            # Selector de día si existe la columna de día/frecuencia
            dias_disponibles = ["Todos los días", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            dia_seleccionado = st.sidebar.selectbox("Seleccionar Día(s):", dias_disponibles)
            
            # Contenedor Lado a Lado (2 Columnas principales)
            col_a, col_b = st.columns(2)
            
            # --------------------------------------------------
            # COLUMNA IZQUIERDA: MOVILIDAD A
            # --------------------------------------------------
            with col_a:
                st.subheader("🚛 Movilidad A")
                mov_a_id = st.selectbox(
                    "Seleccionar Movilidad A:",
                    movilidades_disponibles,
                    index=0,
                    key="select_mov_a"
                )
                
                # Filtrar DataFrame para Movilidad A
                df_a = df_rutas[df_rutas['Movilidad'] == mov_a_id].copy()
                
                # Resumen de Métricas para A
                km_a = df_a['KM_Recorrido'].sum() if 'KM_Recorrido' in df_a.columns else 0
                rutas_a = len(df_a)
                
                m1, m2 = st.columns(2)
                m1.metric("Rutas Asignadas", f"{rutas_a}")
                m2.metric("Total KM", f"{km_a:.1f} km")
                
                st.markdown("##### Itinerario / Sucursales")
                # Seleccionar columnas relevantes para mostrar
                cols_mostrar = [c for c in ['Sucursal_1', 'Sucursal_2', 'Sucursal_3', 'Hora_Salida', 'Hora_Retorno', 'Frecuencia'] if c in df_a.columns]
                st.dataframe(df_a[cols_mostrar] if cols_mostrar else df_a, use_container_width=True)

            # --------------------------------------------------
            # COLUMNA DERECHA: MOVILIDAD B
            # --------------------------------------------------
            with col_b:
                st.subheader("🚚 Movilidad B")
                # Seleccionar por defecto la segunda movilidad para comparar de entrada
                index_b = 1 if len(movilidades_disponibles) > 1 else 0
                mov_b_id = st.selectbox(
                    "Seleccionar Movilidad B:",
                    movilidades_disponibles,
                    index=index_b,
                    key="select_mov_b"
                )
                
                # Filtrar DataFrame para Movilidad B
                df_b = df_rutas[df_rutas['Movilidad'] == mov_b_id].copy()
                
                # Resumen de Métricas para B
                km_b = df_b['KM_Recorrido'].sum() if 'KM_Recorrido' in df_b.columns else 0
                rutas_b = len(df_b)
                
                m3, m4 = st.columns(2)
                m3.metric("Rutas Asignadas", f"{rutas_b}")
                m4.metric("Total KM", f"{km_b:.1f} km")
                
                st.markdown("##### Itinerario / Sucursales")
                st.dataframe(df_b[cols_mostrar] if cols_mostrar else df_b, use_container_width=True)

            # --------------------------------------------------
            # COMPARATIVA RESUMIDA AL FINAL
            # --------------------------------------------------
            st.markdown("---")
            st.markdown("### 📊 Análisis de Solapamiento y Eficiencia")
            
            diff_km = abs(km_a - km_b)
            st.info(f"Diferencia de recorrido entre **Movilidad {mov_a_id}** y **Movilidad {mov_b_id}**: **{diff_km:.1f} km**.")

# ==========================================
# 4. RESTO DE VISTAS (Mantener tu estructura)
# ==========================================
elif modo_vista == "3. Jornada de Movilidades":
    st.header("⏱️ Turnos y Horarios por Movilidad")
    # Tu código existente para la Vista 3...

elif modo_vista == "1. Tarjetas de Ruta y Horarios":
    st.header("📇 Tarjetas de Ruta y Horarios")
    # Tu código para Vista 1...

elif modo_vista == "4. Mapa de Sucursales":
    st.header("🗺️ Mapa de Sucursales")
    # Tu código para Vista 4...
