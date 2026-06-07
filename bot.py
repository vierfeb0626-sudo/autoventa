import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "TU_TOKEN_AQUI"
STOCK_FILE = "stock.json"

# ---------- UTILIDADES ----------

def load_json(file):
if not os.path.exists(file):
return {}
with open(file, "r") as f:
return json.load(f)

def save_json(file, data):
with open(file, "w") as f:
json.dump(data, f, indent=4)

def now():
return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ---------- STOCK ----------

def add_stock(service, tipo, account):
stock = load_json(STOCK_FILE)
stock.setdefault(service, {}).setdefault(tipo, []).append(account)
save_json(STOCK_FILE, stock)

def get_stock(service, tipo):
stock = load_json(STOCK_FILE)
try:
return stock[service][tipo].pop(0)
except:
return None

# ---------- PARSE ----------

def parse_account(acc):
parts = acc.split("_")
email = parts[0]
password = parts[1]
profile = parts[2] if len(parts) > 2 else "N/A"
return email, password, profile

# ---------- ENTREGA ----------

def build_delivery(service, email, password, profile):
return f"""
━━━━━━━━━━━━━━━
🎬 VELTRIX STREAMING
━━━━━━━━━━━━━━━

📱 APP: {service}
📧 CORREO: {email}
🔑 PASS: {password}
👤 PERFIL: {profile}

━━━━━━━━━━━━━━━
📜 REGLAS
━━━━━━━━━━━━━━━
❌ No modificar datos
👤 Usar perfil asignado
⚠️ Compras dentro de la app = pérdida de garantía

⏰ FECHA: {now()}
━━━━━━━━━━━━━━━
"""

# ---------- COMBOS ----------

COMBOS = {
"mexico": ["NETFLIX", "DISNEY", "SPOTIFY"],
"premium": ["NETFLIX", "DISNEY", "PRIME", "HBO"],
"mundial": ["IPTV", "VIX", "YOUTUBE"]
}

SERVICES = ["NETFLIX", "DISNEY", "SPOTIFY", "PRIME", "HBO"]

# ---------- MENÚ PRINCIPAL ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
keyboard = [
[InlineKeyboardButton("👤 Perfiles", callback_data="perfil")],
[InlineKeyboardButton("📺 Cuentas Completas", callback_data="completa")],
[InlineKeyboardButton("🔥 Combos", callback_data="combos")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

```
await update.message.reply_text("🔥 BIENVENIDO A VELTRIX\nSelecciona una opción:", reply_markup=reply_markup)
```

# ---------- CALLBACKS ----------

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

```
data = query.data

# MENÚ PERFILES / COMPLETAS
if data in ["perfil", "completa"]:
    tipo = data

    keyboard = []
    for s in SERVICES:
        keyboard.append([InlineKeyboardButton(s, callback_data=f"buy_{s}_{tipo}")])

    keyboard.append([InlineKeyboardButton("⬅️ Volver", callback_data="back")])

    await query.edit_message_text("Selecciona servicio:", reply_markup=InlineKeyboardMarkup(keyboard))

# MENÚ COMBOS
elif data == "combos":
    keyboard = []
    for c in COMBOS.keys():
        keyboard.append([InlineKeyboardButton(c.upper(), callback_data=f"combo_{c}")])

    keyboard.append([InlineKeyboardButton("⬅️ Volver", callback_data="back")])

    await query.edit_message_text("🔥 Combos disponibles:", reply_markup=InlineKeyboardMarkup(keyboard))

# COMPRAR SERVICIO
elif data.startswith("buy_"):
    _, service, tipo = data.split("_")

    acc = get_stock(service, tipo)

    if not acc:
        await query.edit_message_text("❌ Sin stock disponible")
        return

    email, password, profile = parse_account(acc)
    msg = build_delivery(service, email, password, profile)

    await query.edit_message_text(msg)

# COMPRAR COMBO
elif data.startswith("combo_"):
    combo_name = data.split("_")[1]

    services = COMBOS[combo_name]

    entrega = f"🔥 COMBO VELTRIX: {combo_name.upper()}\n\n"

    cuentas = []

    for s in services:
        acc = get_stock(s, "perfil")
        if not acc:
            await query.edit_message_text(f"❌ Sin stock en {s}")
            return
        cuentas.append((s, acc))

    for s, acc in cuentas:
        email, password, profile = parse_account(acc)

        entrega += f"""
```

📱 {s}
📧 {email}
🔑 {password}
👤 {profile}
━━━━━━━━━━━━━━━
"""

```
    entrega += f"\n⏰ FECHA: {now()}"

    await query.edit_message_text(entrega)

# VOLVER
elif data == "back":
    await start(update, context)
```

# ---------- ADMIN ----------

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
service = context.args[0].upper()
tipo = context.args[1].lower()
account = context.args[2]

```
    add_stock(service, tipo, account)

    await update.message.reply_text("✅ Stock agregado")
except:
    await update.message.reply_text("❌ Uso: /setstock NETFLIX perfil correo_pass_perfil")
```

# ---------- MAIN ----------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CallbackQueryHandler(menu_handler))

print("🔥 BOT CON BOTONES ACTIVO")
app.run_polling()
