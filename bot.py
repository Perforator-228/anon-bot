import os
import logging
import datetime
import random
import string
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

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
    'replied': 0,
    'last_reset': datetime.datetime.now().date()
}

# Хранилище сообщений с уникальными ID
messages_db = {}  # {message_id: {'content': str, 'user_id': int, 'time': str, 'forwarded': bool, ...}}
message_counter = 0  # Только для нумерации в интерфейсе

# Хранилище ответов
replies_db = {}  # {reply_id: {'message_id': str, 'admin_id': int, 'reply_text': str, 'time': str}}

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

def generate_reply_id():
    """Генерирует уникальный ID для ответа"""
    timestamp = int(datetime.datetime.now().timestamp())
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"reply_{timestamp}_{random_part}"

def save_message(content, user_id, media_type="text", file_id=None, caption=None, user_message_id=None):
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
        'user_message_id': user_message_id,  # ID сообщения пользователя
        'media_type': media_type,
        'time': datetime.datetime.now().strftime('%H:%M %d.%m.%Y'),
        'forwarded': False,
        'forwarded_to': None,
        'forwarded_by': None,
        'forwarded_time': None,
        'replied': False,
        'replies': [],  # Список ID ответов
        'private_reply_sent': False  # Флаг отправки приватного ответа
    }
    
    logger.info(f"💾 Сохранено сообщение #{message_counter} (ID: {message_id}) от пользователя {user_id}")
    return message_id, message_counter

def save_reply(message_id, admin_id, reply_text, admin_message_id=None):
    """Сохраняет ответ админа"""
    reply_id = generate_reply_id()
    
    replies_db[reply_id] = {
        'id': reply_id,
        'message_id': message_id,
        'admin_id': admin_id,
        'reply_text': reply_text,
        'time': datetime.datetime.now().strftime('%H:%M %d.%m.%Y'),
        'admin_message_id': admin_message_id
    }
    
    # Добавляем ответ в сообщение
    if message_id in messages_db:
        messages_db[message_id]['replies'].append(reply_id)
        messages_db[message_id]['replied'] = True
    
    logger.info(f"💬 Сохранен ответ {reply_id} к сообщению {message_id}")
    return reply_id

def get_message_by_user_message(user_message_id):
    """Находит сообщение по ID сообщения пользователя"""
    for msg_id, data in messages_db.items():
        if data.get('user_message_id') == user_message_id:
            return msg_id, data
    return None, None

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

def mark_as_replied(message_id):
    """Помечает сообщение как отвеченное"""
    if message_id in messages_db:
        messages_db[message_id]['replied'] = True
        stats['replied'] += 1
        return True
    return False

# ========== КНОПКИ ДЕЙСТВИЙ ==========

