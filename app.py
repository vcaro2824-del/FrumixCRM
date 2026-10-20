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
# BASE DE DATOS RELACIONAL INTEGRAL (SQLITE) - V23 ESTABLE
# ---------------------------------------------------------
DB_NAME = "frumix_enterprise_elite_v23.db"

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
    
    # 2. Catálogo Base (Control manual absoluto por Deiglis)
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

    # Cargar Clientes Oficiales Base si está vacío
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        clientes_oficiales = [
            ("BULLKING", "Principal Caracas", "Supermercados", "Tarifa A (Comprador regular)", "Ladimir (Occidente)", "+58 412-1111111", "Compras Bullking", 15, 12000.0, "2026-09-10"),
            ("CENTRAL MADERENSE", "Sucursal Este", "Supermercados", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-2222222", "Juan Pérez", 30, 20000.0, "2026-08-15"),
            ("CENTRAL MADERENSE", "Sucursal Centro", "Supermercados", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-2222223", "María López", 30, 20000.0, "2026-08-20"),
            ("SUPERMERCADO EUROS", "La Candelaria", "Supermercados", "Tarifa B (Comprador medio)", "Wilmer (Oriente)", "+58 412-3333333", "Ana Gómez", 15, 8000.0, "2026-09-18"),
            ("LADIMIR", "Mercado Mayor", "Mayorista", "Tarifa A (Comprador regular)", "Ladimir (Occidente)", "+58 412-4444444", "Carlos Ladimir", 7, 15000.0, "2026-07-01"),
            ("SUPERMERCADOS LUXOR", "Boleíta", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-5555555", "Luis Luxor", 15, 10000.0, "2026-09-01"),
            ("MERCATO", "Chacao", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-3211234", "Gerencia Mercato", 15, 7000.0, "2026-09-05"),
            ("PLAN SUAREZ", "Baruta", "Supermercados", "Tarifa A (Comprador regular)", "Ladimir (Occidente)", "+58 412-6666666", "Mario Suarez", 30, 18000.0, "2026-06-20"),
            ("RIO CARACAS", "Antímano", "Supermercados", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-7777777", "Pedro Río", 15, 12000.0, "2026-09-12"),
            ("RIO MARGARITA", "Porlamar", "Supermercados", "Tarifa A (Comprador regular)", "Wilmer (Oriente)", "+58 412-1234567", "Ana Río", 30, 15000.0, "2026-08-01"),
            ("RIO VIDA", "Caracas Centro", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-7654321", "Carlos Vida", 15, 8000.0, "2026-09-02"),
            ("SIGO", "Margarita / Central", "Supermercados", "Tarifa A (Comprador regular)", "Wilmer (Oriente)", "+58 412-8888888", "Gerencia Sigo", 30, 25000.0, "2026-05-10"),
            ("TIERRA SANTA", "Sabana Grande", "Minimarket", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-9999999", "Ahmed T.S.", 15, 5000.0, "2026-09-15"),
            ("SUPER 900", "Catia", "Supermercados", "Tarifa B (Comprador medio)", "Ladimir (Occidente)", "+58 412-9876543", "Luis 900", 15, 6000.0, "2026-08-25"),
            ("TODO HOGAR", "Petare", "Comercial", "Tarifa C (Comprador esporádico)", "Tufic (Capital)", "+58 412-5432167", "María Hogar", 15, 4000.0, "2026-07-20"),
            ("VIVA", "El Recreo", "Supermercados", "Tarifa B (Comprador medio)", "Tufic (Capital)", "+58 412-4567890", "Supervisor Viva", 15, 7000.0, "2026-08-30"),
            ("WILMER", "El Valle", "Mayorista", "Tarifa A (Comprador regular)", "Wilmer (Oriente)", "+58 412-1357924", "Wilmer Distribución", 7, 10000.0, "2026-09-14"),
            ("PARAMO COLD 2024", "Altamira", "HORECA", "Tarifa A (Comprador regular)", "Tufic (Capital)", "+58 412-2468135", "Equipo Paramo", 15, 8000.0, "2026-09-16"),
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
    st.write("Centro analítico de alto rendimiento con alertas automáticas detalladas de facturas vencidas.")

    conn = sqlite3.connect(DB_NAME)
    df_ped = pd.read_sql("SELECT * FROM pedidos", conn)
    df_inv = pd.read_sql("SELECT * FROM inventario", conn)
    df_mer = pd.read_sql("SELECT * FROM mermas", conn)
    df_cxc = pd.read_sql("SELECT * FROM cobranza", conn)
    df_cli = pd.read_sql("SELECT * FROM clientes", conn)
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
    
    st.subheader("🔔 Centro de Alertas y Notificaciones Gerenciales")
    col_alerta_1, col_alerta_2 = st.columns(2)
    
    with col_alerta_1:
        st.markdown("### 🚨 Notificación de Facturas Vencidas (Morosidad)")
        if not df_cxc.empty:
            hoy_str = str(date.today())
            df_cxc["fecha_vencimiento"] = pd.to_datetime(df_cxc["fecha_vencimiento"])
            df_morosos = df_cxc[(df_cxc["estatus_pago"] != "Pagado") & (df_cxc["fecha_vencimiento"] < pd.Timestamp(hoy_str))]
            
            if not df_morosos.empty:
                total_mora = (df_morosos["monto_factura"] - df_morosos["monto_pagado"]).sum()
                st.error(f"⚠️ ¡Atención! Hay **{len(df_morosos)} facturas vencidas** por cobrar equivalente a **${total_mora:,.2f} USD**.")
                df_morosos["PENDIENTE ($)"] = df_morosos["monto_factura"] - df_morosos["monto_pagado"]
                df_display_mora = df_morosos[["nro_factura", "cliente", "fecha_emision", "fecha_vencimiento", "monto_factura", "PENDIENTE ($)", "estatus_pago"]]
                st.dataframe(df_display_mora, use_container_width=True)
            else:
                st.success("✅ No hay facturas vencidas en este momento.")
        else:
            st.info("No hay registros de facturación.")

    with col_alerta_2:
        st.markdown("### 💤 Alerta de Clientes Inactivos")
        dias_inactividad_limite = st.slider("Filtrar clientes sin pedidos hace más de (días):", min_value=5, max_value=90, value=30)
        
        if not df_cli.empty:
            hoy_dt = pd.Timestamp(date.today())
            df_cli["ultimo_pedido"] = pd.to_datetime(df_cli["ultimo_pedido"])
            df_cli["dias_sin_comprar"] = (hoy_dt - df_cli["ultimo_pedido"]).dt.days
            
            df_inactivos = df_cli[df_cli["dias_sin_comprar"] >= dias_inactividad_limite]
            
            if not df_inactivos.empty:
                st.warning(f"⚠️ Se detectaron **{len(df_inactivos)} sucursales** sin pedidos en los últimos {dias_inactividad_limite} días.")
                st.dataframe(df_inactivos[["matriz", "sucursal", "dupla", "contacto", "telefono", "dias_sin_comprar"]], use_container_width=True)
            else:
                st.success(f"✅ Todos los clientes están activos.")
        else:
            st.info("No hay clientes registrados.")

    st.markdown("---")
    st.subheader("📈 Gráficos de Comportamiento Financiero y Ventas")
    if not df_ped.empty:
        df_chart = df_ped.groupby("fecha_pedido")["monto_total"].sum().reset_index()
        st.bar_chart(df_chart.set_index("fecha_pedido"))
    else:
        st.info("Aún no hay suficientes registros de pedidos para graficar tendencias.")

# ---------------------------------------------------------
# 2. INVENTARIO POR FRUTA Y CALIBRE
# ---------------------------------------------------------
elif "2." in menu:
    st.title("📦 Control de Inventario por Frutas y Calibres en Existencia")
    st.write("Agrega los calibres que vayan ingresando para cada fruta. Las existencias se actualizarán al vender o registrar mermas.")

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
        lista_frutas_cat = df_cat["descripcion"].unique().tolist() if not df_cat.empty else []

        if not lista_frutas_cat:
            st.warning("⚠️ Primero debes registrar tus frutas en el módulo **'6. 🍓 Lista y Gestión de Productos'**.")
        else:
            with st.form("form_ingreso_fruta_calibre"):
                st.subheader("Registrar Ingreso de Fruta y Calibre Específico")
                col1, col2 = st.columns(2)
                with col1:
                    fruta_sel = st.selectbox("Seleccione Fruta Creada por Ti", lista_frutas_cat)
                    lote_num = st.text_input("Número de Lote", value=f"LOTE-{datetime.now().strftime('%Y%m%d')}")
                    calibre_ingresado = st.text_input("Indica el Calibre (Ej. 80/88, 100/110, Jumbo, Extra, etc.)")
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

# ---------------------------------------------------------
# 3. VENTAS & PEDIDOS POR CALIBRE (RESTOCK AUTOMÁTICO DE INVENTARIO)
# ---------------------------------------------------------
elif "3." in menu:
    st.title("🛒 Generador de Pedidos y Ventas por Calibre")
    st.write("Selecciona la fruta y el calibre en existencia. El stock se restará automáticamente del inventario al procesar el pedido.")

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

                    cursor.execute("UPDATE clientes SET ultimo_pedido = ? WHERE matriz = ? AND sucursal = ?", (str(date.today()), cli_sel, suc_sel))

                    # RESTAR DEL INVENTARIO Y REGISTRAR EN KARDEX SALIDA
                    for item in st.session_state.carrito_pedido:
                        cursor.execute("SELECT stock_cajas FROM inventario WHERE id = ?", (item["inventario_id"],))
                        stk_act = cursor.fetchone()[0]
                        nuevo_stk = max(0.0, stk_act - item["cajas"])
                        
                        cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stk, item["inventario_id"]))

                        cursor.execute("""
                            INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                            VALUES (?, ?, ?, 'SALIDA', ?, ?, ?, ?)
                        """, (item["lote"], item["producto"], item["calibre"], item["cajas"], f"Venta Pedido {nro_p}", str(date.today()), st.session_state.rol))

                    conn.commit()
                    conn.close()

                    st.session_state.carrito_pedido = []
                    st.success(f"¡Pedido {nro_p} procesado con éxito! Las existencias fueron descontadas de las cámaras de frío y se generó su factura CxC.")
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
    st.subheader("📋 Cuadro de Precios:")

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
    else:
        st.info("No hay productos en el catálogo. Agrégalos en el módulo '6. Lista y Gestión de Productos'.")

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
            realizado_por_m = st.text_input("¿Quién realizó el pedido?")
        with c_pm2:
            atendido_por_m = st.selectbox("¿Quién despachó / Asesor?", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
            recibido_por_m = st.text_input("¿Quién recibió en destino?")
            monto_m = st.number_input("Monto Total del Pedido ($)", min_value=0.1, value=1000.0)

        st.markdown("---")
        st.subheader("📌 Datos Importantes y Observaciones")
        datos_imp_m = st.text_area("Notas importantes:")
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

                    cursor.execute("UPDATE clientes SET ultimo_pedido = ? WHERE matriz = ?", (str(fecha_ped_m), cliente_m))

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
    st.title("🍓 Catálogo Oficial de Productos - Configuración de Calidad y Calibre")
    st.write("Aquí creas y defines tus frutas, indicando manualmente si es **Premium**, **Con detalle** o **A granel** y su calibre base.")

    tab_prod1, tab_prod2, tab_prod3 = st.tabs(["📋 Catálogo Actual", "✏️ Editar Producto", "➕ Registrar Nuevo Producto"])

    with tab_prod1:
        df_cat = get_catalogo_cache()
        if not df_cat.empty:
            st.dataframe(df_cat[["id", "codigo", "descripcion", "calibre", "clasificacion_calidad", "empaque_kg", "costo_caja", "precio_caja"]], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ Eliminar Producto del Catálogo")
            prod_id_del = st.selectbox("Seleccione ID de producto a eliminar:", df_cat["id"].tolist())
            if st.button("🗑️ Confirmar Eliminación"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM matriz_precios WHERE id = ?", (int(prod_id_del),))
                conn.commit()
                conn.close()
                st.success("¡Producto eliminado!")
                st.rerun()
        else:
            st.info("Tu catálogo está totalmente limpio. Agrega tu primer producto en la pestaña 'Registrar Nuevo Producto'.")

    with tab_prod2:
        df_cat_ed = get_catalogo_cache()
        if not df_cat_ed.empty:
            st.subheader("✏️ Modificar Detalle, Calidad y Calibre de tus Frutas")
            id_cat_ed = st.selectbox("Seleccione ID de producto a editar:", df_cat_ed["id"].tolist(), key="sel_ed_prod")
            row_prod_ed = df_cat_ed[df_cat_ed["id"] == id_cat_ed].iloc[0]

            with st.form("form_edicion_individual_prod"):
                e_cod = st.text_input("Código", value=row_prod_ed["codigo"])
                e_desc = st.text_input("Descripción de la Fruta", value=row_prod_ed["descripcion"])
                e_cal = st.text_input("Calibre", value=row_prod_ed["calibre"])
                
                calidad_actual = row_prod_ed["clasificacion_calidad"]
                opciones_calidad = ["Premium", "Con detalle", "A granel"]
                idx_cal = opciones_calidad.index(calidad_actual) if calidad_actual in opciones_calidad else 0
                e_calidad = st.selectbox("Clasificación de Calidad", opciones_calidad, index=idx_cal)
                
                e_emp = st.number_input("Empaque (Kg)", min_value=0.01, value=float(row_prod_ed["empaque_kg"]))
                e_cos = st.number_input("Costo Caja ($)", min_value=0.0, value=float(row_prod_ed["costo_caja"]))
                e_pre = st.number_input("Precio Caja ($)", min_value=0.0, value=float(row_prod_ed["precio_caja"]))

                if st.form_submit_button("💾 Guardar Cambios"):
                    p_kg_val = round(e_pre / e_emp, 2) if e_emp > 0 else 0.0
                    mrg_val = round(((e_pre - e_cos) / e_pre * 100), 1) if e_pre > 0 else 0.0
                    
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE matriz_precios 
                        SET codigo = ?, descripcion = ?, calibre = ?, clasificacion_calidad = ?, empaque_kg = ?, costo_caja = ?, precio_caja = ?, precio_kg = ?, margen_pct = ?
                        WHERE id = ?
                    """, (e_cod, e_desc.upper(), e_cal, e_calidad, e_emp, e_cos, e_pre, p_kg_val, mrg_val, int(id_cat_ed)))
                    conn.commit()
                    conn.close()
                    st.success("¡Producto actualizado exitosamente!")
                    st.rerun()

    with tab_prod3:
        with st.form("form_nuevo_producto_manual"):
            st.subheader("Crear Nuevo Producto en tu Catálogo")
            cp1, cp2 = st.columns(2)
            with cp1:
                n_cod = st.text_input("Código del Producto (Ej. 759106)")
                n_desc = st.text_input("Nombre de la Fruta (Ej. MANZANA GALA)")
                n_calibre = st.text_input("Calibre (Ej. 80/88, Granel, etc.)")
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
                    st.success("¡Nuevo producto creado con éxito bajo tu control!")
                    st.rerun()
                else:
                    st.error("Por favor complete código y descripción.")

# ---------------------------------------------------------
# 7. KARDEX DIARIO (ENTRADAS & SALIDAS)
# ---------------------------------------------------------
elif "7." in menu:
    st.title("🔄 Kardex Diario - Control de Entradas y Salidas de Inventario")
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
    st.write("Agrega nuevos clientes, edita sus datos en tiempo real o elimina sucursales.")

    tab_cli1, tab_cli2, tab_cli3 = st.tabs(["📋 Directorio Actual", "✏️ Editar Cliente / Sucursal", "➕ Registrar Nuevo Cliente"])

    with tab_cli1:
        df_clientes = get_clientes_cache()
        if not df_clientes.empty:
            st.dataframe(df_clientes, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ Eliminar Sucursal / Cliente")
            id_eliminar = st.selectbox("Seleccione ID de sucursal a eliminar:", df_clientes["id"].tolist())
            row_del = df_clientes[df_clientes["id"] == id_eliminar].iloc[0]
            st.warning(f"Va a eliminar la sucursal **{row_del['sucursal']}** de **{row_del['matriz']}**.")
            if st.button("🗑️ Confirmar Eliminación"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = ?", (int(id_eliminar),))
                conn.commit()
                conn.close()
                st.success("¡Sucursal eliminada exitosamente!")
                st.rerun()
        else:
            st.info("No hay clientes registrados en el directorio.")

    with tab_cli2:
        df_cli_ed = get_clientes_cache()
        if not df_cli_ed.empty:
            st.subheader("✏️ Modificar Datos de Sucursal Existente")
            id_ed = st.selectbox("Seleccione ID para Editar:", df_cli_ed["id"].tolist(), key="ed_cli_id")
            row_edit = df_cli_ed[df_cli_ed["id"] == id_ed].iloc[0]

            with st.form("form_editar_cliente"):
                e_matriz = st.text_input("Empresa Matriz", value=row_edit["matriz"])
                e_suc = st.text_input("Sucursal", value=row_edit["sucursal"])
                e_seg = st.text_input("Segmento", value=row_edit["segmento"])
                
                t_actual = row_edit["tarifa"]
                opciones_tarifas = ["Tarifa A (Comprador regular)", "Tarifa B (Comprador medio)", "Tarifa C (Comprador esporádico)"]
                idx_t = opciones_tarifas.index(t_actual) if t_actual in opciones_tarifas else 0
                e_tarifa = st.selectbox("Clasificación / Tarifa", opciones_tarifas, index=idx_t)
                
                d_actual = row_edit["dupla"]
                opciones_duplas = ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"]
                idx_d = opciones_duplas.index(d_actual) if d_actual in opciones_duplas else 0
                e_dupla = st.selectbox("Dupla Comercial Oficial", opciones_duplas, index=idx_d)
                
                e_tel = st.text_input("Teléfono", value=row_edit["telefono"])
                e_cont = st.text_input("Contacto", value=row_edit["contacto"])
                e_dias = st.number_input("Días de Crédito", min_value=1, value=int(row_edit["limite_credito_dias"]))
                e_monto = st.number_input("Límite de Crédito ($)", min_value=0.0, value=float(row_edit["limite_credito_dolares"]))

                if st.form_submit_button("💾 Guardar Cambios del Cliente"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE clientes 
                        SET matriz = ?, sucursal = ?, segmento = ?, tarifa = ?, dupla = ?, telefono = ?, contacto = ?, limite_credito_dias = ?, limite_credito_dolares = ?
                        WHERE id = ?
                    """, (e_matriz.upper(), e_suc.upper(), e_seg, e_tarifa, e_dupla, e_tel, e_cont, int(e_dias), e_monto, int(id_ed)))
                    conn.commit()
                    conn.close()
                    st.success("¡Datos del cliente actualizados con éxito!")
                    st.rerun()

    with tab_cli3:
        with st.form("form_nueva_sucursal_completa"):
            st.subheader("Registrar Nuevo Cliente / Sucursal")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                matriz_n = st.text_input("Empresa Matriz (Ej. CENTRAL MADERENSE)")
                sucursal_n = st.text_input("Nombre de la Sucursal (Ej. Sucursal Este)")
                segmento_n = st.selectbox("Segmento", ["Supermercados", "Mayorista", "Minimarket", "HORECA", "Comercial"])
                tarifa_n = st.selectbox("Clasificación / Tarifa", ["Tarifa A (Comprador regular)", "Tarifa B (Comprador medio)", "Tarifa C (Comprador esporádico)"])
            with c_s2:
                dupla_n = st.selectbox("Dupla Comercial Oficial", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
                telefono_n = st.text_input("Teléfono de Contacto", value="+58 412-")
                contacto_n = st.text_input("Nombre del Comprador / Encargado")
                cred_dias = st.number_input("Días de Crédito", min_value=1, value=15)
                cred_monto = st.number_input("Límite de Crédito ($)", min_value=0.0, value=10000.0)

            if st.form_submit_button("💾 Guardar Nuevo Cliente"):
                if matriz_n and sucursal_n:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (matriz, sucursal, segmento, tarifa, dupla, telefono, contacto, limite_credito_dias, limite_credito_dolares, ultimo_pedido)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (matriz_n.upper(), sucursal_n.upper(), segmento_n, tarifa_n, dupla_n, telefono_n, contacto_n, int(cred_dias), cred_monto, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success("¡Cliente y sucursal agregados con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor complete los campos obligatorios de Matriz y Sucursal.")

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
    st.title("💰 Departamento de Cobranza - Cuentas por Cobrar y Facturas")
    st.write("Gestiona las facturas emitidas, revisa saldos pendientes y registra pagos.")

    conn = sqlite3.connect(DB_NAME)
    df_cob = pd.read_sql("SELECT * FROM cobranza", conn)
    conn.close()

    if not df_cob.empty:
        st.subheader("📋 Estado Actual de Facturas")
        st.dataframe(df_cob, use_container_width=True)

        st.markdown("---")
        st.subheader("💵 Registrar Pago de Factura")
        with st.form("form_registrar_pago"):
            fac_sel = st.selectbox("Seleccione Nro. de Factura", df_cob["nro_factura"].tolist())
            row_fac = df_cob[df_cob["nro_factura"] == fac_sel].iloc[0]
            
            saldo_pendiente = row_fac["monto_factura"] - row_fac["monto_pagado"]
            st.info(f"Cliente: **{row_fac['cliente']}** | Monto Total: **${row_fac['monto_factura']:,.2f}** | Pendiente: **${saldo_pendiente:,.2f}**")

            pago_ingresado = st.number_input("Monto a Abonar / Pagar ($)", min_value=0.01, max_value=float(saldo_pendiente) if saldo_pendiente > 0 else 1.0, value=float(saldo_pendiente))

            if st.form_submit_button("💾 Registrar Abono / Pago"):
                nuevo_pagado = row_fac["monto_pagado"] + pago_ingresado
                nuevo_estatus = "Pagado" if nuevo_pagado >= row_fac["monto_factura"] else "Parcial"

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE cobranza 
                    SET monto_pagado = ?, estatus_pago = ?
                    WHERE nro_factura = ?
                """, (nuevo_pagado, nuevo_estatus, fac_sel))
                conn.commit()
                conn.close()

                st.success(f"¡Pago de ${pago_ingresado:,.2f} registrado para la factura {fac_sel}!")
                st.rerun()
    else:
        st.info("No hay registros de cobranza.")

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
# 15. CONTROL DE MERMAS & PÉRDIDAS (RESTA AUTOMÁTICA DE INVENTARIO)
# ---------------------------------------------------------
elif "15." in menu:
    st.title("🗑️ Control de Mermas y Pérdidas Financieras")
    st.write("Registra pérdidas de fruta. Al guardar, **el sistema restará automáticamente las cajas de las cámaras de frío**.")

    tab_m1, tab_m2 = st.tabs(["📋 Historial de Mermas", "➕ Registrar Nueva Merma (Resta Stock)"])

    with tab_m1:
        conn = sqlite3.connect(DB_NAME)
        df_mermas_hist = pd.read_sql("SELECT * FROM mermas", conn)
        conn.close()

        if not df_mermas_hist.empty:
            st.dataframe(df_mermas_hist, use_container_width=True)
        else:
            st.info("No hay mermas registradas.")

    with tab_m2:
        df_inv_merma = get_inventario_cache()
        df_inv_con_stock = df_inv_merma[df_inv_merma["stock_cajas"] > 0] if not df_inv_merma.empty else pd.DataFrame()

        if not df_inv_con_stock.empty:
            with st.form("form_registrar_merma_stock"):
                st.subheader("Seleccionar Lote y Calibre a Dar de Baja por Merma")
                
                # Crear opciones descriptivas para el selectbox
                opciones_lotes = []
                for _, r in df_inv_con_stock.iterrows():
                    opciones_lotes.append(f"ID: {r['id']} | Lote: {r['lote']} | {r['producto']} (Calibre: {r['calibre']}) - Stock: {r['stock_cajas']} cajas")

                lote_sel_str = st.selectbox("Lote y Producto en Cámara", opciones_lotes)
                
                # Extraer el ID del inventario seleccionado
                id_inv_sel = int(lote_sel_str.split("|")[0].replace("ID:", "").strip())
                row_lote_sel = df_inv_con_stock[df_inv_con_stock["id"] == id_inv_sel].iloc[0]

                st.info( ആരാy if False else f"Costo Unitario en Sistema: **${row_lote_sel['costo_unitario_caja']:,.2f} por caja** | Stock actual: **{row_lote_sel['stock_cajas']} cajas**")

                cajas_perdidas = st.number_input("Cantidad de Cajas a Dar de Baja (Merma)", min_value=1.0, max_value=float(row_lote_sel["stock_cajas"]), value=5.0)
                motivo_merma = st.text_input("Motivo de la Merma (Ej. Fruta madura, golpeada, daño por transporte)")
                fecha_m = st.date_input("Fecha de Registro", value=date.today())

                if st.form_submit_button("🗑️ CONFIRMAR MERMA Y RESTAR DEL INVENTARIO"):
                    try:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("BEGIN TRANSACTION;")

                        perdida_monetaria = cajas_perdidas * row_lote_sel["costo_unitario_caja"]

                        # 1. Registrar en tabla mermas
                        cursor.execute("""
                            INSERT INTO mermas (lote, producto, calibre, cantidad_perdida, costo_unitario, perdida_monetaria, motivo, fecha_merma)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (row_lote_sel["lote"], row_lote_sel["producto"], row_lote_sel["calibre"], cajas_perdidas, row_lote_sel["costo_unitario_caja"], perdida_monetaria, motivo_merma, str(fecha_m)))

                        # 2. Restar del stock de inventario
                        nuevo_stock_inv = max(0.0, row_lote_sel["stock_cajas"] - cajas_perdidas)
                        cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stock_inv, id_inv_sel))

                        # 3. Registrar salida en Kardex
                        cursor.execute("""
                            INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                            VALUES (?, ?, ?, 'SALIDA', ?, ?, ?, ?)
                        """, (row_lote_sel["lote"], row_lote_sel["producto"], row_lote_sel["calibre"], cajas_perdidas, f"Merma: {motivo_merma}", str(fecha_m), st.session_state.rol))

                        conn.commit()
                        conn.close()

                        st.success(f"¡Merma registrada! Se descontaron {cajas_perdidas} cajas de {row_lote_sel['producto']} (Calibre {row_lote_sel['calibre']}) del inventario en frío.")
                        st.rerun()

                    except Exception as e:
                        if 'conn' in locals():
                            conn.rollback()
                            conn.close()
                        st.error(f"Error al procesar la merma: {e}")
        else:
            st.warning("No hay existencias en inventario para registrar mermas.")

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
