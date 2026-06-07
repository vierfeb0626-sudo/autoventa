from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from datetime import datetime
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# =========================
# STOCK
# =========================

stock = {}

combos = {
    "COMBO_MEXICO": [
        "NETFLIX",
        "DISNEY",
        "SPOTIFY"
    ]
}

# =========================
# ARCHIVOS
# =========================

def cargar_stock():
    global stock
    if os.path.exists("stock.json"):
        with open("stock.json", "r", encoding="utf-8") as f:
            stock.update(json.load(f))

def guardar_stock():
    with open("stock.json", "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4, ensure_ascii=False)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    keyboard = [
        ["🛒 Comprar"],
        ["📦 Servicios"]
    ]

    mensaje = f"""
👋 Bienvenido a VELTRIX

🆔 Tu ID: {user_id}

💰 Usa este ID para recargar saldo

Selecciona una opción:
"""

    await update.message.reply_text(
        mensaje,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

# =========================
# MENSAJES
# =========================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🛒 Comprar":

        keyboard = [
            ["Netflix"],
            ["Disney"],
            ["Spotify"],
            ["Combo México"]
        ]

        await update.message.reply_text(
            "📦 Selecciona servicio:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    elif text == "📦 Servicios":

        if not stock:
            await update.message.reply_text("❌ No hay servicios aún")
            return

        lista = "\n".join([f"• {s}" for s in stock.keys()])

        await update.message.reply_text(
            f"📦 SERVICIOS DISPONIBLES\n\n{lista}"
        )

    else:
        servicio = text.upper()

        if servicio == "COMBO MÉXICO":
            await entregar(update, combos["COMBO_MEXICO"], "Combo México")
        else:
            await entregar(update, [servicio], servicio)

# =========================
# ENTREGAR
# =========================

async def entregar(update, servicios, nombre):

    cuentas = []

    for servicio in servicios:

        if servicio not in stock or len(stock[servicio]) == 0:
            await update.message.reply_text(
                f"❌ Sin stock en {servicio}"
            )
            return

    for servicio in servicios:
        cuenta = stock[servicio].pop(0)
        cuentas.append(cuenta)

    guardar_stock()

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    datos = "\n".join(cuentas)

    mensaje = f"""
📦 FICHA DE ENTREGA

🛒 Servicio:
{nombre}

🔐 Datos:
{datos}

⚠️ REGLAS
• No modificar datos
• No cambiar contraseña
• No realizar compras

🕒 Fecha:
{fecha}
"""

    with open("ventas.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{update.effective_user.id} | {nombre} | {fecha}\n"
        )

    await update.message.reply_text(
        mensaje,
        protect_content=True
    )

# =========================
# SET STOCK
# =========================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No autorizado")
        return

    try:
        servicio = context.args[0].upper()
        datos = " ".join(context.args[1:])

        # 🔥 CREA SERVICIO AUTOMÁTICO
        if servicio not in stock:
            stock[servicio] = []

        stock[servicio].append(datos)
        guardar_stock()

        await update.message.reply_text(
            f"✅ Cuenta agregada a {servicio}"
        )

    except:
        await update.message.reply_text(
            "Uso:\n/setstock NETFLIX correo:contra:perfil"
        )

# =========================
# VER STOCK
# =========================

async def verstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    texto = "📦 STOCK ACTUAL\n\n"

    for servicio in stock:
        cantidad = len(stock[servicio])
        estado = "🟢" if cantidad > 0 else "🔴"

        texto += f"{estado} {servicio}: {cantidad}\n"

    await update.message.reply_text(texto)

# =========================
# MAIN
# =========================

def main():

    cargar_stock()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setstock", setstock))
    app.add_handler(CommandHandler("verstock", verstock))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes)
    )

    print("🤖 BOT VELTRIX ONLINE")
    app.run_polling()

# =========================

if __name__ == "__main__":
    main()
