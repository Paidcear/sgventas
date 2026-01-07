# SGVentas.py
import streamlit as st
from catalogo import render_catalogo
from punto_venta import render_punto_venta


# Datos compartidos (temporalmente en memoria)
if "productos" not in st.session_state:
    st.session_state.productos = []

if "ventas" not in st.session_state:
    st.session_state.ventas = []

productos = st.session_state.productos
ventas = st.session_state.ventas


# Configuración base
st.set_page_config(
    page_title="SGVentas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ Sidebar ------------------
st.sidebar.title("SGVentas")

opcion = st.sidebar.selectbox(
    "Menú principal",
    [
        "Punto de venta",
        "Catálogo",
        #"Inventario",
        "Registros del día"
    ]
)

# ------------------ Enrutador de módulos ------------------
if opcion == "Punto de venta":
    render_punto_venta(ventas)

elif opcion == "Catálogo":
    render_catalogo()

#elif opcion == "Inventario":
    #render_inventario()

elif opcion == "Registros del día":
    st.header("Registros del día")
    st.info("Módulo de registros en construcción")
