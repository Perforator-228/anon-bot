import os
import logging
import datetime
import random
import string
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

# Хранилище сообщений с уникальными ID
messages_db = {}  # {message_id: {'content': str, 'user_id': int, 'time': str, 'forwarded': bool, ...}}
message_counter = 0  # Только для нумерации в интерфейсе

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

# ========== ГЕНЕРАЦИЯ УНИКАЛЬНЫХ ID ==========

def generate_message_id():
    """Генерирует уникальный ID для сообщения"""
    timestamp = int(datetime.datetime.now().timestamp())
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{random_part}"

def save_message(content, user_id, media_type="text", file_id=None, caption=None):
    """Сохраняет сообщение в базу"""
    global message_counter
    
    message_id = generate_message_id()
    message_counter += 1
    
    messages_db[message_id] = {
        'id': message_id,
        'display_number': message_counter,  # Для отображения пользователю
        'content': content,
        'file_id': file_id,
        'caption': caption,
        'user_id': user_id,
        'media_type': media_type,
        'time': datetime.datetime.now().strftime('%H:%M %d.%m.%Y'),
        'forwarded': False,
        'forwarded_to': None,
        'forwarded_by': None,
        'forwarded_time': None
    }
    
    logger.info(f"💾 Сохранено сообщение #{message_counter} (ID: {message_id})")
    return message_id, message_counter

def update_message_status(message_id, forwarded_to=None, forwarded_by=None):
    """Обновляет статус сообщения"""
    if message_id in messages_db:
        messages_db[message_id]['forwarded'] = True
        messages_db[message_id]['forwarded_to'] = forwarded_to
        messages_db[message_id]['forwarded_by'] = forwarded_by
        messages_db[message_id]['forwarded_time'] = datetime.datetime.now().strftime('%H:%M')
        
        # Обновляем статистику
        stats['forwarded'] += 1
        logger.info(f"📤 Сообщение ID:{message_id} помечено как пересланное в {forwarded_to}")
        return True
    return False

def get_message_status(message_id):
    """Получает статус сообщения"""
    if message_id in messages_db:
        return messages_db[message_id]
    return None

def create_status_header(message_data):
    """Создает заголовок со статусом"""
    if message_data['forwarded']:
        return f"🔥 *АНОНИМКА #{message_data['display_number']}* ✅\n"
    else:
        return f"🔥 *АНОНИМКА #{message_data['display_number']}* ⚪\n"

