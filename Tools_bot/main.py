from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import find_tool_handler, all_tools_handler, my_tools_handler, add_tool_handler, export_all_handler
from handlers.start import start_command, handle_registration
from handlers.tools import handle_tool_action
from handlers.tools import process_tool_id
from handlers.tools import handle_view_tool
from handlers.menu import show_main_menu
from dotenv import load_dotenv
import os

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Хендлеры


app.add_handler(CallbackQueryHandler(find_tool_handler, pattern="^find_tool$"))
app.add_handler(CallbackQueryHandler(all_tools_handler, pattern="^all_tools$"))
app.add_handler(CallbackQueryHandler(my_tools_handler, pattern="^my_tools$"))
app.add_handler(CallbackQueryHandler(add_tool_handler, pattern="^add_tool$"))
app.add_handler(CallbackQueryHandler(export_all_handler, pattern="^export_all$"))
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_view_tool, pattern="^view_tool:"))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^(register:|skip_admin)$"))
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^(take|transfer|store|request):"))
app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_back$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_tool_id))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^register:"))
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^(take|store|request|transfer|assign|export|confirm_transfer|confirm_assign):"))

# Запуск бота
print("Бот запущен.")
app.run_polling()