def create_action_buttons(message_id):
    """Создает кнопки действий для админа"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Отметить пересланным", callback_data=f"mark_{message_id}"),
            InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{message_id}")
        ],
        [
            InlineKeyboardButton("📋 Статус", callback_data=f"status_{message_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{message_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_forward_markup(message_id):
    """Создает кнопки для отметки пересылки"""
    keyboard = [
        [
            InlineKeyboardButton("📰 @новости", callback_data=f"fmark_{message_id}_@новости"),
            InlineKeyboardButton("📢 @объявления", callback_data=f"fmark_{message_id}_@объявления")
        ],
        [
            InlineKeyboardButton("💬 @обсуждения", callback_data=f"fmark_{message_id}_@обсуждения"),
            InlineKeyboardButton("📊 @статистика", callback_data=f"fmark_{message_id}_@статистика")
        ],
        [
            InlineKeyboardButton("✏️ Ввести вручную", callback_data=f"fmark_custom_{message_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИК КНОПОК ==========

def button_handler(update: Update, context: CallbackContext):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    
    # Только админ может использовать кнопки
    if user_id != YOUR_ID:
        query.edit_message_text("❌ У вас нет прав для этого действия!")
        return
    
    data = query.data
    
    if data.startswith("mark_"):
        # Отметить пересланным
        message_id = data.split("_")[1]
        message_data = messages_db.get(message_id)
        
        if message_data:
            keyboard = create_forward_markup(message_id)
            query.edit_message_text(
                f"📤 *КУДА ПЕРЕСЛАНО?*\n\n"
                f"Сообщение: *#{message_data['display_number']}*\n"
                f"Выберите пункт назначения или введите вручную:",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    elif data.startswith("fmark_"):
        # Быстрая отметка пересылки
        parts = data.split("_")
        if len(parts) >= 3:
            message_id = parts[1]
            forwarded_to = parts[2]
            
            update_message_status(message_id, forwarded_to, ADMIN_NAME)
            message_data = messages_db.get(message_id)
            
            # Обновляем оригинальное сообщение
            query.edit_message_text(
                f"✅ *Сообщение #{message_data['display_number']} отмечено как пересланное!*\n\n"
                f"📤 Куда: {forwarded_to}\n"
                f"👤 Кем: {ADMIN_NAME}\n"
                f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}\n\n"
                f"Статус обновлен в основном сообщении.",
                parse_mode='Markdown'
            )
            
            # Сохраняем context для ответа
            context.user_data['waiting_for_reply_to'] = None
    
    elif data.startswith("fmark_custom_"):
        # Ввод места пересылки вручную
        message_id = data.split("_")[2]
        context.user_data['waiting_for_forward_to'] = message_id
        
        query.edit_message_text(
            f"✏️ *ВВЕДИТЕ КУДА ПЕРЕСЛАНО:*\n\n"
            f"Например:\n"
            f"• @канал_новостей\n"
            f"• В группу «Обсуждения»\n"
            f"• В личные сообщения\n\n"
            f"Просто отправьте текст ответом на это сообщение.",
            parse_mode='Markdown'
        )
    
    elif data.startswith("reply_"):
        # Ответить на сообщение
        message_id = data.split("_")[1]
        message_data = messages_db.get(message_id)
        
        if message_data:
            context.user_data['waiting_for_reply_to'] = message_id
            
            # Краткое содержание
            content_preview = str(message_data['content'])[:100]
            if len(str(message_data['content'])) > 100:
                content_preview += "..."
            
            query.edit_message_text(
                f"💬 *ОТВЕТ НА СООБЩЕНИЕ #{message_data['display_number']}*\n\n"
                f"📄 *Сообщение:*\n{content_preview}\n\n"
                f"✏️ *Введите ваш ответ:*\n"
                f"Просто отправьте текст ответом на это сообщение.\n\n"
                f"ℹ️ Ответ будет отправлен анонимно отправителю.",
                parse_mode='Markdown'
            )
    
    elif data.startswith("status_"):
        # Показать статус
        message_id = data.split("_")[1]
        message_data = messages_db.get(message_id)
        
        if message_data:
            status_text = get_status_text(message_data)
            query.edit_message_text(
                status_text,
                parse_mode='Markdown',
                reply_markup=create_action_buttons(message_id)
            )
    
    elif data.startswith("delete_"):
        # Удалить сообщение (только из базы)
        message_id = data.split("_")[1]
        
        if message_id in messages_db:
            del messages_db[message_id]
            query.edit_message_text(
                f"🗑️ *Сообщение удалено из базы данных!*\n\n"
                f"ID: `{message_id}`\n"
                f"ℹ️ Сообщение удалено только из внутренней базы, "
                f"не из чата Telegram.",
                parse_mode='Markdown'
            )

def get_status_text(message_data):
    """Формирует текст статуса"""
    status_icon = "✅" if message_data['forwarded'] else "⚪"
    reply_icon = "💬" if message_data['replied'] else "📭"
    
    text = f"📊 *СТАТУС СООБЩЕНИЯ #{message_data['display_number']}*\n\n"
    text += f"{status_icon} *Пересылка:* {'Переслано' if message_data['forwarded'] else 'Не переслано'}\n"
    text += f"{reply_icon} *Ответ:* {'Отвечено' if message_data['replied'] else 'Нет ответа'}\n\n"
    
    if message_data['forwarded']:
        text += f"📤 *Куда:* {message_data['forwarded_to']}\n"
        text += f"👤 *Кем:* {message_data['forwarded_by']}\n"
        text += f"🕐 *Когда:* {message_data['forwarded_time']}\n\n"
    
    if message_data['replies']:
        text += f"💬 *Ответы ({len(message_data['replies'])}):*\n"
        for i, reply_id in enumerate(message_data['replies'][-3:], 1):  # Последние 3 ответа
            reply = replies_db.get(reply_id)
            if reply:
                text += f"{i}. {reply['time']} - {reply['reply_text'][:50]}...\n"
        text += "\n"
    
    text += f"📝 *Тип:* {message_data['media_type']}\n"
    text += f"🕐 *Получено:* {message_data['time']}\n"
    text += f"👤 *ID отправителя:* `{message_data['user_id']}`\n"
    text += f"🔢 *ID сообщения:* `{message_data['id']}`"
    
    return text

# ========== ОТПРАВКА СООБЩЕНИЙ С КНОПКАМИ ==========

def send_with_buttons(update, context, chat_id):
    """Отправляет медиа с кнопками действий"""
    global stats
    
    stats['total_messages'] += 1
    stats['today_messages'] += 1
    
    today = datetime.datetime.now().date()
    if today != stats['last_reset']:
        stats['today_messages'] = 1
        stats['forwarded'] = 0
        stats['replied'] = 0
        stats['last_reset'] = today
    
    user = update.message.from_user
    
    # Сохраняем ID сообщения пользователя
    user_message_id = update.message.message_id
    
    # 1. ТЕКСТ
    if update.message.text:
        text = update.message.text
        stats['texts'] += 1
        
        # Сохраняем сообщение
        message_id, display_num = save_message(
            text, 
            user.id, 
            "text",
            user_message_id=user_message_id
        )
        message_data = messages_db[message_id]
        
        if len(text) > 150:
            stats['long_texts'] += 1
            # Упрощенная обработка длинных текстов
            header = create_status_header(message_data)
            header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
            header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            
            footer = create_status_footer(message_data)
            
            # Обрезаем текст если очень длинный
            display_text = text[:2000] + "..." if len(text) > 2000 else text
            
            full_text = header + display_text + footer
            
            sent_msg = context.bot.send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=create_action_buttons(message_id)
            )
            
            return "📜 Длинный текст", "long_text", 1, display_num, message_id, sent_msg.message_id
        
        else:
            header = create_status_header(message_data)
            header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
            header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            
            footer = create_status_footer(message_data)
            
            full_text = header + text + footer
            sent_msg = context.bot.send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode='Markdown',
                reply_markup=create_action_buttons(message_id)
            )
            return "📝 Текст", "text", 1, display_num, message_id, sent_msg.message_id
    
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
            caption,
            user_message_id=user_message_id
        )
        message_data = messages_db[message_id]
        
        header = create_status_header(message_data)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption_text = header + (caption if caption else "📸 *ФОТО*")
        caption_text += create_status_footer(message_data)
        
        sent_msg = context.bot.send_photo(
            chat_id=chat_id,
            photo=photo.file_id,
            caption=caption_text,
            parse_mode='Markdown',
            reply_markup=create_action_buttons(message_id)
        )
        return "📸 Фото", "photo", 1, display_num, message_id, sent_msg.message_id
    
    # 3. ВИДЕО и другие типы (упрощенно)
    else:
        media_type = "📦 Медиа"
        if update.message.video:
            stats['videos'] += 1
            media_type = "🎥 Видео"
            file_id = update.message.video.file_id
        elif update.message.document:
            media_type = "📎 Файл"
            file_id = update.message.document.file_id
        elif update.message.animation:
            media_type = "🎞️ GIF"
            file_id = update.message.animation.file_id
        else:
            file_id = None
        
        # Сохраняем сообщение
        caption = update.message.caption if update.message.caption else media_type
        message_id, display_num = save_message(
            caption, 
            user.id, 
            media_type.lower(), 
            file_id, 
            caption,
            user_message_id=user_message_id
        )
        message_data = messages_db[message_id]
        
        header = create_status_header(message_data)
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        # Отправляем заголовок с кнопками
        sent_msg = context.bot.send_message(
            chat_id=chat_id,
            text=header + f"*{media_type}*" + create_status_footer(message_data),
            parse_mode='Markdown',
            reply_markup=create_action_buttons(message_id)
        )
        
        # Пересылаем оригинал если нужно
        try:
            update.message.forward(chat_id=chat_id)
        except:
            pass
        
        return media_type, "other", 1, display_num, message_id, sent_msg.message_id

def create_status_header(message_data):
    """Создает заголовок со статусом"""
    status_icon = "✅" if message_data['forwarded'] else "⚪"
    reply_icon = "💬" if message_data['replied'] else ""
    
    return f"🔥 *АНОНИМКА #{message_data['display_number']}* {status_icon}{reply_icon}\n"

def create_status_footer(message_data):
    """Создает футер со статусом пересылки"""
    footer = f"\n\n──────────────\n"
    
    if message_data['forwarded']:
        footer += f"✅ *ПЕРЕСЛАНО*\n"
        footer += f"📤 Куда: {message_data['forwarded_to']}\n"
        footer += f"👤 Кем: {message_data['forwarded_by']}\n"
        footer += f"🕐 Когда: {message_data['forwarded_time']}\n"
    
    if message_data['replied']:
        footer += f"💬 *ОТВЕЧЕНО*\n"
        footer += f"📨 Ответов: {len(message_data['replies'])}\n"
    
    footer += f"🔢 ID: `{message_data['id']}`"
    return footer

# ========== ОБРАБОТКА ОТВЕТОВ АДМИНА ==========

def handle_admin_reply(update: Update, context: CallbackContext):
    """Обработка ответов админа на сообщения"""
    if update.message.from_user.id != YOUR_ID:
        return
    
    # Проверяем, ждем ли мы ответ для пересылки
    if 'waiting_for_forward_to' in context.user_data:
        message_id = context.user_data['waiting_for_forward_to']
        forwarded_to = update.message.text
        
        update_message_status(message_id, forwarded_to, ADMIN_NAME)
        message_data = messages_db.get(message_id)
        
        update.message.reply_text(
            f"✅ *Сообщение #{message_data['display_number']} отмечено как пересланное!*\n\n"
            f"📤 Куда: {forwarded_to}\n"
            f"👤 Кем: {ADMIN_NAME}\n"
            f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}",
            parse_mode='Markdown'
        )
        
        del context.user_data['waiting_for_forward_to']
        return
    
    # Проверяем, ждем ли мы ответ для пользователя
    elif 'waiting_for_reply_to' in context.user_data:
        message_id = context.user_data['waiting_for_reply_to']
        reply_text = update.message.text
        
        if message_id in messages_db:
            message_data = messages_db[message_id]
            user_id = message_data['user_id']
            
            # Сохраняем ответ
            admin_message_id = update.message.message_id
            reply_id = save_reply(message_id, YOUR_ID, reply_text, admin_message_id)
            
            # Отправляем ответ пользователю
            try:
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"💬 *ОТВЕТ НА ВАШЕ АНОНИМНОЕ СООБЩЕНИЕ #{message_data['display_number']}*\n\n"
                         f"{reply_text}\n\n"
                         f"🕐 {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
                         f"────────────────\n"
                         f"📨 Это ответ на ваше анонимное сообщение. "
                         f"Вы можете продолжать общаться, просто отправляйте новые сообщения.",
                    parse_mode='Markdown'
                )
                
                # Обновляем статус
                mark_as_replied(message_id)
                
                update.message.reply_text(
                    f"✅ *Ответ отправлен пользователю!*\n\n"
                    f"📨 Сообщение: #{message_data['display_number']}\n"
                    f"💬 Ответ: {reply_text[:50]}...\n"
                    f"👤 ID пользователя: `{user_id}`\n"
                    f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}",
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Ошибка отправки ответа пользователю: {e}")
                update.message.reply_text(
                    f"❌ *Не удалось отправить ответ!*\n\n"
                    f"Пользователь, возможно, заблокировал бота.\n"
                    f"Ошибка: {str(e)}",
                    parse_mode='Markdown'
                )
            
            del context.user_data['waiting_for_reply_to']
        return
    
    # Проверяем, является ли это ответом на сообщение бота (реплай)
    elif update.message.reply_to_message:
        replied_message = update.message.reply_to_message
        
        # Ищем сообщение по ID в тексте
        import re
        message_id_match = re.search(r'ID: `([^`]+)`', replied_message.text or "")
        
        if message_id_match:
            message_id = message_id_match.group(1)
            if message_id in messages_db:
                message_data = messages_db[message_id]
                reply_text = update.message.text
                user_id = message_data['user_id']
                
                # Сохраняем ответ
                admin_message_id = update.message.message_id
                reply_id = save_reply(message_id, YOUR_ID, reply_text, admin_message_id)
                
                # Отправляем ответ пользователю
                try:
                    context.bot.send_message(
                        chat_id=user_id,
                        text=f"💬 *ОТВЕТ НА ВАШЕ АНОНИМНОЕ СООБЩЕНИЕ #{message_data['display_number']}*\n\n"
                             f"{reply_text}\n\n"
                             f"🕐 {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
                             f"────────────────\n"
                             f"📨 Это ответ на ваше анонимное сообщение. "
                             f"Вы можете продолжать общаться, просто отправляйте новые сообщения.",
                        parse_mode='Markdown'
                    )
                    
                    # Обновляем статус
                    mark_as_replied(message_id)
                    
                    update.message.reply_text(
                        f"✅ *Ответ отправлен пользователю через реплай!*\n\n"
                        f"📨 Сообщение: #{message_data['display_number']}\n"
                        f"💬 Ответ: {reply_text[:50]}...",
                        parse_mode='Markdown'
                    )
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки ответа пользователю: {e}")
                    update.message.reply_text(
                        f"❌ *Не удалось отправить ответ!*\n\n"
                        f"Пользователь, возможно, заблокировал бота.\n"
                        f"Ошибка: {str(e)}",
                        parse_mode='Markdown'
                    )
                return

# ========== ОБНОВЛЕННЫЕ КОМАНДЫ ==========

def start_command(update: Update, context: CallbackContext):
    """Команда /start"""
    keyboard = [
        [KeyboardButton("📝 Написать анонимно"), KeyboardButton("❓ Помощь")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("🎨 Форматирование")],
        [KeyboardButton("😂 Анекдот"), KeyboardButton("💭 Цитата")],
        [KeyboardButton("🔐 Секреты"), KeyboardButton("📋 Меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    user = update.message.from_user
    is_admin = user.id == YOUR_ID
    
    if is_admin:
        welcome_text = (
            f'🛡️ *АНОНИМНЫЙ ЯЩИК 2.0 - АДМИН ПАНЕЛЬ*\n\n'
            f'✨ *НОВЫЕ ФИЧИ:*\n'
            f'• 💬 Ответы на анонимные сообщения\n'
            f'• 🎯 Кнопки действий под каждым сообщением\n'
            f'• 🔄 Быстрая отметка пересылок\n'
            f'• 👁️‍🗨️ Приватные ответы пользователям\n\n'
            f'🛠️ *КАК РАБОТАТЬ:*\n'
            f'1. Под каждым сообщением есть кнопки\n'
            f'2. Нажми "💬 Ответить" для ответа\n'
            f'3. Или ответьте реплаем на сообщение\n'
            f'4. Пользователь получит ответ приватно\n\n'
            f'🎯 *Используй кнопки ниже или команды!*'
        )
    else:
        welcome_text = (
            f'🕶️ *АНОНИМНЫЙ ЯЩИК 2.0*\n\n'
            f'✨ *НОВЫЕ ФИЧИ:*\n'
            f'• 💬 Теперь админ может отвечать вам!\n'
            f'• 🔒 Полная анонимность\n'
            f'• 📨 Ответы приходят приватно\n'
            f'• 🎭 100+ IT-анекдотов\n\n'
            f'📝 *Как это работает:*\n'
            f'1. Пишите сообщение анонимно\n'
            f'2. Админ может ответить вам\n'
            f'3. Ответ придет сюда же, приватно\n'
            f'4. Никто не увидит ваш диалог\n\n'
            f'🎯 *Используй кнопки ниже или команды!*'
        )
    
    update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def help_command(update: Update, context: CallbackContext):
    """Обновленная команда /help"""
    user = update.message.from_user
    is_admin = user.id == YOUR_ID
    
    if is_admin:
        help_text = (
            '🛡️ *ПОМОЩЬ ДЛЯ АДМИНА*\n\n'
            '🔹 *ОТВЕТЫ НА СООБЩЕНИЯ:*\n'
            '1. *Через кнопки:* Нажми "💬 Ответить" под сообщением\n'
            '2. *Через реплай:* Ответьте на сообщение бота\n'
            '3. *Результат:* Пользователь получит ответ приватно\n\n'
            '🔹 *МАРКИРОВКА ПЕРЕСЫЛОК:*\n'
            '• Нажми "✅ Отметить пересланным"\n'
            '• Выберите канал или введите вручную\n'
            '• Статус обновится в сообщении\n\n'
            '🔹 *ПРОСМОТР СТАТУСА:*\n'
            '• "📋 Статус" - подробная информация\n'
            '• "🗑️ Удалить" - удалить из базы\n\n'
            '🔹 *КОМАНДЫ:*\n'
            '/replies - просмотр всех ответов\n'
            '/dialogs - активные диалоги\n'
            '/unanswered - непрочитанные\n'
            '/stats - статистика ответов'
        )
    else:
        help_text = (
            '📚 *ПОМОЩЬ ДЛЯ ПОЛЬЗОВАТЕЛЯ*\n\n'
            '🔹 *КАК ОТПРАВИТЬ СООБЩЕНИЕ:*\n'
            '• Просто напишите сюда что угодно\n'
            '• Можно отправить фото, видео, файлы\n'
            '• Сообщения полностью анонимны\n\n'
            '🔹 *ОТВЕТЫ АДМИНА:*\n'
            '• Админ может ответить на ваше сообщение\n'
            '• Ответ придет сюда же, приватно\n'
            '• Только вы увидите ответ\n'
            '• Можно продолжать диалог\n\n'
            '🔹 *ЧТО МОЖНО ОТПРАВИТЬ:*\n'
            '📝 Текст любого размера\n'
            '📸 Фото с подписями\n'
            '🎥 Видео, GIF\n'
            '📎 Документы и файлы\n'
            '🎵 Музыка, голосовые\n'
            '🩷 Стикеры и эмодзи\n\n'
            '💡 *СОВЕТ:* Используйте абзацы для лучшей читаемости!'
        )
    
    update.message.reply_text(help_text, parse_mode='Markdown')

def stats_command(update: Update, context: CallbackContext):
    """Обновленная статистика с ответами"""
    stats_text = (
        f'📊 *СТАТИСТИКА БОТА*\n\n'
        f'📨 *СООБЩЕНИЯ:*\n'
        f'• Всего: *{stats["total_messages"]}*\n'
        f'• Сегодня: *{stats["today_messages"]}*\n'
        f'✅ Переслано: *{stats["forwarded"]}*\n'
        f'💬 Отвечено: *{stats["replied"]}*\n'
        f'⚪ Без ответа: *{stats["total_messages"] - stats["replied"]}*\n\n'
        
        f'📈 *ЭФФЕКТИВНОСТЬ:*\n'
        f'• Ответов: *{stats["replied"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n'
        f'• Пересылок: *{stats["forwarded"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n\n'
        
        f'💾 *БАЗА ДАННЫХ:*\n'
        f'• Сообщений: *{len(messages_db)}*\n'
        f'• Ответов: *{len(replies_db)}*\n'
        f'• Пользователей: *{len(set(msg["user_id"] for msg in messages_db.values()))}*'
    )
    
    if update.message.from_user.id == YOUR_ID and replies_db:
        stats_text += f'\n\n💬 *ПОСЛЕДНИЕ ОТВЕТЫ:*\n'
        recent_replies = list(replies_db.items())[-3:]
        for reply_id, reply in recent_replies[::-1]:
            msg_num = messages_db.get(reply['message_id'], {}).get('display_number', '?')
            stats_text += f'• #{msg_num}: {reply["reply_text"][:30]}...\n'
    
    update.message.reply_text(stats_text, parse_mode='Markdown')

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
        '/unforwarded — Непересланные\n'
        '/replies — Просмотр ответов\n'
        '/dialogs — Активные диалоги\n'
        '/unanswered — Непрочитанные\n\n'
        
        '✨ *ИСПОЛЬЗУЙ КНОПКИ ИЛИ КОМАНДЫ!*'
    )
    update.message.reply_text(menu_text, parse_mode='Markdown')

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

# ========== НОВЫЕ КОМАНДЫ ДЛЯ АДМИНА ==========

def replies_command(update: Update, context: CallbackContext):
    """Команда /replies - просмотр всех ответов"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    if not replies_db:
        update.message.reply_text("📭 *Нет отправленных ответов*")
        return
    
    response = f"💬 *ВСЕ ОТПРАВЛЕННЫЕ ОТВЕТЫ:* {len(replies_db)}\n\n"
    
    # Сортируем по времени (новые сначала)
    sorted_replies = sorted(replies_db.items(), 
                          key=lambda x: x[1]['time'], 
                          reverse=True)[:10]  # Последние 10
    
    for reply_id, reply in sorted_replies:
        message_data = messages_db.get(reply['message_id'], {})
        msg_num = message_data.get('display_number', '?')
        
        response += f"📨 *Сообщение #{msg_num}*\n"
        response += f"💬 Ответ: {reply['reply_text'][:50]}"
        if len(reply['reply_text']) > 50:
            response += "..."
        response += f"\n🕐 {reply['time']}\n"
        response += f"🔢 ID ответа: `{reply_id}`\n"
        response += "─" * 30 + "\n\n"
    
    update.message.reply_text(response, parse_mode='Markdown')

