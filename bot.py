#!/usr/bin/env python
# -- coding: utf-8 --

import logging
import sqlite3
import requests
import time  # لإضافة طابع زمني للطلبات المكتملة

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

# ------------------------------------------------
# الإعدادات والمتغيرات العامة
# ------------------------------------------------

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 7655504656         # عدل الآيدي حسب المالك
TOKEN = "8138615524:AAEZGgBRMSzLxxC7F6NquT4dbmk5vA-2w4M"  # ضع توكن البوت الخاص بك هنا
API_KEY = "cc44589ee833e48fc023984723bc78fe"  # ضع API KEY الخاص بك هنا
API_URL = "https://kd1s.com/api/v2"  # تأكد من صحة رابط API

# تعريف قاموس تحويل الخدمات المحلية إلى معطيات API الخارجية
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
    "لايكات تيكتوك 1k": {"service_id": 13761, "quantity_multiplier": 1000},
    "لايكات تيكتوك 2k": {"service_id": 13761, "quantity_multiplier": 2000},
    "لايكات تيكتوك 3k": {"service_id": 13761, "quantity_multiplier": 3000},
    "لايكات تيكتوك 4k": {"service_id": 13761, "quantity_multiplier": 4000},
    "لايكات انستغرام 1k": {"service_id": 7973, "quantity_multiplier": 1000},
    "لايكات انستغرام 2k": {"service_id": 7973, "quantity_multiplier": 2000},
    "لايكات انستغرام 3k": {"service_id": 7973, "quantity_multiplier": 3000},
    "لايكات انستغرام 4k": {"service_id": 7973, "quantity_multiplier": 4000},
    "مشاهدات انستغرام 10k": {"service_id": 13532, "quantity_multiplier": 10000},
    "مشاهدات انستغرام 20k": {"service_id": 13532, "quantity_multiplier": 20000},
    "مشاهدات انستغرام 30k": {"service_id": 13532, "quantity_multiplier": 30000},
    "مشاهدات انستغرام 50k": {"service_id": 13532, "quantity_multiplier": 50000},
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

# قائمة الخدمات المحلية (للعرض فقط)
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
    "متابعين انستغرام 1k": 2,
    "متابعين انستغرام 2k": 4,
    "متابعين انستغرام 3k": 6,
    "متابعين انستغرام 4k": 8,
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

# خدمات شحن شدات ببجي (مثال)
pubg_services = {
    "ببجي 60 شدة": 2,
    "ببجي 120 شده": 4,
    "ببجي 180 شدة": 6,
    "ببجي 240 شدة": 8,
    "ببجي 325 شدة": 9,
    "ببجي 660 شدة": 15,
    "ببجي 1800 شدة": 40,
}

# المتغيرات الخاصة بالطلبات والرصيد
users_balance = {}
pending_orders = []      # الطلبات المعلقة (غير الـ API)
pending_cards = []       # الكروت المعلقة
pending_pubg_orders = [] # طلبات شدات ببجي المعلقة
completed_orders = []    # الطلبات المكتملة (يُضاف لها الطابع الزمني عند الإتمام)

# ------------------------------------------------
# إعداد قاعدة بيانات SQLite
# ------------------------------------------------
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

# ------------------------------------------------
# القاموس الخاص بالمستخدمين المحظورين
# ------------------------------------------------
blocked_users = {}

# ------------------------------------------------
# دوال مساعدة للوصول لبيانات المستخدمين
# ------------------------------------------------
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

# ------------------------------------------------
# مزامنة الرصيد بين القاموس وقاعدة البيانات
# ------------------------------------------------
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
        update_user_balance_to_db(user_id, bal)

