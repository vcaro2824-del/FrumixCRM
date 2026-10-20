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
    page_title="Frumix C.A. - ERP B2B con Logo Oficial",
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
# BASE DE DATOS RELACIONAL CON GESTIÓN DE SUCURSALES (SQLITE)
# ---------------------------------------------------------
DB_NAME = "frumix_sucursales_elite.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Clientes (Matrices y Sucursales Dinámicas)
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
            atendido_por TEXT,
            fecha_pedido TEXT,
            monto_total REAL,
            costo_total REAL,
            ganancia_estimada REAL,
            estatus_despacho TEXT,
            zona_envio TEXT,
            transporte TEXT,
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

    # 5. Inventario por Lotes en Cámaras de Frío
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
            ("759101", "759101", "MANZANA GALA", 19.0, 50.0, 68.0, 3.58, 26.5),
            ("759102", "759102", "MANZANA ROJA", 19.0, 60.0, 80.0, 4.21, 25.0),
            ("759103", "759103", "MANZANA VERDE", 19.0, 62.0, 84.0, 4.42, 26.2),
            ("759105", "759105", "MANZANA GALA GRANEL", 23.0, 45.0, 65.0, 2.83, 30.7),
            ("759201", "759201", "PERA VERDE", 18.0, 48.0, 65.0, 3.61, 26.1),
            ("759203", "759203", "PERA FORELLE EN BANDEJA", 9.0, 60.0, 75.0, 8.33, 20.0),
            ("759301", "759301", "UVA RED GLOBE", 8.2, 70.0, 95.0, 11.58, 26.3),
            ("759502", "759502", "CEREZA", 2.5, 30.0, 45.0, 18.00, 33.3),
            ("759503", "759503", "ARANDANOS", 0.125, 55.0, 70.0, 560.00, 21.4),
            ("759602", "759602", "PITAHAYA ROJA", 1.0, 15.0, 22.0, 22.00, 31.8),
        ]
        cursor.executemany("""
            INSERT INTO matriz_precios (codigo, barra, descripcion, empaque_kg, costo_caja, precio_caja, precio_kg, margen_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, catalogo_inicial)
        conn.commit()

    # Cargar los Clientes Oficiales con sus Matrices y Sucursales
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        clientes_oficiales = [
            ("BULLKING", "Principal Caracas", "Supermercados", "Tarifa A", "Dupla 1", "+58 412-1111111", "Compras Bullking", 15, 12000.0, "2026-10-10"),
            ("CENTRAL MADERENSE", "Sucursal Este", "Supermercados", "Tarifa A", "Dupla 1", "+58 412-2222222", "Juan Pérez", 30, 20000.0, "2026-09-15"),
            ("CENTRAL MADERENSE", "Sucursal Centro", "Supermercados", "Tarifa A", "Dupla 1", "+58 412-2222223", "María López", 30, 20000.0, "2026-09-20"),
            ("SUPERMERCADO EUROS", "La Candelaria", "Supermercados", "Tarifa B", "Dupla 2", "+58 412-3333333", "Ana Gómez", 15, 8000.0, "2026-10-18"),
            ("LADIMIR", "Mercado Mayor", "Mayorista", "Tarifa A", "Dupla 3", "+58 412-4444444", "Carlos Ladimir", 7, 15000.0, "2026-08-01"),
            ("SUPERMERCADOS LUXOR", "Boleíta", "Supermercados", "Tarifa B", "Dupla 2", "+58 412-5555555", "Luis Luxor", 15, 10000.0, "2026-10-01"),
            ("MERCATO", "Chacao", "Supermercados", "Tarifa B", "Dupla 2", "+58 412-3211234", "Gerencia Mercato", 15, 7000.0, "2026-10-05"),
            ("PLAN SUAREZ", "Baruta", "Supermercados", "Tarifa A", "Dupla 1", "+58 412-6666666", "Mario Suarez", 30, 18000.0, "2026-07-20"),
            ("RIO CARACAS", "Antímano", "Supermercados", "Tarifa A", "Dupla 2", "+58 412-7777777", "Pedro Río", 15, 12000.0, "2026-10-12"),
            ("RIO MARGARITA", "Porlamar", "Supermercados", "Tarifa A", "Dupla 3", "+58 412-1234567", "Ana Río", 30, 15000.0, "2026-09-01"),
            ("RIO VIDA", "Caracas Centro", "Supermercados", "Tarifa B", "Dupla 2", "+58 412-7654321", "Carlos Vida", 15, 8000.0, "2026-10-02"),
            ("SIGO", "Margarita / Central", "Supermercados", "Tarifa A", "Dupla 3", "+58 412-8888888", "Gerencia Sigo", 30, 25000.0, "2026-06-10"),
            ("TIERRA SANTA", "Sabana Grande", "Minimarket", "Tarifa B", "Dupla 2", "+58 412-9999999", "Ahmed T.S.", 15, 5000.0, "2026-10-15"),
            ("SUPER 900", "Catia", "Supermercados", "Tarifa B", "Dupla 1", "+58 412-9876543", "Luis 900", 15, 6000.0, "2026-09-25"),
            ("TODO HOGAR", "Petare", "Comercial", "Tarifa C", "Dupla 2", "+58 412-5432167", "María Hogar", 15, 4000.0, "2026-08-20"),
            ("VIVA", "El Recreo", "Supermercados", "Tarifa B", "Dupla 2", "+58 412-4567890", "Supervisor Viva", 15, 7000.0, "2026-09-30"),
            ("WILMER", "El Valle", "Mayorista", "Tarifa A", "Dupla 1", "+58 412-1357924", "Wilmer Distribución", 7, 10000.0, "2026-10-14"),
            ("PARAMO COLD 2024", "Altamira", "HORECA", "Tarifa A", "Dupla 2", "+58 412-2468135", "Equipo Paramo", 15, 8000.0, "2026-10-16"),
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
# MENÚ LATERAL ERP CON GESTIÓN DE SUCURSALES Y LOGO
# ---------------------------------------------------------
st.sidebar.markdown(f"### 🍓 {EMPRESA['nombre']}")
st.sidebar.markdown(f"**RIF:** {EMPRESA['rif']}")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Módulos ERP Enterprise Elite:",
    [
        "📊 Dashboard Gerencial & P&L",
        "🏢 Gestión de Clientes (Matrices y Sucursales)",
        "🎯 Embudo de Ventas (Sales Funnel)",
        "🛒 Ventas & Cotizador Pro (PDF/HTML)",
        "💰 Departamento de Cobranza & CxC",
        "🚚 Logística, Despacho & Rutas",
        "💲 Matriz Dinámica de Precios (Caja a KG)",
        "🗑️ Control de Mermas & Pérdidas",
        "📦 Registro y Estatus de Pedidos",
    ],
)

# ---------------------------------------------------------
# 1. DASHBOARD GERENCIAL & P&L
# ---------------------------------------------------------
if menu == "📊 Dashboard Gerencial & P&L":
    st.title("📊 Dashboard Gerencial y Estado de Resultados (P&L)")
    st.write("Centro analítico de alto rendimiento para el control financiero absoluto de Frumix C.A.")

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
# 2. GESTIÓN DE CLIENTES (MATRICES Y SUCURSALES)
# ---------------------------------------------------------
elif menu == "🏢 Gestión de Clientes (Matrices y Sucursales)":
    st.title("🏢 Directorio y Gestión de Clientes (Matrices y Sucursales)")
    st.write("Agrega, edita o elimina matrices comerciales y sus respectivas sucursales en tiempo real.")

    tab_cli1, tab_cli2 = st.tabs(["📋 Directorio Completo de Sucursales", "➕ Agregar Nueva Matriz o Sucursal"])

    with tab_cli1:
        conn = sqlite3.connect(DB_NAME)
        df_clientes = pd.read_sql("SELECT * FROM clientes", conn)
        conn.close()

        if not df_clientes.empty:
            st.dataframe(df_clientes, use_container_width=True)

            st.markdown("---")
            st.subheader("🗑️ Eliminar Sucursal del Sistema")
            id_eliminar = st.selectbox("Seleccione ID de la sucursal a eliminar:", df_clientes["id"].tolist())
            suc_sel_row = df_clientes[df_clientes["id"] == id_eliminar].iloc[0]
            st.warning(f"Va a eliminar la sucursal **{suc_sel_row['sucursal']}** de la matriz **{suc_sel_row['matriz']}**.")

            if st.button("🗑️ Confirmar y Eliminar Sucursal"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = ?", (int(id_eliminar),))
                conn.commit()
                conn.close()
                st.success("¡Sucursal eliminada con éxito!")
                st.rerun()
        else:
            st.info("No hay sucursales registradas.")

    with tab_cli2:
        with st.form("form_nueva_sucursal"):
            st.subheader("Registrar Nueva Sucursal / Cliente")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                matriz_n = st.text_input("Empresa Matriz (Ej. CENTRAL MADERENSE)")
                sucursal_n = st.text_input("Nombre de la Sucursal (Ej. Sucursal Las Mercedes)")
                segmento_n = st.selectbox("Segmento", ["Supermercados", "Mayorista", "Minimarket", "HORECA", "Comercial"])
                tarifa_n = st.selectbox("Tarifa Asignada", ["Tarifa A", "Tarifa B", "Tarifa C"])
            with c_s2:
                dupla_n = st.selectbox("Dupla Comercial", ["Dupla 1 (Oriente-Centro)", "Dupla 2 (Capital)", "Dupla 3 (Occidente)"])
                telefono_n = st.text_input("Teléfono de Contacto", value="+58 412-")
                contacto_n = st.text_input("Nombre del Comprador / Encargado")
                cred_dias = st.number_input("Días de Crédito", min_value=1, value=15)
                cred_monto = st.number_input("Límite de Crédito ($)", min_value=0.0, value=10000.0)

            if st.form_submit_button("Guardar Sucursal en el Directorio"):
                if matriz_n and sucursal_n:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (matriz, sucursal, segmento, tarifa, dupla, telefono, contacto, limite_credito_dias, limite_credito_dolares, ultimo_pedido)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (matriz_n.upper(), sucursal_n.upper(), segmento_n, tarifa_n, dupla_n, telefono_n, contacto_n, int(cred_dias), cred_monto, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success("¡Matriz y sucursal agregadas exitosamente al sistema!")
                    st.rerun()
                else:
                    st.error("Por favor completa al menos la Empresa Matriz y la Sucursal.")

# ---------------------------------------------------------
# 3. EMBUDO DE VENTAS (SALES FUNNEL)
# ---------------------------------------------------------
elif menu == "🎯 Embudo de Ventas (Sales Funnel)":
    st.title("🎯 Embudo de Ventas y Seguimiento Comercial B2B")
    st.write("Gestiona las oportunidades comerciales desde la prospección de espacios en anaquel hasta el cierre del pedido.")

    conn = sqlite3.connect(DB_NAME)
    df_cli_list = pd.read_sql("SELECT DISTINCT matriz FROM clientes", conn)
    conn.close()
    lista_matrices_activas = df_cli_list["matriz"].tolist() if not df_cli_list.empty else ["BULLKING"]

    tab_f1, tab_f2 = st.tabs(["📊 Embudos Activos por Fases", "➕ Registrar Nueva Oportunidad en el Embudo"])

    with tab_f1:
        conn = sqlite3.connect(DB_NAME)
        df_funnel = pd.read_sql("SELECT * FROM embudo_ventas", conn)
        conn.close()

        if not df_funnel.empty:
            st.subheader("📋 Pipeline del Embudo Comercial")
            st.dataframe(df_funnel, use_container_width=True)

            st.markdown("---")
            st.subheader("🔄 Actualizar Fase de Oportunidad")
            sel_id = st.selectbox("Seleccione ID de Oportunidad:", df_funnel["id"].tolist())
            row_op = df_funnel[df_funnel["id"] == sel_id].iloc[0]

            nueva_etapa = st.selectbox(
                "Mover a Fase del Embudo:",
                ["1. Prospección / Lead", "2. Visita y Muestras", "3. Cotización Emitida", "4. Negociación y Crédito", "5. Cierre Ganado", "6. Cierre Perdido"],
                index=["1. Prospección / Lead", "2. Visita y Muestras", "3. Cotización Emitida", "4. Negociación y Crédito", "5. Cierre Ganado", "6. Cierre Perdido"].index(row_op["etapa_embudo"]) if row_op["etapa_embudo"] in ["1. Prospección / Lead", "2. Visita y Muestras", "3. Cotización Emitida", "4. Negociación y Crédito", "5. Cierre Ganado", "6. Cierre Perdido"] else 0
            )

            if st.button("💾 Actualizar Fase en el Embudo"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE embudo_ventas SET etapa_embudo = ?, fecha_actualizacion = ? WHERE id = ?", (nueva_etapa, str(date.today()), int(sel_id)))
                conn.commit()
                conn.close()
                st.success("¡Fase del embudo actualizada con éxito!")
                st.rerun()
        else:
            st.info("No hay oportunidades registradas en el embudo comercial.")

    with tab_f2:
        with st.form("form_nuevo_embudo"):
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                negocio_n = st.text_input("Nombre de la Oportunidad (Ej. Espacio anaquel manzanas Gala)")
                cliente_n = st.selectbox("Cliente Matriz", lista_matrices_activas)
                etapa_n = st.selectbox("Fase Inicial", ["1. Prospección / Lead", "2. Visita y Muestras", "3. Cotización Emitida", "4. Negociación y Crédito"])
            with c_e2:
                valor_n = st.number_input("Valor Estimado de Venta ($)", min_value=0.0, value=1500.0)
                prob_n = st.selectbox("Probabilidad de Cierre", ["Alta (80%)", "Media (50%)", "Baja (20%)"])
                resp_n = st.selectbox("Dupla Responsable", ["Dupla 1 (Oriente-Centro)", "Dupla 2 (Capital)", "Dupla 3 (Occidente)"])

            if st.form_submit_button("Agregar Oportunidad al Embudo"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO embudo_ventas (negocio, cliente, etapa_embudo, valor_estimado, probabilidad, responsable, fecha_actualizacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (negocio_n, cliente_n, etapa_n, valor_n, prob_n, resp_n, str(date.today())))
                conn.commit()
                conn.close()
                st.success("¡Oportunidad agregada al embudo de ventas con éxito!")
                st.rerun()

# ---------------------------------------------------------
# 4. DEPARTAMENTO DE VENTAS & COTIZADOR PRO (CON LOGO REAL)
# ---------------------------------------------------------
elif menu == "🛒 Ventas & Cotizador Pro (PDF/HTML)":
    st.title("🛒 Departamento de Ventas - Cotizador B2B de Alta Eficiencia")
    st.write("Generación rápida de cotizaciones seleccionando matriz y sucursal registrada.")

    conn = sqlite3.connect(DB_NAME)
    df_mat = pd.read_sql("SELECT * FROM matriz_precios", conn)
    df_cli_db = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()

    lista_matrices = df_cli_db["matriz"].unique().tolist() if not df_cli_db.empty else ["BULLKING"]

    c_v1, c_v2 = st.columns(2)
    with c_v1:
        cli_sel = st.selectbox("Empresa Matriz", lista_matrices)
        sucursales_disponibles = df_cli_db[df_cli_db["matriz"] == cli_sel]["sucursal"].tolist() if not df_cli_db.empty else ["Principal"]
        suc_sel = st.selectbox("Sucursal Específica", sucursales_disponibles)
    with c_v2:
        asesor_sel = st.selectbox("Asesor / Dupla Comercial", ["Dupla 1 (Oriente-Centro)", "Dupla 2 (Capital)", "Dupla 3 (Occidente)"])
        vig_sel = st.date_input("Validez de la Oferta:", value=date.today() + pd.Timedelta(days=7))

    cli_info = df_cli_db[(df_cli_db["matriz"] == cli_sel) & (df_cli_db["sucursal"] == suc_sel)]
    if not cli_info.empty:
        l_cred = cli_info.iloc[0]["limite_credito_dolares"]
        l_dias = cli_info.iloc[0]["limite_credito_dias"]
        st.info(f"💳 **Límite de Crédito ({cli_sel} - {suc_sel}):** ${l_cred:,.2f} USD | **Plazo Acordado:** {l_dias} días")

    st.markdown("---")
    st.subheader("📋 Modifique Precios por Caja (El Precio por KG y el Subtotal se recalculan automáticamente):")

    if not df_mat.empty:
        df_editor_v = df_mat[["codigo", "barra", "descripcion", "empaque_kg", "costo_caja", "precio_caja", "precio_kg"]].copy()
        df_editor_v.columns = ["CÓDIGO", "BARRA", "DESCRIPCIÓN", "EMPAQUE/KG", "COSTO CAJA ($)", "PRECIO CAJA ($)", "PRECIO POR KG ($)"]

        df_editado_venta = st.data_editor(df_editor_v, use_container_width=True, key="cotizador_sucursal_dinamica")

        df_editado_venta["PRECIO POR KG ($)"] = df_editado_venta.apply(
            lambda row: round(row["PRECIO CAJA ($)"] / row["EMPAQUE/KG"], 2) if row["EMPAQUE/KG"] > 0 else 0.0, axis=1
        )

        st.info("💡 **Automatización Activa:** Modifique el Precio por Caja para ver en vivo la actualización del Precio por Kilogramo.")

        if st.button("💾 Procesar Pedido y Guardar Cotización"):
            det_json = json.dumps(df_editado_venta.to_dict(orient="records"))
            monto_aprox = df_editado_venta["PRECIO CAJA ($)"].sum()
            costo_aprox = df_editado_venta["COSTO CAJA ($)"].sum()
            ganancia_aprox = monto_aprox - costo_aprox

            nro_p = f"PED-{datetime.now().strftime('%Y%m%d%H%M')}"

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pedidos (nro_pedido, cliente, sucursal, atendido_por, fecha_pedido, monto_total, costo_total, ganancia_estimada, estatus_despacho, zona_envio, transporte, detalle_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', 'Caracas Centro', 'Flota Interna', ?)
            """, (nro_p, cli_sel, suc_sel, asesor_sel, str(date.today()), monto_aprox, costo_aprox, ganancia_aprox, det_json))
            
            cursor.execute("UPDATE clientes SET ultimo_pedido = ? WHERE matriz = ? AND sucursal = ?", (str(date.today()), cli_sel, suc_sel))
            conn.commit()
            conn.close()

            st.success(f"¡Pedido {nro_p} procesado con éxito para {cli_sel} ({suc_sel})!")

    st.markdown("---")
    st.subheader("📄 Generar Formato Imprimible / Documento Oficial")
    if st.button("📥 Generar Documento HTML de Cotización"):
        # Enlace RAW del logo real subido a GitHub
        logo_url = "https://raw.githubusercontent.com/vcaro2824-del/FrumixCRM/main/IMG-20261016-WA0072~3.jpg"
        
        html_doc = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Cotización Oficial - Frumix C.A.</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 30px; color: #111; }}
                .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6B8E23; padding-bottom: 15px; align-items: center; }}
                .logo {{ max-height: 80px; width: auto; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; font-size: 12px; }}
                th {{ background-color: #f2f2f2; }}
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
                    <strong>Asesor:</strong> {asesor_sel}
                </div>
            </div>
            <h3>Cotización Comercial Oficial</h3>
            <table>
                <tr>
                    <th>Código</th>
                    <th>Descripción</th>
                    <th>Empaque (Kg)</th>
                    <th>Precio Caja ($)</th>
                    <th>Precio por KG ($)</th>
                </tr>
        """
        for _, r in df_editado_venta.iterrows():
            html_doc += f"<tr><td>{r['CÓDIGO']}</td><td>{r['DESCRIPCIÓN']}</td><td>{r['EMPAQUE/KG']}</td><td>${r['PRECIO CAJA ($)']:.2f}</td><td>${r['PRECIO POR KG ($)']:.2f}</td></tr>"
        html_doc += f"""
            </table>
            <br>
            <p><strong>Condiciones Comerciales:</strong> Sujeto a disponibilidad de inventario en cámaras de frío. Validez de oferta hasta {vig_sel}.</p>
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
# 5. DEPARTAMENTO DE COBRANZA & CxC
# ---------------------------------------------------------
elif menu == "💰 Departamento de Cobranza & CxC":
    st.title("💰 Departamento de Cobranza - Cuentas por Cobrar y Morosidad")
    st.write("Control exhaustivo de facturas, plazos de crédito, abonos y alertas automáticas de pago.")

    conn = sqlite3.connect(DB_NAME)
    df_cli_list = pd.read_sql("SELECT DISTINCT matriz FROM clientes", conn)
    conn.close()
    lista_matrices_cobro = df_cli_list["matriz"].tolist() if not df_cli_list.empty else ["BULLKING"]

    tab_c1, tab_c2, tab_c3 = st.tabs(["📋 Estado de Cuenta y Facturas", "➕ Registrar Factura / Crédito", "⚠️ Alertas Reales (Morosidad e Inactividad)"])

    with tab_c1:
        conn = sqlite3.connect(DB_NAME)
        df_cxc = pd.read_sql("SELECT * FROM cobranza", conn)
        conn.close()

        if not df_cxc.empty:
            st.dataframe(df_cxc, use_container_width=True)
            
            st.markdown("---")
            st.subheader("💵 Registrar Abono o Liquidación de Factura")
            fact_ids = df_cxc["id"].tolist()
            sel_fact = st.selectbox("Selecciona ID de Factura:", fact_ids)
            fact_row = df_cxc[df_cxc["id"] == sel_fact].iloc[0]
            
            st.info(f"Cliente: **{fact_row['cliente']}** | Factura: **{fact_row['nro_factura']}** | Total: **${fact_row['monto_factura']:,.2f}** | Abonado: **${fact_row['monto_pagado']:,.2f}**")
            
            monto_abono = st.number_input("Monto del Pago / Abono ($)", min_value=0.0, value=float(fact_row['monto_factura'] - fact_row['monto_pagado']))
            nuevo_estatus = st.selectbox("Estatus Actualizado:", ["Pendiente", "Parcial", "Pagado", "Vencido"])

            if st.button("💾 Actualizar Cobranza"):
                nuevo_pagado = fact_row['monto_pagado'] + monto_abono
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE cobranza SET monto_pagado = ?, estatus_pago = ? WHERE id = ?", (nuevo_pagado, nuevo_estatus, int(sel_fact)))
                conn.commit()
                conn.close()
                st.success("¡Cobranza actualizada con éxito!")
                st.rerun()
        else:
            st.info("No hay facturas registradas en el sistema de cobranza.")

    with tab_c2:
        with st.form("form_reg_cxc_sucursal"):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                nro_fac = st.text_input("Nro. de Factura (Ej. FAC-2026-001)", value="FAC-2026-")
                cli_fac = st.selectbox("Cliente Matriz", lista_matrices_cobro)
                monto_fac = st.number_input("Monto Total Facturado ($)", min_value=0.0, value=500.0)
            with c_f2:
                f_emi = st.date_input("Fecha de Emisión", value=date.today())
                dias_cred = st.number_input("Días de Crédito Otorgados", min_value=1, value=15)
                f_ven = date.today() + pd.Timedelta(days=int(dias_cred))
                st.write(f"Vencimiento Calculado: **{f_ven}**")

            if st.form_submit_button("Generar Factura en CxC"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cobranza (nro_factura, cliente, fecha_emision, fecha_vencimiento, monto_factura, monto_pagado, estatus_pago)
                    VALUES (?, ?, ?, ?, ?, 0.0, 'Pendiente')
                """, (nro_fac.upper(), cli_fac, str(f_emi), str(f_ven), monto_fac))
                conn.commit()
                conn.close()
                st.success("¡Factura cargada en cuentas por cobrar!")
                st.rerun()

    with tab_c3:
        st.subheader("🚨 Alertas Automáticas Reales (Morosidad y Ventas)")
        
        conn = sqlite3.connect(DB_NAME)
        df_cli_alert = pd.read_sql("SELECT * FROM clientes", conn)
        df_cxc_alert = pd.read_sql("SELECT * FROM cobranza", conn)
        conn.close()

        hoy_dt = date.today()

        if not df_cxc_alert.empty:
            df_cxc_alert["vence_dt"] = pd.to_datetime(df_cxc_alert["fecha_vencimiento"]).dt.date
            vencidas = df_cxc_alert[(df_cxc_alert["vence_dt"] < hoy_dt) & (df_cxc_alert["estatus_pago"] != "Pagado")]
            
            if not vencidas.empty:
                st.error(f"⚠️ ¡ATENCIÓN COBRANZA! Hay {len(vencidas)} facturas vencidas sin cancelar:")
                st.dataframe(vencidas[["nro_factura", "cliente", "fecha_vencimiento", "monto_factura", "monto_pagado"]], use_container_width=True)
            else:
                st.success("✅ No existen facturas vencidas en este momento.")

        st.markdown("---")
        dias_limite_inactividad = st.slider("Días límite sin pedidos para alerta comercial:", min_value=1, max_value=60, value=14)
        
        if not df_cli_alert.empty:
            inactivos_list = []
            for _, row in df_cli_alert.iterrows():
                if row["ultimo_pedido"]:
                    try:
                        f_u = datetime.strptime(row["ultimo_pedido"], "%Y-%m-%d").date()
                        dias_sin = (hoy_dt - f_u).days
                        if dias_sin > dias_limite_inactividad:
                            inactivos_list.append({
                                "Matriz": row["matriz"],
                                "Sucursal": row["sucursal"],
                                "Contacto": row["contacto"],
                                "Teléfono": row["telefono"],
                                "Días Sin Comprar": dias_sin
                            })
                    except:
                        pass
            if inactivos_list:
                st.warning(f"⚠️ ¡ALERTA DE VENTAS! {len(inactivos_list)} sucursales superan los {dias_limite_inactividad} días sin pedidos:")
                st.dataframe(pd.DataFrame(inactivos_list), use_container_width=True)
            else:
                st.success(f"✅ Todos los clientes han comprado dentro del margen de {dias_limite_inactividad} días.")

# ---------------------------------------------------------
# 6. LOGÍSTICA, DESPACHO & RUTAS
# ---------------------------------------------------------
elif menu == "🚚 Logística, Despacho & Rutas":
    st.title("🚚 Logística, Despacho y Trazabilidad de Cámaras de Frío")
    st.write("Control de inventario físico por lotes, asignación de transporte y seguimiento de rutas.")

    tab_d1, tab_d2 = st.tabs(["📦 Inventario Actual por Lotes", "🚚 Asignación de Rutas y Despachos"])

    with tab_d1:
        conn = sqlite3.connect(DB_NAME)
        df_inv = pd.read_sql("SELECT * FROM inventario", conn)
        df_mer = pd.read_sql("SELECT lote_id, SUM(cantidad_perdida) as perdida FROM mermas GROUP BY lote_id", conn)
        conn.close()

        if not df_inv.empty:
            if not df_mer.empty:
                df_inv = df_inv.merge(df_mer, left_on="id", right_on="lote_id", how="left")
                df_inv["perdida"] = df_inv["perdida"].fillna(0)
            else:
                df_inv["perdida"] = 0

            df_inv["stock_real"] = df_inv["stock_inicial"] - df_inv["perdida"]
            df_inv["valor_inventario"] = df_inv["stock_real"] * df_inv["costo_unitario_caja"]

            st.dataframe(df_inv[["id", "lote", "producto", "stock_inicial", "perdida", "stock_real", "costo_unitario_caja", "valor_inventario", "fecha_ingreso"]], use_container_width=True)
        else:
            st.info("No hay inventario registrado en cámaras.")

    with tab_d2:
        conn = sqlite3.connect(DB_NAME)
        df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
        conn.close()

        if not df_peds.empty:
            st.subheader("📋 Asignación de Camión y Ruta de Despacho")
            st.dataframe(df_peds[["id", "nro_pedido", "cliente", "sucursal", "monto_total", "estatus_despacho"]], use_container_width=True)

            sel_p_id = st.selectbox("Seleccione ID de Pedido:", df_peds["id"].tolist())
            nuevo_estatus_desp = st.selectbox("Estatus del Despacho:", ["Pendiente", "En Ruta de Entrega", "Entregado Conforme", "Incidencia en Destino"])

            if st.button("💾 Actualizar Ruta de Despacho"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE pedidos SET estatus_despacho = ? WHERE id = ?", (nuevo_estatus_desp, int(sel_p_id)))
                conn.commit()
                conn.close()
                st.success("¡Estatus de despacho actualizado!")
                st.rerun()
        else:
            st.info("No hay pedidos registrados para despachar.")

# ---------------------------------------------------------
# 7. MATRIZ DINÁMICA DE PRECIOS (CAJA A KG)
# ---------------------------------------------------------
elif menu == "💲 Matriz Dinámica de Precios (Caja a KG)":
    st.title("💲 Matriz de Precios - Conversión Automática Caja a Kilogramo")
    st.write("Modifique costo y precio por caja; el sistema calcula de forma instantánea el precio por kilo y los márgenes de ganancia.")

    conn = sqlite3.connect(DB_NAME)
    df_m = pd.read_sql("SELECT * FROM matriz_precios", conn)
    conn.close()

    if not df_m.empty:
        df_m_edit = df_m[["id", "codigo", "descripcion", "empaque_kg", "costo_caja", "precio_caja"]].copy()
        df_m_edit.columns = ["ID", "CÓDIGO", "DESCRIPCIÓN", "EMPAQUE/KG", "COSTO CAJA ($)", "PRECIO CAJA ($)"]

        df_resultado = st.data_editor(df_m_edit, use_container_width=True, key="matriz_sucursal")

        df_resultado["PRECIO POR KG ($)"] = df_resultado.apply(
            lambda r: round(r["PRECIO CAJA ($)"] / r["EMPAQUE/KG"], 2) if r["EMPAQUE/KG"] > 0 else 0.0, axis=1
        )
        df_resultado["MARGEN BRUTO (%)"] = df_resultado.apply(
            lambda r: round(((r["PRECIO CAJA ($)"] - r["COSTO CAJA ($)"]) / r["PRECIO CAJA ($)"] * 100), 1) if r["PRECIO CAJA ($)"] > 0 else 0.0, axis=1
        )

        st.markdown("---")
        st.subheader("📊 Vista Previa de Cálculos Automáticos de Rentabilidad")
        st.dataframe(df_resultado, use_container_width=True)

        if st.button("💾 Guardar Cambios en la Matriz Base"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            for _, row in df_resultado.iterrows():
                cursor.execute("""
                    UPDATE matriz_precios 
                    SET costo_caja = ?, precio_caja = ?, precio_kg = ?, margen_pct = ?
                    WHERE id = ?
                """, (row["COSTO CAJA ($)"], row["PRECIO CAJA ($)"], row["PRECIO POR KG ($)"], row["MARGEN BRUTO (%)"], int(row["ID"])))
            conn.commit()
            conn.close()
            st.success("¡Matriz de precios actualizada correctamente!")
            st.rerun()

# ---------------------------------------------------------
# 8. CONTROL DE MERMAS & PÉRDIDAS
# ---------------------------------------------------------
elif menu == "🗑️ Control de Mermas & Pérdidas":
    st.title("🗑️ Control de Mermas y Pérdidas Financieras Directas")
    st.write("Registro de mermas asociadas a lotes para el cálculo del impacto en la utilidad neta.")

    conn = sqlite3.connect(DB_NAME)
    df_inv_m = pd.read_sql("SELECT * FROM inventario", conn)
    conn.close()

    if not df_inv_m.empty:
        with st.form("form_merma_sucursal"):
            lote_opts = [f"ID: {r['id']} | Lote: {r['lote']} - {r['producto']} (Costo Caja: ${r['costo_unitario_caja']})" for _, r in df_inv_m.iterrows()]
            sel_l_merma = st.selectbox("Seleccione el Lote Afectado:", lote_opts)
            cant_p = st.number_input("Cajas Perdidas por Merma", min_value=0.5, value=1.0)
            motivo_m = st.selectbox("Motivo", ["Maduración excesiva", "Golpes / Daño físico", "Descomposición", "Transporte", "Otro"])
            fecha_m = st.date_input("Fecha del Registro", value=date.today())

            if st.form_submit_button("Procesar Merma y Calcular Pérdida"):
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

                st.success(f"¡Merma procesada! Pérdida monetaria registrada: ${perdida_dinero:,.2f}")
                st.rerun()
    else:
        st.warning("No hay lotes disponibles en inventario para registrar mermas.")

# ---------------------------------------------------------
# 9. REGISTRO Y ESTATUS DE PEDIDOS
# ---------------------------------------------------------
elif menu == "📦 Registro y Estatus de Pedidos":
    st.title("📦 Historial General de Pedidos y Estatus B2B")
    
    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_peds.empty:
        st.dataframe(df_peds, use_container_width=True)
    else:
        st.info("No hay pedidos registrados todavía.")
