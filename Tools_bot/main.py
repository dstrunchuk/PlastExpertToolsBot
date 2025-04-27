from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.tools import handle_view_tool, handle_view_tool_by_index, handle_tool_action, process_tool_id, export_one_tool_history, search_prev, search_next
from handlers.menu import (
    find_tool_handler,
    all_tools_handler,
    all_tools_prev,
    all_tools_next,
    my_tools_handler,
    my_tools_prev,
    my_tools_next,
    add_tool_handler,
    export_all_handler,
    show_main_menu,
    add_foreman_handler,
    add_object_handler,
)
from handlers.start import start_command, handle_registration
from handlers.database import (   # <<< Важно: вот так теперь!
    get_all_tools, get_tool_by_id, update_tool, log_action,
    get_all_foremen, get_all_users, get_tool_history,
    get_user_by_id, save_user, add_foreman_if_missing, update_foreman_id, add_tool
)
from dotenv import load_dotenv
import os

# Инициализация бота
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

async def on_startup(app):
    await app.bot.set_webhook(WEBHOOK_URL)
    print("✅ Бот подключен к Supabase и WebHook установлен!")

app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

# Хендлеры
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(find_tool_handler, pattern="^find_tool$"))
app.add_handler(CallbackQueryHandler(all_tools_handler, pattern="^all_tools$"))
app.add_handler(CallbackQueryHandler(search_prev, pattern="^search_prev$"))
app.add_handler(CallbackQueryHandler(search_next, pattern="^search_next$"))
app.add_handler(CallbackQueryHandler(all_tools_prev, pattern="^all_tools_prev$"))
app.add_handler(CallbackQueryHandler(all_tools_next, pattern="^all_tools_next$"))
app.add_handler(CallbackQueryHandler(my_tools_prev, pattern="^my_tools_prev$"))
app.add_handler(CallbackQueryHandler(my_tools_next, pattern="^my_tools_next$"))
app.add_handler(CallbackQueryHandler(my_tools_handler, pattern="^my_tools$"))
app.add_handler(CallbackQueryHandler(add_tool_handler, pattern="^add_tool$"))
app.add_handler(CallbackQueryHandler(export_all_handler, pattern="^export_all$"))
app.add_handler(CallbackQueryHandler(export_one_tool_history, pattern="^export_one:"))
app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_back$"))
app.add_handler(CallbackQueryHandler(add_foreman_handler, pattern="^add_foreman$"))
app.add_handler(CallbackQueryHandler(add_object_handler, pattern="^add_object$"))
app.add_handler(CallbackQueryHandler(handle_view_tool, pattern="^view_tool:"))
app.add_handler(CallbackQueryHandler(handle_view_tool_by_index, pattern="^view_tool_by_index:"))
app.add_handler(CallbackQueryHandler(handle_registration, pattern="^register:"))
app.add_handler(CallbackQueryHandler(handle_tool_action, pattern="^(take|store|request|transfer|assign|export|confirm_transfer|confirm_assign):"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_tool_id))
app.add_handler(CallbackQueryHandler(foremen_list_handler, pattern="^foremen_list$"))
app.add_handler(CallbackQueryHandler(show_foreman_tools_handler, pattern="^foreman_tools:"))

# Запуск бота через WebHook
print("Бот запущен через WebHook.")
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.getenv("PORT", 8080)),
    webhook_url=WEBHOOK_URL
)