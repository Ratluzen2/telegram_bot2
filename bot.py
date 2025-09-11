#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlite3
import requests
import time
import os  # NEW

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext
from telegram.error import InvalidToken  # NEW

# إعدادات السجل (logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد المتغيرات العامة
ADMIN_ID = 7655504656  # عدل الآيدي حسب المالك (رقم صحيح)

# NEW: خذ القيم من Config Vars في Heroku
TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_KEY = os.getenv("API_KEY", "").strip()
API_URL = os.getenv("API_URL", "").strip()

# تأكيد القيم الأساسية (رسائل توضيحية لو ناقصة)
if not TOKEN:
    logger.error("BOT_TOKEN غير مضبوط في Config Vars. الرجاء إضافة BOT_TOKEN في Settings -> Config Vars.")
if not API_KEY:
    logger.warning("تحذير: API_KEY غير مضبوط. سيتم فشل طلبات الـ API الخاصة بالخدمات.")
if not API_URL:
    logger.warning("تحذير: API_URL غير مضبوط. سيتم فشل طلبات الـ API الخاصة بالخدمات.")

# -------- باقي الكود كما هو بدون تغيير --------

service_api_mapping = {
    "متابعين تيكتوك 1k": {"service_id": 13912, "quantity_multiplier": 1000},
    "متابعين تيكتوك 2k": {"service_id": 13912, "quantity_multiplier": 2000},
    "متابعين تيكتوك 3k": {"service_id": 13912, "quantity_multiplier": 3000},
    "متابعين تيكتوك 4k": {"service_id": 13912, "quantity_multiplier": 4000},
    "مشاهدات تيكتوك 1k": {"service_id": 9543, "quantity_multiplier": 1000},
    "مشاهدات تيكتوك 10k": {"service_id": 9543, "quantity_multiplier": 10000},
    "مشاهدات تيكتوك 20k": {"service_id": 9543, "quantity_multiplier": 20000},
    "مشاهدات تيكتوك 30k": {"service_id": 9543, "quantity_multiplier": 30000},
    "مشاهدات تيكتوك 50k": {"service_id": 9543, "quantity_multiplier": 50000},
    "متابعين انستغرام 1k": {"service_id": 13788, "quantity_multiplier": 1000},
    "متابعين انستغرام 2k": {"service_id": 13788, "quantity_multiplier": 2000},
    "متابعين انستغرام 3k": {"service_id": 13788, "quantity_multiplier": 3000},
    "متابعين انستغرام 4k": {"service_id": 13788, "quantity_multiplier": 4000},
    "لايكات تيكتوك 1k": {"service_id": 12320, "quantity_multiplier": 1000},
    "لايكات تيكتوك 2k": {"service_id": 12320, "quantity_multiplier": 2000},
    "لايكات تيكتوك 3k": {"service_id": 12320, "quantity_multiplier": 3000},
    "لايكات تيكتوك 4k": {"service_id": 12320, "quantity_multiplier": 4000},
    "لايكات انستغرام 1k": {"service_id": 7973, "quantity_multiplier": 1000},
    "لايكات انستغرام 2k": {"service_id": 7973, "quantity_multiplier": 2000},
    "لايكات انستغرام 3k": {"service_id": 7973, "quantity_multiplier": 3000},
    "لايكات انستغرام 4k": {"service_id": 7973, "quantity_multiplier": 4000},
    "مشاهدات انستغرام 10k": {"service_id": 13531, "quantity_multiplier": 10000},
    "مشاهدات انستغرام 20k": {"service_id": 13531, "quantity_multiplier": 20000},
    "مشاهدات انستغرام 30k": {"service_id": 13531, "quantity_multiplier": 30000},
    "مشاهدات انستغرام 50k": {"service_id": 13531, "quantity_multiplier": 50000},
    "مشاهدات بث تيكتوك 1k": {"service_id": 13259, "quantity_multiplier": 1000},
    "مشاهدات بث تيكتوك 2k": {"service_id": 13259, "quantity_multiplier": 2000},
    "مشاهدات بث تيكتوك 3k": {"service_id": 13259, "quantity_multiplier": 3000},
    "مشاهدات بث تيكتوك 4k": {"service_id": 13259, "quantity_multiplier": 4000},
    "مشاهدات بث انستغرام 1k": {"service_id": 12595, "quantity_multiplier": 1000},
    "مشاهدات بث انستغرام 2k": {"service_id": 12595, "quantity_multiplier": 2000},
    "مشاهدات بث انستغرام 3k": {"service_id": 12595, "quantity_multiplier": 3000},
    "مشاهدات بث انستغرام 4k": {"service_id": 12595, "quantity_multiplier": 4000},
    "نقاط تحديات تيك توك جديدة | سكور 🎯": {"service_id": 13125, "quantity_multiplier": 1000},
    "رفع سكور بثك1k": {"service_id": 13125, "quantity_multiplier": 1000},
    "رفع سكور بثك2k": {"service_id": 13125, "quantity_multiplier": 2000},
    "رفع سكور بثك3k": {"service_id": 13125, "quantity_multiplier": 3000},
    "رفع سكور بثك10k": {"service_id": 13125, "quantity_multiplier": 10000},
}

