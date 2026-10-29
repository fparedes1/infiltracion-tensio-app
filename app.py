import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Configuración de la página con perfil de suelo (🌍) y azul Francia oscuro
st.set_page_config(
    page_title="Infiltración - Tensiómetro de Disco",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados en tonos Azul Francia Oscuro (#0F172A, #1E3A8A, #2563EB)
st.markdown("""
    <style>
    .main {
        background-color: #F8FAFC;
    }
    .stApp {
        background-color: #F8FAFC;
    }
    h1, h2, h3 {
        color: #1E3A8A !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .sidebar .stSidebar {
        background-color: #0F172A;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0F172A;
        color: #93C5FD;
        text-align: center;
        padding: 8px;
        font-size: 12px;
        font-family: sans-serif;
        z-index: 1000;
        border-top: 1px solid #1E3A8A;
    }
    </style>
""", unsafe_allow_html=True)

# Título y subtítulo actualizados
st.title("Medición y Análisis de Infiltración a Campo con Tensiómetro de Disco")
st.subheader("Aplicación de la Ecuación de Philip")

# Barra lateral para configuración y carga de archivos
with st.sidebar:
    st.header("⚙️ Configuración del Ensayo")
    
    constante_tensio = st.number_input(
        "Constante del Tensiómetro (Factor)",
        min_value=0.010,
        max_value=1.000,
        value=0.186,
        step=0.001,
        format="%.3f",
        help="Relación entre el área del tubo reservorio y la base del anillo (ej: 0.186)"
    )
    
    st.markdown("---")
    st.header("📂 Carga de Datos")
    archivo_subido = st.file_uploader(
        "Cargar Planilla Excel (.xlsx)", 
        type=["xlsx", "xls"],
        help="Cada hoja debe representar una determinación a campo con columnas: Tiempo (min) y Lámina (cm)"
    )
    
    if archivo_subido is not None:
        st.markdown("---")
        st.header("📋 Cálculos y Resultados")
        try:
            xls_temp = pd.ExcelFile(archivo_subido)
            sheet_names_temp = xls_temp.sheet_names
            hoja_seleccionada = st.selectbox("Seleccione la hoja de campo:", sheet_names_temp)
        except:
            hoja_seleccionada = None

# Pie de página fijo requerido
st.markdown("""
    <div class="footer">
        Desarrollo: Ing. Agr. (Mgter.) Federico A. Paredes &nbsp;|&nbsp; Correo electrónico: paredesfedericoantonio@gmail.com
    </div>
""", unsafe_allow_html=True)

# Pestañas principales de navegación
tab_fund, tab_med, tab_resumen, tab_vel, tab_acum, tab_sort = st.tabs([
    "📖 Fundamentos", 
    "🛠️ Medición a campo", 
    "📊 Planillas resumen", 
    "📈 Velocidad de infiltración", 
    "📉 Lámina acumulada", 
    "📐 Ecuación de Philip"
])

with tab_fund:
    st.header("Fundamentos del Ensayo")
    st.markdown("""
    ### 1. Introducción
    El ensayo de infiltración con tensiómetro de disco permite determinar las propiedades hidráulicas del suelo no saturado *in situ*, operando bajo un potencial matricial (succión) controlado. Esto evita el flujo a través de los macroporos preferenciales vacíos, midiendo el efecto de la matriz del suelo[cite: 1].

    ### 2. Ecuación de Philip
    Para modelar la infiltración unidimensional de corta y mediana duración, se emplea la solución analítica propuesta por J. R. Philip (1957)[cite: 1]:
    
    $$I(t) = S \\cdot t^{0,5} + A \\cdot t$$

    Donde:
    * **$I(t)$**: Infiltración acumulada $L$ (cm)[cite: 1].
    * **$t$**: Tiempo transcurrido $T$ (minutos u horas)[cite: 1].
    * **$S$**: Sorptividad $L \\cdot T^{-0,5}$ (capacidad inicial de succión de la matriz del suelo)[cite: 1].
    * **$A$**: Parámetro de transmisión $L \\cdot T^{-1}$ (relacionado con las fuerzas gravitacionales y el flujo a través de la matriz del suelo)[cite: 1].

    ### 3. Linealización y Cálculo de Parámetros
    Para aislar y calcular experimentalmente la sorptividad ($S$) y el parámetro ($A$) a partir de los datos de campo, se transforma la ecuación de Philip dividiendo ambos miembros por la raíz cuadrada del tiempo ($\\sqrt{t}$)[cite: 1]:
    
    $$\\frac{I(t)}{\\sqrt{t}} = S + A \\cdot \\sqrt{t}$$

    Al representar gráficamente esta relación (en el eje Y: $\\frac{I}{\\sqrt{t}}$, y en el eje X: $\\sqrt{t}$)[cite: 1]:
    * La **Ordenada al Origen (Intersección)** corresponde a la Sorptividad ($S$)[cite: 1].
    * La **Pendiente** de la recta resultante corresponde al parámetro de transmisión ($A$)[cite: 1].

    ### 4. Infiltración básica ($i_b$) y Conductividad hidráulica $K$
    * **Infiltración Básica ($i_b$)**: Se alcanza cuando la tasa de infiltración se estabiliza hacia el final del ensayo, calculándose mediante la media aritmética de las últimas tasas instantáneas consecutivas[cite: 1]:
      $$i_b = \\frac{1}{m} \\sum_{j=N-m+1}^{N} \\frac{I_j - I_{j-1}}{t_j - t_{j-1}}$$
    * **Estimación de la Conductividad Hidráulica $K$**: En régimen estacionario y bajo la aproximación de flujo de disco (Wooding / Zhang), la conductividad hidráulica no saturada $K(h_0)$ a la succión aplicada se estima directamente a partir del tramo final estabilizado de la curva acumulada o de la tasa básica[cite: 1]:
      $$K(h_0) \\approx i_b$$

    ### 5. Referencias Bibliográficas
    * Philip, J. R. (1957). The theory of infiltration: 4. Sorptivity and algebraic equations for infiltration. *Soil Science*, 84(3), 257-264[cite: 1].
    * Wooding, R. A. (1968). Steady infiltration from a shallow circular pond. *Water Resources Research*, 4(6), 1259-1273[cite: 1].
    * Zhang, R. (1997). Determination of soil hydraulic properties from disk infiltrometer measurements. *Soil Science Society of America Journal*, 61(4), 1024-1030[cite: 1].
    * Perdok, U. D., et al. (1996). A disc infiltrometer to measure hydraulic properties of vadose zone. *Journal of Plant Nutrition and Soil Science*[cite: 1].
    """)

with tab_med:
    st.header("Guía para la medición a campo")
    st.markdown("""
    ### Materiales necesarios
    * Tensiómetro / Infiltrómetro de disco calibrado y purgado[cite: 2].
    * Anillos metálicos o de PVC de diámetro coincidente con la base del disco (habitualmente 20 cm de diámetro)[cite: 2].
    * Arena fina tamizada (tamiz de 0,25 mm a 0,5 mm), limpia y seca o con ligera humedad de cohesión[cite: 2].
    * Frasco lavador o rociador con agua destilada o desionizada[cite: 2].
    * Nivel de burbuja[cite: 2].
    * Espátula o cuchillo planero para enrasar la superficie[cite: 2].
    * Agua para la recarga del reservorio[cite: 2].
    * Cronómetro y planilla de campo (o dispositivo digital)[cite: 2].

    ### Paso a paso para la instalación a campo
    1. **Selección y acondicionamiento del punto**: Elegir un sitio representativo, libre de grietas, piedras grandes o raíces superficiales gruesas. Retire con cuidado la vegetación herbácea viva a ras del suelo sin remover ni alterar la estructura superficial del suelo[cite: 2].
    2. **Nivelación del terreno**: Colocar el anillo guía (preferentemente) o realizar una leve limpieza superficial horizontal utilizando la espátula. Verificar la horizontalidad apoyando el nivel de burbuja sobre el sector preparado[cite: 2].
    3. **Capa de contacto (colocación de arena tamizada)**: Extender una capa muy fina (de 2 a 3 mm de espesor máximo) de arena fina tamizada sobre la superficie del suelo. Esto evita espacios de aire milimétricos que bloquearían el contacto hidráulico. Enrase suavemente con la espátula[cite: 2].
    4. **Prueba de contacto e impregnación de la arena**: Humecer ligeramente la capa de arena con el rociador (sin encharcar) para asegurar la continuidad capilar inicial entre el suelo y la arena[cite: 2].
    5. **Asentamiento del disco del infiltrómetro**: Llevar el tensiómetro de disco lleno y purgado (con la succión / potencial matricial $h_0$ ya fijado en la torre de burbujeo) y asentarlo verticalmente sobre la cama de arena tamizada mediante un movimiento vertical suave, evitando giros laterales que rompan la interfase[cite: 2].
    6. **Protección contra factores externos (si es necesario)**: Instalar una sombrilla o pantalla protectora contra la radiación solar directa sobre el reservorio del equipo para evitar dilataciones térmicas del agua en la columna piezométrica que alteren las lecturas de nivel[cite: 2].
    7. **Inicio del ensayo**: Abrir la llave de paso entre el reservorio y el disco de contacto exactamente en el tiempo $T=0$. Registre los descensos de la lámina de agua en el tubo graduado a los tiempos preestablecidos (por ejemplo, a los 0,5, 1, 2, 3, 4, 5, 10, 15... hasta los 70 minutos o hasta alcanzar la estabilización completa del flujo)[cite: 2].
    """)

# Procesamiento de datos cuando se carga un archivo Excel
if archivo_subido is not None:
    try:
        xls = pd.ExcelFile(archivo_subido)
        sheet_names = xls.sheet_names
        
        resultados_globales = []
        diccionario_datos = {}
        
        for hoja in sheet_names:
            df_raw = pd.read_excel(archivo_subido, sheet_name=hoja)
            if df_raw.shape[1] >= 2:
                df = df_raw.iloc[:, :2].copy()
                df.columns = ['Tiempo_min', 'Lamina_cm']
                df = df.dropna().sort_values(by='Tiempo_min').reset_index(drop=True)
                
                df['Th_horas'] = df['Tiempo_min'] / 60.0
                df['t_parcial_h'] = df['Th_horas'].diff()
                df.loc[0, 't_parcial_h'] = df.loc[0, 'Th_horas']
                
                df['Lamina_parcial_cm'] = df['Lamina_cm'].diff() * constante_tensio
                df.loc[0, 'Lamina_parcial_cm'] = 0.0
                df['I_acumulada_cm'] = df['Lamina_parcial_cm'].cumsum()
                
                df['Vel_Infiltracion_cm_h'] = 0.0
                for i in range(1, len(df)):
                    dt_h = df.loc[i, 'Th_horas'] - df.loc[i-1, 'Th_horas']
                    if dt_h > 0:
                        df.loc[i, 'Vel_Infiltracion_cm_h'] = df.loc[i, 'Lamina_parcial_cm'] / dt_h
                    else:
                        df.loc[i, 'Vel_Infiltracion_cm_h'] = 0.0
                
                df['Raiz_t'] = np.sqrt(df['Th_horas'])
                df['I_sobre_Raiz_t'] = 0.0
                df.loc[1:, 'I_sobre_Raiz_t'] = df.loc[1:, 'I_acumulada_cm'] / df.loc[1:, 'Raiz_t']
                
                # Ib (últimos 3 puntos)
                if len(df) >= 3:
                    ib_val = df['Vel_Infiltracion_cm_h'].iloc[-3:].mean()
                else:
                    ib_val = df['Vel_Infiltracion_cm_h'].iloc[-1]
                
                # Regresión para S y A
                df_reg = df.iloc[1:].copy()
                if len(df_reg) >= 2:
                    slope, intercept, r_val, p_val, std_err = linregress(df_reg['Raiz_t'], df_reg['I_sobre_Raiz_t'])
                    s_val = intercept
                    a_val = slope
                    r2_val = r_val**2
                else:
                    s_val, a_val, r2_val = 0.0, 0.0, 0.0
                
                diccionario_datos[hoja] = {
                    'df': df, 'df_reg': df_reg,
                    'ib': ib_val, 'S': s_val, 'A': a_val, 'R2': r2_val
                }
                
                resultados_globales.append({
                    'Determinacion / Hoja': hoja,
                    'Infiltracion Basica ib (cm/h)': round(ib_val, 4),
                    'Sorptividad S (cm*h^-0.5)': round(s_val, 4),
                    'Parametro A (cm/h)': round(a_val, 4),
                    'R2 (Philip)': round(r2_val, 4)
                })
        
        df_resumen_global = pd.DataFrame(resultados_globales)
        
        with tab_resumen:
            st.header("Planillas resumen y Estadísticas")
            st.markdown("Resumen de parámetros hidráulicos obtenidos para cada determinación (hoja) del archivo Excel:")
            st.dataframe(df_resumen_global, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Valores promedio del conjunto de datos")
            
            if not df_resumen_global.empty:
                medias = df_resumen_global.mean(numeric_only=True)
                stdesv = df_resumen_global.std(numeric_only=True)
                cvs = (stdesv / medias) * 100
                
                df_estadistica = pd.DataFrame({
                    'Parametro': ['Infiltracion Basica (ib)', 'Sorptividad (S)', 'Parametro A', 'R2 (Philip)'],
                    'Promedio': [medias.iloc[0], medias.iloc[1], medias.iloc[2], medias.iloc[3]],
                    'Desviacion Estandar': [stdesv.iloc[0], stdesv.iloc[1], stdesv.iloc[2], stdesv.iloc[3]],
                    'Coeficiente de Variacion (CV %)': [cvs.iloc[0], cvs.iloc[1], cvs.iloc[2], cvs.iloc[3]]
                })
                
                st.dataframe(df_estadistica.style.format({
                    'Promedio': '{:.3f}',
                    'Desviacion Estandar': '{:.3f}',
                    'Coeficiente de Variacion (CV %)': '{:.2f}%'
                }), use_container_width=True)
            
            st.markdown("---")
            csv_resumen = df_resumen_global.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Resultados",
                data=csv_resumen,
                file_name="resumen_parametros_infiltracion.csv",
                mime="text/csv",
            )

        with tab_vel:
            st.header("Gráficos de Velocidad de Infiltración")
            st.markdown("Evolución de la velocidad instantánea y línea de Infiltración Básica ($i_b$) para cada determinación a campo:")
            
            for hoja, datos in diccionario_datos.items():
                st.subheader(f"Ensayo: {hoja}")
                df_h = datos['df']
                ib_h = datos['ib']
                
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.plot(df_h['Tiempo_min'][1:], df_h['Vel_Infiltracion_cm_h'][1:], marker='o', color='#2563EB', linewidth=2, label='Velocidad medida ($i_i$)')
                ax.axhline(y=ib_h, color='#DC2626', linestyle='--', linewidth=1.5, label=f'Infiltración Básica ($i_b$ = {ib_h:.2f} cm/h)')
                ax.set_xlabel('Tiempo (minutos)', fontweight='bold', color='#1E3A8A')
                ax.set_ylabel('Velocidad (cm/h)', fontweight='bold', color='#1E3A8A')
                ax.set_title(f'Tasa de Infiltración - {hoja}', fontweight='bold', color='#1E3A8A')
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.legend()
                st.pyplot(fig)
                st.markdown("---")

        with tab_acum:
            st.header("Gráficos de Lámina Acumulada")
            st.markdown("Curvas de infiltración acumulada con sus puntos medidos para cada determinación:")
            
            for hoja, datos in diccionario_datos.items():
                st.subheader(f"Ensayo: {hoja}")
                df_h = datos['df']
                
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.plot(df_h['Tiempo_min'], df_h['I_acumulada_cm'], marker='s', color='#1E3A8A', linewidth=2, label='Infiltración Acumulada ($I$)')
                ax.set_xlabel('Tiempo (minutos)', fontweight='bold', color='#1E3A8A')
                ax.set_ylabel('Lámina Acumulada (cm)', fontweight='bold', color='#1E3A8A')
                ax.set_title(f'Curva Acumulada - {hoja}', fontweight='bold', color='#1E3A8A')
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.legend()
                st.pyplot(fig)
                st.markdown("---")

        with tab_sort:
            st.header("Ecuación de Philip y Estimación Gráfica de la Sortividad ($S$)")
            
            for hoja, datos in diccionario_datos.items():
                st.subheader(f"Ensayo: {hoja}")
                df_reg = datos['df_reg']
                s_val = datos['S']
                a_val = datos['A']
                r2_val = datos['R2']
                
                st.markdown(f"""
                * **Sorptividad ($S$):** `{s_val:.4f} cm·h⁻⁰'⁵` | **Parámetro A:** `{a_val:.4f} cm/h` | **R²:** `{r2_val:.4f}`
                """)
                
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.scatter(df_reg['Raiz_t'], df_reg['I_sobre_Raiz_t'], color='#2563EB', s=50, label='Datos transformados')
                y_fit = s_val + a_val * df_reg['Raiz_t']
                ax.plot(df_reg['Raiz_t'], y_fit, color='#DC2626', linestyle='-', linewidth=2, label=f'Ajuste lineal ($S$ = {s_val:.2f})')
                
                ax.set_xlabel('Raíz cuadrada del tiempo ($\\sqrt{t}$ en h$^{0.5}$)', fontweight='bold', color='#1E3A8A')
                ax.set_ylabel('$I / \\sqrt{t}$ (cm / h$^{0.5}$)', fontweight='bold', color='#1E3A8A')
                ax.set_title(f'Linealización de Philip - {hoja}', fontweight='bold', color='#1E3A8A')
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.legend()
                st.pyplot(fig)
                st.markdown("---")

    except Exception as e:
        with tab_resumen:
            st.error(f"❌ Ocurrió un error al procesar el archivo Excel: {e}")
else:
    with tab_resumen:
        st.info("👈 Por favor, cargue un archivo de planilla de cálculo (.xlsx) en la barra lateral para visualizar las planillas resumen.")
