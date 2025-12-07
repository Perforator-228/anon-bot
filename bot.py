import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем переменные из Railway
TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = os.getenv('YOUR_ID')

# Проверяем
if not TOKEN:
    logger.error("❌ Нет BOT_TOKEN! Добавь в Railway Variables")
    exit()

if not YOUR_ID:
    logger.error("❌ Нет YOUR_ID! Добавь в Railway Variables")
    exit()

try:
    YOUR_ID = int(YOUR_ID)
except ValueError:
    logger.error(f"❌ YOUR_ID должен быть цифрами! Сейчас: {YOUR_ID}")
    exit()

logger.info(f"✅ Токен: {TOKEN[:10]}...")
logger.info(f"✅ ID: {YOUR_ID}")

# Обработчики
def start(update, context):
    update.message.reply_text('👋 Привет! Я анонимный бот. Отправь мне любое сообщение.')

def handle_message(update, context):
    # Пропускаем свои сообщения
    if update.message.from_user.id == YOUR_ID:
        return
    
    user = update.message.from_user
    text = update.message.text or update.message.caption or "📎 Медиа-сообщение"
    
    logger.info(f"📨 Сообщение от {user.id}: {text[:50]}...")
    
    # Отправляем тебе
    context.bot.send_message(
        chat_id=YOUR_ID,
        text=f"📩 *Новое сообщение:*\n\n{text}\n\n👤 От: {user.id}",
        parse_mode='Markdown'
    )
    
    # Подтверждение отправителю
    update.message.reply_text("✅ Сообщение отправлено анонимно!")

def error(update, context):
    logger.warning(f'Ошибка: {context.error}')

def main():
    logger.info("🚀 Запускаю бота...")
    
    try:
        # Создаем updater
        updater = Updater(TOKEN, use_context=True)
        
        # Получаем dispatcher
        dp = updater.dispatcher
        
        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.all, handle_message))
        dp.add_error_handler(error)
        
        # Запускаем
        updater.start_polling()
        logger.info("✅ Бот успешно запущен и работает!")
        
        # Ожидаем остановки
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