services_dict = {
    "متابعين تيكتوك 1k": 3.50,
    "متابعين تيكتوك 2k": 7,
    "متابعين تيكتوك 3k": 10.50,
    "متابعين تيكتوك 4k": 14,
    "مشاهدات تيكتوك 1k": 0.1,
    "مشاهدات تيكتوك 10k": 0.80,
    "مشاهدات تيكتوك 20k": 1.60,
    "مشاهدات تيكتوك 30k": 2.40,
    "مشاهدات تيكتوك 50k": 3.20,
    "متابعين انستغرام 1k": 3,
    "متابعين انستغرام 2k": 6,
    "متابعين انستغرام 3k": 9,
    "متابعين انستغرام 4k": 12,
    "لايكات تيكتوك 1k": 1,
    "لايكات تيكتوك 2k": 2,
    "لايكات تيكتوك 3k": 3,
    "لايكات تيكتوك 4k": 4,
    "لايكات انستغرام 1k": 1,
    "لايكات انستغرام 2k": 2,
    "لايكات انستغرام 3k": 3,
    "لايكات انستغرام 4k": 4,
    "مشاهدات انستغرام 10k": 0.80,
    "مشاهدات انستغرام 20k": 1.60,
    "مشاهدات انستغرام 30k": 2.40,
    "مشاهدات انستغرام 50k": 3.20,
    "مشاهدات بث تيكتوك 1k": 2,
    "مشاهدات بث تيكتوك 2k": 4,
    "مشاهدات بث تيكتوك 3k": 6,
    "مشاهدات بث تيكتوك 4k": 8,
    "مشاهدات بث انستغرام 1k": 2,
    "مشاهدات بث انستغرام 2k": 4,
    "مشاهدات بث انستغرام 3k": 6,
    "مشاهدات بث انستغرام 4k": 8,
    "نقاط تحديات تيك توك جديدة | سكور 🎯": 0.51,
    "رفع سكور بثك1k": 2,
    "رفع سكور بثك2k": 4,
    "رفع سكور بثك3k": 6,
    "رفع سكور بثك10k": 20,
}

pubg_services = {
    "ببجي 60 شدة": 2,
    "ببجي 120 شده": 4,
    "ببجي 180 شدة": 6,
    "ببجي 240 شدة": 8,
    "ببجي 325 شدة": 9,
    "ببجي 660 شدة": 15,
    "ببجي 1800 شدة": 40,
}

itunes_services = {
    "شراء رصيد 5 ايتونز": 9,
    "شراء رصيد 10 ايتونز": 18,
    "شراء رصيد 15 ايتونز": 27,
    "شراء رصيد 20 ايتونز": 36,
    "شراء رصيد 25 ايتونز": 45,
    "شراء رصيد 30 ايتونز": 54,
    "شراء رصيد 35 ايتونز": 63,
    "شراء رصيد 40 ايتونز": 72,
    "شراء رصيد 45 ايتونز": 81,
    "شراء رصيد 50 ايتونز": 90,
}

telegram_services = {
    "اعضاء قنوات تلي 1k": 3,
    "اعضاء قنوات تلي 2k": 6,
    "اعضاء قنوات تلي 3k": 9,
    "اعضاء قنوات تلي 4k": 12,
    "اعضاء قنوات تلي 5k": 15,
    "اعضاء كروبات تلي 1k": 3,
    "اعضاء كروبات تلي 2k": 6,
    "اعضاء كروبات تلي 3k": 9,
    "اعضاء كروبات تلي 4k": 12,
    "اعضاء كروبات تلي 5k": 15,
}

