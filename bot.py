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


ADMIN_IDS = [
    6957858602,
    7477204627
]


logging.basicConfig(level=logging.INFO)


users = {}
stock = {}
prices = {}


# =====================
# BASE DATOS
# =====================

def load(name):
    try:
        with open(name, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save():

    with open("users.json","w",encoding="utf-8") as f:
        json.dump(users,f,indent=4,ensure_ascii=False)

    with open("stock.json","w",encoding="utf-8") as f:
        json.dump(stock,f,indent=4,ensure_ascii=False)

    with open("prices.json","w",encoding="utf-8") as f:
        json.dump(prices,f,indent=4,ensure_ascii=False)



def load_all():

    global users,stock,prices

    users = load("users.json")
    stock = load("stock.json")
    prices = load("prices.json")



# =====================
# UTILIDADES
# =====================

def admin(update):

    return update.effective_user.id in ADMIN_IDS



def user_check(uid):

    if uid not in users:
        users[uid] = {
            "saldo":0
        }



def hora():

    return datetime.now(
        ZoneInfo("America/Chihuahua")
    ).strftime(
        "📆 %d/%m/%Y  ⌚ %H:%M"
    )



def menu_principal():

    return ReplyKeyboardMarkup(
        [
            ["🛒 TIENDA"],
            ["💰 SALDO"]
        ],
        resize_keyboard=True
    )



# =====================
# START
# =====================

async def start(update,context):

    uid=str(update.effective_user.id)

    user_check(uid)

    save()


    await update.message.reply_text(
f"""
👋 Bienvenido VELTRIX

🆔 {uid}
💰 Saldo: ${users[uid]['saldo']}
""",
reply_markup=menu_principal()
)



# =====================
# TIENDA BOTONES
# =====================

async def tienda(update,context):


    botones=[]

    fila=[]


    for servicio,cuentas in stock.items():

        if len(cuentas)>0:

            fila.append(servicio)

            if len(fila)==2:
                botones.append(fila)
                fila=[]


    if fila:
        botones.append(fila)



    if not botones:

        await update.message.reply_text(
            "❌ No hay productos disponibles"
        )
        return



    botones.append(["💰 SALDO"])


    await update.message.reply_text(
        "🛒 Selecciona un producto:",
        reply_markup=ReplyKeyboardMarkup(
            botones,
            resize_keyboard=True
        )
    )



# =====================
# STOCK ADMIN
# =====================

async def stock_cmd(update,context):

    if not admin(update):
        return


    if not stock:
        await update.message.reply_text(
            "❌ Sin stock"
        )
        return


    msg="📦 STOCK VELTRIX\n\n"


    for s,c in stock.items():

        msg+=f"{s}: {len(c)} disponibles\n"


    await update.message.reply_text(msg)



# =====================
# AGREGAR STOCK
# =====================

async def setstock(update,context):

    if not admin(update):
        return


    try:

        servicio=context.args[0].upper()

        cuenta=" ".join(context.args[1:])


        stock.setdefault(
            servicio,
            []
        ).append(cuenta)


        save()


        await update.message.reply_text(
            "✅ Cuenta agregada"
        )


    except:

        await update.message.reply_text(
            "/setstock SERVICIO correo_pass_perfil"
        )



# =====================
# PRECIO
# =====================

async def setprecio(update,context):

    if not admin(update):
        return


    try:

        servicio=context.args[0].upper()

        precio=int(context.args[1])


        prices[servicio]=precio


        save()


        await update.message.reply_text(
            "✅ Precio guardado"
        )


    except:

        await update.message.reply_text(
            "/setprecio SERVICIO PRECIO"
        )



# =====================
# SALDO
# =====================

async def addsaldo(update,context):

    if not admin(update):
        return


    try:

        uid=str(context.args[0])

        monto=int(context.args[1])


        user_check(uid)


        users[uid]["saldo"]+=monto


        save()


        await update.message.reply_text(
            "✅ Saldo agregado"
        )


    except:

        await update.message.reply_text(
            "/addsaldo ID MONTO"
        )



# =====================
# COMPRA
# =====================

async def comprar(update,context):

    uid=str(update.effective_user.id)

    user_check(uid)


    servicio=update.message.text.upper()



    if servicio not in stock:

        return



    if len(stock[servicio])==0:

        await update.message.reply_text(
            "❌ Agotado"
        )
        return



    precio=prices.get(servicio,0)



    if users[uid]["saldo"] < precio:

        await update.message.reply_text(
            "❌ Saldo insuficiente"
        )
        return



    # QUITAR STOCK
    cuenta=stock[servicio].pop(0)

    users[uid]["saldo"]-=precio


    save()



    datos=cuenta.split("_")


    correo=datos[0]
    password=datos[1]
    perfil=datos[2] if len(datos)>2 else "N/A"



    await update.message.reply_text(
f"""
📦 ENTREGA VELTRIX

App
{servicio}

Correo
{correo}

Contraseña
{password}

Perfil
{perfil}


Al adquirir la cuenta aceptas las siguientes reglas

❌ No Modificar contraseña

❌ Usar solo la cantidad de dispositivos contratados

❌ Solo inicios sesión en los dispositivos contratados

⚠️ En caso de incumplir se retira cuenta sin garantía


{hora()} CD JUÁREZ
"""
)



# =====================
# MENSAJES
# =====================

async def mensajes(update,context):

    texto=update.message.text.upper()


    if texto=="🛒 TIENDA":

        await tienda(update,context)
        return



    if texto=="💰 SALDO":

        uid=str(update.effective_user.id)

        user_check(uid)

        await update.message.reply_text(
            f"💰 Saldo: ${users[uid]['saldo']}"
        )

        return



    if texto in stock:

        await comprar(update,context)



# =====================
# RUN
# =====================

load_all()


app=ApplicationBuilder().token(TOKEN).build()



app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


app.add_handler(
    CommandHandler(
        "stock",
        stock_cmd
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
        "setprecio",
        setprecio
    )
)


app.add_handler(
    CommandHandler(
        "addsaldo",
        addsaldo
    )
)



app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        mensajes
    )
)



print("🚀 VELTRIX ACTIVO")

app.run_polling()
