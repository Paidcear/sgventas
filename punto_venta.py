def render_punto_venta(ventas):
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    import streamlit.components.v1 as components

    from db import (
        obtener_producto_por_codigo,
        actualizar_stock
    )

    from db import obtener_productos

    productos = obtener_productos()


    if "carrito" not in st.session_state:
        st.session_state.carrito = []

    sub_opcion = st.sidebar.radio("Opciones", ["Ventas", "Gastos", "Corte de caja"])

    if sub_opcion == "Ventas":

        col1, col2 = st.columns(2)

        # ---------------- COLUMNA 1 ----------------
        with col1:

            if not productos:
                st.warning("No hay productos disponibles. Agrega productos primero.")
            else:
                st.subheader("Escaneo de productos")

                # -------- FORMULARIO PRINCIPAL --------
                with st.form("form_codigo_barra", clear_on_submit=True):
                    codigo_input = st.text_input("Código de barras 🟢", key="codigo_barra")
                    #submitted = st.write(f"**{codigo_input}**")

                    co1, co2 = st.columns(2)

                    with co1:
                        monto_manual = st.text_input("Monto manual 🟢")
                        
                    with co2:
                        cantidad_input = st.number_input(
                            "Cantidad",
                            min_value=1,
                            value=1,
                            step=1
                        )


                    submitted = st.form_submit_button("Agregar")

                    # JS foco automático
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

                # -------- PROCESAMIENTO --------
                if submitted:

                    # PRODUCTO NORMAL
                    if codigo_input:
                        producto = obtener_producto_por_codigo(codigo_input)

                        if not producto:
                            st.error(f"Código no encontrado: {codigo_input}")
                        else:
                            if producto["stock"] < cantidad_input:
                                st.error(
                                    f"Stock insuficiente. Disponible: {producto['stock']}"
                                )
                            else:
                                st.session_state.carrito.append({
                                    "codigo": producto["codigo"],
                                    "nombre": producto["nombre"],
                                    "precio": producto["precio"],
                                    "cantidad": cantidad_input
                                })

                    # INGRESO MANUAL
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
                            else:
                                st.error("El monto manual debe ser mayor que cero.")
                        except ValueError:
                            st.error("Monto manual inválido, ingresa un número válido.")

                    st.rerun()

        # ---------------- COLUMNA 2 ----------------
        with col2:
            st.subheader("Productos escaneados")

            if st.session_state.carrito:
                df_carrito = pd.DataFrame(st.session_state.carrito)
                df_carrito["subtotal"] = df_carrito["precio"] * df_carrito["cantidad"]

                df_vista = df_carrito.copy()
                df_vista["precio"] = df_vista["precio"].map("${:,.2f}".format)
                df_vista["cantidad"] = df_vista["cantidad"].map("{:,.2f}".format)
                df_vista["subtotal"] = df_vista["subtotal"].map("${:,.2f}".format)
                df_vista.index = range(1, len(df_vista) + 1)

                st.dataframe(df_vista, use_container_width=True)

                # ELIMINAR DEL CARRITO
                opciones = []
                for i, item in enumerate(st.session_state.carrito):
                    subtotal = item["precio"] * item["cantidad"]
                    etiqueta = f"{item['nombre']} – ${subtotal:,.2f}"
                    opciones.append((etiqueta, i))

                if opciones:
                    etiquetas_visibles = [et[0] for et in opciones]
                    seleccion = st.selectbox("Eliminar producto", etiquetas_visibles)
                    idx_a_eliminar = dict(opciones)[seleccion]

                    if st.button("Eliminar del carrito"):
                        eliminado = st.session_state.carrito[idx_a_eliminar]["nombre"]
                        del st.session_state.carrito[idx_a_eliminar]
                        st.success(f"Producto '{eliminado}' eliminado.")
                        st.rerun()

                # TOTAL
                total = df_carrito["subtotal"].apply(float).sum()
                #total = df_carrito["subtotal"].sum()
                st.sidebar.markdown("---")
                st.sidebar.title("Total de la compra")
                st.markdown(f"**Subtotal:** ${total:,.2f}")
                st.sidebar.markdown(
                    f"<div style='font-size: 80px; font-weight: bold; color: #2E8B57;'>${total:,.2f}</div>",
                    unsafe_allow_html=True
                )

                # REGISTRAR VENTA
                if st.sidebar.button("**Registrar venta**"):

                    # DESCONTAR STOCK EN BD
                    for item in st.session_state.carrito:
                        if item["codigo"] == "INGRESO":
                            continue

                        producto_db = obtener_producto_por_codigo(item["codigo"])
                        if producto_db:
                            nuevo_stock = producto_db["stock"] - item["cantidad"]
                            if nuevo_stock < 0:
                                nuevo_stock = 0
                            actualizar_stock(item["codigo"], nuevo_stock)

                    ventas.append({
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "items": st.session_state.carrito,
                        "total": total
                    })

                    st.session_state.carrito = []
                    st.success("Venta registrada correctamente.")
                    st.rerun()

            else:
                st.info("El carrito está vacío.")

            # JS foco automático
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
