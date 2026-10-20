import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import json
import threading
import time
import urllib.request

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA CORPORATIVA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Frumix C.A. - ERP B2B Enterprise Elite",
    page_icon="🍓",
    layout="wide",
)

# Limpieza total de caché en arranque
st.cache_data.clear()

# ---------------------------------------------------------
# SISTEMA KEEP-ALIVE BLINDADO PARA CLOUD 24/7
# ---------------------------------------------------------
def keep_alive():
    while True:
        try:
            urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=5)
        except:
            pass
        time.sleep(120)

threading.Thread(target=keep_alive, daemon=True).start()

# ---------------------------------------------------------
# BASE DE DATOS RELACIONAL INTEGRAL (SQLITE) - V17.1 ESTABLE
# ---------------------------------------------------------
DB_NAME = "frumix_enterprise_elite_v17_1.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matriz TEXT,
            sucursal TEXT,
            segmento TEXT,
            tarifa TEXT,
            dupla TEXT,
            telefono TEXT,
            contacto TEXT,
            limite_credito_dias INTEGER DEFAULT 15,
            limite_credito_dolares REAL DEFAULT 15000.0,
            ultimo_pedido TEXT
        )
    """)
    
    # 2. Catálogo Base
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matriz_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            barra TEXT,
            descripcion TEXT,
            calibre TEXT,
            clasificacion_calidad TEXT,
            empaque_kg REAL,
            costo_caja REAL,
            precio_caja REAL,
            precio_kg REAL,
            margen_pct REAL
        )
    """)
    
    # 3. Pedidos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_pedido TEXT,
            cliente TEXT,
            sucursal TEXT,
            realizado_por TEXT,
            atendido_por TEXT,
            recibido_por TEXT,
            datos_importantes TEXT,
            fecha_pedido TEXT,
            monto_total REAL,
            costo_total REAL,
            ganancia_estimada REAL,
            estatus_despacho TEXT,
            detalle_json TEXT
        )
    """)

    # 4. Cobranza
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cobranza (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_factura TEXT,
            cliente TEXT,
            fecha_emision TEXT,
            fecha_vencimiento TEXT,
            monto_factura REAL,
            monto_pagado REAL,
            estatus_pago TEXT
        )
    """)

    # 5. Inventario por Fruta y Calibre
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            producto TEXT,
            calibre TEXT,
            stock_cajas REAL,
            costo_unitario_caja REAL,
            fecha_ingreso TEXT
        )
    """)

    # 5.1. Kardex Movimientos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            producto TEXT,
            calibre TEXT,
            tipo_movimiento TEXT,
            cantidad REAL,
            motivo TEXT,
            fecha_movimiento TEXT,
            responsable TEXT
        )
    """)

    # 6. Mermas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mermas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            producto TEXT,
            calibre TEXT,
            cantidad_perdida REAL,
            costo_unitario REAL,
            perdida_monetaria REAL,
            motivo TEXT,
            fecha_merma TEXT
        )
    """)

    # 6.1. Devoluciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devoluciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_pedido TEXT,
            cliente TEXT,
            sucursal TEXT,
            producto TEXT,
            calibre TEXT,
            cantidad_devuelta REAL,
            motivo_devolucion TEXT,
            destino_merma TEXT,
            fecha_devolucion TEXT
        )
    """)

    # 7. Embudo de Ventas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embudo_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            negocio TEXT,
            cliente TEXT,
            etapa_embudo TEXT,
            valor_estimado REAL,
            probabilidad TEXT,
            responsable TEXT,
            fecha_actualizacion TEXT
        )
    """)

    conn.commit()

    # Cargar Catálogo Base si está vacío
    cursor.execute("SELECT COUNT(*) FROM matriz_precios")
    if cursor.fetchone()[0] == 0:
        catalogo_inicial = [
            ("759101", "759101", "MANZANA GALA", "80/88", "Premium", 19.0, 50.0, 68.0, 3.58, 26.5),
            ("759102", "759102", "MANZANA ROJA", "100/110", "Con detalle", 19.0, 60.0, 80.0, 4.21, 25.0),
            ("759103", "759103", "MANZANA VERDE", "70/80", "Premium", 19.0, 62.0, 84.0, 4.42, 26.2),
            ("759105", "759105", "MANZANA GALA GRANEL", "Granel", "A granel", 23.0, 45.0, 65.0, 2.83, 30.7),
            ("759201", "759201", "PERA VERDE", "90/100", "Premium", 18.0, 48.0, 65.0, 3.61, 26.1),
            ("759203", "759203", "PERA FORELLE EN BANDEJA", "Selección", "Con detalle", 9.0, 60.0, 75.0, 8.33, 20.0),
            ("759301", "759301", "UVA RED GLOBE", "Extra", "Premium", 8.2, 70.0, 95.0, 11.58, 26.3),
            ("759502", "759502", "CEREZA", "Jumbo", "Premium", 2.5, 30.0, 45.0, 18.00, 33.3),
            ("759503", "759503", "ARANDANOS", "Premium", "Premium", 0.125, 55.0, 70.0, 560.00, 21.4),
            ("759602", "759602", "PITAHAYA ROJA", "Grande", "Con detalle", 1.0, 15.0, 22.0, 22.00, 31.8),
        ]
        cursor.executemany("""
            INSERT INTO matriz_precios (codigo, barra, descripcion, calibre, clasificacion_calidad, empaque_kg, costo_caja, precio_caja, precio_kg, margen_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, catalogo_inicial)
        conn.commit()

    # Cargar Inventario Inicial por Defecto si está vacío
    cursor.execute("SELECT COUNT(*) FROM inventario")
    if cursor.fetchone()[0] == 0:
        inv_inicial = [
            ("LOTE-2026-01", "MANZANA GALA", "80/88", 150.0, 50.0, "2026-10-01"),
            ("LOTE-2026-01", "MANZANA GALA", "100/110", 80.0, 48.0, "2026-10-01"),
            ("LOTE-2026-02", "MANZANA ROJA", "100/110", 200.0, 60.0, "2026-10-05"),
            ("LOTE-2026-03", "MANZANA VERDE", "70/80", 120.0, 62.0, "2026-10-10"),
            ("LOTE-2026-04", "PERA VERDE", "90/100", 90.0, 48.0, "2026-10-12"),
            ("LOTE-2026-05", "UVA RED GLOBE", "Extra", 60.0, 70.0, "2026-10-15"),
        ]
        cursor.executemany("""
            INSERT INTO inventario (lote, producto, calibre, stock_cajas, costo_unitario_caja, fecha_ingreso)
            VALUES (?, ?, ?, ?, ?, ?)
        """, inv_inicial)
        conn.commit()

    # Cargar Clientes Oficiales si está vacío
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        clientes_oficiales = [
            ("BULLKING", "Principal Caracas", "Supermercados", "Tarifa A (Comprador regular)", "Ladimir (Occidente)", "+58 412-1111111", "Compras Bullking", 15, 12000.0, "2026-10-10"),
            ("CENTRAL MADERENSE", "Sucursal Este", "Supermercados", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-2222222", "Juan Pérez", 30, 20000.0, "2026-09-15"),
            ("CENTRAL MADERENSE", "Sucursal Centro", "Supermercados", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-2222223", "María López", 30, 20000.0, "2026-09-20"),
            ("SUPERMERCADO EUROS", "La Candelaria", "Supermercados", "Tarifa B (Comprador medio)", "Wilmer (Oriente)", "+58 412-3333333", "Ana Gómez", 15, 8000.0, "2026-10-18"),
            ("LADIMIR", "Mercado Mayor", "Mayorista", "Tarifa A (Comprador regular)", "Ladimir (Occidente)", "+58 412-4444444", "Carlos Ladimir", 7, 15000.0, "2026-08-01"),
            ("SUPERMERCADOS LUXOR", "Boleíta", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-5555555", "Luis Luxor", 15, 10000.0, "2026-10-01"),
            ("MERCATO", "Chacao", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-3211234", "Gerencia Mercato", 15, 7000.0, "2026-10-05"),
            ("PLAN SUAREZ", "Baruta", "Supermercados", "Tarifa A (Comprador regular)", "Ladimir (Occidente)", "+58 412-6666666", "Mario Suarez", 30, 18000.0, "2026-07-20"),
            ("RIO CARACAS", "Antímano", "Supermercados", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-7777777", "Pedro Río", 15, 12000.0, "2026-10-12"),
            ("RIO MARGARITA", "Porlamar", "Supermercados", "Tarifa A (Comprador regular)", "Wilmer (Oriente)", "+58 412-1234567", "Ana Río", 30, 15000.0, "2026-09-01"),
            ("RIO VIDA", "Caracas Centro", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-7654321", "Carlos Vida", 15, 8000.0, "2026-10-02"),
            ("SIGO", "Margarita / Central", "Supermercados", "Tarifa A (Comprador regular)", "Wilmer (Oriente)", "+58 412-8888888", "Gerencia Sigo", 30, 25000.0, "2026-06-10"),
            ("TIERRA SANTA", "Sabana Grande", "Minimarket", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-9999999", "Ahmed T.S.", 15, 5000.0, "2026-10-15"),
            ("SUPER 900", "Catia", "Supermercados", "Tarifa B (Comprador medio)", "Ladimir (Occidente)", "+58 412-9876543", "Luis 900", 15, 6000.0, "2026-09-25"),
            ("TODO HOGAR", "Petare", "Comercial", "Tarifa C (Comprador esporádico)", "Tufic (Capital)", "+58 412-5432167", "María Hogar", 15, 4000.0, "2026-08-20"),
            ("VIVA", "El Recreo", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-4567890", "Supervisor Viva", 15, 7000.0, "2026-09-30"),
            ("WILMER", "El Valle", "Mayorista", "Tarifa A (Comprador regular)", "Wilmer (Oriente)", "+58 412-1357924", "Wilmer Distribución", 7, 10000.0, "2026-10-14"),
            ("PARAMO COLD 2024", "Altamira", "HORECA", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-2468135", "Equipo Paramo", 15, 8000.0, "2026-10-16"),
        ]
        cursor.executemany("""
            INSERT INTO clientes (matriz, sucursal, segmento, tarifa, dupla, telefono, contacto, limite_credito_dias, limite_credito_dolares, ultimo_pedido)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, clientes_oficiales)
        conn.commit()

    conn.close()

init_db()

EMPRESA = {
    "nombre": "FRUMIX C.A.",
    "rif": "J-40985632-1",
    "direccion": "Centro de Distribución Principal, Caracas, Venezuela",
    "telefono": "+58 412-FRUMIX1",
}

# ---------------------------------------------------------
# CONSULTAS OPTIMIZADAS CON CACHÉ (@st.cache_data)
# ---------------------------------------------------------
@st.cache_data
def get_catalogo_cache():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM matriz_precios", conn)
    conn.close()
    return df

@st.cache_data
def get_clientes_cache():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()
    return df

@st.cache_data
def get_inventario_cache():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM inventario", conn)
    conn.close()
    return df

# ---------------------------------------------------------
# SISTEMA DE AUTENTICACIÓN Y ROLES (LOGIN)
# ---------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.rol = ""

if not st.session_state.autenticado:
    st.title("🍓 Frumix C.A. - Control de Acceso ERP B2B")
    st.write("Ingrese sus credenciales corporativas para acceder al sistema.")
    
    with st.form("form_login"):
        user_input = st.text_input("Usuario (ej. gerencia, ventas, logistica, cobranza)")
        pass_input = st.text_input("Contraseña", type="password")
        btn_login = st.form_submit_button("Iniciar Sesión")
        
        if btn_login:
            credenciales = {
                "gerencia": ("frumix2026*", "Gerencia General"),
                "ventas": ("ventas123", "Equipo Comercial"),
                "logistica": ("logistica123", "Logística y Despachos"),
                "cobranza": ("cobranza123", "Departamento de Cobranza")
            }
            if user_input in credenciales and credenciales[user_input][0] == pass_input:
                st.session_state.autenticado = True
                st.session_state.usuario = user_input
                st.session_state.rol = credenciales[user_input][1]
                st.success(f"¡Bienvenido, {st.session_state.rol}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ---------------------------------------------------------
# MENÚ LATERAL ERP COMPLETO (17 MÓDULOS)
# ---------------------------------------------------------
st.sidebar.markdown(f"### 🍓 {EMPRESA['nombre']}")
st.sidebar.markdown(f"**Usuario:** {st.session_state.rol}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
st.sidebar.markdown("---")

modulos_disponibles = [
    "1. 📊 Dashboard Gerencial & P&L",
    "2. 📦 Inventario por Fruta y Calibre",
    "3. 🛒 Ventas & Pedidos por Calibre",
    "4. 📄 Ventas & Cotizador Pro (Con Logo/HTML)",
    "5. 📋 Registro Manual Detallado de Pedidos",
    "6. 🍓 Lista y Gestión de Productos",
    "7. 🔄 Kardex Diario (Entradas & Salidas)",
    "8. 🏢 Gestión y Edición de Clientes",
    "9. 🛍️ Historial de Compras de Clientes",
    "10. 📈 Métricas de Pedidos (Diarios/Semanales)",
    "11. 🎯 Embudo de Ventas (Sales Funnel)",
    "12. 💰 Departamento de Cobranza & CxC",
    "13. 🚚 Logística, Despacho & Rutas",
    "14. 💲 Matriz Dinámica de Precios (Caja a KG)",
    "15. 🗑️ Control de Mermas & Pérdidas",
    "16. ↩️ Registro de Devoluciones y Mermas",
    "17. 📋 Historial Completo de Pedidos",
]

menu = st.sidebar.radio("Módulos ERP Enterprise Elite:", modulos_disponibles)

# ---------------------------------------------------------
# 1. DASHBOARD GERENCIAL & P&L
# ---------------------------------------------------------
if "1." in menu:
    st.title("📊 Dashboard Gerencial y Estado de Resultados (P&L)")
    st.write("Centro analítico de alto rendimiento con gráficos ejecutivos para la toma de decisiones.")

    conn = sqlite3.connect(DB_NAME)
    df_ped = pd.read_sql("SELECT * FROM pedidos", conn)
    df_inv = pd.read_sql("SELECT * FROM inventario", conn)
    df_mer = pd.read_sql("SELECT * FROM mermas", conn)
    df_cxc = pd.read_sql("SELECT * FROM cobranza", conn)
    conn.close()

    total_ventas = df_ped["monto_total"].sum() if not df_ped.empty else 0.0
    total_costos_v = df_ped["costo_total"].sum() if not df_ped.empty else 0.0
    ganancia_neta_pedidos = df_ped["ganancia_estimada"].sum() if not df_ped.empty else 0.0
    
    val_inv = (df_inv["stock_cajas"] * df_inv["costo_unitario_caja"]).sum() if not df_inv.empty else 0.0
    val_merma = df_mer["perdida_monetaria"].sum() if not df_mer.empty else 0.0
    deuda_pendiente = (df_cxc[df_cxc["estatus_pago"] != "Pagado"]["monto_factura"] - df_cxc[df_cxc["estatus_pago"] != "Pagado"]["monto_pagado"]).sum() if not df_cxc.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Ventas Totales Facturadas", f"${total_ventas:,.2f}")
    with c2:
        st.metric("Utilidad Bruta Operativa", f"${ganancia_neta_pedidos:,.2f}", delta=f"{(ganancia_neta_pedidos/total_ventas*100) if total_ventas>0 else 0:.1f}% Margen")
    with c3:
        st.metric("Valor Inventario en Frío", f"${val_inv:,.2f}")
    with c4:
        st.metric("Cuentas por Cobrar Activas", f"${deuda_pendiente:,.2f}")

    st.markdown("---")
    st.subheader("📈 Gráficos de Comportamiento Financiero y Ventas")
    if not df_ped.empty:
        df_chart = df_ped.groupby("fecha_pedido")["monto_total"].sum().reset_index()
        st.bar_chart(df_chart.set_index("fecha_pedido"))
    else:
        st.info("Aún no hay suficientes registros de pedidos para graficar tendencias.")

    st.markdown("---")
    st.subheader("📈 Estado de Resultados Financiero Consolidado (P&L)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(f"""
        * **(+) Ventas Totales Brutas:** ${total_ventas:,.2f}
        * **(-) Costo de Mercancía Vendida (COGS):** ${total_costos_v:,.2f}
        * **(=) Utilidad Bruta Comercial:** **${ganancia_neta_pedidos:,.2f}**
        """)
    with col_p2:
        st.markdown(f"""
        * **(-) Pérdidas Registradas por Mermas:** ${val_merma:,.2f}
        * **(+) Total CxC Pendiente de Cobro:** ${deuda_pendiente:,.2f}
        * **(=) Utilidad Neta Proyectada:** **${ganancia_neta_pedidos - val_merma:,.2f}**
        """)

# ---------------------------------------------------------
# 2. INVENTARIO POR FRUTA Y CALIBRE
# ---------------------------------------------------------
elif "2." in menu:
    st.title("📦 Control de Inventario por Frutas y Calibres en Existencia")
    st.write("Agrega los calibres que vayan ingresando para cada fruta. Las existencias se actualizarán al vender.")

    tab_inv1, tab_inv2 = st.tabs(["📋 Existencias Actuales por Calibre", "➕ Añadir Lote / Fruta / Calibre"])

    with tab_inv1:
        df_inv = get_inventario_cache()
        if not df_inv.empty:
            st.subheader("📊 Resumen de Existencias por Fruta y Calibre")
            st.dataframe(df_inv[["id", "lote", "producto", "calibre", "stock_cajas", "costo_unitario_caja", "fecha_ingreso"]], use_container_width=True)

            st.markdown("---")
            st.subheader("🗑️ Eliminar o Ajustar Lote de Inventario")
            id_inv_del = st.selectbox("Seleccione ID de registro a eliminar:", df_inv["id"].tolist())
            if st.button("🗑️ Eliminar Registro de Inventario"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inventario WHERE id = ?", (int(id_inv_del),))
                conn.commit()
                conn.close()
                st.success("¡Registro de inventario eliminado!")
                st.rerun()
        else:
            st.info("No hay inventario registrado en cámaras.")

    with tab_inv2:
        df_cat = get_catalogo_cache()
        lista_frutas_cat = df_cat["descripcion"].unique().tolist() if not df_cat.empty else ["MANZANA GALA", "MANZANA ROJA", "PERA VERDE"]

        with st.form("form_ingreso_fruta_calibre"):
            st.subheader("Registrar Ingreso de Fruta y Calibre Especifico")
            col1, col2 = st.columns(2)
            with col1:
                fruta_sel = st.selectbox("Seleccione Fruta del Catálogo", lista_frutas_cat)
                lote_num = st.text_input("Número de Lote", value=f"LOTE-{datetime.now().strftime('%Y%m%d')}")
                calibre_ingresado = st.text_input("Escriba / Indique el Calibre (Ej. 80/88, 100/110, Jumbo, Extra, Granel)")
            with col2:
                cajas_ingreso = st.number_input("Cantidad de Cajas que Ingresan", min_value=1.0, value=100.0)
                costo_caja = st.number_input("Costo Unitario por Caja ($)", min_value=0.0, value=50.0)
                fecha_ing = st.date_input("Fecha de Ingreso", value=date.today())

            if st.form_submit_button("💾 Añadir al Inventario"):
                if fruta_sel and calibre_ingresado.strip():
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    
                    calibre_clean = calibre_ingresado.strip().upper()
                    
                    cursor.execute("""
                        SELECT id, stock_cajas FROM inventario 
                        WHERE producto = ? AND calibre = ? AND lote = ?
                    """, (fruta_sel, calibre_clean, lote_num.upper()))
                    row_exist = cursor.fetchone()

                    if row_exist:
                        inv_id, stock_act = row_exist
                        nuevo_stk = stock_act + cajas_ingreso
                        cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stk, inv_id))
                    else:
                        cursor.execute("""
                            INSERT INTO inventario (lote, producto, calibre, stock_cajas, costo_unitario_caja, fecha_ingreso)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (lote_num.upper(), fruta_sel, calibre_clean, cajas_ingreso, costo_caja, str(fecha_ing)))

                    cursor.execute("""
                        INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                        VALUES (?, ?, ?, 'ENTRADA', ?, 'Ingreso inicial / Carga a cámaras', ?, ?)
                    """, (lote_num.upper(), fruta_sel, calibre_clean, cajas_ingreso, str(fecha_ing), st.session_state.rol))

                    conn.commit()
                    conn.close()
                    st.success(f"¡Se agregaron {cajas_ingreso} cajas de {fruta_sel} (Calibre {calibre_clean}) al inventario!")
                    st.rerun()
                else:
                    st.error("Por favor seleccione la fruta e indique el calibre.")

# ---------------------------------------------------------
# 3. VENTAS & PEDIDOS POR CALIBRE
# ---------------------------------------------------------
elif "3." in menu:
    st.title("🛒 Generador de Pedidos y Ventas por Calibre")
    st.write("Selecciona la fruta y el calibre en existencia. El stock se restará automáticamente del inventario al procesar.")

    df_cli_db = get_clientes_cache()
    df_inv_db = get_inventario_cache()

    lista_matrices = df_cli_db["matriz"].unique().tolist() if not df_cli_db.empty else ["BULLKING"]

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        cli_sel = st.selectbox("Empresa Matriz Cliente", lista_matrices)
        sucursales_disponibles = df_cli_db[df_cli_db["matriz"] == cli_sel]["sucursal"].tolist() if not df_cli_db.empty else ["Principal"]
        suc_sel = st.selectbox("Sucursal Específica", sucursales_disponibles)
    with col_v2:
        cli_row_sel = df_cli_db[(df_cli_db["matriz"] == cli_sel) & (df_cli_db["sucursal"] == suc_sel)]
        asesor_asignado = cli_row_sel.iloc[0]["dupla"] if not cli_row_sel.empty else "Tufic (Capital)"
        st.info(f"👤 **Asesor / Dupla Asignada:** {asesor_asignado}")

    st.markdown("---")
    st.subheader("📦 Selección de Frutas y Calibres para el Pedido")

    df_inv_disponible = df_inv_db[df_inv_db["stock_cajas"] > 0] if not df_inv_db.empty else pd.DataFrame()

    if not df_inv_disponible.empty:
        frutas_disponibles = df_inv_disponible["producto"].unique().tolist()
        
        if "carrito_pedido" not in st.session_state:
            st.session_state.carrito_pedido = []

        with st.form("form_agregar_item_pedido"):
            c_p1, c_p2, c_p3, c_p4 = st.columns(4)
            with c_p1:
                fruta_ped = st.selectbox("1. Seleccionar Fruta", frutas_disponibles)
            
            calibres_disponibles = df_inv_disponible[df_inv_disponible["producto"] == fruta_ped]["calibre"].unique().tolist()
            
            with c_p2:
                calibre_ped = st.selectbox("2. Seleccionar Calibre Disponible", calibres_disponibles)
                
            row_inv_item = df_inv_disponible[(df_inv_disponible["producto"] == fruta_ped) & (df_inv_disponible["calibre"] == calibre_ped)].iloc[0]
            stock_disponible = row_inv_item["stock_cajas"]
            costo_item = row_inv_item["costo_unitario_caja"]

            with c_p3:
                st.caption(f"Stock disponible: **{stock_disponible} cajas**")
                cajas_ped = st.number_input("3. Cantidad de Cajas", min_value=1.0, max_value=float(stock_disponible), value=10.0)
            with c_p4:
                precio_caja_ped = st.number_input("4. Precio por Caja ($)", min_value=0.0, value=float(costo_item * 1.3))

            if st.form_submit_button("➕ Agregar Producto al Pedido"):
                subtotal = cajas_ped * precio_caja_ped
                st.session_state.carrito_pedido.append({
                    "inventario_id": int(row_inv_item["id"]),
                    "lote": row_inv_item["lote"],
                    "producto": fruta_ped,
                    "calibre": calibre_ped,
                    "cajas": cajas_ped,
                    "costo_unitario": costo_item,
                    "precio_caja": precio_caja_ped,
                    "subtotal": subtotal
                })
                st.success(f"¡Agregado: {cajas_ped} cajas de {fruta_ped} ({calibre_ped})!")
                st.rerun()

        if st.session_state.carrito_pedido:
            st.markdown("### 🛒 Detalle del Pedido Actual")
            df_cart = pd.DataFrame(st.session_state.carrito_pedido)
            st.dataframe(df_cart[["producto", "calibre", "lote", "cajas", "precio_caja", "subtotal"]], use_container_width=True)

            col_bot1, col_bot2 = st.columns(2)
            with col_bot1:
                monto_total_ped = df_cart["subtotal"].sum()
                st.markdown(f"### **Total del Pedido:** `${monto_total_ped:,.2f} USD`")
            with col_bot2:
                if st.button("🗑️ Vaciar Carrito"):
                    st.session_state.carrito_pedido = []
                    st.rerun()

            if st.button("💾 CONFIRMAR PEDIDO Y RESTAR DEL INVENTARIO"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("BEGIN TRANSACTION;")

                    nro_p = f"PED-{datetime.now().strftime('%Y%m%d%H%M')}"
                    costo_total_ped = sum(item["cajas"] * item["costo_unitario"] for item in st.session_state.carrito_pedido)
                    ganancia_ped = monto_total_ped - costo_total_ped

                    cursor.execute("""
                        INSERT INTO pedidos (nro_pedido, cliente, sucursal, realizado_por, atendido_por, recibido_por, datos_importantes, fecha_pedido, monto_total, costo_total, ganancia_estimada, estatus_despacho, detalle_json)
                        VALUES (?, ?, ?, 'Sistema Ventas', ?, 'Cliente Final', 'Venta directa por calibre', ?, ?, ?, ?, 'Pendiente', ?)
                    """, (nro_p, cli_sel, suc_sel, asesor_asignado, str(date.today()), monto_total_ped, costo_total_ped, ganancia_ped, json.dumps(st.session_state.carrito_pedido)))

                    cursor.execute("""
                        INSERT INTO cobranza (nro_factura, cliente, fecha_emision, fecha_vencimiento, monto_factura, monto_pagado, estatus_pago)
                        VALUES (?, ?, ?, ?, ?, 0.0, 'Pendiente')
                    """, (f"FAC-{nro_p}", cli_sel, str(date.today()), str(date.today() + pd.Timedelta(days=15)), monto_total_ped))

                    for item in st.session_state.carrito_pedido:
                        cursor.execute("SELECT stock_cajas FROM inventario WHERE id = ?", (item["inventario_id"],))
                        stk_act = cursor.fetchone()[0]
                        nuevo_stk = max(0.0, stk_act - item["cajas"])
                        
                        cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stk, item["inventario_id"]))

                        cursor.execute("""
                            INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                            VALUES (?, ?, ?, 'SALIDA', ?, ?, ?, ?)
                        """, (item["lote"], item["producto"], item["calibre"], item["cajas"], f"Despacho Pedido {nro_p}", str(date.today()), st.session_state.rol))

                    conn.commit()
                    conn.close()

                    st.session_state.carrito_pedido = []
                    st.success(f"¡Pedido {nro_p} procesado con éxito! Las existencias del calibre fueron restadas del inventario.")
                    st.rerun()

                except Exception as e:
                    if 'conn' in locals():
                        conn.rollback()
                        conn.close()
                    st.error(f"Error procesando la transacción: {e}")
    else:
        st.warning("No hay productos con existencias en cámaras de frío. Ingrese lotes en el módulo de Inventario.")

# ---------------------------------------------------------
# 4. VENTAS & COTIZADOR PRO (CON LOGO Y DESCARGA HTML)
# ---------------------------------------------------------
elif "4." in menu:
    st.title("📄 Cotizador B2B Profesional con Formato Imprimible")
    st.write("Genera listas de precios oficiales y exporta el documento HTML institucional con logo para clientes.")

    df_mat = get_catalogo_cache()
    df_cli_db = get_clientes_cache()
    lista_matrices = df_cli_db["matriz"].unique().tolist() if not df_cli_db.empty else ["BULLKING"]

    c_v1, c_v2 = st.columns(2)
    with c_v1:
        cli_sel = st.selectbox("Empresa Matriz", lista_matrices)
        sucursales_disponibles = df_cli_db[df_cli_db["matriz"] == cli_sel]["sucursal"].tolist() if not df_cli_db.empty else ["Principal"]
        suc_sel = st.selectbox("Sucursal Específica", sucursales_disponibles)
    with c_v2:
        cli_row_sel = df_cli_db[(df_cli_db["matriz"] == cli_sel) & (df_cli_db["sucursal"] == suc_sel)]
        asesor_asignado = cli_row_sel.iloc[0]["dupla"] if not cli_row_sel.empty else "Tufic (Capital)"
        st.info(f"👤 **Asesor / Dupla Asignada:** {asesor_asignado}")
        vig_sel = st.date_input("Validez de precios:", value=date.today() + pd.Timedelta(days=7))

    st.markdown("---")
    st.subheader("📋 Cuadro de Precios (Edita la columna 'PRECIO CAJA ($)'):")

    if not df_mat.empty:
        df_editor_v = df_mat[["codigo", "barra", "descripcion", "calibre", "clasificacion_calidad", "empaque_kg", "costo_caja", "precio_caja"]].copy()
        df_editor_v.columns = ["CÓDIGO", "BARRA", "DESCRIPCIÓN", "CALIBRE", "CALIDAD", "EMPAQUE/KG", "COSTO CAJA ($)", "PRECIO CAJA ($)"]

        df_editado_venta = st.data_editor(df_editor_v, use_container_width=True, key="cotizador_tabla_maestra")

        df_editado_venta["PRECIO POR KG ($)"] = df_editado_venta.apply(
            lambda r: round(r["PRECIO CAJA ($)"] / r["EMPAQUE/KG"], 2) if r["EMPAQUE/KG"] > 0 else 0.0, axis=1
        )

        st.markdown("---")
        st.subheader("📄 Generar Formato Imprimible")
        if st.button("📥 Generar Documento HTML de Cotización"):
            logo_url = "https://raw.githubusercontent.com/vcaro2824-del/FrumixCRM/main/IMG-20261016-WA0072~3.jpg"
            
            html_doc = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <title>Cotización Oficial - Frumix C.A.</title>
                <style>
                    body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 30px; color: #111; text-align: left; }}
                    .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6B8E23; padding-bottom: 15px; align-items: center; text-align: left; }}
                    .logo {{ max-height: 80px; width: auto; }}
                    .intro-text {{ margin-top: 20px; font-family: Arial, sans-serif; font-size: 12px; line-height: 1.6; color: #333; text-align: left; }}
                    h3 {{ font-family: Arial, sans-serif; font-size: 14px; text-align: left; margin-top: 25px; }}
                    table {{ width: 100%; min-width: 650px; border-collapse: collapse; margin-top: 20px; text-align: left; }}
                    th, td {{ border: 1px solid #bbb; padding: 12px 15px; text-align: left; font-family: Arial, sans-serif; font-size: 12px; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    p {{ font-family: Arial, sans-serif; font-size: 12px; text-align: left; }}
                    .signature-container {{ margin-top: 35px; width: 100%; text-align: center; }}
                    .signature {{ font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; color: #111; display: inline-block; text-align: center; line-height: 1.5; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div>
                        <img src="{logo_url}" class="logo" alt="Logo Frumix C.A.">
                        <div style="font-size: 11px; color: #555; margin-top: 5px;">RIF: J-40985632-1 | Caracas, Venezuela</div>
                    </div>
                    <div style="text-align: right; font-size: 12px;">
                        <strong>Fecha:</strong> {date.today()}<br>
                        <strong>Cliente:</strong> {cli_sel} - {suc_sel}<br>
                        <strong>Asesor:</strong> {asesor_asignado}
                    </div>
                </div>
                
                <div class="intro-text">
                    A continuación encontrará nuestra lista de precios.<br>
                    Nuestra alianza con los mejores productos de frutas frescas a nivel mundial y el correcto manejo del producto garantiza la calidad y buen servicio que nos caracteriza.
                </div>

                <h3>Cotización Comercial Oficial</h3>
                <table>
                    <tr>
                        <th>Código</th>
                        <th>Descripción</th>
                        <th>Calibre</th>
                        <th>Calidad</th>
                        <th>Empaque (Kg)</th>
                        <th>Precio Caja ($)</th>
                        <th>Precio por KG ($)</th>
                    </tr>
            """
            for _, r in df_editado_venta.iterrows():
                html_doc += f"<tr><td>{r['CÓDIGO']}</td><td>{r['DESCRIPCIÓN']}</td><td>{r['CALIBRE']}</td><td>{r['CALIDAD']}</td><td>{r['EMPAQUE/KG']}</td><td>${r['PRECIO CAJA ($)']:.2f}</td><td>${r['PRECIO POR KG ($)']:.2f}</td></tr>"
            html_doc += f"""
                </table>
                <br>
                <p><strong>Condiciones Comerciales:</strong> Sujeto a disponibilidad en cámaras de frío. Validez de precios hasta {vig_sel}.</p>
                
                <div class="signature-container">
                    <div class="signature">
                        Atentamente;<br>
                        Gcia. De Ventas<br>
                        FRUMIX C.A.
                    </div>
                </div>
            </body>
            </html>
            """
            st.download_button(
                label="💾 Descargar Cotización en HTML para Imprimir / WhatsApp",
                data=html_doc,
                file_name=f"Cotizacion_{cli_sel.replace(' ', '_')}_{suc_sel.replace(' ', '_')}.html",
                mime="text/html"
            )

# ---------------------------------------------------------
# 5. REGISTRO MANUAL DETALLADO DE PEDIDOS
# ---------------------------------------------------------
elif "5." in menu:
    st.title("📋 Registro Manual de Pedidos y Trazabilidad")
    st.write("Ingresa de forma manual los datos completos de un pedido con asignación de dupla y monto.")

    df_cli_m = get_clientes_cache()
    lista_mat_ped = df_cli_m["matriz"].tolist() if not df_cli_m.empty else ["BULLKING"]

    with st.form("form_registro_pedido_manual"):
        st.subheader("📝 Datos Generales del Pedido")
        c_pm1, c_pm2 = st.columns(2)
        with c_pm1:
            nro_ped_m = st.text_input("Nro. de Pedido (Ej. PED-2026-001)", value="PED-2026-")
            cliente_m = st.selectbox("Cliente Matriz", lista_mat_ped)
            realizado_por_m = st.text_input("¿Quién realizó el pedido? (Ej. Comprador / Encargado)")
        with c_pm2:
            atendido_por_m = st.selectbox("¿Quién despachó / Asesor?", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
            recibido_por_m = st.text_input("¿Quién recibió en destino?")
            monto_m = st.number_input("Monto Total del Pedido ($)", min_value=0.1, value=1000.0)

        st.markdown("---")
        st.subheader("📌 Datos Importantes y Observaciones")
        datos_imp_m = st.text_area("Notas importantes (Horario de entrega, transporte, etc.):")
        fecha_ped_m = st.date_input("Fecha del Pedido", value=date.today())

        if st.form_submit_button("💾 Guardar Pedido Manualmente"):
            if nro_ped_m and realizado_por_m and monto_m > 0:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("BEGIN TRANSACTION;")
                    
                    cursor.execute("""
                        INSERT INTO pedidos (nro_pedido, cliente, sucursal, realizado_por, atendido_por, recibido_por, datos_importantes, fecha_pedido, monto_total, costo_total, ganancia_estimada, estatus_despacho, detalle_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?)
                    """, (nro_ped_m.upper(), cliente_m, "Sucursal Principal", realizado_por_m, atendido_por_m, recibido_por_m, datos_imp_m, str(fecha_ped_m), monto_m, monto_m * 0.7, monto_m * 0.3, json.dumps([])))
                    
                    cursor.execute("""
                        INSERT INTO cobranza (nro_factura, cliente, fecha_emision, fecha_vencimiento, monto_factura, monto_pagado, estatus_pago)
                        VALUES (?, ?, ?, ?, ?, 0.0, 'Pendiente')
                    """, (f"FAC-{nro_ped_m.upper()}", cliente_m, str(fecha_ped_m), str(fecha_ped_m + pd.Timedelta(days=15)), monto_m))

                    conn.commit()
                    conn.close()
                    st.success(f"¡Pedido manual {nro_ped_m} registrado!")
                    st.rerun()
                except Exception as e:
                    if 'conn' in locals():
                        conn.rollback()
                        conn.close()
                    st.error(f"Error al procesar el pedido: {e}")
            else:
                st.error("Por favor complete los campos obligatorios.")

# ---------------------------------------------------------
# 6. LISTA Y GESTIÓN DE PRODUCTOS
# ---------------------------------------------------------
elif "6." in menu:
    st.title("🍓 Catálogo Oficial de Productos y Clasificación de Calidad")
    st.write("Administra el catálogo de frutas con sus calidades: **Premium**, **Con detalle** o **A granel**.")

    tab_prod1, tab_prod2 = st.tabs(["📋 Catálogo Actual y Edición", "➕ Registrar Nuevo Producto"])

    with tab_prod1:
        df_cat = get_catalogo_cache()
        if not df_cat.empty:
            st.subheader("Edición General del Catálogo")
            df_edit_cat = st.data_editor(
                df_cat[["id", "codigo", "descripcion", "calibre", "clasificacion_calidad", "empaque_kg", "costo_caja", "precio_caja"]],
                use_container_width=True,
                key="editor_cat_gral"
            )
            
            if st.button("💾 Guardar Cambios en el Catálogo"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for _, r in df_edit_cat.iterrows():
                    p_kg = round(r["precio_caja"] / r["empaque_kg"], 2) if r["empaque_kg"] > 0 else 0.0
                    mrg = round(((r["precio_caja"] - r["costo_caja"]) / r["precio_caja"] * 100), 1) if r["precio_caja"] > 0 else 0.0
                    cursor.execute("""
                        UPDATE matriz_precios 
                        SET codigo = ?, descripcion = ?, calibre = ?, clasificacion_calidad = ?, empaque_kg = ?, costo_caja = ?, precio_caja = ?, precio_kg = ?, margen_pct = ?
                        WHERE id = ?
                    """, (r["codigo"], r["descripcion"].upper(), r["calibre"], r["clasificacion_calidad"], r["empaque_kg"], r["costo_caja"], r["precio_caja"], p_kg, mrg, int(r["id"])))
                conn.commit()
                conn.close()
                st.success("¡Catálogo de productos actualizado con éxito!")
                st.rerun()
        else:
            st.info("No hay productos en el catálogo.")

    with tab_prod2:
        with st.form("form_nuevo_producto"):
            st.subheader("Agregar Nuevo Fruto / Producto al Sistema")
            cp1, cp2 = st.columns(2)
            with cp1:
                n_cod = st.text_input("Código del Producto (Ej. 759106)")
                n_desc = st.text_input("Descripción (Ej. MANZANA RED DELICIOUS)")
                n_calibre = st.text_input("Calibre Base (Ej. 80/88 o Extra)")
                n_calidad = st.selectbox("Clasificación de Calidad", ["Premium", "Con detalle", "A granel"])
            with cp2:
                n_emp = st.number_input("Empaque en Kilogramos por Caja", min_value=0.01, value=19.0)
                n_costo = st.number_input("Costo Unitario por Caja ($)", min_value=0.0, value=50.0)
                n_precio = st.number_input("Precio de Venta por Caja ($)", min_value=0.0, value=70.0)

            if st.form_submit_button("Guardar Nuevo Producto"):
                if n_cod and n_desc:
                    p_kg_n = round(n_precio / n_emp, 2) if n_emp > 0 else 0.0
                    mrg_n = round(((n_precio - n_costo) / n_precio * 100), 1) if n_precio > 0 else 0.0
                    
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO matriz_precios (codigo, barra, descripcion, calibre, clasificacion_calidad, empaque_kg, costo_caja, precio_caja, precio_kg, margen_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (n_cod, n_cod, n_desc.upper(), n_calibre, n_calidad, n_emp, n_costo, n_precio, p_kg_n, mrg_n))
                    conn.commit()
                    conn.close()
                    st.success("¡Nuevo producto agregado al catálogo con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor complete al menos el código y la descripción.")

# ---------------------------------------------------------
# 7. KARDEX DIARIO (ENTRADAS & SALIDAS)
# ---------------------------------------------------------
elif "7." in menu:
    st.title("🔄 Kardex Diario - Control de Entradas y Salidas de Inventario")
    st.write("Auditoría de todos los movimientos de mercancía por fruta, calibre y lote.")

    conn = sqlite3.connect(DB_NAME)
    df_kardex = pd.read_sql("SELECT * FROM movimientos_inventario", conn)
    conn.close()

    if not df_kardex.empty:
        st.dataframe(df_kardex, use_container_width=True)
    else:
        st.info("No hay movimientos registrados en el kardex.")

# ---------------------------------------------------------
# 8. GESTIÓN Y EDICIÓN DE CLIENTES
# ---------------------------------------------------------
elif "8." in menu:
    st.title("🏢 Directorio, Edición y Gestión de Clientes (Matrices y Sucursales)")
    df_clientes = get_clientes_cache()
    if not df_clientes.empty:
        st.dataframe(df_clientes, use_container_width=True)
    else:
        st.info("No hay clientes registrados.")

# ---------------------------------------------------------
# 9. HISTORIAL DE COMPRAS DE CLIENTES
# ---------------------------------------------------------
elif "9." in menu:
    st.title("🛍️ Historial de Compras y Trazabilidad por Cliente")
    df_cli_h = get_clientes_cache()
    lista_mat_hist = df_cli_h["matriz"].unique().tolist() if not df_cli_h.empty else ["BULLKING"]

    cliente_sel_hist = st.selectbox("Seleccione Empresa Matriz:", lista_mat_hist)

    conn = sqlite3.connect(DB_NAME)
    df_ped_hist = pd.read_sql("SELECT * FROM pedidos WHERE cliente = ?", conn, params=(cliente_sel_hist,))
    conn.close()

    if not df_ped_hist.empty:
        st.dataframe(df_ped_hist[["nro_pedido", "sucursal", "fecha_pedido", "monto_total", "atendido_por", "estatus_despacho"]], use_container_width=True)
    else:
        st.info(f"El cliente {cliente_sel_hist} no registra compras previas.")

# ---------------------------------------------------------
# 10. MÉTRICAS DE PEDIDOS
# ---------------------------------------------------------
elif "10." in menu:
    st.title("📈 Métricas y Registro de Pedidos")
    conn = sqlite3.connect(DB_NAME)
    df_p = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True)
    else:
        st.info("No hay pedidos registrados.")

# ---------------------------------------------------------
# 11. EMBUDO DE VENTAS
# ---------------------------------------------------------
elif "11." in menu:
    st.title("🎯 Embudo de Ventas y Seguimiento Comercial B2B")
    conn = sqlite3.connect(DB_NAME)
    df_funnel = pd.read_sql("SELECT * FROM embudo_ventas", conn)
    conn.close()

    if not df_funnel.empty:
        st.dataframe(df_funnel, use_container_width=True)
    else:
        st.info("No hay oportunidades en el embudo.")

# ---------------------------------------------------------
# 12. DEPARTAMENTO DE COBRANZA & CxC
# ---------------------------------------------------------
elif "12." in menu:
    st.title("💰 Departamento de Cobranza - Cuentas por Cobrar")
    conn = sqlite3.connect(DB_NAME)
    df_cxc = pd.read_sql("SELECT * FROM cobranza", conn)
    conn.close()

    if not df_cxc.empty:
        st.dataframe(df_cxc, use_container_width=True)
    else:
        st.info("No hay cuentas por cobrar registradas.")

# ---------------------------------------------------------
# 13. LOGÍSTICA, DESPACHO & RUTAS
# ---------------------------------------------------------
elif "13." in menu:
    st.title("🚚 Logística y Estatus de Despachos")
    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_peds.empty:
        st.dataframe(df_peds, use_container_width=True)
    else:
        st.info("No hay pedidos para despachar.")

# ---------------------------------------------------------
# 14. MATRIZ DINÁMICA DE PRECIOS
# ---------------------------------------------------------
elif "14." in menu:
    st.title("💲 Matriz de Precios - Conversión Caja a Kilogramo")
    df_m = get_catalogo_cache()

    if not df_m.empty:
        st.dataframe(df_m, use_container_width=True)

# ---------------------------------------------------------
# 15. CONTROL DE MERMAS & PÉRDIDAS
# ---------------------------------------------------------
elif "15." in menu:
    st.title("🗑️ Control de Mermas y Pérdidas Financieras")
    conn = sqlite3.connect(DB_NAME)
    df_mermas_hist = pd.read_sql("SELECT * FROM mermas", conn)
    conn.close()

    if not df_mermas_hist.empty:
        st.dataframe(df_mermas_hist, use_container_width=True)
    else:
        st.info("No hay mermas registradas.")

# ---------------------------------------------------------
# 16. REGISTRO DE DEVOLUCIONES Y MERMAS
# ---------------------------------------------------------
elif "16." in menu:
    st.title("↩️ Módulo de Devoluciones de Clientes Vinculadas a Mermas")
    conn = sqlite3.connect(DB_NAME)
    df_dev_hist = pd.read_sql("SELECT * FROM devoluciones", conn)
    conn.close()

    if not df_dev_hist.empty:
        st.dataframe(df_dev_hist, use_container_width=True)
    else:
        st.info("No hay devoluciones registradas.")

# ---------------------------------------------------------
# 17. HISTORIAL COMPLETO DE PEDIDOS
# ---------------------------------------------------------
elif "17." in menu:
    st.title("📋 Historial y Fidelidad Histórica de Pedidos B2B")
    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_peds.empty:
        st.dataframe(df_peds, use_container_width=True)
    else:
        st.info("No hay pedidos registrados todavía.")