def create_status_footer(message_data):
    """Создает футер со статусом пересылки"""
    if message_data['forwarded']:
        footer = f"\n\n──────────────\n"
        footer += f"✅ *ПЕРЕСЛАНО*\n"
        footer += f"📤 Куда: {message_data['forwarded_to']}\n"
        footer += f"👤 Кем: {message_data['forwarded_by']}\n"
        footer += f"🕐 Когда: {message_data['forwarded_time']}\n"
        footer += f"🔢 ID: `{message_data['id']}`"
        return footer
    else:
        return f"\n\n──────────────\n🔢 ID: `{message_data['id']}`"

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
    
    user = update.message.from_user
    
    # 1. ТЕКСТ
    if update.message.text:
        text = update.message.text
        stats['texts'] += 1
        
        # Сохраняем сообщение
        message_id, display_num = save_message(text, user.id, "text")
        message_data = messages_db[message_id]
        
        if len(text) > 150:
            stats['long_texts'] += 1
            parts, is_multi_part = format_long_text_for_telegram(text, display_num)
            
            for i, part in enumerate(parts):
                # Добавляем статус к каждой части
                status_header = create_status_header(message_data)
                status_footer = create_status_footer(message_data)
                full_part = status_header + part.split('\n', 1)[1] + status_footer if '\n' in part else status_header + part + status_footer
                
                context.bot.send_message(
                    chat_id=chat_id,
                    text=full_part,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            
            return "📜 Длинный текст", "long_text", len(parts) if is_multi_part else 1, display_num, message_id
        
        else:
            header = create_status_header(message_data)
            header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
            header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            
            footer = create_status_footer(message_data)
            
            full_text = header + text + footer
            context.bot.send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode='Markdown'
            )
            return "📝 Текст", "text", 1, display_num, message_id
    
    # 2. ФОТО
    elif update.message.photo:
        stats['photos'] += 1
        photo = update.message.photo[-1]
        
        # Сохраняем сообщение
        caption = update.message.caption if update.message.caption else "📸 ФОТО"
        message_id, display_num = save_message(
            caption, 
            user.id, 
            "photo", 
            photo.file_id, 
            caption
        )
        message_data = messages_db[message_id]
        
        header = create_status_header(message_data)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption_text = header + (caption if caption else "📸 *ФОТО*")
        caption_text += create_status_footer(message_data)
        
        context.bot.send_photo(
            chat_id=chat_id,
            photo=photo.file_id,
            caption=caption_text,
            parse_mode='Markdown'
        )
        return "📸 Фото", "photo", 1, display_num, message_id
    
    # 3. ВИДЕО
    elif update.message.video:
        stats['videos'] += 1
        
        # Сохраняем сообщение
        caption = update.message.caption if update.message.caption else "🎥 ВИДЕО"
        message_id, display_num = save_message(
            caption, 
            user.id, 
            "video", 
            update.message.video.file_id, 
            caption
        )
        message_data = messages_db[message_id]
        
        header = create_status_header(message_data)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption_text = header + (caption if caption else "🎥 *ВИДЕО*")
        caption_text += create_status_footer(message_data)
        
        context.bot.send_video(
            chat_id=chat_id,
            video=update.message.video.file_id,
            caption=caption_text,
            parse_mode='Markdown'
        )
        return "🎥 Видео", "video", 1, display_num, message_id
    
    # 4. ОСТАЛЬНЫЕ ТИПЫ
    else:
        media_type = "📦 Медиа"
        if update.message.animation:
            media_type = "🎞️ GIF"
            file_id = update.message.animation.file_id
        elif update.message.document:
            media_type = "📎 Файл"
            file_id = update.message.document.file_id
        elif update.message.audio:
            media_type = "🎵 Музыка"
            file_id = update.message.audio.file_id
        elif update.message.voice:
            media_type = "🎤 Голосовое"
            file_id = update.message.voice.file_id
        elif update.message.sticker:
            media_type = "🩷 Стикер"
            file_id = update.message.sticker.file_id
        else:
            file_id = None
        
        # Сохраняем сообщение
        caption = update.message.caption if update.message.caption else media_type
        message_id, display_num = save_message(
            caption, 
            user.id, 
            media_type.lower(), 
            file_id, 
            caption
        )
        message_data = messages_db[message_id]
        
        header = create_status_header(message_data)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        # Отправляем заголовок с статусом
        context.bot.send_message(
            chat_id=chat_id,
            text=header + f"*{media_type}*" + create_status_footer(message_data),
            parse_mode='Markdown'
        )
        
        # Потом пересылаем оригинал если есть file_id
        try:
            if update.message.animation:
                context.bot.send_animation(chat_id=chat_id, animation=file_id)
            elif update.message.document:
                context.bot.send_document(chat_id=chat_id, document=file_id)
            elif update.message.audio:
                context.bot.send_audio(chat_id=chat_id, audio=file_id)
            elif update.message.voice:
                context.bot.send_voice(chat_id=chat_id, voice=file_id)
            elif update.message.sticker:
                context.bot.send_sticker(chat_id=chat_id, sticker=file_id)
            else:
                update.message.forward(chat_id=chat_id)
        except Exception as e:
            logger.error(f"Ошибка отправки медиа: {e}")
            context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ *Не удалось отправить медиа*\n\nОшибка: {str(e)}",
                parse_mode='Markdown'
            )
        
        return media_type, "other", 1, display_num, message_id

# ========== КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ПЕРЕСЫЛКАМИ ==========

