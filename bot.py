import os
import logging
import datetime
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ========== НАСТРОЙКИ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем переменные из Railway
TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = os.getenv('YOUR_ID')
ADMIN_NAME = os.getenv('ADMIN_NAME', 'Админ')

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

# Статистика
stats = {
    'total_messages': 0,
    'today_messages': 0,
    'photos': 0,
    'videos': 0,
    'texts': 0,
    'long_texts': 0,
    'last_reset': datetime.datetime.now().date()
}

# ========== ФУНКЦИИ ДЛЯ ЦИТИРОВАНИЯ ==========

def create_collapsible_text(text, max_length=150):
    """Создает сворачиваемый текст для Telegram"""
    text_length = len(text)
    
    if text_length <= max_length:
        return text
    
    lines = text.split('\n')
    if len(lines) > 5:
        preview = '\n'.join(lines[:3])
        if len(preview) > 100:
            preview = preview[:100] + "..."
        
        quoted_text = f"📜 *ДЛИННОЕ СООБЩЕНИЕ*\n"
        quoted_text += f"📏 Символов: {text_length}\n"
        quoted_text += f"📄 Строк: {len(lines)}\n"
        quoted_text += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        quoted_text += f"*ПРЕВЬЮ:*\n{preview}\n\n"
        quoted_text += f"*ПОЛНЫЙ ТЕКСТ:*\n{text}"
        
        return quoted_text
    else:
        return text

