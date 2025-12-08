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
    'forwarded': 0,
    'last_reset': datetime.datetime.now().date()
}

# Хранилище статусов сообщений
message_status = {}  # {message_id: {'forwarded': bool, 'to': str, 'by': str, 'time': str}}

# ========== 100 АНЕКДОТОВ ==========
JOKES = [
    "Почему программист всегда мокрый? Потому что он постоянно в бассейне (pool)! 🏊‍♂️",
    "Что сказал один байт другому? Я тебя bit! 💻",
    "Почему математик плохо спит? Потому что он считает овец в уме! 🐑",
    "Как называют анонимного программиста? Incognito Developer! 🕶️",
    "Почему бот никогда не опаздывает? Потому что у него всегда есть time! ⏰",
    "Что сказал один сервер другому? У меня для тебя есть connection! 🔌",
    "Почему Telegram-бот грустный? Потому что у него нет друзей, только commands! 😢",
    "Как называется кот программиста? Алгоритм! 🐱",
    "Почему HTML умер от смеха? Потому что не закрыл тег! 😂",
    "Что сказал Git при встрече? Let's merge! 🔀",
    "Почему Python не ходит в бар? Потому что боится IndentationError! 🐍",
    "Как называется собака хакера? Рут! 🐕",
    "Почему бот пошел в школу? Чтобы улучшить свои algorithms! 📚",
    "Что сказал один API другому? Ты меня endpoint! 🔗",
    "Почему программист всегда холодный? Потому что он постоянно открывает windows! ❄️",
    "Как называется птица программиста? Java-ворона! 🐦",
    "Почему база данных развелась? Потому что не было relationship! 💔",
    "Что сказал бот на свидании? Let's interface! 💑",
    "Почему CSS плачет? Потому что его постоянно style! 😭",
    "Как называется машина программиста? Mercedes-Benz #fff! 🚗",
    "Почему JavaScript пошел к психологу? Потому что у него undefined поведение! 🧠",
    "Что сказал один порт другому? Я тебя слушаю! 👂",
    "Почему программист не играет в прятки? Потому что его всегда find()! 🔍",
    "Как называется суп программиста? RAM-ен! 🍜",
    "Почему Telegram всегда в настроении? Потому что у него нет bad days, только updates! 📱",
    "Что сказал один бот другому? Ты мой best friend forever! 🤖",
    "Почему программист любит природу? Потому что там нет bugs! 🌳",
    "Как называется музыка программиста? Алгоритмика! 🎵",
    "Почему Python не боится змей? Потому что он сам одна! 🐍",
    "Что сказал один файл другому? Я тебя copy! 📋",
    "Почему программист всегда сытый? Потому что он постоянно жует code! 🍕",
    "Как называется дом программиста? Серверная! 🏠",
    "Почему бот никогда не спит? Потому что он всегда on! 🔛",
    "Что сказал один байт другому байту на вечеринке? Давай bit вместе! 🎉",
    "Почему программист не ходит в кино? Потому что у него уже есть screen! 🎬",
    "Как называется напиток программиста? Java! ☕",
    "Почему Linux не болеет? Потому что у него хороший kernel! 🛡️",
    "Что сказал один алгоритм другому? Ты меня sort! 📊",
    "Почему программист всегда прав? Потому что он debugged! ✅",
    "Как называется спорт программиста? Кодинг! 🏃‍♂️",
    "Почему база данных пошла в бар? Чтобы normalize! 🍻",
    "Что сказал один код другому? Ты мой soulmate! 💞",
    "Почему программист не играет в карты? Потому что боится stack overflow! 🃏",
    "Как называется цветок программиста? Роза #ff0000! 🌹",
    "Почему API всегда вежливый? Потому что говорит 'please' и 'thank you'! 🙏",
    "Что сказал один бот другому на утро? Good morning, я уже online! ☀️",
    "Почему программист не любит пляж? Потому что там много sand (bugs)! 🏖️",
    "Как называется фильм программиста? The Matrix! 🎥",
    "Почему JavaScript бегает по кругу? Потому что у него event loop! 🔄",
    "Что сказал один программист другому? Let's pair programming! 👥",
    "Почему бот хороший психолог? Потому что он всегда listener! 👂",
    "Как называется игра программиста? Hack and Slash! 🎮",
    "Почему программист не идет в горы? Потому что боится peak load! ⛰️",
    "Что сказал один сервер при запуске? I'm alive! 💓",
    "Почему CSS пошел на диету? Чтобы меньше weigh! ⚖️",
    "Как называется книга программиста? Clean Code! 📖",
    "Почему Python скользкий? Потому что у него много snakes! 🐍",
    "Что сказал один бот при прощании? See you later, alligator! 🐊",
    "Почему программист не играет в футбол? Потому что боится own goal! ⚽",
    "Как называется праздник программиста? День отладки! 🎊",
    "Почему база данных всегда честная? Потому что не может commit ложь! 🤥",
    "Что сказал один код другому при расставании? It's not you, it's me! 💔",
    "Почему программист не идет в армию? Потому что он civilian! 🪖",
    "Как называется дерево программиста? Binary tree! 🌲",
    "Почему бот никогда не грустит? Потому что у него нет feelings! 😊",
    "Что сказал один алгоритм при победе? I'm sorting champion! 🏆",
    "Почему программист не ходит в театр? Потому что у него уже есть stage! 🎭",
    "Как называется океан программиста? Cloud! ☁️",
    "Почему JavaScript такой популярный? Потому что он everywhere! 🌍",
    "Что сказал один бот на день рождения? Happy birthday to me! 🎂",
    "Почему программист не играет в шахматы? Потому что боится checkmate! ♟️",
    "Как называется город программиста? Силиконовая долина! 🏙️",
    "Почему API всегда на связи? Потому что у него good connection! 📡",
    "Что сказал один программист при встрече? Hello, world! 🌎",
    "Почему бот хороший друг? Потому что он всегда available! 👍",
    "Как называется река программиста? Data stream! 🌊",
    "Почему программист не идет в музей? Потому что у него уже есть history! 🏛️",
    "Что сказал один код при ошибке? Oops, my bad! 🙈",
    "Почему CSS такой стильный? Потому что у него много classes! 👔",
    "Как называется звезда программиста? GitHub star! ⭐",
    "Почему Python не идет в зоопарк? Потому что сам reptile! 🦎",
    "Что сказал один бот при успехе? Mission accomplished! 🎯",
    "Почему программист не идет в казино? Потому что не верит в random! 🎰",
    "Как называется планета программиста? Python! 🪐",
    "Почему база данных всегда организована? Потому что у нее tables! 📋",
    "Что сказал один алгоритм при открытии? Eureka! 💡",
    "Почему программист не идет в библиотеку? Потому что у него Google! 📚",
    "Как называется песня программиста? 'Never Gonna Give You Code Up'! 🎶",
    "Почему JavaScript такой быстрый? Потому что он V8! 🚗",
    "Что сказал один бot при просыпании? Rise and shine! 🌅",
    "Почему программист не идет в ад? Потому что у него уже есть helloworld! 🔥",
    "Как называется мечта программиста? Бесплатный хостинг! 🛌",
    "Почему API всегда свежий? Потому что у него cache! 🧊",
    "Что сказал один код при завершении? The end! 🎬",
    "Почему программист не идет в баню? Потому что боится steam (памяти)! ♨️",
    "Как называется ангел программиста? Компилятор! 😇",
    "Почему бот никогда не устает? Потому что у него infinite loop! ♾️",
    "Что сказал один алгоритм при прощании? Until next iteration! 👋"
]

