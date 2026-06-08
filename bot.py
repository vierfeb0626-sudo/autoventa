from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json, os
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

stock = {}
usuarios = {}
tienda = {}

# =========================
# ARCHIVOS
# =========================

def cargar_datos():
    global stock, usuarios, tienda

    if os.path.exists("stock.json"):
        with open("stock.json", "r") as f:
            stock.update(json.load(f))

    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r") as f:
            usuarios.update(json.load(f))

    if os.path.exists("tienda.json"):
        with open("tienda.json", "r") as f:
            tienda.update(json.load(f))


def guardar_stock():
    with open("stock.json", "w") as f:
        json.dump(stock, f, indent=4)


def guardar_usuarios():
    with open("usuarios.json", "w") as f:
        json.dump(usuarios, f, indent=4)


def guardar_tienda():
    with open("tienda.json", "w") as f:
        json.dump(tienda, f, indent=4)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in usuarios:
        usuarios[user_id] = {"saldo": 0}
        guardar_usuarios()

    keyboard = [["🛒 Comprar"], ["💰 Saldo"], ["🛍️ Tienda"]]

    await update.message.reply_text(
        f"👋 Bienvenido\n\n🆔 ID: {user_id}\n💰 Saldo: {usuarios[user_id]['saldo']}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# FORMATO CUENTA
# =========================

def formatear(cuenta):
    try:
        p = cuenta.split("_")
        correo = p[0]
        contra = p[1]
        perfil = p[2] if len(p) > 2 else "N/A"

        return (
            f"📧 Correo: {correo}\n"
            f"🔑 Contraseña: {contra}\n"
            f"👤 Perfil: {perfil}"
        )
    except:
        return cuenta

# =========================
# DISPONIBLES
# =========================

def disponibles(servicio):
    p = len(stock.get(f"{servicio}_PERFIL", []))
    c = len(stock.get(f"{servicio}_COMPLETA", []))
    return p, c

# =========================
# MENSAJES
# =========================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    if text == "🛒 Comprar":

        servicios = set([k.split("_")[0] for k in stock.keys()])

        if not servicios:
            await update.message.reply_text("❌ Sin servicios")
            return

        keyboard = [[s] for s in servicios]

        await update.message.reply_text(
            "📦 Selecciona servicio:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "💰 Saldo":
        saldo = usuarios.get(user_id, {}).get("saldo", 0)
        await update.message.reply_text(f"💰 Saldo: {saldo}")

    elif text == "🛍️ Tienda":
        await vertienda(update, context)

    elif "Perfil" in text or "Completa" in text:

        base = context.user_data.get("servicio")

        if not base:
            await update.message.reply_text("❌ Error")
            return

        tipo = "PERFIL" if "Perfil" in text else "COMPLETA"
        servicio = f"{base}_{tipo}"

        await entregar(update, servicio)

    else:
        servicio = text.upper()
        context.user_data["servicio"] = servicio

        p, c = disponibles(servicio)

        keyboard = []

        if p > 0:
            keyboard.append([f"👤 Perfil ({p})"])
        if c > 0:
            keyboard.append([f"📺 Completa ({c})"])

        if not keyboard:
            await update.message.reply_text("❌ Sin stock")
            return

        await update.message.reply_text(
            f"{servicio}\nSelecciona tipo:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

# =========================
# ENTREGAR
# =========================

async def entregar(update: Update, servicio):
    user_id = str(update.effective_user.id)

    if servicio not in stock or not stock[servicio]:
        await update.message.reply_text("❌ Sin stock")
        return

    precio = tienda.get(servicio, 1)

    if usuarios[user_id]["saldo"] < precio:
        await update.message.reply_text("❌ Saldo insuficiente")
        return

    cuenta = stock[servicio].pop(0)
    guardar_stock()

    usuarios[user_id]["saldo"] -= precio
    guardar_usuarios()

    mensaje = f"""
📦 ENTREGA

Servicio: {servicio.replace("_"," ")}
{formatear(cuenta)}

💰 Costo: {precio}
🕒 {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""

    await update.message.reply_text(mensaje)

# =========================
# ADMIN
# =========================

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        servicio = context.args[0].upper()
        tipo = context.args[1].upper()
        datos = " ".join(context.args[2:])

        if tipo not in ["PERFIL", "COMPLETA"]:
            await update.message.reply_text("❌ Usa PERFIL o COMPLETA")
            return

        key = f"{servicio}_{tipo}"

        if key not in stock:
            stock[key] = []

        # ❌ EVITAR DUPLICADOS
        if datos in stock[key]:
            await update.message.reply_text("⚠️ Cuenta ya existe")
            return

        stock[key].append(datos)
        guardar_stock()

        await update.message.reply_text(f"✅ Agregado a {key}")

    except:
        await update.message.reply_text(
            "Uso:\n/setstock APPLE PERFIL correo_contra_perfil"
        )

# 💰 AHORA ES PRECIO POR SERVICIO
async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        key = context.args[0].upper()
        precio = int(context.args[1])

        tienda[key] = precio
        guardar_tienda()

        await update.message.reply_text(
            f"✅ Precio asignado\n{key} = ${precio}"
        )

    except:
        await update.message.reply_text(
            "Uso:\n/addsaldo APPLE_PERFIL 2"
        )

# 🛍️ TIENDA
async def vertienda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not tienda:
        await update.message.reply_text("❌ No hay precios")
        return

    txt = "🛒 TIENDA\n\n"

    for k, v in tienda.items():
        txt += f"{k.replace('_',' ')} - 💰 {v}\n"

    await update.message.reply_text(txt)

# =========================
# MAIN
# =========================

def main():
    cargar_datos()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setstock", setstock))
    app.add_handler(CommandHandler("addsaldo", addsaldo))
    app.add_handler(CommandHandler("tienda", vertienda))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

    print("🤖 BOT ONLINE")
    app.run_polling()

if __name__ == "__main__":
    main()
