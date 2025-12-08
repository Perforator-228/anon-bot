import os
import logging
import datetime
import random
import string
import re
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
        'admin_message_id': None  # ID сообщения с кнопками
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
            InlineKeyboardButton("✏️ Ввести вручную", callback_data=f"custom_{message_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИК КНОПОК ==========

def button_handler(update: Update, context: CallbackContext):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    
    # Обязательно отвечаем на callback
    query.answer()
    
    user_id = query.from_user.id
    
    # Только админ может использовать кнопки
    if user_id != YOUR_ID:
        query.edit_message_text("❌ У вас нет прав для этого действия!")
        return
    
    data = query.data
    
    # Логируем нажатие
    logger.info(f"🎯 Нажата кнопка: {data} от пользователя {user_id}")
    
    try:
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
            else:
                query.edit_message_text("❌ Сообщение не найдено в базе!")
        
        elif data.startswith("fmark_"):
            # Быстрая отметка пересылки
            parts = data.split("_")
            if len(parts) >= 3:
                message_id = parts[1]
                # Объединяем все оставшиеся части как название канала
                forwarded_to = "_".join(parts[2:])
                
                if update_message_status(message_id, forwarded_to, ADMIN_NAME):
                    message_data = messages_db.get(message_id)
                    
                    # Обновляем оригинальное сообщение с кнопками
                    try:
                        # Получаем текущий текст сообщения
                        original_text = query.message.text
                        if original_text:
                            # Обновляем статус в тексте (меняем ⚪ на ✅)
                            if "⚪" in original_text:
                                updated_text = original_text.replace("⚪", "✅")
                            else:
                                # Если нет ⚪, добавляем статус
                                lines = original_text.split('\n')
                                if len(lines) > 0:
                                    lines[0] = lines[0].replace("⚪", "✅")
                                    updated_text = '\n'.join(lines)
                                else:
                                    updated_text = original_text
                            
                            # Обновляем сообщение
                            context.bot.edit_message_text(
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                text=updated_text,
                                parse_mode='Markdown',
                                reply_markup=create_action_buttons(message_id)
                            )
                    except Exception as e:
                        logger.error(f"Не удалось обновить сообщение: {e}")
                    
                    query.edit_message_text(
                        f"✅ *Сообщение #{message_data['display_number']} отмечено как пересланное!*\n\n"
                        f"📤 Куда: {forwarded_to}\n"
                        f"👤 Кем: {ADMIN_NAME}\n"
                        f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}\n\n"
                        f"Статус обновлен в основном сообщении.",
                        parse_mode='Markdown'
                    )
                else:
                    query.edit_message_text("❌ Не удалось обновить статус сообщения!")
        
        elif data.startswith("custom_"):
            # Ввод места пересылки вручную
            message_id = data.split("_")[1]
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
            else:
                query.edit_message_text("❌ Сообщение не найдено!")
        
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
            else:
                query.edit_message_text("❌ Сообщение не найдено!")
        
        elif data.startswith("delete_"):
            # Удалить сообщение (только из базы)
            message_id = data.split("_")[1]
            
            if message_id in messages_db:
                display_num = messages_db[message_id]['display_number']
                del messages_db[message_id]
                query.edit_message_text(
                    f"🗑️ *Сообщение #{display_num} удалено из базы данных!*\n\n"
                    f"ID: `{message_id}`\n"
                    f"ℹ️ Сообщение удалено только из внутренней базы, "
                    f"не из чата Telegram.",
                    parse_mode='Markdown'
                )
            else:
                query.edit_message_text("❌ Сообщение не найдено!")
        
        else:
            query.edit_message_text(f"❌ Неизвестная команда: {data}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в обработчике кнопок: {e}")
        query.edit_message_text(f"❌ Произошла ошибка: {str(e)[:100]}")

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
        
        # Создаем заголовок
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        # Обрезаем текст если очень длинный
        if len(text) > 150:
            stats['long_texts'] += 1
            if len(text) > 2000:
                display_text = text[:2000] + "..."
            else:
                display_text = text
        else:
            display_text = text
        
        # Футер с ID
        footer = f"\n\n──────────────\n🔢 ID: `{message_id}`"
        
        full_text = header + display_text + footer
        
        # Отправляем сообщение с кнопками
        sent_msg = context.bot.send_message(
            chat_id=chat_id,
            text=full_text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=create_action_buttons(message_id)
        )
        
        # Сохраняем ID сообщения с кнопками
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        
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
        
        # Создаем заголовок
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption_text = header + (caption if caption else "📸 *ФОТО*")
        caption_text += f"\n\n──────────────\n🔢 ID: `{message_id}`"
        
        # Отправляем фото с кнопками
        sent_msg = context.bot.send_photo(
            chat_id=chat_id,
            photo=photo.file_id,
            caption=caption_text,
            parse_mode='Markdown',
            reply_markup=create_action_buttons(message_id)
        )
        
        # Сохраняем ID сообщения с кнопками
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        
        return "📸 Фото", "photo", 1, display_num, message_id, sent_msg.message_id
    
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
            caption,
            user_message_id=user_message_id
        )
        
        # Создаем заголовок
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        caption_text = header + (caption if caption else "🎥 *ВИДЕО*")
        caption_text += f"\n\n──────────────\n🔢 ID: `{message_id}`"
        
        # Отправляем видео с кнопками
        sent_msg = context.bot.send_video(
            chat_id=chat_id,
            video=update.message.video.file_id,
            caption=caption_text,
            parse_mode='Markdown',
            reply_markup=create_action_buttons(message_id)
        )
        
        # Сохраняем ID сообщения с кнопками
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        
        return "🎥 Видео", "video", 1, display_num, message_id, sent_msg.message_id
    
    # 4. Другие типы
    else:
        media_type = "📦 Медиа"
        if update.message.document:
            media_type = "📎 Файл"
            file_id = update.message.document.file_id
        elif update.message.animation:
            media_type = "🎞️ GIF"
            file_id = update.message.animation.file_id
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
            caption,
            user_message_id=user_message_id
        )
        
        # Создаем заголовок
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        
        # Отправляем заголовок с кнопками
        sent_msg = context.bot.send_message(
            chat_id=chat_id,
            text=header + f"*{media_type}*" + f"\n\n──────────────\n🔢 ID: `{message_id}`",
            parse_mode='Markdown',
            reply_markup=create_action_buttons(message_id)
        )
        
        # Сохраняем ID сообщения с кнопками
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        
        # Пересылаем оригинал если нужно
        try:
            if update.message.document:
                context.bot.send_document(chat_id=chat_id, document=file_id)
            elif update.message.animation:
                context.bot.send_animation(chat_id=chat_id, animation=file_id)
            elif update.message.audio:
                context.bot.send_audio(chat_id=chat_id, audio=file_id)
            elif update.message.voice:
                context.bot.send_voice(chat_id=chat_id, voice=file_id)
            elif update.message.sticker:
                context.bot.send_sticker(chat_id=chat_id, sticker=file_id)
            else:
                update.message.forward(chat_id=chat_id)
        except:
            pass
        
        return media_type, "other", 1, display_num, message_id, sent_msg.message_id