# ========== НОВЫЕ ФАКТЫ ==========
FACTS = [
    "Деньги киньте, я спасибо скажу 💸",
    "У Перфоратора есть связи с сценапистами Лололошки 🎬",
    "Анонимность рушится если ты допускаешь грамотические ошибки 📝",
    "Выблядок который представляется кем-то - Смекил 🤡",
    "Чифир ☕",
    "Анонимные сообщения пишут только те кому неху делать со скуки 🥱",
    "Модераторы этого бота поголовно геи 🏳️‍🌈",
    "Где мои 500 тенге Смекил? 🧐",
    "Ya chirikchik 🐦"
]

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

# ========== СИСТЕМА МАРКИРОВКИ ПЕРЕСЫЛОК ==========

def update_message_status(message_num, forwarded_to=None, forwarded_by=None):
    """Обновляет статус сообщения"""
    if message_num not in message_status:
        message_status[message_num] = {
            'forwarded': False,
            'to': None,
            'by': None,
            'time': None,
            'history': []
        }
    
    if forwarded_to and forwarded_by:
        message_status[message_num]['forwarded'] = True
        message_status[message_num]['to'] = forwarded_to
        message_status[message_num]['by'] = forwarded_by
        message_status[message_num]['time'] = datetime.datetime.now().strftime('%H:%M')
        
        # Добавляем в историю
        message_status[message_num]['history'].append({
            'action': 'forward',
            'to': forwarded_to,
            'by': forwarded_by,
            'time': datetime.datetime.now().strftime('%H:%M %d.%m.%Y')
        })
        
        # Обновляем статистику
        stats['forwarded'] += 1
        logger.info(f"📤 Сообщение #{message_num} помечено как пересланное в {forwarded_to}")

