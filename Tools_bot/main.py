import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.start import start_command, handle_registration

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Инициализация приложения ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Хендлеры ===
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^(reg_|skip_admin)$"))

# === Запуск ===
print("Бот запущен.")
app.run_polling()