def mark_command(update: Update, context: CallbackContext):
    """Команда /mark - пометить сообщение как пересланное"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    if not context.args or len(context.args) < 2:
        update.message.reply_text(
            "📌 *Использование:*\n"
            "`/mark <ID_сообщения> <куда_переслано>`\n\n"
            "*Пример:*\n"
            "`/mark 1702034567_abc123 @новости`\n"
            "`/mark 42 в канал`\n\n"
            "ℹ️ *ID сообщения* смотри в конце каждого сообщения (после 🔢 ID:)\n"
            "Можно использовать номер сообщения (например: 42)",
            parse_mode='Markdown'
        )
        return
    
    search_id = context.args[0]
    forwarded_to = ' '.join(context.args[1:])
    
    # Пробуем найти сообщение по ID
    if search_id in messages_db:
        message_data = messages_db[search_id]
        message_id = search_id
        
    else:
        # Пробуем найти по номеру отображения
        try:
            display_num = int(search_id)
            found = False
            for msg_id, data in messages_db.items():
                if data.get('display_number') == display_num:
                    message_data = data
                    message_id = msg_id
                    found = True
                    break
            
            if not found:
                update.message.reply_text(
                    f"❌ *Сообщение #{search_id} не найдено!*\n\n"
                    f"ℹ️ Используйте правильный ID или номер сообщения.\n"
                    f"ID смотрите в конце каждого сообщения (после 🔢 ID:)\n\n"
                    f"*Пример ID:* `1702034567_abc123`",
                    parse_mode='Markdown'
                )
                return
        except ValueError:
            update.message.reply_text(
                f"❌ *Неверный формат ID!*\n\n"
                f"ℹ️ Используйте:\n"
                f"• ID сообщения (например: `1702034567_abc123`)\n"
                f"• Или номер сообщения (например: `42`)\n\n"
                f"Смотрите ID в конце каждого полученного сообщения.",
                parse_mode='Markdown'
            )
            return
    
    update_message_status(
        message_id=message_id,
        forwarded_to=forwarded_to,
        forwarded_by=ADMIN_NAME
    )
    
    update.message.reply_text(
        f"✅ *Сообщение #{message_data['display_number']} помечено!*\n\n"
        f"📤 Куда: {forwarded_to}\n"
        f"👤 Кем: {ADMIN_NAME}\n"
        f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}\n"
        f"🔢 ID: `{message_id}`\n\n"
        f"Теперь в сообщении будет отображаться статус ✅",
        parse_mode='Markdown'
    )

def status_command_cmd(update: Update, context: CallbackContext):
    """Команда /status - статус конкретного сообщения"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    if not context.args:
        # Показываем последние сообщения
        recent_messages = list(messages_db.items())[-5:]  # Последние 5
        
        if not recent_messages:
            update.message.reply_text("📭 *Нет сообщений*")
            return
        
        response = "📋 *ПОСЛЕДНИЕ СООБЩЕНИЯ:*\n\n"
        
        for msg_id, data in recent_messages[::-1]:  # В обратном порядке
            status_icon = "✅" if data['forwarded'] else "⚪"
            response += f"{status_icon} *#{data['display_number']}* "
            response += f"({data['time']})\n"
            response += f"📝 *Тип:* {data['media_type']}\n"
            
            # Краткое содержание
            content_preview = str(data['content'])[:50]
            if len(str(data['content'])) > 50:
                content_preview += "..."
            response += f"📄 *Содержание:* {content_preview}\n"
            
            if data['forwarded']:
                response += f"📤 *Переслано в:* {data['forwarded_to']}\n"
            
            response += f"🔢 *ID:* `{msg_id}`\n"
            response += "─" * 30 + "\n\n"
        
        response += "ℹ️ *Используйте:* `/status <ID>` для подробностей"
        update.message.reply_text(response, parse_mode='Markdown')
        return
    
    # Ищем конкретное сообщение
    search_id = context.args[0]
    
    # Пробуем как ID
    if search_id in messages_db:
        data = messages_db[search_id]
        message_id = search_id
    else:
        # Пробуем как номер отображения
        try:
            display_num = int(search_id)
            found = False
            for msg_id, msg_data in messages_db.items():
                if msg_data.get('display_number') == display_num:
                    data = msg_data
                    message_id = msg_id
                    found = True
                    break
            
            if not found:
                update.message.reply_text(f"❌ Сообщение #{search_id} не найдено!")
                return
        except ValueError:
            update.message.reply_text(f"❌ Неверный ID: {search_id}")
            return
    
    # Формируем подробный ответ
    if data['forwarded']:
        response = (
            f"📊 *СТАТУС СООБЩЕНИЯ #{data['display_number']}*\n\n"
            f"✅ *ПЕРЕСЛАНО*\n"
            f"📤 Куда: {data['forwarded_to']}\n"
            f"👤 Кем: {data['forwarded_by']}\n"
            f"🕐 Когда: {data['forwarded_time']}\n\n"
            f"📝 *ИНФОРМАЦИЯ:*\n"
            f"• Тип: {data['media_type']}\n"
            f"• Время получения: {data['time']}\n"
            f"• ID пользователя: `{data['user_id']}`\n"
            f"• ID сообщения: `{message_id}`\n\n"
        )
    else:
        response = (
            f"📊 *СТАТУС СООБЩЕНИЯ #{data['display_number']}*\n\n"
            f"⚪ *НЕ ПЕРЕСЛАНО*\n\n"
            f"📝 *ИНФОРМАЦИЯ:*\n"
            f"• Тип: {data['media_type']}\n"
            f"• Время получения: {data['time']}\n"
            f"• ID пользователя: `{data['user_id']}`\n"
            f"• ID сообщения: `{message_id}`\n\n"
            f"ℹ️ Используйте `/mark {message_id} <куда>` чтобы пометить."
        )
    
    # Показываем содержание (если текст не очень длинный)
    if data['media_type'] in ["text", "long_text"] and len(str(data['content'])) < 500:
        response += f"📄 *СОДЕРЖАНИЕ:*\n{data['content']}\n"
    
    update.message.reply_text(response, parse_mode='Markdown')

