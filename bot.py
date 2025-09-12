#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlite3
import requests
import time  # لإضافة طابع زمني للطلبات المكتملة

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

# إعدادات السجل (logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد المتغيرات العامة (اتركها كما هي لديك)
ADMIN_ID = 7655504656  # عدل الآيدي حسب المالك
TOKEN = "8138615524:AAFr6m5Z4_gY0k7pdg7teD9nM8ReDC-KQKU"  # ضع توكن البوت الخاص بك هنا
API_KEY = "3e4f5503764fa06793da9a76d24d65a4"  # ضع API KEY الخاص بك هنا
API_URL = "https://kd1s.com/api/v2"  # تأكد من صحة رابط API

# تعريف القواميس الخاصة بالخدمات
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

# المتغيرات الخاصة بالطلبات والرصيد
users_balance = {}
pending_orders = []         # الطلبات المعلقة (غير الـ API)
pending_cards = []          # الكروت المعلقة
pending_pubg_orders = []    # طلبات شدات ببجي المعلقة
completed_orders = []       # الطلبات المكتملة (مع إضافة الطابع الزمني)
pending_itunes_orders = []  # طلبات شحن الايتونز المعلقة

# إعداد قاعدة بيانات SQLite (تبقى كما الأصل)
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

# === جدول المشرفين (إضافة جديدة بدون المساس بباقي الجداول) ===
cursor.execute("""
    CREATE TABLE IF NOT EXISTS moderators(
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        username TEXT
    )
""")
conn.commit()

# قاموس المستخدمين المحظورين
blocked_users = {}

# ====== دوال مساعدة قاعدة البيانات والمستخدمين ======
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

# ====== إدارة المشرفين ======
def is_moderator(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    cursor.execute("SELECT 1 FROM moderators WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def add_moderator_db(user_id: int, full_name: str, username: str):
    cursor.execute("INSERT OR IGNORE INTO moderators (user_id, full_name, username) VALUES (?, ?, ?)",
                   (user_id, full_name, username))
    conn.commit()

def remove_moderator_db(user_id: int):
    cursor.execute("DELETE FROM moderators WHERE user_id=?", (user_id,))
    conn.commit()

def list_moderators_db():
    cursor.execute("SELECT user_id, full_name, username FROM moderators ORDER BY user_id")
    return cursor.fetchall()

# ====== خصومات المشرفين ======
def service_category(service_name: str) -> str:
    if "متابعين" in service_name:
        return "followers"
    if "لايكات" in service_name:
        return "likes"
    if "مشاهدات بث" in service_name:
        return "live_views"
    if "مشاهدات تيكتوك" in service_name or "مشاهدات انستغرام" in service_name:
        return "views"
    if "سكور" in service_name:
        return "tiktok_score"
    if service_name in itunes_services:
        return "itunes"
    if service_name in pubg_services:
        return "pubg"
    if service_name in telegram_services:
        return "telegram"
    return "other"

def moderator_price(user_id: int, service_name: str, base_price: float) -> float:
    # المالك: لا حاجة لخصم (يبقى السعر كما هو)
    if user_id == ADMIN_ID:
        return base_price
    # المشرف فقط يحصل على خصم
    if not is_moderator(user_id):
        return base_price
    cat = service_category(service_name)
    if cat in {"followers", "views", "live_views", "likes", "tiktok_score", "telegram"}:
        return round(base_price * 0.8, 4)
    if cat in {"itunes", "pubg"}:
        return round(base_price * 0.9, 4)
    return base_price

# لوحات المفاتيح (Keyboards)
def main_menu_keyboard(user_id):
    buttons = []
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("لوحة تحكم المالك", callback_data="admin_menu")])
    if is_moderator(user_id) and user_id != ADMIN_ID:
        buttons.append([InlineKeyboardButton("لوحة تحكم المشرف", callback_data="mod_menu")])
    buttons.extend([
        [InlineKeyboardButton("الخدمات", callback_data="show_services")],
        [InlineKeyboardButton("رصيدي", callback_data="show_balance")]
    ])
    return InlineKeyboardMarkup(buttons)