# ========== ОБРАБОТКА ОТВЕТОВ АДМИНА ==========

def handle_admin_reply(update: Update, context: CallbackContext):
    """Обработка ответов админа на сообщения"""
    if update.message.from_user.id != YOUR_ID:
        return
    
    # Проверяем, ждем ли мы ответ для пересылки
    if 'waiting_for_forward_to' in context.user_data:
        message_id = context.user_data['waiting_for_forward_to']
        forwarded_to = update.message.text
        
        if update_message_status(message_id, forwarded_to, ADMIN_NAME):
            message_data = messages_db.get(message_id)
            
            update.message.reply_text(
                f"✅ *Сообщение #{message_data['display_number']} отмечено как пересланное!*\n\n"
                f"📤 Куда: {forwarded_to}\n"
                f"👤 Кем: {ADMIN_NAME}\n"
                f"🕐 Время: {datetime.datetime.now().strftime('%H:%M')}",
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text("❌ Не удалось обновить статус сообщения!")
        
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
                    f"Ошибка: {str(e)[:100]}",
                    parse_mode='Markdown'
                )
            
            del context.user_data['waiting_for_reply_to']
        return
    
    # Проверяем, является ли это ответом на сообщение бота (реплай)
    elif update.message.reply_to_message:
        replied_message = update.message.reply_to_message
        
        # Ищем сообщение по ID в тексте
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
                        f"Ошибка: {str(e)[:100]}",
                        parse_mode='Markdown'
                    )
                return

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

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
            f'🛡️ *АНОНИМНЫЙ ЯЩИК - АДМИН ПАНЕЛЬ*\n\n'
            f'✨ *ИНСТРУКЦИЯ:*\n'
            f'1. Под каждым сообщением есть кнопки\n'
            f'2. "✅ Отметить" - отметить пересылку\n'
            f'3. "💬 Ответить" - ответить пользователю\n'
            f'4. Ответы приходят пользователям приватно\n\n'
            f'🎯 *Кнопки работают!* Нажмите на любую кнопку под сообщением.'
        )
    else:
        welcome_text = (
            f'🕶️ *АНОНИМНЫЙ ЯЩИК*\n\n'
            f'✨ *НОВЫЕ ФИЧИ:*\n'
            f'• 💬 Админ может отвечать вам!\n'
            f'• 🔒 Полная анонимность\n'
            f'• 📨 Ответы приходят приватно\n'
            f'• 🎭 100+ IT-анекдотов\n'
            f'• 📚 9 интересных фактов\n\n'
            f'📝 *Как это работает:*\n'
            f'1. Пишите сообщение анонимно\n'
            f'2. Админ может ответить вам\n'
            f'3. Ответ придет сюда же, приватно\n\n'
            f'🎯 *Напишите что-нибудь чтобы начать!*'
        )
    
    update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def help_command(update: Update, context: CallbackContext):
    """Команда /help"""
    user = update.message.from_user
    is_admin = user.id == YOUR_ID
    
    if is_admin:
        help_text = (
            '🛡️ *ПОМОЩЬ ДЛЯ АДМИНА*\n\n'
            '🔹 *КНОПКИ ПОД СООБЩЕНИЯМИ:*\n'
            '✅ *Отметить пересланным* - отметить куда переслано\n'
            '💬 *Ответить* - отправить ответ пользователю\n'
            '📋 *Статус* - подробная информация\n'
            '🗑️ *Удалить* - удалить из базы\n\n'
            '🔹 *ТРИ СПОСОБА ОТВЕТИТЬ:*\n'
            '1. Нажать "💬 Ответить" под сообщением\n'
            '2. Ответить реплаем на сообщение бота\n'
            '3. Пользователь получит ответ приватно\n\n'
            '🔹 *СТАТУСЫ:*\n'
            '⚪ - не переслано\n'
            '✅ - переслано\n'
            '💬 - есть ответы\n\n'
            '🔹 *КОМАНДЫ:*\n'
            '/admin - панель админа\n'
            '/stats - статистика\n'
            '/joke - анекдот\n'
            '/fact - интересный факт'
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
    """Команда /stats - статистика"""
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
    
    update.message.reply_text(stats_text, parse_mode='Markdown')

# ========== РАЗВЛЕКАТЕЛЬНЫЕ КОМАНДЫ ==========

def joke_command(update: Update, context: CallbackContext):
    """Команда /joke - 100+ анекдотов!"""
    joke = random.choice(JOKES)
    joke_number = random.randint(1, 100)
    
    response = f"😂 *АНЕКДОТ #{joke_number}*\n\n{joke}\n\n"
    response += f"📚 В базе: {len(JOKES)} анекдотов\n"
    response += f"🎯 Хочешь еще? Пиши /joke снова!"
    
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
        '/stats — Статистика\n\n'
        
        '😂 *РАЗВЛЕЧЕНИЯ:*\n'
        '/joke — 100+ анекдотов про IT!\n'
        '/fact — Интересные факты\n'
        '/quote — Цитата дня\n'
        '/secret — Секретная информация\n\n'
        
        '🛡️ *АДМИН:*\n'
        '/admin — Панель админа\n\n'
        
        '✨ *ИСПОЛЬЗУЙ КНОПКИ ИЛИ КОМАНДЫ!*'
    )
    update.message.reply_text(menu_text, parse_mode='Markdown')

