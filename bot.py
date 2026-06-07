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

BOT_TOKEN = "AQUI_TU_TOKEN"
ADMIN_ID = 123456789

# =========================
# STOCK
# =========================

stock = {
    "NETFLIX": [],
    "DISNEY": [],
    "SPOTIFY": []
}

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

        with open(
            "stock.json",
            "r",
            encoding="utf-8"
        ) as f:

            stock.update(json.load(f))


def guardar_stock():

    with open(
        "stock.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            stock,
            f,
            indent=4,
            ensure_ascii=False
        )

# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        ["🛒 Comprar"],
        ["📦 Servicios"]
    ]

    await update.message.reply_text(
        "👋 Bienvenido a VELTRIX\n\nSelecciona una opción:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

# =========================
# MENSAJES
# =========================

async def mensajes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    # =====================
    # COMPRAR
    # =====================

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

    # =====================
    # SERVICIOS
    # =====================

    elif text == "📦 Servicios":

        mensaje = """
📦 SERVICIOS DISPONIBLES

• Netflix
• Disney
• Spotify
• Combo México
"""

        await update.message.reply_text(mensaje)

    # =====================
    # NETFLIX
    # =====================

    elif text == "Netflix":

        await entregar(
            update,
            ["NETFLIX"],
            "Netflix"
        )

    # =====================
    # DISNEY
    # =====================

    elif text == "Disney":

        await entregar(
            update,
            ["DISNEY"],
            "Disney"
        )

    # =====================
    # SPOTIFY
    # =====================

    elif text == "Spotify":

        await entregar(
            update,
            ["SPOTIFY"],
            "Spotify"
        )

    # =====================
    # COMBO
    # =====================

    elif text == "Combo México":

        await entregar(
            update,
            combos["COMBO_MEXICO"],
            "Combo México"
        )

# =========================
# ENTREGAR
# =========================

async def entregar(
    update,
    servicios,
    nombre
):

    cuentas = []

    # VERIFICAR STOCK

    for servicio in servicios:

        if len(stock[servicio]) == 0:

            await update.message.reply_text(
                f"❌ Sin stock en {servicio}"
            )

            return

    # ENTREGAR

    for servicio in servicios:

        cuenta = stock[servicio].pop(0)

        cuentas.append(cuenta)

    guardar_stock()

    fecha = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

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
• Usar solo perfil asignado

🕒 Fecha:
{fecha}
"""

    # GUARDAR LOG

    with open(
        "ventas.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{update.effective_user.id} | "
            f"{nombre} | "
            f"{fecha}\n"
        )

    # ENVIAR

    await update.message.reply_text(
        mensaje,
        protect_content=True
    )

# =========================
# SET STOCK
# =========================

async def setstock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ No autorizado"
        )

        return

    try:

        servicio = context.args[0].upper()

        datos = " ".join(context.args[1:])

        if servicio not in stock:

            await update.message.reply_text(
                "❌ Servicio inválido"
            )

            return

        stock[servicio].append(datos)

        guardar_stock()

        await update.message.reply_text(
            f"✅ Cuenta agregada a {servicio}"
        )

    except Exception as e:

        print(e)

        await update.message.reply_text(
            "Uso:\n"
            "/setstock NETFLIX correo:contra:perfil"
        )

# =========================
# VER STOCK
# =========================

async def verstock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    texto = "📦 STOCK ACTUAL\n\n"

    for servicio in stock:

        cantidad = len(stock[servicio])

        estado = "🟢" if cantidad > 0 else "🔴"

        texto += (
            f"{estado} "
            f"{servicio}: "
            f"{cantidad}\n"
        )

    await update.message.reply_text(texto)

# =========================
# ERROR
# =========================

async def error_handler(
    update,
    context
):

    print(f"ERROR: {context.error}")

# =========================
# MAIN
# =========================

def main():

    cargar_stock()

    app = ApplicationBuilder().token(
        BOT_TOKEN
    ).build()

    # COMANDOS

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "setstock",
            setstock
        )
    )

    app.add_handler(
        CommandHandler(
            "verstock",
            verstock
        )
    )

    # MENSAJES

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mensajes
        )
    )

    # ERRORES

    app.add_error_handler(
        error_handler
    )

    print("🤖 BOT VELTRIX ONLINE")

    app.run_polling()

# =========================
# START
# =========================

if __name__ == "__main__":
    main()
