import logging
import json
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# =========================
# DATA
# =========================

users = {}
stock = {}
prices = {}
tienda = {}

logging.basicConfig(level=logging.INFO)

# =========================
# JSON
# =========================

def save_data():

    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

    with open("stock.json", "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4)

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=4)

    with open("tienda.json", "w", encoding="utf-8") as f:
        json.dump(tienda, f, indent=4)


def load_data():
    global users, stock, prices, tienda

    try:
        with open("users.json", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = {}

    try:
        with open("stock.json", encoding="utf-8") as f:
            stock = json.load(f)
    except:
        stock = {}

    try:
        with open("prices.json", encoding="utf-8") as f:
            prices = json.load(f)
    except:
        prices = {}

    try:
        with open("tienda.json", encoding="utf-8") as f:
            tienda = json.load(f)
    except:
        tienda = {}

# =========================
# UTILIDADES
# =========================

def get_time():
    now = datetime.now(ZoneInfo("America/Chihuahua"))
    return now.strftime("📆 %d/%m/%Y 🕒 %H:%M")


def parse_account(data):

    try:
        parts = data.split("_")

        return {
            "correo": parts[0],
            "password": parts[1],
            "perfil": parts[2] if len(parts) > 2 else "N/A"
        }

    except:
        return {
            "correo": "ERROR",
            "password": "ERROR",
            "perfil": "ERROR"
        }

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if user_id not in users:
        users[user_id] = {"saldo": 0}
        save_data()

    keyboard = []

    bases = set()

    for servicio in tienda.keys():

        base = servicio.split("_")[0]

        if base not in bases:
            bases.add(base)
            keyboard.append([base])

    keyboard.append(["💰 SALDO", "🛒 TIENDA"])

    await update.message.reply_text(
        f"👋 Bienvenido\n\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Saldo: ${users[user_id]['saldo']}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

# =========================
# TIENDA
# =========================

async def tienda_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not tienda:
        await update.message.reply_text("❌ No hay tienda")
        return

    msg = "🛒 TIENDA\n\n"

    for s, p in tienda.items():
        msg += f"• {s.replace('_',' ')} = ${p}\n"

    await update.message.reply_text(msg)

# =========================
# SALDO
# =========================

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        user_id = str(context.args[0])
        monto = int(context.args[1])

        if user_id not in users:
            users[user_id] = {"saldo": 0}

        users[user_id]["saldo"] += monto

        save_data()

        await update.message.reply_text(
            f"✅ {user_id} = ${users[user_id]['saldo']}"
        )

    except:
        await update.message.reply_text(
            "❌ /addsaldo ID MONTO"
        )

# =========================
# STOCK
# =========================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        servicio = context.args[0].upper()
        data = " ".join(context.args[1:])

        if "_" not in data:
            await update.message.reply_text(
                "❌ Formato inválido"
            )
            return

        if servicio not in stock:
            stock[servicio] = []

        if data in stock[servicio]:
            await update.message.reply_text(
                "⚠️ Ya existe"
            )
            return

        stock[servicio].append(data)

        save_data()

        await update.message.reply_text(
            f"✅ Stock agregado a {servicio}"
        )

    except:
        await update.message.reply_text(
            "❌ /setstock NETFLIX_PERFIL correo_pass_perfil"
        )

# =========================
# PRECIOS
# =========================

async def setprecio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        servicio = context.args[0].upper()
        precio = int(context.args[1])

        prices[servicio] = precio

        save_data()

        await update.message.reply_text(
            f"💰 {servicio} = ${precio}"
        )

    except:
        await update.message.reply_text(
            "❌ /setprecio NETFLIX_PERFIL 20"
        )

# =========================
# TIENDA ADMIN
# =========================

async def addtienda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        servicio = context.args[0].upper()
        precio = context.args[1]

        tienda[servicio] = precio

        save_data()

        await update.message.reply_text(
            "✅ Tienda actualizada"
        )

    except:
        await update.message.reply_text(
            "❌ /addtienda NETFLIX_PERFIL 20"
        )

# =========================
# MENU
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.upper()

    if text == "🛒 TIENDA":
        await tienda_cmd(update, context)
        return

    if text == "💰 SALDO":

        user_id = str(update.effective_user.id)

        if user_id not in users:
            users[user_id] = {"saldo": 0}

        await update.message.reply_text(
            f"💰 Saldo: ${users[user_id]['saldo']}"
        )
        return

    bases = set()

    for servicio in tienda.keys():
        bases.add(servicio.split("_")[0])

    if text in bases:

        context.user_data["base"] = text

        keyboard = [["PERFIL", "COMPLETA"]]

        await update.message.reply_text(
            f"{text}\nSelecciona tipo:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

        return

    if text in ["PERFIL", "COMPLETA"]:

        base = context.user_data.get("base")

        if not base:
            return

        servicio = f"{base}_{text}"

        await comprar(update, servicio)

# =========================
# COMPRAR
# =========================

async def comprar(update, servicio):

    user_id = str(update.effective_user.id)

    if user_id not in users:
        users[user_id] = {"saldo": 0}

    if servicio not in prices:
        await update.message.reply_text("❌ Sin precio")
        return

    if servicio not in stock or not stock[servicio]:
        await update.message.reply_text("❌ Sin stock")
        return

    precio = prices[servicio]
    saldo = users[user_id]["saldo"]

    if saldo < precio:
        await update.message.reply_text(
            "❌ Saldo insuficiente"
        )
        return

    cuenta = stock[servicio].pop(0)

    users[user_id]["saldo"] -= precio

    save_data()

    datos = parse_account(cuenta)

    msg = f"""
📦 ENTREGA

🛒 Servicio:
{servicio.replace("_", " ")}

📧 Correo:
{datos['correo']}

🔑 Contraseña:
{datos['password']}

👤 Perfil:
{datos['perfil']}

_Al adquirir la cuenta aceptas los términos_

❌ No cambiar datos
❌ No modificar perfiles
❌ No comprar dentro de la app

*Cualquier uso indebido es pérdida de garantía*

⚠️ Garantía de 28 días

{get_time()}
"""

    with open("ventas.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{user_id} | {servicio} | {get_time()}\n"
        )

    await update.message.reply_text(msg)

# =========================
# ERRORES
# =========================

async def error_handler(update, context):
    logging.error(f"ERROR: {context.error}")

# =========================
# RUN
# =========================

load_data()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addsaldo", addsaldo))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("setprecio", setprecio))
app.add_handler(CommandHandler("addtienda", addtienda))
app.add_handler(CommandHandler("tienda", tienda_cmd))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle
    )
)

app.add_error_handler(error_handler)

print("🚀 BOT ACTIVO")

app.run_polling()
