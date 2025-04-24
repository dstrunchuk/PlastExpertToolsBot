import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.start import start_command, handle_registration
from handlers.tools import handle_tool_action
from handlers.menu import show_main_menu
from telegram.ext import MessageHandler, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Инициализация приложения ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Хендлеры ===
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^(reg_|skip_admin)$"))
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^find_tool$"))  # Поиск инструмента
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tool_action))  # Обработка ID
app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_back$"))  # Кнопка "Назад"
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^(take|transfer|store|request):"))  # Действия с инструментами
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^search_by_id$"))  # Поиск инструмента через кнопку

# === Запуск ===
print("Бот запущен.")
app.run_polling()