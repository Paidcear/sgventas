import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(
    page_title="SGVentas",
    page_icon="logo.png",
    layout="wide"
)

# ------------------ Utilidades ------------------
RUTA_PRODUCTOS = "productos.json"
RUTA_VENTAS = "ventas.json"

def cargar_datos(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_datos(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

# ------------------ Inicialización ------------------
if "carrito" not in st.session_state:
    st.session_state.carrito = []

if "form_estado" not in st.session_state:
    st.session_state.form_estado = {
        "codigo": "",
        "nombre": "",
        "precio": 0.0
    }

productos = cargar_datos(RUTA_PRODUCTOS)
ventas = cargar_datos(RUTA_VENTAS)

# ------------------ Sidebar ------------------
st.sidebar.title("Sistemas de Gestión de Ventas")
opcion = st.sidebar.selectbox("Menú", [
    "Punto de venta",
    "Catálogo de productos",
    "Registros del día"
])

# ------------------ Catálogo ------------------
if opcion == "Catálogo de productos":

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Registrar / Consultar")

    # Formulario solo para el código de barras
    with st.sidebar.form("form_codigo", clear_on_submit=True):
        codigo = st.text_input("Código de barras 🟢", key="codigo_input")
        submit_codigo = st.write(f"**{codigo}**")
        submit_codigo = st.form_submit_button("Registro manual")

    if submit_codigo:
        if not codigo:
            st.sidebar.error("Debe ingresar un código de barras válido.")
        else:
            st.session_state["codigo_value"] = codigo
            st.rerun()

    # Inyectar JS para enfocar automáticamente el campo
    components.html(
        """
        <script>
        setTimeout(function() {
            const inputs = window.parent.document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                    input.focus();
                    break;
                }
            }
        }, 100);
        </script>
        """,
        height=0
    )

    # Formulario para nombre y precio
    with st.sidebar.form("form_producto", clear_on_submit=True):
        nombre = st.text_input("Nombre del producto 🟢")
        precio = st.text_input("Precio")
        submitted = st.form_submit_button("Agregar producto")

    if submitted:
        try:
            precio_float = float(precio)
            codigo = st.session_state.get("codigo_value", "").strip()
            if not codigo or not nombre or precio_float <= 0:
                st.sidebar.error("Debe completar todos los campos obligatorios.")
                # Inyectar JS para enfocar automáticamente el campo
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Nombre del producto 🟢" || input.ariaLabel === "Nombre del producto 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )
            elif any(str(p["codigo"]).strip() == codigo for p in productos):
                st.sidebar.error("El código de barras ya está registrado.")
            else:
                productos.append({
                    "codigo": codigo,
                    "nombre": nombre,
                    "precio": precio_float
                })
                guardar_datos(RUTA_PRODUCTOS, productos)
                st.sidebar.success("Producto agregado correctamente.")
                st.session_state["codigo_value"] = ""
                st.rerun()
        except ValueError:
            st.sidebar.error("El precio debe ser un número válido.")
        # Inyectar JS para enfocar automáticamente el campo
        components.html(
            """
            <script>
            setTimeout(function() {
                const inputs = window.parent.document.querySelectorAll('input');
                for (let input of inputs) {
                    if (input.placeholder === "Nombre del producto 🟢" || input.ariaLabel === "Nombre del producto 🟢") {
                        input.focus();
                        break;
                    }
                }
            }, 100);
            </script>
            """,
            height=0
        )
        st.rerun()


    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Productos registrados")

        if productos:
            # Crear DataFrame con código como índice
            df = pd.DataFrame(productos)
            df.set_index("codigo", inplace=True)

            # Formatear el precio como moneda (guardamos copia original para estilo)
            df["precio"] = df["precio"].astype(float)
            df_styled = df.copy()
            df_styled["precio"] = df_styled["precio"].map("${:,.2f}".format)

            # Campo de búsqueda por nombre
            filtro = st.text_input("Buscar producto")

            # Determinar si hay código escaneado
            codigo_actual = st.session_state.get("codigo_value", "")

            # Determinar si hay código escaneado
            codigo_actual = st.session_state.get("codigo_value", "")

            def resaltar_codigo(row):
                if str(row.name).strip() == str(codigo_actual).strip():
                    return ["background-color: #088602"] * len(row)  # verde claro
                return [""] * len(row)

            if filtro:
                df_filtrado = df_styled[df_styled["nombre"].str.contains(filtro, case=False, na=False)]
                df_filtrado = df_filtrado.style.apply(resaltar_codigo, axis=1)
                st.write(df_filtrado, use_container_width=True)
            else:
                df_formateado = df_styled.style.apply(resaltar_codigo, axis=1)
                st.write(df_formateado, use_container_width=True)


        else:
            st.info("No hay productos registrados.")


    # --- Importar desde CSV ---
    importar_csv = st.sidebar.checkbox("Importar desde CSV")

    if importar_csv:
        archivo_csv = st.sidebar.file_uploader("Selecciona un archivo CSV", type=["csv"], key="archivo_csv")

        if archivo_csv is not None:
            try:
                df_importado = pd.read_csv(archivo_csv)

                # Validar columnas necesarias
                columnas_requeridas = {"codigo", "nombre", "precio"}
                if not columnas_requeridas.issubset(df_importado.columns):
                    st.sidebar.error("El archivo debe contener las columnas: codigo, nombre y precio.")
                else:
                    # Crear copia para evitar modificar df original
                    df_mostrado = df_importado.copy()

                    # Resetear índice a partir de 1
                    df_mostrado.index = range(1, len(df_mostrado) + 1)

                    st.subheader("Vista previa del catálogo importado")
                    st.dataframe(df_mostrado, use_container_width=True)

                    confirmar = st.button("Importar datos")

                    if confirmar:
                        # Convertir a lista de dicts y filtrar duplicados
                        nuevos_productos = df_importado.to_dict(orient="records")
                        codigos_existentes = {p["codigo"] for p in productos}
                        nuevos_sin_duplicados = [p for p in nuevos_productos if p["codigo"] not in codigos_existentes]

                        if nuevos_sin_duplicados:
                            productos.extend(nuevos_sin_duplicados)
                            guardar_datos(RUTA_PRODUCTOS, productos)
                            st.success(f"Se han importado {len(nuevos_sin_duplicados)} productos nuevos correctamente.")
                            st.rerun()
                        else:
                            st.info("Todos los productos ya existen en el catálogo. No se importó ningún registro.")
            except Exception as e:
                st.sidebar.error(f"Error al leer el archivo CSV: {e}")


    with col2:
        st.markdown("### Editar / Eliminar producto")

        # Tomar el código ya ingresado en el formulario de registro
        codigo_edicion = st.session_state.get("codigo_input", "").strip()

        # Buscar el producto por código (limpiando espacios y forzando tipo str)
        producto_sel_idx = next(
            (
                i for i, p in enumerate(productos)
                if str(p.get("codigo", "")).strip() == codigo_edicion
            ),
            None
        )

        if producto_sel_idx is not None:
            producto_sel = productos[producto_sel_idx]

            nuevo_nombre = st.text_input("Nuevo nombre", value=producto_sel["nombre"], key="edit_nombre")
            nuevo_precio = st.text_input("Nuevo precio", value=str(producto_sel["precio"]), key="edit_precio")
            #nuevo_precio = st.number_input("Nuevo precio", min_value=0.1, value==str(producto_sel["precio"]), step=1.0, key="edit_precio")
            # Inyectar JS para enfocar automáticamente el campo
            components.html(
                """
                <script>
                setTimeout(function() {
                    const inputs = window.parent.document.querySelectorAll('input');
                    for (let input of inputs) {
                        if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                            input.focus();
                            break;
                        }
                    }
                }, 100);
                </script>
                """,
                height=0
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Guardar cambios"):
                    try:
                        productos[producto_sel_idx]["nombre"] = nuevo_nombre
                        productos[producto_sel_idx]["precio"] = float(nuevo_precio)
                        guardar_datos(RUTA_PRODUCTOS, productos)
                        st.success("Producto actualizado correctamente.")
                        st.rerun()
                    except ValueError:
                        st.error("El precio debe ser un número válido.")
                # Inyectar JS para enfocar automáticamente el campo
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )

            with col2:
                if st.button("Eliminar producto"):
                    del productos[producto_sel_idx]
                    guardar_datos(RUTA_PRODUCTOS, productos)
                    st.success("Producto eliminado correctamente.")
                    st.rerun()

        else:
            if codigo_edicion:
                # Inyectar JS para enfocar automáticamente el campo
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Nombre del producto 🟢" || input.ariaLabel === "Nombre del producto 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )
                st.info("Para modificar o eliminar, primero asegúrate de registrar el producto o escanear un código válido.")
        


