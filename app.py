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
# BASE DE DATOS RELACIONAL INTEGRAL (SQLITE)
# ---------------------------------------------------------
DB_NAME = "frumix_enterprise_elite_v11.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Clientes (Matrices y Sucursales)
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
    
    # 2. Matriz de Precios y Catálogo Base
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matriz_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            barra TEXT,
            descripcion TEXT,
            calibre TEXT,
            empaque_kg REAL,
            costo_caja REAL,
            precio_caja REAL,
            precio_kg REAL,
            margen_pct REAL
        )
    """)
    
    # 3. Pedidos y Despachos Comerciales
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

    # 4. Cobranza y Cuentas por Cobrar (CxC)
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

    # 5. Inventario Diario por Lotes en Cámaras de Frío
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            producto TEXT,
            stock_inicial REAL,
            costo_unitario_caja REAL,
            fecha_ingreso TEXT
        )
    """)

    # 6. Mermas e Impacto Financiero
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mermas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            producto TEXT,
            cantidad_perdida REAL,
            perdida_monetaria REAL,
            motivo TEXT,
            fecha_merma TEXT
        )
    """)

    # 7. Embudo de Ventas (Sales Funnel)
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
            ("759101", "759101", "MANZANA GALA", "80/88", 19.0, 50.0, 68.0, 3.58, 26.5),
            ("759102", "759102", "MANZANA ROJA", "100/110", 19.0, 60.0, 80.0, 4.21, 25.0),
            ("759103", "759103", "MANZANA VERDE", "70/80", 19.0, 62.0, 84.0, 4.42, 26.2),
            ("759105", "759105", "MANZANA GALA GRANEL", "Granel", 23.0, 45.0, 65.0, 2.83, 30.7),
            ("759201", "759201", "PERA VERDE", "90/100", 18.0, 48.0, 65.0, 3.61, 26.1),
            ("759203", "759203", "PERA FORELLE EN BANDEJA", "Selección", 9.0, 60.0, 75.0, 8.33, 20.0),
            ("759301", "759301", "UVA RED GLOBE", "Extra", 8.2, 70.0, 95.0, 11.58, 26.3),
            ("759502", "759502", "CEREZA", "Jumbo", 2.5, 30.0, 45.0, 18.00, 33.3),
            ("759503", "759503", "ARANDANOS", "Premium", 0.125, 55.0, 70.0, 560.00, 21.4),
            ("759602", "759602", "PITAHAYA ROJA", "Grande", 1.0, 15.0, 22.0, 22.00, 31.8),
        ]
        cursor.executemany("""
            INSERT INTO matriz_precios (codigo, barra, descripcion, calibre, empaque_kg, costo_caja, precio_caja, precio_kg, margen_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, catalogo_inicial)
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
# MENÚ LATERAL ERP CON FILTRADO POR ROL
# ---------------------------------------------------------
st.sidebar.markdown(f"### 🍓 {EMPRESA['nombre']}")
st.sidebar.markdown(f"**Usuario:** {st.session_state.rol}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
st.sidebar.markdown("---")

modulos_disponibles = [
    "📊 Dashboard Gerencial & P&L",
    "📦 Inventario Diario en Cámaras",
    "🏢 Gestión y Edición de Clientes",
    "📈 Métricas de Pedidos (Diarios/Semanales)",
    "🎯 Embudo de Ventas (Sales Funnel)",
    "🛒 Ventas & Cotizador Pro (Con Calibres y Logo)",
    "📋 Registro Manual Detallado de Pedidos",
    "💰 Departamento de Cobranza & CxC",
    "🚚 Logística, Despacho & Rutas",
    "💲 Matriz Dinámica de Precios (Caja a KG)",
    "🗑️ Control de Mermas & Pérdidas",
    "📋 Historial Completo de Pedidos",
]

menu = st.sidebar.radio("Módulos ERP Enterprise Elite:", modulos_disponibles)

# ---------------------------------------------------------
# 1. DASHBOARD GERENCIAL & P&L
# ---------------------------------------------------------
if menu == "📊 Dashboard Gerencial & P&L":
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
    
    val_inv = (df_inv["stock_inicial"] * df_inv["costo_unitario_caja"]).sum() if not df_inv.empty else 0.0
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
# 2. INVENTARIO DIARIO EN CÁMARAS DE FRÍO
# ---------------------------------------------------------
elif menu == "📦 Inventario Diario en Cámaras":
    st.title("📦 Control de Inventario Diario en Cámaras de Frío")
    st.write("Registra nuevos lotes de frutas, verifica existencias y controla entradas diarias.")

    tab_inv1, tab_inv2 = st.tabs(["📋 Existencias Actuales", "➕ Registrar Ingreso de Lote Diario"])

    with tab_inv1:
        conn = sqlite3.connect(DB_NAME)
        df_inv = pd.read_sql("SELECT * FROM inventario", conn)
        conn.close()
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True)
        else:
            st.info("No hay inventario registrado en cámaras.")

    with tab_inv2:
        with st.form("form_ingreso_lote"):
            st.subheader("Ingresar Nuevo Lote al Inventario")
            l_nro = st.text_input("Número de Lote (Ej. LOTE-2026-10-20)", value="LOTE-")
            l_prod = st.text_input("Nombre del Producto (Ej. MANZANA GALA)")
            l_stock = st.number_input("Cantidad Inicial de Cajas", min_value=0.1, value=100.0)
            l_costo = st.number_input("Costo Unitario por Caja ($)", min_value=0.0, value=50.0)
            l_fecha = st.date_input("Fecha de Ingreso", value=date.today())

            if st.form_submit_button("Guardar Ingreso de Lote"):
                if l_stock > 0 and l_costo >= 0:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO inventario (lote, producto, stock_inicial, costo_unitario_caja, fecha_ingreso)
                        VALUES (?, ?, ?, ?, ?)
                    """, (l_nro.upper(), l_prod.upper(), l_stock, l_costo, str(l_fecha)))
                    conn.commit()
                    conn.close()
                    st.success("¡Lote ingresado al inventario con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor verifique que los valores numéricos sean válidos.")

# ---------------------------------------------------------
# 3. GESTIÓN Y EDICIÓN DE CLIENTES
# ---------------------------------------------------------
elif menu == "🏢 Gestión y Edición de Clientes":
    st.title("🏢 Directorio, Edición y Gestión de Clientes (Matrices y Sucursales)")
    st.write("Agrega, edita en tiempo real o elimina sucursales y matrices comerciales.")

    tab_cli1, tab_cli2, tab_cli3 = st.tabs(["📋 Ver Directorio", "✏️ Editar Cliente / Sucursal", "➕ Agregar Nueva Sucursal"])

    with tab_cli1:
        df_clientes = get_clientes_cache()
        if not df_clientes.empty:
            st.dataframe(df_clientes, use_container_width=True)
            st.markdown("---")
            st.subheader("🗑️ Eliminar Sucursal")
            id_eliminar = st.selectbox("Seleccione ID de sucursal a eliminar:", df_clientes["id"].tolist())
            row_del = df_clientes[df_clientes["id"] == id_eliminar].iloc[0]
            st.warning(f"Va a eliminar la sucursal **{row_del['sucursal']}** de **{row_del['matriz']}**.")
            if st.button("🗑️ Confirmar Eliminación"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = ?", (int(id_eliminar),))
                conn.commit()
                conn.close()
                st.success("¡Sucursal eliminada!")
                st.rerun()

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
                e_tarifa = st.selectbox("Clasificación / Tarifa", ["Tarifa A (Comprador regular)", "Tarifa B (Comprador medio)", "Tarifa C (Comprador esporádico)"])
                e_dupla = st.selectbox("Dupla Comercial Oficial", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
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
            st.subheader("Registrar Nueva Sucursal")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                matriz_n = st.text_input("Empresa Matriz (Ej. CENTRAL MADERENSE)")
                sucursal_n = st.text_input("Nombre de la Sucursal")
                segmento_n = st.selectbox("Segmento", ["Supermercados", "Mayorista", "Minimarket", "HORECA", "Comercial"])
                tarifa_n = st.selectbox("Clasificación / Tarifa", ["Tarifa A (Comprador regular)", "Tarifa B (Comprador medio)", "Tarifa C (Comprador esporádico)"])
            with c_s2:
                dupla_n = st.selectbox("Dupla Comercial Oficial", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
                telefono_n = st.text_input("Teléfono de Contacto", value="+58 412-")
                contacto_n = st.text_input("Nombre del Comprador")
                cred_dias = st.number_input("Días de Crédito", min_value=1, value=15)
                cred_monto = st.number_input("Límite de Crédito ($)", min_value=0.0, value=10000.0)

            if st.form_submit_button("Guardar Nueva Sucursal"):
                if matriz_n and sucursal_n:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (matriz, sucursal, segmento, tarifa, dupla, telefono, contacto, limite_credito_dias, limite_credito_dolares, ultimo_pedido)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (matriz_n.upper(), sucursal_n.upper(), segmento_n, tarifa_n, dupla_n, telefono_n, contacto_n, int(cred_dias), cred_monto, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success("¡Sucursal agregada con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor completa Matriz y Sucursal.")

# ---------------------------------------------------------
# 4. MÉTRICAS DE PEDIDOS
# ---------------------------------------------------------
elif menu == "📈 Métricas de Pedidos (Diarios/Semanales)":
    st.title("📈 Métricas y Registro de Pedidos (Diarios, Semanales y Mensuales)")
    st.write("Auditoría de volumen de pedidos ejecutados por períodos de tiempo.")

    conn = sqlite3.connect(DB_NAME)
    df_p = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_p.empty:
        df_p["fecha_dt"] = pd.to_datetime(df_p["fecha_pedido"])
        hoy_str = str(date.today())
        
        pedidos_hoy = df_p[df_p["fecha_pedido"] == hoy_str]
        hace_7_dias = pd.Timestamp.today() - pd.Timedelta(days=7)
        pedidos_sem = df_p[df_p["fecha_dt"] >= hace_7_dias]
        mes_actual = pd.Timestamp.today().month
        pedidos_mes = df_p[df_p["fecha_dt"].dt.month == mes_actual]

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Pedidos Realizados Hoy", len(pedidos_hoy), f"${pedidos_hoy['monto_total'].sum():,.2f}")
        with col_m2:
            st.metric("Pedidos Últimos 7 Días", len(pedidos_sem), f"${pedidos_sem['monto_total'].sum():,.2f}")
        with col_m3:
            st.metric("Pedidos Mes en Curso", len(pedidos_mes), f"${pedidos_mes['monto_total'].sum():,.2f}")

        st.markdown("---")
        st.subheader("📋 Listado Histórico Detallado de Pedidos")
        st.dataframe(df_p, use_container_width=True)
    else:
        st.info("No hay pedidos registrados en el sistema todavía.")

# ---------------------------------------------------------
# 5. EMBUDO DE VENTAS (SALES FUNNEL)
# ---------------------------------------------------------
elif menu == "🎯 Embudo de Ventas (Sales Funnel)":
    st.title("🎯 Embudo de Ventas y Seguimiento Comercial B2B")
    st.write("Gestiona las oportunidades comerciales desde la prospección de espacios en anaquel hasta el cierre.")

    df_cli_list = get_clientes_cache()
    lista_matrices_activas = df_cli_list["matriz"].unique().tolist() if not df_cli_list.empty else ["BULLKING"]

    tab_f1, tab_f2 = st.tabs(["📊 Embudos Activos", "➕ Registrar Oportunidad"])

    with tab_f1:
        conn = sqlite3.connect(DB_NAME)
        df_funnel = pd.read_sql("SELECT * FROM embudo_ventas", conn)
        conn.close()

        if not df_funnel.empty:
            st.dataframe(df_funnel, use_container_width=True)
            st.markdown("---")
            sel_id = st.selectbox("Seleccione ID de Oportunidad para Mover de Fase:", df_funnel["id"].tolist())
            row_op = df_funnel[df_funnel["id"] == sel_id].iloc[0]
            
            nueva_etapa = st.selectbox(
                "Mover a Fase:",
                ["1. Prospección / Lead", "2. Visita y Muestras", "3. Cotización Emitida", "4. Negociación y Crédito", "5. Cierre Ganado", "6. Cierre Perdido"]
            )
            if st.button("💾 Actualizar Fase"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE embudo_ventas SET etapa_embudo = ?, fecha_actualizacion = ? WHERE id = ?", (nueva_etapa, str(date.today()), int(sel_id)))
                conn.commit()
                conn.close()
                st.success("¡Fase actualizada!")
                st.rerun()
        else:
            st.info("No hay oportunidades en el embudo.")

    with tab_f2:
        with st.form("form_nuevo_embudo"):
            negocio_n = st.text_input("Nombre de la Oportunidad")
            cliente_n = st.selectbox("Cliente Matriz", lista_matrices_activas)
            etapa_n = st.selectbox("Fase Inicial", ["1. Prospección / Lead", "2. Visita y Muestras", "3. Cotización Emitida", "4. Negociación y Crédito"])
            valor_n = st.number_input("Valor Estimado ($)", min_value=0.0, value=1500.0)
            prob_n = st.selectbox("Probabilidad", ["Alta (80%)", "Media (50%)", "Baja (20%)"])
            resp_n = st.selectbox("Dupla Responsable", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])

            if st.form_submit_button("Agregar al Embudo"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO embudo_ventas (negocio, cliente, etapa_embudo, valor_estimado, probabilidad, responsable, fecha_actualizacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (negocio_n, cliente_n, etapa_n, valor_n, prob_n, resp_n, str(date.today())))
                conn.commit()
                conn.close()
                st.success("¡Oportunidad agregada!")
                st.rerun()

# ---------------------------------------------------------
# 6. VENTAS & COTIZADOR PRO
# ---------------------------------------------------------
elif menu == "🛒 Ventas & Cotizador Pro (Con Calibres y Logo)":
    st.title("🛒 Departamento de Ventas - Cotizador B2B Profesional")
    st.write("Modifica el precio por caja en la tabla; el precio por kilogramo se calculará de inmediato.")

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
        vig_sel = st.date_input("Validez de la Oferta:", value=date.today() + pd.Timedelta(days=7))

    if not cli_row_sel.empty:
        l_cred = cli_row_sel.iloc[0]["limite_credito_dolares"]
        l_dias = cli_row_sel.iloc[0]["limite_credito_dias"]
        st.info(f"💳 **Crédito ({cli_sel} - {suc_sel}):** ${l_cred:,.2f} USD | **Plazo:** {l_dias} días")

    st.markdown("---")
    st.subheader("📋 Cuadro de Precios (Edita la columna 'PRECIO CAJA ($)'):")

    if not df_mat.empty:
        df_editor_v = df_mat[["codigo", "barra", "descripcion", "calibre", "empaque_kg", "costo_caja", "precio_caja"]].copy()
        df_editor_v.columns = ["CÓDIGO", "BARRA", "DESCRIPCIÓN", "CALIBRE", "EMPAQUE/KG", "COSTO CAJA ($)", "PRECIO CAJA ($)"]

        df_editado_venta = st.data_editor(df_editor_v, use_container_width=True, key="cotizador_tabla_maestra")

        df_editado_venta["PRECIO POR KG ($)"] = df_editado_venta.apply(
            lambda r: round(r["PRECIO CAJA ($)"] / r["EMPAQUE/KG"], 2) if r["EMPAQUE/KG"] > 0 else 0.0, axis=1
        )

        st.markdown("---")
        st.subheader("📊 Vista Previa Actualizada del Cotizador:")
        st.dataframe(df_editado_venta, use_container_width=True)

        if st.button("💾 Procesar Pedido (Transacción Atómica Segura)"):
            det_json = json.dumps(df_editado_venta.to_dict(orient="records"))
            monto_aprox = df_editado_venta["PRECIO CAJA ($)"].sum()
            costo_aprox = df_editado_venta["COSTO CAJA ($)"].sum()
            ganancia_aprox = monto_aprox - costo_aprox
            nro_p = f"PED-{datetime.now().strftime('%Y%m%d%H%M')}"

            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION;")
                
                cursor.execute("""
                    INSERT INTO pedidos (nro_pedido, cliente, sucursal, realizado_por, atendido_por, recibido_por, datos_importantes, fecha_pedido, monto_total, costo_total, ganancia_estimada, estatus_despacho, detalle_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?)
                """, (nro_p, cli_sel, suc_sel, "Sistema Cotizador", asesor_asignado, "Cliente Final", "Generado desde Cotizador Pro", str(date.today()), monto_aprox, costo_aprox, ganancia_aprox, det_json))
                
                cursor.execute("""
                    INSERT INTO cobranza (nro_factura, cliente, fecha_emision, fecha_vencimiento, monto_factura, monto_pagado, estatus_pago)
                    VALUES (?, ?, ?, ?, ?, 0.0, 'Pendiente')
                """, (f"FAC-{nro_p}", cli_sel, str(date.today()), str(date.today() + pd.Timedelta(days=15)), monto_aprox))

                cursor.execute("UPDATE clientes SET ultimo_pedido = ? WHERE matriz = ? AND sucursal = ?", (str(date.today()), cli_sel, suc_sel))
                
                conn.commit()
                conn.close()
                st.success(f"¡Pedido {nro_p} procesado con éxito, sincronizado y validado de forma atómica!")
            except Exception as e:
                if 'conn' in locals():
                    conn.rollback()
                    conn.close()
                st.error(f"Error crítico en la transacción: {e}")

    st.markdown("---")
    st.subheader("📄 Generar Formato Imprimible (Arial 12, Justificado Izquierda, Firma Centrada)")
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
                    <th>Empaque (Kg)</th>
                    <th>Precio Caja ($)</th>
                    <th>Precio por KG ($)</th>
                </tr>
        """
        for _, r in df_editado_venta.iterrows():
            html_doc += f"<tr><td>{r['CÓDIGO']}</td><td>{r['DESCRIPCIÓN']}</td><td>{r['CALIBRE']}</td><td>{r['EMPAQUE/KG']}</td><td>${r['PRECIO CAJA ($)']:.2f}</td><td>${r['PRECIO POR KG ($)']:.2f}</td></tr>"
        html_doc += f"""
            </table>
            <br>
            <p><strong>Condiciones Comerciales:</strong> Sujeto a disponibilidad en cámaras de frío. Validez de oferta hasta {vig_sel}.</p>
            
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
# 7. REGISTRO MANUAL DETALLADO DE PEDIDOS
# ---------------------------------------------------------
elif menu == "📋 Registro Manual Detallado de Pedidos":
    st.title("📋 Registro Manual de Pedidos y Trazabilidad")
    st.write("Ingresa de forma manual los datos completos de un pedido con validación atómica.")

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

        if st.form_submit_button("💾 Guardar Pedido Manualmente (Atómico)"):
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
                    st.success(f"¡Pedido manual {nro_ped_m} registrado y sincronizado de forma segura!")
                    st.rerun()
                except Exception as e:
                    if 'conn' in locals():
                        conn.rollback()
                        conn.close()
                    st.error(f"Error al procesar el pedido: {e}")
            else:
                st.error("Por favor complete los campos obligatorios y verifique que el monto sea mayor a 0.")

# ---------------------------------------------------------
# 8. DEPARTAMENTO DE COBRANZA & CxC
# ---------------------------------------------------------
elif menu == "💰 Departamento de Cobranza & CxC":
    st.title("💰 Departamento de Cobranza - Cuentas por Cobrar y Morosidad")
    st.write("Control exhaustivo de facturas, plazos de crédito y alertas automáticas.")

    df_cli_list = get_clientes_cache()
    lista_matrices_cobro = df_cli_list["matriz"].tolist() if not df_cli_list.empty else ["BULLKING"]

    tab_c1, tab_c2, tab_c3 = st.tabs(["📋 Facturas Activas", "➕ Registrar Factura", "⚠️ Alertas de Morosidad"])

    with tab_c1:
        conn = sqlite3.connect(DB_NAME)
        df_cxc = pd.read_sql("SELECT * FROM cobranza", conn)
        conn.close()

        if not df_cxc.empty:
            st.dataframe(df_cxc, use_container_width=True)
            sel_fact = st.selectbox("ID de Factura a Abonar:", df_cxc["id"].tolist())
            fact_row = df_cxc[df_cxc["id"] == sel_fact].iloc[0]
            
            monto_abono = st.number_input("Monto del Abono ($)", min_value=0.0, value=float(fact_row['monto_factura'] - fact_row['monto_pagado']))
            nuevo_estatus = st.selectbox("Estatus:", ["Pendiente", "Parcial", "Pagado", "Vencido"])

            if st.button("💾 Actualizar Cobranza"):
                nuevo_pagado = fact_row['monto_pagado'] + monto_abono
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE cobranza SET monto_pagado = ?, estatus_pago = ? WHERE id = ?", (nuevo_pagado, nuevo_estatus, int(sel_fact)))
                conn.commit()
                conn.close()
                st.success("¡Cobranza actualizada!")
                st.rerun()
        else:
            st.info("No hay facturas registradas.")

    with tab_c2:
        with st.form("form_reg_cxc"):
            nro_fac = st.text_input("Nro. Factura", value="FAC-2026-")
            cli_fac = st.selectbox("Cliente Matriz", lista_matrices_cobro)
            monto_fac = st.number_input("Monto Total ($)", min_value=0.1, value=500.0)
            f_emi = st.date_input("Fecha Emisión", value=date.today())
            dias_cred = st.number_input("Días de Crédito", min_value=1, value=15)
            f_ven = date.today() + pd.Timedelta(days=int(dias_cred))

            if st.form_submit_button("Generar Factura"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cobranza (nro_factura, cliente, fecha_emision, fecha_vencimiento, monto_factura, monto_pagado, estatus_pago)
                    VALUES (?, ?, ?, ?, ?, 0.0, 'Pendiente')
                """, (nro_fac.upper(), cli_fac, str(f_emi), str(f_ven), monto_fac))
                conn.commit()
                conn.close()
                st.success("¡Factura generada!")
                st.rerun()

    with tab_c3:
        conn = sqlite3.connect(DB_NAME)
        df_cxc_alert = pd.read_sql("SELECT * FROM cobranza", conn)
        conn.close()
        if not df_cxc_alert.empty:
            df_cxc_alert["vence_dt"] = pd.to_datetime(df_cxc_alert["fecha_vencimiento"]).dt.date
            vencidas = df_cxc_alert[(df_cxc_alert["vence_dt"] < date.today()) & (df_cxc_alert["estatus_pago"] != "Pagado")]
            if not vencidas.empty:
                st.error(f"⚠️ ¡Hay {len(vencidas)} facturas vencidas!")
                st.dataframe(vencidas, use_container_width=True)
            else:
                st.success("✅ No hay facturas vencidas.")

