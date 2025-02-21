#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import psycopg2
import requests
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)

# -----------------------------------
# إعدادات السجل (logging)
# -----------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------
# متغيرات البيئة (ENV Variables)
# -----------------------------------
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
TOKEN = os.environ.get("TOKEN")
API_KEY = os.environ.get("API_KEY")
API_URL = os.environ.get("API_URL")

# -----------------------------------
# تعريف القواميس الخاصة بالخدمات
# -----------------------------------
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
    "مشاهدات بث تيكتوك 1k": {"service_id": 13813, "quantity_multiplier": 1000},
    "مشاهدات بث تيكتوك 2k": {"service_id": 13813, "quantity_multiplier": 2000},
    "مشاهدات بث تيكتوك 3k": {"service_id": 13813, "quantity_multiplier": 3000},
    "مشاهدات بث تيكتوك 4k": {"service_id": 13813, "quantity_multiplier": 4000},
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

# -----------------------------------
# متغيرات التخزين المؤقت للطلبات والرصيد
# -----------------------------------
users_balance = {}
pending_orders = []         # الطلبات المعلقة (غير الـ API)
pending_cards = []          # الكروت المعلقة
pending_pubg_orders = []    # طلبات شدات ببجي المعلقة
completed_orders = []       # الطلبات المكتملة (مع إضافة الطابع الزمني)
pending_itunes_orders = []  # طلبات شحن الايتونز المعلقة
blocked_users = {}          # قاموس المستخدمين المحظورين

