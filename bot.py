#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sqlite3
import requests
import time
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

# =========================
# 0) LOGGING & CONFIG
# =========================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# مالك البوت (يمكن تعديله)
ADMIN_ID = 7655504656

# متغيرات البيئة (يمكنك استبدالها بقيم صلبة)
TOKEN   = os.getenv("BOT_TOKEN", "")
API_KEY = os.getenv("KD1S_API_KEY", "3e4f5503764fa06793da9a76d24d65a4")
API_URL = os.getenv("KD1S_API_URL", "https://kd1s.com/api/v2")

if not TOKEN:
    logger.warning("⚠️ BOT_TOKEN غير مضبوط في متغيرات البيئة!")

# =========================
# 1) جداول الخدمات (كما زودتني)
# =========================
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
    "متابعين تيكتوك 1k": 3.50, "متابعين تيكتوك 2k": 7, "متابعين تيكتوك 3k": 10.50, "متابعين تيكتوك 4k": 14,
    "مشاهدات تيكتوك 1k": 0.1, "مشاهدات تيكتوك 10k": 0.80, "مشاهدات تيكتوك 20k": 1.60, "مشاهدات تيكتوك 30k": 2.40, "مشاهدات تيكتوك 50k": 3.20,
    "متابعين انستغرام 1k": 3, "متابعين انستغرام 2k": 6, "متابعين انستغرام 3k": 9, "متابعين انستغرام 4k": 12,
    "لايكات تيكتوك 1k": 1, "لايكات تيكتوك 2k": 2, "لايكات تيكتوك 3k": 3, "لايكات تيكتوك 4k": 4,
    "لايكات انستغرام 1k": 1, "لايكات انستغرام 2k": 2, "لايكات انستغرام 3k": 3, "لايكات انستغرام 4k": 4,
    "مشاهدات انستغرام 10k": 0.80, "مشاهدات انستغرام 20k": 1.60, "مشاهدات انستغرام 30k": 2.40, "مشاهدات انستغرام 50k": 3.20,
    "مشاهدات بث تيكتوك 1k": 2, "مشاهدات بث تيكتوك 2k": 4, "مشاهدات بث تيكتوك 3k": 6, "مشاهدات بث تيكتوك 4k": 8,
    "مشاهدات بث انستغرام 1k": 2, "مشاهدات بث انستغرام 2k": 4, "مشاهدات بث انستغرام 3k": 6, "مشاهدات بث انستغرام 4k": 8,
    "نقاط تحديات تيك توك جديدة | سكور 🎯": 0.51, "رفع سكور بثك1k": 2, "رفع سكور بثك2k": 4, "رفع سكور بثك3k": 6, "رفع سكور بثك10k": 20,
}

pubg_services = {
    "ببجي 60 شدة": 2, "ببجي 120 شده": 4, "ببجي 180 شدة": 6, "ببجي 240 شدة": 8, "ببجي 325 شدة": 9, "ببجي 660 شدة": 15, "ببجي 1800 شدة": 40,
}

itunes_services = {
    "شراء رصيد 5 ايتونز": 9, "شراء رصيد 10 ايتونز": 18, "شراء رصيد 15 ايتونز": 27, "شراء رصيد 20 ايتونز": 36,
    "شراء رصيد 25 ايتونز": 45, "شراء رصيد 30 ايتونز": 54, "شراء رصيد 35 ايتونز": 63, "شراء رصيد 40 ايتونز": 72,
    "شراء رصيد 45 ايتونز": 81, "شراء رصيد 50 ايتونز": 90,
}

telegram_services = {
    "اعضاء قنوات تلي 1k": 3, "اعضاء قنوات تلي 2k": 6, "اعضاء قنوات تلي 3k": 9, "اعضاء قنوات تلي 4k": 12, "اعضاء قنوات تلي 5k": 15,
    "اعضاء كروبات تلي 1k": 3, "اعضاء كروبات تلي 2k": 6, "اعضاء كروبات تلي 3k": 9, "اعضاء كروبات تلي 4k": 12, "اعضاء كروبات تلي 5k": 15,
}

# =========================
# 2) الحالة العامة/الذاكرة
# =========================
users_balance = {}
pending_orders = []         # الطلبات المعلقة (غير الـ API)
pending_cards = []          # الكروت المعلقة
pending_pubg_orders = []    # طلبات شدات ببجي المعلقة
completed_orders = []       # الطلبات المكتملة
pending_itunes_orders = []  # طلبات ايتونز المعلقة
blocked_users = {}          # قاموس الحظر

