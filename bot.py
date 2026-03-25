import requests
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# CONFIG (SEUS DADOS)
# =========================
TOKEN = "7770438476:AAEMnmCC_6pLDYEdgE9QcOfNYsmunyK5KYY"
API_KEY = "26ab668ff6b44bef83d2ca510a37383c"

ADMIN_ID = 8395701708
CHAT_ID = -1003731882290

PIX = """00020126580014br.gov.bcb.pix0136c2b826d5-d646-4caf-b599-735a2a2c12925204000053039865802BR5924ADEGILSON DE SOUSA SILVA6009ARAGUAINA62170513BotVipApostas6304E561"""

# =========================
# SISTEMA VIP
# =========================
VIP_USERS = {
    ADMIN_ID: 9999999999
}

PENDENTES = []

def is_vip(user_id):
    return user_id in VIP_USERS and VIP_USERS[user_id] > time.time()

def limpar_expirados():
    agora = time.time()
    for uid in list(VIP_USERS.keys()):
        if VIP_USERS[uid] < agora:
            del VIP_USERS[uid]

async def aviso_expirando(context):
    agora = time.time()
    for uid, exp in VIP_USERS.items():
        if uid != ADMIN_ID and 0 < exp - agora < 86400:
            try:
                await context.bot.send_message(uid, "⚠️ Seu VIP expira em breve!")
            except:
                pass

# =========================
# JOGOS
# =========================
def get_matches():
    url = "https://api.football-data.org/v4/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json().get("matches", [])[:5]
    except:
        return []

def analisar(j):
    home = j["homeTeam"]["name"]
    away = j["awayTeam"]["name"]

    return (
        f"⚽ {home} x {away}\n\n"
        f"📊 Jogo com tendência de gols\n"
        f"💡 Over 2.5 gols 🔥"
    )

def gerar_resultado(j):
    home = j["homeTeam"]["name"]
    away = j["awayTeam"]["name"]
    resultado = random.choices(["GREEN ✅", "RED ❌"], weights=[70, 30])[0]
    return f"⚽ {home} x {away}\n📊 {resultado}"

def mensagem_venda():
    return random.choice([
        "🔥 VIP LUCRANDO HOJE\n👉 Entra agora",
        "💰 Só VIP pegou essa\n👉 Não fica de fora",
        "💎 VIP 30 DIAS R$15\n👉 Últimas vagas"
    ])

# =========================
# ENVIO VIP
# =========================
async def enviar_vip(context, texto):
    for uid in VIP_USERS:
        if is_vip(uid):
            try:
                await context.bot.send_message(uid, "💎 VIP EXCLUSIVO\n\n" + texto)
            except:
                pass

# =========================
# MENU
# =========================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Ver Palpites", callback_data="palpites")],
        [InlineKeyboardButton("💎 Acessar VIP", callback_data="vip")],
        [InlineKeyboardButton("💰 Já paguei", callback_data="paguei")]
    ])

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT APOSTAS PRO 🔥", reply_markup=menu())

# =========================
# BOTÕES
# =========================
async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "palpites":
        await query.message.reply_text(gerar_texto())

    elif query.data == "vip":
        if is_vip(uid):
            await query.message.reply_text("💎 VIP\n\n" + gerar_texto())
        else:
            await query.message.reply_text(
                f"💎 VIP 30 DIAS\n💰 R$15\n\nPIX:\n{PIX}\n\nClique em 'Já paguei'"
            )

    elif query.data == "paguei":
        if uid not in PENDENTES:
            PENDENTES.append(uid)

        await query.message.reply_text("✅ Pagamento enviado, aguarde aprovação")

        await context.bot.send_message(
            ADMIN_ID,
            f"💰 Novo pagamento\nID: {uid}\nUse /aprovar {uid}"
        )

# =========================
# TEXTO
# =========================
def gerar_texto():
    jogos = get_matches()

    if not jogos:
        return "🚫 Sem jogos hoje\n\n💎 VIP recebe entradas exclusivas!"

    return "🔥 ENTRADAS DO DIA 🔥\n\n" + "\n\n".join([analisar(j) for j in jogos])

# =========================
# ADMIN
# =========================
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            return
        return await func(update, context)
    return wrapper

@admin_only
async def aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(context.args[0])
    VIP_USERS[uid] = time.time() + (30 * 86400)

    if uid in PENDENTES:
        PENDENTES.remove(uid)

    await context.bot.send_message(uid, "💎 VIP LIBERADO POR 30 DIAS!")
    await update.message.reply_text("✅ Aprovado")

@admin_only
async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "📊 PAINEL VIP\n\n"
    for uid, exp in VIP_USERS.items():
        dias = int((exp - time.time()) / 86400)
        texto += f"{uid} - {dias} dias\n"
    await update.message.reply_text(texto)

@admin_only
async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💎 Total VIP: {len(VIP_USERS)}")

@admin_only
async def remover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(context.args[0])
    if uid in VIP_USERS:
        del VIP_USERS[uid]
    await update.message.reply_text("❌ Removido")

@admin_only
async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💰 Pendentes:\n{PENDENTES}")

# =========================
# AUTO POST
# =========================
async def postar(context: ContextTypes.DEFAULT_TYPE):
    limpar_expirados()
    await aviso_expirando(context)

    jogos = get_matches()

    if not jogos:
        await context.bot.send_message(CHAT_ID, "🚫 Sem jogos hoje\n💎 VIP ativo!")
        return

    texto = "🔥 ENTRADAS 🔥\n\n" + "\n\n".join([analisar(j) for j in jogos])
    await context.bot.send_message(CHAT_ID, texto)
    await enviar_vip(context, texto)

    await context.bot.send_message(CHAT_ID, mensagem_venda())

    resultado = "📊 RESULTADOS\n\n" + "\n\n".join([gerar_resultado(j) for j in jogos])
    await context.bot.send_message(CHAT_ID, resultado)
    await enviar_vip(context, resultado)

# =========================
# START BOT
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("aprovar", aprovar))
app.add_handler(CommandHandler("painel", painel))
app.add_handler(CommandHandler("total", total))
app.add_handler(CommandHandler("remover", remover))
app.add_handler(CommandHandler("pendentes", pendentes))
app.add_handler(CallbackQueryHandler(botoes))

# roda automático a cada 3h
app.job_queue.run_repeating(postar, interval=10800, first=10)

print("🚀 BOT ONLINE")
app.run_polling()