# -----------------------------------
# إعداد قاعدة بيانات Neon (psycopg2)
# -----------------------------------
NEON_DATABASE_URL = os.environ.get("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise Exception("NEON_DATABASE_URL environment variable is not set.")

conn = psycopg2.connect(NEON_DATABASE_URL, sslmode="require")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    full_name TEXT,
    username TEXT,
    balance REAL DEFAULT 0
)
""")
conn.commit()

required_columns = {
    "full_name": "TEXT",
    "username": "TEXT",
    "balance": "REAL DEFAULT 0"
}
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
existing_cols_info = cursor.fetchall()
existing_col_names = [col[0] for col in existing_cols_info]

for col_name, col_def in required_columns.items():
    if col_name not in existing_col_names:
        alter_stmt = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
        cursor.execute(alter_stmt)
        conn.commit()

# -----------------------------------
# دوال قاعدة البيانات والمستخدمين
# -----------------------------------
def get_user_from_db(user_id):
    cursor.execute("SELECT user_id, full_name, username, balance FROM users WHERE user_id=%s", (user_id,))
    return cursor.fetchone()

def add_user_to_db(user_id, full_name, username):
    row = get_user_from_db(user_id)
    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, full_name, username, balance) VALUES (%s, %s, %s, %s)",
            (user_id, full_name, username, 0.0)
        )
        conn.commit()

def update_user_balance_in_db(user_id, balance):
    cursor.execute("UPDATE users SET balance=%s WHERE user_id=%s", (balance, user_id))
    conn.commit()

def update_username_in_db(user_id, username):
    cursor.execute("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))
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

# -----------------------------------
# لوحات المفاتيح
# -----------------------------------
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
        [
            InlineKeyboardButton("حضر المستخدم", callback_data="block_user"),
            InlineKeyboardButton("الغاء حظر المستخدم", callback_data="unblock_user")
        ],
        [
            InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance"),
            InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")
        ],
        [
            InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"),
            InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance")
        ],
        [
            InlineKeyboardButton("مراجعة الطلبات", callback_data="review_orders"),
            InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")
        ],
        [
            InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders"),
            InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance")
        ],
        [
            InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status"),
            InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")
        ],
        [
            InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")
        ],
        [
            InlineKeyboardButton("تعديل أسعار الخدمات", callback_data="edit_service_prices")
        ],
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

# -----------------------------------
# تفريغ حالات الانتظار من user_data
# -----------------------------------
def clear_all_waiting_flags(context: CallbackContext):
    waiting_keys = [
        "waiting_for_card",
        "waiting_for_block",
        "waiting_for_add_balance_user_id",
        "waiting_for_add_balance_amount",
        "waiting_for_discount_user_id",
        "waiting_for_discount_amount",
        "waiting_for_broadcast",
        "waiting_for_api_order_status",
        "selected_service",
        "service_price",
        "selected_pubg_service",
        "pubg_service_price",
        "card_to_approve",
        "card_to_approve_index",
        "waiting_for_amount",
        "selected_itunes_service",
        "itunes_service_price",
        "waiting_for_itunes_confirm",
        "itunes_temp_choice",
        "waiting_for_itunes_code",
        "itunes_to_complete",
        "itunes_to_complete_index",
        "selected_telegram_service",
        "telegram_service_price",
        "waiting_for_telegram_link",
        "service_to_update",
        "waiting_for_new_price"
    ]
    for key in waiting_keys:
        context.user_data.pop(key, None)

# -----------------------------------
# النظام الجديد للإعلان
# -----------------------------------
def broadcast_ad(update: Update, context: CallbackContext):
    announcement_prefix = "✨ إعلان من مالك البوت ✨\n\n"
    all_users = get_all_users()
    admin_reply = "تم إرسال الإعلان لجميع المستخدمين."

    # صورة
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

    # فيديو
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

    # تسجيل صوتي
    elif update.message.voice:
        file_id = update.message.voice.file_id
        for usr in all_users:
            try:
                context.bot.send_message(chat_id=usr[0], text=announcement_prefix)
                context.bot.send_voice(chat_id=usr[0], voice=file_id)
            except Exception as e:
                logger.error("Error sending voice to %s: %s", usr[0], e)
        update.message.reply_text(admin_reply)

    # نص
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

# -----------------------------------
# دالة /start
# -----------------------------------
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

    text_msg = "مرحباً بك في البوت!"
    reply_markup = main_menu_keyboard(user_id)
    update.message.reply_text(text_msg, reply_markup=reply_markup)

# -----------------------------------
# فحص رصيد الـ API
# -----------------------------------
def api_check_balance(update: Update, context: CallbackContext):
    params = {'key': API_KEY, 'action': 'balance'}
    try:
        response = requests.post(API_URL, data=params)
        balance_info = response.json()
        if "balance" in balance_info:
            text_msg = f"رصيد حسابك في API: {balance_info['balance']}$"
        else:
            text_msg = f"حدث خطأ في جلب الرصيد من API: {balance_info.get('error', 'غير معروف')}"
    except Exception as e:
        text_msg = "فشل الاتصال بالـ API."

    if update.callback_query:
        query = update.callback_query
        btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
    else:
        update.message.reply_text(text_msg)

# -----------------------------------
# تنفيذ الطلب عبر الـ API (عند قبول الأدمـن)
# -----------------------------------
def approve_order_process(order_index: int, context: CallbackContext, query):
    order_info = pending_orders.pop(order_index)
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
            response = requests.post(API_URL, data=params)
            api_response = response.json()
        except Exception as e:
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
            btns = [[InlineKeyboardButton("رجوع", callback_data="review_orders")]]
            query.edit_message_text("تم تنفيذ الطلب عبر API وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))
        else:
            # فشل تنفيذ الطلب => إعادة الرصيد
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])

            context.bot.send_message(
                chat_id=order_info['user_id'],
                text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك."
            )
            btns = [[InlineKeyboardButton("رجوع", callback_data="review_orders")]]
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
    else:
        # خدمة يدوية
        order_info["order_number"] = "N/A"
        order_info["service_number"] = "N/A"
        order_info["refunded"] = False
        order_info["completed_at"] = time.time()
        completed_orders.append(order_info)

        context.bot.send_message(
            chat_id=order_info['user_id'],
            text="تم إكمال طلبك بنجاح (دون تنفيذ API)؛ لا يوجد تطابق للخدمة."
        )
        btns = [[InlineKeyboardButton("رجوع", callback_data="review_orders")]]
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))

# -----------------------------------
# معالج الضغط على الأزرار
# -----------------------------------
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    clear_all_waiting_flags(context)

    if user_id in blocked_users and user_id != ADMIN_ID:
        query.answer("لقد تم حضرك من استخدام البوت 🤣.", show_alert=True)
        return

    # -- اختيار خدمة من الخدمات العامة --
    if data.startswith("service_"):
        service_name = data[len("service_"):]
        price = services_dict.get(service_name)
        if price is None:
            query.edit_message_text("الخدمة غير موجودة.")
            return

        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="show_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return

        # نص مخصص لبعض الخدمات
        if "انستغرام" in service_name:
            message_text = (
                "الرجاء إرسال رابط الخدمة الخاص بك\n"
                "🔴 تنبيه:\n"
                "يرجى إطفاء زر 'تميز للمراجعة' داخل حسابك الانستغرام قبل ارسال رابط الخدمه لضمان إكمال طلبك!"
            )
        elif "رفع سكور بث" in service_name:
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

    # زر الرجوع للقائمة الرئيسية
    if data == "back_main":
        query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return

    # عرض الخدمات
    if data == "show_services":
        query.edit_message_text("اختر القسم:", reply_markup=services_menu_keyboard())
        return

    if data == "show_tiktok_score":
        query.edit_message_text("اختر خدمة رفع سكور تيكتوك المطلوبة:", reply_markup=tiktok_score_keyboard())
        return

    # لوحة المالك
    if data == "admin_menu":
        if user_id == ADMIN_ID:
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return

    # -- تعديل أسعار الخدمات --
    if data == "edit_service_prices":
        if user_id != ADMIN_ID:
            query.edit_message_text("عذراً، هذه الميزة مخصصة للمالك فقط.")
            return

        keyboard = []
        for service_name, price in services_dict.items():
            btn_text = f"{service_name} - {price}$"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"edit_service_price_{service_name}")])

        keyboard.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
        query.edit_message_text("اختر الخدمة التي تريد تعديل سعرها:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("edit_service_price_"):
        if user_id != ADMIN_ID:
            query.edit_message_text("عذراً، هذه الميزة مخصصة للمالك فقط.")
            return

        service_name = data[len("edit_service_price_"):]
        context.user_data["service_to_update"] = service_name
        context.user_data["waiting_for_new_price"] = True
        query.edit_message_text(f"أرسل السعر الجديد لـ {service_name}:")
        return

    # بقية الأزرار الإدارية (حظر/إلغاء حظر ... إضافة الرصيد ... إلخ)
    # ... ستجدها في الكود الأصلي إذا كنت بحاجة لكل التفاصيل ...
    # لم نحذفها، إنما تُتابع بنفس المنطق (block_user, unblock_user, admin_add_balance...الخ)
    # ------------------------------------------
    # بقية الأقسام من الكود: show_followers, show_likes, show_views, show_live_views, show_pubg, show_itunes_services...
    # (كما هو في الكود الذي بعثته أنت، أو في الأمثلة السابقة).

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

    # وغيرها من الأقسام...
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


# -----------------------------------
# معالج الرسائل النصية
# -----------------------------------
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text_msg = update.message.text.strip() if update.message.text else ""

    # 1) إذا كان الأدمـن بانتظار إدخال سعر جديد (تعديل السعر في الخدمات)
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_new_price"):
        context.user_data.pop("waiting_for_new_price", None)
        service_name = context.user_data.pop("service_to_update", None)
        if not service_name:
            update.message.reply_text("لم يتم تحديد الخدمة بشكل صحيح.")
            return

        try:
            new_price = float(text_msg)
        except ValueError:
            update.message.reply_text("الرجاء إدخال رقم صالح للسعر.")
            return

        # هنا الإصلاح: استخدام services_dict
        if service_name in services_dict:
            services_dict[service_name] = new_price
            update.message.reply_text(f"تم تعديل سعر الخدمة '{service_name}' إلى {new_price}$ بنجاح.")
        else:
            update.message.reply_text("الخدمة غير موجودة في القاموس.")
        return

    # 2) بقية حالات الانتظار (مثل إدخال آيدي المستخدم لشحن الرصيد، إدخال كود ايتونز...)
    # ... انسخ كودك الأصلي كما هو ...

    # إذا لم تنطبق أي حالة انتظار معروفة
    update.message.reply_text("يرجى استخدام الأزرار لتنفيذ الأوامر أو التحقق من الخيارات.")

# -----------------------------------
# دالة main
# -----------------------------------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
