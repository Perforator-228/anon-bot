from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# Берем данные из переменных окружения Railway
TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = int(os.getenv('YOUR_ID'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('👋 Привет! Отправь мне любое сообщение, и я анонимно передам его админу.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Игнорируем сообщения от самого админа
    if update.effective_user.id == YOUR_ID:
        return
    
    # Получаем текст или подпись
    text = update.message.text or update.message.caption
    
    # Формируем сообщение для админа
    user_info = f"👤 Пользователь: @{update.effective_user.username or 'без username'}"
    user_info += f"\n🆔 ID: {update.effective_user.id}"
    
    if text:
        message_to_admin = f"📩 *Новое анонимное сообщение:*\n\n{text}\n\n_{user_info}_"
    else:
        message_to_admin = f"📩 *Новое медиа-сообщение*\n\n_{user_info}_"
    
    # Отправляем админу
    await context.bot.send_message(
        chat_id=YOUR_ID,
        text=message_to_admin,
        parse_mode='Markdown'
    )
    
    # Отправляем медиа, если есть
    if update.message.photo:
        await context.bot.send_photo(
            chat_id=YOUR_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"📸 Фото" + (f": {text}" if text else "")
        )
    
    # Подтверждение отправителю
    await update.message.reply_text("✅ Сообщение отправлено анонимно!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