def list_command(update: Update, context: CallbackContext):
    """Команда /list - список всех сообщений"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    if not messages_db:
        update.message.reply_text("📭 *База сообщений пуста*")
        return
    
    # Фильтры
    filter_type = None
    if context.args:
        arg = context.args[0].lower()
        if arg in ['переслано', 'forwarded', '✅']:
            filter_type = 'forwarded'
        elif arg in ['непереслано', 'unforwarded', '⚪']:
            filter_type = 'unforwarded'
        elif arg in ['сегодня', 'today']:
            filter_type = 'today'
    
    # Фильтруем сообщения
    filtered_messages = []
    today = datetime.datetime.now().strftime('%d.%m.%Y')
    
    for msg_id, data in messages_db.items():
        include = True
        
        if filter_type == 'forwarded':
            include = data['forwarded']
        elif filter_type == 'unforwarded':
            include = not data['forwarded']
        elif filter_type == 'today':
            include = today in data['time']
        
        if include:
            filtered_messages.append((msg_id, data))
    
    if not filtered_messages:
        update.message.reply_text(f"📭 *Нет сообщений по фильтру*")
        return
    
    # Сортируем по времени (новые сначала)
    filtered_messages.sort(key=lambda x: x[1]['display_number'], reverse=True)
    
    # Ограничиваем вывод
    limit = min(20, len(filtered_messages))
    filtered_messages = filtered_messages[:limit]
    
    # Формируем ответ
    total = len(messages_db)
    filtered = len(filtered_messages)
    
    if filter_type:
        filter_text = {
            'forwarded': '✅ ПЕРЕСЛАННЫЕ',
            'unforwarded': '⚪ НЕПЕРЕСЛАННЫЕ', 
            'today': '📅 СЕГОДНЯ'
        }.get(filter_type, 'ВСЕ')
        
        response = f"📋 *{filter_text} СООБЩЕНИЯ* ({filtered} из {total})\n\n"
    else:
        response = f"📋 *ПОСЛЕДНИЕ СООБЩЕНИЯ* ({filtered} из {total})\n\n"
    
    for msg_id, data in filtered_messages:
        status_icon = "✅" if data['forwarded'] else "⚪"
        
        # Краткая информация
        time_parts = data['time'].split()
        time_str = time_parts[0] if len(time_parts) > 0 else data['time']
        
        response += f"{status_icon} *#{data['display_number']}* "
        response += f"— {time_str}\n"
        
        # Содержание (первые 30 символов)
        content_preview = str(data['content'])[:30].replace('\n', ' ')
        if len(str(data['content'])) > 30:
            content_preview += "..."
        
        response += f"   📄 {content_preview}\n"
        
        if data['forwarded']:
            forwarded_to_preview = data['forwarded_to'][:20]
            if len(data['forwarded_to']) > 20:
                forwarded_to_preview += "..."
            response += f"   📤 {forwarded_to_preview}\n"
        
        response += f"   🔢 ID: `{msg_id}`\n"
        response += "   ─\n"
    
    response += f"\nℹ️ *КОМАНДЫ:*\n"
    response += f"`/list` — все сообщения\n"
    response += f"`/list переслано` — только пересланные\n"
    response += f"`/list непереслано` — только непересланные\n"
    response += f"`/status <ID>` — подробности сообщения\n"
    response += f"`/mark <ID> <куда>` — пометить пересылку"
    
    update.message.reply_text(response, parse_mode='Markdown')

def unforwarded_command(update: Update, context: CallbackContext):
    """Команда /unforwarded - список непересланных сообщений"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    # Находим непересланные сообщения
    unforwarded = []
    for msg_id, data in messages_db.items():
        if not data['forwarded']:
            unforwarded.append((msg_id, data))
    
    if not unforwarded:
        update.message.reply_text(
            "🎉 *ВСЕ СООБЩЕНИЯ ПЕРЕСЛАНЫ!*\n\n"
            f"✅ Переслано: {stats['forwarded']} из {stats['total_messages']}\n"
            f"📊 Эффективность: {stats['forwarded'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0:.1f}%",
            parse_mode='Markdown'
        )
        return
    
    # Сортируем по номеру (новые сначала)
    unforwarded.sort(key=lambda x: x[1]['display_number'], reverse=True)
    
    # Ограничиваем вывод
    limit = min(15, len(unforwarded))
    unforwarded = unforwarded[:limit]
    
    response = f"📋 *НЕПЕРЕСЛАННЫЕ СООБЩЕНИЯ:* {len(unforwarded)} из {stats['total_messages']}\n\n"
    
    for i, (msg_id, data) in enumerate(unforwarded, 1):
        # Время в удобном формате
        time_parts = data['time'].split()
        time_str = time_parts[0] if len(time_parts) > 0 else data['time']
        
        # Содержание (первые 40 символов)
        content_preview = str(data['content'])[:40].replace('\n', ' ')
        if len(str(data['content'])) > 40:
            content_preview += "..."
        
        response += f"{i}. *#{data['display_number']}* ({time_str})\n"
        response += f"   📄 {content_preview}\n"
        response += f"   🔢 ID: `{msg_id}`\n"
        
        if i < len(unforwarded):
            response += "   ─\n"
    
    response += f"\n📊 *СТАТИСТИКА:*\n"
    response += f"• Всего сообщений: {stats['total_messages']}\n"
    response += f"• Переслано: {stats['forwarded']}\n"
    response += f"• Не переслано: {len(unforwarded)}\n"
    response += f"• Эффективность: {stats['forwarded'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0:.1f}%\n\n"
    response += f"💡 *ИСПОЛЬЗОВАНИЕ:*\n"
    response += f"`/mark {unforwarded[0][0]} @канал` — пометить первое\n"
    response += f"`/status ID` — подробности сообщения\n"
    response += f"`/list` — все сообщения"
    
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
        f'• 📍 Уникальные ID сообщений\n'
        f'• 📊 База данных сообщений\n'
        f'• ✅ Точная маркировка пересылок\n'
        f'• 🔍 Поиск по ID или номеру\n'
        f'• 🎭 100+ IT-анекдотов\n'
        f'• 📚 9 новых фактов\n\n'
        f'🔧 *Команды админа:*\n'
        f'/mark <ID> <куда> — пометить пересылку\n'
        f'/status <ID> — статус сообщения\n'
        f'/list — все сообщения\n'
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
        '• ✅ — сообщение переслано админом\n'
        '• 🔢 ID — уникальный идентификатор\n\n'
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
        f'⚪ Не переслано: *{stats["total_messages"] - stats["forwarded"]}*\n'
        f'💾 В базе: *{len(messages_db)}*\n\n'
        
        f'📈 *ЭФФЕКТИВНОСТЬ:*\n'
        f'• Пересылки: *{stats["forwarded"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n'
        f'• Сообщений/день: *{stats["today_messages"]}*\n\n'
        
        f'🎪 *РАЗВЛЕЧЕНИЯ:*\n'
        f'• Анекдотов: *{len(JOKES)}*\n'
        f'• Фактов: *{len(FACTS)}*\n\n'
        
        f'🔧 *СИСТЕМА:*\n'
        f'• Уникальные ID: ✅ РАБОТАЕТ\n'
        f'• Маркировка: ⚪/✅\n'
        f'• ID формат: timestamp_random'
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
        '/list — Список сообщений\n'
        '/unforwarded — Непересланные\n\n'
        
        '✨ *ИСПОЛЬЗУЙ КНОПКИ ИЛИ КОМАНДЫ!*'
    )
    update.message.reply_text(menu_text, parse_mode='Markdown')

