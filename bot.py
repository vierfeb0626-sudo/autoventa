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

# =====================
# CONFIG
# =====================

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
        with open(name, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save():
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

    with open("stock.json", "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4, ensure_ascii=False)

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=4, ensure_ascii=False)

def load_all():
    global users, stock, prices
    users = load("users.json")
    stock = load("stock.json")
    prices = load("prices.json")

# =====================
# UTILS
# =====================

def is_admin(update: Update):
    return update.effective_user.id in ADMIN_IDS

def ensure(uid):
    if uid not in users:
        users[uid] = {"saldo": 0}

def now():
    return datetime.now(ZoneInfo("America/Chihuahua")).strftime("%d/%m/%Y %H:%M")

# =====================
# START (BOTONES DINÁMICOS)
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    ensure(uid)
    save()

    botones = []
    fila = []

    for i, servicio in enumerate(prices.keys(), start=1):
        fila.append(servicio)

        if i % 2 == 0:
            botones.append(fila)
            fila = []

    if fila:
        botones.append(fila)

    botones.append(["🛒 TIENDA", "💰 SALDO"])

    await update.message.reply_text(
        f"👋 Bienvenido VELTRIX\n💰 Saldo: ${users[uid]['saldo']}",
        reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True)
    )

# =====================
# TIENDA
# =====================

async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not prices:
        await update.message.reply_text("❌ Sin productos disponibles")
        return

    msg = "🛒 TIENDA VELTRIX\n\n"

    for s, p in prices.items():
        msg += f"👉 {s}\n💰 ${p}\n📦 Stock: {len(stock.get(s, []))}\n\n"

    await update.message.reply_text(msg)

# =====================
# SET STOCK (ADMIN)
# =====================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
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
# SET PRECIO (ADMIN)
# =====================

async def setprecio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
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
# ADD SALDO (ADMIN)
# =====================

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
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
# MENSAJES + COMPRA DINÁMICA
# =====================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.upper()
    uid = str(update.effective_user.id)

    ensure(uid)

    # SALDO
    if text == "💰 SALDO":
        await update.message.reply_text(f"💰 Saldo: ${users[uid]['saldo']}")
        return

    # TIENDA
    if text == "🛒 TIENDA":
        await tienda(update, context)
        return

    # COMPRA AUTOMÁTICA
    if text in prices:

        servicio = text

        if servicio not in stock or len(stock[servicio]) == 0:
            await update.message.reply_text("❌ Sin stock")
            return

        precio = prices[servicio]

        if users[uid]["saldo"] < precio:
            await update.message.reply_text("❌ Saldo insuficiente")
            return

        cuenta = stock[servicio].pop(0)
        users[uid]["saldo"] -= precio

        save()

        try:
            correo, passw, perfil = cuenta.split("_")
        except:
            correo = cuenta
            passw = "N/A"
            perfil = "N/A"

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
# RUN
# =====================

load_all()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("setprecio", setprecio))
app.add_handler(CommandHandler("addsaldo", addsaldo))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

print("🚀 VELTRIX BOT ONLINE")

app.run_polling()
