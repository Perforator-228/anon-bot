import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = int(os.getenv('YOUR_ID'))

def start(update, context):
    update.message.reply_text('📨 Анонимный ящик. Отправляй сообщения - они дойдут без сохранения данных.')

def handle_message(update, context):
    if update.message.from_user.id == YOUR_ID:
        return
    
    text = update.message.text or update.message.caption or "[Медиа-файл]"
    
    # Только для логов (не видно пользователям)
    logger.info(f"📨 Анонимное сообщение получено")
    
    # Отправляем тебе - полностью чистое сообщение
    context.bot.send_message(
        chat_id=YOUR_ID,
        text=f"{text}"
    )
    
    # Подтверждение
    update.message.reply_text("✅ Доставлено")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.all, handle_message))
    
    logger.info("✅ Анонимный бот запущен")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
