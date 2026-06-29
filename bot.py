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

# =====================
# CONFIG
# =====================

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    6957858602,
    7477204627
]

logging.basicConfig(level=logging.INFO)

# =====================
# BASE DE DATOS
# =====================

users = {}
stock = {}
prices = {}
tienda = {}

# =====================
# SAVE / LOAD
# =====================

def save_data():
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

    with open("stock.json", "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4, ensure_ascii=False)

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=4, ensure_ascii=False)

    with open("tienda.json", "w", encoding="utf-8") as f:
        json.dump(tienda, f, indent=4, ensure_ascii=False)


def load_file(name):
    try:
        with open(name, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def load_data():
    global users, stock, prices, tienda

    users = load_file("users.json")
    stock = load_file("stock.json")
    prices = load_file("prices.json")
    tienda = load_file("tienda.json")


# =====================
# UTILIDADES
# =====================

def is_admin(update: Update):
    return update.effective_user.id in ADMIN_IDS


def now():
    return datetime.now(ZoneInfo("America/Chihuahua")).strftime("📆 %d/%m/%Y 🕒 %H:%M")


def parse_account(data):
    p = data.split("_")
    return {
        "correo": p[0] if len(p) > 0 else "",
        "password": p[1] if len(p) > 1 else "",
        "perfil": p[2] if len(p) > 2 else "N/A"
    }


def ensure_user(uid):
    if uid not in users:
        users[uid] = {"saldo": 0}


# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    ensure_user(uid)
    save_data()

    await update.message.reply_text(
        f"""
👋 Bienvenido VELTRIX

🆔 ID: {uid}
💰 Saldo: ${users[uid]['saldo']}
""",
        reply_markup=ReplyKeyboardMarkup(
            [["🛒 TIENDA"], ["💰 SALDO"]],
            resize_keyboard=True
        )
    )


# =====================
# VER STOCK (ADMIN)
# =====================

async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    if not stock:
        await update.message.reply_text("❌ Sin stock")
        return

    msg = "📦 STOCK ACTUAL\n\n"

    for s, items in stock.items():
        msg += f"🔹 {s} → {len(items)} cuentas\n"

    await update.message.reply_text(msg)


# =====================
# TIENDA
# =====================

async def tienda_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not tienda:
        await update.message.reply_text("❌ Sin productos disponibles")
        return

    msg = "🛒 TIENDA\n\n"

    for s, p in tienda.items():
        msg += f"• {s.replace('_',' ')} = ${p}\n"

    await update.message.reply_text(msg)


# =====================
# AGREGAR PRODUCTO
# =====================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    try:
        servicio = context.args[0].upper()
        cuenta = " ".join(context.args[1:])

        if servicio not in stock:
            stock[servicio] = []

        stock[servicio].append(cuenta)
        save_data()

        await update.message.reply_text("✅ Stock agregado")

    except:
        await update.message.reply_text("/setstock SERVICIO correo_pass_perfil")


# =====================
# PRECIO
# =====================

async def setprecio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    try:
        servicio = context.args[0].upper()
        precio = int(context.args[1])

        prices[servicio] = precio
        save_data()

        await update.message.reply_text("✅ Precio actualizado")

    except:
        await update.message.reply_text("/setprecio SERVICIO PRECIO")


# =====================
# SALDO
# =====================

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    try:
        uid = str(context.args[0])
        monto = int(context.args[1])

        ensure_user(uid)

        users[uid]["saldo"] += monto
        save_data()

        await update.message.reply_text("✅ Saldo agregado")

    except:
        await update.message.reply_text("/addsaldo ID MONTO")


# =====================
# COMPRA AUTOMÁTICA
# =====================

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    ensure_user(uid)

    if not context.args:
        await update.message.reply_text("Uso: /comprar SERVICIO")
        return

    servicio = context.args[0].upper()

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

    # DESCUENTA STOCK ANTES DE ENTREGAR (ANTI DUPLICADO)
    cuenta = stock[servicio].pop(0)
    users[uid]["saldo"] -= precio

    save_data()

    d = parse_account(cuenta)

    await update.message.reply_text(
f"""
📦 ENTREGA VELTRIX

🛒 {servicio}

📧 {d['correo']}
🔑 {d['password']}
👤 {d['perfil']}

⚠️ No compartir ni modificar

🕒 {now()}
"""
    )


# =====================
# BOTONES
# =====================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.upper()

    if text == "🛒 TIENDA":
        await tienda_cmd(update, context)

    elif text == "💰 SALDO":
        uid = str(update.effective_user.id)
        ensure_user(uid)
        await update.message.reply_text(f"💰 Saldo: ${users[uid]['saldo']}")


# =====================
# RUN
# =====================

load_data()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stock", stock_cmd))
app.add_handler(CommandHandler("tienda", tienda_cmd))

app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("setprecio", setprecio))
app.add_handler(CommandHandler("addsaldo", addsaldo))
app.add_handler(CommandHandler("comprar", comprar))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

print("🚀 VELTRIX BOT ACTIVO")

app.run_polling()