# ------------------ Punto de Venta ------------------
elif opcion == "Punto de venta":
    sub_opcion = st.sidebar.radio("Opciones", ["Ventas", "Gastos", "Corte de caja"])

    if sub_opcion == "Ventas":

        col1, col2 = st.columns(2)
        with col1:

            if not productos:
                st.warning("No hay productos disponibles. Agrega productos primero.")
            else:
                st.subheader("Escaneo de productos")

                # Formulario para escanear
                with st.form("form_codigo_barra", clear_on_submit=True):
                    codigo_input = st.text_input("Código de barras 🟢", key="codigo_barra")

                    co1, co2 = st.columns(2)
                    with co1:
                        monto_manual = st.text_input("Monto manual 🟢", key="monto_manual")
                    with co2:
                        cantidad_input = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.25, key="cantidad_barra")
                    #with co3:
                        #gramos_input = st.text_input("Gramos 🟡", key="gramos_input")

                    submitted = st.form_submit_button("Agregar")

                # Inyectar JS para enfocar automáticamente el campo de código de barras
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )

                # Procesamiento del formulario
                if submitted:
                    if codigo_input:
                        producto = next((p for p in productos if p["codigo"] == codigo_input), None)
                        if producto:
                            st.session_state.carrito.append({
                                "codigo": producto["codigo"],
                                "nombre": producto["nombre"],
                                "precio": producto["precio"],
                                "cantidad": cantidad_input
                            })
                            st.rerun()
                        else:
                            st.error(f"Código no encontrado: {codigo_input}")

                    # Inyectar JS para enfocar automáticamente el campo de código de barras
                    components.html(
                        """
                        <script>
                        setTimeout(function() {
                            const inputs = window.parent.document.querySelectorAll('input');
                            for (let input of inputs) {
                                if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                    input.focus();
                                    break;
                                }
                            }
                        }, 100);
                        </script>
                        """,
                        height=0
                    )

                    if monto_manual:
                        try:
                            monto_valor = float(monto_manual)
                            if monto_valor > 0:
                                st.session_state.carrito.append({
                                    "codigo": "INGRESO",
                                    "nombre": "VARIOS",
                                    "precio": monto_valor,
                                    "cantidad": 1
                                })
                                st.rerun()
                            else:
                                st.error("El monto manual debe ser mayor que cero.")
                        except ValueError:
                            st.error("Monto manual inválido, ingresa un número válido.")

                # Inyectar JS para enfocar automáticamente el campo de código de barras
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )



        with col2:
            st.subheader("Productos escaneados")

            if st.session_state.carrito:
                df_carrito = pd.DataFrame(st.session_state.carrito)
                df_carrito["subtotal"] = df_carrito["precio"] * df_carrito["cantidad"]

                # Formato de moneda
                df_vista = df_carrito.copy()
                df_vista["precio"] = df_vista["precio"].map("${:,.2f}".format)
                df_vista["cantidad"] = df_vista["cantidad"].map("{:,.2f}".format)
                df_vista["subtotal"] = df_vista["subtotal"].map("${:,.2f}".format)

                # Índice desde 1
                df_vista.index = range(1, len(df_vista) + 1)

                # Mostrar tabla formateada
                st.dataframe(df_vista, use_container_width=True)

                # --- Eliminar productos del carrito por nombre + subtotal ---

                # Crear lista de opciones con etiqueta personalizada y su índice en el carrito
                opciones = []
                for i, item in enumerate(st.session_state.carrito):
                    subtotal = item["precio"] * item["cantidad"]
                    etiqueta = f"{item['nombre']} – ${subtotal:,.2f}"
                    opciones.append((etiqueta, i))  # (etiqueta visible, índice en carrito)

                if opciones:
                    etiquetas_visibles = [et[0] for et in opciones]
                    seleccion = st.selectbox("Eliminar producto", etiquetas_visibles)

                    # Buscar el índice interno usando la etiqueta seleccionada
                    idx_a_eliminar = dict(opciones)[seleccion]

                    if st.button("Eliminar del carrito"):
                        eliminado = st.session_state.carrito[idx_a_eliminar]["nombre"]
                        del st.session_state.carrito[idx_a_eliminar]
                        st.success(f"Producto '{eliminado}' eliminado.")
                        st.rerun()

                # Inyectar JS para enfocar automáticamente el campo de código de barras
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )



                # Calcular total real
                total = df_carrito["subtotal"].sum()

                # Mostrar total destacado
                st.sidebar.markdown("---")
                st.sidebar.title("Total de la compra")
                st.sidebar.markdown(f"**Subtotal:** ${total:,.2f}")
                st.sidebar.markdown(
                    f"<div style='font-size: 80px; font-weight: bold; color: #2E8B57;'>${total:,.2f}</div>",
                    unsafe_allow_html=True
                )

                # Botón para finalizar venta
                if st.sidebar.button("**Registrar venta**"):
                    ventas.append({
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "items": st.session_state.carrito,
                        "total": total
                    })
                    guardar_datos(RUTA_VENTAS, ventas)
                    st.session_state.carrito = []
                    st.success("Venta registrada correctamente.")
                    st.rerun()
            else:
                st.info("El carrito está vacío.")

            # Inyectar JS para enfocar automáticamente el campo de código de barras
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )

