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

logging.basicConfig(level=logging.INFO)

=========================

JSON

=========================

def save_data():

files = {  
    "users.json": users,  
    "stock.json": stock,  
    "prices.json": prices  
}  

for name, data in files.items():  
    with open(name, "w", encoding="utf-8") as f:  
        json.dump(data, f, indent=4)

def load_data():

global users, stock, prices  

try:  
    users = json.load(open("users.json", encoding="utf-8"))  
except:  
    users = {}  

try:  
    stock = json.load(open("stock.json", encoding="utf-8"))  
except:  
    stock = {}  

try:  
    prices = json.load(open("prices.json", encoding="utf-8"))  
except:  
    prices = {}

=========================

UTILIDADES

=========================

def get_time():

now = datetime.now(  
    ZoneInfo("America/Chihuahua")  
)  

return now.strftime(  
    "📆 %d/%m/%Y 🕒 %H:%M"  
)

def parse_account(data):

try:  
    p = data.split("_")  

    return {  
        "correo": p[0],  
        "password": p[1],  
        "perfil": p[2] if len(p) > 2 else "N/A"  
    }  

except:  

    return {  
        "correo":"ERROR",  
        "password":"ERROR",  
        "perfil":"ERROR"  
    }

def tienda_disponible():

lista = []  

for item, cuentas in stock.items():  

    if cuentas:  
        lista.append(item)  

return lista

=========================

START

=========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

uid = str(update.effective_user.id)  

if uid not in users:  
    users[uid] = {  
        "saldo":0  
    }  
    save_data()  


keyboard = []  


bases = set()  

for servicio in tienda_disponible():  

    base = servicio.split("_")[0]  

    if base not in bases:  

        bases.add(base)  
        keyboard.append([base])  


keyboard.append(  
    ["💰 SALDO","🛒 TIENDA"]  
)  


await update.message.reply_text(  

    f"👋 Bienvenido\n\n"  
    f"🆔 ID: {uid}\n"  
    f"💰 Saldo: ${users[uid]['saldo']}",  

    reply_markup=ReplyKeyboardMarkup(  
        keyboard,  
        resize_keyboard=True  
    )  
)

=========================

TIENDA

=========================

async def tienda_cmd(update, context):

disponibles = tienda_disponible()  


if not disponibles:  

    await update.message.reply_text(  
        "❌ Sin productos disponibles"  
    )  
    return  


msg = "🛒 TIENDA\n\n"  


for item in disponibles:  

    precio = prices.get(item,"?")  

    msg += (  
        f"• {item.replace('_',' ')} "  
        f"= ${precio}\n"  
    )  


await update.message.reply_text(msg)

=========================

STOCK ADMIN

=========================

async def stock_cmd(update, context):

if update.effective_user.id != ADMIN_IDS:  
    return  


msg = "📦 STOCK DISPONIBLE\n\n"  


if not stock:  

    msg += "Sin datos"  

else:  

    for servicio, cuentas in stock.items():  

        msg += (  
            f"{servicio.replace('_',' ')}\n"  
            f"📦 {len(cuentas)} disponibles\n\n"  
        )  


await update.message.reply_text(msg)

=========================

SALDO

=========================

async def addsaldo(update, context):

if update.effective_user.id != ADMIN_IDS:  
    return  


try:  

    uid = str(context.args[0])  
    monto = int(context.args[1])  


    if uid not in users:  

        users[uid]={  
            "saldo":0  
        }  


    users[uid]["saldo"] += monto  


    save_data()  


    await update.message.reply_text(  
        "✅ Saldo actualizado"  
    )  


except:  

    await update.message.reply_text(  
        "❌ /addsaldo ID MONTO"  
    )

=========================

AGREGAR STOCK

=========================

async def setstock(update, context):

if update.effective_user.id != ADMIN_IDS:  
    return  


try:  

    servicio = context.args[0].upper()  

    data = " ".join(  
        context.args[1:]  
    )  


    if servicio not in stock:  

        stock[servicio]=[]  


    stock[servicio].append(data)  


    save_data()  


    await update.message.reply_text(  
        f"✅ Stock agregado {servicio}"  
    )  


except:  

    await update.message.reply_text(  
        "❌ /setstock NETFLIX_PERFIL correo_pass_perfil"  
    )

=========================

PRECIO

=========================

async def setprecio(update, context):

if update.effective_user.id != ADMIN_IDS:  
    return  


try:  

    servicio=context.args[0].upper()  
    precio=int(context.args[1])  


    prices[servicio]=precio  


    save_data()  


    await update.message.reply_text(  
        "✅ Precio guardado"  
    )  


except:  

    await update.message.reply_text(  
        "❌ /setprecio NETFLIX_PERFIL 20"  
    )

=========================

MENU

=========================

async def handle(update, context):

text = update.message.text.upper()  


if text=="🛒 TIENDA":  

    await tienda_cmd(update,context)  
    return  



if text=="💰 SALDO":  

    uid=str(update.effective_user.id)  

    await update.message.reply_text(  
        f"💰 Saldo: ${users.get(uid,{'saldo':0})['saldo']}"  
    )  

    return  



bases=set()  


for servicio in tienda_disponible():  

    bases.add(  
        servicio.split("_")[0]  
    )  


if text in bases:  

    context.user_data["base"]=text  


    await update.message.reply_text(  

        "Selecciona:",  

        reply_markup=ReplyKeyboardMarkup(  
            [["PERFIL","COMPLETA"]],  
            resize_keyboard=True  
        )  
    )  

    return  



if text in ["PERFIL","COMPLETA"]:  

    base=context.user_data.get("base")  


    if base:  

        await comprar(  
            update,  
            f"{base}_{text}"  
        )

=========================

COMPRA

=========================

async def comprar(update, servicio):

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


datos=parse_account(cuenta)  



await update.message.reply_text(

f"""
📦 ENTREGA

🛒 Servicio:
{servicio.replace('_',' ')}

📧 Correo:
{datos['correo']}

🔑 Contraseña:
{datos['password']}

👤 Perfil:
{datos['perfil']}

❌ No cambiar datos
❌ No modificar perfiles

⚠️ Garantía 28 días

{get_time()}
"""
)

=========================

RUN

=========================

load_data()

app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("addsaldo",addsaldo))
app.add_handler(CommandHandler("setstock",setstock))
app.add_handler(CommandHandler("setprecio",setprecio))
app.add_handler(CommandHandler("stock",stock_cmd))
app.add_handler(CommandHandler("tienda",tienda_cmd))

app.add_handler(
MessageHandler(
filters.TEXT & ~filters.COMMAND,
handle
)
)

print("🚀 BOT ACTIVO")

app.run_polling()
