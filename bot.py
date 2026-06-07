import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "TU_TOKEN_AQUI"

STOCK_FILE = "stock.json"
USERS_FILE = "users.json"
PRICES_FILE = "prices.json"

# ---------- UTIL ----------

def load(file):
if not os.path.exists(file):
return {}
with open(file) as f:
return json.load(f)

def save(file, data):
with open(file, "w") as f:
json.dump(data, f, indent=4)

def now():
return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ---------- STOCK ----------

def add_stock(service, tipo, acc):
data = load(STOCK_FILE)
data.setdefault(service, {}).setdefault(tipo, []).append(acc)
save(STOCK_FILE, data)

def get_stock(service, tipo):
data = load(STOCK_FILE)
try:
acc = data[service][tipo].pop(0)
save(STOCK_FILE, data)
return acc
except:
return None

def count_stock():
data = load(STOCK_FILE)
msg = "📦 STOCK DISPONIBLE:\n\n"
for s in data:
for t in data[s]:
msg += f"{s} {t}: {len(data[s][t])}\n"
return msg

# ---------- USUARIOS ----------

def get_saldo(user):
data = load(USERS_FILE)
return data.get(str(user), 0)

def add_saldo(user, monto):
data = load(USERS_FILE)
data[str(user)] = data.get(str(user), 0) + monto
save(USERS_FILE, data)

def restar_saldo(user, monto):
data = load(USERS_FILE)
data[str(user)] -= monto
save(USERS_FILE, data)

# ---------- PRECIOS ----------

def set_price(service, tipo, price):
data = load(PRICES_FILE)
data.setdefault(service, {})[tipo] = price
save(PRICES_FILE, data)

def get_price(service, tipo):
data = load(PRICES_FILE)
return data.get(service, {}).get(tipo, 0)

# ---------- PARSE ----------

def parse(acc):
p = acc.split("_")
return p[0], p[1], p[2] if len(p) > 2 else "N/A"

# ---------- ENTREGA ----------

def entrega(service, email, password, perfil):
return f"""
━━━━━━━━━━━━━━━
🎬 VELTRIX
━━━━━━━━━━━━━━━

📱 APP: {service}
📧 {email}
🔑 {password}
👤 {perfil}

📜 REGLAS
❌ No modificar
👤 Usar perfil asignado
⚠️ No comprar dentro de la app

⏰ {now()}
━━━━━━━━━━━━━━━
"""

# ---------- MENU ----------

SERVICES = ["NETFLIX", "DISNEY", "SPOTIFY", "HBO"]

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
kb = []
for s in SERVICES:
kb.append([InlineKeyboardButton(s, callback_data=f"buy_{s}_perfil")])

```
await update.message.reply_text(
    "🛒 Selecciona servicio:",
    reply_markup=InlineKeyboardMarkup(kb)
)
```

# ---------- CALLBACK ----------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()

```
data = q.data

if data.startswith("buy_"):
    _, service, tipo = data.split("_")

    price = get_price(service, tipo)
    saldo = get_saldo(q.from_user.id)

    if saldo < price:
        await q.edit_message_text(f"❌ Saldo insuficiente\n💰 Tienes: {saldo}")
        return

    acc = get_stock(service, tipo)
    if not acc:
        await q.edit_message_text("❌ Sin stock")
        return

    email, password, perfil = parse(acc)

    restar_saldo(q.from_user.id, price)

    await q.edit_message_text(
        entrega(service, email, password, perfil) +
        f"\n💰 Saldo restante: {get_saldo(q.from_user.id)}"
    )
```

# ---------- ADMIN ----------

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
s = context.args[0].upper()
t = context.args[1].lower()
acc = context.args[2]

```
    add_stock(s, t, acc)
    await update.message.reply_text("✅ Stock agregado")
except:
    await update.message.reply_text("Uso: /setstock NETFLIX perfil correo_pass_perfil")
```

async def verstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(count_stock())

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
user = context.args[0]
monto = int(context.args[1])

```
    add_saldo(user, monto)
    await update.message.reply_text("💰 Saldo agregado")
except:
    await update.message.reply_text("Uso: /addsaldo ID MONTO")
```

async def setsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
s = context.args[0].upper()
t = context.args[1].lower()
p = int(context.args[2])

```
    set_price(s, t, p)
    await update.message.reply_text("💲 Precio actualizado")
except:
    await update.message.reply_text("Uso: /setsaldo NETFLIX perfil 50")
```

# ---------- MAIN ----------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("comprar", comprar))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("verstock", verstock))
app.add_handler(CommandHandler("addsaldo", addsaldo))
app.add_handler(CommandHandler("setsaldo", setsaldo))

app.add_handler(CallbackQueryHandler(buttons))

print("🔥 BOT TIENDA ACTIVO")
app.run_polling()
