import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем переменные
TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = os.getenv('YOUR_ID')

logger.info(f"Токен: {'Есть' if TOKEN else 'НЕТ'}")
logger.info(f"ID: {YOUR_ID or 'НЕТ'}")

# Проверки
if not TOKEN:
    logger.error("❌ НЕТ BOT_TOKEN! Добавь в Railway Variables")
    exit()
    
if not YOUR_ID:
    logger.error("❌ НЕТ YOUR_ID! Добавь в Railway Variables")
    exit()

try:
    YOUR_ID = int(YOUR_ID)
except ValueError:
    logger.error(f"❌ YOUR_ID должен быть цифрами! Сейчас: {YOUR_ID}")
    exit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🤖 Бот запущен! Отправь мне сообщение.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пропускаем свои сообщения
    if update.effective_user.id == YOUR_ID:
        return
    
    # Получаем текст
    text = update.message.text or update.message.caption or "📎 Медиа"
    
    # Формируем сообщение
    user_info = f"👤 ID: {update.effective_user.id}"
    if update.effective_user.username:
        user_info += f" (@{update.effective_user.username})"
    
    # Отправляем тебе
    try:
        await context.bot.send_message(
            chat_id=YOUR_ID,
            text=f"📩 *Новое сообщение:*\n\n{text}\n\n{user_info}",
            parse_mode='Markdown'
        )
        await update.message.reply_text("✅ Сообщение отправлено!")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await update.message.reply_text("❌ Ошибка!")

def main():
    logger.info("🚀 Запускаю бота...")
    
    try:
        app = Application.builder().token(TOKEN).build()
        logger.info("✅ Приложение создано")
    except Exception as e:
        logger.error(f"❌ Ошибка создания приложения: {e}")
        return
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL,
        handle_message
    ))
    
    logger.info("✅ Бот запущен и слушает сообщения...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