#--------------- Gastos ----------------------------
    elif sub_opcion == "Gastos":
        accion = st.sidebar.selectbox("Acciones", ["Agregar", "Proveedores"])
        if accion == "Agregar":

            col1, col2 = st.columns(2)

            if "gastos" not in st.session_state:
                st.session_state.gastos = cargar_datos("gastos.json")

            if "proveedores" not in st.session_state:
                st.session_state.proveedores = cargar_datos("proveedores.json")

            proveedores_disponibles = [p["nombre"] for p in st.session_state.proveedores]

            with col1:
                st.subheader("Registrar gasto")

                with st.form("form_gasto", clear_on_submit=True):
                    proveedor = st.selectbox("Proveedor", opciones := proveedores_disponibles)
                    co1, co2 = st.columns(2)
                    with co1:
                        monto = st.text_input("Monto")
                    with co2:
                        fecha = st.date_input("Fecha", value=datetime.now())
                    submitted = st.form_submit_button("Registrar gasto")

                if submitted:
                    try:
                        monto_float = float(monto)
                        if not proveedor or monto_float <= 0:
                            st.error("Por favor selecciona un proveedor y un monto válido.")
                        else:
                            nuevo_gasto = {
                                "proveedor": proveedor,
                                "monto": monto_float,
                                "fecha": fecha.strftime("%Y-%m-%d")
                            }
                            st.session_state.gastos.append(nuevo_gasto)
                            guardar_datos("gastos.json", st.session_state.gastos)
                            st.success("Gasto registrado correctamente.")
                            st.rerun()
                    except ValueError:
                        st.error("El monto debe ser un número válido.")

            with col2:
                st.subheader("Editar / Eliminar gasto")

                if st.session_state.gastos:
                    opciones = []
                    for i, g in enumerate(st.session_state.gastos):
                        etiqueta = f"{g['fecha']} – {g['proveedor']} – ${g['monto']:,.2f}"
                        opciones.append((etiqueta, i))

                    etiquetas_visibles = [et[0] for et in opciones]
                    seleccion = st.selectbox("Selecciona un gasto", etiquetas_visibles, label_visibility="collapsed")
                    idx_seleccionado = dict(opciones)[seleccion]
                    gasto = st.session_state.gastos[idx_seleccionado]

                    proveedor_edit = st.selectbox("Proveedor", proveedores_disponibles, index=proveedores_disponibles.index(gasto["proveedor"]))
                    monto_edit = st.text_input("Monto", value=str(gasto["monto"]))
                    fecha_edit = st.date_input("Fecha", value=datetime.strptime(gasto["fecha"], "%Y-%m-%d"))

                    col_ed1, col_ed2 = st.columns(2)
                    with col_ed1:
                        if st.button("Actualizar gasto"):
                            try:
                                monto_float = float(monto_edit)
                                gasto["proveedor"] = proveedor_edit
                                gasto["monto"] = monto_float
                                gasto["fecha"] = fecha_edit.strftime("%Y-%m-%d")
                                guardar_datos("gastos.json", st.session_state.gastos)
                                st.success("Gasto actualizado correctamente.")
                                st.rerun()
                            except ValueError:
                                st.error("El monto debe ser un número válido.")

                    with col_ed2:
                        if st.button("Eliminar gasto"):
                            eliminado = st.session_state.gastos[idx_seleccionado]
                            del st.session_state.gastos[idx_seleccionado]
                            guardar_datos("gastos.json", st.session_state.gastos)
                            st.success(f"Gasto del proveedor '{eliminado['proveedor']}' eliminado.")
                            st.rerun()
                else:
                    st.info("No hay gastos registrados.")


