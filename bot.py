import os
import logging
import datetime
import random
import string
import re
import json
import time
from collections import defaultdict
from typing import Optional, Dict, Any, Tuple

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
YOUR_ID = os.getenv('YOUR_ID')
ADMIN_NAME = os.getenv('ADMIN_NAME', 'Админ')

if not TOKEN:
    logger.error("❌ Нет BOT_TOKEN!")
    exit()

if not YOUR_ID:
    logger.error("❌ Нет YOUR_ID!")
    exit()

try:
    YOUR_ID = int(YOUR_ID)
except ValueError:
    logger.error(f"❌ YOUR_ID должен быть числом: {YOUR_ID}")
    exit()

stats = {
    'total_messages': 0,
    'today_messages': 0,
    'photos': 0,
    'videos': 0,
    'texts': 0,
    'long_texts': 0,
    'forwarded': 0,
    'replied': 0,
    'last_reset': datetime.datetime.now().date().isoformat()
}

messages_db: Dict[str, Any] = {}
replies_db: Dict[str, Any] = {}
message_counter = 0

def load_database() -> Dict:
    try:
        if os.path.exists('messages_db.json'):
            with open('messages_db.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"📂 Загружена база данных")
                return data
        return {'messages': {}, 'replies': {}, 'message_counter': 0, 'stats': stats}
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return {'messages': {}, 'replies': {}, 'message_counter': 0, 'stats': stats}

def save_database() -> None:
    try:
        data = {
            'messages': messages_db,
            'replies': replies_db,
            'message_counter': message_counter,
            'stats': stats
        }
        with open('messages_db.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("💾 База данных сохранена")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")

data = load_database()
messages_db = data.get('messages', {})
replies_db = data.get('replies', {})
message_counter = data.get('message_counter', 0)
stats.update(data.get('stats', stats))

today = datetime.datetime.now().date().isoformat()
if today != stats['last_reset']:
    stats['today_messages'] = 0
    stats['last_reset'] = today

JOKES = [
    "Почему программист всегда мокрый? Потому что он постоянно в бассейне (pool)! 🏊‍♂️",
    "Что сказал один байт другому? Я тебя bit! 💻",
    "Почему математик плохо спит? Потому что он считает овец в уме! 🐑",
]

FACTS = [
    "Деньги киньте, я спасибо скажу 💸",
    "У Перфоратора есть связи с сценапистами Лололошки 🎬",
]

def escape_markdown(text: str) -> str:
    chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(chars)}])', r'\\\1', str(text))

def find_message_by_display_number(display_number: int) -> Tuple[Optional[str], Optional[Dict]]:
    for msg_id, msg_data in messages_db.items():
        if msg_data.get('display_number') == display_number:
            return msg_id, msg_data
    return None, None

def find_message_by_any_id(search_id: str) -> Tuple[Optional[str], Optional[Dict]]:
    if search_id in messages_db:
        return search_id, messages_db[search_id]
    try:
        display_num = int(search_id)
        return find_message_by_display_number(display_num)
    except ValueError:
        return None, None

def generate_message_id() -> str:
    timestamp = int(datetime.datetime.now().timestamp())
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{random_part}"

def generate_reply_id() -> str:
    timestamp = int(datetime.datetime.now().timestamp())
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"reply_{timestamp}_{random_part}"

def save_message(content: str, user_id: int, media_type: str = "text", file_id: str = None, caption: str = None, user_message_id: int = None) -> Tuple[str, int]:
    global message_counter
    message_id = generate_message_id()
    message_counter += 1
    messages_db[message_id] = {
        'id': message_id,
        'display_number': message_counter,
        'content': content,
        'file_id': file_id,
        'caption': caption,
        'user_id': user_id,
        'user_message_id': user_message_id,
        'media_type': media_type,
        'time': datetime.datetime.now().strftime('%H:%M %d.%m.%Y'),
        'forwarded': False,
        'forwarded_to': None,
        'forwarded_by': None,
        'forwarded_time': None,
        'replied': False,
        'replies': [],
        'admin_message_id': None
    }
    if message_counter % 5 == 0:
        save_database()
    return message_id, message_counter

