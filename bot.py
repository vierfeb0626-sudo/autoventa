import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

# ---------- PARSE ACCOUNT ----------

def parse_account(acc):
parts = acc.split("_")
email = parts[0]
password = parts[1]
profile = parts[2] if len(parts) > 2 else "N/A"
return email, password, profile

# ---------- ENTREGA INDIVIDUAL ----------

def build_delivery(service, email, password, profile):
return f"""
━━━━━━━━━━━━━━━
🎬 VELTRIX STREAMING
━━━━━━━━━━━━━━━

📱 APP: {service}
📧 CORREO: {email}
🔑 CONTRASEÑA: {password}
👤 PERFIL: {profile}

━━━━━━━━━━━━━━━
📜 REGLAS
━━━━━━━━━━━━━━━
❌ No modificar datos
👤 Usar solo perfil asignado
⚠️ Compras dentro de la app = pérdida de garantía

━━━━━━━━━━━━━━━
⏰ FECHA: {now()}
━━━━━━━━━━━━━━━
"""

# ---------- COMBOS ----------

COMBOS = {
"mexico": ["NETFLIX", "DISNEY", "SPOTIFY"],
"premium": ["NETFLIX", "DISNEY", "PRIME", "HBO"],
"mundial": ["IPTV", "VIX", "YOUTUBE"]
}

# ---------- COMANDOS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"🔥 Bienvenido a VELTRIX\n\n"
"Comandos:\n"
"/buy NETFLIX perfil\n"
"/buycombo mexico"
)

async def setstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
service = context.args[0].upper()
tipo = context.args[1].lower()
account = context.args[2]

```
    add_stock(service, tipo, account)

    await update.message.reply_text("✅ Cuenta agregada al stock")

except:
    await update.message.reply_text(
        "❌ Uso:\n/setstock NETFLIX perfil correo_pass_perfil"
    )
```

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
service = context.args[0].upper()
tipo = context.args[1].lower()

```
    account = get_stock(service, tipo)

    if not account:
        await update.message.reply_text("❌ Sin stock disponible")
        return

    email, password, profile = parse_account(account)

    msg = build_delivery(service, email, password, profile)

    await update.message.reply_text(msg)

except:
    await update.message.reply_text(
        "❌ Uso:\n/buy NETFLIX perfil"
    )
```

async def buycombo(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
combo_name = context.args[0].lower()

```
    if combo_name not in COMBOS:
        await update.message.reply_text("❌ Combo no existe")
        return

    services = COMBOS[combo_name]

    entrega = f"""
```

━━━━━━━━━━━━━━━
🔥 COMBO VELTRIX: {combo_name.upper()}
━━━━━━━━━━━━━━━
"""

```
    cuentas = []

    # VALIDAR STOCK COMPLETO
    for service in services:
        acc = get_stock(service, "perfil")
        if not acc:
            await update.message.reply_text(f"❌ Sin stock en {service}")
            return
        cuentas.append((service, acc))

    # CONSTRUIR ENTREGA
    for service, acc in cuentas:
        email, password, profile = parse_account(acc)

        entrega += f"""
```

📱 APP: {service}
📧 CORREO: {email}
🔑 PASS: {password}
👤 PERFIL: {profile}
━━━━━━━━━━━━━━━
"""

```
    entrega += f"""
```

📜 REGLAS
❌ No modificar datos
👤 Usar perfil asignado
⚠️ Compras dentro de la app = pérdida de garantía

⏰ FECHA: {now()}
━━━━━━━━━━━━━━━
"""

```
    await update.message.reply_text(entrega)

except:
    await update.message.reply_text("❌ Uso:\n/buycombo mexico")
```

# ---------- MAIN ----------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setstock", setstock))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("buycombo", buycombo))

print("🔥 BOT VELTRIX ACTIVO...")
app.run_polling()
                  