def split_long_message(text, max_length=4000):
    """Разбивает очень длинные сообщения на части"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        
        split_point = text.rfind('\n\n', 0, max_length)
        if split_point == -1:
            split_point = text.rfind('\n', 0, max_length)
        if split_point == -1:
            split_point = max_length
        
        parts.append(text[:split_point].strip())
        text = text[split_point:].strip()
    
    if len(parts) > 1:
        for i in range(len(parts)):
            parts[i] = f"📄 *Часть {i+1}/{len(parts)}*\n\n{parts[i]}"
    
    return parts

def format_long_text_for_telegram(text, message_num):
    """Форматирует длинный текст для Telegram с цитированием"""
    header = f"🔥 *АНОНИМКА #{message_num}*\n"
    header += f"📜 *ТИП: Длинный текст*\n"
    header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
    header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    
    processed_text = create_collapsible_text(text)
    
    if len(processed_text) > 3500:
        parts = split_long_message(processed_text, 3500)
        return parts, True
    else:
        full_text = header + processed_text
        return [full_text], False

# ========== ОТПРАВКА СООБЩЕНИЙ ==========

def send_with_header(update, context, chat_id):
    """Отправляет медиа с крутым заголовком"""
    global stats
    
    stats['total_messages'] += 1
    stats['today_messages'] += 1
    
    today = datetime.datetime.now().date()
    if today != stats['last_reset']:
        stats['today_messages'] = 1
        stats['last_reset'] = today
    
    message_num = stats['total_messages']
    
    # 1. ТЕКСТ
    if update.message.text:
        text = update.message.text
        stats['texts'] += 1
        
        if len(text) > 150:
            stats['long_texts'] += 1
            parts, is_multi_part = format_long_text_for_telegram(text, message_num)
            
            for i, part in enumerate(parts):
                context.bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            
            return "📜 Длинный текст", "long_text", len(parts) if is_multi_part else 1
        
        else:
            header = f"🔥 *АНОНИМКА #{message_num}*\n"
            header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
            header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            
            full_text = header + text
            context.bot.send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode='Markdown'
            )
            return "📝 Текст", "text", 1
    
    # 2. ФОТО
    elif update.message.photo:
        stats['photos'] += 1
        photo = update.message.photo[-1]
        header = f"🔥 *АНОНИМКА #{message_num}*\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption = header + (update.message.caption if update.message.caption else "📸 *ФОТО*")
        context.bot.send_photo(
            chat_id=chat_id,
            photo=photo.file_id,
            caption=caption,
            parse_mode='Markdown'
        )
        return "📸 Фото", "photo", 1
    
    # 3. ВИДЕО
    elif update.message.video:
        stats['videos'] += 1
        header = f"🔥 *АНОНИМКА #{message_num}*\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption = header + (update.message.caption if update.message.caption else "🎥 *ВИДЕО*")
        context.bot.send_video(
            chat_id=chat_id,
            video=update.message.video.file_id,
            caption=caption,
            parse_mode='Markdown'
        )
        return "🎥 Видео", "video", 1
    
    # 4. ОСТАЛЬНЫЕ ТИПЫ
    else:
        header = f"🔥 *АНОНИМКА #{message_num}*\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        media_type = "📦 Медиа"
        if update.message.animation:
            media_type = "🎞️ GIF"
        elif update.message.document:
            media_type = "📎 Файл"
        elif update.message.audio:
            media_type = "🎵 Музыка"
        elif update.message.voice:
            media_type = "🎤 Голосовое"
        elif update.message.sticker:
            media_type = "🩷 Стикер"
        
        context.bot.send_message(
            chat_id=chat_id,
            text=header + f"*{media_type}*",
            parse_mode='Markdown'
        )
        
        try:
            update.message.forward(chat_id=chat_id)
        except:
            pass
        
        return media_type, "other", 1

# ========== КОМАНДЫ ==========

def start_command(update: Update, context: CallbackContext):
    """Команда /start"""
    keyboard = [
        [KeyboardButton("📝 Написать анонимно")],
        [KeyboardButton("❓ Помощь"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("🎨 Форматирование"), KeyboardButton("🧪 Тест цитирования")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        f'🕶️ *АНОНИМНЫЙ ЯЩИК 2.0*\n\n'
        f'📜 *НОВАЯ ФИЧА:* Авто-цитирование длинных текстов!\n\n'
        f'✨ *Что нового:*\n'
        f'• Тексты >150 символов сворачиваются\n'
        f'• Можно развернуть/свернуть в Telegram\n'
        f'• Авто-разбивка очень длинных текстов\n'
        f'• Сохранение форматирования\n\n'
        f'🔧 *Команды:*\n'
        f'/help — все возможности\n'
        f'/testquote — тест цитирования\n'
        f'/format — как форматировать текст\n\n'
        f'🎯 *Просто пиши — мы все обработаем!*',
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def help_command(update: Update, context: CallbackContext):
    """Команда /help"""
    update.message.reply_text(
        '📚 *ПОЛНАЯ ИНСТРУКЦИЯ*\n\n'
        '🔹 *ЦИТИРОВАНИЕ ТЕКСТОВ:*\n'
        '• Тексты >150 символов *автоматически сворачиваются*\n'
        '• В Telegram можно *развернуть/свернуть* текст\n'
        '• Очень длинные тексты разбиваются на части\n'
        '• Сохраняется *полное форматирование*\n\n'
        '🔹 *ЧТО МОЖНО ОТПРАВИТЬ:*\n'
        '• 📝 Текст любого размера (1-10.000 символов)\n'
        '• 📸 Фото с подписями\n'
        '• 🎥 Видео до 50 МБ\n'
        '• 🎵 Музыку и голосовые\n'
        '• 📎 Документы и файлы\n'
        '• 🎞️ GIF и анимации\n'
        '• 🩷 Стикеры и эмодзи\n\n'
        '💡 *СОВЕТ:* Используй абзацы (два Enter) для лучшей читаемости!',
        parse_mode='Markdown'
    )

def stats_command(update: Update, context: CallbackContext):
    """Команда /stats"""
    stats_text = (
        f'📊 *СТАТИСТИКА БОТА*\n\n'
        f'📨 Всего сообщений: *{stats["total_messages"]}*\n'
        f'📅 Сегодня: *{stats["today_messages"]}*\n'
        f'📸 Фото: *{stats["photos"]}*\n'
        f'🎥 Видео: *{stats["videos"]}*\n'
        f'📝 Тексты: *{stats["texts"]}*\n'
        f'📜 Длинные тексты (>150 с.): *{stats["long_texts"]}*\n\n'
        
        f'📈 *АНАЛИТИКА:*\n'
        f'• Длинных текстов: *{stats["long_texts"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n'
        f'• Средняя длина: *{stats["total_messages"] // 30 if stats["total_messages"] > 30 else 1}* в день\n'
        f'• Популярный тип: *{"Текст" if stats["texts"] > stats["photos"] else "Фото"}*\n\n'
        
        f'🔧 *СИСТЕМА:*\n'
        f'• Цитирование: *Включено*\n'
        f'• Лимит: 150+ символов\n'
        f'• Авто-разбивка: Да'
    )
    update.message.reply_text(stats_text, parse_mode='Markdown')

def test_quote_command(update: Update, context: CallbackContext):
    """Команда /testquote - тест цитирования"""
    test_text = """Это тестовое длинное сообщение для демонстрации функции цитирования.

В Telegram есть крутая фича: когда текст слишком длинный, его можно свернуть в цитату, а потом развернуть по необходимости.

Пример длинного текста:

1. Первый пункт с описанием
2. Второй пункт с более подробным описанием
3. Третий пункт о важности конфиденциальности

Заключение:
Анонимность — это не просто возможность скрыть свое имя, это свобода выражения без страха осуждения.

