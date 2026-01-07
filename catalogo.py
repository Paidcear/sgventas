import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from db import (
    obtener_productos,
    crear_producto,
    actualizar_producto,
    eliminar_producto
)

# ------------------ Render Catálogo ------------------
def render_catalogo():

    # -------- Obtener productos desde BD --------
    productos = obtener_productos()

    if "codigo_value" not in st.session_state:
        st.session_state.codigo_value = ""

    # ------------------ Sidebar ------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Registrar / Consultar")

    # -------- Form código de barras --------
    with st.sidebar.form("form_codigo", clear_on_submit=True):
        codigo = st.text_input("Código de barras 🟢", key="codigo_input")
        submit_codigo = st.write(f"**{codigo}**")
        submit_codigo = st.form_submit_button("Registro manual")

    if submit_codigo:
        if not codigo:
            st.sidebar.error("Debe ingresar un código de barras válido.")
        else:
            st.session_state.codigo_value = codigo
            st.rerun()

    # -------- JS focus código --------
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

    # -------- Form producto --------
    with st.sidebar.form("form_producto", clear_on_submit=True):
        nombre = st.text_input("Nombre del producto 🟢")
        precio = st.text_input("Precio")
        stock = st.number_input("Stock inicial", min_value=0, step=1)
        submitted = st.form_submit_button("Agregar producto")

    if submitted:
        try:
            precio_float = float(precio)
            codigo_val = st.session_state.get("codigo_value", "").strip()

            if not codigo_val or not nombre or precio_float <= 0:
                st.sidebar.error("Debe completar todos los campos obligatorios.")
            elif any(str(p["codigo"]).strip() == codigo_val for p in productos):
                st.sidebar.error("El código de barras ya está registrado.")
            else:
                crear_producto(
                    codigo=codigo_val,
                    nombre=nombre,
                    precio=precio_float,
                    stock=stock
                )
                st.sidebar.success("Producto agregado correctamente.")
                st.session_state.codigo_value = ""
                st.rerun()
        except ValueError:
            st.sidebar.error("El precio debe ser un número válido.")

    # ------------------ Panel principal ------------------
    col1, col2 = st.columns(2)

    # -------- Productos registrados --------
    with col1:
        st.subheader("Productos registrados")

        if productos:
            df = pd.DataFrame(productos)
            df.set_index("codigo", inplace=True)

            df_styled = df.copy()
            df_styled["precio"] = df_styled["precio"].map("${:,.2f}".format)

            filtro = st.text_input("Buscar producto")
            codigo_actual = st.session_state.get("codigo_value", "")

            def resaltar_codigo(row):
                if str(row.name).strip() == str(codigo_actual).strip():
                    return ["background-color: #088602"] * len(row)
                return [""] * len(row)

            if filtro:
                df_filtrado = df_styled[
                    df_styled["nombre"].str.contains(filtro, case=False, na=False)
                ]
                st.write(df_filtrado.style.apply(resaltar_codigo, axis=1))
            else:
                st.write(df_styled.style.apply(resaltar_codigo, axis=1))
        else:
            st.info("No hay productos registrados.")


    # -------- Editar / Eliminar --------
    with col2:
        st.markdown("### Editar / Eliminar producto")

        codigo_edicion = st.session_state.get("codigo_input", "").strip()
        producto_sel_idx = next(
            (i for i, p in enumerate(productos) if str(p["codigo"]).strip() == codigo_edicion),
            None
        )

        if producto_sel_idx is not None:
            producto_sel = productos[producto_sel_idx]

            nuevo_nombre = st.text_input(
                "Nuevo nombre",
                value=producto_sel["nombre"]
            )

            nuevo_precio = st.text_input(
                "Nuevo precio",
                value=str(producto_sel["precio"])
            )

            col1, col2 = st.columns(2)

            with col1:
                agregar_stock = st.number_input(
                    "Agregar stock",
                    min_value=0,
                    step=1,
                    value=0
                )

            with col2:
                nuevo_stock = st.number_input(
                    "Nuevo stock",
                    min_value=0,
                    step=1,
                    value=producto_sel["stock"]
                    #disabled="True"
                )

            c1, c2 = st.columns(2)

            with c1:
                if st.button("Guardar cambios", use_container_width="True"):
                    try:
                        from db import actualizar_stock, sumar_stock

                        productos[producto_sel_idx]["nombre"] = nuevo_nombre
                        productos[producto_sel_idx]["precio"] = float(nuevo_precio)

                        if agregar_stock > 0:
                            sumar_stock(producto_sel["codigo"], agregar_stock)
                            productos[producto_sel_idx]["stock"] += agregar_stock
                        else:
                            actualizar_stock(producto_sel["codigo"], nuevo_stock)
                            productos[producto_sel_idx]["stock"] = nuevo_stock

                        st.success("Producto actualizado correctamente.")
                        st.rerun()

                    except ValueError:
                        st.error("El precio debe ser un número válido.")


            with c2:
                if st.button("Eliminar producto", use_container_width="True"):
                    del productos[producto_sel_idx]
                    st.success("Producto eliminado correctamente.")
                    st.rerun()

        else:
            if codigo_edicion:
                st.info(f"Agregar producto **{codigo}**")

                # JS foco automático
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

