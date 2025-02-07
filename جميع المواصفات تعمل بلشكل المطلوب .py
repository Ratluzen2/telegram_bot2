#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext
)

# ------------------------------------------------
# 1) الإعدادات العامة والمتغيّرات
# ------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 7655504656  # غيّر الرقم إلى ايدي المالك

services_dict = {
    "متابعين تيكتوك 1k": 3.50,
    "متابعين تيكتوك 2k": 7,
    "متابعين تيكتوك 3k": 10.50,
    "متابعين تيكتوك 4k": 14,

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

    "مشاهدات تيكتوك 10k": 0.80,
    "مشاهدات تيكتوك 20k": 1.60,
    "مشاهدات تيكتوك 30k": 2.40,
    "مشاهدات تيكتوك 50k": 3.20,

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
}

# الخدمات الخاصة بشحن شدات ببجي
pubg_services = {
    "ببجي 60 شدة": 2,
    "ببجي 120 شده": 4,
    "ببجي 180 شدة": 6,
    "ببجي 240 شدة": 8,
    "ببجي 325 شدة": 9,
    "ببجي 660 شدة": 15,
    "ببجي 1800 شدة": 40,
}

users_balance = {}   
pending_orders = []
pending_cards = []
# قائمة طلبات شدات ببجي المعلقة
pending_pubg_orders = []

# ------------------------------------------------
# 2) إعداد قاعدة بيانات SQLite
# ------------------------------------------------
DB_FILE = "bot_database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
    -- سيتم إضافة الأعمدة الأخرى بواسطة ALTER TABLE لاحقاً
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
# 3) دوال مساعدة للوصول لبيانات المستخدمين
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
# 4) مزامنة الرصيد بين dict و DB
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
        update_user_balance_in_db(user_id, bal)