# ------------------------------------------------
# دوال لبناء قوائم الأزرار
# ------------------------------------------------
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
        [InlineKeyboardButton("الطلبات المعلقة", callback_data="pending_orders"),
         InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders"),
         InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance")],
        [InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status"),
         InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")],
        [InlineKeyboardButton("الطلبات المكتملة", callback_data="completed_orders")],
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
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def tiktok_score_keyboard():
    score_services = {k: v for k, v in services_dict.items() if "رفع سكور" in k}
    buttons = []
    for service_name, price in score_services.items():
        btn_text = f"{service_name} - {price}$"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

# ------------------------------------------------
# دالة /start
# ------------------------------------------------
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

# ------------------------------------------------
# دالة مساعدة لتنفيذ الطلبات (approve_order_process)
# ------------------------------------------------
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
            order_info["completed_at"] = time.time()  # حفظ وقت الإتمام
            completed_orders.append(order_info)
            context.bot.send_message(
                chat_id=order_info['user_id'],
                text=f"تم تنفيذ طلبك بنجاح عبر النظام الخارجي. رقم الطلب: {api_response['order']}"
            )
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_orders")]]
            query.edit_message_text("تم تنفيذ الطلب عبر API وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))
        else:
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(
                chat_id=order_info['user_id'],
                text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك."
            )
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_orders")]]
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
    else:
        order_info["order_number"] = "N/A"
        order_info["service_number"] = "N/A"
        order_info["refunded"] = False
        order_info["completed_at"] = time.time()
        completed_orders.append(order_info)
        context.bot.send_message(
            chat_id=order_info['user_id'],
            text="تم إكمال طلبك بنجاح (دون تنفيذ API)؛ لا يوجد تطابق للخدمة."
        )
        btns = [[InlineKeyboardButton("رجوع", callback_data="pending_orders")]]
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))

# ------------------------------------------------
# دالة button_handler للتعامل مع ضغط الأزرار
# ------------------------------------------------
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    # عند بدء عملية جديدة يتم مسح علامة انتظار إدخال رقم الكارت إن وجدت
    if data in ["show_services", "show_followers", "show_likes", "show_views", "show_live_views", "show_pubg", "show_tiktok_score"] or \
       data.startswith("service_") or data.startswith("pubg_service_"):
        context.user_data.pop("waiting_for_card", None)

    if user_id in blocked_users and user_id != ADMIN_ID:
        query.answer("لقد تم حضرك من استخدام البوت 🤣.", show_alert=True)
        return

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
        if user_id == ADMIN_ID:
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return

    # أوامر المالك
    if user_id == ADMIN_ID:
        if data == "block_user":
            query.edit_message_text("أرسل اليوزرنيم أو الآيدي للمستخدم الذي تريد حضره:")
            context.user_data["waiting_for_block"] = True
            return
        if data == "unblock_user":
            if not blocked_users:
                query.edit_message_text("لا يوجد مستخدمين محظورين.")
                return
            else:
                text = "قائمة المستخدمين المحظورين:\n"
                keyboard = []
                for uid in blocked_users:
                    row = get_user_from_db(uid)
                    if row:
                        user_display = f"{row[1]} (@{row[2]})"
                    else:
                        user_display = f"User {uid}"
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
            query.edit_message_text("أرسل الآن الرسالة أو الوسائط للإعلان لجميع المستخدمين:")
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
        if data == "pending_orders":
            if not pending_orders:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات معلّقة حالياً.", reply_markup=InlineKeyboardMarkup(btns))
            else:
                text_msg = "الطلبات المعلقة:\n"
                buttons = []
                for idx, order in enumerate(pending_orders):
                    text_msg += f"{idx+1}) طلب من @{order['username']} - الخدمة: {order['service']}\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الطلب رقم {idx+1}", callback_data=f"process_order_{idx}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return
        if data.startswith("process_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_orders[order_index]
            text_msg = (
                f"تفاصيل الطلب رقم {order_index+1}:\n"
                f"- المعرف: {order_info['user_id']}\n"
                f"- الاسم: {order_info['full_name']}\n"
                f"- يوزر: @{order_info['username']}\n"
                f"- الخدمة: {order_info['service']}\n"
                f"- السعر: {order_info['price']}$\n"
                f"- الرابط: {order_info['link']}\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("تم إكمال الطلب بنجاح", callback_data=f"approve_order_{order_index}"),
                 InlineKeyboardButton("تم رفض الطلب", callback_data=f"reject_order_{order_index}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return
        if data.startswith("approve_order_"):
            order_index = int(data.split("_")[-1])
            approve_order_process(order_index, context, query)
            return
        if data.startswith("reject_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_orders.pop(order_index)
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="تم رفض الطلب، وتمت إعادة الرصيد إلى حسابك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_orders")]]
            query.edit_message_text("تم رفض الطلب وإعادة الرصيد للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))
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
                f"- المعرف: `{card_info['user_id']}`\n"
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
            query.message.reply_text(
                text=f"رقم الكارت:\n`{card_info['card_number']}`\nاضغط مطولاً للنسخ.",
                parse_mode="Markdown"
            )
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
        if data == "api_check_balance":
            api_check_balance(update, context)
            return
        if data == "api_order_status":
            query.edit_message_text("أدخل رقم الطلب للتحقق من حالته عبر API:")
            context.user_data["waiting_for_api_order_status"] = True
            return

        # ----- نظام عرض الطلبات المكتملة -----
        if data == "completed_orders":
            if not completed_orders:
                btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
                query.edit_message_text("لا توجد طلبات مكتملة.", reply_markup=InlineKeyboardMarkup(btns))
            else:
                text_msg = "الطلبات المكتملة:\n\n"
                buttons = []
                for idx, order in enumerate(completed_orders):
                    text_msg += (
                        f"{idx+1}) الاسم: {order['full_name']}, يوزر: @{order['username']}, ID: {order['user_id']}\n"
                        f"   الرابط: {order['link']}\n"
                        f"   رقم الطلب: {order.get('order_number', 'N/A')}, رقم الخدمة: {order.get('service_number', 'N/A')}\n"
                        f"   سعر الخدمة: {order['price']}$\n"
                    )
                    if not order.get("refunded", False):
                        buttons.append([InlineKeyboardButton(
                            f"ارجاع الرصيد المخصوم للطلب {idx+1}",
                            callback_data=f"refund_order_{idx}"
                        )])
                    else:
                        text_msg += "   (تم ارجاع الرصيد المخصوم)\n"
                    text_msg += "\n"
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
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

            context.bot.send_message(
                chat_id=target_id,
                text=f"تم استعادة رصيدك المخصوم ({refund_amount}$)"
            )
            query.answer("تم ارجاع الرصيد.")

            # تحديث عرض الطلبات المكتملة بعد عملية الاسترجاع
            text_msg = "الطلبات المكتملة:\n\n"
            buttons = []
            for idx, order in enumerate(completed_orders):
                text_msg += (
                    f"{idx+1}) الاسم: {order['full_name']}, يوزر: @{order['username']}, ID: {order['user_id']}\n"
                    f"   الرابط: {order['link']}\n"
                    f"   رقم الطلب: {order.get('order_number', 'N/A')}, رقم الخدمة: {order.get('service_number', 'N/A')}\n"
                    f"   سعر الخدمة: {order['price']}$\n"
                )
                if not order.get("refunded", False):
                    buttons.append([InlineKeyboardButton(
                        f"ارجاع الرصيد المخصوم للطلب {idx+1}",
                        callback_data=f"refund_order_{idx}"
                    )])
                else:
                    text_msg += "   (تم ارجاع الرصيد المخصوم)\n"
                text_msg += "\n"
            buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return

    # أوامر المستخدمين العادية
    else:
        if data == "show_services":
            query.edit_message_text("اختر القسم:", reply_markup=services_menu_keyboard())
            return
        elif data == "show_followers":
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
            sorted_views = sorted(views_services.items(), key=lambda item: item[1])
            service_buttons = []
            for service_name, price in sorted_views:
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
            context.user_data.pop("waiting_for_card", None)
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
        elif data.startswith("service_"):
            context.user_data.pop("waiting_for_card", None)
            service_name = data[len("service_"):]
            price = services_dict.get(service_name, 0)
            current_balance = users_balance.get(user_id, 0.0)
            if current_balance < price:
                buttons = [
                    [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                    [InlineKeyboardButton("رجوع", callback_data="show_services")]
                ]
                query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
                return
            context.user_data["selected_service"] = service_name
            context.user_data["service_price"] = price
            query.edit_message_text(f"لقد اخترت الخدمة: {service_name} - {price}$. الآن، يرجى إرسال الرابط الخاص بالخدمة:")
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
            # عند اختيار شحن عبر اسياسيل يتم تفعيل flag خاص وانتظار رقم الكارت
            context.user_data["waiting_for_card"] = True
            query.edit_message_text("أرسل رقم الكارت المكون من 14 رقم أو 16 رقم:")
            return

# ------------------------------------------------
# دالة handle_messages للتعامل مع الرسائل النصية
# ------------------------------------------------
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # إذا كان المستخدم محظوراً
    if user_id in blocked_users and user_id != ADMIN_ID:
        update.message.reply_text("لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك.")
        return

    # التعامل مع انتظار البث (broadcast) وغيرها من الانتظارات الخاصة بالمالك...
    if context.user_data.get("waiting_for_broadcast") and user_id == ADMIN_ID:
        context.user_data["waiting_for_broadcast"] = False
        announcement_prefix = "✨ إعلان من مالك البوت ✨\n\n"
        all_users = get_all_users()
        admin_reply = "تم إرسال الإعلان لجميع المستخدمين."
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            caption = update.message.caption if update.message.caption else ""
            new_caption = announcement_prefix + caption
            for user in all_users:
                try:
                    context.bot.send_photo(chat_id=user[0], photo=file_id, caption=new_caption)
                except Exception as e:
                    logger.error(e)
            update.message.reply_text(admin_reply)
            return
        elif update.message.video:
            file_id = update.message.video.file_id
            caption = update.message.caption if update.message.caption else ""
            new_caption = announcement_prefix + caption
            for user in all_users:
                try:
                    context.bot.send_video(chat_id=user[0], video=file_id, caption=new_caption)
                except Exception as e:
                    logger.error(e)
            update.message.reply_text(admin_reply)
            return
        elif update.message.voice:
            file_id = update.message.voice.file_id
            caption = update.message.caption if update.message.caption else ""
            new_caption = announcement_prefix + caption
            for user in all_users:
                try:
                    context.bot.send_voice(chat_id=user[0], voice=file_id, caption=new_caption)
                except Exception as e:
                    logger.error(e)
            update.message.reply_text(admin_reply)
            return
        elif update.message.document:
            file_id = update.message.document.file_id
            caption = update.message.caption if update.message.caption else ""
            new_caption = announcement_prefix + caption
            for user in all_users:
                try:
                    context.bot.send_document(chat_id=user[0], document=file_id, caption=new_caption)
                except Exception as e:
                    logger.error(e)
            update.message.reply_text(admin_reply)
            return
        elif update.message.audio:
            file_id = update.message.audio.file_id
            caption = update.message.caption if update.message.caption else ""
            new_caption = announcement_prefix + caption
            for user in all_users:
                try:
                    context.bot.send_audio(chat_id=user[0], audio=file_id, caption=new_caption)
                except Exception as e:
                    logger.error(e)
            update.message.reply_text(admin_reply)
            return
        elif update.message.text:
            text_to_send = announcement_prefix + update.message.text
            for user in all_users:
                try:
                    context.bot.send_message(chat_id=user[0], text=text_to_send)
                except Exception as e:
                    logger.error(e)
            update.message.reply_text(admin_reply)
            return
        else:
            update.message.reply_text("نوع الرسالة غير مدعوم.")
            return

    # التعامل مع انتظار إدخال رقم الكارت (شحن عبر اسياسيل)
    if context.user_data.get("waiting_for_card"):
        text = update.message.text.strip()
        if text and (len(text) == 14 or len(text) == 16) and text.isdigit():
            context.user_data["waiting_for_card"] = False
            full_name = update.effective_user.full_name
            username = update.effective_user.username or "NoUsername"
            new_card = {
                "user_id": user_id,
                "full_name": full_name,
                "username": username,
                "card_number": text
            }
            pending_cards.append(new_card)
            update.message.reply_text("تم استلام رقم الكارت بنجاح، سنقوم بالمراجعة قريباً.")
            context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن جديد في الكارتات المعلقة.")
        else:
            update.message.reply_text("الرقم المدخل غير صحيح. تأكّد أنه مكوّن من 14 رقم أو 16 رقم.")
        return

    # باقي الشيفرة لمعالجة باقي حالات الانتظار (مثل waiting_for_api_order_status، selected_service، selected_pubg_service، ...)

    if context.user_data.get("waiting_for_api_order_status") and user_id == ADMIN_ID:
        order_id = update.message.text.strip()
        context.user_data["waiting_for_api_order_status"] = False
        params = {
            'key': API_KEY,
            'action': 'status',
            'order': order_id
        }
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
        except Exception as e:
            update.message.reply_text("❌ فشل الاتصال بالنظام الخارجي. حاول مرة أخرى لاحقاً.")
        return

    if "selected_service" in context.user_data and "service_price" in context.user_data:
        text = update.message.text
        if not text:
            update.message.reply_text("الرجاء إرسال الرابط كنص فقط.")
            return
        service_name = context.user_data.pop("selected_service")
        price = context.user_data.pop("service_price")
        full_name = update.effective_user.full_name
        username = update.effective_user.username or "NoUsername"
        users_balance[user_id] -= price
        sync_balance_to_db(user_id)
        if service_name in service_api_mapping:
            mapping = service_api_mapping[service_name]
            quantity = mapping["quantity_multiplier"]
            params = {
                'key': API_KEY,
                'action': 'add',
                'service': mapping["service_id"],
                'link': text,
                'quantity': quantity
            }
            try:
                response = requests.post(API_URL, data=params)
                api_response = response.json()
            except Exception as e:
                api_response = {"error": "فشل استدعاء API"}
            if "order" in api_response:
                update.message.reply_text(f"تم تنفيذ طلبك بنجاح عبر النظام الخارجي. رقم الطلب: {api_response['order']}")
            else:
                users_balance[user_id] += price
                sync_balance_to_db(user_id)
                update.message.reply_text("فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
            return
        else:
            new_order = {
                "user_id": user_id,
                "full_name": full_name,
                "username": username,
                "service": service_name,
                "price": price,
                "link": text
            }
            pending_orders.append(new_order)
            update.message.reply_text("تم تأكيد طلبك وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند إتمام الطلب أو رفضه.")
            context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب رشق جديد في الطلبات المعلقة.")
            return

    if "selected_pubg_service" in context.user_data and "pubg_service_price" in context.user_data:
        pubg_id_text = update.message.text
        if not pubg_id_text:
            update.message.reply_text("الرجاء إرسال الآيدي كنص فقط.")
            return
        service_name = context.user_data.pop("selected_pubg_service")
        price = context.user_data.pop("pubg_service_price")
        full_name = update.effective_user.full_name
        username = update.effective_user.username or "NoUsername"
        users_balance[user_id] -= price
        sync_balance_to_db(user_id)
        new_pubg_order = {
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "pubg_id": pubg_id_text
        }
        pending_pubg_orders.append(new_pubg_order)
        update.message.reply_text("تم تأكيد طلب شحن شدات ببجي وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند شحن الشدات أو إلغائها.")
        context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن شدات في قسم الشدات المعلقة")
        return

    if context.user_data.get("waiting_for_add_balance_user_id") and user_id == ADMIN_ID:
        text = update.message.text
        context.user_data["waiting_for_add_balance_user_id"] = False
        try:
            target_user_id = int(text)
            row = get_user_from_db(target_user_id)
            if not row:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات.")
                return
            context.user_data["add_balance_target_user_id"] = target_user_id
            update.message.reply_text(f"تم العثور على المستخدم: {row[1]} (@{row[2]})\nأرسل الآن المبلغ المراد إضافته إلى رصيده:")
            context.user_data["waiting_for_add_balance_amount"] = True
        except ValueError:
            update.message.reply_text("الرجاء إدخال رقم آيدي صحيح (عدد).")
        return

    if context.user_data.get("waiting_for_add_balance_amount") and user_id == ADMIN_ID:
        text = update.message.text
        context.user_data["waiting_for_add_balance_amount"] = False
        try:
            amount_to_add = float(text)
            target_user_id = context.user_data.pop("add_balance_target_user_id", None)
            if target_user_id is None:
                update.message.reply_text("حدث خطأ: لا يوجد آيدي مستخدم مخزّن.")
                return
            sync_balance_from_db(target_user_id)
            current_balance = users_balance.get(target_user_id, 0.0)
            new_balance = current_balance + amount_to_add
            users_balance[target_user_id] = new_balance
            sync_balance_to_db(target_user_id)
            update.message.reply_text(f"تم إضافة {amount_to_add}$ إلى رصيد المستخدم.\nالرصيد الجديد: {new_balance}$")
            context.bot.send_message(chat_id=target_user_id, text=f"تم إضافة {amount_to_add}$ إلى رصيدك بواسطة الإدارة.\nرصيدك الحالي: {new_balance}$")
        except ValueError:
            update.message.reply_text("الرجاء إدخال مبلغ صحيح (رقم).")
        return

    if context.user_data.get("waiting_for_discount_user_id") and user_id == ADMIN_ID:
        text = update.message.text
        context.user_data["waiting_for_discount_user_id"] = False
        try:
            target_user_id = int(text)
            row = get_user_from_db(target_user_id)
            if not row:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات.")
                return
            context.user_data["discount_target_user_id"] = target_user_id
            update.message.reply_text(f"تم العثور على المستخدم: {row[1]} (@{row[2]})\nأرسل الآن المبلغ المراد خصمه من رصيده:")
            context.user_data["waiting_for_discount_amount"] = True
        except ValueError:
            update.message.reply_text("الرجاء إدخال رقم آيدي صحيح (عدد).")
        return

    if context.user_data.get("waiting_for_discount_amount") and user_id == ADMIN_ID:
        text = update.message.text
        context.user_data["waiting_for_discount_amount"] = False
        try:
            amount_to_discount = float(text)
            target_user_id = context.user_data.pop("discount_target_user_id", None)
            if target_user_id is None:
                update.message.reply_text("حدث خطأ: لا يوجد آيدي مستخدم مسجّل.")
                return
            sync_balance_from_db(target_user_id)
            current_balance = users_balance.get(target_user_id, 0.0)
            if current_balance <= 0:
                update.message.reply_text("لا يمكن الخصم، رصيد المستخدم = 0.")
                return
            if current_balance >= amount_to_discount:
                new_balance = current_balance - amount_to_discount
                users_balance[target_user_id] = new_balance
                sync_balance_to_db(target_user_id)
                update.message.reply_text(f"تم خصم {amount_to_discount}$ من رصيد المستخدم بنجاح.\nالرصيد الجديد: {new_balance}$")
                context.bot.send_message(chat_id=target_user_id, text=f"تم خصم {amount_to_discount}$ من رصيدك بواسطة الإدارة.\nرصيدك الحالي: {new_balance}$")
            else:
                update.message.reply_text(f"رصيد المستخدم ({current_balance}$) لا يكفي لخصم {amount_to_discount}$.")
        except ValueError:
            update.message.reply_text("الرجاء إدخال مبلغ صحيح (رقم).")
        return

    if context.user_data.get("waiting_for_amount") and user_id == ADMIN_ID:
        text = update.message.text
        try:
            amount = float(text)
            context.user_data["waiting_for_amount"] = False
            card_info = context.user_data.pop("card_to_approve")
            card_index = context.user_data.pop("card_to_approve_index")
            pending_cards.pop(card_index)
            users_balance[card_info["user_id"]] = users_balance.get(card_info["user_id"], 0.0) + amount
            sync_balance_to_db(card_info["user_id"])
            update.message.reply_text(f"تم شحن رصيد المستخدم بمبلغ {amount}$ وإشعاره بذلك.")
            context.bot.send_message(chat_id=card_info["user_id"], text=f"تم شحن رصيدك بقيمة {amount}$. شكراً لاستخدامك خدمتنا.")
        except ValueError:
            update.message.reply_text("الرجاء إدخال مبلغ شحن صالح (رقم).")
        return

# ------------------------------------------------
# دالة API check balance
# ------------------------------------------------
def api_check_balance(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    params = {
        'key': API_KEY,
        'action': 'balance'
    }
    try:
        response = requests.post(API_URL, data=params)
        balance_data = response.json()
        if "balance" in balance_data:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]])
            query.edit_message_text(f"💰 رصيد حساب API: {balance_data['balance']}$", reply_markup=reply_markup)
        else:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]])
            query.edit_message_text(f"❌ فشل جلب الرصيد: {balance_data.get('error', 'خطأ غير معروف')}", reply_markup=reply_markup)
    except Exception as e:
        query.edit_message_text("❌ فشل الاتصال بـ API.")

# ------------------------------------------------
# تسجيل المعالجات وتشغيل البوت
# ------------------------------------------------
if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.all, handle_messages))

    updater.start_polling()
    updater.idle()
