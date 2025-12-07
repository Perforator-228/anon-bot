import os
import logging

# Сначала настраиваем логи
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Берем переменные из Railway
TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = os.getenv('YOUR_ID')

# Проверяем переменные
if not TOKEN:
    logger.error("❌ ОШИБКА: Нет переменной BOT_TOKEN!")
    exit()

if not YOUR_ID:
    logger.error("❌ ОШИБКА: Нет переменной YOUR_ID!")
    exit()

try:
    YOUR_ID = int(YOUR_ID)
    logger.info(f"✅ ID получен: {YOUR_ID}")
except ValueError:
    logger.error(f"❌ ОШИБКА: YOUR_ID должен быть цифрами! Получено: {YOUR_ID}")
    exit()

# Теперь импортируем telegram (после проверок)
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    logger.info("✅ Библиотеки загружены")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта библиотек: {e}")
    logger.error("Проверь requirements.txt - должны быть: python-telegram-bot==20.7 и imghdr")
    exit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('👋 Привет! Я анонимный бот. Отправь мне сообщение.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пропускаем свои сообщения
    if update.effective_user.id == YOUR_ID:
        return
    
    # Получаем текст
    text = update.message.text or update.message.caption or "📎 Медиа-сообщение"
    
    # Формируем сообщение
    user = update.effective_user
    message_to_admin = f"📩 Новое сообщение:\n\n{text}\n\n"
    message_to_admin += f"👤 ID отправителя: {user.id}"
    
    try:
        # Отправляем тебе
        await context.bot.send_message(
            chat_id=YOUR_ID,
            text=message_to_admin
        )
        
        # Подтверждаем отправителю
        await update.message.reply_text("✅ Отправлено!")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")

def main():
    logger.info("🚀 Запускаю бота...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Бот запущен!")
        logger.info("⏳ Ожидаю сообщения...")
        
        # Запускаем
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
