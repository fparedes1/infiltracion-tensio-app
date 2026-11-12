import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.optimize import curve_fit
import io
from docx import Document
from docx.shared import Inches

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

# Título y subtítulo
st.title("Medición y Análisis de Infiltración a Campo con Tensiómetro de Disco")
st.subheader("Aplicación de la Ecuación de Philip")

# Barra lateral para configuración y modo de entrada
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
    st.header("📥 Método de Ingreso de Datos")
    
    modo_ingreso = st.radio(
        "Seleccione cómo desea ingresar los datos:",
        ["Planilla Excel (.xlsx)", "Carga Manual en Campo"]
    )
    
    diccionario_datos = {}
    
    if modo_ingreso == "Planilla Excel (.xlsx)":
        archivo_subido = st.file_uploader(
            "Cargar Planilla Excel (.xlsx)", 
            type=["xlsx", "xls"],
            help="Cada hoja debe representar una determinación a campo con columnas: Tiempo (min) y Lámina (cm)"
        )
        st.markdown("""
            <div style="background-color: #1E3A8A; padding: 10px; border-radius: 6px; color: #E2E8F0; font-size: 13px; margin-top: 10px;">
                📋 <b>Instrucciones:</b><br>
                Cada hoja del archivo Excel debe contener las lecturas de campo en dos columnas (Columna 1: Tiempo en minutos, Columna 2: Lámina en cm).
            </div>
        """, unsafe_allow_html=True)
        
        if archivo_subido is not None:
            try:
                xls = pd.ExcelFile(archivo_subido)
                for hoja in xls.sheet_names:
                    df_raw = pd.read_excel(archivo_subido, sheet_name=hoja)
                    if df_raw.shape[1] >= 2:
                        df = df_raw.iloc[:, :2].copy()
                        df.columns = ['Tiempo_min', 'Lamina_cm']
                        diccionario_datos[hoja] = df
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

    else:  # Carga manual interactiva en campo
        st.markdown("""
            <div style="background-color: #1E3A8A; padding: 10px; border-radius: 6px; color: #E2E8F0; font-size: 13px; margin-top: 10px;">
                ✍️ <b>Carga en Campo:</b><br>
                Ingrese directamente las lecturas de tiempo y lámina leída. Puede agregar o quitar filas según necesite.
            </div>
        """, unsafe_allow_html=True)
        
        nombre_muestra = st.text_input("Identificación de la Muestra", value="Muestra_1")
        
        # Datos iniciales por defecto para la tabla interactiva
        datos_iniciales = pd.DataFrame({
            'Tiempo_min': [0.0, 1.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0],
            'Lamina_cm': [45.0, 42.5, 39.0, 36.5, 31.0, 27.5, 24.5, 20.0]
        })
        
        df_manual = st.data_editor(datos_iniciales, num_rows="dynamic", use_container_width=True)
        if not df_manual.empty:
            diccionario_datos[nombre_muestra] = df_manual

# Pie de página fijo requerido
st.markdown("""
    <div class="footer">
        Desarrollo: Ing. Agr. (Mgter.) Federico A. Paredes &nbsp;|&nbsp; Correo electrónico: paredesfedericoantonio@gmail.com
    </div>
""", unsafe_allow_html=True)

# Pestañas principales de navegación
tab_fund, tab_med, tab_resumen, tab_vel, tab_acum = st.tabs([
    "📖 Fundamentos", 
    "🛠️ Medición a campo", 
    "📊 Planillas resumen", 
    "📈 Velocidad de infiltración", 
    "📉 Lámina acumulada"
])

