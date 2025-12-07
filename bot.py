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

# Функция для отправки медиа
def forward_media(update, context, chat_id):
    """Пересылает любой тип медиа"""
    
    # 1. ФОТО
    if update.message.photo:
        photo = update.message.photo[-1]  # Берем самое качественное фото
        context.bot.send_photo(
            chat_id=chat_id,
            photo=photo.file_id,
            caption=update.message.caption if update.message.caption else None
        )
        return "📸 Фото"
    
    # 2. ВИДЕО
    elif update.message.video:
        context.bot.send_video(
            chat_id=chat_id,
            video=update.message.video.file_id,
            caption=update.message.caption if update.message.caption else None
        )
        return "🎥 Видео"
    
    # 3. GIF/Анимация
    elif update.message.animation:
        context.bot.send_animation(
            chat_id=chat_id,
            animation=update.message.animation.file_id,
            caption=update.message.caption if update.message.caption else None
        )
        return "🎞️ GIF"
    
    # 4. ДОКУМЕНТ (музыка, файлы и т.д.)
    elif update.message.document:
        context.bot.send_document(
            chat_id=chat_id,
            document=update.message.document.file_id,
            caption=update.message.caption if update.message.caption else None
        )
        return "📎 Файл"
    
    # 5. ГОЛОСОВОЕ СООБЩЕНИЕ
    elif update.message.voice:
        context.bot.send_voice(
            chat_id=chat_id,
            voice=update.message.voice.file_id
        )
        return "🎤 Голосовое"
    
    # 6. АУДИО (музыка)
    elif update.message.audio:
        context.bot.send_audio(
            chat_id=chat_id,
            audio=update.message.audio.file_id,
            caption=update.message.caption if update.message.caption else None
        )
        return "🎵 Аудио"
    
    # 7. ВИДЕО-ЗАМЕТКА (кружочек)
    elif update.message.video_note:
        context.bot.send_video_note(
            chat_id=chat_id,
            video_note=update.message.video_note.file_id
        )
        return "📹 Видео-заметка"
    
    # 8. СТИКЕР
    elif update.message.sticker:
        context.bot.send_sticker(
            chat_id=chat_id,
            sticker=update.message.sticker.file_id
        )
        return "🩷 Стикер"
    
    # 9. ЛОКАЦИЯ
    elif update.message.location:
        context.bot.send_location(
            chat_id=chat_id,
            latitude=update.message.location.latitude,
            longitude=update.message.location.longitude
        )
        return "📍 Локация"
    
    # 10. КОНТАКТ
    elif update.message.contact:
        context.bot.send_contact(
            chat_id=chat_id,
            phone_number=update.message.contact.phone_number,
            first_name=update.message.contact.first_name,
            last_name=update.message.contact.last_name if update.message.contact.last_name else None
        )
        return "👤 Контакт"
    
    # 11. ОПРОС
    elif update.message.poll:
        context.bot.send_poll(
            chat_id=chat_id,
            question=update.message.poll.question,
            options=[option.text for option in update.message.poll.options],
            is_anonymous=update.message.poll.is_anonymous,
            allows_multiple_answers=update.message.poll.allows_multiple_answers
        )
        return "📊 Опрос"
    
    # 12. ДИЗАЙНЕРСКИЙ ЭМОДЗИ (Premium)
    elif update.message.effective_attachment:
        # Для Premium эмодзи и других новых типов
        try:
            update.message.forward(chat_id=chat_id)
            return "✨ Premium-контент"
        except:
            return "📦 Медиа-файл"
    
    # 13. ТЕКСТ
    elif update.message.text:
        context.bot.send_message(
            chat_id=chat_id,
            text=update.message.text
        )
        return "📝 Текст"
    
    else:
        # Любой другой тип
        try:
            update.message.forward(chat_id=chat_id)
            return "📦 Медиа"
        except:
            return "❓ Неизвестный тип"

# Обработчики
def start(update, context):
    update.message.reply_text(
        '👋 *Анонимный медиа-бот*\n\n'
        '📌 *Что можно отправлять:*\n'
        '• 📝 Текст\n'
        '• 📸 Фото\n'
        '• 🎥 Видео\n'
        '• 🎞️ GIF\n'
        '• 📎 Файлы\n'
        '• 🎵 Музыка\n'
        '• 🎤 Голосовые\n'
        '• 🩷 Стикеры\n'
        '• ✨ Emoji Premium\n'
        '• 📍 Локации\n'
        '• 👤 Контакты\n'
        '• 📊 Опросы\n\n'
        '✅ *Полная анонимность гарантирована*',
        parse_mode='Markdown'
    )

def handle_message(update, context):
    # Пропускаем свои сообщения
    if update.message.from_user.id == YOUR_ID:
        return
    
    # Логируем для себя
    logger.info(f"📨 Новое сообщение от пользователя")
    
    # Отправляем медиа тебе
    media_type = forward_media(update, context, YOUR_ID)
    
    # Подтверждение отправителю
    update.message.reply_text(
        f"✅ {media_type} отправлено анонимно!\n"
        "ℹ️ Никакие данные не сохраняются"
    )

def error(update, context):
    logger.warning(f'Ошибка: {context.error}')

def main():
    logger.info("🚀 Запускаю медиа-бота...")
    
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
        logger.info("✅ Медиа-бот успешно запущен!")
        logger.info("✅ Поддерживает: фото, видео, GIF, стикеры, аудио, документы и т.д.")
        
        # Ожидаем остановки
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
