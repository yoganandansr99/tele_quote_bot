import requests
import asyncio
from telegram import Update,BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, ContextTypes
import logging


BOT_TOKEN = '8384433707:AAGEZN-15TPkhIwz57Mem7AeW5eSoNzARng'
UNSPLASH_ACCESS_KEY = '0fKaXM_4WtGjSCFgn09WWnpVa39sbxY892VToTs6lUE'
user_jobs={}
# Logging
logging.basicConfig(level=logging.INFO)

# Get quote from ZenQuotes API
def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    if response.status_code == 200:
        data = response.json()[0]
        quote = data['q']
        author = data['a']
        return quote, author,1
    else:
        return "Be — don't try to become.", "Osho",0

# Get image URL from Unsplash API
def get_image_url(query):
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&client_id={UNSPLASH_ACCESS_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()['results']
        if results:
            return results[0]['urls']['regular']
    return None

# Command handler to manually get a quote
async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote_text, author,num = get_quote()
    # if any error
    if num==0:
        await update.message.reply_text("There is error in fetching data enjoy below one example quote")

    keyword = quote_text.split()[0]  # Simple keyword extraction
    image_url = get_image_url(keyword)

    caption = f"<b>{quote_text}</b>\n<i>~ {author}</i>"

    if image_url:
        await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")
    else:
        await update.message.reply_text(text=caption, parse_mode="HTML")

# Auto-send quote every 12 hours
async def auto_send_quote(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    quote_text, author,num = get_quote()

    if num==0:
        await context.bot.send_message("There is error in fetching data enjoy below one example quote")

    keyword = quote_text.split()[0]
    image_url = get_image_url(keyword)
    caption = f"<b>{quote_text}</b>\n<i>— {author}</i>"

    if image_url:
        await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")

# Start command: register user for auto sending
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user=update.message.from_user
    first_name=user.first_name
    await update.message.reply_text(f"Hello {first_name}!,have a good day \n go >> /help")

# scheduler
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Avoid multiple jobs for same user
    if chat_id in user_jobs:
        await update.message.reply_text("You're already subscribed.")
        return

    # Schedule the job
    job = context.job_queue.run_repeating(
        auto_send_quote,
        interval=86400,  # every 24 hours
        first=5,
        data=chat_id,
        name=str(chat_id)
    )

    user_jobs[chat_id] = job  # Store reference
    await update.message.reply_text("You've been subscribed to daily quotes!")

#schedule discarder
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    job = user_jobs.get(chat_id)

    if job:
        job.schedule_removal()
        del user_jobs[chat_id]
        await update.message.reply_text("You've been unsubscribed.")
    else:
        await update.message.reply_text("You're not subscribed.")


async def message_handler(update:Update,context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pls click >> /help  for more info")

async def help(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("this bot can insipire u today \n for quote >> /quote \n for everyday day quote >> /subscribe")

async def inv(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Invalid Command \npls go >> /help")       

async def set_commands(app):
    commands = [
        BotCommand("start", "🟩 To check bot is alive or not"),
        BotCommand("subscribe", "📖 To Get a quote everyday"),
        BotCommand("quote", "🎞️ To inspire Today"),
        BotCommand("help", "🖥️ To get help message"),
        BotCommand("unsubscribe","🟥 To stop receiving quotes")
    ]
    await app.bot.set_my_commands(commands)

# Main
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quote", quote))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,message_handler))
    app.add_handler(CommandHandler("help",help))
    app.add_handler(CommandHandler("subscribe",subscribe))
    app.add_handler(CommandHandler("unsubscribe",unsubscribe))
    app.add_handler(MessageHandler(filters.COMMAND,inv))
    

    app.post_init = set_commands

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
