import datetime
import json
import sqlite3
import pandas as pd
import streamlit as st
import threading
import time
import urllib.request

st.set_page_config(
    page_title="Frumix B2B - Sistema Integral Gerencial y Operativo",
    page_icon="🍓",
    layout="wide",
)

# ---------------------------------------------------------
# SISTEMA KEEP-ALIVE BLINDADO (EVITA CIERRES POR INACTIVIDAD)
# ---------------------------------------------------------
def keep_alive():
    while True:
        try:
            urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=5)
        except:
            pass
        time.sleep(120) # Consulta cada 2 minutos para mantener activo el servidor

threading.Thread(target=keep_alive, daemon=True).start()

# ---------------------------------------------------------
# CONEXIÓN Y PERSISTENCIA PERMANENTE CON SQLITE BLINDADA
# ---------------------------------------------------------
DB_NAME = "frumix_b2b.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabla de Clientes General
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_padre TEXT,
            matriz TEXT,
            id_suc TEXT,
            sucursal TEXT,
            segmento TEXT,
            tarifa TEXT,
            dupla TEXT,
            calibre_pref TEXT,
            telefono TEXT,
            contacto TEXT,
            ultimo_pedido TEXT
        )
    """)
    
    # 2. Tabla de Matriz de Precios / Catálogo Base
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matriz_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            barra TEXT,
            descripcion TEXT,
            empaque_kg REAL,
            costo_anterior REAL,
            dcto1 REAL,
            dcto2 REAL,
            costo_nuevo REAL,
            precio_base REAL
        )
    """)
    
    # 3. Tabla de Cotizaciones Emitidas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            sucursal TEXT,
            vigencia TEXT,
            pago TEXT,
            detalle_json TEXT,
            fecha_emision TEXT
        )
    """)
    
    # 4. Tabla de Pedidos Despachados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_pedido TEXT,
            empresa_matriz TEXT,
            sucursal TEXT,
            atendido_por TEXT,
            fecha_pedido TEXT,
            monto_total REAL,
            detalle_pedido TEXT
        )
    """)

    # 5. Tabla de Pipeline
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            negocio TEXT,
            estado TEXT,
            valor REAL
        )
    """)

    # 6. Tabla de Inventario y Lotes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote TEXT,
            producto TEXT,
            stock_inicial INTEGER,
            costo REAL,
            fecha_ingreso TEXT
        )
    """)

    # 7. Tabla de Mermas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mermas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            producto TEXT,
            cantidad_perdida INTEGER,
            perdida_monetaria REAL,
            motivo TEXT,
            fecha_merma TEXT
        )
    """)

    # 8. Tabla de Comisiones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asesor TEXT,
            total REAL
        )
    """)

    conn.commit()
    
    # Comprobación de seguridad para columnas de matriz_precios
    cursor.execute("PRAGMA table_info(matriz_precios)")
    cols_m = [col[1] for col in cursor.fetchall()]
    if "codigo" not in cols_m:
        cursor.execute("ALTER TABLE matriz_precios ADD COLUMN codigo TEXT DEFAULT ''")
    if "dcto1" not in cols_m:
        cursor.execute("ALTER TABLE matriz_precios ADD COLUMN dcto1 REAL DEFAULT 0.0")
    if "dcto2" not in cols_m:
        cursor.execute("ALTER TABLE matriz_precios ADD COLUMN dcto2 REAL DEFAULT 0.0")
    if "costo_nuevo" not in cols_m:
        cursor.execute("ALTER TABLE matriz_precios ADD COLUMN costo_nuevo REAL DEFAULT 0.0")

    # Comprobación de seguridad para columnas de mermas
    cursor.execute("PRAGMA table_info(mermas)")
    cols_mer = [col[1] for col in cursor.fetchall()]
    if "lote_id" not in cols_mer:
        cursor.execute("ALTER TABLE mermas ADD COLUMN lote_id INTEGER DEFAULT 1")
    if "perdida_monetaria" not in cols_mer:
        cursor.execute("ALTER TABLE mermas ADD COLUMN perdida_monetaria REAL DEFAULT 0.0")
    if "motivo" not in cols_mer:
        cursor.execute("ALTER TABLE mermas ADD COLUMN motivo TEXT DEFAULT ''")
    if "fecha_merma" not in cols_mer:
        cursor.execute("ALTER TABLE mermas ADD COLUMN fecha_merma TEXT DEFAULT ''")

    conn.commit()

    # Cargar catálogo inicial de frutas si está vacío
    cursor.execute("SELECT COUNT(*) FROM matriz_precios")
    if cursor.fetchone()[0] == 0:
        catalogo_inicial = [
            ("", "759101", "MANZANA GALA", 19.0, 68.0, 0.0, 0.0, 68.0, 3.58),
            ("", "759102", "MANZANA ROJA", 19.0, 80.0, 0.0, 0.0, 80.0, 4.21),
            ("", "759103", "MANZANA VERDE", 19.0, 80.0, 0.0, 0.0, 80.0, 4.44),
            ("", "759104", "MANZANA AMARILLA (americana)", 18.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759105", "MANZANA GALA GRANEL", 23.0, 55.0, 0.0, 0.0, 59.2, 3.20),
            ("", "759106", "MANZANA PINK LADY", 18.5, 58.0, 0.0, 0.0, 60.0, 3.33),
            ("", "759201", "PERA VERDE", 18.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759202", "PERA COSCIA", 10.0, 0.0, 0.0, 0.0, 30.0, 3.33),
            ("", "759203", "PERA FORELLE EN BANDEJA", 9.0, 80.0, 0.0, 0.0, 80.0, 8.29),
            ("", "759301", "UVA RED GLOBE", 8.2, 95.0, 0.0, 0.0, 78.0, 9.51),
            ("", "759302", "UVA VERDE S/SEMILLA", 8.2, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759303", "UVA NEGRA S/SEMILLA", 7.3, 0.0, 0.0, 0.0, 70.0, 7.78),
            ("", "759401", "CIRUELA IMPORTADA", 9.0, 0.0, 0.0, 0.0, 68.0, 6.80),
            ("", "759402", "KIWI VERDE", 10.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759403", "KIWI AMARILLO", 9.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759501", "GRANADA", 3.8, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759502", "CEREZA", 2.5, 4.5, 0.0, 0.0, 4.5, 36.00),
            ("", "759503", "ARANDANOS", 0.125, 75.0, 0.0, 0.0, 70.0, 4.67),
            ("", "759504", "NARANJAS IMPORTADAS", 15.0, 40.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759505", "TANGELO", 9.5, 49.0, 0.0, 0.0, 55.0, 5.79),
            ("", "759506", "MANDARINAS IMPORTADAS", 9.5, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759601", "POMELO", 14.5, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759602", "PITAHAYA ROJA", 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759603", "PITAHAYA AMARILLA", 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759604", "LIMON AMARILLO (importado)", 16.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759605", "CASTANA", 5.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("", "759606", "NECTARINA", 9.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ]
        cursor.executemany("""
            INSERT INTO matriz_precios (codigo, barra, descripcion, empaque_kg, costo_anterior, dcto1, dcto2, costo_nuevo, precio_base)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, catalogo_inicial)
        conn.commit()

    conn.close()

init_db()

EMPRESA = {
    "nombre": "FRUMIX C.A.",
    "rif": "J-40985632-1",
    "direccion": "Centro de Distribución Principal, Área Metropolitana de Caracas",
    "telefono": "+58 412-FRUMIX1",
    "email": "ventas@frumixb2b.com",
    "bancos": "Banesco / Mercantil / Pago Móvil / Zelle (Pagos corporativos)",
}

CLIENTES_CLAVE_ACTUALIZACION = [
    "BULLKING",
    "CENTRAL MADERENSE",
    "SUPERMERCADO EUROS",
    "LADIMIR",
    "SUPERMERCADOS LUXOR",
    "MERCATO",
    "PLAN SUAREZ",
    "RIO CARACAS",
    "RIO MARGARITA",
    "RIO VIDA",
    "SIGO",
    "TIERRA SANTA",
    "SUPER 900",
    "TODO HOGAR",
    "VIVA",
    "WILMER",
    "PARAMO COLD 2024"
]

# ---------------------------------------------------------
# MENÚ LATERAL
# ---------------------------------------------------------
st.sidebar.markdown(f"### 🍓 PROVEEDOR: {EMPRESA['nombre']}")
st.sidebar.markdown(f"**RIF:** {EMPRESA['rif']}")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Menú Integral Frumix B2B",
    [
        "📊 Dashboard Gerencial",
        "📋 Cartera de Clientes (Key Accounts)",
        "💲 Catálogo Base de Frutas y Pesos",
        "🧾 Formato de Actualización de Precios",
        "📦 Registro y Conteo de Pedidos",
        "🛒 Historial y Pipeline de Ventas",
        "📦 Control de Inventario y Lotes",
        "🗑️ Muestreo y Control de Mermas",
        "💰 Liquidación de Comisiones",
        "📅 Rutina Semanal Comercial",
    ],
)

# ---------------------------------------------------------
# 1. DASHBOARD GERENCIAL
# ---------------------------------------------------------
if menu == "📊 Dashboard Gerencial":
    st.title("📊 Dashboard Gerencial y Métricas Permanentes")
    
    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql("SELECT * FROM clientes", conn)
    df_inv = pd.read_sql("SELECT * FROM inventario", conn)
    df_mer = pd.read_sql("SELECT * FROM mermas", conn)
    df_com = pd.read_sql("SELECT * FROM comisiones", conn)
    df_pedidos = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cuentas Clave Activas", len(df_cli))
    with col2:
        val_inv = (df_inv["stock_inicial"] * df_inv["costo"]).sum() if not df_inv.empty else 0.0
        st.metric("Valor Inventario en Frío", f"${val_inv:,.2f}")
    with col3:
        val_mer = df_mer["perdida_monetaria"].sum() if not df_mer.empty else 0.0
        st.metric("Pérdida Total por Mermas", f"${val_mer:,.2f}")
    with col4:
        total_pedidos_count = len(df_pedidos)
        st.metric("Pedidos Totales Registrados", total_pedidos_count)

    st.markdown("---")
    st.subheader("⚠️ Alertas de Clientes Inactivos (Configuración de Días Límite)")
    dias_limite = st.slider("Días límite sin pedidos para alerta:", min_value=1, max_value=60, value=15)

    if not df_cli.empty:
        hoy = datetime.date.today()
        inactivos = []
        for _, row in df_cli.iterrows():
            if row["ultimo_pedido"]:
                try:
                    f_ult = datetime.datetime.strptime(row["ultimo_pedido"], "%Y-%m-%d").date()
                    dias_sin_comprar = (hoy - f_ult).days
                    if dias_sin_comprar > dias_limite:
                        inactivos.append({
                            "Matriz": row["matriz"],
                            "Sucursal": row["sucursal"],
                            "Contacto": row["contacto"],
                            "Teléfono": row["telefono"],
                            "Días Sin Comprar": dias_sin_comprar
                        })
                except:
                    pass
        if inactivos:
            st.warning(f"¡Atención! Hay {len(inactivos)} sucursales superando los {dias_limite} días sin comprar:")
            st.dataframe(pd.DataFrame(inactivos), use_container_width=True)
        else:
            st.success(f"¡Excelente! Ninguna sucursal supera los {dias_limite} días de inactividad.")
    else:
        st.info("No hay clientes registrados en la base de datos.")

# ---------------------------------------------------------
# 2. CARTERA DE CLIENTES GENERAL
# ---------------------------------------------------------
elif menu == "📋 Cartera de Clientes (Key Accounts)":
    st.title("📋 Gestión de Cuentas Clave y Sucursales (Permanente)")

    tab_nuevo, tab_editar = st.tabs(["➕ Registrar Sucursal / Matriz", "✏️ Consultar y Gestionar por Matriz"])

    with tab_nuevo:
        with st.form("form_cliente_db"):
            c1, c2 = st.columns(2)
            with c1:
                id_padre = st.text_input("ID Cuenta Padre", value="KA-001")
                matriz = st.text_input("Empresa Matriz")
                id_suc = st.text_input("ID Sucursal", value="SUC-01")
                sucursal = st.text_input("Nombre de Sucursal y Estado")
                segmento = st.selectbox("Segmento B2B", ["Supermercados", "Frutería / Minimarket", "HORECA (Hotel/Restaurante)"])
            with c2:
                tarifa = st.selectbox("Tarifa Asignada", ["Tarifa A (Mayorista)", "Tarifa B (Regular)", "Tarifa C (Preferencial)"])
                dupla = st.selectbox("Dupla Comercial", ["Dupla 1 (Oriente-Centro)", "Dupla 2 (Capital)", "Dupla 3 (Occidente)"])
                calibre_pref = st.text_input("Calibre Preferido", value="Calibre 80/82")
                telefono = st.text_input("Teléfono / WhatsApp de Sucursal")
                contacto = st.text_input("Persona de Contacto")
                f_ultimo = st.date_input("Fecha Último Pedido", value=datetime.date.today())

            btn_save = st.form_submit_button("Guardar Sucursal Permanentemente")
            if btn_save:
                if matriz and sucursal:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (id_padre, matriz, id_suc, sucursal, segmento, tarifa, dupla, calibre_pref, telefono, contacto, ultimo_pedido)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (id_padre, matriz.upper(), id_suc, sucursal, segmento, tarifa, dupla, calibre_pref, telefono, contacto, str(f_ultimo)))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Sucursal para '{matriz.upper()}' guardada con éxito!")
                    st.rerun()
                else:
                    st.warning("Completa al menos la Matriz y el Nombre de la Sucursal.")

    with tab_editar:
        conn = sqlite3.connect(DB_NAME)
        df_cli = pd.read_sql("SELECT * FROM clientes", conn)
        conn.close()

        if not df_cli.empty:
            matrices_unicas = sorted(df_cli["matriz"].unique())
            matriz_sel = st.selectbox("📁 Filtrar por Empresa Matriz:", matrices_unicas)

            df_filtrado = df_cli[df_cli["matriz"] == matriz_sel]
            sucursales_de_matriz = [f"{row['sucursal']} (ID: {row['id_suc']})" for _, row in df_filtrado.iterrows()]
            
            suc_sel = st.selectbox("🏢 Seleccionar Sucursal Específica:", sucursales_de_matriz)
            idx_real = sucursales_de_matriz.index(suc_sel)
            cli_row = df_filtrado.iloc[idx_real]

            with st.form("form_edit_cli"):
                st.write(f"Editando sucursal: **{cli_row['sucursal']}** de **{cli_row['matriz']}**")
                n_cont = st.text_input("Actualizar Contacto", value=cli_row["contacto"])
                n_tel = st.text_input("Actualizar Teléfono", value=cli_row["telefono"])
                n_fec = st.date_input("Actualizar Último Pedido", value=datetime.datetime.strptime(cli_row["ultimo_pedido"], "%Y-%m-%d").date() if cli_row["ultimo_pedido"] else datetime.date.today())

                col1, col2 = st.columns(2)
                with col1:
                    b_upd = st.form_submit_button("💾 Actualizar Sucursal")
                with col2:
                    b_del = st.form_submit_button("🗑️ Eliminar Sucursal")

                if b_upd:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE clientes SET contacto=?, telefono=?, ultimo_pedido=? WHERE id=?", (n_cont, n_tel, str(n_fec), int(cli_row["id"])))
                    conn.commit()
                    conn.close()
                    st.success("¡Sucursal actualizada con éxito!")
                    st.rerun()
                
                if b_del:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM clientes WHERE id=?", (int(cli_row["id"]),))
                    conn.commit()
                    conn.close()
                    st.success("¡Sucursal eliminada!")
                    st.rerun()
        else:
            st.info("No hay clientes registrados.")

    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()
    if not df_cli.empty:
        st.markdown("---")
        st.subheader("📋 Listado General de Clientes Agrupados por Matriz")
        st.dataframe(df_cli, use_container_width=True)

# ---------------------------------------------------------
# 3. CATÁLOGO BASE DE FRUTAS Y PESOS
# ---------------------------------------------------------
elif menu == "💲 Catálogo Base de Frutas y Pesos":
    st.title("💲 Catálogo Base de Frutas y Pesos (Permanente)")

    tab_v, tab_a = st.tabs(["📋 Ver Catálogo Base", "➕ Agregar Fruta"])

    with tab_v:
        conn = sqlite3.connect(DB_NAME)
        df_m = pd.read_sql("SELECT * FROM matriz_precios", conn)
        conn.close()
        st.dataframe(df_m, use_container_width=True)

    with tab_a:
        with st.form("form_matriz_db"):
            cod = st.text_input("Código Interno", value="")
            b = st.text_input("Código de Barra / SKU", value="759900")
            d = st.text_input("Descripción de la Fruta")
            e = st.number_input("Empaque / KG", min_value=0.001, value=10.0, step=0.1)
            c = st.number_input("Costo Anterior ($)", min_value=0.0, value=30.0, step=0.1)
            p = st.number_input("Precio Base KG ($)", min_value=0.0, value=3.0, step=0.01)

            if st.form_submit_button("Guardar en Catálogo Base"):
                if d:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO matriz_precios (codigo, barra, descripcion, empaque_kg, costo_anterior, dcto1, dcto2, costo_nuevo, precio_base)
                        VALUES (?, ?, ?, ?, ?, 0.0, 0.0, ?, ?)
                    """, (cod, b, d.upper(), e, c, c, p))
                    conn.commit()
                    conn.close()
                    st.success("¡Fruta agregada permanentemente!")
                    st.rerun()
                else:
                    st.warning("Ingrese la descripción.")

# ---------------------------------------------------------
# 4. FORMATO DE ACTUALIZACIÓN DE PRECIOS
# ---------------------------------------------------------
elif menu == "🧾 Formato de Actualización de Precios":
    st.title("📄 EMISIÓN DE LISTA DE PRECIOS")
    st.write("Selecciona el cliente de la lista oficial, ajusta los precios semanales y emite tu formato con diseño oficial integrado.")

    conn = sqlite3.connect(DB_NAME)
    df_matriz = pd.read_sql("SELECT * FROM matriz_precios", conn)
    conn.close()

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        cliente_elegido = st.selectbox("🏢 EMPRESA CLIENTE (LISTA OFICIAL):", CLIENTES_CLAVE_ACTUALIZACION)
        sucursal_elegida = st.text_input("📍 Sucursal / Ubicación Destino", value="Principal")
        cliente_final = f"{cliente_elegido} - {sucursal_elegida}"

    with col_top2:
        fecha_emision_val = st.date_input("📅 Fecha de Emisión:", value=datetime.date.today())
        fecha_vigencia = st.date_input("📅 Vigente a partir de:", value=datetime.date.today())
        fecha_vencimiento = st.date_input("📅 Vence el:", value=datetime.date.today() + datetime.timedelta(days=10))
        st.info(f"**PROVEEDOR:** {EMPRESA['nombre']} | **RIF:** {EMPRESA['rif']}")

    st.markdown("---")
    st.subheader("📋 Matriz Semanal de Frutas (Modifica directamente los valores):")

    if not df_matriz.empty:
        df_cotiza_editor = df_matriz[["codigo", "barra", "descripcion", "empaque_kg", "costo_anterior", "dcto1", "dcto2", "costo_nuevo", "precio_base"]].copy()
        df_cotiza_editor.columns = ["CODIGO", "BARRA", "DESCRIPCIÓN", "EMPAQUE/KG", "COSTO ANTERIOR", "DCTO 1", "DCTO 2", "COSTO NUEVO", "PRECIO POR KG"]

        df_editado = st.data_editor(
            df_cotiza_editor,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_matriz_semanal"
        )

        if st.button("💾 EMITIR Y GUARDAR LISTA DE PRECIOS"):
            det_json = json.dumps(df_editado.to_dict(orient="records"))
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cotizaciones (cliente, sucursal, vigencia, pago, detalle_json, fecha_emision)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cliente_final, sucursal_elegida, str(fecha_vigencia), f"Emisión:{fecha_emision_val}|Vence:{fecha_vencimiento}", det_json, str(datetime.date.today())))
            conn.commit()
            conn.close()
            st.success(f"¡Lista de precios emitida exitosamente para {cliente_final}!")
            st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_cot = pd.read_sql("SELECT * FROM cotizaciones ORDER BY id DESC", conn)
    conn.close()

    if not df_cot.empty:
        st.markdown("---")
        st.subheader("📄 Historial de Listas Emitidas (Modificar o Eliminar)")
        for i, row in df_cot.iterrows():
            with st.expander(f"LISTA DE PRECIOS #{row['id']} - {row['cliente']} (Vigencia: {row['vigencia']})"):
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    if st.button(f"🗑️ Eliminar Lista #{row['id']}", key=f"del_cot_{row['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM cotizaciones WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.success(f"¡Lista #{row['id']} eliminada con éxito!")
                        st.rerun()

                st.markdown(f"**PROVEEDOR:** {EMPRESA['nombre']} | **CLIENTE:** {row['cliente']} | **VIGENCIA:** {row['vigencia']}")
                items = json.loads(row["detalle_json"])
                df_items = pd.DataFrame(items)
                
                df_modificado = st.data_editor(
                    df_items, 
                    use_container_width=True, 
                    key=f"edit_cot_table_{row['id']}"
                )
                
                if st.button(f"💾 Guardar Cambios de la Lista #{row['id']}", key=f"save_mod_{row['id']}"):
                    nuevo_json = json.dumps(df_modificado.to_dict(orient="records"))
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE cotizaciones SET detalle_json = ? WHERE id = ?", (nuevo_json, row['id']))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Lista #{row['id']} actualizada correctamente!")
                    st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

                # HTML del documento oficial con Logo Frumix tricolor idéntico al solicitado
                html_contenido = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Lista de Precios - {row['cliente']}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; color: #000; }}
                        .top-banner {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                        .logo-box {{ display: flex; align-items: center; gap: 10px; }}
                        .logo-circle {{ display: flex; align-items: center; justify-content: center; width: 45px; height: 45px; border-radius: 50%; border: 2px solid #333; font-size: 20px; font-weight: bold; background: #fff; }}
                        .logo-text {{ font-size: 24px; font-weight: bold; font-family: 'Arial Black', sans-serif; color: #000; letter-spacing: -1px; }}
                        .intro-text {{ font-size: 13px; line-height: 1.4; margin-bottom: 15px; }}
                        .meta-table {{ width: 100%; margin-bottom: 15px; font-size: 13px; border-collapse: collapse; }}
                        .meta-table td {{ border: 1px solid #333; padding: 5px 8px; }}
                        .meta-title {{ font-weight: bold; background-color: #f2f2f2; width: 25%; }}
                        table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                        th, td {{ border: 1px solid #333; padding: 6px 8px; text-align: center; font-size: 12px; }}
                        th {{ background-color: #f2f2f2; }}
                        .desc {{ text-align: left; }}
                        .firmas {{ display: flex; justify-content: space-between; margin-top: 50px; }}
                        .firma-box {{ text-align: center; width: 40%; border-top: 1px solid #000; padding-top: 5px; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="top-banner">
                        <div class="logo-box">
                            <div class="logo-circle">
                                <span style="color:#6B8E23;">🟢</span><span style="color:#B22222;">🔴</span><span style="color:#4B0082;">🟣</span>
                            </div>
                            <div class="logo-text">Frumix</div>
                        </div>
                        <div style="text-align: right; font-size: 13px;">
                            <strong>{row['vigencia']}</strong>
                        </div>
                    </div>

                    <div class="intro-text">
                        A continuación encontrará nuestra lista de precios.<br>
                        Nuestra alianza con los mejores productores de frutas frescas a nivel mundial y el correcto manejo del producto garantiza la calidad y buen servicio que nos caracteriza.
                    </div>

                    <table class="meta-table">
                        <tr>
                            <td class="meta-title">COTIZACIÓN N°</td>
                            <td><strong>{row['id']}</strong></td>
                        </tr>
                        <tr>
                            <td class="meta-title">Cliente / Sucursal</td>
                            <td>{row['cliente']}</td>
                        </tr>
                        <tr>
                            <td class="meta-title">Fecha de emisión</td>
                            <td>{row.get('fecha_emision', '16/10/2026')}</td>
                        </tr>
                        <tr>
                            <td class="meta-title">Vigente a partir de:</td>
                            <td>{row['vigencia']}</td>
                        </tr>
                        <tr>
                            <td class="meta-title">Vence el:</td>
                            <td>{str(datetime.date.today() + datetime.timedelta(days=10))}</td>
                        </tr>
                    </table>
                    
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>CÓDIGO</th>
                                <th>BARRA</th>
                                <th class="desc">DESCRIPCIÓN</th>
                                <th>EMPAQUE/KG</th>
                                <th>COSTO ANTERIOR</th>
                                <th>DCTO 1</th>
                                <th>DCTO 2</th>
                                <th>COSTO NUEVO</th>
                                <th>PRECIO POR KG</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for it in df_modificado.to_dict(orient="records"):
                    html_contenido += f"""
                            <tr>
                                <td>{it.get('CODIGO', '')}</td>
                                <td>{it.get('BARRA', '')}</td>
                                <td class="desc">{it.get('DESCRIPCIÓN', '')}</td>
                                <td>{it.get('EMPAQUE/KG', '')}</td>
                                <td>{it.get('COSTO ANTERIOR', '')}</td>
                                <td>{it.get('DCTO 1', '')}</td>
                                <td>{it.get('DCTO 2', '')}</td>
                                <td>{it.get('COSTO NUEVO', '')}</td>
                                <td>{it.get('PRECIO POR KG', '')}</td>
                            </tr>
                    """
                html_contenido += f"""
                        </tbody>
                    </table>
                    
                    <div class="firmas">
                        <div class="firma-box">
                            <strong>FIRMA DE COMPRADOR</strong>
                        </div>
                        <div class="firma-box">
                            <strong>FIRMA DE APROBACIÓN</strong>
                        </div>
                    </div>
                </body>
                </html>
                """

                st.download_button(
                    label=f"📥 Descargar Lista de Precios Oficial #{row['id']} ({row['cliente']}) en HTML/Imprimible",
                    data=html_contenido,
                    file_name=f"Lista_Precios_{row['cliente'].replace(' ', '_')}_{row['vigencia']}.html",
                    mime="text/html",
                    key=f"dl_html_{row['id']}"
                )

# ---------------------------------------------------------
# 5. REGISTRO Y CONTEO DE PEDIDOS
# ---------------------------------------------------------
elif menu == "📦 Registro y Conteo de Pedidos":
    st.title("📦 Control y Registro de Pedidos (Diario, Semanal y Mensual)")
    st.write("Lleva el historial de compras e interacciones de los clientes con el número de pedido, empresa matriz, sucursal y quién lo atendió.")

    tab_reg, tab_hist = st.tabs(["➕ Registrar Nuevo Pedido Saliente", "📊 Historial y Conteo (Día / Semana / Mes)"])

    with tab_reg:
        with st.form("form_reg_pedido"):
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                nro_ped = st.text_input("Número de Pedido (Ej. PED-2026-001)", value="PED-2026-")
                matriz_ped = st.selectbox("Empresa Matriz / Cliente", CLIENTES_CLAVE_ACTUALIZACION)
                sucursal_ped = st.text_input("Sucursal Destino", value="Principal")
            with c_p2:
                atendido_ped = st.text_input("Atendido por (Asesor / Dupla)")
                fecha_ped = st.date_input("Fecha del Pedido", value=datetime.date.today())
                monto_ped = st.number_input("Monto Total del Pedido ($)", min_value=0.0, value=0.0, step=0.1)

            det_ped = st.text_area("Detalle de la Compra / Frutas / Observaciones")

            btn_save_ped = st.form_submit_button("💾 Guardar Pedido en el Historial")
            if btn_save_ped:
                if nro_ped:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO pedidos (nro_pedido, empresa_matriz, sucursal, atendido_por, fecha_pedido, monto_total, detalle_pedido)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (nro_ped.upper(), matriz_ped, sucursal_ped, atendido_ped, str(fecha_ped), monto_ped, det_ped))
                    conn.commit()
                    conn.close()
                    st.success("¡Pedido registrado exitosamente en el historial!")
                    st.rerun()
                else:
                    st.warning("Completa el Número de Pedido.")

    with tab_hist:
        conn = sqlite3.connect(DB_NAME)
        df_ped = pd.read_sql("SELECT * FROM pedidos", conn)
        conn.close()

        if not df_ped.empty:
            df_ped["fecha_dt"] = pd.to_datetime(df_ped["fecha_pedido"])
            hoy_ts = pd.Timestamp(datetime.date.today())

            pedidos_dia = df_ped[df_ped["fecha_dt"] == hoy_ts]
            inicio_semana = hoy_ts - pd.Timedelta(days=hoy_ts.dayofweek)
            pedidos_semana = df_ped[df_ped["fecha_dt"] >= inicio_semana]
            pedidos_mes = df_ped[(df_ped["fecha_dt"].dt.year == hoy_ts.year) & (df_ped["fecha_dt"].dt.month == hoy_ts.month)]

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Pedidos Hoy (Día)", len(pedidos_dia), f"${pedidos_dia['monto_total'].sum():,.2f}")
            with col_m2:
                st.metric("Pedidos esta Semana", len(pedidos_semana), f"${pedidos_semana['monto_total'].sum():,.2f}")
            with col_m3:
                st.metric("Pedidos este Mes", len(pedidos_mes), f"${pedidos_mes['monto_total'].sum():,.2f}")

            st.markdown("---")
            st.subheader("📋 Historial Completo de Pedidos Registrados")
            st.dataframe(df_ped.drop(columns=["fecha_dt"]), use_container_width=True)
        else:
            st.info("No hay pedidos registrados todavía en el sistema.")

# ---------------------------------------------------------
# 6. HISTORIAL Y PIPELINE DE VENTAS
# ---------------------------------------------------------
elif menu == "🛒 Historial y Pipeline de Ventas":
    st.title("🛒 Historial y Pipeline (Permanente)")
    with st.form("form_pipe_db"):
        n = st.text_input("Negocio / Oportunidad")
        e = st.selectbox("Estado", ["Prospecto", "Cotizado", "Cerrado Ganado", "Cerrado Perdido"])
        v = st.number_input("Valor ($)", min_value=0.0)
        if st.form_submit_button("Guardar Negocio"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO pipeline (negocio, estado, valor) VALUES (?, ?, ?)", (n, e, v))
            conn.commit()
            conn.close()
            st.success("¡Registrado!")
            st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_p = pd.read_sql("SELECT * FROM pipeline", conn)
    conn.close()
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True)

# ---------------------------------------------------------
# 7. CONTROL DE INVENTARIO Y LOTES
# ---------------------------------------------------------
elif menu == "📦 Control de Inventario y Lotes":
    st.title("📦 Control de Inventario, Lotes y Stock")
    st.write("Registra la llegada de mercancía por lotes y controla el stock disponible restando mermas automáticamente.")

    tab_inv_reg, tab_inv_ver = st.tabs(["➕ Registrar Nuevo Lote", "📋 Ver Inventario Activo y Lotes"])

    with tab_inv_reg:
        with st.form("form_inv_db"):
            lote_n = st.text_input("Número de Lote (Ej. LOTE-GALA-01)")
            prod_n = st.text_input("Descripción de la Fruta / Producto (Ej. MANZANA GALA)")
            stock_n = st.number_input("Cantidad de Cajas / Empaques Ingresados", min_value=1, value=100)
            costo_n = st.number_input("Costo Unitario por Caja ($)", min_value=0.0, value=50.0, step=0.1)
            fecha_lote = st.date_input("Fecha de Ingreso", value=datetime.date.today())

            if st.form_submit_button("Guardar Lote en Inventario"):
                if lote_n and prod_n:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO inventario (lote, producto, stock_inicial, costo, fecha_ingreso)
                        VALUES (?, ?, ?, ?, ?)
                    """, (lote_n.upper(), prod_n.upper(), stock_n, costo_n, str(fecha_lote)))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Lote {lote_n} registrado con éxito!")
                    st.rerun()
                else:
                    st.warning("Completa el número de lote y el producto.")

    with tab_inv_ver:
        conn = sqlite3.connect(DB_NAME)
        df_inv = pd.read_sql("SELECT * FROM inventario", conn)
        df_mer_res = pd.read_sql("SELECT lote_id, SUM(cantidad_perdida) as total_perdido FROM mermas GROUP BY lote_id", conn)
        conn.close()

        if not df_inv.empty:
            if not df_mer_res.empty:
                df_inv = df_inv.merge(df_mer_res, left_on="id", right_on="lote_id", how="left")
                df_inv["total_perdido"] = df_inv["total_perdido"].fillna(0)
            else:
                df_inv["total_perdido"] = 0

            df_inv["stock_actual"] = df_inv["stock_inicial"] - df_inv["total_perdido"]
            df_inv["valor_total_inventario"] = df_inv["stock_actual"] * df_inv["costo"]

            st.subheader("📊 Resumen General de Lotes en Frío (Stock Restado por Mermas)")
            st.dataframe(df_inv[["id", "lote", "producto", "stock_inicial", "total_perdido", "stock_actual", "costo", "valor_total_inventario", "fecha_ingreso"]], use_container_width=True)

            st.markdown("---")
            st.subheader("🗑️ Eliminar Lote Obsoleto")
            lote_a_borrar = st.selectbox("Selecciona ID y Lote a eliminar:", [f"ID: {r['id']} - {r['lote']} ({r['producto']})" for _, r in df_inv.iterrows()])
            if st.button("Eliminar Lote Seleccionado"):
                id_a_del = int(lote_a_borrar.split("ID: ")[1].split(" -")[0])
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inventario WHERE id = ?", (id_a_del,))
                cursor.execute("DELETE FROM mermas WHERE lote_id = ?", (id_a_del,))
                conn.commit()
                conn.close()
                st.success("¡Lote y sus registros de mermas eliminados!")
                st.rerun()
        else:
            st.info("No hay lotes de inventario registrados.")

# ---------------------------------------------------------
# 8. MUESTREO Y CONTROL DE MERMAS
# ---------------------------------------------------------
elif menu == "🗑️ Muestreo y Control de Mermas":
    st.title("🗑️ Control de Mermas y Descuento Automático de Stock")
    st.write("Registra las pérdidas por mermas asociadas directamente a tus lotes de inventario para calcular el impacto monetario.")

    conn = sqlite3.connect(DB_NAME)
    df_inv_merma = pd.read_sql("SELECT * FROM inventario", conn)
    conn.close()

    tab_m_reg, tab_m_ver = st.tabs(["➕ Registrar Nueva Merma", "📊 Historial y Pérdidas Monetarias"])

    with tab_m_reg:
        if not df_inv_merma.empty:
            with st.form("form_mer_db"):
                lote_opciones = [f"ID: {r['id']} | Lote: {r['lote']} - {r['producto']} (Costo: ${r['costo']})" for _, r in df_inv_merma.iterrows()]
                lote_sel_merma = st.selectbox("📦 Seleccionar Lote Afectado:", lote_opciones)
                
                cant_perdida = st.number_input("Cantidad de Cajas / Unidades Perdidas", min_value=1, value=1)
                motivo_merma = st.selectbox("Motivo de la Merma", ["Maduración excesiva / Daño", "Golpes en transporte", "Plagas / Descomposición", "Robo / Extravío", "Otro"])
                f_merma = st.date_input("Fecha de Registro de Merma", value=datetime.date.today())

                if st.form_submit_button("Registrar Merma y Descontar de Inventario"):
                    id_lote_Elegido = int(lote_sel_merma.split("ID: ")[1].split(" |")[0])
                    lote_row = df_inv_merma[df_inv_merma["id"] == id_lote_Elegido].iloc[0]
                    
                    perdida_monetaria_total = cant_perdida * lote_row["costo"]

                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO mermas (lote_id, producto, cantidad_perdida, perdida_monetaria, motivo, fecha_merma)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (id_lote_Elegido, lote_row["producto"], cant_perdida, perdida_monetaria_total, motivo_merma, str(f_merma)))
                    conn.commit()
                    conn.close()

                    st.success(f"¡Merma registrada! Se restaron {cant_perdida} unidades al lote y se calculó una pérdida de ${perdida_monetaria_total:,.2f}.")
                    st.rerun()
        else:
            st.warning("Primero debes registrar al menos un lote en el módulo de 'Control de Inventario y Lotes'.")

    with tab_m_ver:
        conn = sqlite3.connect(DB_NAME)
        df_mermas_hist = pd.read_sql("SELECT * FROM mermas", conn)
        conn.close()

        if not df_mermas_hist.empty:
            total_perdida_dinero = df_mermas_hist["perdida_monetaria"].sum()
            total_cajas_perdidas = df_mermas_hist["cantidad_perdida"].sum()

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Total Cajas Perdidas por Merma", f"{total_cajas_perdidas} cajas")
            with col_m2:
                st.metric("💰 Pérdida Monetaria Total", f"${total_perdida_dinero:,.2f}")

            st.markdown("---")
            st.subheader("📋 Historial Detallado de Mermas")
            st.dataframe(df_mermas_hist, use_container_width=True)

            st.markdown("---")
            st.subheader("🗑️ Eliminar Registro de Merma")
            merma_a_borrar = st.selectbox("Selecciona ID de Merma a eliminar:", [f"ID Merma: {r['id']} - {r['producto']} ({r['cantidad_perdida']} cajas)" for _, r in df_mermas_hist.iterrows()])
            if st.button("Eliminar Merma Seleccionada"):
                id_m_del = int(merma_a_borrar.split("ID Merma: ")[1].split(" -")[0])
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM mermas WHERE id = ?", (id_m_del,))
                conn.commit()
                conn.close()
                st.success("¡Registro de merma eliminado y stock restituido!")
                st.rerun()
        else:
            st.info("No hay registros de mermas todavía.")

# ---------------------------------------------------------
# 9. LIQUIDACIÓN DE COMISIONES
# ---------------------------------------------------------
elif menu == "💰 Liquidación de Comisiones":
    st.title("💰 Liquidación de Comisiones (Permanente)")
    with st.form("form_com_db"):
        asesor = st.text_input("Asesor / Dupla")
        tot = st.number_input("Comisión Total ($)", min_value=0.0)
        if st.form_submit_button("Guardar Comisión"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO comisiones (asesor, total) VALUES (?, ?)", (asesor, tot))
            conn.commit()
            conn.close()
            st.success("¡Guardado!")
            st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_com = pd.read_sql("SELECT * FROM comisiones", conn)
    conn.close()
    if not df_com.empty:
        st.dataframe(df_com, use_container_width=True)

# ---------------------------------------------------------
# 10. RUTINA SEMANAL COMERCIAL
# ---------------------------------------------------------
elif menu == "📅 Rutina Semanal Comercial":
    st.title("📅 Rutina Semanal Comercial")
    st.write("Planificación de visitas comerciales, llamadas de seguimiento y cuentas clave.")
    st.info("Módulo operativo permanente habilitado.")