# =========================
# 3) SQLite
# =========================
DB_FILE = "bot_database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  full_name TEXT,
  username TEXT,
  balance REAL DEFAULT 0
)
""")
conn.commit()

# جدول المشرفين
cursor.execute("""
CREATE TABLE IF NOT EXISTS moderators (
  user_id INTEGER PRIMARY KEY,
  is_active INTEGER DEFAULT 1
)
""")
conn.commit()

# =========================
# 4) دوال قاعدة البيانات
# =========================
def get_user_from_db(user_id):
    cursor.execute("SELECT user_id, full_name, username, balance FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def add_user_to_db(user_id, full_name, username):
    row = get_user_from_db(user_id)
    if not row:
        cursor.execute("INSERT INTO users (user_id, full_name, username, balance) VALUES (?, ?, ?, ?)", (user_id, full_name, username, 0.0))
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

# =========================
# 5) نظام المشرفين
# =========================
def is_owner(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_moderator(user_id: int) -> bool:
    cursor.execute("SELECT is_active FROM moderators WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return False
    return bool(row[0] == 1)

def add_moderator(user_id: int):
    cursor.execute("INSERT OR REPLACE INTO moderators (user_id, is_active) VALUES (?, 1)", (user_id,))
    conn.commit()

def remove_moderator(user_id: int):
    cursor.execute("DELETE FROM moderators WHERE user_id=?", (user_id,))
    conn.commit()

def list_moderators():
    cursor.execute("SELECT user_id FROM moderators WHERE is_active=1")
    return [r[0] for r in cursor.fetchall()]

# =========================
# 6) لوحات مفاتيح
# =========================
def main_menu_keyboard(user_id):
    if is_owner(user_id):
        buttons = [
            [InlineKeyboardButton("لوحة تحكم المالك", callback_data="admin_menu")],
            [InlineKeyboardButton("لوحة المشرف", callback_data="mod_menu")],
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
        ]
    elif is_moderator(user_id):
        buttons = [
            [InlineKeyboardButton("لوحة المشرف", callback_data="mod_menu")],
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")]
        ]
    return InlineKeyboardMarkup(buttons)

def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("حضر المستخدم", callback_data="block_user"), InlineKeyboardButton("الغاء حظر المستخدم", callback_data="unblock_user")],
        [InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance"), InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")],
        [InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"), InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance")],
        [InlineKeyboardButton("مراجعة الطلبات", callback_data="review_orders"), InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders"), InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance")],
        [InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status"), InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")],
        [InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")],
        [InlineKeyboardButton("إدارة المشرفين", callback_data="admin_mods")],  # جديد
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_mods_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة مشرف", callback_data="admin_mods_add")],
        [InlineKeyboardButton("📋 عرض المشرفين", callback_data="admin_mods_list")],
        [InlineKeyboardButton("رجوع", callback_data="admin_menu")],
    ])

def moderator_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("مراجعة الطلبات (إشعار)", callback_data="mod_review_orders")],
        [InlineKeyboardButton("الكارتات المعلقة (اقتراح)", callback_data="mod_pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="mod_pending_pubg")],
        [InlineKeyboardButton("طلبات ايتونز", callback_data="mod_pending_itunes")],
        [InlineKeyboardButton("إحصائيات اليوم", callback_data="mod_kpis_today")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")],
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

# =========================
# 7) أدوات مساعدة
# =========================
def clear_all_waiting_flags(context: CallbackContext):
    waiting_keys = [
        "waiting_for_card", "waiting_for_block",
        "waiting_for_add_balance_user_id", "waiting_for_add_balance_amount",
        "waiting_for_discount_user_id", "waiting_for_discount_amount",
        "waiting_for_broadcast", "waiting_for_api_order_status",
        "selected_service", "service_price",
        "selected_pubg_service", "pubg_service_price",
        "card_to_approve", "card_to_approve_index",
        "waiting_for_amount",
        "selected_itunes_service", "itunes_service_price",
        "waiting_for_itunes_confirm", "itunes_temp_choice",
        "waiting_for_itunes_code", "itunes_to_complete", "itunes_to_complete_index",
        "selected_telegram_service", "telegram_service_price", "waiting_for_telegram_link",
        # للمشرف
        "mod_card_idx", "mod_waiting_suggest_amount",
        # لإضافة مشرف عبر زر
        "waiting_for_add_mod_user_id",
    ]
    for key in waiting_keys:
        context.user_data.pop(key, None)

def _ensure_owner_or_mod(user_id, query):
    if is_owner(user_id) or is_moderator(user_id):
        return True
    query.edit_message_text("عذراً، هذه الخاصية متاحة للمالك أو المشرف فقط.")
    return False

# =========================
# 8) البث (إعلان المالك)
# =========================
def broadcast_ad(update: Update, context: CallbackContext):
    announcement_prefix = "✨ إعلان من مالك البوت ✨\n\n"
    all_users = get_all_users()
    admin_reply = "تم إرسال الإعلان لجميع المستخدمين."
    msg = update.message
    if not msg:
        return

    try:
        if msg.photo:
            file_id = msg.photo[-1].file_id
            caption = msg.caption or ""
            new_caption = announcement_prefix + caption
            for usr in all_users:
                context.bot.send_photo(chat_id=usr[0], photo=file_id, caption=new_caption)
            msg.reply_text(admin_reply)

        elif msg.video:
            file_id = msg.video.file_id
            caption = msg.caption or ""
            new_caption = announcement_prefix + caption
            for usr in all_users:
                context.bot.send_video(chat_id=usr[0], video=file_id, caption=new_caption)
            msg.reply_text(admin_reply)

        elif msg.voice:
            file_id = msg.voice.file_id
            for usr in all_users:
                context.bot.send_message(chat_id=usr[0], text=announcement_prefix)
                context.bot.send_voice(chat_id=usr[0], voice=file_id)
            msg.reply_text(admin_reply)

        elif msg.text:
            text_to_send = announcement_prefix + msg.text
            for usr in all_users:
                context.bot.send_message(chat_id=usr[0], text=text_to_send)
            msg.reply_text(admin_reply)
        else:
            msg.reply_text("نوع الرسالة غير مدعوم.")
    except Exception as e:
        logger.error("Broadcast error: %s", e)
        msg.reply_text("حصل خطأ أثناء الإرسال.")

# =========================
# 9) أوامر نصية
# =========================
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in blocked_users and not is_owner(user_id):
        update.message.reply_text("لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك.")
        return

    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    add_user_to_db(user_id, full_name, username)
    update_username_in_db(user_id, username)
    sync_balance_from_db(user_id)

    update.message.reply_text("مرحباً بك في البوت!", reply_markup=main_menu_keyboard(user_id))

def help_cmd(update: Update, context: CallbackContext):
    txt = (
        "الأوامر المتاحة:\n"
        "/start - بدء\n"
        "/help - مساعدة\n"
        "/addmod <user_id> (مالك فقط) - إضافة مشرف\n"
        "/delmod <user_id> (مالك فقط) - حذف مشرف\n"
        "/mods - عرض قائمة المشرفين\n"
    )
    update.message.reply_text(txt)

def addmod_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        update.message.reply_text("للمالك فقط.")
        return
    if not context.args:
        update.message.reply_text("استخدم: /addmod <user_id>")
        return
    try:
        target = int(context.args[0])
    except Exception:
        update.message.reply_text("user_id غير صالح.")
        return
    add_moderator(target)
    update.message.reply_text(f"تمت إضافة {target} كمشرف ✅")

def delmod_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        update.message.reply_text("للمالك فقط.")
        return
    if not context.args:
        update.message.reply_text("استخدم: /delmod <user_id>")
        return
    try:
        target = int(context.args[0])
    except Exception:
        update.message.reply_text("user_id غير صالح.")
        return
    remove_moderator(target)
    update.message.reply_text(f"تم حذف {target} من المشرفين ✅")

def mods_cmd(update: Update, context: CallbackContext):
    mods = list_moderators()
    if not mods:
        update.message.reply_text("لا يوجد مشرفون نشطون.")
    else:
        update.message.reply_text("المشرفون:\n" + "\n".join([str(m) for m in mods]))

def api_check_balance(update: Update, context: CallbackContext):
    params = {'key': API_KEY, 'action': 'balance'}
    try:
        response = requests.post(API_URL, data=params)
        balance_info = response.json()
        if "balance" in balance_info:
            text_msg = f"رصيد حسابك في API: {balance_info['balance']}$"
        else:
            text_msg = f"حدث خطأ في جلب الرصيد من API: {balance_info.get('error', 'غير معروف')}"
    except Exception:
        text_msg = "فشل الاتصال بالـ API."
    if update.callback_query:
        query = update.callback_query
        btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
    else:
        update.message.reply_text(text_msg)

# تنفيذ طلب API (كما في منطقك)
def approve_order_process(order_index: int, context: CallbackContext, query):
    order_info = pending_orders.pop(order_index)
    if order_info['service'] in service_api_mapping:
        mapping = service_api_mapping[order_info['service']]
        quantity = mapping['quantity_multiplier']
        params = {'key': API_KEY, 'action': 'add', 'service': mapping['service_id'], 'link': order_info['link'], 'quantity': quantity}
        try:
            response = requests.post(API_URL, data=params)
            api_response = response.json()
        except Exception:
            api_response = {"error": "فشل استدعاء API"}

        if "order" in api_response:
            order_info["order_number"] = api_response["order"]
            order_info["service_number"] = mapping["service_id"]
            order_info["refunded"] = False
            order_info["completed_at"] = time.time()
            completed_orders.append(order_info)
            context.bot.send_message(chat_id=order_info['user_id'], text=f"تم استلام طلبك وسوف يتم تنفيذه قريباً\nرقم طلبك ({api_response['order']})")
            btns = [[InlineKeyboardButton("رجوع", callback_data="review_orders")]]
            query.edit_message_text("تم تنفيذ الطلب عبر API وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))
        else:
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="review_orders")]]
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
    else:
        order_info["order_number"] = "N/A"
        order_info["service_number"] = "N/A"
        order_info["refunded"] = False
        order_info["completed_at"] = time.time()
        completed_orders.append(order_info)
        context.bot.send_message(chat_id=order_info['user_id'], text="تم إكمال طلبك بنجاح (دون تنفيذ API)؛ لا يوجد تطابق للخدمة.")
        btns = [[InlineKeyboardButton("رجوع", callback_data="review_orders")]]
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))

# =========================
# 10) الأزرار (CallbackQuery)
# =========================
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    clear_all_waiting_flags(context)

    if user_id in blocked_users and not is_owner(user_id):
        query.answer("لقد تم حضرك من استخدام البوت 🤣.", show_alert=True)
        return

    # ------ لوحة المشرف ------
    if data == "mod_menu":
        if is_owner(user_id) or is_moderator(user_id):
            query.edit_message_text("لوحة المشرف:", reply_markup=moderator_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست مشرفاً.")
        return

    if data == "mod_review_orders":
        if not _ensure_owner_or_mod(user_id, query): return
        filtered = []
        for i, order in enumerate(completed_orders):
            if order.get("order_number", "N/A") != "N/A":
                filtered.append((i, order))
        if not filtered:
            btns = [[InlineKeyboardButton("رجوع", callback_data="mod_menu")]]
            query.edit_message_text("لا توجد طلبات API مكتملة.", reply_markup=InlineKeyboardMarkup(btns))
            return
        keyboard = []
        text_msg = "طلبات مكتملة عبر API (إشعار فقط):\n\n"
        for display_idx, (orig_idx, order) in enumerate(filtered, start=1):
            text_msg += f"{display_idx}) الاسم: {order['full_name']}, الخدمة: {order['service']}, السعر: {order['price']}$, رقم الطلب: {order.get('order_number','N/A')}\n\n"
            keyboard.append([InlineKeyboardButton("اشعار المستخدم", callback_data=f"mod_notify_order_{orig_idx}")])
        keyboard.append([InlineKeyboardButton("رجوع", callback_data="mod_menu")])
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("mod_notify_order_"):
        if not _ensure_owner_or_mod(user_id, query): return
        try:
            order_index = int(data.split("_")[-1])
        except ValueError:
            query.answer("خطأ في بيانات الطلب", show_alert=True)
            return
        if order_index < 0 or order_index >= len(completed_orders):
            query.answer("طلب غير موجود", show_alert=True)
            return
        order = completed_orders[order_index]
        context.bot.send_message(chat_id=order['user_id'], text="تم تنفيذ طلبك بنجاح")
        query.answer("تم إرسال إشعار للمستخدم", show_alert=True)
        return

    if data == "mod_pending_cards":
        if not _ensure_owner_or_mod(user_id, query): return
        if not pending_cards:
            btns = [[InlineKeyboardButton("رجوع", callback_data="mod_menu")]]
            query.edit_message_text("لا توجد كروت معلقة حالياً.", reply_markup=InlineKeyboardMarkup(btns))
            return
        text_msg = "الكروت المعلقة (اقتراح شحن للمالك):\n"
        buttons = []
        for idx, card in enumerate(pending_cards):
            text_msg += f"{idx+1}) @{card['username']} - كارت معلق\n"
            buttons.append([InlineKeyboardButton(f"اقتراح شحن للكارت {idx+1}", callback_data=f"mod_card_suggest_{idx}")])
        buttons.append([InlineKeyboardButton("رجوع", callback_data="mod_menu")])
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("mod_card_suggest_"):
        if not _ensure_owner_or_mod(user_id, query): return
        card_index = int(data.split("_")[-1])
        if card_index < 0 or card_index >= len(pending_cards):
            query.edit_message_text("كارت غير موجود.")
            return
        context.user_data["mod_card_idx"] = card_index
        context.user_data["mod_waiting_suggest_amount"] = True
        btns = [[InlineKeyboardButton("رجوع", callback_data="mod_pending_cards")]]
        query.edit_message_text("أرسل الآن المبلغ المقترح لشحن هذا الكارت (لن يتم الشحن مباشرة، فقط إشعار للمالك).", reply_markup=InlineKeyboardMarkup(btns))
        return

    if data == "mod_pending_pubg":
        if not _ensure_owner_or_mod(user_id, query): return
        if not pending_pubg_orders:
            btns = [[InlineKeyboardButton("رجوع", callback_data="mod_menu")]]
            query.edit_message_text("لا توجد طلبات شدات ببجي.", reply_markup=InlineKeyboardMarkup(btns))
            return
        text_msg = "طلبات شدات ببجي (إجراءات غير مالية):\n"
        buttons = []
        for idx, order in enumerate(pending_pubg_orders):
            text_msg += f"{idx+1}) @{order['username']} - {order['service']} - ID: {order['pubg_id']}\n"
            buttons.append([
                InlineKeyboardButton(f"إشعار انتظار {idx+1}", callback_data=f"mod_pubg_wait_{idx}"),
                InlineKeyboardButton(f"رفع للمالك {idx+1}", callback_data=f"mod_pubg_raise_{idx}")
            ])
        buttons.append([InlineKeyboardButton("رجوع", callback_data="mod_menu")])
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("mod_pubg_wait_"):
        if not _ensure_owner_or_mod(user_id, query): return
        idx = int(data.split("_")[-1])
        if idx < 0 or idx >= len(pending_pubg_orders):
            query.edit_message_text("طلب غير موجود.")
            return
        order_info = pending_pubg_orders[idx]
        context.bot.send_message(chat_id=order_info['user_id'], text="سوف يتم تنفيذ طلبك قريباً")
        query.answer("تم إشعار المستخدم بالانتظار", show_alert=True)
        return

    if data.startswith("mod_pubg_raise_"):
        if not _ensure_owner_or_mod(user_id, query): return
        idx = int(data.split("_")[-1])
        if idx < 0 or idx >= len(pending_pubg_orders):
            query.edit_message_text("طلب غير موجود.")
            return
        order_info = pending_pubg_orders[idx]
        context.bot.send_message(chat_id=ADMIN_ID, text=f"[مشرف] يطلب موافقة على شحن شدات ببجي:\n{order_info}")
        query.answer("تم إرسال الطلب للمالك", show_alert=True)
        return

    if data == "mod_pending_itunes":
        if not _ensure_owner_or_mod(user_id, query): return
        if not pending_itunes_orders:
            btns = [[InlineKeyboardButton("رجوع", callback_data="mod_menu")]]
            query.edit_message_text("لا توجد طلبات شحن ايتونز معلقة.", reply_markup=InlineKeyboardMarkup(btns))
            return
        text_msg = "طلبات ايتونز المعلقة:\n"
        buttons = []
        for idx, order in enumerate(pending_itunes_orders):
            text_msg += f"{idx+1}) @{order['username']} - {order['service']} بسعر {order['price']}$\n"
            buttons.append([
                InlineKeyboardButton(f"إشعار انتظار {idx+1}", callback_data=f"mod_itunes_wait_{idx}"),
                InlineKeyboardButton(f"رفع للمالك {idx+1}", callback_data=f"mod_itunes_raise_{idx}")
            ])
        buttons.append([InlineKeyboardButton("رجوع", callback_data="mod_menu")])
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("mod_itunes_wait_"):
        if not _ensure_owner_or_mod(user_id, query): return
        idx = int(data.split("_")[-1])
        if idx < 0 or idx >= len(pending_itunes_orders):
            query.edit_message_text("طلب غير موجود.")
            return
        itunes_order = pending_itunes_orders[idx]
        context.bot.send_message(chat_id=itunes_order['user_id'], text="سوف يتم ارسال كود الهدايا قريباً")
        query.answer("تم إشعار المستخدم بالانتظار", show_alert=True)
        return

    if data.startswith("mod_itunes_raise_"):
        if not _ensure_owner_or_mod(user_id, query): return
        idx = int(data.split("_")[-1])
        if idx < 0 or idx >= len(pending_itunes_orders):
            query.edit_message_text("طلب غير موجود.")
            return
        itunes_order = pending_itunes_orders[idx]
        context.bot.send_message(chat_id=ADMIN_ID, text=f"[مشرف] يطلب موافقة على إكمال طلب ايتونز:\n{itunes_order}")
        query.answer("تم إرسال الطلب للمالك", show_alert=True)
        return

    if data == "mod_kpis_today":
        if not _ensure_owner_or_mod(user_id, query): return
        today = datetime.utcnow().strftime('%Y-%m-%d')
        total_users = len(get_all_users())
        total_completed = len(completed_orders)
        total_pending = len(pending_orders) + len(pending_pubg_orders) + len(pending_itunes_orders) + len(pending_cards)
        msg = (
            f"📊 إحصائيات اليوم ({today} UTC)\n"
            f"إجمالي المستخدمين: {total_users}\n"
            f"طلبات مكتملة: {total_completed}\n"
            f"طلبات/كروت معلقة: {total_pending}"
        )
        btns = [[InlineKeyboardButton("رجوع", callback_data="mod_menu")]]
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btns))
        return

    # ------ لوحة المستخدم/المالك ------
    if data == "back_main":
        query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return

    if data == "show_services":
        query.edit_message_text("اختر القسم:", reply_markup=services_menu_keyboard())
        return

    if data == "show_tiktok_score":
        query.edit_message_text("اختر خدمة رفع سكور تيكتوك المطلوبة:", reply_markup=tiktok_score_keyboard())
        return

    if data == "admin_menu":
        if is_owner(user_id):
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return

    # == أوامر المالك الأصلية + إدارة المشرفين ==
    if is_owner(user_id):
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
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(text, reply_markup=reply_markup)
            return

        if data.startswith("unblock_"):
            try:
                target_id = int(data.split("_")[1])
            except Exception:
                query.edit_message_text("حدث خطأ في بيانات المستخدم.")
                return
            if target_id in blocked_users:
                del blocked_users[target_id]
                query.edit_message_text("تم إلغاء حظر المستخدم بنجاح.")
            else:
                query.edit_message_text("المستخدم غير موجود في القائمة المحظورة.")
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

        if data == "review_orders":
            filtered = []
            for i, order in enumerate(completed_orders):
                if order.get("order_number", "N/A") != "N/A":
                    filtered.append((i, order))
            if not filtered:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات تم تنفيذها عبر API.", reply_markup=InlineKeyboardMarkup(btns))
                return
            keyboard = []
            text_msg = ""
            for display_idx, (orig_idx, order) in enumerate(filtered, start=1):
                text_msg += f"{display_idx}) الاسم: {order['full_name']}, الخدمة: {order['service']}, السعر: {order['price']}$, رقم الطلب: {order.get('order_number', 'N/A')}\n\n"
                keyboard.append([InlineKeyboardButton("اشعار المستخدم", callback_data=f"notify_order_{orig_idx}")])
                keyboard.append([InlineKeyboardButton("ارجاع الرصيد", callback_data=f"refund_order_{orig_idx}")])
            keyboard.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith("notify_order_"):
            try:
                order_index = int(data.split("_")[-1])
            except ValueError:
                query.answer("خطأ في بيانات الطلب", show_alert=True)
                return
            if order_index < 0 or order_index >= len(completed_orders):
                query.answer("طلب غير موجود", show_alert=True)
                return
            order = completed_orders[order_index]
            context.bot.send_message(chat_id=order['user_id'], text="تم تنفيذ طلبك بنجاح")
            query.answer("تم إرسال إشعار للمستخدم", show_alert=True)
            return

        if data.startswith("refund_order_"):
            try:
                order_index = int(data.split("_")[-1])
                order = completed_orders[order_index]
            except (IndexError, ValueError):
                query.edit_message_text("طلب غير موجود.")
                return
            if order.get("refunded", False):
                query.answer("لقد تم ارجاع الرصيد مسبقاً.", show_alert=True)
                return
            refund_amount = order['price']
            target_id = order['user_id']
            users_balance[target_id] = users_balance.get(target_id, 0.0) + refund_amount
            sync_balance_to_db(target_id)
            order["refunded"] = True
            context.bot.send_message(chat_id=target_id, text=f"تم استعادة رصيدك المخصوم ({refund_amount}$)")
            query.answer("تم ارجاع الرصيد.")
            # إعادة القائمة
            filtered = []
            for i, o in enumerate(completed_orders):
                if o.get("order_number", "N/A") != "N/A":
                    filtered.append((i, o))
            if not filtered:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات تم تنفيذها عبر API.", reply_markup=InlineKeyboardMarkup(btns))
                return
            keyboard = []
            text_msg = ""
            for display_idx, (orig_idx, ord_data) in enumerate(filtered, start=1):
                text_msg += f"{display_idx}) الاسم: {ord_data['full_name']}, الخدمة: {ord_data['service']}, السعر: {ord_data['price']}$, رقم الطلب: {ord_data.get('order_number', 'N/A')}\n\n"
                keyboard.append([InlineKeyboardButton("اشعار المستخدم", callback_data=f"notify_order_{orig_idx}")])
                keyboard.append([InlineKeyboardButton("ارجاع الرصيد", callback_data=f"refund_order_{orig_idx}")])
            keyboard.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return

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

        # إدارة المشرفين (قائمة فرعية)
        if data == "admin_mods":
            query.edit_message_text("إدارة المشرفين:", reply_markup=admin_mods_keyboard())
            return

        if data == "admin_mods_add":
            context.user_data["waiting_for_add_mod_user_id"] = True
            query.edit_message_text(
                "أرسل الآن آيدي المستخدم أو اليوزر لإضافته كمشرف.\n"
                "نصيحة: اطلب من المستخدم إرسال أي رسالة للبوت ثم اعمل Reply/forward لمعرفة الـID."
            )
            return

        if data == "admin_mods_list":
            mods = list_moderators()
            if not mods:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_mods")]]
                query.edit_message_text("لا يوجد مشرفون حالياً.", reply_markup=InlineKeyboardMarkup(btns))
                return
            text_msg = "المشرفون الحاليون:\n\n"
            kb = []
            for m in mods:
                text_msg += f"- {m}\n"
                kb.append([InlineKeyboardButton(f"❌ حذف {m}", callback_data=f"admin_mods_del_{m}")])
            kb.append([InlineKeyboardButton("رجوع", callback_data="admin_mods")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(kb))
            return

        if data.startswith("admin_mods_del_"):
            try:
                target = int(data.split("_")[-1])
            except Exception:
                query.edit_message_text("ID غير صالح.", reply_markup=admin_mods_keyboard())
                return
            remove_moderator(target)
            query.edit_message_text(f"تم حذف {target} من المشرفين ✅", reply_markup=admin_mods_keyboard())
            return

    # == أوامر المستخدم العادية ==
    else:
        if data == "show_followers":
            followers_services = {k: v for k, v in services_dict.items() if "متابعين" in k}
            service_buttons = []
            for service_name, price in followers_services.items():
                btn_text = f"{service_name} - {price}$"
                service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
            return

        elif data == "show_likes":
            likes_services = {k: v for k, v in services_dict.items() if "لايكات" in k}
            service_buttons = []
            for service_name, price in likes_services.items():
                btn_text = f"{service_name} - {price}$"
                service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
            return

        elif data == "show_views":
            views_services = {k: v for k, v in services_dict.items() if "مشاهدات تيكتوك" in k or "مشاهدات انستغرام" in k}
            service_buttons = []
            for service_name, price in views_services.items():
                btn_text = f"{service_name} - {price}$"
                service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
            return

        elif data == "show_live_views":
            live_views_services = {k: v for k, v in services_dict.items() if "مشاهدات بث" in k}
            service_buttons = []
            for service_name, price in live_views_services.items():
                btn_text = f"{service_name} - {price}$"
                service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
            return

        elif data == "show_pubg":
            service_buttons = []
            for service_name, price in pubg_services.items():
                btn_text = f"{service_name} - {price}$"
                service_buttons.append([InlineKeyboardButton(btn_text, callback_data=f"pubg_service_{service_name}")])
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر خدمة شحن شدات ببجي:", reply_markup=InlineKeyboardMarkup(service_buttons))
            return

        elif data.startswith("pubg_service_"):
            service_name = data[len("pubg_service_"):]
            price = pubg_services.get(service_name, 0)
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

        elif data == "show_itunes_services":
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=itunes_services_keyboard())
            return

        elif data.startswith("itunes_service_"):
            service_name = data[len("itunes_service_"):]
            price = itunes_services.get(service_name, 0)
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

        elif data == "show_telegram_services":
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=telegram_services_keyboard())
            return

        elif data.startswith("telegram_service_"):
            service_name = data[len("telegram_service_"):]
            price = telegram_services.get(service_name, 0)
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

        elif data == "show_balance":
            balance = users_balance.get(user_id, 0.0)
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="back_main")]
            ]
            query.edit_message_text(f"رصيدك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(buttons))
            return

        elif data == "charge_asiacell":
            context.user_data["waiting_for_card"] = True
            query.edit_message_text("أرسل رقم الكارت المكون من 14 رقم أو 16 رقم:")
            return

# =========================
# 11) الرسائل النصية/الوسائط
# =========================
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text if update.message and update.message.text else ""

    if user_id in blocked_users and not is_owner(user_id):
        update.message.reply_text("لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك.")
        return

    # مالك: إضافة/خصم رصيد
    if is_owner(user_id) and context.user_data.get("waiting_for_add_balance_user_id"):
        target_input = text.strip()
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

    if is_owner(user_id) and context.user_data.get("waiting_for_discount_user_id"):
        target_input = text.strip()
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

    if is_owner(user_id) and context.user_data.get("waiting_for_add_balance_amount"):
        amount_input = text.strip()
        try:
            amount = float(amount_input)
        except ValueError:
            update.message.reply_text("الرجاء إدخال رقم صالح للمبلغ.")
            return
        target_id = context.user_data.pop("admin_target_id", None)
        context.user_data["waiting_for_add_balance_amount"] = False
        if target_id is None:
            update.message.reply_text("حدث خطأ: لا يوجد مستخدم مستهدف.")
            return
        current_balance = users_balance.get(target_id, 0.0)
        new_balance = current_balance + amount
        users_balance[target_id] = new_balance
        sync_balance_to_db(target_id)
        update.message.reply_text(f"تمت إضافة {amount}$ إلى رصيد المستخدم (ID: {target_id}). الرصيد الجديد: {new_balance}$.")
        context.bot.send_message(chat_id=target_id, text=f"تنبيه: تمت إضافة {amount}$ إلى حسابك. رصيدك الجديد: {new_balance}$.")
        return

    if is_owner(user_id) and context.user_data.get("waiting_for_discount_amount"):
        amount_input = text.strip()
        try:
            amount = float(amount_input)
        except ValueError:
            update.message.reply_text("الرجاء إدخال رقم صالح للمبلغ.")
            return
        target_id = context.user_data.pop("admin_target_id", None)
        context.user_data["waiting_for_discount_amount"] = False
        if target_id is None:
            update.message.reply_text("حدث خطأ: لا يوجد مستخدم مستهدف.")
            return
        current_balance = users_balance.get(target_id, 0.0)
        if current_balance < amount:
            update.message.reply_text("المستخدم ليس لديه رصيد كافٍ للخصم.")
            return
        new_balance = current_balance - amount
        users_balance[target_id] = new_balance
        sync_balance_to_db(target_id)
        update.message.reply_text(f"تم خصم {amount}$ من رصيد المستخدم (ID: {target_id}). الرصيد الجديد: {new_balance}$.")
        context.bot.send_message(chat_id=target_id, text=f"تنبيه: تم خصم {amount}$ من حسابك. رصيدك الجديد: {new_balance}$.")
        return

    # حضر المستخدم (مالك)
    if context.user_data.get("waiting_for_block") and is_owner(user_id):
        block_input = text.strip()
        context.user_data["waiting_for_block"] = False
        try:
            target_id = int(block_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == block_input.lower():
                    found_user = usr
                    break
            if not found_user:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات.")
                return
            target_id = found_user[0]
        blocked_users[target_id] = True
        update.message.reply_text(f"تم حضر المستخدم بنجاح. (ID: {target_id})")
        return

    # إعلان المالك
    if context.user_data.get("waiting_for_broadcast") and is_owner(user_id):
        context.user_data["waiting_for_broadcast"] = False
        broadcast_ad(update, context)
        return

    # إضافة مشرف عبر إدخال من المالك (زر إدارة المشرفين)
    if is_owner(user_id) and context.user_data.get("waiting_for_add_mod_user_id"):
        context.user_data["waiting_for_add_mod_user_id"] = False
        raw = (text or "").strip()
        target_id = None

        # محاولة كـ ID مباشر
        try:
            target_id = int(raw)
        except ValueError:
            # محاولة باليوزر
            handle = raw.lstrip("@").lower()
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == handle:
                    target_id = usr[0]
                    break

        if not target_id:
            update.message.reply_text("تعذر إيجاد المستخدم. أرسل ID صحيح أو @username موجود في قاعدة البيانات.")
            return

        if target_id == ADMIN_ID:
            update.message.reply_text("هذا المستخدم هو المالك بالفعل.")
            return

        add_moderator(target_id)
        update.message.reply_text(f"تمت إضافة {target_id} كمشرف ✅")
        return

    # كارت الشحن من المستخدم
    if context.user_data.get("waiting_for_card"):
        text_input = text.strip()
        if text_input and (len(text_input) in (14, 16)) and text_input.isdigit():
            context.user_data["waiting_for_card"] = False
            full_name = update.effective_user.full_name
            username = update.effective_user.username or "NoUsername"
            new_card = {"user_id": user_id, "full_name": full_name, "username": username, "card_number": text_input}
            pending_cards.append(new_card)
            update.message.reply_text("تم استلام رقم الكارت بنجاح، سنقوم بالمراجعة قريباً.")
            context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن جديد في الكارتات المعلقة.")
        else:
            update.message.reply_text("الرقم المدخل غير صحيح. تأكّد أنه مكوّن من 14 أو 16 رقم.")
        return

    # مشرف: اقتراح مبلغ شحن للكارت (لا يشحن فعلياً)
    if context.user_data.get("mod_waiting_suggest_amount") and (is_owner(user_id) or is_moderator(user_id)):
        amount_input = text.strip()
        try:
            amount = float(amount_input)
        except ValueError:
            update.message.reply_text("الرجاء إدخال رقم صالح للمبلغ.")
            return
        card_index = context.user_data.pop("mod_card_idx", None)
        context.user_data["mod_waiting_suggest_amount"] = False
        if card_index is None or card_index < 0 or card_index >= len(pending_cards):
            update.message.reply_text("حدث خطأ: لا يوجد كارت مستهدف.")
            return
        card_info = pending_cards[card_index]
        # إرسال اقتراح للمالك فقط
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"[مشرف] يقترح شحن الكارت للمستخدم {card_info['user_id']} (@{card_info['username']}) بمبلغ: {amount}$\n"
                 f"يمكنك الموافقة من لوحة المالك > الكارتات المعلقة."
        )
        update.message.reply_text("تم إرسال الاقتراح للمالك ✅")
        return

    # فحص حالة طلب API (مالك)
    if context.user_data.get("waiting_for_api_order_status") and is_owner(user_id):
        order_id = text.strip()
        context.user_data["waiting_for_api_order_status"] = False
        params = {'key': API_KEY, 'action': 'status', 'order': order_id}
        try:
            response = requests.post(API_URL, data=params)
            order_status = response.json()
            if "status" in order_status:
                order_num    = order_status.get("order", order_id)
                order_date   = order_status.get("date", "غير متوفر")
                order_link   = order_status.get("link", "غير متوفر")
                order_cost   = order_status.get("cost", "غير متوفر")
                order_start  = order_status.get("start_count", "غير متوفر")
                order_remains= order_status.get("remains", "غير متوفر")
                message = (
                    f"🆔 رقم الطلب: {order_num}\n"
                    f"📅 التاريخ: {order_date}\n"
                    f"🔗 الرابط: {order_link}\n"
                    f"💰 التكلفه: {order_cost}$\n"
                    f"🔢 عدد البداية: {order_start}\n"
                    f"📉 المتبقى: {order_remains}"
                )
                update.message.reply_text(message)
            else:
                update.message.reply_text(f"❌ لم يتم العثور على حالة الطلب: {order_status.get('error', 'خطأ غير معروف')}")
        except Exception:
            update.message.reply_text("❌ فشل الاتصال بالنظام الخارجي. حاول مرة أخرى لاحقاً.")
        return

    # اختيار خدمة عامة: استلام الرابط
    if "selected_service" in context.user_data and "service_price" in context.user_data:
        link_text = text.strip()
        if not link_text:
            update.message.reply_text("الرجاء إرسال الرابط كنص فقط.")
            return
        service_name = context.user_data.pop("selected_service")
        price = context.user_data.pop("service_price")
        users_balance[user_id] = users_balance.get(user_id, 0.0) - price
        sync_balance_to_db(user_id)
        if service_name in service_api_mapping:
            mapping = service_api_mapping[service_name]
            quantity = mapping["quantity_multiplier"]
            params = {'key': API_KEY, 'action': 'add', 'service': mapping["service_id"], 'link': link_text, 'quantity': quantity}
            try:
                api_response = requests.post(API_URL, data=params).json()
            except Exception:
                api_response = {"error": "فشل استدعاء API"}
            if "order" in api_response:
                update.message.reply_text(f"تم استلام طلبك وسوف يتم تنفيذه قريباً\nرقم طلبك ({api_response['order']})")
            else:
                users_balance[user_id] += price
                sync_balance_to_db(user_id)
                update.message.reply_text("فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
        else:
            new_order = {
                "user_id": user_id,
                "full_name": update.effective_user.full_name,
                "username": update.effective_user.username or "NoUsername",
                "service": service_name,
                "price": price,
                "link": link_text
            }
            pending_orders.append(new_order)
            update.message.reply_text("تم تأكيد طلبك وخصم المبلغ من رصيدك. سيتم تنفيذ الطلب قريباً.")
            context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب رشق جديد في الطلبات المعلقة.")
        return

    # شدات ببجي
    if "selected_pubg_service" in context.user_data and "pubg_service_price" in context.user_data:
        pubg_id_text = text.strip()
        service_name = context.user_data.pop("selected_pubg_service")
        price = context.user_data.pop("pubg_service_price")
        if not pubg_id_text:
            update.message.reply_text("الرجاء إرسال الآيدي كنص فقط.")
            return
        users_balance[user_id] = users_balance.get(user_id, 0.0) - price
        sync_balance_to_db(user_id)
        new_pubg_order = {
            "user_id": user_id,
            "full_name": update.effective_user.full_name,
            "username": update.effective_user.username or "NoUsername",
            "service": service_name,
            "price": price,
            "pubg_id": pubg_id_text
        }
        pending_pubg_orders.append(new_pubg_order)
        update.message.reply_text("تم تأكيد طلب شحن شدات ببجي وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند شحن الشدات أو إلغائها.")
        context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن شدات في قسم الشدات المعلقة")
        return

    # ايتونز: تأكيد 1
    if context.user_data.get("waiting_for_itunes_confirm"):
        if text.strip() == "1":
            service_name = context.user_data.pop("selected_itunes_service")
            price = context.user_data.pop("itunes_service_price")
            context.user_data["waiting_for_itunes_confirm"] = False
            current_balance = users_balance.get(user_id, 0.0)
            if current_balance < price:
                update.message.reply_text("رصيدك غير كافٍ، قم بالشحن أولاً.")
                return
            users_balance[user_id] = current_balance - price
            sync_balance_to_db(user_id)
            new_itunes_order = {
                "user_id": user_id,
                "full_name": update.effective_user.full_name,
                "username": update.effective_user.username or "NoUsername",
                "service": service_name,
                "price": price
            }
            pending_itunes_orders.append(new_itunes_order)
            update.message.reply_text("تم تأكيد طلب شراء رصيد ايتونز.\nسيتم إبلاغك عند معالجة الطلب.")
            context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن ايتونز جديد في قسم الايتونز المعلقة")
        else:
            update.message.reply_text("لم يتم تأكيد الطلب. إذا أردت إعادة المحاولة اختر الخدمة مجدداً.")
        return

    # ايتونز: إدخال الكود (مالك)
    if context.user_data.get("waiting_for_itunes_code") and is_owner(user_id):
        gift_code = text.strip()
        context.user_data["waiting_for_itunes_code"] = False
        itunes_order = context.user_data.pop("itunes_to_complete", None)
        itunes_index = context.user_data.pop("itunes_to_complete_index", None)
        if not itunes_order or itunes_index is None:
            update.message.reply_text("حدث خطأ: لا يوجد طلب ايتونز لحفظ الكود عليه.")
            return
        pending_itunes_orders.pop(itunes_index)
        context.bot.send_message(chat_id=itunes_order['user_id'], text=f"تم تنفيذ طلب شراء كود الهدايا.\nالكود:\n`{gift_code}`", parse_mode="Markdown")
        update.message.reply_text("تم إرسال كود الهدايا للمستخدم بنجاح.")
        return

    # خدمات تليجرام: رابط الدعوة
    if context.user_data.get("waiting_for_telegram_link"):
        context.user_data["waiting_for_telegram_link"] = False
        service_name = context.user_data.pop("selected_telegram_service")
        price = context.user_data.pop("telegram_service_price")
        link_invite = text.strip()
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            update.message.reply_text("رصيدك غير كافٍ. اشحن أولاً.")
            return
        users_balance[user_id] = current_balance - price
        sync_balance_to_db(user_id)
        # تحديد الكمية من اسم الخدمة
        quantity = 0
        if "1k" in service_name: quantity = 1000
        elif "2k" in service_name: quantity = 2000
        elif "3k" in service_name: quantity = 3000
        elif "4k" in service_name: quantity = 4000
        elif "5k" in service_name: quantity = 5000
        params = {'key': API_KEY, 'action': 'add', 'service': 12891, 'link': link_invite, 'quantity': quantity}
        try:
            api_response = requests.post(API_URL, data=params).json()
        except Exception:
            api_response = {"error": "فشل استدعاء API"}
        if "order" in api_response:
            update.message.reply_text(f"تم استلام طلبك وسوف يتم تنفيذه قريباً\nرقم طلبك ({api_response['order']})")
        else:
            users_balance[user_id] += price
            sync_balance_to_db(user_id)
            update.message.reply_text("فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
        return

# =========================
# 12) MAIN
# =========================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # أوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("addmod", addmod_cmd))
    dp.add_handler(CommandHandler("delmod", delmod_cmd))
    dp.add_handler(CommandHandler("mods", mods_cmd))

    # أزرار
    dp.add_handler(CallbackQueryHandler(button_handler))

    # رسائل (نص+وسائط)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video | Filters.voice, handle_messages))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
