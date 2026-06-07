from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import json
import os
from datetime import datetime

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# =========================
# BASE DE DATOS
# =========================

stock = {}
usuarios = {}
tienda = {}

# =========================
# ARCHIVOS
# =========================

def cargar_datos():
    global stock, usuarios, tienda

    if os.path.exists("stock.json"):
        with open("stock.json", "r", encoding="utf-8") as f:
            stock.update(json.load(f))

    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r", encoding="utf-8") as f:
            usuarios.update(json.load(f))

    if os.path.exists("tienda.json"):
        with open("tienda.json", "r", encoding="utf-8") as f:
            tienda.update(json.load(f))


def guardar_stock():
    with open("stock.json", "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4, ensure_ascii=False)


def guardar_usuarios():
    with open("usuarios.json", "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


def guardar_tienda():
    with open("tienda.json", "w", encoding="utf-8") as f:
        json.dump(tienda, f, indent=4, ensure_ascii=False)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if user_id not in usuarios:
        usuarios[user_id] = {"saldo": 0}
        guardar_usuarios()

    keyboard = [
        ["🛒 Comprar"],
        ["💰 Mi saldo"],
        ["🏪 Tienda"]
    ]

    await update.message.reply_text(
        f"👋 Bienvenido\n\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Saldo: {usuarios[user_id]['saldo']}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# MENSAJES
# =========================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = str(update.effective_user.id)

    # -------------------------
    # TIENDA
    # -------------------------
    if text == "🏪 Tienda":

        if not tienda:
            await update.message.reply_text("❌ Sin tienda disponible")
            return

        lista = "\n".join(
            [f"• {s.replace('_',' ').title()} - ${p}" for s, p in tienda.items()]
        )

        await update.message.reply_text(f"🏪 TIENDA\n\n{lista}")
        return

    # -------------------------
    # COMPRAR
    # -------------------------
    if text == "🛒 Comprar":

        if not stock:
            await update.message.reply_text("❌ No hay servicios")
            return

        keyboard = []
        for servicio in stock.keys():
            keyboard.append([servicio.replace("_", " ").title()])

        await update.message.reply_text(
            "📦 Selecciona servicio:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # -------------------------
    # SALDO
    # -------------------------
    if text == "💰 Mi saldo":
        saldo = usuarios.get(user_id, {}).get("saldo", 0)
        await update.message.reply_text(f"💰 Saldo: {saldo}")
        return

    # -------------------------
    # SERVICIO SELECCIONADO
    # -------------------------
    servicio = text.upper().replace(" ", "_")

    if servicio in stock:

        keyboard = [
            ["👤 Perfiles disponibles"],
            ["📦 Cuentas completas"]
        ]

        context.user_data["servicio"] = servicio

        await update.message.reply_text(
            f"📦 {servicio.replace('_',' ')}\nSelecciona tipo:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # -------------------------
    # SUBMENÚ
    # -------------------------
    if text in ["👤 Perfiles disponibles", "📦 Cuentas completas"]:

        servicio = context.user_data.get("servicio")

        if not servicio or servicio not in stock:
            await update.message.reply_text("❌ Servicio no seleccionado")
            return

        await entregar(update, servicio)
        return

# =========================
# FORMATO CUENTA
# =========================

def formatear_cuenta(cuenta):

    try:
        partes = cuenta.split("_")

        correo = partes[0]
        contra = partes[1]
        perfil = partes[3] if len(partes) > 3 else "N/A"

        return (
            f"📧 Correo: {correo}\n"
            f"🔑 Contraseña: {contra}\n"
            f"👤 Perfil: {perfil}"
        )
    except:
        return cuenta

# =========================
# ENTREGAR
# =========================

async def entregar(update: Update, servicio):

    user_id = str(update.effective_user.id)

    if usuarios[user_id]["saldo"] <= 0:
        await update.message.reply_text("❌ Sin saldo")
        return

    if servicio not in stock or len(stock[servicio]) == 0:
        await update.message.reply_text("❌ Sin stock")
        return

    cuenta = stock[servicio].pop(0)
    guardar_stock()

    usuarios[user_id]["saldo"] -= 1
    guardar_usuarios()

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    mensaje = f"""
📦 ENTREGA

🛒 Servicio:
{servicio.replace('_',' ')}

🔐 Datos:
{formatear_cuenta(cuenta)}

🕒 Fecha:
{fecha}
"""

    with open("ventas.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id} | {servicio} | {fecha}\n")

    await update.message.reply_text(mensaje)

# =========================
# ADMIN: STOCK
# =========================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0].upper()
        datos = " ".join(context.args[1:])

        if servicio not in stock:
            stock[servicio] = []

        stock[servicio].append(datos)
        guardar_stock()

        await update.message.reply_text("✅ Agregado")
    except:
        await update.message.reply_text("Uso: /setstock SERVICIO datos")

# =========================
# ADMIN: TIENDA
# =========================

async def addtienda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0].upper()
        precio = context.args[1]

        tienda[servicio] = precio
        guardar_tienda()

        await update.message.reply_text(f"✅ {servicio} agregado a tienda")
    except:
        await update.message.reply_text("Uso: /addtienda SERVICIO PRECIO")

# =========================
# ADMIN: SALDO
# =========================

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = context.args[0]
        monto = int(context.args[1])

        if user_id not in usuarios:
            usuarios[user_id] = {"saldo": 0}

        usuarios[user_id]["saldo"] += monto
        guardar_usuarios()

        await update.message.reply_text("✅ saldo agregado")
    except:
        await update.message.reply_text("Uso: /addsaldo ID MONTO")

# =========================
# MAIN
# =========================

def main():

    cargar_datos()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setstock", setstock))
    app.add_handler(CommandHandler("addsaldo", addsaldo))
    app.add_handler(CommandHandler("addtienda", addtienda))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

    print("🤖 BOT ONLINE")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