# ----------------------
        if accion == "Proveedores":
            

            if "proveedores" not in st.session_state:
                st.session_state.proveedores = cargar_datos("proveedores.json")

            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

            # --- Registro desde sidebar ---
            st.sidebar.markdown("### Registrar proveedor")
            with st.sidebar.form("form_proveedor", clear_on_submit=True):
                nombre = st.text_input("Nombre del proveedor")
                dias = st.multiselect("Días de entrega", options=dias_semana)
                submitted = st.form_submit_button("Registrar")

            if submitted:
                if not nombre or not dias:
                    st.sidebar.error("Debes ingresar el nombre y al menos un día.")
                elif any(p["nombre"].lower() == nombre.lower() for p in st.session_state.proveedores):
                    st.sidebar.error("Este proveedor ya está registrado.")
                else:
                    st.session_state.proveedores.append({
                        "nombre": nombre,
                        "dia": dias  # Se guarda como lista
                    })
                    guardar_datos("proveedores.json", st.session_state.proveedores)
                    st.sidebar.success("Proveedor registrado correctamente.")
                    st.rerun()

            # --- Panel principal dividido en 2 columnas ---
            col1, col2 = st.columns([1, 1])

            # Columna 1: Mostrar proveedores con filtros en columnas
            with col1:
                st.markdown("### Lista de proveedores")

                if st.session_state.proveedores:
                    df_prov = pd.DataFrame(st.session_state.proveedores)

                    # Asegurar que la columna 'dia' sea lista
                    df_prov["dia"] = df_prov["dia"].apply(lambda d: d if isinstance(d, list) else [])

                    # Controles de filtros en columnas
                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        nombre_filtro = st.text_input("Buscar por nombre", key="filtro_nombre")

                    with col_f2:
                        dias_filtro = st.multiselect("Filtrar por día", dias_semana, key="filtro_dias")

                    # Aplicar filtros
                    if nombre_filtro:
                        df_prov = df_prov[df_prov["nombre"].str.contains(nombre_filtro, case=False, na=False)]

                    if dias_filtro:
                        df_prov = df_prov[df_prov["dia"].apply(lambda dias: any(d in dias for d in dias_filtro))]

                    # Convertir días a texto para mostrar
                    df_prov["dia_str"] = df_prov["dia"].apply(lambda d: ", ".join(d))
                    df_prov.index = range(1, len(df_prov) + 1)

                    # Solo columnas que queremos mostrar
                    df_mostrar = df_prov[["nombre", "dia_str"]]

                    def resaltar_nombre(row):
                        color_fila = ""
                        dias = df_prov.loc[row.name, "dia"]
                        if not isinstance(dias, list):
                            dias = []

                        if dias_filtro and any(d in dias for d in dias_filtro):
                            color_fila = "background-color: #90EE9055"  # Verde suave

                        # Crear una lista vacía para todas las columnas (sin color)
                        colores = [""] * len(row)
                        # Buscar índice de la columna "nombre" para pintar solo esa celda
                        idx_nombre = df_mostrar.columns.get_loc("nombre")
                        colores[idx_nombre] = color_fila
                        return colores

                    df_estilado = df_mostrar.style.apply(resaltar_nombre, axis=1)

                    st.dataframe(df_estilado, use_container_width=True)

                else:
                    st.info("No hay proveedores registrados.")


            # Columna 2: Editar o eliminar
            with col2:
                st.markdown("### Modificar/Eliminar proveedor")

                if st.session_state.proveedores:
                    nombres = [p["nombre"] for p in st.session_state.proveedores]
                    seleccion = st.selectbox("Selecciona un proveedor", nombres)

                    proveedor = next((p for p in st.session_state.proveedores if p["nombre"] == seleccion), None)

                    if proveedor:
                        nuevo_nombre = st.text_input("Nuevo nombre", value=proveedor["nombre"], key="edit_nombre_prov")
                        nuevos_dias = st.multiselect(
                            "Nuevos días de entrega",
                            options=dias_semana,
                            default=proveedor.get("dia", []) if isinstance(proveedor.get("dia", []), list) else []
                        )

                        col_ed, col_del, col3, col4 = st.columns(4)
                        with col_ed:
                            if st.button("Guardar cambios"):
                                proveedor["nombre"] = nuevo_nombre
                                proveedor["dia"] = nuevos_dias
                                guardar_datos("proveedores.json", st.session_state.proveedores)
                                st.success("Proveedor actualizado correctamente.")
                                st.rerun()
                        with col_del:
                            if st.button("Eliminar proveedor"):
                                st.session_state.proveedores = [
                                    p for p in st.session_state.proveedores if p["nombre"] != seleccion
                                ]
                                guardar_datos("proveedores.json", st.session_state.proveedores)
                                st.success("Proveedor eliminado correctamente.")
                                st.rerun()
                else:
                    st.info("No hay proveedores para editar o eliminar.")