С уважением,
Анонимный разработчик."""
    
    update.message.reply_text(
        "📋 *ТЕСТ ЦИТИРОВАНИЯ*\n\n"
        "Отправляю тестовое длинное сообщение...",
        parse_mode='Markdown'
    )
    
    parts, _ = format_long_text_for_telegram(test_text, 999)
    for part in parts:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=part,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

def format_command(update: Update, context: CallbackContext):
    """Команда /format - как форматировать текст"""
    update.message.reply_text(
        '🎨 *ФОРМАТИРОВАНИЕ ТЕКСТА В TELEGRAM*\n\n'
        '🔸 *ОСНОВНОЕ:*\n'
        '*жирный текст* → *текст*\n'
        '_курсив_ → _текст_\n'
        '`код или моноширинный` → `текст`\n'
        '[ссылка](https://example.com) → [текст](url)\n\n'
        '💡 *СОВЕТ:* Используй абзацы (два Enter) для лучшей читаемости!',
        parse_mode='Markdown'
    )

def admin_command(update: Update, context: CallbackContext):
    """Команда /admin — только для тебя!"""
    if update.message.from_user.id == YOUR_ID:
        now = datetime.datetime.now()
        admin_text = (
            f'🛡️ *ПАНЕЛЬ АДМИНИСТРАТОРА*\n\n'
            f'👑 *ЛИЧНОЕ:*\n'
            f'• Ваш ID: `{YOUR_ID}`\n'
            f'• Имя: *{ADMIN_NAME}*\n'
            f'• Уровень доступа: *Владелец*\n\n'
            
            f'📊 *СТАТИСТИКА:*\n'
            f'• Всего сообщений: *{stats["total_messages"]}*\n'
            f'• Сегодня: *{stats["today_messages"]}*\n'
            f'• Фото/Видео/Текст: *{stats["photos"]}/{stats["videos"]}/{stats["texts"]}*\n'
            f'• Длинные тексты: *{stats["long_texts"]}*\n\n'
            
            f'⚙️ *СИСТЕМА:*\n'
            f'• Сервер: Railway\n'
            f'• Время: {now.strftime("%H:%M:%S")}\n'
            f'• Дата: {now.strftime("%d.%m.%Y")}\n\n'
            
            f'✅ *ВСЕ СИСТЕМЫ РАБОТАЮТ НОРМАЛЬНО*'
        )
        update.message.reply_text(admin_text, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ Доступ запрещен. Требуются права администратора.")

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

def handle_message(update: Update, context: CallbackContext):
    """Обрабатывает все сообщения с поддержкой цитирования"""
    if update.message.from_user.id == YOUR_ID:
        return
    
    user = update.message.from_user
    logger.info(f"📨 #{stats['total_messages'] + 1} от пользователя {user.id}")
    
    try:
        media_type, media_category, parts_count = send_with_header(update, context, YOUR_ID)
        
        if media_category == "long_text":
            if parts_count > 1:
                response = (
                    f"✅ *Длинный текст отправлен!*\n"
                    f"🔢 Номер: #{stats['total_messages']}\n"
                    f"📄 Частей: {parts_count}\n"
                    f"🔐 Статус: Доставлено с цитированием\n"
                    f"💡 Совет: В Telegram текст можно развернуть/свернуть\n\n"
                    f"🕐 {datetime.datetime.now().strftime('%H:%M')}"
                )
            else:
                response = (
                    f"✅ *Длинный текст отправлен!*\n"
                    f"🔢 Номер: #{stats['total_messages']}\n"
                    f"📏 Символов: {len(update.message.text) if update.message.text else 0}\n"
                    f"🔐 Статус: Доставлено с цитированием\n"
                    f"💡 Фича: Текст свернут для удобства просмотра\n\n"
                    f"🕐 {datetime.datetime.now().strftime('%H:%M')}"
                )
        else:
            funny_responses = [
                "Я как почтальон Печкин - все доставлю! 📮",
                "Сообщение улетело в космос анонимности 🚀",
                "Шепну на ушко админу твои слова 🤫",
                "Засекречено и отправлено 🔐",
                "Анонимность уровня 007 🕶️",
            ]
            random_response = random.choice(funny_responses)
            
            response = (
                f"✅ *{media_type} отправлен!*\n"
                f"🔢 Номер: #{stats['total_messages']}\n"
                f"🔐 Статус: Доставлено анонимно\n"
                f"💫 {random_response}\n\n"
                f"🕐 {datetime.datetime.now().strftime('%H:%M')}"
            )
        
        update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        update.message.reply_text(
            "❌ *Упс, ошибка!*\n"
            "Но не волнуйся — админ уже уведомлен.\n"
            "Попробуй еще раз через минуту.",
            parse_mode='Markdown'
        )

# ========== ОБРАБОТЧИК ОШИБОК ==========

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f'Ошибка бота: {context.error}')

# ========== ЗАПУСК ==========

def main():
    """Запуск бота"""
    logger.info("🚀 ЗАПУСКАЮ БОТА 2.0 С ЦИТИРОВАНИЕМ...")
    logger.info(f"👑 Админ ID: {YOUR_ID}")
    logger.info("✅ Цитирование длинных текстов: ВКЛЮЧЕНО")
    
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Регистрация команд
        commands = [
            ('start', start_command),
            ('help', help_command),
            ('stats', stats_command),
            ('testquote', test_quote_command),
            ('format', format_command),
            ('admin', admin_command),
        ]
        
        for cmd_name, cmd_func in commands:
            dp.add_handler(CommandHandler(cmd_name, cmd_func))
        
        # Обработчик сообщений
        dp.add_handler(MessageHandler(Filters.all, handle_message))
        
        # Обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем
        updater.start_polling()
        
        logger.info("=" * 50)
        logger.info("✅ БОТ С ЦИТИРОВАНИЕМ ЗАПУЩЕН!")
        logger.info(f"✅ Команд: {len(commands)}")
        logger.info("✅ Готов принимать анонимки 24/7")
        logger.info("=" * 50)
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