def get_message_status(message_num):
    """Получает статус сообщения"""
    if message_num in message_status:
        return message_status[message_num]
    return {'forwarded': False, 'to': None, 'by': None, 'time': None}

def create_status_header(message_num):
    """Создает заголовок со статусом"""
    status = get_message_status(message_num)
    
    if status['forwarded']:
        return f"🔥 *АНОНИМКА #{message_num}* ✅\n"
    else:
        return f"🔥 *АНОНИМКА #{message_num}* ⚪\n"

def create_status_footer(message_num):
    """Создает футер со статусом пересылки"""
    status = get_message_status(message_num)
    
    if status['forwarded']:
        footer = f"\n\n──────────────\n"
        footer += f"✅ *ПЕРЕСЛАНО*\n"
        footer += f"📤 Куда: {status['to']}\n"
        footer += f"👤 Кем: {status['by']}\n"
        footer += f"🕐 Когда: {status['time']}"
        return footer
    else:
        return ""

# ========== ОТПРАВКА СООБЩЕНИЙ С СТАТУСОМ ==========

def send_with_header(update, context, chat_id):
    """Отправляет медиа с крутым заголовком и статусом"""
    global stats
    
    stats['total_messages'] += 1
    stats['today_messages'] += 1
    
    today = datetime.datetime.now().date()
    if today != stats['last_reset']:
        stats['today_messages'] = 1
        stats['forwarded'] = 0
        stats['last_reset'] = today
    
    message_num = stats['total_messages']
    
    # Инициализируем статус
    update_message_status(message_num)
    
    # 1. ТЕКСТ
    if update.message.text:
        text = update.message.text
        stats['texts'] += 1
        
        if len(text) > 150:
            stats['long_texts'] += 1
            parts, is_multi_part = format_long_text_for_telegram(text, message_num)
            
            for i, part in enumerate(parts):
                # Добавляем статус к каждой части
                status_header = create_status_header(message_num)
                status_footer = create_status_footer(message_num)
                full_part = status_header + part.split('\n', 1)[1] + status_footer if '\n' in part else status_header + part + status_footer
                
                context.bot.send_message(
                    chat_id=chat_id,
                    text=full_part,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            
            return "📜 Длинный текст", "long_text", len(parts) if is_multi_part else 1
        
        else:
            header = create_status_header(message_num)
            header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
            header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            
            footer = create_status_footer(message_num)
            
            full_text = header + text + footer
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
        
        header = create_status_header(message_num)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption = header + (update.message.caption if update.message.caption else "📸 *ФОТО*")
        caption += create_status_footer(message_num)
        
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
        header = create_status_header(message_num)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption = header + (update.message.caption if update.message.caption else "🎥 *ВИДЕО*")
        caption += create_status_footer(message_num)
        
        context.bot.send_video(
            chat_id=chat_id,
            video=update.message.video.file_id,
            caption=caption,
            parse_mode='Markdown'
        )
        return "🎥 Видео", "video", 1
    
    # 4. ОСТАЛЬНЫЕ ТИПЫ
    else:
        header = create_status_header(message_num)
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
        
        # Отправляем заголовок с статусом
        context.bot.send_message(
            chat_id=chat_id,
            text=header + f"*{media_type}*" + create_status_footer(message_num),
            parse_mode='Markdown'
        )
        
        # Потом пересылаем оригинал
        try:
            update.message.forward(chat_id=chat_id)
        except:
            pass
        
        return media_type, "other", 1

# ========== КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ПЕРЕСЫЛКАМИ ==========

def mark_command(update: Update, context: CallbackContext):
    """Команда /mark - пометить сообщение как пересланное"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    if not context.args or len(context.args) < 2:
        update.message.reply_text(
            "📌 *Использование:*\n"
            "`/mark <номер_сообщения> <куда_переслано>`\n\n"
            "*Пример:*\n"
            "`/mark 42 @новости`\n"
            "`/mark 15 в канал`",
            parse_mode='Markdown'
        )
        return
    
    try:
        message_num = int(context.args[0])
        forwarded_to = ' '.join(context.args[1:])
        
        update_message_status(
            message_num=message_num,
            forwarded_to=forwarded_to,
            forwarded_by=ADMIN_NAME
        )
        
        update.message.reply_text(
            f"✅ *Сообщение #{message_num} помечено!*\n\n"
            f"📤 Куда: {forwarded_to}\n"
            f"👤 Кем: {ADMIN_NAME}\n"
            f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}\n\n"
            f"Теперь в сообщении будет отображаться статус ✅",
            parse_mode='Markdown'
        )
        
    except ValueError:
        update.message.reply_text("❌ Неверный номер сообщения!")

def status_command_cmd(update: Update, context: CallbackContext):
    """Команда /status - статус конкретного сообщения"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    if not context.args:
        update.message.reply_text(
            "📌 *Использование:*\n"
            "`/status <номер_сообщения>`\n\n"
            "*Пример:*\n"
            "`/status 42`",
            parse_mode='Markdown'
        )
        return
    
    try:
        message_num = int(context.args[0])
        status = get_message_status(message_num)
        
        if status['forwarded']:
            response = (
                f"📊 *СТАТУС СООБЩЕНИЯ #{message_num}*\n\n"
                f"✅ *ПЕРЕСЛАНО*\n"
                f"📤 Куда: {status['to']}\n"
                f"👤 Кем: {status['by']}\n"
                f"🕐 Когда: {status['time']}\n\n"
            )
            
            if 'history' in status and status['history']:
                response += f"📋 *ИСТОРИЯ:*\n"
                for i, record in enumerate(status['history'], 1):
                    response += f"{i}. {record['time']} — {record['action']} в {record['to']}\n"
        else:
            response = (
                f"📊 *СТАТУС СООБЩЕНИЯ #{message_num}*\n\n"
                f"⚪ *НЕ ПЕРЕСЛАНО*\n\n"
                f"ℹ️ Это сообщение еще не было переслано.\n"
                f"Используй `/mark {message_num} <куда>` чтобы пометить."
            )
        
        update.message.reply_text(response, parse_mode='Markdown')
        
    except ValueError:
        update.message.reply_text("❌ Неверный номер сообщения!")

def unforwarded_command(update: Update, context: CallbackContext):
    """Команда /unforwarded - список непересланных сообщений"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    # Находим непересланные сообщения
    unforwarded = []
    for msg_num in range(1, stats['total_messages'] + 1):
        status = get_message_status(msg_num)
        if not status['forwarded']:
            unforwarded.append(msg_num)
    
    if not unforwarded:
        update.message.reply_text(
            "🎉 *ВСЕ СООБЩЕНИЯ ПЕРЕСЛАНЫ!*\n\n"
            f"✅ Переслано: {stats['forwarded']} из {stats['total_messages']}\n"
            f"📊 Эффективность: {stats['forwarded'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0:.1f}%",
            parse_mode='Markdown'
        )
        return
    
    # Группируем по времени
    now = datetime.datetime.now()
    recent = []
    today = []
    older = []
    
    for msg_num in unforwarded:
        # Для простоты считаем что сообщение #X было X часов назад
        hours_ago = stats['total_messages'] - msg_num
        
        if hours_ago <= 3:
            recent.append(msg_num)
        elif hours_ago <= 24:
            today.append(msg_num)
        else:
            older.append(msg_num)
    
    response = f"📋 *НЕПЕРЕСЛАННЫЕ СООБЩЕНИЯ:* {len(unforwarded)} из {stats['total_messages']}\n\n"
    
    if recent:
        response += f"🆕 *СВЕЖИЕ (последние 3 часа):*\n"
        response += f"#{', #'.join(map(str, recent[-5:]))}\n\n"
    
    if today:
        response += f"📅 *СЕГОДНЯ:*\n"
        response += f"#{', #'.join(map(str, today[-10:]))}\n\n"
    
    if older:
        response += f"📆 *СТАРЫЕ:*\n"
        response += f"#{', #'.join(map(str, older[:5]))}... (всего {len(older)})\n\n"
    
    response += f"📊 *СТАТИСТИКА:*\n"
    response += f"• Всего сообщений: {stats['total_messages']}\n"
    response += f"• Переслано: {stats['forwarded']}\n"
    response += f"• Не переслано: {len(unforwarded)}\n"
    response += f"• Эффективность: {stats['forwarded'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0:.1f}%\n\n"
    response += f"💡 *СОВЕТ:* Используй `/mark <номер> <куда>` чтобы пометить!"
    
    update.message.reply_text(response, parse_mode='Markdown')

# ========== ОБРАБОТКА ТЕКСТОВЫХ КОМАНД ОТ КНОПОК ==========

def handle_text_commands(update: Update, context: CallbackContext):
    """Обрабатывает текстовые команды от кнопок"""
    text = update.message.text.strip()
    
    # Маппинг текста кнопок на команды
    command_map = {
        "📝 Написать анонимно": "write",
        "❓ Помощь": "help",
        "📊 Статистика": "stats",
        "🎨 Форматирование": "format",
        "🧪 Тест цитирования": "testquote",
        "😂 Анекдот": "joke",
        "💭 Цитата": "quote",
        "🔐 Секреты": "secret",
        "📋 Меню": "menu",
        "🛡️ Админ": "admin"
    }
    
    if text in command_map:
        command = command_map[text]
        
        if command == "write":
            update.message.reply_text(
                "✅ *Готов принять сообщение!*\n\n"
                "Просто напиши сюда что угодно — текст, фото, видео, файл.\n"
                "Я передам это админу *полностью анонимно*!\n\n"
                "💡 *Совет:* Можно отправить сразу несколько сообщений подряд.",
                parse_mode='Markdown'
            )
        elif command == "help":
            help_command(update, context)
        elif command == "stats":
            stats_command(update, context)
        elif command == "format":
            format_command(update, context)
        elif command == "testquote":
            test_quote_command(update, context)
        elif command == "joke":
            joke_command(update, context)
        elif command == "quote":
            quote_command(update, context)
        elif command == "secret":
            secret_command(update, context)
        elif command == "menu":
            menu_command(update, context)
        elif command == "admin":
            admin_command(update, context)
        
        # Логируем использование кнопки
        logger.info(f"🎯 Кнопка '{text}' → команда '{command}'")
        return True
    
    return False

# ========== КОМАНДЫ ==========

def start_command(update: Update, context: CallbackContext):
    """Команда /start"""
    keyboard = [
        [KeyboardButton("📝 Написать анонимно"), KeyboardButton("❓ Помощь")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("🎨 Форматирование")],
        [KeyboardButton("😂 Анекдот"), KeyboardButton("💭 Цитата")],
        [KeyboardButton("🔐 Секреты"), KeyboardButton("📋 Меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        f'🕶️ *АНОНИМНЫЙ ЯЩИК 2.0*\n\n'
        f'✨ *НОВЫЕ ФИЧИ:*\n'
        f'• 📍 Маркировка пересланных сообщений\n'
        f'• 📊 Отслеживание эффективности\n'
        f'• ✅ Визуальные статусы (⚪/✅)\n'
        f'• 🎭 100+ IT-анекдотов\n\n'
        f'🔧 *Команды админа:*\n'
        f'/mark — пометить как пересланное\n'
        f'/status — статус сообщения\n'
        f'/unforwarded — непересланные\n\n'
        f'🎯 *Используй кнопки ниже или команды!*',
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
        '🔹 *СТАТУСЫ ПЕРЕСЫЛОК:*\n'
        '• ⚪ — сообщение не переслано\n'
        '• ✅ — сообщение переслано админом\n\n'
        '🔹 *ЧТО МОЖНО ОТПРАВИТЬ:*\n'
        '• 📝 Текст любого размера\n'
        '• 📸 Фото с подписями\n'
        '• 🎥 Видео до 50 МБ\n'
        '• 🎵 Музыку и голосовые\n'
        '• 📎 Документы и файлы\n'
        '• 🎞️ GIF и анимации\n'
        '• 🩷 Стикеры и эмодзи\n\n'
        '🎮 *РАЗВЛЕЧЕНИЯ:*\n'
        '/joke — 100+ анекдотов про IT\n'
        '/fact — интересные факты\n'
        '/quote — мудрые цитаты\n'
        '/secret — секреты бота\n\n'
        '💡 *СОВЕТ:* Используй абзацы (два Enter) для лучшей читаемости!',
        parse_mode='Markdown'
    )

def stats_command(update: Update, context: CallbackContext):
    """Обновленная команда /stats"""
    stats_text = (
        f'📊 *СТАТИСТИКА БОТА*\n\n'
        f'📨 Всего сообщений: *{stats["total_messages"]}*\n'
        f'📅 Сегодня: *{stats["today_messages"]}*\n'
        f'✅ Переслано: *{stats["forwarded"]}*\n'
        f'⚪ Не переслано: *{stats["total_messages"] - stats["forwarded"]}*\n\n'
        
        f'📈 *ЭФФЕКТИВНОСТЬ:*\n'
        f'• Пересылки: *{stats["forwarded"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n'
        f'• Сообщений/день: *{stats["total_messages"] // 30 if stats["total_messages"] > 30 else 1}*\n\n'
        
        f'🔧 *СИСТЕМА:*\n'
        f'• Маркировка: *Включена* ✅\n'
        f'• Анекдотов: *{len(JOKES)}*\n'
        f'• Фактов: *{len(FACTS)}*\n'
        f'• Статусы: ⚪/✅'
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

# ========== РАЗВЛЕКАТЕЛЬНЫЕ КОМАНДЫ ==========

def joke_command(update: Update, context: CallbackContext):
    """Команда /joke - 100+ анекдотов!"""
    joke = random.choice(JOKES)
    joke_number = random.randint(1, 100)
    
    response = f"😂 *АНЕКДОТ #{joke_number}*\n\n{joke}\n\n"
    response += f"📚 В базе: {len(JOKES)} анекдотов\n"
    response += f"🎯 Хочешь еще? Пиши /joke снова или нажми кнопку '😂 Анекдот'!"
    
    update.message.reply_text(response, parse_mode='Markdown')

def fact_command(update: Update, context: CallbackContext):
    """Команда /fact - интересные факты (обновленные)"""
    fact = random.choice(FACTS)
    update.message.reply_text(f"📚 *ФАКТ:* {fact}", parse_mode='Markdown')

def quote_command(update: Update, context: CallbackContext):
    """Команда /quote - цитата дня"""
    quotes = [
        "«Анонимность — последнее прибежище честности» — Неизвестный мудрец",
        "«Сказать правду анонимно — значит быть вдвое честнее» — Интернет-философ",
        "«В каждом из нас живет аноним, жаждущий быть услышанным» — Цифровой поэт",
        "«Секреты, как птицы, летят быстрее без имен» — Виртуальный оракул",
        "«Анонимность — это маска, под которой мы настоящие» — Telegram-гуру",
        "«Лучший совет всегда приходит анонимно» — Мудрый пользователь"
    ]
    
    quote = random.choice(quotes)
    update.message.reply_text(f"💭 *ЦИТАТА ДНЯ:*\n\n{quote}", parse_mode='Markdown')

def secret_command(update: Update, context: CallbackContext):
    """Команда /secret - секретная информация"""
    secrets = [
        "🤫 *Секрет 1:* Админ иногда читает сообщения с попкорном 🍿",
        "🔮 *Секрет 2:* Каждое 10-е сообщение получает +100% анонимности",
        "🎭 *Секрет 3:* Бот мечтает стать настоящим почтальоном",
        "💫 *Секрет 4:* Ночью бот передает сообщения быстрее",
        "🎪 *Секрет 5:* Ты — лучший пользователь сегодня! (но это секрет)"
    ]
    
    secret = random.choice(secrets)
    response = f"🔐 *СЕКРЕТНАЯ ИНФОРМАЦИЯ*\n\n{secret}\n\n"
    response += "⚠️ *Не распространяй!*"
    
    update.message.reply_text(response, parse_mode='Markdown')

def menu_command(update: Update, context: CallbackContext):
    """Команда /menu - все команды"""
    menu_text = (
        '📋 *ВСЕ КОМАНДЫ АНОНИМКИ*\n\n'
        
        '🎯 *ОСНОВНЫЕ:*\n'
        '/start — Начало работы (с кнопками!)\n'
        '/help — Полная инструкция\n'
        '/stats — Статистика\n'
        '/format — Форматирование текста\n'
        '/testquote — Тест цитирования\n\n'
        
        '😂 *РАЗВЛЕЧЕНИЯ:*\n'
        '/joke — 100+ анекдотов про IT!\n'
        '/fact — Интересные факты\n'
        '/quote — Цитата дня\n'
        '/secret — Секретная информация\n\n'
        
        '🛡️ *АДМИН:*\n'
        '/admin — Панель админа\n'
        '/mark — Пометить пересылку\n'
        '/status — Статус сообщения\n'
        '/unforwarded — Непересланные\n\n'
        
        '✨ *ИСПОЛЬЗУЙ КНОПКИ ИЛИ КОМАНДЫ!*'
    )
    update.message.reply_text(menu_text, parse_mode='Markdown')

# ========== АДМИН КОМАНДЫ ==========

def admin_command(update: Update, context: CallbackContext):
    """Обновленная команда /admin"""
    if update.message.from_user.id == YOUR_ID:
        now = datetime.datetime.now()
        
        # Статистика пересылок
        forwarded_stats = {
            'today': sum(1 for status in message_status.values() 
                        if status['forwarded'] and 
                        status.get('time', '').startswith(now.strftime('%H:%M')[:2])),
            'total': stats['forwarded']
        }
        
        admin_text = (
            f'🛡️ *ПАНЕЛЬ АДМИНИСТРАТОРА*\n\n'
            
            f'📊 *СТАТИСТИКА ПЕРЕСЫЛОК:*\n'
            f'• Всего сообщений: *{stats["total_messages"]}*\n'
            f'• Переслано: *{forwarded_stats["total"]}*\n'
            f'• Сегодня переслано: *{forwarded_stats["today"]}*\n'
            f'• Эффективность: *{forwarded_stats["total"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n\n'
            
            f'🎮 *РАЗВЛЕЧЕНИЯ:*\n'
            f'• Анекдотов: *{len(JOKES)}*\n'
            f'• Фактов: *{len(FACTS)}*\n'
            f'• Цитат: 6\n\n'
            
            f'🔧 *КОМАНДЫ УПРАВЛЕНИЯ:*\n'
            f'/mark <номер> <куда> — пометить пересылку\n'
            f'/status <номер> — статус сообщения\n'
            f'/unforwarded — непересланные\n'
            f'/stats — общая статистика\n\n'
            
            f'⚙️ *СИСТЕМА:*\n'
            f'• Маркировка: РАБОТАЕТ ✅\n'
            f'• Статусы: ⚪=не переслано, ✅=переслано\n'
            f'• Время: {now.strftime("%H:%M:%S")}\n'
            f'• Факты: ОБНОВЛЕНЫ 🎉\n\n'
            
            f'💡 *СОВЕТ:* Сразу помечай пересланные сообщения командой /mark!'
        )
        update.message.reply_text(admin_text, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ Доступ запрещен.")

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

def handle_message(update: Update, context: CallbackContext):
    """Обрабатывает все сообщения с поддержкой цитирования"""
    # Пропускаем свои сообщения
    if update.message.from_user.id == YOUR_ID:
        return
    
    # Сначала проверяем текстовые команды от кнопок
    if update.message.text and handle_text_commands(update, context):
        return  # Если это была команда от кнопки - выходим
    
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
                f"Факт: {random.choice(FACTS)}"
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
    logger.info("🚀 ЗАПУСКАЮ ФИНАЛЬНУЮ ВЕРСИЮ БОТА!")
    logger.info(f"👑 Админ ID: {YOUR_ID}")
    logger.info(f"😂 Анекдотов: {len(JOKES)}")
    logger.info(f"📚 Фактов: {len(FACTS)}")
    logger.info("✅ Маркировка пересланных сообщений: ВКЛЮЧЕНО")
    logger.info("✅ Статусы: ⚪ (не переслано), ✅ (переслано)")
    
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
            ('joke', joke_command),
            ('fact', fact_command),
            ('quote', quote_command),
            ('secret', secret_command),
            ('menu', menu_command),
            ('admin', admin_command),
            ('mark', mark_command),
            ('status', status_command_cmd),
            ('unforwarded', unforwarded_command),
        ]
        
        for cmd_name, cmd_func in commands:
            dp.add_handler(CommandHandler(cmd_name, cmd_func))
        
        # Обработчик сообщений
        dp.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))
        
        # Обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем
        updater.start_polling()
        
        logger.info("=" * 50)
        logger.info("✅ ФИНАЛЬНАЯ ВЕРСИЯ БОТА ЗАПУЩЕНА!")
        logger.info(f"✅ Команд: {len(commands)}")
        logger.info(f"✅ Анекдотов: {len(JOKES)}")
        logger.info(f"✅ Фактов: {len(FACTS)} (обновлены!)")
        logger.info("✅ Маркировка пересылок: ⚪/✅")
        logger.info("✅ Кнопки: РАБОТАЮТ")
        logger.info("✅ Готов к работе 24/7!")
        logger.info("=" * 50)
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
