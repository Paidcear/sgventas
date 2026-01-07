import mysql.connector
import os
import streamlit as st

# ------------------ CONEXIÓN ------------------
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )


# ======================================================
# ===================== PRODUCTOS ======================
# ======================================================

# -------- CREATE --------
def crear_producto(codigo, nombre, precio, stock=0):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO productos (codigo, nombre, precio, stock)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (codigo, nombre, precio, stock))

    conn.commit()
    cursor.close()
    conn.close()

def obtener_productos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT codigo, nombre, precio, stock
        FROM productos
        ORDER BY nombre
    """)

    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    return productos


# -------- READ (uno) --------
def obtener_producto(codigo):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM productos WHERE codigo = %s",
        (codigo,)
    )
    producto = cursor.fetchone()

    cursor.close()
    conn.close()
    return producto


# -------- READ (todos) --------
def obtener_productos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT codigo, nombre, precio, stock
        FROM productos
        ORDER BY nombre
    """)
    productos = cursor.fetchall()

    cursor.close()
    conn.close()
    return productos


# -------- UPDATE producto --------
def actualizar_producto(codigo, nombre, precio):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE productos
        SET nombre = %s,
            precio = %s
        WHERE codigo = %s
    """, (nombre, precio, codigo))

    conn.commit()
    cursor.close()
    conn.close()


# -------- UPDATE stock --------
def actualizar_stock(codigo, stock):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE productos
        SET stock = %s
        WHERE codigo = %s
    """, (stock, codigo))

    conn.commit()
    cursor.close()
    conn.close()


# -------- DELETE --------
def eliminar_producto(codigo):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM productos WHERE codigo = %s",
        (codigo,)
    )

    conn.commit()
    cursor.close()
    conn.close()


#-------SUMARSTOCK---------
def sumar_stock(codigo, cantidad):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE productos
        SET stock = stock + %s
        WHERE codigo = %s
    """, (cantidad, codigo))

    conn.commit()
    cursor.close()
    conn.close()

def obtener_producto_por_codigo(codigo):
    """
    Devuelve un producto por su código de barras.
    Retorna None si no existe.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT codigo, nombre, precio, stock
        FROM productos
        WHERE codigo = %s
    """, (codigo,))

    producto = cursor.fetchone()

    cursor.close()
    conn.close()

    return producto

def actualizar_stock(codigo, nuevo_stock):
    """
    Actualiza el stock de un producto sobrescribiendo el valor.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE productos
        SET stock = %s
        WHERE codigo = %s
    """, (int(nuevo_stock), codigo))

    conn.commit()
    cursor.close()
    conn.close()
