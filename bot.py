import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ reemplazo de pytz

# ===== CONFIG =====
TOKEN = "TU_TOKEN_AQUI"
ADMIN_ID = 123456789

# ===== DATA =====
users = {}
stock = {}
prices = {}
tienda = {}

logging.basicConfig(level=logging.INFO)

# ===== FUNCIONES =====

def get_time():
    now = datetime.now(ZoneInfo("America/Chihuahua"))
    return now.strftime("📆 %d/%m/%Y 🕒 %H:%M")

def parse_account(data):
    parts = data.split("_")
    return {
        "correo": parts[0],
        "password": parts[1],
        "perfil": parts[2] if len(parts) > 2 else "N/A"
    }

# ===== START =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users:
        users[user_id] = {"saldo": 0}

    keyboard = [["APPLE", "DISNEY"], ["NETFLIX"]]

    await update.message.reply_text(
        f"👋 Bienvenido\n\n🆔 ID: {user_id}\n💰 Saldo: ${users[user_id]['saldo']}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ===== SALDO =====

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        monto = int(context.args[1])

        if user_id not in users:
            users[user_id] = {"saldo": 0}

        users[user_id]["saldo"] += monto

        await update.message.reply_text(f"✅ {user_id} = ${users[user_id]['saldo']}")
    except:
        await update.message.reply_text("❌ /addsaldo ID MONTO")

# ===== STOCK =====

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0].upper()
        data = context.args[1]

        if servicio not in stock:
            stock[servicio] = []

        if data in stock[servicio]:
            await update.message.reply_text("⚠️ Ya existe")
            return

        stock[servicio].append(data)
        await update.message.reply_text(f"✅ Stock agregado a {servicio}")
    except:
        await update.message.reply_text("❌ /setstock APPLE_PERFIL correo_pass_perfil")

# ===== PRECIO =====

async def setprecio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0].upper()
        precio = int(context.args[1])

        prices[servicio] = precio
        await update.message.reply_text(f"💰 {servicio} = ${precio}")
    except:
        await update.message.reply_text("❌ /setprecio APPLE_PERFIL 20")

# ===== TIENDA =====

async def addtienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0].upper()
        precio = context.args[1]

        tienda[servicio] = precio
        await update.message.reply_text("✅ Tienda actualizada")
    except:
        await update.message.reply_text("❌ /addtienda APPLE_PERFIL 20")

async def tienda_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tienda:
        await update.message.reply_text("❌ No hay tienda")
        return

    msg = "🛒 TIENDA\n\n"
    for s, p in tienda.items():
        msg += f"{s} = ${p}\n"

    await update.message.reply_text(msg)

# ===== MENÚ =====

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()

    if text in ["APPLE", "DISNEY", "NETFLIX"]:
        context.user_data["base"] = text

        keyboard = [["PERFIL", "COMPLETA"]]

        await update.message.reply_text(
            f"{text}\nSelecciona tipo:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    if text in ["PERFIL", "COMPLETA"]:
        base = context.user_data.get("base")

        if not base:
            return

        servicio = f"{base}_{text}"
        await comprar(update, servicio)

# ===== COMPRA =====

async def comprar(update, servicio):
    user_id = update.effective_user.id

    if servicio not in prices:
        await update.message.reply_text("❌ Sin precio")
        return

    if servicio not in stock or not stock[servicio]:
        await update.message.reply_text("❌ Sin stock")
        return

    precio = prices[servicio]
    saldo = users[user_id]["saldo"]

    if saldo < precio:
        await update.message.reply_text("❌ Saldo insuficiente")
        return

    cuenta = stock[servicio].pop(0)
    users[user_id]["saldo"] -= precio

    datos = parse_account(cuenta)

    msg = f"""
📦 ENTREGA

Servicio: {servicio.replace("_", " ")}

📧 Correo: {datos['correo']}
🔑 Contraseña: {datos['password']}
👤 Perfil: {datos['perfil']}

❌ No cambiar datos
❌ No hacer suscripción dentro de la app
❌ Respetar perfiles

{get_time()}
"""

    await update.message.reply_text(msg)

# ===== RUN =====

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addsaldo", addsaldo))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("setprecio", setprecio))
app.add_handler(CommandHandler("addtienda", addtienda))
app.add_handler(CommandHandler("tienda", tienda_cmd))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 BOT ACTIVO")
app.run_polling()
