from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
from dotenv import load_dotenv
import os

from handlers.start import start_command, handle_registration

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Запуск бота ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Обработчики ===
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^(reg_|skip_admin)$"))

print("Бот запущен.")
app.run_polling()