#--------------- Corte de caja ----------------------------
    elif sub_opcion == "Corte de caja":
        st.title("Corte de Caja")
        if ventas:
            df_hist = pd.DataFrame([
                {
                    "fecha": v["fecha"],
                    "total": v["total"]
                }
                for v in ventas
            ])
            total_general = df_hist["total"].sum()
            st.dataframe(df_hist)
            st.write(f"Total de ventas: ${total_general:.2f}")
        else:
            st.info("No hay ventas registradas.")

# ------------------ Registro de ventas del día ------------------
elif opcion == "Registros del día":
    col1, col2 = st.columns(2)
    with col1:
        st.sidebar.title("Ventas del día")
        st.write("**Ventas**")
        if ventas:
            df_hist = pd.DataFrame([
                {
                    "fecha": v["fecha"],
                    "total": v["total"]
                }
                for v in ventas
            ])
            st.line_chart(df_hist.set_index("fecha"))
            st.write("---")
            st.write("Resúmen de ventas")

            # Clonar el DataFrame para no alterar el original
            df_vista = df_hist.copy()
            df_vista.index = range(1, len(df_vista) + 1)  # Índice desde 1

            df_vista["total"] = df_vista["total"].astype(float).map("${:,.2f}".format)
            st.dataframe(df_vista, use_container_width=True)

            # Calcular el total general normalmente
            total_general = df_hist["total"].sum()
            st.sidebar.markdown(
                        f"<div style='font-size: 50px; font-weight: bold; color: #2E8B57;'>${total_general:,.2f}</div>",    #Total general: 
                        unsafe_allow_html=True
                    )
        else:
            st.info("No hay datos disponibles.")


