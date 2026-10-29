import streamlit as pd_st # Usaremos st para streamlit
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Configuración de la página con tema de azul Francia oscuro
st.set_page_config(
    page_title="Infiltración - Tensiómetro de Disco",
    page_icon="💧",
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

# Título principal
st.title("💧 Medición y Análisis de Infiltración a Campo")
st.subheader("Tensiómetro de Disco - Ecuación de Philip[cite: 1]")

# Barra lateral para configuración y carga de archivos
with st.sidebar:
    st.header("⚙️ Configuración del Ensayo")
    
    # Parámetro ajustable de la constante del tensiómetro (rango ampliado)
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
    
    st.markdown("---")
    st.info("💡 **Instrucciones:** Cada hoja del Excel debe contener las lecturas de campo en dos columnas (Columna 1: Tiempo en minutos, Columna 2: Lámina leída en cm).")

# Pie de página fijo requerido
st.markdown("""
    <div class="footer">
        Desarrollo: Ing. Agr. (Mgter.) Federico A. Paredes &nbsp;|&nbsp; Correo electrónico: paredesfedericoantonio@gmail.com
    </div>
""", unsafe_allow_html=True)

# Lógica principal de procesamiento
if archivo_subido is not None:
    try:
        # Cargar todas las hojas del archivo Excel
        xls = pd.ExcelFile(archivo_subido)
        sheet_names = xls.sheet_names
        
        # Selector de hoja (determinación a campo)
        st.sidebar.markdown("---")
        st.header("🔍 Selección de Ensayo")
        hoja_seleccionada = st.sidebar.selectbox("Seleccione la hoja de campo:", sheet_names)
        
        # Leer la hoja seleccionada
        df_raw = pd.read_excel(archivo_subido, sheet_name=hoja_seleccionada)
        
        # Validar que al menos tenga 2 columnas
        if df_raw.shape[1] < 2:
            st.error("⚠️ La hoja seleccionada debe tener al menos dos columnas (Tiempo y Lámina).")
        else:
            # Tomar las primeras dos columnas independientemente de los nombres de encabezado
            df = df_raw.iloc[:, :2].copy()
            df.columns = ['Tiempo_min', 'Lamina_cm']
            
            # Limpiar nulos y ordenar por tiempo
            df = df.dropna().sort_values(by='Tiempo_min').reset_index(drop=True)
            
            # Cálculos hidráulicos
            # Tiempo en horas
            df['Th_horas'] = df['Tiempo_min'] / 60.0
            
            # t parcial (horas)
            df['t_parcial_h'] = df['Th_horas'].diff()
            df.loc[0, 't_parcial_h'] = df.loc[0, 'Th_horas']
            
            # Lámina parcial multiplicada por la constante
            df['Lamina_parcial_cm'] = df['Lamina_cm'].diff() * constante_tensio
            df.loc[0, 'Lamina_parcial_cm'] = (df.loc[0, 'Lamina_cm'] - df.loc[0, 'Lamina_cm']) * constante_tensio # o valor inicial 0
            # Corrección rigurosa para el primer punto (si t=0, I=0 o delta inicial)
            df.loc[0, 'Lamina_parcial_cm'] = 0.0
            
            # Infiltración acumulada (Iacum)
            df['I_acumulada_cm'] = df['Lamina_parcial_cm'].cumsum()
            
            # Velocidad / Tasa de infiltración instantánea (cm/h) = dI / dt_parcial
            df['Vel_Infiltracion_cm_h'] = 0.0
            for i in range(1, len(df)):
                dt_h = df.loc[i, 'Th_horas'] - df.loc[i-1, 'Th_horas']
                if dt_h > 0:
                    df.loc[i, 'Vel_Infiltracion_cm_h'] = df.loc[i, 'Lamina_parcial_cm'] / dt_h
                else:
                    df.loc[i, 'Vel_Infiltracion_cm_h'] = 0.0
            
            # Raíz cuadrada del tiempo en horas (para Philip)
            df['Raiz_t'] = np.sqrt(df['Th_horas'])
            
            # Linealización de Philip: I_acumulada / Raiz_t (evitando división por cero en t=0)
            df['I_sobre_Raiz_t'] = 0.0
            df.loc[1:, 'I_sobre_Raiz_t'] = df.loc[1:, 'I_acumulada_cm'] / df.loc[1:, 'Raiz_t']
            
            # Cálculo de la Infiltración Básica (Ib) como promedio de los últimos 3 puntos estables
            n_puntos = len(df)
            if n_puntos >= 3:
                ib_valor = df['Vel_Infiltracion_cm_h'].iloc[-3:].mean()
            else:
                ib_valor = df['Vel_Infiltracion_cm_h'].iloc[-1]
                
            # Regresión lineal para Sorptividad (S) y Parámetro A usando los datos desde i=1
            df_reg = df.iloc[1:].copy()
            if len(df_reg) >= 2:
                slope, intercept, r_value, p_value, std_err = linregress(df_reg['Raiz_t'], df_reg['I_sobre_Raiz_t'])
                s_valor = intercept  # Ordenada al origen = Sorptividad (S)
                a_valor = slope      # Pendiente = Parámetro A
            else:
                s_valor, a_valor = 0.0, 0.0

            # Organizar Pestañas de Salida
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Resultados y Planilla", 
                "📈 Velocidad de Infiltración", 
                "📉 Lámina Acumulada", 
                "📐 Ecuación de Philip (Sortividad)"
            ])
            
            with tab1:
                st.header("Resultados Hidráulicos Generales")
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Infiltración Básica ($i_b$)", f"{ib_valor:.3f} cm/h")
                col_m2.metric("Sorptividad ($S$)", f"{s_valor:.3f} cm·h⁻⁰'⁵")
                col_m3.metric("Parámetro A", f"{a_valor:.3f} cm/h")
                
                st.markdown("---")
                st.subheader("Planilla Completa de Cálculos (Descargable)")
                st.dataframe(df, use_container_width=True)
                
                # Botón de descarga independiente para análisis estadístico posterior
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Resultados en Formato CSV (para análisis estadístico)",
                    data=csv_data,
                    file_name=f"resultados_infiltracion_{hoja_seleccionada}.csv",
                    mime="text/csv",
                )

            with tab2:
                st.header("Gráfico de Velocidad de Infiltración Instantánea")
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                ax2.plot(df['Tiempo_min'][1:], df['Vel_Infiltracion_cm_h'][1:], marker='o', color='#2563EB', linewidth=2, label='Velocidad Instantánea ($i_i$)')
                ax2.axhline(y=ib_valor, color='#DC2626', linestyle='--', linewidth=1.5, label=f'Infiltración Básica ($i_b$ = {ib_valor:.2f} cm/h)')
                ax2.set_xlabel('Tiempo (minutos)', fontsize=12, fontweight='bold', color='#1E3A8A')
                ax2.set_ylabel('Velocidad de Infiltración (cm/h)', fontsize=12, fontweight='bold', color='#1E3A8A')
                ax2.set_title(f'Tasa de Infiltración vs Tiempo - {hoja_seleccionada}', fontsize=14, fontweight='bold', color='#1E3A8A')
                ax2.grid(True, linestyle=':', alpha=0.6)
                ax2.legend()
                st.pyplot(fig2)

            with tab3:
                st.header("Gráfico de Lámina Acumulada")
                fig3, ax3 = plt.subplots(figsize=(10, 5))
                ax3.plot(df['Tiempo_min'], df['I_acumulada_cm'], marker='s', color='#1E3A8A', linewidth=2, label='Infiltración Acumulada ($I$)')
                ax3.set_xlabel('Tiempo (minutos)', fontsize=12, fontweight='bold', color='#1E3A8A')
                ax3.set_ylabel('Infiltración Acumulada (cm)', fontsize=12, fontweight='bold', color='#1E3A8A')
                ax3.set_title(f'Curva de Infiltración Acumulada - {hoja_seleccionada}', fontsize=14, fontweight='bold', color='#1E3A8A')
                ax3.grid(True, linestyle=':', alpha=0.6)
                ax3.legend()
                st.pyplot(fig3)

            with tab4:
                st.header("Linealización Gráfica para Estimación de la Sortividad ($S$)[cite: 1]")
                st.markdown(f"""
                * **Ecuación ajustada:** $\\frac{{I}}{{\\sqrt{{t}}}} = S + A \\cdot \\sqrt{{t}}$[cite: 1]
                * **Ordenada al origen ($S$ - Sorptividad):** `{s_valor:.4f} cm·h⁻⁰'⁵`[cite: 1]
                * **Pendiente ($A$ - Parámetro de transmisión):** `{a_valor:.4f} cm/h`[cite: 1]
                * **Coeficiente de determinación ($R^2$):** `{r_value**2:.4f}`
                """)
                
                fig4, ax4 = plt.subplots(figsize=(10, 5))
                ax4.scatter(df_reg['Raiz_t'], df_reg['I_sobre_Raiz_t'], color='#2563EB', s=50, label='Datos de campo transformados')
                
                # Línea de tendencia
                y_fit = intercept + slope * df_reg['Raiz_t']
                ax4.plot(df_reg['Raiz_t'], y_fit, color='#DC2626', linestyle='-', linewidth=2, label=f'Ajuste lineal: S = {s_valor:.2f}')
                
                ax4.set_xlabel('Raíz cuadrada del tiempo ($\\sqrt{t}$ en h$^{0.5}$)', fontsize=12, fontweight='bold', color='#1E3A8A')
                ax4.set_ylabel('$I / \\sqrt{t}$ (cm / h$^{0.5}$)', fontsize=12, fontweight='bold', color='#1E3A8A')
                ax4.set_title(f'Determinación Gráfica de la Sortividad - {hoja_seleccionada}', fontsize=14, fontweight='bold', color='#1E3A8A')
                ax4.grid(True, linestyle=':', alpha=0.6)
                ax4.legend()
                st.pyplot(fig4)

    except Exception as e:
        st.error(f"❌ Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, cargue un archivo de planilla de cálculo (.xlsx) en la barra lateral para comenzar el análisis.")
