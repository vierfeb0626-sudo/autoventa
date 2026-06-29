import json
import os
import logging

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [6957858602, 7477204627]

logging.basicConfig(level=logging.INFO)

# =====================
# DB
# =====================

users = {}
stock = {}
prices = {}

# =====================
# LOAD / SAVE
# =====================

def load(name):
    try:
        return json.load(open(name, "r", encoding="utf-8"))
    except:
        return {}

def save():
    json.dump(users, open("users.json","w",encoding="utf-8"), indent=4)
    json.dump(stock, open("stock.json","w",encoding="utf-8"), indent=4)
    json.dump(prices, open("prices.json","w",encoding="utf-8"), indent=4)

def load_all():
    global users, stock, prices
    users = load("users.json")
    stock = load("stock.json")
    prices = load("prices.json")

# =====================
# UTILS
# =====================

def admin(update):
    return update.effective_user.id in ADMIN_IDS

def ensure(uid):
    if uid not in users:
        users[uid] = {"saldo": 0}

def now():
    return datetime.now(ZoneInfo("America/Chihuahua")).strftime("%d/%m/%Y %H:%M")

# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    ensure(uid)
    save()

    keyboard = [
        ["📺 YOUTUBE", "🎬 NETFLIX"],
        ["🛒 TIENDA", "💰 SALDO"]
    ]

    await update.message.reply_text(
        f"👋 Bienvenido\n💰 Saldo: ${users[uid]['saldo']}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =====================
# TIENDA BOTONES
# =====================

async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not prices:
        await update.message.reply_text("❌ Sin productos disponibles")
        return

    msg = "🛒 TIENDA\n\n"
    for s, p in prices.items():
        msg += f"👉 {s} = ${p}\n"

    await update.message.reply_text(msg)

# =====================
# STOCK ADMIN
# =====================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return

    try:
        servicio = context.args[0].upper()
        cuenta = " ".join(context.args[1:])

        stock.setdefault(servicio, []).append(cuenta)
        save()

        await update.message.reply_text("✅ Stock agregado")

    except:
        await update.message.reply_text("/setstock SERVICIO correo_pass_perfil")

# =====================
# PRECIO ADMIN
# =====================

async def setprecio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return

    try:
        servicio = context.args[0].upper()
        precio = int(context.args[1])

        prices[servicio] = precio
        save()

        await update.message.reply_text("✅ Precio guardado")

    except:
        await update.message.reply_text("/setprecio SERVICIO PRECIO")

# =====================
# SALDO ADMIN
# =====================

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin(update):
        return

    try:
        uid = str(context.args[0])
        monto = int(context.args[1])

        ensure(uid)
        users[uid]["saldo"] += monto
        save()

        await update.message.reply_text("✅ Saldo agregado")

    except:
        await update.message.reply_text("/addsaldo ID MONTO")

# =====================
# COMPRA POR BOTÓN
# =====================

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    ensure(uid)

    text = update.message.text.upper()

    servicio = None

    if "YOUTUBE" in text:
        servicio = "YOUTUBE_COMPLETA"
    elif "NETFLIX" in text:
        servicio = "NETFLIX"
    else:
        await update.message.reply_text("❌ Servicio no válido")
        return

    if servicio not in stock or len(stock[servicio]) == 0:
        await update.message.reply_text("❌ Sin stock")
        return

    if servicio not in prices:
        await update.message.reply_text("❌ Sin precio")
        return

    precio = prices[servicio]

    if users[uid]["saldo"] < precio:
        await update.message.reply_text("❌ Saldo insuficiente")
        return

    cuenta = stock[servicio].pop(0)
    users[uid]["saldo"] -= precio

    save()

    correo, passw, perfil = cuenta.split("_")

    await update.message.reply_text(
f"""
📦 ENTREGA VELTRIX

🛒 {servicio}

📧 {correo}
🔑 {passw}
👤 {perfil}

🕒 {now()}
"""
    )

# =====================
# MENSAJES
# =====================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.upper()

    if text == "🛒 TIENDA":
        await tienda(update, context)

    elif text == "💰 SALDO":
        uid = str(update.effective_user.id)
        ensure(uid)
        await update.message.reply_text(f"💰 Saldo: ${users[uid]['saldo']}")

    elif text in ["📺 YOUTUBE", "🎬 NETFLIX"]:
        await comprar(update, context)

# =====================
# RUN
# =====================

load_all()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("setprecio", setprecio))
app.add_handler(CommandHandler("addsaldo", addsaldo))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

print("🚀 BOT VELTRIX LISTO")

app.run_polling()