# ---------------------------------------------------------
# 9. LOGÍSTICA, DESPACHO & RUTAS
# ---------------------------------------------------------
elif menu == "🚚 Logística, Despacho & Rutas":
    st.title("🚚 Logística y Estatus de Despachos")
    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_peds.empty:
        st.dataframe(df_peds, use_container_width=True)
        sel_p_id = st.selectbox("ID de Pedido:", df_peds["id"].tolist())
        nuevo_estatus_desp = st.selectbox("Estatus de Despacho:", ["Pendiente", "En Ruta de Entrega", "Entregado Conforme", "Incidencia"])
        if st.button("💾 Actualizar Despacho"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE pedidos SET estatus_despacho = ? WHERE id = ?", (nuevo_estatus_desp, int(sel_p_id)))
            conn.commit()
            conn.close()
            st.success("¡Despacho actualizado!")
            st.rerun()
    else:
        st.info("No hay pedidos para despachar.")

# ---------------------------------------------------------
# 10. MATRIZ DINÁMICA DE PRECIOS
# ---------------------------------------------------------
elif menu == "💲 Matriz Dinámica de Precios (Caja a KG)":
    st.title("💲 Matriz de Precios - Conversión Caja a Kilogramo")
    df_m = get_catalogo_cache()

    if not df_m.empty:
        df_m_edit = df_m[["id", "codigo", "descripcion", "calibre", "empaque_kg", "costo_caja", "precio_caja"]].copy()
        df_m_edit.columns = ["ID", "CÓDIGO", "DESCRIPCIÓN", "CALIBRE", "EMPAQUE/KG", "COSTO CAJA ($)", "PRECIO CAJA ($)"]
        df_resultado = st.data_editor(df_m_edit, use_container_width=True, key="matriz_def")

        df_resultado["PRECIO POR KG ($)"] = df_resultado.apply(lambda r: round(r["PRECIO CAJA ($)"] / r["EMPAQUE/KG"], 2) if r["EMPAQUE/KG"] > 0 else 0.0, axis=1)
        df_resultado["MARGEN BRUTO (%)"] = df_resultado.apply(lambda r: round(((r["PRECIO CAJA ($)"] - r["COSTO CAJA ($)"]) / r["PRECIO CAJA ($)"] * 100), 1) if r["PRECIO CAJA ($)"] > 0 else 0.0, axis=1)

        st.dataframe(df_resultado, use_container_width=True)
        if st.button("💾 Guardar Cambios en la Matriz"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            for _, row in df_resultado.iterrows():
                cursor.execute("""
                    UPDATE matriz_precios SET costo_caja = ?, precio_caja = ?, precio_kg = ?, margen_pct = ? WHERE id = ?
                """, (row["COSTO CAJA ($)"], row["PRECIO CAJA ($)"], row["PRECIO POR KG ($)"], row["MARGEN BRUTO (%)"], int(row["ID"])))
            conn.commit()
            conn.close()
            st.success("¡Matriz actualizada!")
            st.rerun()

# ---------------------------------------------------------
# 11. CONTROL DE MERMAS & PÉRDIDAS
# ---------------------------------------------------------
elif menu == "🗑️ Control de Mermas & Pérdidas":
    st.title("🗑️ Control de Mermas y Pérdidas Financieras")
    conn = sqlite3.connect(DB_NAME)
    df_inv_m = pd.read_sql("SELECT * FROM inventario", conn)
    conn.close()

    if not df_inv_m.empty:
        with st.form("form_merma"):
            lote_opts = [f"ID: {r['id']} | Lote: {r['lote']} - {r['producto']}" for _, r in df_inv_m.iterrows()]
            sel_l_merma = st.selectbox("Lote Afectado:", lote_opts)
            cant_p = st.number_input("Cajas Perdidas", min_value=0.1, value=1.0)
            motivo_m = st.selectbox("Motivo", ["Maduración", "Golpes", "Descomposición", "Transporte"])
            fecha_m = st.date_input("Fecha", value=date.today())

            if st.form_submit_button("Procesar Merma"):
                lote_id_sel = int(sel_l_merma.split("ID: ")[1].split(" |")[0])
                row_l = df_inv_m[df_inv_m["id"] == lote_id_sel].iloc[0]
                perdida_dinero = cant_p * row_l["costo_unitario_caja"]

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mermas (lote_id, producto, cantidad_perdida, perdida_monetaria, motivo, fecha_merma)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lote_id_sel, row_l["producto"], cant_p, perdida_dinero, motivo_m, str(fecha_m)))
                conn.commit()
                conn.close()
                st.success(f"¡Merma registrada! Pérdida: ${perdida_dinero:,.2f}")
                st.rerun()

# ---------------------------------------------------------
# 12. HISTORIAL COMPLETO DE PEDIDOS
# ---------------------------------------------------------
elif menu == "📋 Historial Completo de Pedidos":
    st.title("📋 Historial y Fidelidad Histórica de Pedidos B2B")
    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_peds.empty:
        st.dataframe(df_peds, use_container_width=True)
    else:
        st.info("No hay pedidos registrados todavía.")