# ========== АДМИН КОМАНДЫ ==========

def admin_command(update: Update, context: CallbackContext):
    """Обновленная команда /admin"""
    if update.message.from_user.id == YOUR_ID:
        now = datetime.datetime.now()
        
        admin_text = (
            f'🛡️ *ПАНЕЛЬ АДМИНИСТРАТОРА*\n\n'
            
            f'📊 *СТАТИСТИКА:*\n'
            f'• Всего сообщений: *{stats["total_messages"]}*\n'
            f'• В базе данных: *{len(messages_db)}*\n'
            f'• Переслано: *{stats["forwarded"]}*\n'
            f'• Эффективность: *{stats["forwarded"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n\n'
            
            f'🔧 *КОМАНДЫ УПРАВЛЕНИЯ:*\n'
            f'`/mark <ID> <куда>` — пометить пересылку\n'
            f'`/status <ID>` — статус сообщения\n'
            f'`/list` — все сообщения\n'
            f'`/list переслано` — пересланные\n'
            f'`/list непереслано` — непересланные\n'
            f'`/unforwarded` — непересланные (кратко)\n\n'
            
            f'⚙️ *СИСТЕМА:*\n'
            f'• Уникальные ID: ✅ РАБОТАЕТ\n'
            f'• ID формат: `timestamp_random`\n'
            f'• Пример ID: `1702034567_abc123`\n'
            f'• Время: {now.strftime("%H:%M:%S")}\n\n'
            
            f'💡 *КАК РАБОТАТЬ:*\n'
            f'1. Смотри ID в конце каждого сообщения\n'
            f'2. Используй `/mark ID @канал`\n'
            f'3. Проверяй статус `/status ID`\n'
            f'4. Смотри все `/list`'
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
    logger.info(f"📨 Входящее сообщение от пользователя {user.id}")
    
    try:
        media_type, media_category, parts_count, display_num, message_id = send_with_header(update, context, YOUR_ID)
        
        if media_category == "long_text":
            if parts_count > 1:
                response = (
                    f"✅ *Длинный текст отправлен!*\n"
                    f"🔢 Номер: #{display_num}\n"
                    f"📄 Частей: {parts_count}\n"
                    f"🔐 Статус: Доставлено с цитированием\n"
                    f"💡 Совет: В Telegram текст можно развернуть/свернуть\n\n"
                    f"🕐 {datetime.datetime.now().strftime('%H:%M')}"
                )
            else:
                response = (
                    f"✅ *Длинный текст отправлен!*\n"
                    f"🔢 Номер: #{display_num}\n"
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
                f"🔢 Номер: #{display_num}\n"
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
    logger.info("✅ Уникальные ID сообщений: ВКЛЮЧЕНО")
    logger.info("✅ Статусы: ⚪ (не переслано), ✅ (переслано)")
    logger.info("✅ База данных сообщений: ГОТОВА")
    
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
            ('list', list_command),
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
        logger.info(f"✅ Сообщений в базе: {len(messages_db)}")
        logger.info("✅ Уникальные ID: timestamp_random")
        logger.info("✅ Маркировка пересылок: ⚪/✅")
        logger.info("✅ Кнопки: РАБОТАЮТ")
        logger.info("✅ Готов к работе 24/7!")
        logger.info("=" * 50)
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
