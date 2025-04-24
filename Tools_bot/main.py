from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.start import start_command, handle_registration
from handlers.tools import handle_tool_action
from telegram.ext import MessageHandler, filters
from handlers.menu import show_main_menu
from telegram.ext import CallbackQueryHandler
from dotenv import load_dotenv
import os

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Хендлеры
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^(register:|skip_admin)$"))
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^(take|transfer|store|request):"))
app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_back$"))

# Запуск бота
print("Бот запущен.")
app.run_polling()