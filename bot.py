from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# VARIABLES
BOT_TOKEN = "AQUI_TU_TOKEN"
ADMIN_ID = 123456789  # tu ID

# STOCK (ejemplo)
stock = {
    "NETFLIX_PERFIL": [],
    "DISNEY": [],
    "COMBO_MEXICO": []
}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🛒 Comprar"],
        ["📦 Ver servicios"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Bienvenido 👋\nSelecciona una opción:", reply_markup=reply_markup)

# MENSAJES
async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛒 Comprar":
        keyboard = [
            ["Netflix Perfil"],
            ["Disney"],
            ["Combo México"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("Selecciona servicio:", reply_markup=reply_markup)

    elif text == "Netflix Perfil":
        await entregar(update, "NETFLIX_PERFIL")

    elif text == "Disney":
        await entregar(update, "DISNEY")

    elif text == "Combo México":
        await entregar(update, "COMBO_MEXICO")

# ENTREGA AUTOMÁTICA
async def entregar(update, servicio):
    if len(stock[servicio]) == 0:
        await update.message.reply_text("❌ Sin stock disponible")
        return

    cuenta = stock[servicio].pop(0)

    entrega = f"""
📦 FICHA DE ENTREGA

Servicio: {servicio}

🔐 Datos:
{cuenta}

⚠️ Reglas:
- No modificar
- Usar perfil asignado
- No compras dentro de la app

🕒 Entregado automáticamente
"""

    await update.message.reply_text(entrega)

# ADMIN - SETSTOCK
async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0]
        datos = " ".join(context.args[1:])

        stock[servicio].append(datos)

        await update.message.reply_text(f"✅ Cuenta agregada a {servicio}")
    except:
        await update.message.reply_text("Uso:\n/setstock SERVICIO correo_contraseña_perfil")

# VER STOCK
async def verstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    texto = "📦 STOCK:\n"
    for s in stock:
        texto += f"{s}: {len(stock[s])}\n"

    await update.message.reply_text(texto)

# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("verstock", verstock))
app.add_handler(MessageHandler(filters.TEXT, mensajes))

app.run_polling()