with tab_fund:
    st.header("Fundamentos del Ensayo")
    st.markdown("""
    ### 1. Introducción
    El ensayo de infiltración con tensiómetro de disco permite determinar las propiedades hidráulicas del suelo no saturado *in situ*, operando bajo un potencial matricial (succión) controlado. Esto evita el flujo a través de los macroporos preferenciales vacíos, midiendo el efecto de la matriz del suelo.

    ### 2. Ecuación de Philip
    Para modelar la infiltración unidimensional de corta y mediana duración, se emplea la solución analítica propuesta por J. R. Philip (1957):
    
    $$I(t) = S \\cdot t^{0,5} + A \\cdot t$$

    Donde:
    * **$I(t)$**: Infiltración acumulada $L$ (cm).
    * **$t$**: Tiempo transcurrido $T$ (minutos u horas).
    * **$S$**: Sorptividad $L \\cdot T^{-0,5}$ (capacidad inicial de succión de la matriz del suelo).
    * **$A$**: Parámetro de transmisión $L \\cdot T^{-1}$ (relacionado con las fuerzas gravitacionales y el flujo a través de la matriz del suelo).

    ### 3. Linealización y Cálculo de Parámetros
    Para aislar y calcular experimentalmente la sorptividad ($S$) y el parámetro ($A$) a partir de los datos de campo, se transforma la ecuación de Philip dividiendo ambos miembros por la raíz cuadrada del tiempo ($\\sqrt{t}$):
    
    $$\\frac{I(t)}{\\sqrt{t}} = S + A \\cdot \\sqrt{t}$$

    Al representar gráficamente esta relación (en el eje Y: $\\frac{I}{\\sqrt{t}}$, y en el eje X: $\\sqrt{t}$):
    * La **Ordenada al Origen (Intersección)** corresponde a la Sorptividad ($S$).
    * La **Pendiente** de la recta resultante corresponde al parámetro de transmisión ($A$).

    ### 4. Infiltración básica ($i_b$) y Conductividad hidráulica $K$
    * **Infiltración Básica ($i_b$)**: Se alcanza cuando la tasa de infiltración se estabiliza hacia el final del ensayo, calculándose mediante la media aritmética de las últimas tasas instantáneas consecutivas:
      $$i_b = \\frac{1}{m} \\sum_{j=N-m+1}^{N} \\frac{I_j - I_{j-1}}{t_j - t_{j-1}}$$
    * **Estimación de la Conductividad Hidráulica $K$**: En régimen estacionario y bajo la aproximación de flujo de disco (Wooding / Zhang), la conductividad hidráulica no saturada $K(h_0)$ a la succión aplicada se estima directamente a partir del tramo final estabilizado de la curva acumulada o de la tasa básica:
      $$K(h_0) \\approx i_b$$

    ### 5. Clasificación general en ocho clases
    El *Soil Quality Test Kit Guide* del USDA presenta una clasificación de ocho clases de infiltración, desde muy rápida hasta prácticamente impermeable. La clasificación se basa en valores de infiltración estabilizada y recoge referencias clave como Hillel (1982) y Lowery et al. (1996).
    """)
    
    df_clases = pd.DataFrame({
        'Clase': [
            'Muy rápida', 'Rápida', 'Moderadamente rápida', 'Moderada', 
            'Moderadamente lenta', 'Lenta', 'Muy lenta', 'Prácticamente impermeable'
        ],
        'Infiltración básica (cm/h)': [
            '> 50,8', '15,24 – 50,8', '5,08 – 15,24', '1,52 – 5,08', 
            '0,508 – 1,52', '0,152 – 0,508', '0,0038 – 0,152', '< 0,0038'
        ]
    })
    st.table(df_clases)

    st.markdown("""
    ### 6. Referencias Bibliográficas
    * **FAO**. Annex 2: Infiltration rate and infiltration test. Presenta valores de infiltración básica para grupos texturales y un procedimiento de medición de campo.
    * **USDA, Agricultural Research Service, Natural Resources Conservation Service, Soil Quality Institute**. (1999). *Soil Quality Test Kit Guide*. Incluye procedimientos de campo e interpretación de indicadores de calidad del suelo, incluida la infiltración.
    * **Hillel, D.** (1982). *Introduction to Soil Physics*. Academic Press. Obra de referencia sobre física del suelo; citada en el manual de USDA para la clasificación de infiltración.
    * **Lowery, B., Arshad, M. A., Lal, R., & Hickey, W. J.** (1996). Soil water parameters and soil quality. En J. W. Doran & A. J. Jones (eds.), *Methods for Assessing Soil Quality*, pp. 143–157. Soil Science Society of America, Special Publication 49.
    * **Philip, J. R.** (1957). The theory of infiltration: 4. Sorptivity and algebraic equations for infiltration. *Soil Science*, 84(3), 257-264.
    * **Wooding, R. A.** (1968). Steady infiltration from a shallow circular pond. *Water Resources Research*, 4(6), 1259-1273.
    * **Zhang, R.** (1997). Determination of soil hydraulic properties from disk infiltrometer measurements. *Soil Science Society of America Journal*, 61(4), 1024-1030.
    * **Perdok, U. D., et al.** (1996). A disc infiltrometer to measure hydraulic properties of vadose zone. *Journal of Plant Nutrition and Soil Science*.
    """)

