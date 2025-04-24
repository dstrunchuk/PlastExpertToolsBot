from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.start import start_command, handle_registration
from handlers.tools import handle_tool_action
from handlers.tools import process_tool_id
from handlers.menu import show_main_menu
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_tool_id))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^register:"))

# Запуск бота
print("Бот запущен.")
app.run_polling()