def dialogs_command(update: Update, context: CallbackContext):
    """Команда /dialogs - активные диалоги"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    # Группируем сообщения по пользователям
    users_messages = {}
    for msg_id, msg_data in messages_db.items():
        user_id = msg_data['user_id']
        if user_id not in users_messages:
            users_messages[user_id] = []
        users_messages[user_id].append(msg_data)
    
    if not users_messages:
        update.message.reply_text("📭 *Нет активных диалогов*")
        return
    
    response = f"💬 *АКТИВНЫЕ ДИАЛОГИ:* {len(users_messages)}\n\n"
    
    for user_id, messages in users_messages.items():
        messages.sort(key=lambda x: x['display_number'], reverse=True)
        latest_msg = messages[0]
        
        response += f"👤 *Пользователь:* `{user_id}`\n"
        response += f"📨 Сообщений: {len(messages)}\n"
        response += f"💬 Ответов: {sum(1 for m in messages if m['replied'])}\n"
        response += f"📝 Последнее: #{latest_msg['display_number']}\n"
        
        if latest_msg['replied']:
            response += f"✅ Последний ответ: {messages_db[latest_msg['id']]['replies'][-1] if latest_msg['replies'] else '?'}\n"
        
        response += "─" * 30 + "\n\n"
    
    update.message.reply_text(response, parse_mode='Markdown')

def unanswered_command(update: Update, context: CallbackContext):
    """Команда /unanswered - непрочитанные сообщения"""
    if update.message.from_user.id != YOUR_ID:
        update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    # Находим неотвеченные сообщения
    unanswered = []
    for msg_id, msg_data in messages_db.items():
        if not msg_data['replied']:
            unanswered.append((msg_id, msg_data))
    
    if not unanswered:
        update.message.reply_text(
            "🎉 *ВСЕМ ОТВЕЧЕНО!*\n\n"
            f"✅ Отвечено: {stats['replied']} из {stats['total_messages']}\n"
            f"📊 Эффективность: {stats['replied'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0:.1f}%",
            parse_mode='Markdown'
        )
        return
    
    # Сортируем по номеру (новые сначала)
    unanswered.sort(key=lambda x: x[1]['display_number'], reverse=True)
    
    response = f"📭 *НЕОТВЕЧЕННЫЕ СООБЩЕНИЯ:* {len(unanswered)}\n\n"
    
    for i, (msg_id, msg_data) in enumerate(unanswered[:10], 1):  # Первые 10
        content_preview = str(msg_data['content'])[:50]
        if len(str(msg_data['content'])) > 50:
            content_preview += "..."
        
        response += f"{i}. *#{msg_data['display_number']}* ({msg_data['time']})\n"
        response += f"   📄 {content_preview}\n"
        response += f"   🔢 ID: `{msg_id}`\n"
        
        # Кнопки быстрых действий
        keyboard = [
            [
                InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{msg_id}"),
                InlineKeyboardButton("✅ Отметить", callback_data=f"mark_{msg_id}")
            ]
        ]
        
        if i < len(unanswered[:10]):
            response += "   ─\n"
    
    update.message.reply_text(
        response, 
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard) if unanswered[:10] else None
    )

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
            f'• Отвечено: *{stats["replied"]}*\n'
            f'• Эффективность: *{stats["replied"] / stats["total_messages"] * 100 if stats["total_messages"] > 0 else 0:.1f}%*\n\n'
            
            f'🔧 *КОМАНДЫ УПРАВЛЕНИЯ:*\n'
            f'`/mark <ID> <куда>` — пометить пересылку\n'
            f'`/status <ID>` — статус сообщения\n'
            f'`/list` — все сообщения\n'
            f'`/list переслано` — пересланные\n'
            f'`/list непереслано` — непересланные\n'
            f'`/unforwarded` — непересланные (кратко)\n'
            f'`/replies` — все ответы\n'
            f'`/dialogs` — активные диалоги\n'
            f'`/unanswered` — неотвеченные\n\n'
            
            f'⚙️ *СИСТЕМА:*\n'
            f'• Уникальные ID: ✅ РАБОТАЕТ\n'
            f'• Кнопки действий: ✅ ВКЛЮЧЕНО\n'
            f'• Приватные ответы: ✅ ВКЛЮЧЕНО\n'
            f'• Время: {now.strftime("%H:%M:%S")}\n\n'
            
            f'💡 *КАК ОТВЕЧАТЬ:*\n'
            f'1. Нажми "💬 Ответить" под сообщением\n'
            f'2. Или ответьте реплаем на сообщение бота\n'
            f'3. Пользователь получит ответ приватно'
        )
        update.message.reply_text(admin_text, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ Доступ запрещен.")

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

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

def handle_message(update: Update, context: CallbackContext):
    """Обрабатывает все сообщения"""
    # Если это админ и это ответ на что-то
    if update.message.from_user.id == YOUR_ID:
        handle_admin_reply(update, context)
        return
    
    # Пропускаем команды от кнопок
    if update.message.text and handle_text_commands(update, context):
        return
    
    user = update.message.from_user
    logger.info(f"📨 Входящее сообщение от пользователя {user.id}")
    
    try:
        media_type, media_category, parts_count, display_num, message_id, admin_message_id = send_with_buttons(
            update, context, YOUR_ID
        )
        
        # Сохраняем ID сообщения админа
        if message_id in messages_db:
            messages_db[message_id]['admin_message_id'] = admin_message_id
        
        # Отправляем подтверждение пользователю
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
            f"💡 *Теперь админ может ответить вам!*\n"
            f"Ответ придет сюда же, приватно.\n\n"
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
    logger.info("🚀 ЗАПУСКАЮ БОТА С СИСТЕМОЙ ОТВЕТОВ!")
    logger.info(f"👑 Админ ID: {YOUR_ID}")
    logger.info("✅ Система ответов: ВКЛЮЧЕНО")
    logger.info("✅ Кнопки действий: ВКЛЮЧЕНО")
    logger.info("✅ Приватные ответы: ВКЛЮЧЕНО")
    
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
            ('replies', replies_command),
            ('dialogs', dialogs_command),
            ('unanswered', unanswered_command),
        ]
        
        for cmd_name, cmd_func in commands:
            dp.add_handler(CommandHandler(cmd_name, cmd_func))
        
        # Обработчик кнопок
        dp.add_handler(CallbackQueryHandler(button_handler))
        
        # Обработчик сообщений
        dp.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))
        
        # Обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем
        updater.start_polling()
        
        logger.info("=" * 50)
        logger.info("✅ БОТ С СИСТЕМОЙ ОТВЕТОВ ЗАПУЩЕН!")
        logger.info(f"✅ Команд: {len(commands)}")
        logger.info("✅ Кнопки действий под сообщениями")
        logger.info("✅ Приватные ответы пользователям")
        logger.info("✅ Быстрая отметка пересылок")
        logger.info("✅ Готов к работе!")
        logger.info("=" * 50)
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