#---------------------------------------------
        with st.expander("Registro de Ventas"):

            if ventas:
                for venta in reversed(ventas):
                    st.markdown(f"Fecha: {venta['fecha']}")

                    # Crear DataFrame y calcular subtotal
                    df = pd.DataFrame(venta["items"])
                    df["subtotal"] = df["precio"] * df["cantidad"]

                    # Formatear columnas numéricas como moneda
                    df["precio"] = df["precio"].map("${:,.2f}".format)
                    df["subtotal"] = df["subtotal"].map("${:,.2f}".format)

                    # Ajustar índice visual desde 1
                    df.index = range(1, len(df) + 1)

                    # Mostrar tabla
                    st.dataframe(df, use_container_width=True)

                    # Mostrar total
                    st.write(f"Total: ${venta['total']:.2f}")
                    st.markdown("---")
            else:
                st.info("No hay ventas registradas.")

    with col2:
        st.sidebar.write("---")
        st.sidebar.title("Gastos del día")
        st.write("**Gastos**")

        gastos = st.session_state.get("gastos", [])

        if gastos:

            # Crear un dataframe con fecha y monto
            df_gastos = pd.DataFrame([
                {
                    "proveedor": g.get("proveedor", "N/A"),
                    #"fecha": g.get("fecha", ""),
                    "total": g.get("total", g.get("monto", 0))  # intenta total, sino monto, sino 0
                }
                for g in gastos
            ])

            # Agrupar por fecha sumando total para graficar resumen diario
            df_gastos_resumen = df_gastos.groupby("proveedor", as_index=False).sum()

            st.line_chart(df_gastos_resumen.set_index("proveedor"))
            st.write("---")
            st.write("Resúmen de gastos")

            # Clonar y preparar para mostrar
            df_gvista = df_gastos_resumen.copy()
            df_gvista.index = range(1, len(df_gvista) + 1)

            df_gvista["total"] = df_gvista["total"].astype(float).map("${:,.2f}".format)
            st.dataframe(df_gvista, use_container_width=True)

            # Total general sumando todos los montos
            #with st.sidebar.container():
            total_gastos = df_gastos["total"].sum()
            st.sidebar.markdown(
                    f"<div style='font-size: 50px; font-weight: bold; color: #B22222;'>${total_gastos:,.2f}</div>",    #Gasto total:
                unsafe_allow_html=True
            )
        else:
            st.info("No hay gastos registrados.")

        with st.expander("Registro de Gastos"):

            if gastos:
                for gasto in reversed(gastos):
                    proveedor = gasto.get("proveedor", "Sin proveedor")
                    total = gasto.get("total", gasto.get("monto", 0))   

                    st.write(f"Proveedor: **{proveedor}**")
                    st.write(f"Total: ${total:.2f}")
                    st.markdown("---")
            else:
                st.info("No hay gastos registrados.")

