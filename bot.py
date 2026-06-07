from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# VARIABLES
BOT_TOKEN = "AQUI_TU_TOKEN"
ADMIN_ID = 123456789

# STOCK
stock = {
    "NETFLIX": [],
    "DISNEY": [],
    "SPOTIFY": [],
}

# COMBOS (usa servicios existentes)
combos = {
    "COMBO_MEXICO": ["NETFLIX", "DISNEY", "SPOTIFY"]
}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🛒 Comprar"],
        ["📦 Servicios"]
    ]
    await update.message.reply_text(
        "Bienvenido 👋\nSelecciona una opción:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# MENÚ
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
            "Selecciona servicio:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "📦 Servicios":
        await update.message.reply_text(
            "Servicios disponibles:\nNetflix\nDisney\nSpotify\nCombo México"
        )

    elif text == "Netflix":
        await entregar(update, ["NETFLIX"], "Netflix")

    elif text == "Disney":
        await entregar(update, ["DISNEY"], "Disney")

    elif text == "Spotify":
        await entregar(update, ["SPOTIFY"], "Spotify")

    elif text == "Combo México":
        await entregar(update, combos["COMBO_MEXICO"], "Combo México")

# ENTREGA
async def entregar(update, servicios, nombre):
    cuentas_entregadas = []

    for servicio in servicios:
        if len(stock[servicio]) == 0:
            await update.message.reply_text(f"❌ Sin stock en {servicio}")
            return
        cuentas_entregadas.append(stock[servicio].pop(0))

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    texto_cuentas = "\n".join(cuentas_entregadas)

    mensaje = f"""
📦 FICHA DE ENTREGA

🛒 Servicio: {nombre}

🔐 Datos:
{texto_cuentas}

⚠️ Reglas:
- No modificar datos
- Usar solo el perfil asignado
- No realizar compras dentro de la app

🕒 Fecha: {fecha}
"""

    await update.message.reply_text(mensaje)

# ADMIN: SETSTOCK
async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No autorizado")
        return

    try:
        servicio = context.args[0].upper()
        datos = " ".join(context.args[1:])

        if servicio not in stock:
            await update.message.reply_text("❌ Servicio no válido")
            return

        stock[servicio].append(datos)
        await update.message.reply_text(f"✅ Cuenta agregada a {servicio}")

    except:
        await update.message.reply_text("Uso:\n/setstock NETFLIX correo_contra_perfil")

# ADMIN: VER STOCK
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

print("🤖 Bot corriendo...")
app.run_polling()
