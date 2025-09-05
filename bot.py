# ================== CHECK ENV ==================
import sys
import subprocess
import os, shutil

def uninstall_pkg(pkg):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", pkg])
    except Exception:
        pass

def install_pkg(pkg, version=None):
    try:
        if version:
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{pkg}=={version}", "--force-reinstall"])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--force-reinstall"])
    except Exception as e:
        print("⚠️ Failed to install", pkg, ":", e)

# 1. Remove fake telegram/telebot
uninstall_pkg("telegram")
uninstall_pkg("telebot")

# 2. Delete leftovers
site_pkg = "/usr/local/lib/python3.12/dist-packages/telegram"
if os.path.exists(site_pkg):
    shutil.rmtree(site_pkg)

# 3. Install correct python-telegram-bot
install_pkg("python-telegram-bot", "20.3")

# ================== BOT CODE ==================
import nest_asyncio
nest_asyncio.apply()

import asyncio
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "7790549396:AAHcS06HmfuiKiK_vZHLok-mLSl0I_elZhM"
ADMIN_IDS = [6440196035]  # developer id
OWNER_USERNAME = "@DAOUD_VIP"
GROUP_LINK = "https://t.me/free_fire_liker"

SERVERS = {
    "ME": "Middle East",
    "EU": "Europe",
    "US": "United States",
    "AS": "Asia",
    "IND": "India"
}

user_data = {}

# ===== API function =====
def send_likes(uid, region):
    url = f"https://likes.ffgarena.cloud/api/v2/likes?uid={uid}&amount_of_likes=100&auth=trial-7d&region={region}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "nickname": data.get("nickname"),
                "likes_before": data.get("likes_antes"),
                "likes_after": data.get("likes_depois"),
                "level": data.get("level")
            }
        else:
            return {"success": False, "error": f"Status Code: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===== Start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    keyboard = [
        [InlineKeyboardButton(name, callback_data=code)] for code, name in SERVERS.items()
    ]
    keyboard.append([InlineKeyboardButton("📩 Contact Developer", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")])
    keyboard.append([InlineKeyboardButton("🌐 Join Group", url=GROUP_LINK)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Welcome!\nTo use this bot, first choose your server with /use.\n\nOwner: {OWNER_USERNAME}\nGroup: {GROUP_LINK}",
        reply_markup=reply_markup
    )

# ===== Use command (show servers) =====
async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=code)] for code, name in SERVERS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌍 Choose your server:", reply_markup=reply_markup)

# ===== Select server =====
async def select_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    region = query.data
    user_data[user_id] = {"region": region}
    await query.edit_message_text(f"✅ Server selected: {SERVERS[region]}\nNow send your UID.")

# ===== Handle UID =====
async def auto_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if not text.isdigit():
        return

    if user_id not in user_data or "region" not in user_data[user_id]:
        await update.message.reply_text("⚠️ Please choose a server first using /use")
        return

    uid = text
    region = user_data[user_id]["region"]
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, send_likes, uid, region)

    if result["success"]:
        likes_sent = 0
        if result.get("likes_before") is not None and result.get("likes_after") is not None:
            likes_sent = result["likes_after"] - result["likes_before"]

        msg = (
            f"Nickname: {result.get('nickname','N/A')}\n"
            f"Region: {region}\n"
            f"Level: {result.get('level','N/A')}\n"
            f"Likes Before: {result.get('likes_before','N/A')}\n"
            f"Likes After: {result.get('likes_after','N/A')}\n"
            f"Message: {likes_sent} likes\n\n"
            f"Owner: {OWNER_USERNAME}\nGroup: {GROUP_LINK}"
        )
        user_data[user_id].update({"uid": uid})
    else:
        msg = f"❌ Error: {result['error']}\n\nOwner: {OWNER_USERNAME}\nGroup: {GROUP_LINK}"

    await update.message.reply_text(msg)

# ===== Broadcast =====
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    for uid in user_data.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast from {OWNER_USERNAME}:\n\n{message}")
        except:
            pass
    await update.message.reply_text("✅ Broadcast sent.")

# ===== Setup bot =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("use", use))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CallbackQueryHandler(select_server))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_like))

print("🤖 Bot is running...")
app.run_polling()