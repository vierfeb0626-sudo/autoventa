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

# =========================
# ARCHIVOS
# =========================

def cargar_datos():
    global stock, usuarios

    if os.path.exists("stock.json"):
        with open("stock.json", "r", encoding="utf-8") as f:
            stock.update(json.load(f))

    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r", encoding="utf-8") as f:
            usuarios.update(json.load(f))


def guardar_stock():
    with open("stock.json", "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4, ensure_ascii=False)


def guardar_usuarios():
    with open("usuarios.json", "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

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
        ["📦 Servicios"]
    ]

    await update.message.reply_text(
        f"👋 Bienvenido a VELTRIX\n\n"
        f"🆔 Tu ID: {user_id}\n"
        f"💰 Saldo: {usuarios[user_id]['saldo']}\n\n"
        f"Usa tu ID para recargar saldo",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# MENSAJES
# =========================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = str(update.effective_user.id)

    if text == "🛒 Comprar":

        if not stock:
            await update.message.reply_text("❌ No hay servicios")
            return

        keyboard = []

        for servicio in stock.keys():
            nombre = servicio.replace("_", " ").title()
            keyboard.append([nombre])

        await update.message.reply_text(
            "📦 Selecciona servicio:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "💰 Mi saldo":

        saldo = usuarios.get(user_id, {}).get("saldo", 0)

        await update.message.reply_text(
            f"💰 Tu saldo actual es: {saldo}"
        )

    elif text == "📦 Servicios":

        if not stock:
            await update.message.reply_text("❌ No hay servicios")
            return

        lista = "\n".join([
            f"• {s.replace('_',' ').title()} ({len(stock[s])})"
            for s in stock
        ])

        await update.message.reply_text(
            f"📦 SERVICIOS DISPONIBLES\n\n{lista}"
        )

    else:

        servicio = text.upper().replace(" ", "_")
        await entregar(update, servicio)

# =========================
# FORMATEAR CUENTA
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

    if user_id not in usuarios:
        usuarios[user_id] = {"saldo": 0}

    # SIN SALDO
    if usuarios[user_id]["saldo"] <= 0:
        await update.message.reply_text(
            "❌ No tienes saldo\nContacta al admin 💰"
        )
        return

    # SIN STOCK
    if servicio not in stock or len(stock[servicio]) == 0:
        await update.message.reply_text(
            f"❌ Sin stock en {servicio}"
        )
        return

    # ENTREGAR
    cuenta = stock[servicio].pop(0)
    guardar_stock()

    usuarios[user_id]["saldo"] -= 1
    guardar_usuarios()

    datos_formateados = formatear_cuenta(cuenta)

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    mensaje = f"""
📦 FICHA DE ENTREGA

🛒 Servicio:
{servicio.replace('_',' ')}

🔐 Datos:
{datos_formateados}

⚠️ REGLAS
• No cambiar contraseña
• No modificar cuenta

🕒 Fecha:
{fecha}
"""

    with open("ventas.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id} | {servicio} | {fecha}\n")

    await update.message.reply_text(mensaje)

# =========================
# ADMIN
# =========================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No autorizado")
        return

    try:
        servicio = context.args[0].upper()
        datos = " ".join(context.args[1:])

        if servicio not in stock:
            stock[servicio] = []

        stock[servicio].append(datos)
        guardar_stock()

        await update.message.reply_text(
            f"✅ Agregado a {servicio}"
        )

    except:
        await update.message.reply_text(
            "Uso:\n/setstock NETFLIX correo_contra_perfil"
        )


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

        await update.message.reply_text(
            f"✅ Saldo agregado a {user_id}: {monto}"
        )

    except:
        await update.message.reply_text(
            "Uso:\n/addsaldo ID 10"
        )


async def verstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    texto = "📦 STOCK\n\n"

    for s in stock:
        texto += f"{s}: {len(stock[s])}\n"

    await update.message.reply_text(texto)

# =========================
# MAIN
# =========================

def main():

    cargar_datos()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setstock", setstock))
    app.add_handler(CommandHandler("addsaldo", addsaldo))
    app.add_handler(CommandHandler("verstock", verstock))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes)
    )

    print("🤖 BOT VELTRIX ONLINE")
    app.run_polling(drop_pending_updates=True)

# =========================

if __name__ == "__main__":
    main()