with tab_med:
    st.header("Guía para la medición a campo")
    st.markdown("""
    ### Materiales necesarios
    * Tensiómetro / Infiltrómetro de disco calibrado y purgado.
    * Anillos metálicos o de PVC de diámetro coincidente con la base del disco (habitualmente 20 cm de diámetro).
    * Arena fina tamizada (tamiz de 0,25 mm a 0,5 mm), limpia y seca o con ligera humedad de cohesión.
    * Frasco lavador o rociador con agua destilada o desionizada.
    * Nivel de burbuja.
    * Espátula o cuchillo planero para enrasar la superficie.
    * Agua para la recarga del reservorio.
    * Cronómetro y planilla de campo (o dispositivo digital).

    ### Paso a paso para la instalación a campo
    1. **Selección y acondicionamiento del punto**: Elegir un sitio representativo, libre de grietas, piedras grandes o raíces superficiales gruesas. Retire con cuidado la vegetación herbácea viva a ras del suelo sin remover ni alterar la estructura superficial del suelo.
    2. **Nivelación del terreno**: Colocar el anillo guía (preferentemente) o realizar una leve limpieza superficial horizontal utilizando la espátula. Verificar la horizontalidad apoyando el nivel de burbuja sobre el sector preparado.
    3. **Capa de contacto (colocación de arena tamizada)**: Extender una capa muy fina (de 2 a 3 mm de espesor máximo) de arena fina tamizada sobre la superficie del suelo. Esto evita espacios de aire milimétricos que bloquearían el contacto hidráulico. Enrase suavemente con la espátula.
    4. **Prueba de contacto e impregnación de la arena**: Humecer ligeramente la capa de arena con el rociador (sin encharcar) para asegurar la continuidad capilar inicial entre el suelo y la arena.
    5. **Asentamiento del disco del infiltrómetro**: Llevar el tensiómetro de disco lleno y purgado (con la succión / potencial matricial $h_0$ ya fijado en la torre de burbujeo) y asentarlo verticalmente sobre la cama de arena tamizada mediante un movimiento vertical suave, evitando giros laterales que rompan la interfase.
    6. **Protección contra factores externos (si es necesario)**: Instalar una sombrilla o pantalla protectora contra la radiación solar directa sobre el reservorio del equipo para evitar dilataciones térmicas del agua en la columna piezométrica que alteren las lecturas de nivel.
    7. **Inicio del ensayo**: Abrir la llave de paso entre el reservorio y el disco de contacto exactamente en el tiempo $T=0$. Registre los descensos de la lámina de agua en el tubo graduado a los tiempos preestablecidos (por ejemplo, a los 0,5, 1, 2, 3, 4, 5, 10, 15... hasta los 70 minutos o hasta alcanzar la estabilización completa del flujo).
    """)

# Función auxiliar para determinar la clase de infiltración y el ícono sin letras de color
def clasificar_infiltracion(ib_cm_h):
    ib_mm_h = ib_cm_h * 10.0
    if ib_mm_h > 508:
        return "Muy rápida (> 50,8 cm/h)", "🔵", "Infiltración elevada. Evaluar si puede favorecer la percolación o dificultar el manejo del agua."
    elif ib_mm_h >= 152.4:
        return "Rápida (15,24 - 50,8 cm/h)", "🟢", "Infiltración relativamente favorable para numerosos usos agrícolas."
    elif ib_mm_h >= 50.8:
        return "Moderadamente rápida (5,08 - 15,24 cm/h)", "🟢", "Infiltración favorable para el desarrollo radicular y retención hídrica."
    elif ib_mm_h >= 15.2:
        return "Moderada (1,52 - 5,08 cm/h)", "🟡", "Infiltración intermedia. Interpretar según el suelo y el sistema productivo."
    elif ib_mm_h >= 5.08:
        return "Moderadamente lenta (0,508 - 1,52 cm/h)", "🟠", "Infiltración relativamente baja. Evaluar textura, estructura, humedad y manejo."
    elif ib_mm_h >= 1.52:
        return "Lenta (0,152 - 0,508 cm/h)", "🟠", "Infiltración baja. Investigar posibles limitaciones físicas, estructurales o de drenaje."
    elif ib_mm_h >= 0.038:
        return "Muy lenta (0,0038 - 0,152 cm/h)", "🔴", "Infiltración muy baja. Riesgo de encharcamiento o escorrentía superficial."
    else:
        return "Prácticamente impermeable (< 0,0038 cm/h)", "🔴", "Suelo prácticamente impermeable. Severas restricciones de drenaje."