def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("حضر المستخدم", callback_data="block_user"),
         InlineKeyboardButton("الغاء حظر المستخدم", callback_data="unblock_user")],
        [InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance"),
         InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")],
        [InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"),
         InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance")],
        [InlineKeyboardButton("مراجعة الطلبات المعلقة", callback_data="admin_review_pending"),
         InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders"),
         InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance")],
        [InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status"),
         InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")],
        [InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")],
        [InlineKeyboardButton("ادارة المشرفين", callback_data="manage_mods")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def moderator_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("مراجعة الطلبات المعلقة", callback_data="mod_review_pending")],
        [InlineKeyboardButton("احصائيات الطلبات", callback_data="mod_stats")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def manage_mods_keyboard():
    buttons = [
        [InlineKeyboardButton("إضافة مشرف", callback_data="add_mod")],
        [InlineKeyboardButton("حذف مشرف", callback_data="del_mod")],
        [InlineKeyboardButton("عرض المشرفين", callback_data="list_mods")],
        [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
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

def tiktok_score_keyboard(user_id=None):
    score_services = {k: v for k, v in services_dict.items() if "رفع سكور" in k or "سكور" in k}
    service_buttons = []
    for service_name, price in score_services.items():
        p = moderator_price(user_id, service_name, price) if user_id else price
        btn_text = f"{service_name} - {p}$"
        service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
    service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(service_buttons)

def itunes_services_keyboard(user_id=None):
    buttons = []
    for service_name, price in itunes_services.items():
        p = moderator_price(user_id, service_name, price) if user_id else price
        btn_text = f"{service_name} - {p}$"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"itunes_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def telegram_services_keyboard(user_id=None):
    buttons = []
    for service_name, price in telegram_services.items():
        p = moderator_price(user_id, service_name, price) if user_id else price
        btn_text = f"{service_name} - {p}$"
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
        "selected_telegram_service", "telegram_service_price", "waiting_for_telegram_link",
        "waiting_for_add_mod", "waiting_for_del_mod"
    ]
    for key in waiting_keys:
        context.user_data.pop(key, None)

# النظام الجديد للإعلان: يدعم الصور، الفيديو، التسجيل الصوتي والنص
def broadcast_ad(update: Update, context: CallbackContext):
    announcement_prefix = "✨ إعلان من مالك البوت ✨\n\n"
    all_users = get_all_users()
    admin_reply = "تم إرسال الإعلان لجميع المستخدمين."
    try:
        # قد لا تكون الخاصية موجودة في بعض الإصدارات
        logger.info("Broadcast ad")
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
    except Exception as e:
        logger.exception("broadcast_ad error: %s", e)
        update.message.reply_text("حدث خطأ أثناء الإرسال.")

# دالة البداية (start)
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

def api_check_balance(update: Update, context: CallbackContext):
    params = {'key': API_KEY, 'action': 'balance'}
    try:
        response = requests.post(API_URL, data=params, timeout=25)
        balance_info = response.json()
        if "balance" in balance_info:
            text_msg = f"رصيد حسابك في API: {balance_info['balance']}$"
        else:
            text_msg = f"حدث خطأ في جلب الرصيد من API: {balance_info.get('error', 'غير معروف')}"
    except Exception as e:
        logger.error("api_check_balance error: %s", e)
        text_msg = "فشل الاتصال بالـ API."
    if update.callback_query:
        query = update.callback_query
        btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
    else:
        update.message.reply_text(text_msg)

def approve_order_process(order_index: int, context: CallbackContext, query):
    try:
        order_info = pending_orders.pop(order_index)
    except Exception:
        query.answer("طلب غير موجود.", show_alert=True)
        return
    if order_info['service'] in service_api_mapping:
        mapping = service_api_mapping[order_info['service']]
        quantity = mapping['quantity_multiplier']
        params = {
            'key': API_KEY,
            'action': 'add',
            'service': mapping['service_id'],
            'link': order_info['link'],
            'quantity': quantity
        }
        try:
            response = requests.post(API_URL, data=params, timeout=25)
            api_response = response.json()
        except Exception as e:
            logger.error("API add error: %s", e)
            api_response = {"error": "فشل استدعاء API"}

        if "order" in api_response:
            order_info["order_number"] = api_response["order"]
            order_info["service_number"] = mapping["service_id"]
            order_info["refunded"] = False
            order_info["completed_at"] = time.time()
            completed_orders.append(order_info)
            context.bot.send_message(
                chat_id=order_info['user_id'],
                text=f"تم استلام طلبك وسوف يتم تنفيذه قريباً\nرقم طلبك ({api_response['order']})"
            )
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_review_pending")]]
            query.edit_message_text("تم تنفيذ الطلب عبر API وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))
        else:
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(
                chat_id=order_info['user_id'],
                text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك."
            )
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_review_pending")]]
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
    else:
        order_info["order_number"] = "N/A"
        order_info["service_number"] = "N/A"
        order_info["refunded"] = False
        order_info["completed_at"] = time.time()
        completed_orders.append(order_info)
        context.bot.send_message(chat_id=order_info['user_id'], text="تم إكمال طلبك بنجاح.")
        btns = [[InlineKeyboardButton("رجوع", callback_data="admin_review_pending")]]
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    clear_all_waiting_flags(context)

    if user_id in blocked_users and user_id != ADMIN_ID:
        query.answer("لقد تم حضرك من استخدام البوت 🤣.", show_alert=True)
        return

    # عامة
    if data == "back_main":
        query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return
    if data == "show_services":
        query.edit_message_text("اختر القسم:", reply_markup=services_menu_keyboard())
        return
    if data == "show_tiktok_score":
        query.edit_message_text("اختر خدمة رفع سكور تيكتوك المطلوبة:", reply_markup=tiktok_score_keyboard(user_id))
        return

    # لوحات
    if data == "admin_menu":
        if user_id == ADMIN_ID:
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return
    if data == "mod_menu" and is_moderator(user_id) and user_id != ADMIN_ID:
        query.edit_message_text("لوحة تحكم المشرف:", reply_markup=moderator_menu_keyboard())
        return

    # ===== أوامر المالك =====
    if user_id == ADMIN_ID:
        if data == "block_user":
            query.edit_message_text("أرسل اليوزرنيم أو الآيدي للمستخدم الذي تريد حضره:")
            context.user_data["waiting_for_block"] = True
            return
        if data == "unblock_user":
            if not blocked_users:
                query.edit_message_text("لا يوجد مستخدمين محظورين.")
            else:
                text = "قائمة المستخدمين المحظورين:\n"
                keyboard = []
                for uid in blocked_users:
                    row = get_user_from_db(uid)
                    user_display = f"{row[1]} (@{row[2]})" if row else f"User {uid}"
                    text += f"{user_display} (ID: {uid})\n"
                    keyboard.append([InlineKeyboardButton(f"إلغاء حظر {user_display}", callback_data=f"unblock_{uid}")])
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        if data.startswith("unblock_"):
            try:
                target_id = int(data.split("_")[1])
            except Exception:
                query.edit_message_text("حدث خطأ في بيانات المستخدم.")
                return
            blocked_users.pop(target_id, None)
            query.edit_message_text("تم إلغاء حظر المستخدم بنجاح.")
            return
        if data == "admin_add_balance":
            query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد إضافة الرصيد له:")
            context.user_data["waiting_for_add_balance_user_id"] = True
            return
        if data == "admin_discount":
            query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد خصم الرصيد منه:")
            context.user_data["waiting_for_discount_user_id"] = True
            return
        if data == "admin_announce":
            query.edit_message_text("أرسل الآن الرسالة أو الوسائط (صورة/فيديو/تسجيل صوتي/نص) لإعلان البوت لجميع المستخدمين:")
            context.user_data["waiting_for_broadcast"] = True
            return
        if data == "admin_users_count":
            users = get_all_users()
            count_users = len(users)
            text_msg = f"عدد المستخدمين: {count_users}\n\n"
            for i, usr in enumerate(users, start=1):
                text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, أيدي: {usr[0]}\n"
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return
        if data == "admin_users_balance":
            users = get_users_with_balance_desc()
            if not users:
                text_msg = "لا يوجد مستخدمون لديهم رصيد > 0."
            else:
                text_msg = "مستخدمو البوت (رصيد > 0) - ترتيب تنازلي:\n\n"
                for i, usr in enumerate(users, start=1):
                    text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, الرصيد: {usr[3]}$, أيدي: {usr[0]}\n"
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        # مراجعة الطلبات المعلّقة (إضافة جديدة)
        if data == "admin_review_pending":
            if not pending_orders:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات معلقة حالياً.", reply_markup=InlineKeyboardMarkup(btns))
            else:
                text_msg = "الطلبات المعلقة:\n"
                buttons = []
                for idx, o in enumerate(pending_orders, 1):
                    text_msg += f"{idx}) {o['full_name']} - {o['service']} - {o['price']}$\n"
                    buttons.append([
                        InlineKeyboardButton(f"تنفيذ #{idx}", callback_data=f"approve_pending_{idx-1}"),
                        InlineKeyboardButton(f"رفض #{idx}", callback_data=f"reject_pending_{idx-1}")
                    ])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return
        if data.startswith("approve_pending_"):
            order_index = int(data.split("_")[-1])
            approve_order_process(order_index, context, query)
            return
        if data.startswith("reject_pending_"):
            order_index = int(data.split("_")[-1])
            try:
                order_info = pending_orders.pop(order_index)
            except Exception:
                query.answer("طلب غير موجود.", show_alert=True)
                return
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="تم رفض الطلب وتمت إعادة المبلغ لرصيدك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_review_pending")]]
            query.edit_message_text("تم رفض الطلب وإرجاع الرصيد.", reply_markup=InlineKeyboardMarkup(btns))
            return

        # الكارتات المعلقة
        if data == "pending_cards":
            if not pending_cards:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد كروت معلقة حالياً.", reply_markup=InlineKeyboardMarkup(btns))
            else:
                text_msg = "الكروت المعلقة:\n"
                buttons = []
                for idx, card in enumerate(pending_cards):
                    text_msg += f"{idx+1}) @{card['username']} - كارت معلق\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الكارت {idx+1}", callback_data=f"process_card_{idx}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return
        if data.startswith("process_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            text_msg = (
                f"تفاصيل الكارت رقم {card_index+1}:\n"
                f"- المعرف: {card_info['user_id']}\n"
                f"- الاسم: {card_info['full_name']}\n"
                f"- يوزر: @{card_info['username']}\n"
                f"- رقم الكارت: اضغط زر (إظهار الرقم) أدناه.\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("إظهار الرقم", callback_data=f"show_card_{card_index}")],
                [InlineKeyboardButton("قبول الكارت", callback_data=f"approve_card_{card_index}"),
                 InlineKeyboardButton("رفض الكارت", callback_data=f"reject_card_{card_index}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_cards")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
            return
        if data.startswith("show_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            query.message.reply_text(text=f"رقم الكارت:\n`{card_info['card_number']}`\n(اضغط مطولاً للنسخ)", parse_mode="Markdown")
            query.answer()
            return
        if data.startswith("approve_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]
            query.edit_message_text("أرسل الآن المبلغ المراد شحنه للمستخدم:", reply_markup=InlineKeyboardMarkup(btns))
            context.user_data["card_to_approve"] = card_info
            context.user_data["card_to_approve_index"] = card_index
            context.user_data["waiting_for_amount"] = True
            return
        if data.startswith("reject_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards.pop(card_index)
            context.bot.send_message(chat_id=card_info["user_id"], text="تم رفض الشحن لأن رقم الكارت غير صحيح.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]
            query.edit_message_text("تم رفض الكارت بنجاح.", reply_markup=InlineKeyboardMarkup(btns))
            return

        # شدات ببجي
        if data == "pending_pubg_orders":
            if not pending_pubg_orders:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات شدات ببجي معلقة حالياً.", reply_markup=InlineKeyboardMarkup(btns))
            else:
                text_msg = "طلبات شدات ببجي المعلقة:\n"
                buttons = []
                for idx, order in enumerate(pending_pubg_orders):
                    text_msg += f"{idx+1}) طلب من @{order['username']} - الخدمة: {order['service']}, الآيدي: {order['pubg_id']}\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الطلب رقم {idx+1}", callback_data=f"process_pubg_order_{idx}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return
        if data.startswith("process_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders[order_index]
            text_msg = (
                f"تفاصيل طلب شحن شدات ببجي رقم {order_index+1}:\n"
                f"- المعرف: {order_info['user_id']}\n"
                f"- الاسم: {order_info['full_name']}\n"
                f"- يوزر: @{order_info['username']}\n"
                f"- الخدمة: {order_info['service']}\n"
                f"- السعر: {order_info['price']}$\n"
                f"- الآيدي: {order_info['pubg_id']}\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("تم شحن الشدات", callback_data=f"approve_pubg_order_{order_index}"),
                 InlineKeyboardButton("تم الغاء شحن الشدات", callback_data=f"reject_pubg_order_{order_index}")],
                [InlineKeyboardButton("انتظار المستخدم", callback_data=f"user_wait_pubg_order_{order_index}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return
        if data.startswith("approve_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders.pop(order_index)
            context.bot.send_message(chat_id=order_info['user_id'], text="تم شحن شدات ببجي بنجاح.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]
            query.edit_message_text("تم شحن شدات ببجي وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))
            return
        if data.startswith("reject_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders.pop(order_index)
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ إلى حسابك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]
            query.edit_message_text("تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
            return
        if data.startswith("user_wait_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders[order_index]
            context.bot.send_message(chat_id=order_info['user_id'], text="سوف يتم تنفيذ طلبك قريبا")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
            return

        if data == "api_check_balance":
            api_check_balance(update, context)
            return
        if data == "api_order_status":
            query.edit_message_text("أدخل رقم الطلب للتحقق من حالته عبر API:")
            context.user_data["waiting_for_api_order_status"] = True
            return

        # ايتونز
        if data == "pending_itunes_orders":
            if not pending_itunes_orders:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات شحن ايتونز معلقة حالياً.", reply_markup=InlineKeyboardMarkup(btns))
            else:
                text_msg = "طلبات شحن الايتونز المعلقة:\n"
                buttons = []
                for idx, order in enumerate(pending_itunes_orders):
                    text_msg += f"{idx+1}) @{order['username']} - {order['service']} بسعر {order['price']}$\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الطلب رقم {idx+1}", callback_data=f"process_itunes_{idx}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return
        if data.startswith("process_itunes_"):
            itunes_index = int(data.split("_")[-1])
            itunes_order = pending_itunes_orders[itunes_index]
            text_msg = (
                f"تفاصيل طلب شحن ايتونز رقم {itunes_index+1}:\n"
                f"- المعرف: {itunes_order['user_id']}\n"
                f"- الاسم: {itunes_order['full_name']}\n"
                f"- يوزر: @{itunes_order['username']}\n"
                f"- الخدمة: {itunes_order['service']}\n"
                f"- السعر: {itunes_order['price']}$\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("انتظار المستخدم", callback_data=f"itunes_wait_{itunes_index}")],
                [InlineKeyboardButton("اكمال الطلب", callback_data=f"itunes_complete_{itunes_index}")],
                [InlineKeyboardButton("الغاء الطلب", callback_data=f"itunes_cancel_{itunes_index}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return
        if data.startswith("itunes_wait_"):
            itunes_index = int(data.split("_")[-1])
            itunes_order = pending_itunes_orders[itunes_index]
            context.bot.send_message(chat_id=itunes_order['user_id'], text="سوف يتم ارسال كود الهدايا قريبا")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
            return
        if data.startswith("itunes_complete_"):
            itunes_index = int(data.split("_")[-1])
            itunes_order = pending_itunes_orders[itunes_index]
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]
            query.edit_message_text("أرسل الآن كود الهدايا الايتونز:", reply_markup=InlineKeyboardMarkup(btns))
            context.user_data["itunes_to_complete"] = itunes_order
            context.user_data["itunes_to_complete_index"] = itunes_index
            context.user_data["waiting_for_itunes_code"] = True
            return
        if data.startswith("itunes_cancel_"):
            itunes_index = int(data.split("_")[-1])
            itunes_order = pending_itunes_orders.pop(itunes_index)
            users_balance[itunes_order['user_id']] += itunes_order['price']
            sync_balance_to_db(itunes_order['user_id'])
            context.bot.send_message(chat_id=itunes_order['user_id'], text="تم إلغاء طلب شحن الايتونز وإعادة المبلغ لرصيدك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]
            query.edit_message_text("تم إلغاء طلب شحن الايتونز وإعادة المبلغ للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
            return

        # إدارة المشرفين
        if data == "manage_mods":
            query.edit_message_text("إدارة المشرفين:", reply_markup=manage_mods_keyboard()); return
        if data == "add_mod":
            query.edit_message_text("أرسل الآن آيدي المستخدم أو اليوزرنيم لإضافته كمشرف:")
            context.user_data["waiting_for_add_mod"] = True; return
        if data == "del_mod":
            query.edit_message_text("أرسل الآن آيدي المستخدم أو اليوزرنيم لحذفه من المشرفين:")
            context.user_data["waiting_for_del_mod"] = True; return
        if data == "list_mods":
            mods = list_moderators_db()
            if not mods:
                query.edit_message_text("لا يوجد مشرفون حالياً.", reply_markup=manage_mods_keyboard()); return
            text_msg = f"عدد المشرفين: {len(mods)}\n\n"
            for i, (mid, mname, muser) in enumerate(mods, 1):
                text_msg += f"{i}) {mname} @{muser or ''} — ID: {mid}\n"
            query.edit_message_text(text_msg, reply_markup=manage_mods_keyboard()); return

    # ===== لوحة المشرف =====
    if is_moderator(user_id) and user_id != ADMIN_ID:
        if data == "mod_review_pending":
            if not pending_orders:
                query.edit_message_text("لا توجد طلبات معلقة حالياً.", reply_markup=moderator_menu_keyboard())
            else:
                text_msg = "الطلبات المعلقة:\n"
                keyboard = []
                for idx, o in enumerate(pending_orders, 1):
                    text_msg += f"{idx}) {o['full_name']} - {o['service']} - {o['price']}$\n"
                    keyboard.append([
                        InlineKeyboardButton(f"إشعار المالك #{idx}", callback_data=f"notify_admin_{idx-1}")
                    ])
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="mod_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        if data.startswith("notify_admin_"):
            order_index = int(data.split("_")[-1])
            if 0 <= order_index < len(pending_orders):
                o = pending_orders[order_index]
                context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔔 إشعار من مشرف\nطلب معلق يحتاج مراجعة:\n"
                         f"المستخدم: {o['full_name']} (@{o['username']})\nالخدمة: {o['service']}\nالسعر: {o['price']}$\nالرابط: {o['link']}"
                )
                query.answer("تم إشعار المالك.", show_alert=True)
            else:
                query.answer("طلب غير موجود.", show_alert=True)
            return
        if data == "mod_stats":
            stats_text = (
                f"الطلبات:\n"
                f"- المكتملة: {len(completed_orders)}\n"
                f"- المعلقة: {len(pending_orders) + len(pending_pubg_orders) + len(pending_itunes_orders) + len(pending_cards)}\n"
                f"- الجاريه: 0\n"
                f"- الملغية: 0\n"
            )
            query.edit_message_text(stats_text, reply_markup=moderator_menu_keyboard())
            return

    # ===== أقسام المستخدم =====
    if data == "show_followers":
        followers_services = {k: v for k, v in services_dict.items() if "متابعين" in k}
        service_buttons = []
        for service_name, price in followers_services.items():
            p = moderator_price(user_id, service_name, price)
            service_buttons.append([InlineKeyboardButton(f"{service_name} - {p}$", callback_data=f"service_{service_name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_likes":
        likes_services = {k: v for k, v in services_dict.items() if "لايكات" in k}
        service_buttons = []
        for service_name, price in likes_services.items():
            p = moderator_price(user_id, service_name, price)
            service_buttons.append([InlineKeyboardButton(f"{service_name} - {p}$", callback_data=f"service_{service_name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_views":
        views_services = {k: v for k, v in services_dict.items() if "مشاهدات تيكتوك" in k or "مشاهدات انستغرام" in k}
        service_buttons = []
        for service_name, price in views_services.items():
            p = moderator_price(user_id, service_name, price)
            service_buttons.append([InlineKeyboardButton(f"{service_name} - {p}$", callback_data=f"service_{service_name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_live_views":
        live_views_services = {k: v for k, v in services_dict.items() if "مشاهدات بث" في k if False else {}}
        live_views_services = {k: v for k, v in services_dict.items() if "مشاهدات بث" in k}
        service_buttons = []
        for service_name, price in live_views_services.items():
            p = moderator_price(user_id, service_name, price)
            service_buttons.append([InlineKeyboardButton(f"{service_name} - {p}$", callback_data=f"service_{service_name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_pubg":
        service_buttons = []
        for service_name, price in pubg_services.items():
            p = moderator_price(user_id, service_name, price)
            service_buttons.append([InlineKeyboardButton(f"{service_name} - {p}$", callback_data=f"pubg_service_{service_name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر خدمة شحن شدات ببجي:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data.startswith("pubg_service_"):
        service_name = data[len("pubg_service_"):]
        base_price = pubg_services.get(service_name, 0)
        price = moderator_price(user_id, service_name, base_price)
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="show_pubg")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_pubg_service"] = service_name
        context.user_data["pubg_service_price"] = price
        query.edit_message_text("ارسل الايدي الخاص بك:")
        return

    if data == "show_itunes_services":
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=itunes_services_keyboard(user_id))
        return

    if data.startswith("itunes_service_"):
        service_name = data[len("itunes_service_"):]
        base_price = itunes_services.get(service_name, 0)
        price = moderator_price(user_id, service_name, base_price)
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="show_itunes_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_itunes_service"] = service_name
        context.user_data["itunes_service_price"] = price
        query.edit_message_text(f"تم اختيار الخدمة: {service_name}\n\nارسل رقم 1 لتأكيد طلبك")
        context.user_data["waiting_for_itunes_confirm"] = True
        return

    if data == "show_telegram_services":
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=telegram_services_keyboard(user_id))
        return

    if data.startswith("telegram_service_"):
        service_name = data[len("telegram_service_"):]
        base_price = telegram_services.get(service_name, 0)
        price = moderator_price(user_id, service_name, base_price)
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="show_telegram_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_telegram_service"] = service_name
        context.user_data["telegram_service_price"] = price
        context.user_data["waiting_for_telegram_link"] = True
        note_text = (
            "الرجاء إرسال رابط دعوة انضمام وليس رابط القناة أو اسم المستخدم (مثل: https://t.me/+xxxx).\n\n"
            "خطوات إنشاء رابط الدعوة الخاص:\n"
            "1. ادخل إلى القناة.\n"
            "2. اختر خيار المشتركون.\n"
            "3. اضغط على الدعوة عبر رابط خاص.\n"
            "4. أنشئ رابط دعوة جديد."
        )
        query.edit_message_text(note_text)
        return

    if data == "show_balance":
        balance = users_balance.get(user_id, 0.0)
        buttons = [
            [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
            [InlineKeyboardButton("رجوع", callback_data="back_main")]
        ]
        query.edit_message_text(f"رصيدك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "charge_asiacell":
        context.user_data["waiting_for_card"] = True
        query.edit_message_text("أرسل رقم الكارت المكون من 14 رقم أو 16 رقم:")
        return

    # اختيار خدمة عامة
    if data.startswith("service_"):
        service_name = data[len("service_"):]
        base_price = services_dict.get(service_name)
        if base_price is None:
            query.edit_message_text("الخدمة غير موجودة.")
            return
        price = moderator_price(user_id, service_name, base_price)
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="show_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        if "انستغرام" in service_name:
            message_text = (
                "الرجاء إرسال رابط الخدمة الخاص بك\n"
                "🔴 تنبيه:\n"
                "يرجى إطفاء زر 'تميز للمراجعة' داخل حسابك الانستغرام قبل ارسال رابط الخدمه لضمان إكمال طلبك!"
            )
        elif "رفع سكور بث" in service_name or "سكور" in service_name:
            message_text = (
                "يرجى ارسال رابط البث الخاص بك\n"
                "🔴تنبيه: يرجى ارسال رابط البث وليس اليوزرنيم!!"
            )
        elif "تيكتوك" in service_name:
            message_text = (
                "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:\n"
                "🔴ملاحظة:ارسل الرابط وليس اليوزرنيم!"
            )
        else:
            message_text = "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:"
        context.user_data["selected_service"] = service_name
        context.user_data["service_price"] = price
        query.edit_message_text(message_text)
        return

# دالة استقبال الرسائل ومعالجتها
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if user_id in blocked_users and user_id != ADMIN_ID:
        update.message.reply_text("لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك.")
        return

    # إعلان المالك
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_broadcast"):
        broadcast_ad(update, context)
        return

    # حضر/إلغاء حضر
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_block"):
        target_input = text
        try:
            target_id = int(target_input)
        except ValueError:
            # البحث باليوزرنيم
            target_id = None
            for usr in get_all_users():
                if usr[2] and (usr[2].lower() == target_input.lower() or "@"+usr[2].lower() == target_input.lower()):
                    target_id = usr[0]
                    break
        if not target_id:
            update.message.reply_text("المستخدم غير موجود.")
            return
        blocked_users[target_id] = True
        update.message.reply_text("تم حضر المستخدم.")
        return

    # إضافة الرصيد (المالك)
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_add_balance_user_id"):
        target_input = text
        try:
            target_id = int(target_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == target_input.lower():
                    found_user = usr
                    break
            if not found_user:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات.")
                return
            target_id = found_user[0]
        context.user_data["admin_target_id"] = target_id
        context.user_data["waiting_for_add_balance_user_id"] = False
        context.user_data["waiting_for_add_balance_amount"] = True
        update.message.reply_text("أرسل الآن المبلغ المراد إضافته إلى رصيد المستخدم:")
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_add_balance_amount"):
        try:
            amount = float(text)
        except Exception:
            update.message.reply_text("أرسل مبلغاً صحيحاً.")
            return
        target_id = context.user_data.get("admin_target_id")
        users_balance[target_id] = users_balance.get(target_id, 0.0) + amount
        sync_balance_to_db(target_id)
        update.message.reply_text(f"تمت إضافة {amount}$ إلى رصيد المستخدم ({target_id}).")
        return

    # خصم الرصيد (المالك)
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_discount_user_id"):
        target_input = text
        try:
            target_id = int(target_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == target_input.lower():
                    found_user = usr
                    break
            if not found_user:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات.")
                return
            target_id = found_user[0]
        context.user_data["admin_target_id"] = target_id
        context.user_data["waiting_for_discount_user_id"] = False
        context.user_data["waiting_for_discount_amount"] = True
        update.message.reply_text("أرسل الآن المبلغ المراد خصمه من رصيد المستخدم:")
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_discount_amount"):
        try:
            amount = float(text)
        except Exception:
            update.message.reply_text("أرسل مبلغاً صحيحاً.")
            return
        target_id = context.user_data.get("admin_target_id")
        users_balance[target_id] = max(0.0, users_balance.get(target_id, 0.0) - amount)
        sync_balance_to_db(target_id)
        update.message.reply_text(f"تم خصم {amount}$ من رصيد المستخدم ({target_id}).")
        return

    # إدارة المشرفين (المالك)
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_add_mod"):
        # يقبل ID أو username
        m_user = None
        try:
            mid = int(text)
            row = get_user_from_db(mid)
            if row:
                m_user = (row[0], row[1], row[2])
        except ValueError:
            for usr in get_all_users():
                if usr[2] and (usr[2].lower() == text.lower() or "@"+usr[2].lower() == text.lower()):
                    m_user = usr
                    break
        if not m_user:
            update.message.reply_text("لم يتم العثور على المستخدم.")
            return
        add_moderator_db(m_user[0], m_user[1], m_user[2] or "")
        context.bot.send_message(chat_id=m_user[0], text="تمت ترقيتك إلى مشرف. افتح /start لرؤية لوحة المشرف.")
        update.message.reply_text("تمت إضافة المشرف بنجاح.")
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_del_mod"):
        mid = None
        try:
            mid = int(text)
        except ValueError:
            for usr in list_moderators_db():
                if usr[2] and (usr[2].lower() == text.lower() or "@"+usr[2].lower() == text.lower()):
                    mid = usr[0]
                    break
        if not mid:
            update.message.reply_text("لم يتم العثور على المشرف.")
            return
        remove_moderator_db(mid)
        update.message.reply_text("تم حذف المشرف بنجاح.")
        return

    # فحص حالة طلب API
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_api_order_status"):
        order_id = text
        params = {'key': API_KEY, 'action': 'status', 'order': order_id}
        try:
            response = requests.post(API_URL, data=params, timeout=25)
            rj = response.json()
            update.message.reply_text(f"نتيجة الطلب {order_id}:\n{rj}")
        except Exception as e:
            update.message.reply_text("فشل الاتصال بالـ API.")
        return

    # شحن آسياسيل — المستخدم
    if context.user_data.get("waiting_for_card"):
        card = text.replace(" ", "")
        if not card.isdigit() or len(card) not in (14, 16):
            update.message.reply_text("رقم الكارت غير صحيح. أرسل 14 أو 16 رقم.")
            return
        full_name = update.effective_user.full_name
        username = update.effective_user.username or "NoUsername"
        card_info = {
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "card_number": card
        }
        pending_cards.append(card_info)
        update.message.reply_text("تم استلام رقم الكارت ✅ وسيتم مراجعته.")
        # إشعار المالك فورًا
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⭕ طلب شحن آسياسيل جديد:\nمن: {full_name} (@{username})\nID: {user_id}\nالرقم: {card}"
        )
        return

    # تنفيذ شراء خدمة عامة — المستخدم يرسل الرابط
    if context.user_data.get("selected_service") and not context.user_data.get("selected_pubg_service") and not context.user_data.get("selected_itunes_service") and not context.user_data.get("selected_telegram_service"):
        link = text
        service_name = context.user_data.get("selected_service")
        price = float(context.user_data.get("service_price"))
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            update.message.reply_text("رصيدك ليس كافياً.")
            return
        users_balance[user_id] = current_balance - price
        sync_balance_to_db(user_id)
        order = {
            "user_id": user_id,
            "full_name": update.effective_user.full_name,
            "username": update.effective_user.username or "NoUsername",
            "service": service_name,
            "price": price,
            "link": link
        }
        pending_orders.append(order)
        update.message.reply_text("تم تسجيل طلبك وسيتم تنفيذه بعد المراجعة ✅")
        # إشعار المالك فورًا
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📝 طلب خدمة جديد (معلّق):\n{order['full_name']} (@{order['username']})\nالخدمة: {service_name}\nالسعر: {price}$\nالرابط: {link}"
        )
        context.user_data.pop("selected_service", None)
        context.user_data.pop("service_price", None)
        return

    # شدات ببجي — المستخدم يرسل الآيدي
    if context.user_data.get("selected_pubg_service"):
        pubg_id = text
        price = float(context.user_data.get("pubg_service_price"))
        if users_balance.get(user_id, 0.0) < price:
            update.message.reply_text("رصيدك ليس كافياً.")
            return
        users_balance[user_id] -= price
        sync_balance_to_db(user_id)
        order_info = {
            "user_id": user_id,
            "full_name": update.effective_user.full_name,
            "username": update.effective_user.username or "NoUsername",
            "service": context.user_data.get("selected_pubg_service"),
            "price": price,
            "pubg_id": pubg_id
        }
        pending_pubg_orders.append(order_info)
        update.message.reply_text("تم تسجيل طلب شدات ببجي، سيتم التنفيذ بعد المراجعة.")
        context.bot.send_message(chat_id=ADMIN_ID, text=f"📝 طلب ببجي جديد:\n{order_info}")
        context.user_data.pop("selected_pubg_service", None)
        context.user_data.pop("pubg_service_price", None)
        return

    # ايتونز — تأكيد ثم استلام الكود
    if context.user_data.get("waiting_for_itunes_confirm"):
        if text.strip() != "1":
            update.message.reply_text("للتأكيد أرسل 1 فقط.")
            return
        price = float(context.user_data.get("itunes_service_price"))
        if users_balance.get(user_id, 0.0) < price:
            update.message.reply_text("رصيدك ليس كافياً.")
            return
        users_balance[user_id] -= price
        sync_balance_to_db(user_id)
        order = {
            "user_id": user_id,
            "full_name": update.effective_user.full_name,
            "username": update.effective_user.username or "NoUsername",
            "service": context.user_data.get("selected_itunes_service"),
            "price": price
        }
        pending_itunes_orders.append(order)
        update.message.reply_text("تم تثبيت طلبك، سيتم إرسال كود الهدايا قريباً.")
        context.bot.send_message(chat_id=ADMIN_ID, text=f"📝 طلب ايتونز جديد:\n{order}")
        context.user_data.pop("waiting_for_itunes_confirm", None)
        context.user_data.pop("selected_itunes_service", None)
        context.user_data.pop("itunes_service_price", None)
        return

    if context.user_data.get("waiting_for_itunes_code") and user_id == ADMIN_ID:
        code = text
        itunes_order = context.user_data.get("itunes_to_complete")
        idx = context.user_data.get("itunes_to_complete_index")
        try:
            pending_itunes_orders.pop(idx)
        except Exception:
            pass
        context.bot.send_message(chat_id=itunes_order['user_id'], text=f"كود الهدايا: {code}")
        update.message.reply_text("تم إرسال الكود للمستخدم.")
        context.user_data.pop("waiting_for_itunes_code", None)
        context.user_data.pop("itunes_to_complete", None)
        context.user_data.pop("itunes_to_complete_index", None)
        return

    # روابط انضمام التليجرام
    if context.user_data.get("waiting_for_telegram_link"):
        link = text
        price = float(context.user_data.get("telegram_service_price"))
        if users_balance.get(user_id, 0.0) < price:
            update.message.reply_text("رصيدك ليس كافياً.")
            return
        users_balance[user_id] -= price
        sync_balance_to_db(user_id)
        update.message.reply_text("تم استلام الطلب وسيتم التنفيذ قريباً.")
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📝 طلب خدمة تليجرام:\nالمستخدم: {update.effective_user.full_name} (@{update.effective_user.username})\nالخدمة: {context.user_data.get('selected_telegram_service')}\nالرابط: {link}\nالسعر: {price}$"
        )
        context.user_data.pop("waiting_for_telegram_link", None)
        context.user_data.pop("selected_telegram_service", None)
        context.user_data.pop("telegram_service_price", None)
        return

    # شحن الكارت — المالك يرسل مبلغ الشحن
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_amount"):
        try:
            amount = float(text)
        except Exception:
            update.message.reply_text("أرسل مبلغاً صحيحاً.")
            return
        card_info = context.user_data.get("card_to_approve")
        index = context.user_data.get("card_to_approve_index")
        users_balance[card_info['user_id']] = users_balance.get(card_info['user_id'], 0.0) + amount
        sync_balance_to_db(card_info['user_id'])
        if 0 <= index < len(pending_cards):
            pending_cards.pop(index)
        context.bot.send_message(chat_id=card_info['user_id'], text=f"تم شحن رصيدك بمبلغ {amount}$.")
        update.message.reply_text("تم شحن الرصيد بنجاح.")
        context.user_data.pop("waiting_for_amount", None)
        context.user_data.pop("card_to_approve", None)
        context.user_data.pop("card_to_approve_index", None)
        return

    # افتراضي
    update.message.reply_text("اختر من القوائم أو ارسل /start لفتح القائمة الرئيسية.")

# أوامر للمشرف عبر /stats
def mod_stats_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_moderator(user_id) or user_id == ADMIN_ID:
        update.message.reply_text("هذا الأمر للمشرفين فقط.")
        return
    stats_text = (
        f"الطلبات:\n"
        f"- المكتملة: {len(completed_orders)}\n"
        f"- المعلقة: {len(pending_orders) + len(pending_pubg_orders) + len(pending_itunes_orders) + len(pending_cards)}\n"
        f"- الجاريه: 0\n"
        f"- الملغية: 0\n"
    )
    update.message.reply_text(stats_text)

# أخطاء عامة
def error_handler(update: Update, context: CallbackContext):
    logger.exception("Update error: %s", context.error)

# Main
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stats", mod_stats_cmd))  # للمشرفين
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))

    dp.add_error_handler(error_handler)

    logger.info("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
```0