# ------------------------------------------------
# 5) دوال لبناء قوائم الأزرار
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
        [
            InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards"),
            InlineKeyboardButton("الطلبات المعلقة", callback_data="pending_orders")
        ],
        [
            InlineKeyboardButton("اعلان البوت", callback_data="admin_announce"),
            InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count")
        ],
        [
            InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance"),
            InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")
        ],
        [
            InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance")
        ],
        [
            InlineKeyboardButton("طلبات الشدات المعلقه", callback_data="pending_pubg_orders")
        ],
        [
            InlineKeyboardButton("رجوع", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

# ------------------------------------------------
# 6) دالة /start
# ------------------------------------------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"

    add_user_to_db(user_id, full_name, username)
    update_username_in_db(user_id, username)
    sync_balance_from_db(user_id)

    text = "مرحباً بك في البوت!"
    reply_markup = main_menu_keyboard(user_id)
    update.message.reply_text(text, reply_markup=reply_markup)

# ------------------------------------------------
# 7) التعامل مع ضغط الأزرار (button_handler)
# ------------------------------------------------
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    query.answer()

    # زر الرجوع للقائمة الرئيسية
    if data == "back_main":
        query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return

    # دخول لوحة المالك
    if data == "admin_menu":
        if user_id == ADMIN_ID:
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return

    # ------------------------ أزرار لوحة تحكم المالك ------------------------
    if user_id == ADMIN_ID:
        if data == "admin_add_balance":
            query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد إضافة الرصيد له:")
            context.user_data["waiting_for_add_balance_user_id"] = True
            return

        if data == "admin_discount":
            query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد خصم الرصيد منه:")
            context.user_data["waiting_for_discount_user_id"] = True
            return

        elif data == "admin_announce":
            query.edit_message_text("أرسل الآن الرسالة أو الوسائط للإعلان لجميع المستخدمين:")
            context.user_data["waiting_for_broadcast"] = True
            return

        elif data == "admin_users_count":
            users = get_all_users()
            count_users = len(users)
            text_msg = f"عدد المستخدمين: {count_users}\n\n"
            for i, usr in enumerate(users, start=1):
                text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, أيدي: {usr[0]}\n"
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        elif data == "admin_users_balance":
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

        elif data == "pending_orders":
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

        elif data.startswith("process_order_"):
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
            buttons = [
                [
                    InlineKeyboardButton("تم إكمال الطلب بنجاح", callback_data=f"approve_order_{order_index}"),
                    InlineKeyboardButton("تم رفض الطلب", callback_data=f"reject_order_{order_index}")
                ],
                [InlineKeyboardButton("رجوع", callback_data="pending_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))

        elif data.startswith("approve_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_orders.pop(order_index)
            context.bot.send_message(chat_id=order_info['user_id'], text="تم إكمال طلبك بنجاح.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_orders")]]
            query.edit_message_text("تم تأكيد إكمال الطلب وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))

        elif data.startswith("reject_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_orders.pop(order_index)
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="تم رفض الطلب، وتمت إعادة الرصيد إلى حسابك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_orders")]]
            query.edit_message_text("تم رفض الطلب وإعادة الرصيد للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))

        elif data == "pending_cards":
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

        elif data.startswith("process_card_"):
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
            buttons = [
                [
                    InlineKeyboardButton("إظهار الرقم", callback_data=f"show_card_{card_index}"),
                ],
                [
                    InlineKeyboardButton("قبول الكارت", callback_data=f"approve_card_{card_index}"),
                    InlineKeyboardButton("رفض الكارت", callback_data=f"reject_card_{card_index}")
                ],
                [InlineKeyboardButton("رجوع", callback_data="pending_cards")]
            ]
            query.edit_message_text(text_msg,
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    parse_mode="Markdown")

        elif data.startswith("show_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            query.message.reply_text(
                text=f"رقم الكارت:\n`{card_info['card_number']}`\n"
                     "اضغط مطوّلاً على الرقم لنسخه.",
                parse_mode="Markdown"
            )
            query.answer()

        elif data.startswith("approve_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]
            query.edit_message_text("أرسل الآن المبلغ المراد شحنه للمستخدم:", reply_markup=InlineKeyboardMarkup(btns))
            context.user_data["card_to_approve"] = card_info
            context.user_data["card_to_approve_index"] = card_index
            context.user_data["waiting_for_amount"] = True

        elif data.startswith("reject_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards.pop(card_index)
            context.bot.send_message(chat_id=card_info["user_id"], text="تم رفض الشحن لأن رقم الكارت غير صحيح.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]
            query.edit_message_text("تم رفض الكارت بنجاح.", reply_markup=InlineKeyboardMarkup(btns))

        # زر "طلبات الشدات المعلقه" الخاصة بشحن شدات ببجي
        elif data == "pending_pubg_orders":
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

        elif data.startswith("process_pubg_order_"):
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
            buttons = [
                [
                    InlineKeyboardButton("تم شحن الشدات", callback_data=f"approve_pubg_order_{order_index}"),
                    InlineKeyboardButton("تم الغاء شحن الشدات", callback_data=f"reject_pubg_order_{order_index}")
                ],
                [InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))

        elif data.startswith("approve_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders.pop(order_index)
            context.bot.send_message(chat_id=order_info['user_id'], text="تم شحن شدات ببجي بنجاح.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]
            query.edit_message_text("تم شحن شدات ببجي وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup(btns))

        elif data.startswith("reject_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders.pop(order_index)
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ إلى حسابك.")
            btns = [[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]
            query.edit_message_text("تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ للمستخدم.", reply_markup=InlineKeyboardMarkup(btns))

    # ------------------------ أزرار المستخدم العادي ------------------------
    else:
        if data == "show_services":
            sections_buttons = [
                [InlineKeyboardButton("قسم المتابعين", callback_data="show_followers")],
                [InlineKeyboardButton("قسم اللايكات", callback_data="show_likes")],
                [InlineKeyboardButton("قسم المشاهدات", callback_data="show_views")],
                [InlineKeyboardButton("قسم مشاهدات البث المباشر", callback_data="show_live_views")],
                [InlineKeyboardButton("قسم شحن شدات ببجي", callback_data="show_pubg")],
                [InlineKeyboardButton("رجوع", callback_data="back_main")]
            ]
            query.edit_message_text("اختر القسم:", reply_markup=InlineKeyboardMarkup(sections_buttons))

        elif data == "show_followers":
            followers_services = {k: v for k, v in services_dict.items() if "متابعين" in k}
            service_buttons = []
            row = []
            for service_name, price in followers_services.items():
                btn_text = f"{service_name} - {price}$"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}"))
                if len(row) == 2:
                    service_buttons.append(row)
                    row = []
            if row:
                service_buttons.append(row)
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))

        elif data == "show_likes":
            likes_services = {k: v for k, v in services_dict.items() if "لايكات" in k}
            service_buttons = []
            row = []
            for service_name, price in likes_services.items():
                btn_text = f"{service_name} - {price}$"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}"))
                if len(row) == 2:
                    service_buttons.append(row)
                    row = []
            if row:
                service_buttons.append(row)
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))

        elif data == "show_views":
            views_services = {}
            for k, v in services_dict.items():
                if "مشاهدات تيكتوك " in k or "مشاهدات انستغرام " in k:
                    views_services[k] = v

            service_buttons = []
            row = []
            for service_name, price in views_services.items():
                btn_text = f"{service_name} - {price}$"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}"))
                if len(row) == 2:
                    service_buttons.append(row)
                    row = []
            if row:
                service_buttons.append(row)
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))

        elif data == "show_live_views":
            live_views_services = {k: v for k, v in services_dict.items() if "مشاهدات بث" in k}
            service_buttons = []
            row = []
            for service_name, price in live_views_services.items():
                btn_text = f"{service_name} - {price}$"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"service_{service_name}"))
                if len(row) == 2:
                    service_buttons.append(row)
                    row = []
            if row:
                service_buttons.append(row)
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))

        # قسم شحن شدات ببجي
        elif data == "show_pubg":
            service_buttons = []
            row = []
            for service_name, price in pubg_services.items():
                btn_text = f"{service_name} - {price}$"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"pubg_service_{service_name}"))
                if len(row) == 2:
                    service_buttons.append(row)
                    row = []
            if row:
                service_buttons.append(row)
            service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
            query.edit_message_text("اختر خدمة شحن شدات ببجي:", reply_markup=InlineKeyboardMarkup(service_buttons))

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

        # --------------------- التعديل الأساسي: فحص الرصيد في الخدمات العامة ---------------------
        elif data.startswith("service_"):
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

        elif data == "show_balance":
            balance = users_balance.get(user_id, 0.0)
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="back_main")]
            ]
            query.edit_message_text(f"رصيدك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(buttons))

        elif data == "charge_asiacell":
            query.edit_message_text("أرسل رقم الكارت المكون من 16 رقم:")
            context.user_data["waiting_for_card"] = True

# ------------------------------------------------
# 8) التعامل مع **كل الرسائل** (نص/صورة/فيديو...)  بعد التعديل
# ------------------------------------------------
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # في حال كان المالك يرسل رسالة للنشر العام (Broadcast)
    if context.user_data.get("waiting_for_broadcast") and user_id == ADMIN_ID:
        context.user_data["waiting_for_broadcast"] = False
        
        msg = update.message
        all_users = get_all_users()
        sent_count = 0
        for usr in all_users:
            target_id = usr[0]
            if target_id == ADMIN_ID:
                continue

            if msg.photo:
                photo_id = msg.photo[-1].file_id
                caption = msg.caption or ""
                context.bot.send_photo(chat_id=target_id, photo=photo_id, caption=caption)
            elif msg.video:
                context.bot.send_video(chat_id=target_id, video=msg.video.file_id, caption=msg.caption or "")
            elif msg.sticker:
                context.bot.send_sticker(chat_id=target_id, sticker=msg.sticker.file_id)
            elif msg.document:
                context.bot.send_document(chat_id=target_id, document=msg.document.file_id, caption=msg.caption or "")
            elif msg.animation:
                context.bot.send_animation(chat_id=target_id, animation=msg.animation.file_id, caption=msg.caption or "")
            elif msg.text:
                context.bot.send_message(chat_id=target_id, text=msg.text)
            else:
                pass

            sent_count += 1

        update.message.reply_text(f"تم إرسال الإعلان إلى {sent_count} مستخدم.")
        return

    # معالجة طلب خدمة عامة (غير شدات ببجي)
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

        new_order = {
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "link": text
        }
        pending_orders.append(new_order)

        update.message.reply_text(
            "تم تأكيد طلبك وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند إتمام الطلب أو رفضه."
        )
        context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب رشق جديد في الطلبات المعلقة.")
        return

    # معالجة طلب شحن شدات ببجي
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

        update.message.reply_text(
            "تم تأكيد طلب شحن شدات ببجي وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند شحن الشدات أو إلغائها."
        )
        context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن شدات في قسم الشدات المعلقه")
        return

    # معالجة رقم الكارت لشحن الرصيد
    if context.user_data.get("waiting_for_card"):
        text = update.message.text
        if text and len(text) == 16 and text.isdigit():
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
            update.message.reply_text("الرقم المدخل غير صحيح. تأكّد أنه مكوّن من 16 رقم.")
        return

    # معالجة إضافة الرصيد (admin_add_balance)
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
            update.message.reply_text(
                f"تم العثور على المستخدم: {row[1]} (@{row[2]})\n" +
                "أرسل الآن المبلغ المراد إضافته إلى رصيده:"
            )
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

            update.message.reply_text(
                f"تم إضافة {amount_to_add}$ إلى رصيد المستخدم.\n" +
                f"الرصيد الجديد للمستخدم: {new_balance}$"
            )
            context.bot.send_message(
                chat_id=target_user_id,
                text=f"تم إضافة {amount_to_add}$ إلى رصيدك بواسطة الإدارة.\nرصيدك الحالي: {new_balance}$"
            )
        except ValueError:
            update.message.reply_text("الرجاء إدخال مبلغ صحيح (رقم).")
        return

    # معالجة خصم الرصيد (admin_discount)
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
            update.message.reply_text(
                f"تم العثور على المستخدم: {row[1]} (@{row[2]})\n" +
                "أرسل الآن المبلغ المراد خصمه من رصيده:"
            )
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

                update.message.reply_text(
                    f"تم خصم {amount_to_discount}$ من رصيد المستخدم بنجاح.\n" +
                    f"الرصيد الجديد للمستخدم: {new_balance}$"
                )
                context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"تم خصم {amount_to_discount}$ من رصيدك بواسطة الإدارة.\nرصيدك الحالي: {new_balance}$"
                )
            else:
                update.message.reply_text(
                    f"رصيد المستخدم ({current_balance}$) لا يكفي لخصم {amount_to_discount}$.\n" +
                    "يمكنك خصم مبلغ أقل أو طلب شحن إضافي للمستخدم."
                )
        except ValueError:
            update.message.reply_text("الرجاء إدخال مبلغ صحيح (رقم).")
        return

    # معالجة شحن الكروت (admin approve card)
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

            update.message.reply_text(
                f"تم شحن رصيد المستخدم بمبلغ {amount}.\nوإبلاغه بذلك."
            )
            context.bot.send_message(
                chat_id=card_info["user_id"],
                text=f"تم شحن رصيدك بقيمة {amount}$. شكراً لاستخدامك خدمتنا."
            )
        except ValueError:
            update.message.reply_text("الرجاء إدخال مبلغ شحن صالح (رقم).")
        return

# ------------------------------------------------
# 9) الدالة الرئيسية لتشغيل البوت
# ------------------------------------------------
def main():
    TOKEN = "8138615524:AAEZGgBRMSzLxxC7F6NquT4dbmk5vA-2w4M"  # ضع توكن بوتك هنا
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_messages))

    updater.start_polling()
    updater.idle()

# ------------------------------------------------
# 10) تشغيل الملف
# ------------------------------------------------
if __name__ == "__main__":
    main()