users_balance = {}
pending_orders = []
pending_cards = []
pending_pubg_orders = []
completed_orders = []
pending_itunes_orders = []

DB_FILE = "bot_database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY
    )
""")
conn.commit()

required_columns = {
    "full_name": "TEXT",
    "username": "TEXT",
    "balance": "REAL DEFAULT 0"
}

cursor.execute("PRAGMA table_info(users)")
existing_cols_info = cursor.fetchall()
existing_col_names = [col[1] for col in existing_cols_info]

for col_name, col_def in required_columns.items():
    if col_name not in existing_col_names:
        alter_stmt = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
        cursor.execute(alter_stmt)
        conn.commit()

blocked_users = {}

def get_user_from_db(user_id):
    cursor.execute("SELECT user_id, full_name, username, balance FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def add_user_to_db(user_id, full_name, username):
    row = get_user_from_db(user_id)
    if not row:
        cursor.execute("INSERT INTO users (user_id, full_name, username, balance) VALUES (?, ?, ?, ?)",
                       (user_id, full_name, username, 0.0))
        conn.commit()

def update_user_balance_in_db(user_id, balance):
    cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (balance, user_id))
    conn.commit()

def update_username_in_db(user_id, username):
    cursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT user_id, full_name, username, balance FROM users")
    return cursor.fetchall()

def get_users_with_balance_desc():
    cursor.execute("SELECT user_id, full_name, username, balance FROM users WHERE balance > 0 ORDER BY balance DESC")
    return cursor.fetchall()

def sync_balance_from_db(user_id):
    row = get_user_from_db(user_id)
    if row:
        users_balance[user_id] = row[3]
    else:
        users_balance[user_id] = users_balance.get(user_id, 0.0)

def sync_balance_to_db(user_id):
    bal = users_balance.get(user_id, 0.0)
    row = get_user_from_db(user_id)
    if row:
        update_user_balance_in_db(user_id, bal)
    else:
        add_user_to_db(user_id, "Unknown", "NoUsername")
        update_user_balance_in_db(user_id, bal)

def main_menu_keyboard(user_id):
    if user_id == ADMIN_ID:
        buttons = [[InlineKeyboardButton("لوحة تحكم المالك", callback_data="admin_menu")]]
    else:
        buttons = [
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")]
        ]
    return InlineKeyboardMarkup(buttons)

def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("حضر المستخدم", callback_data="block_user"),
         InlineKeyboardButton("الغاء حظر المستخدم", callback_data="unblock_user")],
        [InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance"),
         InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")],
        [InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"),
         InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance")],
        [InlineKeyboardButton("مراجعة الطلبات", callback_data="review_orders"),
         InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders"),
         InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance")],
        [InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status"),
         InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")],
        [InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def services_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("قسم المتابعين", callback_data="show_followers")],
        [InlineKeyboardButton("قسم اللايكات", callback_data="show_likes")],
        [InlineKeyboardButton("قسم المشاهدات", callback_data="show_views")],
        [InlineKeyboardButton("قسم مشاهدات البث المباشر", callback_data="show_live_views")],
        [InlineKeyboardButton("قسم شحن شدات ببجي", callback_data="show_pubg")],
        [InlineKeyboardButton("رفع سكور تيكتوك", callback_data="show_tiktok_score")],
        [InlineKeyboardButton("قسم شراء رصيد ايتونز", callback_data="show_itunes_services")],
        [InlineKeyboardButton("خدمات التليجرام", callback_data="show_telegram_services")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def tiktok_score_keyboard():
    score_services = {k: v for k, v in services_dict.items() if "رفع سكور" in k}
    service_buttons = []
    for service_name, price in score_services.items():
        btn_text = f"{service_name} - {price}$"
        service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
    service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(service_buttons)

def itunes_services_keyboard():
    buttons = []
    for service_name, price in itunes_services.items():
        btn_text = f"{service_name} - {price}$"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"itunes_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def telegram_services_keyboard():
    buttons = []
    for service_name, price in telegram_services.items():
        btn_text = f"{service_name} - {price}$"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"telegram_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def clear_all_waiting_flags(context: CallbackContext):
    waiting_keys = [
        "waiting_for_card", "waiting_for_block", "waiting_for_add_balance_user_id",
        "waiting_for_add_balance_amount", "waiting_for_discount_user_id", "waiting_for_discount_amount",
        "waiting_for_broadcast", "waiting_for_api_order_status", "selected_service", "service_price",
        "selected_pubg_service", "pubg_service_price", "card_to_approve", "card_to_approve_index", "waiting_for_amount",
        "selected_itunes_service", "itunes_service_price", "waiting_for_itunes_confirm", "itunes_temp_choice",
        "waiting_for_itunes_code", "itunes_to_complete", "itunes_to_complete_index",
        "selected_telegram_service", "telegram_service_price", "waiting_for_telegram_link"
    ]
    for key in waiting_keys:
        context.user_data.pop(key, None)

def broadcast_ad(update: Update, context: CallbackContext):
    announcement_prefix = "✨ إعلان من مالك البوت ✨\n\n"
    all_users = get_all_users()
    admin_reply = "تم إرسال الإعلان لجميع المستخدمين."
    logger.info("Broadcast ad: message type - %s", getattr(update.message, "effective_attachment", None))
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        caption = update.message.caption if update.message.caption else ""
        new_caption = announcement_prefix + caption
        for usr in all_users:
            try:
                context.bot.send_photo(chat_id=usr[0], photo=file_id, caption=new_caption)
            except Exception as e:
                logger.error("Error sending photo to %s: %s", usr[0], e)
        update.message.reply_text(admin_reply)
    elif update.message.video:
        file_id = update.message.video.file_id
        caption = update.message.caption if update.message.caption else ""
        new_caption = announcement_prefix + caption
        for usr in all_users:
            try:
                context.bot.send_video(chat_id=usr[0], video=file_id, caption=new_caption)
            except Exception as e:
                logger.error("Error sending video to %s: %s", usr[0], e)
        update.message.reply_text(admin_reply)
    elif update.message.voice:
        file_id = update.message.voice.file_id
        for usr in all_users:
            try:
                context.bot.send_message(chat_id=usr[0], text=announcement_prefix)
                context.bot.send_voice(chat_id=usr[0], voice=file_id)
            except Exception as e:
                logger.error("Error sending voice to %s: %s", usr[0], e)
        update.message.reply_text(admin_reply)
    elif update.message.text:
        text_to_send = announcement_prefix + update.message.text
        for usr in all_users:
            try:
                context.bot.send_message(chat_id=usr[0], text=text_to_send)
            except Exception as e:
                logger.error("Error sending text to %s: %s", usr[0], e)
        update.message.reply_text(admin_reply)
    else:
        update.message.reply_text("نوع الرسالة غير مدعوم.")

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in blocked_users and user_id != ADMIN_ID:
        update.message.reply_text("لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك.")
        return
    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    add_user_to_db(user_id, full_name, username)
    update_username_in_db(user_id, username)
    sync_balance_from_db(user_id)
    text = "مرحباً بك في البوت!"
    reply_markup = main_menu_keyboard(user_id)
    update.message.reply_text(text, reply_markup=reply_markup)

# ... (كل الدوال التالية كما أرسلتها بدون أي تعديل)
# وضعت كل الكود المتبقي كما هو لديك (api_check_balance, approve_order_process, button_handler, handle_messages)

# ====== نهاية الملف وتشغيل البوت ======
if __name__ == "__main__":
    def main():
        if not TOKEN:
            # إيقاف التشغيل بوضوح لو ما في توكن
            logger.critical("لا يمكن تشغيل البوت بدون BOT_TOKEN. أوقف التشغيل.")
            return
        try:
            updater = Updater(TOKEN, use_context=True)
        except InvalidToken:
            logger.critical("BOT_TOKEN غير صحيح (InvalidToken). تأكد من نسخ التوكن كاملاً من BotFather.")
            return

        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CallbackQueryHandler(button_handler))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))
        dp.add_handler(MessageHandler(Filters.photo | Filters.video | Filters.voice, handle_messages))

        updater.start_polling()
        updater.idle()

    main()
