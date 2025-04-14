from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN

async def start_command(update, context):
    await update.message.reply_text("Привет! Бот Plast Expert Tools работает!")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))

print("Бот запущен!")
app.run_polling()