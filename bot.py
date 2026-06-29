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


TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    6957858602,
    7477204627
]


users = {}
stock = {}
prices = {}
tienda = {}


logging.basicConfig(level=logging.INFO)


# =====================
# DATOS
# =====================

def save_data():

    with open("users.json","w",encoding="utf-8") as f:
        json.dump(users,f,indent=4)

    with open("stock.json","w",encoding="utf-8") as f:
        json.dump(stock,f,indent=4)

    with open("prices.json","w",encoding="utf-8") as f:
        json.dump(prices,f,indent=4)

    with open("tienda.json","w",encoding="utf-8") as f:
        json.dump(tienda,f,indent=4)



def load_file(name):

    try:
        return json.load(
            open(name,encoding="utf-8")
        )
    except:
        return {}



def load_data():

    global users,stock,prices,tienda

    users = load_file("users.json")
    stock = load_file("stock.json")
    prices = load_file("prices.json")
    tienda = load_file("tienda.json")



def admin(update):

    return update.effective_user.id in ADMIN_IDS



def get_time():

    return datetime.now(
        ZoneInfo("America/Chihuahua")
    ).strftime(
        "📆 %d/%m/%Y 🕒 %H:%M"
    )



def parse_account(data):

    p=data.split("_")

    return {
        "correo":p[0],
        "password":p[1],
        "perfil":p[2] if len(p)>2 else "N/A"
    }



# =====================
# START
# =====================

async def start(update,context):

    uid=str(update.effective_user.id)

    if uid not in users:

        users[uid]={
            "saldo":0
        }

        save_data()


    await update.message.reply_text(
f"""
👋 Bienvenido VELTRIX

🆔 ID: {uid}
💰 Saldo: ${users[uid]['saldo']}
""",
reply_markup=ReplyKeyboardMarkup(
[
["🛒 TIENDA"],
["💰 SALDO"]
],
resize_keyboard=True
)
)



# =====================
# TIENDA
# =====================

async def tienda_cmd(update,context):

    if not tienda:

        await update.message.reply_text(
            "❌ Sin productos disponibles"
        )
        return


    msg="🛒 TIENDA\n\n"


    for s,p in tienda.items():

        msg += f"• {s.replace('_',' ')} ${p}\n"


    await update.message.reply_text(msg)



# =====================
# ADD TIENDA
# =====================

async def addtienda(update,context):

    if not admin(update):
        return


    try:

        servicio=context.args[0].upper()
        precio=int(context.args[1])

        tienda[servicio]=precio

        save_data()

        await update.message.reply_text(
            "✅ Producto agregado"
        )

    except:

        await update.message.reply_text(
            "/addtienda SERVICIO PRECIO"
        )



# =====================
# STOCK
# =====================

async def setstock(update,context):

    if not admin(update):
        return


    try:

        servicio=context.args[0].upper()

        cuenta=" ".join(context.args[1:])


        if servicio not in stock:
            stock[servicio]=[]


        stock[servicio].append(cuenta)

        save_data()


        await update.message.reply_text(
            "✅ Cuenta agregada"
        )

    except:

        await update.message.reply_text(
            "/setstock NETFLIX_PERFIL correo_pass_perfil"
        )



# =====================
# PRECIO
# =====================

async def setprecio(update,context):

    if not admin(update):
        return


    servicio=context.args[0].upper()
    precio=int(context.args[1])


    prices[servicio]=precio

    save_data()


    await update.message.reply_text(
        "✅ Precio guardado"
    )



# =====================
# SALDO
# =====================

async def addsaldo(update,context):

    if not admin(update):
        return


    uid=context.args[0]
    monto=int(context.args[1])


    if uid not in users:

        users[uid]={
            "saldo":0
        }


    users[uid]["saldo"] += monto

    save_data()


    await update.message.reply_text(
        "✅ Saldo agregado"
    )



# =====================
# COMPRA
# =====================

async def comprar(update,servicio):

    uid=str(update.effective_user.id)


    if servicio not in stock or not stock[servicio]:

        await update.message.reply_text(
            "❌ Sin stock"
        )
        return



    precio=prices.get(servicio)


    if not precio:

        await update.message.reply_text(
            "❌ Sin precio"
        )
        return



    saldo=users[uid]["saldo"]


    if saldo < precio:

        await update.message.reply_text(
            "❌ Saldo insuficiente"
        )
        return



    cuenta=stock[servicio].pop(0)

    users[uid]["saldo"]-=precio


    save_data()


    d=parse_account(cuenta)


    await update.message.reply_text(
f"""
📦 ENTREGA

🛒 Servicio:
{servicio.replace('_',' ')}

📧 Correo:
{d['correo']}

🔑 Contraseña:
{d['password']}

👤 Perfil:
{d['perfil']}

_Al adquirir la cuenta aceptas los términos_

❌ No cambiar datos
❌ No modificar perfiles
❌ No comprar dentro de la app

*Cualquier uso indebido es pérdida de garantía*

⚠️ Garantía 28 días

{get_time()}
"""
)



# =====================
# BOTONES
# =====================

async def mensajes(update,context):

    text=update.message.text.upper()


    if text=="🛒 TIENDA":

        await tienda_cmd(update,context)
        return


    if text=="💰 SALDO":

        uid=str(update.effective_user.id)

        await update.message.reply_text(
            f"💰 Saldo: ${users.get(uid,{'saldo':0})['saldo']}"
        )
        return



# =====================
# RUN
# =====================

load_data()


app=ApplicationBuilder().token(TOKEN).build()


app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("tienda",tienda_cmd))
app.add_handler(CommandHandler("addtienda",addtienda))
app.add_handler(CommandHandler("setstock",setstock))
app.add_handler(CommandHandler("setprecio",setprecio))
app.add_handler(CommandHandler("addsaldo",addsaldo))


app.add_handler(
MessageHandler(
filters.TEXT & ~filters.COMMAND,
mensajes
)
)


print("🚀 BOT ACTIVO")

app.run_polling()