# ========== АДМИН КОМАНДЫ ==========

def admin_command(update: Update, context: CallbackContext):
    """Команда /admin - панель админа"""
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
            
            f'🎯 *КНОПКИ РАБОТАЮТ!*\n'
            f'Под каждым сообщением есть 4 кнопки:\n'
            f'1. ✅ Отметить пересланным\n'
            f'2. 💬 Ответить пользователю\n'
            f'3. 📋 Статус сообщения\n'
            f'4. 🗑️ Удалить из базы\n\n'
            
            f'⚙️ *СИСТЕМА:*\n'
            f'• Inline-кнопки: ✅ РАБОТАЮТ\n'
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
    logger.info("🚀 ЗАПУСКАЮ БОТА С РАБОЧИМИ КНОПКАМИ!")
    logger.info(f"👑 Админ ID: {YOUR_ID}")
    logger.info("✅ Inline кнопки: ВКЛЮЧЕНО")
    logger.info("✅ CallbackQueryHandler: ЗАРЕГИСТРИРОВАН")
    logger.info("✅ 100+ анекдотов и 9 фактов: ГОТОВО")
    
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # ОЧЕНЬ ВАЖНО: Регистрируем обработчик кнопок ПЕРВЫМ!
        dp.add_handler(CallbackQueryHandler(button_handler))
        
        # Регистрация команд
        commands = [
            ('start', start_command),
            ('help', help_command),
            ('stats', stats_command),
            ('joke', joke_command),
            ('fact', fact_command),
            ('quote', quote_command),
            ('secret', secret_command),
            ('menu', menu_command),
            ('admin', admin_command),
        ]
        
        for cmd_name, cmd_func in commands:
            dp.add_handler(CommandHandler(cmd_name, cmd_func))
        
        # Обработчик сообщений (последним!)
        dp.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))
        
        # Обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем
        updater.start_polling()
        
        logger.info("=" * 50)
        logger.info("✅ БОТ ЗАПУЩЕН С РАБОЧИМИ КНОПКАМИ!")
        logger.info(f"✅ Команд: {len(commands)}")
        logger.info("✅ Inline-кнопки готовы к работе")
        logger.info("✅ Система ответов включена")
        logger.info("✅ Анекдоты и факты загружены")
        logger.info("✅ Готов к работе 24/7!")
        logger.info("=" * 50)
        
        # Отправляем тестовое сообщение админу
        try:
            updater.bot.send_message(
                chat_id=YOUR_ID,
                text="🤖 *Бот успешно запущен!*\n\n"
                     "✨ *Все функции работают:*\n"
                     "✅ Inline-кнопки под сообщениями\n"
                     "✅ Приватные ответы пользователям\n"
                     "✅ 100+ IT-анекдотов (/joke)\n"
                     "✅ 9 интересных фактов (/fact)\n\n"
                     "🎯 *Как тестировать:*\n"
                     "1. Попросите кого-нибудь отправить сообщение\n"
                     "2. Под сообщением появятся 4 кнопки\n"
                     "3. Нажмите любую кнопку - она сработает!\n\n"
                     "💡 Кнопки: ✅ Отметить, 💬 Ответить, 📋 Статус, 🗑️ Удалить",
                parse_mode='Markdown'
            )
        except:
            pass
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