# Procesamiento de datos del diccionario (ya sea por Excel o carga manual)
if len(diccionario_datos) > 0:
    try:
        resultados_globales = []
        procesados_datos = {}
        
        for hoja, df_raw in diccionario_datos.items():
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
                
                # Regresión lineal para S y A
                df_reg = df.iloc[1:].copy()
                if len(df_reg) >= 2:
                    slope, intercept, r_val, p_val, std_err = linregress(df_reg['Raiz_t'], df_reg['I_sobre_Raiz_t'])
                    s_val = intercept
                    a_val = slope
                else:
                    s_val, a_val = 0.0, 0.0
                
                # Ajuste exponencial para velocidad
                t_vel = df['Tiempo_min'].values[1:]
                v_vel = df['Vel_Infiltracion_cm_h'].values[1:]
                
                def exp_func(t, a, b, c):
                    return a * np.exp(-b * t) + c
                
                t_fit = np.linspace(t_vel.min(), t_vel.max(), 100) if len(t_vel) > 1 else np.array([0, 1])
                v_fit = np.zeros_like(t_fit)
                
                try:
                    popt, _ = curve_fit(exp_func, t_vel, v_vel, p0=[30, 0.1, ib_val], bounds=([-np.inf, 0, -np.inf], [np.inf, np.inf, np.inf]), maxfev=5000)
                    v_fit = exp_func(t_fit, *popt)
                except:
                    v_fit = np.full_like(t_fit, ib_val)

                clase_inf, icono_inf, desc_inf = clasificar_infiltracion(ib_val)

                procesados_datos[hoja] = {
                    'df': df, 'ib': ib_val, 'S': s_val, 'A': a_val,
                    't_fit': t_fit, 'v_fit': v_fit,
                    'clase': clase_inf, 'icono': icono_inf, 'desc': desc_inf
                }
                
                resultados_globales.append({
                    'Muestra': hoja,
                    'Infiltración básica Ib (cm/h)': round(ib_val, 4),
                    'Clase (USDA)': clase_inf.split(" (")[0],
                    'Indicador': icono_inf,
                    'Sorptividad S (cm*h^-0.5)': round(s_val, 4),
                    'Parámetro A de Ecuación de Philip (cm/h)': round(a_val, 4)
                })
        
        df_resumen_global = pd.DataFrame(resultados_globales)
        
        with tab_resumen:
            st.header("Planillas resumen")
            st.markdown("Resumen de parámetros hidráulicos y clasificación obtenida para cada determinación:")
            st.dataframe(df_resumen_global, use_container_width=True)
            
            csv_muestra = df_resumen_global.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Planilla Resumen por Muestra",
                data=csv_muestra,
                file_name="planilla_resumen_muestras.csv",
                mime="text/csv",
            )
            
            st.markdown("---")
            st.subheader("🚦 Interpretación por muestra")
            for hoja, datos in procesados_datos.items():
                st.markdown(f"""
                * **Muestra `{hoja}`** $\\rightarrow$ **$i_b$ = {datos['ib']:.3f} cm/h** | **Clase:** {datos['clase']} | **Indicador:** {datos['icono']}  
                  *Interpretación:* {datos['desc']}
                """)

            st.markdown("---")
            st.subheader("Valores promedio del conjunto de datos")
            
            df_num_stats = pd.DataFrame({
                'Infiltración básica Ib (cm/h)': [d['ib'] for d in procesados_datos.values()],
                'Sorptividad S (cm*h^-0.5)': [d['S'] for d in procesados_datos.values()],
                'Parámetro A de Ecuación de Philip (cm/h)': [d['A'] for d in procesados_datos.values()]
            })
            
            if not df_num_stats.empty:
                medias = df_num_stats.mean()
                stdesv = df_num_stats.std()
                cvs = (stdesv / medias) * 100
                
                df_estadistica = pd.DataFrame({
                    'Parámetro': ['Infiltración básica (Ib)', 'Sorptividad (S)', 'Parámetro A de Ecuación de Philip'],
                    'Promedio': [medias.iloc[0], medias.iloc[1], medias.iloc[2]],
                    'Desviación Estándar': [stdesv.iloc[0], stdesv.iloc[1], stdesv.iloc[2]],
                    'Coeficiente de Variación (CV %)': [cvs.iloc[0], cvs.iloc[1], cvs.iloc[2]]
                })
                
                st.dataframe(df_estadistica.style.format({
                    'Promedio': '{:.3f}',
                    'Desviación Estándar': '{:.3f}',
                    'Coeficiente de Variación (CV %)': '{:.2f}%'
                }), use_container_width=True)
                
                st.markdown("---")
                st.subheader("Análisis de Variabilidad")
                
                fig_box, axes = plt.subplots(1, 3, figsize=(12, 4))
                
                cols_boxplot = [
                    ('Infiltración básica Ib (cm/h)', 'Ib (cm/h)', '#2563EB'),
                    ('Sorptividad S (cm*h^-0.5)', 'S (cm*h^-0.5)', '#1E3A8A'),
                    ('Parámetro A de Ecuación de Philip (cm/h)', 'A (cm/h)', '#0F172A')
                ]
                
                for idx, (col_name, label_name, color_box) in enumerate(cols_boxplot):
                    ax = axes[idx]
                    ax.boxplot(df_num_stats[col_name], patch_artist=True,
                               boxprops=dict(facecolor=color_box, color='#0F172A', linewidth=1.5),
                               medianprops=dict(color='white', linewidth=2),
                               whiskerprops=dict(color='#0F172A', linewidth=1.5),
                               capprops=dict(color='#0F172A', linewidth=1.5))
                    ax.set_title(label_name, fontweight='bold', color='#1E3A8A')
                    ax.grid(True, linestyle=':', alpha=0.6)
                    ax.set_xticklabels([label_name])
                
                plt.tight_layout()
                st.pyplot(fig_box)
            
            st.markdown("---")
            csv_promedios = df_estadistica.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Valores Promedio y Estadísticas",
                data=csv_promedios,
                file_name="valores_promedio_variabilidad.csv",
                mime="text/csv",
            )

        with tab_vel:
            st.header("Gráficos de Velocidad de Infiltración")
            st.markdown("Evolución de la velocidad instantánea (valores observados), curva de ajuste y línea de Infiltración Básica ($i_b$):")
            
            for hoja, datos in procesados_datos.items():
                st.subheader(f"Muestra: {hoja} | Clase: {datos['clase']} {datos['icono']}")
                df_h = datos['df']
                ib_h = datos['ib']
                t_fit = datos['t_fit']
                v_fit = datos['v_fit']
                
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.plot(df_h['Tiempo_min'][1:], df_h['Vel_Infiltracion_cm_h'][1:], marker='o', color='#2563EB', linestyle='', label='Valores observados ($i_i$)')
                ax.plot(t_fit, v_fit, color='#0F172A', linestyle='-', linewidth=2)
                ax.axhline(y=ib_h, color='#DC2626', linestyle='--', linewidth=1.5, label=f'Infiltración básica $i_b$ = {ib_h:.2f} cm/h')
                
                ax.set_xlim(left=0)
                ax.set_ylim(bottom=0)
                
                ax.set_xlabel('Tiempo (minutos)', fontweight='bold', color='#1E3A8A')
                ax.set_ylabel('Velocidad (cm/h)', fontweight='bold', color='#1E3A8A')
                ax.set_title(f'Muestra {hoja} - {datos["clase"].split(" (")[0]} {datos["icono"]}', fontweight='bold', color='#1E3A8A')
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.legend()
                st.pyplot(fig)
                st.markdown("---")

        with tab_acum:
            st.header("Gráficos de Lámina Acumulada")
            st.markdown("Curvas de infiltración acumulada con sus puntos medidos:")
            
            for hoja, datos in procesados_datos.items():
                st.subheader(f"Muestra: {hoja}")
                df_h = datos['df']
                
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.plot(df_h['Tiempo_min'], df_h['I_acumulada_cm'], marker='s', color='#1E3A8A', linewidth=2, label='Infiltración Acumulada ($I$)')
                
                ax.set_xlim(left=0)
                ax.set_ylim(bottom=0)
                
                ax.set_xlabel('Tiempo (minutos)', fontweight='bold', color='#1E3A8A')
                ax.set_ylabel('Lámina Acumulada (cm)', fontweight='bold', color='#1E3A8A')
                ax.set_title(f'Curva Acumulada - Muestra {hoja}', fontweight='bold', color='#1E3A8A')
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.legend()
                st.pyplot(fig)
                st.markdown("---")

        # Botón para descargar todos los gráficos en un solo archivo Word (.docx)
        st.markdown("---")
        st.header("📄 Exportar Reporte de Gráficos")
        if st.button("📥 Generar y Descargar todos los gráficos en Word (.docx)"):
            doc = Document()
            doc.add_heading('Reporte de Gráficos de Infiltración', 0)
            doc.add_paragraph('Resultados de ensayos con Tensiómetro de Disco.')
            
            for hoja, datos in procesados_datos.items():
                doc.add_heading(f'Muestra: {hoja}', level=1)
                
                # Gráfico velocidad
                fig_v, ax_v = plt.subplots(figsize=(6, 3.5))
                df_h = datos['df']
                ib_h = datos['ib']
                ax_v.plot(df_h['Tiempo_min'][1:], df_h['Vel_Infiltracion_cm_h'][1:], marker='o', color='#2563EB', linestyle='', label='Observados')
                ax_v.plot(datos['t_fit'], datos['v_fit'], color='#0F172A', linestyle='-', linewidth=2)
                ax_v.axhline(y=ib_h, color='#DC2626', linestyle='--', linewidth=1.5, label=f'Ib = {ib_h:.2f} cm/h')
                ax_v.set_xlim(left=0)
                ax_v.set_ylim(bottom=0)
                ax_v.set_xlabel('Tiempo (min)')
                ax_v.set_ylabel('Velocidad (cm/h)')
                ax_v.set_title(f'Velocidad - {hoja}')
                ax_v.grid(True, linestyle=':', alpha=0.6)
                ax_v.legend(fontsize=8)
                
                buf_v = io.BytesIO()
                plt.savefig(buf_v, format='png', bbox_inches='tight', dpi=150)
                buf_v.seek(0)
                doc.add_paragraph(f'Tasa de Infiltración - Muestra {hoja}')
                doc.add_picture(buf_v, width=Inches(5.5))
                plt.close(fig_v)
                
                # Gráfico acumulado
                fig_a, ax_a = plt.subplots(figsize=(6, 3.5))
                ax_a.plot(df_h['Tiempo_min'], df_h['I_acumulada_cm'], marker='s', color='#1E3A8A', linewidth=2, label='Acumulada')
                ax_a.set_xlim(left=0)
                ax_a.set_ylim(bottom=0)
                ax_a.set_xlabel('Tiempo (min)')
                ax_a.set_ylabel('Lámina Acumulada (cm)')
                ax_a.set_title(f'Curva Acumulada - {hoja}')
                ax_a.grid(True, linestyle=':', alpha=0.6)
                ax_a.legend(fontsize=8)
                
                buf_a = io.BytesIO()
                plt.savefig(buf_a, format='png', bbox_inches='tight', dpi=150)
                buf_a.seek(0)
                doc.add_paragraph(f'Lámina Acumulada - Muestra {hoja}')
                doc.add_picture(buf_a, width=Inches(5.5))
                plt.close(fig_a)
                
                doc.add_page_break()
            
            word_io = io.BytesIO()
            doc.save(word_io)
            word_io.seek(0)
            
            st.download_button(
                label="📥 Click aquí para descargar el archivo Word (.docx)",
                data=word_io,
                file_name="reporte_graficos_infiltracion.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    except Exception as e:
        with tab_resumen:
            st.error(f"❌ Ocurrió un error al procesar los datos: {e}")
else:
    with tab_resumen:
        st.info("👈 Por favor, seleccione el método de ingreso y cargue el archivo Excel o complete la tabla manual en la barra lateral para comenzar.")