def save_reply(message_id: str, admin_id: int, reply_text: str, admin_message_id: int = None) -> str:
    reply_id = generate_reply_id()
    replies_db[reply_id] = {
        'id': reply_id,
        'message_id': message_id,
        'admin_id': admin_id,
        'reply_text': reply_text,
        'time': datetime.datetime.now().strftime('%H:%M %d.%m.%Y'),
        'admin_message_id': admin_message_id
    }
    if message_id in messages_db:
        messages_db[message_id]['replies'].append(reply_id)
        messages_db[message_id]['replied'] = True
    save_database()
    return reply_id

def update_message_status(message_id: str, forwarded_to: str = None, forwarded_by: str = None) -> bool:
    if message_id in messages_db:
        messages_db[message_id]['forwarded'] = True
        messages_db[message_id]['forwarded_to'] = forwarded_to
        messages_db[message_id]['forwarded_by'] = forwarded_by
        messages_db[message_id]['forwarded_time'] = datetime.datetime.now().strftime('%H:%M')
        stats['forwarded'] += 1
        save_database()
        return True
    return False

def mark_as_replied(message_id: str) -> bool:
    if message_id in messages_db:
        messages_db[message_id]['replied'] = True
        stats['replied'] += 1
        save_database()
        return True
    return False

def create_action_buttons(message_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("✅ Отметить пересланным", callback_data=f"mark_{message_id[:20]}"),
            InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{message_id[:20]}")
        ],
        [
            InlineKeyboardButton("📋 Статус", callback_data=f"status_{message_id[:20]}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{message_id[:20]}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_forward_markup(message_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📰 @новости", callback_data=f"fmark_{message_id[:20]}_@новости"),
            InlineKeyboardButton("📢 @объявления", callback_data=f"fmark_{message_id[:20]}_@объявления")
        ],
        [
            InlineKeyboardButton("💬 @обсуждения", callback_data=f"fmark_{message_id[:20]}_@обсуждения"),
            InlineKeyboardButton("📊 @статистика", callback_data=f"fmark_{message_id[:20]}_@статистика")
        ],
        [
            InlineKeyboardButton("✏️ Ввести вручную", callback_data=f"custom_{message_id[:20]}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_status_text(message_data: Dict) -> str:
    status_icon = "✅" if message_data['forwarded'] else "⚪"
    reply_icon = "💬" if message_data['replied'] else "📭"
    text = f"📊 *СТАТУС СООБЩЕНИЯ #{message_data['display_number']}*\n\n"
    text += f"{status_icon} *Пересылка:* {'Переслано' if message_data['forwarded'] else 'Не переслано'}\n"
    text += f"{reply_icon} *Ответ:* {'Отвечено' if message_data['replied'] else 'Нет ответа'}\n\n"
    if message_data['forwarded']:
        text += f"📤 *Куда:* {escape_markdown(message_data['forwarded_to'])}\n"
        text += f"👤 *Кем:* {escape_markdown(message_data['forwarded_by'])}\n"
        text += f"🕐 *Когда:* {message_data['forwarded_time']}\n\n"
    if message_data['replies']:
        text += f"💬 *Ответы ({len(message_data['replies'])}):*\n"
        for i, reply_id in enumerate(message_data['replies'][-3:], 1):
            reply = replies_db.get(reply_id)
            if reply:
                text += f"{i}. {reply['time']} - {escape_markdown(reply['reply_text'][:50])}...\n"
        text += "\n"
    text += f"📝 *Тип:* {message_data['media_type']}\n"
    text += f"🕐 *Получено:* {message_data['time']}\n"
    text += f"👤 *ID отправителя:* `{message_data['user_id']}`\n"
    text += f"🔢 *ID сообщения:* `{message_data['id']}`"
    return text

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != YOUR_ID:
        await query.edit_message_text("❌ У вас нет прав для этого действия!")
        return
    
    data = query.data
    logger.info(f"🎯 Нажата кнопка: {data}")
    
    try:
        if data.startswith("mark_"):
            search_id = data[5:]
            message_id, message_data = find_message_by_any_id(search_id)
            if message_data:
                keyboard = create_forward_markup(message_id)
                await query.edit_message_text(
                    f"📤 *КУДА ПЕРЕСЛАНО?*\n\n"
                    f"Сообщение: *#{message_data['display_number']}*\n"
                    f"Выберите пункт назначения или введите вручную:",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            else:
                await query.edit_message_text(f"❌ Сообщение не найдено!")
        
        elif data.startswith("fmark_"):
            parts = data.split("_", 2)
            if len(parts) >= 3:
                search_id = parts[1]
                forwarded_to = parts[2]
                message_id, message_data = find_message_by_any_id(search_id)
                if message_data and update_message_status(message_id, forwarded_to, ADMIN_NAME):
                    await query.edit_message_text(
                        f"✅ *Сообщение #{message_data['display_number']} отмечено как пересланное!*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await query.edit_message_text("❌ Не удалось обновить статус!")
        
        elif data.startswith("custom_"):
            search_id = data[7:]
            message_id, message_data = find_message_by_any_id(search_id)
            if message_data:
                context.user_data['waiting_for_forward_to'] = message_id
                await query.edit_message_text(
                    f"✏️ *ВВЕДИТЕ КУДА ПЕРЕСЛАНО:*\n\n"
                    f"Просто отправьте текст ответом на это сообщение.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(f"❌ Сообщение не найдено!")
        
        elif data.startswith("reply_"):
            search_id = data[6:]
            message_id, message_data = find_message_by_any_id(search_id)
            if message_data:
                context.user_data['waiting_for_reply_to'] = message_id
                await query.edit_message_text(
                    f"💬 *ОТВЕТ НА СООБЩЕНИЕ #{message_data['display_number']}*\n\n"
                    f"✏️ *Введите ваш ответ:*\n"
                    f"Просто отправьте текст ответом на это сообщение.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(f"❌ Сообщение не найдено!")
        
        elif data.startswith("status_"):
            search_id = data[7:]
            message_id, message_data = find_message_by_any_id(search_id)
            if message_data:
                status_text = get_status_text(message_data)
                await query.edit_message_text(
                    status_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=create_action_buttons(message_id)
                )
            else:
                await query.edit_message_text(f"❌ Сообщение не найдено!")
        
        elif data.startswith("delete_"):
            search_id = data[7:]
            message_id, message_data = find_message_by_any_id(search_id)
            if message_data:
                display_num = message_data['display_number']
                del messages_db[message_id]
                save_database()
                await query.edit_message_text(
                    f"🗑️ *Сообщение #{display_num} удалено из базы данных!*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(f"❌ Сообщение не найдено!")
    
    except Exception as e:
        logger.error(f"❌ Ошибка в кнопках: {e}")
        await query.edit_message_text(f"❌ Произошла ошибка")

async def send_with_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> Tuple[str, str, int, int, str, int]:
    global stats
    stats['total_messages'] += 1
    stats['today_messages'] += 1
    
    today = datetime.datetime.now().date().isoformat()
    if today != stats['last_reset']:
        stats['today_messages'] = 1
        stats['forwarded'] = 0
        stats['replied'] = 0
        stats['last_reset'] = today
    
    user = update.message.from_user
    user_message_id = update.message.message_id
    
    if update.message.text:
        text = update.message.text
        stats['texts'] += 1
        message_id, display_num = save_message(text, user.id, "text", user_message_id=user_message_id)
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        if len(text) > 150:
            stats['long_texts'] += 1
            if len(text) > 2000:
                display_text = text[:2000] + "..."
            else:
                display_text = text
        else:
            display_text = text
        footer = f"\n\n──────────────\n🔢 ID: `{message_id}`"
        full_text = header + display_text + footer
        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=full_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=create_action_buttons(message_id)
        )
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        save_database()
        return "📝 Текст", "text", 1, display_num, message_id, sent_msg.message_id
    
    elif update.message.photo:
        stats['photos'] += 1
        photo = update.message.photo[-1]
        caption = update.message.caption if update.message.caption else "📸 ФОТО"
        message_id, display_num = save_message(caption, user.id, "photo", photo.file_id, caption, user_message_id)
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        caption_text = header + (caption if caption else "📸 *ФОТО*")
        caption_text += f"\n\n──────────────\n🔢 ID: `{message_id}`"
        sent_msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo.file_id,
            caption=caption_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_action_buttons(message_id)
        )
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        save_database()
        return "📸 Фото", "photo", 1, display_num, message_id, sent_msg.message_id
    
    elif update.message.video:
        stats['videos'] += 1
        caption = update.message.caption if update.message.caption else "🎥 ВИДЕО"
        message_id, display_num = save_message(caption, user.id, "video", update.message.video.file_id, caption, user_message_id)
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        caption_text = header + (caption if caption else "🎥 *ВИДЕО*")
        caption_text += f"\n\n──────────────\n🔢 ID: `{message_id}`"
        sent_msg = await context.bot.send_video(
            chat_id=chat_id,
            video=update.message.video.file_id,
            caption=caption_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_action_buttons(message_id)
        )
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        save_database()
        return "🎥 Видео", "video", 1, display_num, message_id, sent_msg.message_id
    
    else:
        media_type = "📦 Медиа"
        file_id = None
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
        
        caption = update.message.caption if update.message.caption else media_type
        message_id, display_num = save_message(caption, user.id, media_type.lower(), file_id, caption, user_message_id)
        header = f"🔥 *АНОНИМКА #{display_num}* ⚪\n"
        header += f"⏰ {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}\n"
        header += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=header + f"*{media_type}*" + f"\n\n──────────────\n🔢 ID: `{message_id}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_action_buttons(message_id)
        )
        messages_db[message_id]['admin_message_id'] = sent_msg.message_id
        save_database()
        try:
            if update.message.document:
                await context.bot.send_document(chat_id=chat_id, document=file_id)
            elif update.message.animation:
                await context.bot.send_animation(chat_id=chat_id, animation=file_id)
            elif update.message.audio:
                await context.bot.send_audio(chat_id=chat_id, audio=file_id)
            elif update.message.voice:
                await context.bot.send_voice(chat_id=chat_id, voice=file_id)
            elif update.message.sticker:
                await context.bot.send_sticker(chat_id=chat_id, sticker=file_id)
        except:
            pass
        return media_type, "other", 1, display_num, message_id, sent_msg.message_id

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != YOUR_ID:
        return
    
    if 'waiting_for_forward_to' in context.user_data:
        search_id = context.user_data['waiting_for_forward_to']
        forwarded_to = update.message.text
        message_id, message_data = find_message_by_any_id(search_id)
        if message_data and update_message_status(message_id, forwarded_to, ADMIN_NAME):
            await update.message.reply_text(
                f"✅ *Сообщение #{message_data['display_number']} отмечено как пересланное!*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Не удалось обновить статус!")
        del context.user_data['waiting_for_forward_to']
        return
    
    elif 'waiting_for_reply_to' in context.user_data:
        search_id = context.user_data['waiting_for_reply_to']
        reply_text = update.message.text
        message_id, message_data = find_message_by_any_id(search_id)
        if message_data:
            user_id = message_data['user_id']
            reply_id = save_reply(message_id, YOUR_ID, reply_text, update.message.message_id)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"💬 *ОТВЕТ НА ВАШЕ АНОНИМНОЕ СООБЩЕНИЕ #{message_data['display_number']}*\n\n"
                         f"{escape_markdown(reply_text)}\n\n"
                         f"🕐 {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}",
                    parse_mode=ParseMode.MARKDOWN
                )
                mark_as_replied(message_id)
                await update.message.reply_text(
                    f"✅ *Ответ отправлен пользователю!*",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Ошибка отправки ответа: {e}")
                await update.message.reply_text(
                    f"❌ *Не удалось отправить ответ!*",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await update.message.reply_text(f"❌ Сообщение не найдено!")
        del context.user_data['waiting_for_reply_to']
        return
    
    elif update.message.reply_to_message:
        replied_message = update.message.reply_to_message
        message_id_match = re.search(r'ID: `([^`]+)`', replied_message.text or "")
        if message_id_match:
            search_id = message_id_match.group(1)
            message_id, message_data = find_message_by_any_id(search_id)
            if message_data:
                reply_text = update.message.text
                user_id = message_data['user_id']
                save_reply(message_id, YOUR_ID, reply_text, update.message.message_id)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"💬 *ОТВЕТ НА ВАШЕ АНОНИМНОЕ СООБЩЕНИЕ #{message_data['display_number']}*\n\n"
                             f"{escape_markdown(reply_text)}\n\n"
                             f"🕐 {datetime.datetime.now().strftime('%H:%M | %d.%m.%Y')}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    mark_as_replied(message_id)
                    await update.message.reply_text(
                        f"✅ *Ответ отправлен пользователю через реплай!*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки ответа: {e}")
                    await update.message.reply_text(
                        f"❌ *Не удалось отправить ответ!*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                return

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    is_admin = user.id == YOUR_ID
    if is_admin:
        welcome_text = (
            f'🛡️ *АНОНИМНЫЙ ЯЩИК - АДМИН ПАНЕЛЬ*\n\n'
            f'✨ *СИСТЕМА РАБОТАЕТ КОРРЕКТНО!*\n'
            f'✅ База данных загружена: {len(messages_db)} сообщений\n'
            f'✅ Ответов в базе: {len(replies_db)}\n'
        )
    else:
        welcome_text = (
            f'🕶️ *АНОНИМНЫЙ ЯЩИК*\n\n'
            f'✨ *ВСЕ ФУНКЦИИ РАБОТАЮТ:*\n'
            f'• 💬 Админ может отвечать вам!\n'
            f'• 🔒 Полная анонимность\n'
            f'• 📨 Ответы приходят приватно\n\n'
            f'📝 *Напишите что-нибудь чтобы начать!*'
        )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    is_admin = user.id == YOUR_ID
    if is_admin:
        help_text = (
            '🛡️ *ПОМОЩЬ ДЛЯ АДМИНА*\n\n'
            '🔹 *КНОПКИ ПОД СООБЩЕНИЯМИ:*\n'
            '✅ *Отметить пересланным*\n'
            '💬 *Ответить*\n'
            '📋 *Статус*\n'
            '🗑️ *Удалить*\n'
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
        )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats_text = (
        f'📊 *СТАТИСТИКА БОТА*\n\n'
        f'📨 *СООБЩЕНИЯ:*\n'
        f'• Всего: *{stats["total_messages"]}*\n'
        f'• Сегодня: *{stats["today_messages"]}*\n'
        f'✅ Переслано: *{stats["forwarded"]}*\n'
        f'💬 Отвечено: *{stats["replied"]}*\n\n'
        f'💾 *БАЗА ДАННЫХ:*\n'
        f'• Сообщений: *{len(messages_db)}*\n'
        f'• Ответов: *{len(replies_db)}*'
    )
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def dbinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != YOUR_ID:
        await update.message.reply_text("❌ Эта команда только для админа!")
        return
    db_info = (
        f'🗄️ *ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ*\n\n'
        f'📊 *СТАТИСТИКА:*\n'
        f'• Всего сообщений: *{len(messages_db)}*\n'
        f'• Всего ответов: *{len(replies_db)}*\n'
        f'• Счетчик сообщений: *{message_counter}*'
    )
    await update.message.reply_text(db_info, parse_mode=ParseMode.MARKDOWN)

async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    joke = random.choice(JOKES)
    response = f"😂 *АНЕКДОТ #{random.randint(1, 100)}*\n\n{joke}"
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    fact = random.choice(FACTS)
    await update.message.reply_text(f"📚 *ФАКТ:* {fact}", parse_mode=ParseMode.MARKDOWN)

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    quotes = [
        "«Анонимность — последнее прибежище честности»",
        "«Сказать правду анонимно — значит быть вдвое честнее»",
    ]
    quote = random.choice(quotes)
    await update.message.reply_text(f"💭 *ЦИТАТА ДНЯ:*\n\n{quote}", parse_mode=ParseMode.MARKDOWN)

async def secret_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    secrets = [
        "🤫 *Секрет 1:* Админ иногда читает сообщения с попкорном 🍿",
        "🔮 *Секрет 2:* Каждое 10-е сообщение получает +100% анонимности",
    ]
    secret = random.choice(secrets)
    response = f"🔐 *СЕКРЕТНАЯ ИНФОРМАЦИЯ*\n\n{secret}"
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu_text = (
        '📋 *ВСЕ КОМАНДЫ АНОНИМКИ*\n\n'
        '🎯 *ОСНОВНЫЕ:*\n'
        '/start — Начало работы\n'
        '/help — Помощь\n'
        '/stats — Статистика\n\n'
        '😂 *РАЗВЛЕЧЕНИЯ:*\n'
        '/joke — Анекдоты\n'
        '/fact — Факты\n'
        '/quote — Цитаты\n'
        '/secret — Секреты\n\n'
        '🛡️ *АДМИН:*\n'
        '/admin — Панель админа\n'
        '/dbinfo — Информация о базе'
    )
    await update.message.reply_text(menu_text, parse_mode=ParseMode.MARKDOWN)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id == YOUR_ID:
        admin_text = (
            f'🛡️ *ПАНЕЛЬ АДМИНИСТРАТОРА*\n\n'
            f'📊 *СТАТИСТИКА:*\n'
            f'• Сообщений в базе: *{len(messages_db)}*\n'
            f'• Ответов в базе: *{len(replies_db)}*\n'
            f'• Последнее сообщение: #{message_counter}\n\n'
            f'✅ *КНОПКИ РАБОТАЮТ КОРРЕКТНО!*'
        )
        await update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Доступ запрещен.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    now = time.time()
    user_last_msg = context.user_data.get('last_message_time', 0)
    if now - user_last_msg < 3:
        await update.message.reply_text("⏳ Слишком часто! Подождите 3 секунды.")
        return
    context.user_data['last_message_time'] = now
    
    if user_id == YOUR_ID:
        await handle_admin_reply(update, context)
        return
    
    try:
        media_type, _, _, display_num, message_id, _ = await send_with_buttons(update, context, YOUR_ID)
        response = (
            f"✅ *{media_type} отправлен!*\n"
            f"🔢 Номер: #{display_num}\n"
            f"🔐 Статус: Доставлено анонимно\n\n"
            f"💡 *Теперь админ может ответить вам!*"
        )
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ *Упс, ошибка!* Попробуй еще раз.", parse_mode=ParseMode.MARKDOWN)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f'Ошибка бота: {context.error}')

def main() -> None:
    logger.info("🚀 ЗАПУСКАЮ БОТА")
    logger.info(f"👑 Админ ID: {YOUR_ID}")
    
    try:
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CallbackQueryHandler(button_handler))
        
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
            ('dbinfo', dbinfo_command),
        ]
        for cmd_name, cmd_func in commands:
            app.add_handler(CommandHandler(cmd_name, cmd_func))
        
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)
        
        logger.info("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
