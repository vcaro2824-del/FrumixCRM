import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import sqlite3
import json
import threading
import time
import urllib.request
import os

venezuela_tz = timezone(timedelta(hours=-4))

def get_now_vz():
    return datetime.now(venezuela_tz)

def get_today_vz():
    return datetime.now(venezuela_tz).date()

st.set_page_config(
    page_title="Frumix C.A. - ERP B2B Enterprise Elite V40",
    page_icon="🍓",
    layout="wide",
)

def keep_alive():
    while True:
        try:
            urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=5)
        except:
            pass
        time.sleep(120)

threading.Thread(target=keep_alive, daemon=True).start()

# ---------------------------------------------------------
# RUTA PERSISTENTE DE BASE DE DATOS (GARANTIZA QUE NO SE BORRE NADA)
# ---------------------------------------------------------
DB_FILE_NAME = "frumix_enterprise_elite_v40.db"

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            return os.path.join(data_dir, DB_FILE_NAME)
        except:
            pass
    return os.path.join(base_dir, DB_FILE_NAME)

DB_NAME = get_db_path()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matriz_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            barra TEXT,
            descripcion TEXT,
            maneja_calibre TEXT,
            clasificacion_calidad TEXT,
            empaque_kg REAL,
            costo_caja REAL,
            precio_caja REAL,
            precio_kg REAL,
            margen_pct REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizador_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descripcion TEXT,
            calibre_sugerido TEXT,
            empaque_kg REAL,
            precio_caja REAL,
            orden INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones_guardadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_cotizacion TEXT,
            cliente TEXT,
            fecha_cotizacion TEXT,
            validez TEXT,
            detalle_json TEXT
        )
    """)
    
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devoluciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_pedido TEXT,
            cliente TEXT,
            sucursal TEXT,
            producto TEXT,
            calibre TEXT,
            cantidad_devuelta TEXT,
            motivo_devolucion TEXT,
            destino_accion TEXT,
            fecha_devolucion TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            rol TEXT,
            accion TEXT,
            detalles TEXT,
            fecha_hora TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes_cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cliente_o_asesor TEXT,
            empresa TEXT,
            observacion TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

EMPRESA = {
    "nombre": "FRUMIX C.A.",
    "rif": "J-40985632-1",
    "direccion": "Centro de Distribución Principal, Caracas, Venezuela",
    "telefono": "+58 412-FRUMIX1",
}

def get_catalogo_cache():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM matriz_precios", conn)
    conn.close()
    return df

def get_clientes_cache():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()
    return df

def get_inventario_cache():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM inventario", conn)
    conn.close()
    return df

def registrar_auditoria(usuario, rol, accion, detalles):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        hora_vz = get_now_vz().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO bitacora_auditoria (usuario, rol, accion, detalles, fecha_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario, rol, accion, detalles, hora_vz))
        conn.commit()
        conn.close()
    except:
        pass

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.rol = ""

if not st.session_state.autenticado:
    st.title("🍓 Frumix C.A. - Control de Acceso ERP B2B")
    st.write("Ingrese sus credenciales corporativas autorizadas.")
    
    with st.form("form_login"):
        user_input = st.text_input("Usuario (ej. gerencia, ventas)")
        pass_input = st.text_input("Contraseña", type="password")
        btn_login = st.form_submit_button("Iniciar Sesión")
        
        if btn_login:
            credenciales = {
                "gerencia": ("frumix2026*", "Gerencia General"),
                "ventas": ("ventas123", "Equipo Comercial")
            }
            if user_input in credenciales and credenciales[user_input][0] == pass_input:
                st.session_state.autenticado = True
                st.session_state.usuario = user_input
                st.session_state.rol = credenciales[user_input][1]
                
                registrar_auditoria(user_input, credenciales[user_input][1], "INICIO DE SESIÓN", f"Acceso exitoso al sistema por {credenciales[user_input][1]}")
                
                st.success(f"¡Bienvenido, {st.session_state.rol}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

st.sidebar.markdown(f"### 🍓 {EMPRESA['nombre']}")
st.sidebar.markdown(f"**Usuario Activo:** {st.session_state.rol}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    registrar_auditoria(st.session_state.usuario, st.session_state.rol, "CIERRE DE SESIÓN", "El usuario cerró sesión.")
    st.session_state.autenticado = False
    st.rerun()
st.sidebar.markdown("---")

modulos_disponibles = [
    "1. 📊 Dashboard Gerencial, P&L & Auditoría",
    "2. 📦 Inventario Flexible (Tabla 100% Editable)",
    "3. 🛒 Generador de Pedidos y Presupuestos (Manual y Formato Frumix)",
    "4. 📄 Cotizador Pro (Historial por Cliente, Precios, Edición y Calibres)",
    "5. 📋 Registro Manual de Facturación & CxC Independiente",
    "6. 🍓 Catálogo de Productos (Calibre Opcional)",
    "7. 🔄 Kardex & Trazabilidad de Lotes (FIFO)",
    "8. 🏢 Cartera Oficial de Clientes (Manual, Editable y Sucursales)",
    "9. 🛍️ Historial de Compras de Clientes",
    "10. 📈 Métricas y Reportes Comerciales",
    "11. 🎯 Embudo de Ventas (Sales Funnel)",
    "12. 💰 Cobranza, Facturación (Editar/Eliminar) y Crédito",
    "13. 🚚 Logística y Estatus de Despachos",
    "14. 💲 Matriz Dinámica de Precios (Caja a KG)",
    "15. 🗑️ Control de Mermas & Pérdidas",
    "16. ↩️ Módulo de Devoluciones (Merma o Reingreso)",
    "17. 📋 Historial Completo de Pedidos & Edición/Eliminación",
]

menu = st.sidebar.radio("Módulos ERP Enterprise Elite V40:", modulos_disponibles)

# ---------------------------------------------------------
# 1. DASHBOARD GERENCIAL, P&L & AUDITORÍA
# ---------------------------------------------------------
if menu.startswith("1."):
    st.title("📊 Dashboard Gerencial, Estado de Resultados y Auditoría")
    st.write("Centro analítico con control de actividad de usuarios y salud financiera.")

    conn = sqlite3.connect(DB_NAME)
    df_ped = pd.read_sql("SELECT * FROM pedidos", conn)
    df_inv = pd.read_sql("SELECT * FROM inventario", conn)
    df_mer = pd.read_sql("SELECT * FROM mermas", conn)
    df_cxc = pd.read_sql("SELECT * FROM cobranza", conn)
    df_cli = pd.read_sql("SELECT * FROM clientes", conn)
    df_audit = pd.read_sql("SELECT * FROM bitacora_auditoria ORDER BY id DESC LIMIT 50", conn)
    conn.close()

    total_ventas = df_ped["monto_total"].sum() if not df_ped.empty else 0.0
    ganancia_neta_pedidos = df_ped["ganancia_estimada"].sum() if not df_ped.empty else 0.0
    val_inv = (df_inv["stock_cajas"] * df_inv["costo_unitario_caja"]).sum() if not df_inv.empty else 0.0
    deuda_pendiente = (df_cxc[df_cxc["estatus_pago"] != "Pagado"]["monto_factura"] - df_cxc[df_cxc["estatus_pago"] != "Pagado"]["monto_pagado"]).sum() if not df_cxc.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Ventas Totales", f"${total_ventas:,.2f}")
    with c2:
        st.metric("Utilidad Bruta Estimada", f"${ganancia_neta_pedidos:,.2f}", delta=f"{(ganancia_neta_pedidos/total_ventas*100) if total_ventas>0 else 0:.1f}% Margen")
    with c3:
        st.metric("Valor Inventario en Frío", f"${val_inv:,.2f}")
    with c4:
        st.metric("CxC Activas", f"${deuda_pendiente:,.2f}")

    st.markdown("---")
    st.subheader("🕵️‍♂️ Bitácora de Auditoría y Control de Accesos")
    if not df_audit.empty:
        st.dataframe(df_audit[["fecha_hora", "usuario", "rol", "accion", "detalles"]], use_container_width=True)
        csv_audit = df_audit.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Auditoría en Excel (CSV)", csv_audit, "auditoria_frumix.csv", "text/csv")
    else:
        st.info("No hay registros en la bitácora de auditoría.")

# ---------------------------------------------------------
# 2. INVENTARIO FLEXIBLE (TABLA INTERACTIVA 100% EDITABLE)
# ---------------------------------------------------------
elif menu.startswith("2."):
    st.title("📦 Inventario Flexible - Tabla de Existencias 100% Editable")
    st.write("Modifica cualquier celda directamente en la tabla y guarda los cambios permanentes.")

    tab_inv1, tab_inv2, tab_inv3 = st.tabs(["📋 Existencias & Edición Directa", "➕ Añadir Lote de Fruta", "🗑️ Eliminar Lote"])

    with tab_inv1:
        df_inv = get_inventario_cache()
        if not df_inv.empty:
            st.subheader("📊 Tabla de Existencias en Cámaras")
            st.info("💡 Haz clic en cualquier celda para editar el lote, producto, calibre, stock o costo directamente.")

            df_editado_inv = st.data_editor(
                df_inv,
                use_container_width=True,
                key="editor_inventario_general_v40",
                num_rows="dynamic"
            )

            if st.button("💾 Guardar Todos los Cambios de la Tabla"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    
                    for _, row in df_editado_inv.iterrows():
                        cursor.execute("""
                            UPDATE inventario 
                            SET lote = ?, producto = ?, calibre = ?, stock_cajas = ?, costo_unitario_caja = ?, fecha_ingreso = ?
                            WHERE id = ?
                        """, (
                            str(row["lote"]).upper(),
                            str(row["producto"]).upper(),
                            str(row["calibre"]).upper(),
                            float(row["stock_cajas"]),
                            float(row["costo_unitario_caja"]),
                            str(row["fecha_ingreso"]),
                            int(row["id"])
                        ))
                    
                    conn.commit()
                    conn.close()
                    
                    registrar_auditoria(st.session_state.usuario, st.session_state.rol, "EDICIÓN MASIVA INVENTARIO", "Se actualizaron existencias en la base de datos persistente.")
                    st.success("¡Los cambios del inventario se han guardado exitosamente y de forma permanente!")
                    st.rerun()
                except Exception as e:
                    if 'conn' in locals():
                        conn.close()
                    st.error(f"Error al guardar los cambios: {e}")

            st.markdown("---")
            csv_inv = df_inv.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Inventario en Excel (CSV)", csv_inv, "inventario_frumix.csv", "text/csv")
        else:
            st.info("No hay inventario registrado en cámaras.")

    with tab_inv2:
        df_cat = get_catalogo_cache()
        lista_frutas_cat = df_cat["descripcion"].unique().tolist() if not df_cat.empty else []

        if not lista_frutas_cat:
            st.warning("⚠️ Primero debes registrar tus frutas en el módulo **'6. 🍓 Catálogo de Productos'**.")
        else:
            with st.form("form_ingreso_lote_flexible"):
                st.subheader("Cargar Lote a Cámaras de Frío")
                c1, c2 = st.columns(2)
                with c1:
                    fruta_sel = st.selectbox("Seleccionar Fruta", lista_frutas_cat)
                    lote_num = st.text_input("Número de Lote", value=f"LOTE-{get_now_vz().strftime('%Y%m%d')}")
                    
                    row_prod_info = df_cat[df_cat["descripcion"] == fruta_sel].iloc[0]
                    maneja_calibre = row_prod_info["maneja_calibre"]
                    
                    if maneja_calibre == "Sí":
                        calibre_ingresado = st.text_input("Calibre Específico (Ej. 80/88, Extra, etc.)")
                    else:
                        calibre_ingresado = "N/A (Sin calibre)"
                        st.info("Este producto no maneja calibre según su catálogo.")
                with c2:
                    cajas_ingreso = st.number_input("Cantidad de Cajas", min_value=1.0, value=100.0)
                    costo_caja = st.number_input("Costo Unitario por Caja ($)", min_value=0.0, value=50.0)
                    fecha_ing = st.date_input("Fecha de Ingreso", value=get_today_vz())

                if st.form_submit_button("💾 Guardar Lote en Inventario"):
                    if fruta_sel:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        calibre_clean = calibre_ingresado.strip().upper()
                        
                        cursor.execute("""
                            INSERT INTO inventario (lote, producto, calibre, stock_cajas, costo_unitario_caja, fecha_ingreso)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (lote_num.upper(), fruta_sel, calibre_clean, cajas_ingreso, costo_caja, str(fecha_ing)))

                        cursor.execute("""
                            INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                            VALUES (?, ?, ?, 'ENTRADA', ?, 'Carga inicial a cámaras', ?, ?)
                        """, (lote_num.upper(), fruta_sel, calibre_clean, cajas_ingreso, str(fecha_ing), st.session_state.rol))

                        conn.commit()
                        conn.close()
                        
                        registrar_auditoria(st.session_state.usuario, st.session_state.rol, "INGRESO INVENTARIO", f"Carga permanente de {cajas_ingreso} cajas de {fruta_sel} Lote {lote_num}")
                        st.success(f"¡Lote cargado y guardado con éxito!")
                        st.rerun()

    with tab_inv3:
        df_inv_del = get_inventario_cache()
        if not df_inv_del.empty:
            st.subheader("🗑️ Eliminar Registro de Inventario")
            id_del_inv = st.selectbox("Seleccione ID de Inventario a Eliminar:", df_inv_del["id"].tolist())
            if st.button("🗑️ Confirmar Eliminación de Lote"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inventario WHERE id = ?", (int(id_del_inv),))
                conn.commit()
                conn.close()
                st.success("¡Lote eliminado del sistema!")
                st.rerun()

# ---------------------------------------------------------
# 3. GENERADOR DE PEDIDOS Y PRESUPUESTOS (INGRESO MANUAL)
# ---------------------------------------------------------
elif menu.startswith("3."):
    st.title("🛒 Generador de Pedidos y Presupuestos (Ingreso Manual - Estilo Frumix)")
    st.write("Ingresa de forma manual el número de presupuesto, datos del cliente, comercial y condiciones de pago.")

    df_inv_db = get_inventario_cache()

    with st.container():
        st.subheader("📝 Datos Generales del Documento (Manuales)")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            nro_presupuesto_manual = st.text_input("Número de Presupuesto / Pedido (Ej. S13385)", value="S13385")
            cliente_manual = st.text_input("Nombre de la Empresa / Cliente", value="")
            sucursal_manual = st.text_input("Sucursal / Dirección", value="")
        with col_m2:
            comercial_manual = st.text_input("Comercial / Asesor Asignado", value="")
            dias_credito_manual = st.number_input("Condiciones de pago (Días de crédito)", min_value=0, value=21)
            fecha_presupuesto = st.date_input("Fecha del Presupuesto", value=get_today_vz())

    st.markdown("---")
    st.subheader("📦 Agregar Productos al Carrito de Pedido (Prioridad FIFO)")

    df_inv_disponible = df_inv_db[df_inv_db["stock_cajas"] > 0] if not df_inv_db.empty else pd.DataFrame()

    if not df_inv_disponible.empty:
        frutas_disponibles = df_inv_disponible["producto"].unique().tolist()
        
        if "carrito_pedido" not in st.session_state:
            st.session_state.carrito_pedido = []

        with st.form("form_agregar_item_pedido"):
            c_p1, c_p2, c_p3, c_p4 = st.columns(4)
            with c_p1:
                fruta_ped = st.selectbox("1. Seleccionar Fruta", frutas_disponibles)
            
            calibres_disp_fruta = df_inv_disponible[df_inv_disponible["producto"] == fruta_ped]["calibre"].unique().tolist()
            
            with c_p2:
                calibre_ped = st.selectbox("2. Seleccionar Calibre Disponible", calibres_disp_fruta)
                
            df_lotes_fifo = df_inv_disponible[(df_inv_disponible["producto"] == fruta_ped) & (df_inv_disponible["calibre"] == calibre_ped)].sort_values(by="fecha_ingreso", ascending=True)
            row_inv_item = df_lotes_fifo.iloc[0]
            
            stock_disponible = row_inv_item["stock_cajas"]
            costo_item = row_inv_item["costo_unitario_caja"]
            lote_sugerido = row_inv_item["lote"]

            with c_p3:
                st.caption(f"Lote FIFO: {lote_sugerido} | Stock: **{stock_disponible} cajas**")
                cajas_ped = st.number_input("3. Cantidad de Cajas", min_value=1.0, max_value=float(stock_disponible), value=1.0)
            with c_p4:
                precio_caja_ped = st.number_input("4. Precio por Caja ($)", min_value=0.0, value=float(costo_item * 1.3))

            if st.form_submit_button("➕ Agregar al Carrito"):
                subtotal = cajas_ped * precio_caja_ped
                st.session_state.carrito_pedido.append({
                    "inventario_id": int(row_inv_item["id"]),
                    "lote": lote_sugerido,
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

            monto_total_ped = df_cart["subtotal"].sum()
            st.markdown(f"### **Monto Total:** `${monto_total_ped:,.2f} USD`")

            if st.button("💾 CONFIRMAR PEDIDO Y RESERVAR STOCK EN CÁMARAS"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("BEGIN TRANSACTION;")

                    costo_total_ped = sum(item["cajas"] * item["costo_unitario"] for item in st.session_state.carrito_pedido)
                    ganancia_ped = monto_total_ped - costo_total_ped

                    cursor.execute("""
                        INSERT INTO pedidos (nro_pedido, cliente, sucursal, realizado_por, atendido_por, recibido_por, datos_importantes, fecha_pedido, monto_total, costo_total, ganancia_estimada, estatus_despacho, detalle_json)
                        VALUES (?, ?, ?, ?, ?, ?, 'Presupuesto B2B - Frumix', ?, ?, ?, ?, 'Reservado / En Espera', ?)
                    """, (nro_presupuesto_manual, cliente_manual, sucursal_manual, st.session_state.rol, comercial_manual, "Cliente Final", str(fecha_presupuesto), monto_total_ped, costo_total_ped, ganancia_ped, json.dumps(st.session_state.carrito_pedido)))

                    for item in st.session_state.carrito_pedido:
                        cursor.execute("SELECT stock_cajas FROM inventario WHERE id = ?", (item["inventario_id"],))
                        stk_act = cursor.fetchone()[0]
                        nuevo_stk = max(0.0, stk_act - item["cajas"])
                        
                        cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stk, item["inventario_id"]))

                        cursor.execute("""
                            INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                            VALUES (?, ?, ?, 'RESERVA SALIDA', ?, ?, ?, ?)
                        """, (item["lote"], item["producto"], item["calibre"], item["cajas"], f"Reserva Pedido #{nro_presupuesto_manual}", str(get_today_vz()), st.session_state.rol))

                    conn.commit()
                    conn.close()

                    registrar_auditoria(st.session_state.usuario, st.session_state.rol, "REGISTRO PEDIDO", f"Presupuesto #{nro_presupuesto_manual} creado para {cliente_manual} por ${monto_total_ped:,.2f}")
                    st.success(f"¡Presupuesto #{nro_presupuesto_manual} registrado con éxito y stock descontado!")
                    
                    logo_url = "https://raw.githubusercontent.com/vcaro2824-del/FrumixCRM/main/IMG-20261016-WA0072~3.jpg"
                    vencimiento_calc = fecha_presupuesto + timedelta(days=int(dias_credito_manual))
                    
                    html_presupuesto = f"""
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Presupuesto #{nro_presupuesto_manual} - Frumix C.A.</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; font-size: 13px; margin: 30px; color: #111; text-align: left; }}
                            .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6B8E23; padding-bottom: 15px; align-items: center; text-align: left; }}
                            .logo {{ max-height: 75px; width: auto; }}
                            .info-box {{ margin-top: 20px; display: flex; justify-content: space-between; line-height: 1.5; text-align: left; }}
                            h2 {{ color: #222; margin-top: 25px; text-align: left; }}
                            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; text-align: left; }}
                            th, td {{ border: 1px solid #bbb; padding: 10px 12px; text-align: left; font-family: Arial, sans-serif; }}
                            th {{ background-color: #f2f2f2; font-weight: bold; text-align: left; }}
                            .footer-cond {{ margin-top: 30px; font-weight: bold; font-size: 12px; text-align: left; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <div>
                                <img src="{logo_url}" class="logo" alt="Logo Frumix">
                                <div style="font-size: 15px; color: #333; margin-top: 4px; font-weight: bold;">RIF: J-40985632-1 | Caracas, Venezuela</div>
                            </div>
                            <div style="text-align: right; font-size: 12px;">
                                <strong>Documento generado<br>(hora de Caracas):</strong><br>{get_now_vz().strftime('%Y-%m-%d %H:%M:%S')}
                            </div>
                        </div>
                        
                        <div class="info-box">
                            <div>
                                <strong>{cliente_manual}</strong><br>
                                {sucursal_manual}<br>
                                Venezuela<br>
                            </div>
                            <div style="text-align: right;">
                                <strong>Comercial:</strong> {comercial_manual}<br>
                                <strong>Fecha del presupuesto:</strong> {fecha_presupuesto}<br>
                                <strong>Vencimiento:</strong> {vencimiento_calc}
                            </div>
                        </div>

                        <h2>Presupuesto # {nro_presupuesto_manual}</h2>
                        <table>
                            <tr>
                                <th>Descripción</th>
                                <th style="text-align: right;">Cantidad</th>
                            </tr>
                    """
                    for item in st.session_state.carrito_pedido:
                        html_presupuesto += f"<tr><td>[{item['lote']}] {item['producto']} ({item['calibre']})</td><td style='text-align: right;'>{item['cajas']:.2f} CAJA</td></tr>"
                    
                    html_presupuesto += f"""
                        </table>
                        <div class="footer-cond">
                            <p>Condiciones de pago: {dias_credito_manual} días</p>
                            <p>Monto Total: ${monto_total_ped:,.2f} USD</p>
                        </div>
                    </body>
                    </html>
                    """
                    st.download_button(
                        label="📥 Descargar Documento Oficial / Presupuesto HTML",
                        data=html_presupuesto,
                        file_name=f"Presupuesto_{nro_presupuesto_manual}.html",
                        mime="text/html"
                    )
                    st.session_state.carrito_pedido = []

                except Exception as e:
                    if 'conn' in locals():
                        conn.rollback()
                        conn.close()
                    st.error(f"Error procesando la transacción: {e}")
    else:
        st.warning("No hay existencias disponibles en cámaras de frío.")

# ---------------------------------------------------------
# 4. COTIZADOR PRO (HISTORIAL POR CLIENTE, EDICIÓN Y CALIBRES)
# ---------------------------------------------------------
elif menu.startswith("4."):
    st.title("📄 Cotizador B2B Profesional - Historial y Gestión por Cliente")
    st.write("Crea, edita, guarda y consulta cotizaciones específicas para cada cliente de forma permanente.")

    conn = sqlite3.connect(DB_NAME)
    df_cot_items = pd.read_sql("SELECT * FROM cotizador_items", conn) if "cotizador_items" in [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else pd.DataFrame()
    df_cli_cot = pd.read_sql("SELECT * FROM clientes_cotizaciones", conn)
    df_cot_guardadas = pd.read_sql("SELECT * FROM cotizaciones_guardadas", conn)
    conn.close()

    if df_cot_items.empty:
        items_iniciales = [
            ("MANZANA GALA", "125-113-88-80", 19.0, 59.66, 1),
            ("MANZANA ROJA", "125-113-100-88-80", 19.0, 72.01, 2),
            ("MANZANA VERDE", "113-100-88", 19.0, 79.04, 3),
            ("MANZANA AMARILLA (americana)", "-", 18.0, 0.00, 4),
            ("MANZANA PINK LADY", "125-113-100", 18.5, 58.09, 5),
            ("PERA VERDE", "100", 18.0, 59.94, 6),
            ("PERA COSCIA", "40-44", 10.0, 0.00, 7),
            ("PERA FORELLE", "G", 9.0, 0.00, 8),
            ("UVA RED GLOBE", "Jumbo", 8.2, 65.02, 9),
            ("UVA VERDE S/SEMILLA", "Doble Jumbo", 8.2, 50.00, 10),
            ("UVA NEGRA S/SEMILLA", "-", 7.3, 0.00, 11),
            ("CIRUELA IMPORTADA", "Grande", 9.0, 70.02, 12),
            ("KIWI VERDE", "-", 10.0, 60.00, 13),
            ("KIWI AMARILLO", "-", 9.0, 0.00, 14),
            ("GRANADA", "-", 3.8, 0.00, 15),
            ("CEREZA", "-", 2.5, 0.00, 16),
            ("CEREZA (Jumbo)", "Jumbo", 5.0, 0.00, 17),
            ("ARANDANOS", "-", 0.125, 4.00, 18),
            ("NARANJAS IMPORTADAS", "-", 15.0, 66.00, 19),
            ("TANGELO", "-", 9.5, 0.00, 20),
            ("MANDARINAS IMPORTADAS", "-", 9.5, 55.00, 21),
            ("POMELO", "-", 14.5, 0.00, 22),
            ("PITAHAYA ROJA", "-", 1.0, 0.00, 23),
            ("PITAHAYA AMARILLA", "-", 1.0, 0.00, 24),
            ("NECTARINA", "-", 9.0, 0.00, 25),
            ("LIMÓN AMARILLO (Importado)", "-", 16.0, 0.00, 26)
        ]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizador_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT,
                descripcion TEXT,
                calibre_sugerido TEXT,
                empaque_kg REAL,
                precio_caja REAL,
                orden INTEGER
            )
        """)
        for desc, cal_sug, emp, prec, ord_n in items_iniciales:
            cursor.execute("INSERT INTO cotizador_items (codigo, descripcion, calibre_sugerido, empaque_kg, precio_caja, orden) VALUES (?, ?, ?, ?, ?, ?)", (f"FRU-{ord_n:02d}", desc, cal_sug, emp, prec, ord_n))
        conn.commit()
        conn.close()
        
        conn = sqlite3.connect(DB_NAME)
        df_cot_items = pd.read_sql("SELECT * FROM cotizador_items", conn)
        conn.close()

    tab_cot_gen, tab_cot_hist, tab_cot_dest = st.tabs(["📄 Editor y Creador de Cotización", "📂 Historial de Cotizaciones Guardadas", "👥 Gestionar Destinatarios"])

    with tab_cot_dest:
        with st.form("form_add_cot_cli"):
            st.subheader("Registrar Cliente / Destinatario Frecuente")
            nombre_cot = st.text_input("Nombre del Cliente, Prospecto o Asesor Solicitante")
            empresa_cot = st.text_input("Empresa o Referencia")
            obs_cot = st.text_input("Observación")
            if st.form_submit_button("Guardar Destinatario"):
                if nombre_cot:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO clientes_cotizaciones (nombre_cliente_o_asesor, empresa, observacion) VALUES (?, ?, ?)", (nombre_cot, empresa_cot, obs_cot))
                    conn.commit()
                    conn.close()
                    st.success("¡Destinatario guardado permanentemente!")
                    st.rerun()

    if not df_cli_cot.empty:
        lista_dest_cot = (df_cli_cot["nombre_cliente_o_asesor"] + " (" + df_cli_cot["empresa"] + ")").tolist()
    else:
        lista_dest_cot = ["Cliente General / Mostrador"]

    with tab_cot_gen:
        st.subheader("📝 Configuración de la Cotización Actual")
        c_cg1, c_cg2, c_cg3 = st.columns(3)
        with c_cg1:
            nro_cot_input = st.text_input("Número de Cotización", value=f"COT-{get_now_vz().strftime('%Y%m%d')}-01")
        with c_cg2:
            dest_sel = st.selectbox("Seleccionar Destinatario / Cliente", lista_dest_cot)
        with c_cg3:
            vig_sel = st.date_input("Validez de la cotización:", value=get_today_vz() + timedelta(days=7))

        st.markdown("---")
        st.subheader("📋 Tabla de Precios, Calibres & Edición")
        st.info("💡 Edita los calibres sugeridos o precios. Al hacer clic en **Guardar Cotización en el Sistema**, quedará almacenada en el historial de este cliente.")

        df_editor_v = df_cot_items[["id", "orden", "codigo", "descripcion", "calibre_sugerido", "empaque_kg", "precio_caja"]].sort_values(by="orden").copy()
        df_editor_v.columns = ["ID", "ORDEN", "CÓDIGO", "DESCRIPCIÓN", "CALIBRE A MOSTRAR", "EMPAQUE/KG", "PRECIO CAJA ($)"]

        df_editado_venta = st.data_editor(df_editor_v, use_container_width=True, key="cotizador_tabla_maestra_v40", num_rows="dynamic")

        c_bt1, c_bt2 = st.columns(2)
        with c_bt1:
            if st.button("💾 Guardar Cotización en el Sistema (Permanente)"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    
                    # Guardamos la tabla maestra actual
                    for _, r in df_editado_venta.iterrows():
                        cursor.execute("""
                            UPDATE cotizador_items 
                            SET orden = ?, codigo = ?, descripcion = ?, calibre_sugerido = ?, empaque_kg = ?, precio_caja = ?
                            WHERE id = ?
                        """, (int(r["ORDEN"]), str(r["CÓDIGO"]), str(r["DESCRIPCIÓN"]).upper(), str(r["CALIBRE A MOSTRAR"]), float(r["EMPAQUE/KG"]), float(r["PRECIO CAJA ($)"]), int(r["ID"])))

                    # Guardamos el respaldo histórico de esta cotización específica para el cliente
                    detalle_snapshot = df_editado_venta.to_dict(orient="records")
                    cursor.execute("""
                        INSERT INTO cotizaciones_guardadas (nro_cotizacion, cliente, fecha_cotizacion, validez, detalle_json)
                        VALUES (?, ?, ?, ?, ?)
                    """, (nro_cot_input.upper(), dest_sel, str(get_today_vz()), str(vig_sel), json.dumps(detalle_snapshot)))

                    conn.commit()
                    conn.close()
                    st.success(f"¡Cotización {nro_cot_input} guardada exitosamente en el historial del cliente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

        with c_bt2:
            # Botón de Descarga HTML directa
            if st.button("📥 Generar Documento HTML de la Cotización"):
                logo_url = "https://raw.githubusercontent.com/vcaro2824-del/FrumixCRM/main/IMG-20261016-WA0072~3.jpg"
                html_doc = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Cotización {nro_cot_input} - Frumix C.A.</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 30px; color: #111; text-align: left; }}
                        .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6B8E23; padding-bottom: 15px; align-items: center; text-align: left; }}
                        .logo {{ max-height: 80px; width: auto; }}
                        .intro-text {{ margin-top: 22px; font-family: Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #222; text-align: left; }}
                        h3 {{ font-family: Arial, sans-serif; font-size: 14px; text-align: left; margin-top: 25px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; text-align: left; }}
                        th, td {{ border: 1px solid #bbb; padding: 10px 12px; text-align: left; font-family: Arial, sans-serif; font-size: 12px; }}
                        th {{ background-color: #f2f2f2; font-weight: bold; text-align: left; }}
                        p {{ font-family: Arial, sans-serif; font-size: 12px; text-align: left; }}
                        .signature-container {{ margin-top: 35px; width: 100%; text-align: center; }}
                        .signature {{ font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; color: #111; display: inline-block; text-align: center; line-height: 1.5; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div>
                            <img src="{logo_url}" class="logo" alt="Logo Frumix C.A.">
                            <div style="font-size: 15px; color: #333; margin-top: 5px; font-weight: bold;">RIF: J-40985632-1 | Caracas, Venezuela</div>
                        </div>
                        <div style="text-align: right; font-size: 12px;">
                            <strong>Cotización:</strong> {nro_cot_input}<br>
                            <strong>Fecha:</strong> {get_today_vz()}<br>
                            <strong>Destinatario:</strong> {dest_sel}
                        </div>
                    </div>
                    
                    <div class="intro-text">
                        A continuación encontrará nuestra lista oficial de precios y los calibres disponibles actualmente en cámaras de frío.<br>
                        Nuestra alianza con los mejores productos de frutas frescas a nivel mundial garantiza la calidad y buen servicio que nos caracteriza.
                    </div>

                    <h3>Cotización Comercial Oficial & Calibres</h3>
                    <table>
                        <tr>
                            <th>Código</th>
                            <th>Descripción</th>
                            <th>Presentación (KG)</th>
                            <th>Calibre</th>
                            <th>Precio $ X Caja</th>
                            <th>Precio $ X Kilo</th>
                        </tr>
                """
                for _, r in df_editado_venta.iterrows():
                    p_kg = round(r['PRECIO CAJA ($)'] / r['EMPAQUE/KG'], 2) if r['EMPAQUE/KG'] > 0 else 0.0
                    html_doc += f"<tr><td>{r['CÓDIGO']}</td><td>{r['DESCRIPCIÓN']}</td><td>{r['EMPAQUE/KG']}</td><td><strong>{r['CALIBRE A MOSTRAR']}</strong></td><td>${r['PRECIO CAJA ($)']:.2f}</td><td>${p_kg:.2f}</td></tr>"
                    
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
                    label="📥 Descargar Archivo HTML de Cotización",
                    data=html_doc,
                    file_name=f"Cotizacion_{nro_cot_input}.html",
                    mime="text/html"
                )

    with tab_cot_hist:
        st.subheader("📂 Historial de Cotizaciones Guardadas por Cliente")
        if not df_cot_guardadas.empty:
            st.dataframe(df_cot_guardadas[["id", "nro_cotizacion", "cliente", "fecha_cotizacion", "validez"]], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔍 Consultar, Descargar o Eliminar Cotización Guardada")
            id_cot_sel = st.selectbox("Seleccione ID de la Cotización Guardada:", df_cot_guardadas["id"].tolist(), key="sel_hist_cot")
            row_cot_h = df_cot_guardadas[df_cot_guardadas["id"] == id_cot_sel].iloc[0]
            
            st.info(f"Mostrando cotización **{row_cot_h['nro_cotizacion']}** para el cliente **{row_cot_h['cliente']}** (Fecha: {row_cot_h['fecha_cotizacion']})")
            
            detalle_cargado = json.loads(row_cot_h["detalle_json"])
            df_hist_view = pd.DataFrame(detalle_cargado)
            st.dataframe(df_hist_view, use_container_width=True)

            c_h1, c_h2 = st.columns(2)
            with c_h1:
                if st.button("📥 Volver a Descargar esta Cotización en HTML"):
                    logo_url = "https://raw.githubusercontent.com/vcaro2824-del/FrumixCRM/main/IMG-20261016-WA0072~3.jpg"
                    html_doc_h = f"""
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Cotización {row_cot_h['nro_cotizacion']} - Frumix C.A.</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 30px; color: #111; text-align: left; }}
                            .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6B8E23; padding-bottom: 15px; align-items: center; text-align: left; }}
                            .logo {{ max-height: 80px; width: auto; }}
                            .intro-text {{ margin-top: 22px; font-family: Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #222; text-align: left; }}
                            h3 {{ font-family: Arial, sans-serif; font-size: 14px; text-align: left; margin-top: 25px; }}
                            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; text-align: left; }}
                            th, td {{ border: 1px solid #bbb; padding: 10px 12px; text-align: left; font-family: Arial, sans-serif; font-size: 12px; }}
                            th {{ background-color: #f2f2f2; font-weight: bold; text-align: left; }}
                            p {{ font-family: Arial, sans-serif; font-size: 12px; text-align: left; }}
                            .signature-container {{ margin-top: 35px; width: 100%; text-align: center; }}
                            .signature {{ font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; color: #111; display: inline-block; text-align: center; line-height: 1.5; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <div>
                                <img src="{logo_url}" class="logo" alt="Logo Frumix C.A.">
                                <div style="font-size: 15px; color: #333; margin-top: 5px; font-weight: bold;">RIF: J-40985632-1 | Caracas, Venezuela</div>
                            </div>
                            <div style="text-align: right; font-size: 12px;">
                                <strong>Cotización:</strong> {row_cot_h['nro_cotizacion']}<br>
                                <strong>Fecha:</strong> {row_cot_h['fecha_cotizacion']}<br>
                                <strong>Destinatario:</strong> {row_cot_h['cliente']}
                            </div>
                        </div>
                        
                        <div class="intro-text">
                            A continuación encontrará nuestra lista oficial de precios y los calibres disponibles actualmente en cámaras de frío.
                        </div>

                        <h3>Cotización Comercial Oficial & Calibres</h3>
                        <table>
                            <tr>
                                <th>Código</th>
                                <th>Descripción</th>
                                <th>Presentación (KG)</th>
                                <th>Calibre</th>
                                <th>Precio $ X Caja</th>
                                <th>Precio $ X Kilo</th>
                            </tr>
                    """
                    for r in detalle_cargado:
                        p_kg = round(r['PRECIO CAJA ($)'] / r['EMPAQUE/KG'], 2) if r['EMPAQUE/KG'] > 0 else 0.0
                        html_doc_h += f"<tr><td>{r['CÓDIGO']}</td><td>{r['DESCRIPCIÓN']}</td><td>{r['EMPAQUE/KG']}</td><td><strong>{r['CALIBRE A MOSTRAR']}</strong></td><td>${r['PRECIO CAJA ($)']:.2f}</td><td>${p_kg:.2f}</td></tr>"
                        
                    html_doc_h += f"""
                        </table>
                        <br>
                        <p><strong>Condiciones Comerciales:</strong> Sujeto a disponibilidad en cámaras de frío. Validez hasta {row_cot_h['validez']}.</p>
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
                        label="📥 Descargar HTML Histórico",
                        data=html_doc_h,
                        file_name=f"Cotizacion_{row_cot_h['nro_cotizacion']}.html",
                        mime="text/html",
                        key="btn_dl_hist"
                    )

            with c_h2:
                if st.button("🗑️ Eliminar esta Cotización Guardada"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM cotizaciones_guardadas WHERE id = ?", (int(id_cot_sel),))
                    conn.commit()
                    conn.close()
                    st.success("¡Cotización eliminada del historial!")
                    st.rerun()
        else:
            st.info("No hay cotizaciones guardadas en el historial todavía. Crea una y guárdala desde la pestaña 'Editor y Creador de Cotización'.")

# ---------------------------------------------------------
# 5. REGISTRO MANUAL DE FACTURACIÓN & CXC
# ---------------------------------------------------------
elif menu.startswith("5."):
    st.title("📋 Registro Manual de Facturación e Ingreso (Estilo Frumix)")
    st.write("Emite facturas comerciales de manera manual con la misma estructura oficial de datos.")

    with st.form("form_factura_manual_estilo"):
        st.subheader("📝 Datos de Facturación (Manuales)")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            nro_factura_m = st.text_input("Nro. de Factura Oficial (Ej. FAC-00201)", value="FAC-")
            cliente_fac_m = st.text_input("Empresa / Cliente Matriz", value="")
            sucursal_fac_m = st.text_input("Sucursal / Dirección de Facturación", value="")
        with c_f2:
            comercial_fac_m = st.text_input("Comercial Asignado", value="")
            monto_fac_m = st.number_input("Monto Total de la Factura ($)", min_value=1.0, value=1000.0)
            dias_venc_m = st.number_input("Días de Crédito Otorgados", min_value=1, value=21)
            fecha_em_m = st.date_input("Fecha de Emisión", value=get_today_vz())

        if st.form_submit_button("💾 Registrar Factura y Activar Cuenta por Cobrar"):
            if nro_factura_m:
                fecha_venc_calc = fecha_em_m + timedelta(days=int(dias_venc_m))
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cobranza (nro_factura, cliente, fecha_emision, fecha_vencimiento, monto_factura, monto_pagado, estatus_pago)
                    VALUES (?, ?, ?, ?, ?, 0.0, 'Pendiente')
                """, (nro_factura_m.upper(), cliente_fac_m, str(fecha_em_m), str(fecha_venc_calc), monto_fac_m))
                conn.commit()
                conn.close()

                registrar_auditoria(st.session_state.usuario, st.session_state.rol, "REGISTRO FACTURA", f"Factura {nro_factura_m} por ${monto_fac_m:,.2f} para {cliente_fac_m}")
                st.success(f"¡Factura {nro_factura_m} registrada con éxito en Cuentas por Cobrar!")
                
                logo_url = "https://raw.githubusercontent.com/vcaro2824-del/FrumixCRM/main/IMG-20261016-WA0072~3.jpg"
                html_factura = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Factura #{nro_factura_m} - Frumix C.A.</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; font-size: 13px; margin: 30px; color: #111; text-align: left; }}
                        .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6B8E23; padding-bottom: 15px; align-items: center; text-align: left; }}
                        .logo {{ max-height: 75px; width: auto; }}
                        .info-box {{ margin-top: 20px; display: flex; justify-content: space-between; line-height: 1.5; text-align: left; }}
                        h2 {{ color: #222; margin-top: 25px; text-align: left; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; text-align: left; }}
                        th, td {{ border: 1px solid #bbb; padding: 10px 12px; text-align: left; font-family: Arial, sans-serif; }}
                        th {{ background-color: #f2f2f2; font-weight: bold; text-align: left; }}
                        .footer-cond {{ margin-top: 30px; font-weight: bold; font-size: 12px; text-align: left; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div>
                            <img src="{logo_url}" class="logo" alt="Logo Frumix">
                            <div style="font-size: 15px; color: #333; margin-top: 4px; font-weight: bold;">RIF: J-40985632-1 | Caracas, Venezuela</div>
                        </div>
                        <div style="text-align: right; font-size: 12px;">
                            <strong>Fecha de Emisión:</strong> {fecha_em_m}<br>
                            <strong>Vencimiento:</strong> {fecha_venc_calc}
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <div>
                            <strong>CLIENTE:</strong> {cliente_fac_m}<br>
                            <strong>DIRECCIÓN:</strong> {sucursal_fac_m}<br>
                        </div>
                        <div style="text-align: right;">
                            <strong>Comercial:</strong> {comercial_fac_m}<br>
                            <strong>Condiciones de Pago:</strong> {dias_venc_m} días
                        </div>
                    </div>

                    <h2>Factura # {nro_factura_m}</h2>
                    <table>
                        <tr>
                            <th>Descripción del Documento / Servicio</th>
                            <th style="text-align: right;">Monto Total ($)</th>
                        </tr>
                        <tr>
                            <td>Facturación Comercial B2B - Frumix C.A.</td>
                            <td style="text-align: right;">${monto_fac_m:,.2f} USD</td>
                        </tr>
                    </table>
                    <div class="footer-cond">
                        <p>Estatus: Pendiente de Pago</p>
                    </div>
                </body>
                </html>
                """
                st.download_button(
                    label="📥 Descargar Documento de Factura Oficial HTML",
                    data=html_factura,
                    file_name=f"Factura_{nro_factura_m}.html",
                    mime="text/html"
                )

# ---------------------------------------------------------
# 6. CATÁLOGO DE PRODUCTOS (CALIBRE OPCIONAL)
# ---------------------------------------------------------
elif menu.startswith("6."):
    st.title("🍓 Catálogo Oficial de Productos - Calibre Opcional")
    st.write("Define tus productos indicando si manejan calibre o si se venden a granel/empaque directo.")

    tab_p1, tab_p2, tab_p3 = st.tabs(["📋 Catálogo Actual", "✏️ Editar Producto", "➕ Registrar Nuevo Producto"])

    with tab_p1:
        df_cat = get_catalogo_cache()
        if not df_cat.empty:
            st.dataframe(df_cat, use_container_width=True)
            
            csv_cat = df_cat.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Catálogo en Excel (CSV)", csv_cat, "catalogo_frumix.csv", "text/csv")

            st.markdown("---")
            id_p_del = st.selectbox("Seleccione ID de producto a eliminar:", df_cat["id"].tolist())
            if st.button("🗑️ Eliminar Producto"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM matriz_precios WHERE id = ?", (int(id_p_del),))
                conn.commit()
                conn.close()
                st.success("¡Producto eliminado!")
                st.rerun()
        else:
            st.info("Catálogo vacío.")

    with tab_p2:
        df_cat_ed = get_catalogo_cache()
        if not df_cat_ed.empty:
            id_ce = st.selectbox("Seleccionar ID para Editar:", df_cat_ed["id"].tolist(), key="ed_p_cat")
            row_ce = df_cat_ed[df_cat_ed["id"] == id_ce].iloc[0]

            with st.form("form_edit_prod"):
                ec_cod = st.text_input("Código", value=row_ce["codigo"])
                ec_desc = st.text_input("Descripción", value=row_ce["descripcion"])
                
                cal_opc = ["Sí", "No"]
                idx_c = cal_opc.index(row_ce["maneja_calibre"]) if row_ce["maneja_calibre"] in cal_opc else 0
                ec_maneja = st.selectbox("¿Maneja Calibre?", cal_opc, index=idx_c)
                
                cal_calidad = ["Premium", "Con detalle", "A granel"]
                idx_q = cal_calidad.index(row_ce["clasificacion_calidad"]) if row_ce["clasificacion_calidad"] in cal_calidad else 0
                ec_calidad = st.selectbox("Calidad", cal_calidad, index=idx_q)

                ec_emp = st.number_input("Empaque (Kg)", min_value=0.01, value=float(row_ce["empaque_kg"]))
                ec_cos = st.number_input("Costo Caja ($)", min_value=0.0, value=float(row_ce["costo_caja"]))
                ec_pre = st.number_input("Precio Caja ($)", min_value=0.0, value=float(row_ce["precio_caja"]))

                if st.form_submit_button("💾 Guardar Cambios"):
                    p_kg = round(ec_pre / ec_emp, 2) if ec_emp > 0 else 0.0
                    mrg = round(((ec_pre - ec_cos) / ec_pre * 100), 1) if ec_pre > 0 else 0.0
                    
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE matriz_precios 
                        SET codigo = ?, descripcion = ?, maneja_calibre = ?, clasificacion_calidad = ?, empaque_kg = ?, costo_caja = ?, precio_caja = ?, precio_kg = ?, margen_pct = ?
                        WHERE id = ?
                    """, (ec_cod, ec_desc.upper(), ec_maneja, ec_calidad, ec_emp, ec_cos, ec_pre, p_kg, mrg, int(id_ce)))
                    conn.commit()
                    conn.close()
                    st.success("¡Producto actualizado y guardado!")
                    st.rerun()

    with tab_p3:
        with st.form("form_nuevo_prod"):
            np_cod = st.text_input("Código (Ej. 759105)")
            np_desc = st.text_input("Descripción de la Fruta")
            np_maneja = st.selectbox("¿Maneja Calibre?", ["Sí", "No"])
            np_calidad = st.selectbox("Calidad", ["Premium", "Con detalle", "A granel"])
            np_emp = st.number_input("Empaque en Kg por Caja", min_value=0.01, value=19.0)
            np_cos = st.number_input("Costo por Caja ($)", min_value=0.0, value=45.0)
            np_pre = st.number_input("Precio por Caja ($)", min_value=0.0, value=65.0)

            if st.form_submit_button("Guardar Nuevo Producto"):
                if np_cod and np_desc:
                    p_kg = round(np_pre / np_emp, 2) if np_emp > 0 else 0.0
                    mrg = round(((np_pre - np_cos) / np_pre * 100), 1) if np_pre > 0 else 0.0
                    
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO matriz_precios (codigo, barra, descripcion, maneja_calibre, clasificacion_calidad, empaque_kg, costo_caja, precio_caja, precio_kg, margen_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (np_cod, np_cod, np_desc.upper(), np_maneja, np_calidad, np_emp, np_cos, np_pre, p_kg, mrg))
                    conn.commit()
                    conn.close()
                    st.success("¡Producto creado y guardado!")
                    st.rerun()

# ---------------------------------------------------------
# 7. KARDEX & TRAZABILIDAD DE LOTES (FIFO)
# ---------------------------------------------------------
elif menu.startswith("7."):
    st.title("🔄 Kardex Diario y Trazabilidad de Lotes (Regla FIFO)")
    conn = sqlite3.connect(DB_NAME)
    df_kardex = pd.read_sql("SELECT * FROM movimientos_inventario ORDER BY id DESC", conn)
    conn.close()

    if not df_kardex.empty:
        st.dataframe(df_kardex, use_container_width=True)
        csv_k = df_kardex.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Kardex en Excel (CSV)", csv_k, "kardex_frumix.csv", "text/csv")
    else:
        st.info("No hay movimientos en el kardex.")

# ---------------------------------------------------------
# 8. CARTERA OFICIAL DE CLIENTES (PERMANENTE Y EDITABLE)
# ---------------------------------------------------------
elif menu.startswith("8."):
    st.title("🏢 Cartera Oficial de Clientes (Manual, Editable y con Sucursales)")
    st.write("Tu directorio oficial de clientes guardado permanentemente en el sistema.")

    tab_c1, tab_c2, tab_c3 = st.tabs(["📋 Directorio Oficial", "✏️ Editar Sucursal / Cliente", "➕ Registrar Cliente o Sucursal"])

    with tab_c1:
        df_cli = get_clientes_cache()
        if not df_cli.empty:
            st.dataframe(df_cli, use_container_width=True)
            
            csv_cli = df_cli.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Cartera de Clientes en Excel (CSV)", csv_cli, "clientes_frumix.csv", "text/csv")

            st.markdown("---")
            id_cli_del = st.selectbox("Seleccione ID de registro a eliminar:", df_cli["id"].tolist())
            if st.button("🗑️ Eliminar Sucursal"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clientes WHERE id = ?", (int(id_cli_del),))
                conn.commit()
                conn.close()
                st.success("¡Sucursal eliminada de la cartera!")
                st.rerun()
        else:
            st.info("Tu cartera de clientes está vacía.")

    with tab_c2:
        df_cli_ed = get_clientes_cache()
        if not df_cli_ed.empty:
            id_edc = st.selectbox("Seleccione ID de Cliente para Editar:", df_cli_ed["id"].tolist(), key="ed_cli_c")
            row_ec = df_cli_ed[df_cli_ed["id"] == id_edc].iloc[0]

            with st.form("form_edit_cliente_oficial"):
                eo_matriz = st.text_input("Empresa Matriz", value=row_ec["matriz"])
                eo_suc = st.text_input("Sucursal", value=row_ec["sucursal"])
                eo_seg = st.selectbox("Segmento", ["Supermercados", "Mayorista", "Minimarket", "HORECA", "Comercial"], index=0)
                eo_tarifa = st.selectbox("Tarifa", ["Tarifa A (Comprador regular)", "Tarifa B (Comprador medio)", "Tarifa C (Comprador esporádico)"])
                eo_dupla = st.selectbox("Dupla Comercial", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
                eo_tel = st.text_input("Teléfono", value=row_ec["telefono"])
                eo_cont = st.text_input("Contacto", value=row_ec["contacto"])
                eo_dias = st.number_input("Días de Crédito", min_value=1, value=int(row_ec["limite_credito_dias"]))
                eo_monto = st.number_input("Límite de Crédito ($)", min_value=0.0, value=float(row_ec["limite_credito_dolares"]))

                if st.form_submit_button("💾 Guardar Cambios"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE clientes 
                        SET matriz = ?, sucursal = ?, segmento = ?, tarifa = ?, dupla = ?, telefono = ?, contacto = ?, limite_credito_dias = ?, limite_credito_dolares = ?
                        WHERE id = ?
                    """, (eo_matriz.upper(), eo_suc.upper(), eo_seg, eo_tarifa, eo_dupla, eo_tel, eo_cont, int(eo_dias), eo_monto, int(id_edc)))
                    conn.commit()
                    conn.close()
                    st.success("¡Cliente actualizado y guardado permanentemente!")
                    st.rerun()

    with tab_c3:
        with st.form("form_nuevo_cliente_manual"):
            st.subheader("Añadir Nueva Empresa Matriz o Sucursal")
            nc_mat = st.text_input("Empresa Matriz (Ej. CENTRAL MADERENSE)")
            nc_suc = st.text_input("Nombre de la Sucursal (Ej. Sucursal Este / Principal)")
            nc_seg = st.selectbox("Segmento", ["Supermercados", "Mayorista", "Minimarket", "HORECA", "Comercial"])
            nc_tarifa = st.selectbox("Tarifa Oficial", ["Tarifa A (Comprador regular)", "Tarifa B (Comprador medio)", "Tarifa C (Comprador esporádico)"])
            nc_dupla = st.selectbox("Dupla Asignada", ["Ladimir (Occidente)", "Tufic (Capital)", "Wilmer (Oriente)"])
            nc_tel = st.text_input("Teléfono", value="+58 412-")
            nc_cont = st.text_input("Persona de Contacto / Comprador")
            nc_dias = st.number_input("Días de Crédito", min_value=1, value=15)
            nc_monto = st.number_input("Límite de Crédito ($)", min_value=0.0, value=15000.0)

            if st.form_submit_button("💾 Guardar Permanentemente en Cartera de Clientes"):
                if nc_mat and nc_suc:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (matriz, sucursal, segmento, tarifa, dupla, telefono, contacto, limite_credito_dias, limite_credito_dolares, ultimo_pedido)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nc_mat.upper(), nc_suc.upper(), nc_seg, nc_tarifa, nc_dupla, nc_tel, nc_cont, int(nc_dias), nc_monto, str(get_today_vz())))
                    conn.commit()
                    conn.close()
                    
                    registrar_auditoria(st.session_state.usuario, st.session_state.rol, "NUEVO CLIENTE", f"Se registró a {nc_mat} - {nc_suc} en BD permanente.")
                    st.success("¡Cliente y sucursal guardados con éxito y de forma permanente!")
                    st.rerun()
                else:
                    st.error("Por favor complete Matriz y Sucursal.")

# ---------------------------------------------------------
# 9. HISTORIAL DE COMPRAS DE CLIENTES
# ---------------------------------------------------------
elif menu.startswith("9."):
    st.title("🛍️ Historial de Compras de Clientes")
    df_cli_h = get_clientes_cache()
    if not df_cli_h.empty:
        lista_mat_hist = df_cli_h["matriz"].unique().tolist()
        cliente_sel_hist = st.selectbox("Seleccionar Empresa Matriz:", lista_mat_hist)

        conn = sqlite3.connect(DB_NAME)
        df_ped_hist = pd.read_sql("SELECT * FROM pedidos WHERE cliente = ?", conn, params=(cliente_sel_hist,))
        conn.close()

        if not df_ped_hist.empty:
            st.dataframe(df_ped_hist[["nro_pedido", "sucursal", "fecha_pedido", "monto_total", "atendido_por", "estatus_despacho"]], use_container_width=True)
        else:
            st.info(f"El cliente {cliente_sel_hist} no registra compras previas.")
    else:
        st.info("No hay clientes en la cartera.")

# ---------------------------------------------------------
# 10. MÉTRICAS Y REPORTES
# ---------------------------------------------------------
elif menu.startswith("10."):
    st.title("📈 Métricas y Reportes Comerciales")
    conn = sqlite3.connect(DB_NAME)
    df_p = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True)
        csv_rep = df_p.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte en Excel (CSV)", csv_rep, "reporte_ventas.csv", "text/csv")
    else:
        st.info("No hay pedidos registrados.")

# ---------------------------------------------------------
# 11. EMBUDO DE VENTAS
# ---------------------------------------------------------
elif menu.startswith("11."):
    st.title("🎯 Embudo de Ventas B2B")
    conn = sqlite3.connect(DB_NAME)
    df_funnel = pd.read_sql("SELECT * FROM embudo_ventas", conn) if "embudo_ventas" in [row[0] for row in sqlite3.connect(DB_NAME).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else pd.DataFrame()
    conn.close()
    if not df_funnel.empty:
        st.dataframe(df_funnel, use_container_width=True)
    else:
        st.info("No hay oportunidades registradas en el embudo de ventas.")

# ---------------------------------------------------------
# 12. COBRANZA, GESTIÓN, EDICIÓN Y ELIMINACIÓN DE FACTURAS
# ---------------------------------------------------------
elif menu.startswith("12."):
    st.title("💰 Departamento de Cobranza - Cuentas por Cobrar, Edición y Anulación")
    st.write("Visualiza, registra abonos, **edita o elimina facturas** de forma directa.")

    conn = sqlite3.connect(DB_NAME)
    df_cob = pd.read_sql("SELECT * FROM cobranza", conn)
    conn.close()

    if not df_cob.empty:
        tab_cxc1, tab_cxc2, tab_cxc3 = st.tabs(["📋 Listado General y Pagos", "✏️ Editar Factura", "🗑️ Anular / Eliminar Factura"])

        with tab_cxc1:
            st.dataframe(df_cob, use_container_width=True)
            csv_cxc = df_cob.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar CxC en Excel (CSV)", csv_cxc, "cxc_frumix.csv", "text/csv")
            
            st.markdown("---")
            st.subheader("💵 Registrar Pago / Abono de Factura")
            with st.form("form_pago_cxc"):
                fac_pendientes = df_cob[df_cob["estatus_pago"] != "Pagado"]["nro_factura"].tolist() if not df_cob[df_cob["estatus_pago"] != "Pagado"].empty else []
                fac_sel = st.selectbox("Factura Pendiente", fac_pendientes)
                if fac_sel:
                    row_f = df_cob[df_cob["nro_factura"] == fac_sel].iloc[0]
                    pendiente = row_f["monto_factura"] - row_f["monto_pagado"]
                    st.info(f"Pendiente: **${pendiente:,.2f} USD**")
                    pago_val = st.number_input("Monto a Abonar ($)", min_value=0.01, max_value=float(pendiente), value=float(pendiente))
                    
                    if st.form_submit_button("Registrar Abono"):
                        nuevo_pagado = row_f["monto_pagado"] + pago_val
                        nuevo_est = "Pagado" if nuevo_pagado >= row_f["monto_factura"] else "Parcial"
                        
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE cobranza SET monto_pagado = ?, estatus_pago = ? WHERE nro_factura = ?", (nuevo_pagado, nuevo_est, fac_sel))
                        conn.commit()
                        conn.close()
                        st.success("¡Pago registrado con éxito!")
                        st.rerun()

        with tab_cxc2:
            st.subheader("✏️ Editar Datos de Factura Existente")
            fac_ids = df_cob["id"].tolist()
            sel_fac_id = st.selectbox("Seleccione ID de Factura a Modificar:", fac_ids, key="sel_edit_fac")
            row_edit_fac = df_cob[df_cob["id"] == sel_fac_id].iloc[0]

            with st.form("form_editar_factura_real"):
                ed_nro_fac = st.text_input("Nro. de Factura", value=row_edit_fac["nro_factura"])
                ed_cli_fac = st.text_input("Cliente Matriz", value=row_edit_fac["cliente"])
                ed_monto_fac = st.number_input("Monto Total de la Factura ($)", min_value=0.0, value=float(row_edit_fac["monto_factura"]))
                ed_est_fac = st.selectbox("Estatus de Pago", ["Pendiente", "Parcial", "Pagado"], index=["Pendiente", "Parcial", "Pagado"].index(row_edit_fac["estatus_pago"]) if row_edit_fac["estatus_pago"] in ["Pendiente", "Parcial", "Pagado"] else 0)

                if st.form_submit_button("💾 Guardar Cambios en Factura"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE cobranza 
                        SET nro_factura = ?, cliente = ?, monto_factura = ?, estatus_pago = ?
                        WHERE id = ?
                    """, (ed_nro_fac.upper(), ed_cli_fac.upper(), ed_monto_fac, ed_est_fac, int(sel_fac_id)))
                    conn.commit()
                    conn.close()
                    st.success("¡Factura actualizada con éxito!")
                    st.rerun()

        with tab_cxc3:
            st.subheader("🗑️ Eliminar / Anular Factura del Sistema")
            fac_del_id = st.selectbox("Seleccione ID de Factura a Eliminar:", df_cob["id"].tolist(), key="sel_del_fac")
            if st.button("🗑️ Confirmar Eliminación de Factura"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cobranza WHERE id = ?", (int(fac_del_id),))
                conn.commit()
                conn.close()
                st.success("¡Factura eliminada de Cuentas por Cobrar!")
                st.rerun()
    else:
        st.info("No hay registros de cobranza activos.")

# ---------------------------------------------------------
# 13. LOGÍSTICA Y DESPACHOS
# ---------------------------------------------------------
elif menu.startswith("13."):
    st.title("🚚 Logística y Estatus de Despachos")
    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()
    if not df_peds.empty:
        st.dataframe(df_peds, use_container_width=True)
    else:
        st.info("No hay pedidos registrados para logística.")

# ---------------------------------------------------------
# 14. MATRIZ DINÁMICA DE PRECIOS
# ---------------------------------------------------------
elif menu.startswith("14."):
    st.title("💲 Matriz de Precios - Conversión de Caja a Kilogramo")
    df_m = get_catalogo_cache()
    if not df_m.empty:
        df_m["precio_kg"] = df_m.apply(lambda r: round(r["precio_caja"] / r["empaque_kg"], 2) if r["empaque_kg"] > 0 else 0.0, axis=1)
        st.dataframe(df_m[["codigo", "descripcion", "maneja_calibre", "clasificacion_calidad", "empaque_kg", "costo_caja", "precio_caja", "precio_kg", "margen_pct"]], use_container_width=True)
    else:
        st.info("No hay productos en el catálogo para mostrar la matriz.")

# ---------------------------------------------------------
# 15. CONTROL DE MERMAS & PÉRDIDAS
# ---------------------------------------------------------
elif menu.startswith("15."):
    st.title("🗑️ Control de Mermas y Pérdidas (Resta Stock)")
    tab_m1, tab_m2 = st.tabs(["📋 Historial de Mermas", "➕ Registrar Nueva Merma"])

    with tab_m1:
        conn = sqlite3.connect(DB_NAME)
        df_mer = pd.read_sql("SELECT * FROM mermas", conn)
        conn.close()
        if not df_mer.empty:
            st.dataframe(df_mer, use_container_width=True)
            csv_m = df_mer.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Mermas en Excel (CSV)", csv_m, "mermas_frumix.csv", "text/csv")
        else:
            st.info("No hay mermas registradas.")

    with tab_m2:
        df_inv_m = get_inventario_cache()
        df_inv_stk = df_inv_m[df_inv_m["stock_cajas"] > 0] if not df_inv_m.empty else pd.DataFrame()
        if not df_inv_stk.empty:
            with st.form("form_merma"):
                op_lotes = [f"ID: {r['id']} | Lote: {r['lote']} | {r['producto']} ({r['calibre']}) - Stock: {r['stock_cajas']}" for _, r in df_inv_stk.iterrows()]
                sel_lote_m = st.selectbox("Seleccionar Lote", op_lotes)
                id_inv_m = int(sel_lote_m.split("|")[0].replace("ID:", "").strip())
                row_m = df_inv_stk[df_inv_stk["id"] == id_inv_m].iloc[0]

                cajas_m = st.number_input("Cajas a Dar de Baja", min_value=1.0, max_value=float(row_m["stock_cajas"]), value=2.0)
                motivo_m = st.text_input("Motivo de la Merma")

                if st.form_submit_button("Confirmar Merma"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("BEGIN TRANSACTION;")
                    
                    perdida = cajas_m * row_m["costo_unitario_caja"]
                    cursor.execute("INSERT INTO mermas (lote, producto, calibre, cantidad_perdida, costo_unitario, perdida_monetaria, motivo, fecha_merma) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (row_m["lote"], row_m["producto"], row_m["calibre"], cajas_m, row_m["costo_unitario_caja"], perdida, motivo_m, str(get_today_vz())))
                    
                    nuevo_stk = max(0.0, row_m["stock_cajas"] - cajas_m)
                    cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stk, id_inv_m))
                    
                    cursor.execute("INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable) VALUES (?, ?, ?, 'SALIDA MERMA', ?, ?, ?, ?)",
                                   (row_m["lote"], row_m["producto"], row_m["calibre"], cajas_m, f"Merma: {motivo_m}", str(get_today_vz()), st.session_state.rol))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Merma registrada y stock descontado!")
                    st.rerun()
        else:
            st.warning("No hay inventario con stock disponible para generar mermas.")

# ---------------------------------------------------------
# 16. MÓDULO DE DEVOLUCIONES (MERMA O REINGRESO)
# ---------------------------------------------------------
elif menu.startswith("16."):
    st.title("↩️ Módulo de Devoluciones de Clientes (Destino Merma o Reingreso)")
    st.write("Registra devoluciones indicando si el producto se descarta como pérdida o si regresa a las cámaras de frío.")

    tab_d1, tab_d2 = st.tabs(["📋 Historial de Devoluciones", "➕ Registrar Nueva Devolución"])

    with tab_d1:
        conn = sqlite3.connect(DB_NAME)
        df_dev = pd.read_sql("SELECT * FROM devoluciones", conn)
        conn.close()
        if not df_dev.empty:
            st.dataframe(df_dev, use_container_width=True)
            csv_d = df_dev.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Devoluciones en Excel (CSV)", csv_d, "devoluciones_frumix.csv", "text/csv")
        else:
            st.info("No hay devoluciones registradas.")

    with tab_d2:
        df_cli_d = get_clientes_cache()
        if not df_cli_d.empty:
            with st.form("form_devolucion"):
                mat_dev = st.selectbox("Cliente Matriz", df_cli_d["matriz"].unique().tolist())
                prod_dev = st.text_input("Producto Devuelto")
                cal_dev = st.text_input("Calibre (si aplica)", value="N/A")
                cant_dev = st.number_input("Cantidad de Cajas Devueltas", min_value=1.0, value=5.0)
                motivo_dev = st.text_input("Motivo de la Devolución")
                destino_dev = st.selectbox("Destino de la Fruta", ["Enviar a Merma (Pérdida)", "Reingresar a Inventario en Frío (Stock Disponible)"])

                if st.form_submit_button("💾 Procesar Devolución"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO devoluciones (nro_pedido, cliente, sucursal, producto, calibre, cantidad_devuelta, motivo_devolucion, destino_accion, fecha_devolucion)
                        VALUES ('DEV-MANUAL', ?, 'Principal', ?, ?, ?, ?, ?, ?)
                    """, (mat_dev, prod_dev.upper(), cal_dev.upper(), cant_dev, motivo_dev, destino_dev, str(get_today_vz())))

                    if "Reingresar" in destino_dev:
                        cursor.execute("""
                            INSERT INTO inventario (lote, producto, calibre, stock_cajas, costo_unitario_caja, fecha_ingreso)
                            VALUES ('LOTE-DEV', ?, ?, ?, 45.0, ?)
                        """, (prod_dev.upper(), cal_dev.upper(), cant_dev, str(get_today_vz())))
                    
                    conn.commit()
                    conn.close()
                    st.success("¡Devolución procesada con éxito!")
                    st.rerun()
        else:
            st.warning("Debe registrar clientes antes de procesar devoluciones.")

# ---------------------------------------------------------
# 17. HISTORIAL COMPLETO DE PEDIDOS, EDICIÓN & REVERSIÓN
# ---------------------------------------------------------
elif menu.startswith("17."):
    st.title("📋 Historial de Pedidos, Edición y Eliminación con Reversión")
    st.write("Visualiza tus pedidos, edita sus datos generales o elimínalos para que el stock regrese automáticamente a cámaras.")

    conn = sqlite3.connect(DB_NAME)
    df_peds = pd.read_sql("SELECT * FROM pedidos", conn)
    conn.close()

    if not df_peds.empty:
        tab_p_ed1, tab_p_ed2, tab_p_ed3 = st.tabs(["📋 Listado de Pedidos", "✏️ Editar Datos de Pedido", "🗑️ Anular Pedido y Reintegrar Stock"])

        with tab_p_ed1:
            st.dataframe(df_peds, use_container_width=True)
            csv_p = df_peds.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Pedidos en Excel (CSV)", csv_p, "pedidos_frumix.csv", "text/csv")

        with tab_p_ed2:
            st.subheader("✏️ Editar Pedido Existente")
            id_sel_ped_ed = st.selectbox("Seleccione ID de Pedido a Editar:", df_peds["id"].tolist(), key="sel_ed_ped_real")
            row_p_ed = df_peds[df_peds["id"] == id_sel_ped_ed].iloc[0]

            with st.form("form_editar_pedido_datos"):
                ed_nro_p = st.text_input("Número de Pedido", value=row_p_ed["nro_pedido"])
                ed_cli_p = st.text_input("Cliente", value=row_p_ed["cliente"])
                ed_suc_p = st.text_input("Sucursal", value=row_p_ed["sucursal"])
                ed_est_p = st.selectbox("Estatus de Despacho", ["Reservado / En Espera", "Despachado", "Cancelado"], index=0)

                if st.form_submit_button("💾 Guardar Cambios del Pedido"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE pedidos 
                        SET nro_pedido = ?, cliente = ?, sucursal = ?, estatus_despacho = ?
                        WHERE id = ?
                    """, (ed_nro_p, ed_cli_p.upper(), ed_suc_p.upper(), ed_est_p, int(id_sel_ped_ed)))
                    conn.commit()
                    conn.close()
                    st.success("¡Pedido actualizado exitosamente!")
                    st.rerun()

        with tab_p_ed3:
            st.subheader("🗑️ Cancelar / Eliminar Pedido y Reintegrar Stock")
            pedido_id_del = st.selectbox("Seleccione ID de Pedido a Anular/Eliminar:", df_peds["id"].tolist(), key="sel_del_ped_real")
            
            if st.button("🗑️ Anular Pedido y Devolver Stock a Cámaras"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("BEGIN TRANSACTION;")

                    cursor.execute("SELECT nro_pedido, detalle_json FROM pedidos WHERE id = ?", (int(pedido_id_del),))
                    res_ped = cursor.fetchone()
                    
                    if res_ped:
                        nro_ped_del = res_ped[0]
                        detalle_json_str = res_ped[1]
                        
                        if detalle_json_str:
                            items_cancelados = json.loads(detalle_json_str)
                            for item in items_cancelados:
                                inv_id = item["inventario_id"]
                                cajas_dev = item["cajas"]
                                
                                cursor.execute("SELECT stock_cajas FROM inventario WHERE id = ?", (inv_id,))
                                row_stk = cursor.fetchone()
                                
                                if row_stk:
                                    nuevo_stock = row_stk[0] + cajas_dev
                                    cursor.execute("UPDATE inventario SET stock_cajas = ? WHERE id = ?", (nuevo_stock, inv_id))
                                else:
                                    cursor.execute("""
                                        INSERT INTO inventario (lote, producto, calibre, stock_cajas, costo_unitario_caja, fecha_ingreso)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (item["lote"], item["producto"], item["calibre"], cajas_dev, item["costo_unitario"], str(get_today_vz())))

                                cursor.execute("""
                                    INSERT INTO movimientos_inventario (lote, producto, calibre, tipo_movimiento, cantidad, motivo, fecha_movimiento, responsable)
                                    VALUES (?, ?, ?, 'REINGRESO ANULACIÓN', ?, ?, ?, ?)
                                """, (item["lote"], item["producto"], item["calibre"], cajas_dev, f"Anulación Pedido {nro_ped_del}", str(get_today_vz()), st.session_state.rol))

                        cursor.execute("DELETE FROM pedidos WHERE id = ?", (int(pedido_id_del),))
                        conn.commit()
                        conn.close()

                        registrar_auditoria(st.session_state.usuario, st.session_state.rol, "ANULACIÓN DE PEDIDO", f"Pedido {nro_ped_del} anulado y stock reingresado a cámaras.")
                        st.success("¡Pedido anulado con éxito y stock devuelto a cámaras!")
                        st.rerun()

                except Exception as e:
                    if 'conn' in locals():
                        conn.rollback()
                        conn.close()
                    st.error(f"Error al anular el pedido: {e}")
    else:
        st.info("No hay pedidos registrados en el sistema.")
