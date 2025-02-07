#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ------------------------------------------------
# 1) الإعدادات العامة والمتغيّرات
# ------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 7655504656  # غيّر الرقم إلى آيدي المالك

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
pending_pubg_orders = []  # قائمة طلبات شدات ببجي المعلقة

# ------------------------------------------------
# 2) إعداد قاعدة بيانات SQLite
# ------------------------------------------------
DB_FILE = "bot_database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
    -- سيتم إضافة الأعمدة الأخرى بواسطة ALTER TABLE لاحقاً
)
"""
)
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
def get_user_from_db(user_id: int):
    cursor.execute(
        "SELECT user_id, full_name, username, balance FROM users WHERE user_id=?",
        (user_id,),
    )
    return cursor.fetchone()

def add_user_to_db(user_id: int, full_name: str, username: str):
    row = get_user_from_db(user_id)
    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, full_name, username, balance) VALUES (?, ?, ?, ?)",
            (user_id, full_name, username, 0.0),
        )
        conn.commit()

def update_user_balance_in_db(user_id: int, balance: float):
    cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (balance, user_id))
    conn.commit()

def update_username_in_db(user_id: int, username: str):
    cursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT user_id, full_name, username, balance FROM users")
    return cursor.fetchall()

def get_users_with_balance_desc():
    cursor.execute(
        "SELECT user_id, full_name, username, balance FROM users WHERE balance > 0 ORDER BY balance DESC"
    )
    return cursor.fetchall()

# ------------------------------------------------
# 4) مزامنة الرصيد بين dict و DB
# ------------------------------------------------
def sync_balance_from_db(user_id: int):
    row = get_user_from_db(user_id)
    if row:
        users_balance[user_id] = row[3]
    else:
        users_balance[user_id] = users_balance.get(user_id, 0.0)

def sync_balance_to_db(user_id: int):
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
def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    if user_id == ADMIN_ID:
        buttons = [[InlineKeyboardButton("لوحة تحكم المالك", callback_data="admin_menu")]]
    else:
        buttons = [
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
        ]
    return InlineKeyboardMarkup(buttons)

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards"),
            InlineKeyboardButton("الطلبات المعلقة", callback_data="pending_orders"),
        ],
        [
            InlineKeyboardButton("اعلان البوت", callback_data="admin_announce"),
            InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"),
        ],
        [
            InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance"),
            InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount"),
        ],
        [InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance")],
        [InlineKeyboardButton("طلبات الشدات المعلقه", callback_data="pending_pubg_orders")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)

# ------------------------------------------------
# 6) أوامر البوت
# ------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    add_user_to_db(user_id, full_name, username)
    update_username_in_db(user_id, username)
    sync_balance_from_db(user_id)
    text = "مرحباً بك في البوت!"
    reply_markup = main_menu_keyboard(user_id)
    await update.message.reply_text(text, reply_markup=reply_markup)

# ------------------------------------------------
# 7) التعامل مع ضغط الأزرار
# ------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    # زر الرجوع للقائمة الرئيسية
    if data == "back_main":
        await query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return

    # دخول لوحة المالك
    if data == "admin_menu":
        if user_id == ADMIN_ID:
            await query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            await query.edit_message_text("عذراً، أنت لست المالك.")
        return

    # ------------------------ أوامر لوحة تحكم المالك ------------------------
    if user_id == ADMIN_ID:
        if data == "admin_add_balance":
            await query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد إضافة الرصيد له:")
            context.user_data["waiting_for_add_balance_user_id"] = True
            return

        if data == "admin_discount":
            await query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد خصم الرصيد منه:")
            context.user_data["waiting_for_discount_user_id"] = True
            return

        elif data == "admin_announce":
            await query.edit_message_text("أرسل الآن الرسالة أو الوسائط للإعلان لجميع المستخدمين:")
            context.user_data["waiting_for_broadcast"] = True
            return

        elif data == "admin_users_count":
            users = get_all_users()
            count_users = len(users)
            text_msg = f"عدد المستخدمين: {count_users}\n\n"
            i = 1
            for usr in users:
                text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, أيدي: {usr[0]}\n"
                i += 1
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
            await query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        elif data == "admin_users_balance":
            users = get_users_with_balance_desc()
            if not users:
                text_msg = "لا يوجد مستخدمون لديهم رصيد > 0."
            else:
                text_msg = "مستخدمو البوت (رصيد > 0) - ترتيب تنازلي:\n\n"
                i = 1
                for usr in users:
                    text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, الرصيد: {usr[3]}$, أيدي: {usr[0]}\n"
                    i += 1
            btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
            await query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        # باقي أوامر لوحة تحكم المالك (الطلبات، الكروت، شدات ببجي، إلخ)
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
                [InlineKeyboardButton("رجوع", callback_data="pending_orders")],
            ]
            await query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
        # باقي فروع لوحة تحكم المالك (approve_order, reject_order, pending_cards, process_card, ... إلخ)
        # يمكنك استكمالها بنفس النمط مع استخدام await

    # ------------------------ أوامر المستخدم العادي ------------------------
    else:
        if data == "show_services":
            sections_buttons = [
                [InlineKeyboardButton("قسم المتابعين", callback_data="show_followers")],
                [InlineKeyboardButton("قسم اللايكات", callback_data="show_likes")],
                [InlineKeyboardButton("قسم المشاهدات", callback_data="show_views")],
                [InlineKeyboardButton("قسم مشاهدات البث المباشر", callback_data="show_live_views")],
                [InlineKeyboardButton("قسم شحن شدات ببجي", callback_data="show_pubg")],
                [InlineKeyboardButton("رجوع", callback_data="back_main")],
            ]
            await query.edit_message_text("اختر القسم:", reply_markup=InlineKeyboardMarkup(sections_buttons))
        elif data.startswith("service_"):
            service_name = data[len("service_"):]
            price = services_dict.get(service_name, 0)
            # فحص الرصيد أولاً
            if users_balance.get(user_id, 0) < price:
                buttons = [
                    [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                    [InlineKeyboardButton("رجوع", callback_data="show_services")],
                ]
                await query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
                return
            context.user_data["selected_service"] = service_name
            context.user_data["service_price"] = price
            await query.edit_message_text(f"لقد اخترت الخدمة: {service_name} - {price}$. الآن، يرجى إرسال الرابط الخاص بالخدمة:")
        elif data == "show_balance":
            balance = users_balance.get(user_id, 0.0)
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("رجوع", callback_data="back_main")],
            ]
            await query.edit_message_text(f"رصيدك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(buttons))
        elif data == "charge_asiacell":
            await query.edit_message_text("أرسل رقم الكارت المكون من 16 رقم:")
            context.user_data["waiting_for_card"] = True

# ------------------------------------------------
# 8) التعامل مع الرسائل (النصوص، الصور، إلخ)
# ------------------------------------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    # إذا كان المالك في وضع النشر (Broadcast)
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
                await context.bot.send_photo(chat_id=target_id, photo=photo_id, caption=caption)
            elif msg.video:
                await context.bot.send_video(chat_id=target_id, video=msg.video.file_id, caption=msg.caption or "")
            elif msg.sticker:
                await context.bot.send_sticker(chat_id=target_id, sticker=msg.sticker.file_id)
            elif msg.document:
                await context.bot.send_document(chat_id=target_id, document=msg.document.file_id, caption=msg.caption or "")
            elif msg.animation:
                await context.bot.send_animation(chat_id=target_id, animation=msg.animation.file_id, caption=msg.caption or "")
            elif msg.text:
                await context.bot.send_message(chat_id=target_id, text=msg.text)
            sent_count += 1
        await update.message.reply_text(f"تم إرسال الإعلان إلى {sent_count} مستخدم.")
        return

    # معالجة طلب خدمة عامة (غير شدات ببجي)
    if context.user_data.get("selected_service") and context.user_data.get("service_price"):
        text = update.message.text
        if not text:
            await update.message.reply_text("الرجاء إرسال الرابط كنص فقط.")
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
            "link": text,
        }
        pending_orders.append(new_order)
        await update.message.reply_text("تم تأكيد طلبك وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند إتمام الطلب أو رفضه.")
        await context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب رشق جديد في الطلبات المعلقة.")
        return

    # معالجة طلب شحن شدات ببجي
    if context.user_data.get("selected_pubg_service") and context.user_data.get("pubg_service_price"):
        pubg_id_text = update.message.text
        if not pubg_id_text:
            await update.message.reply_text("الرجاء إرسال الآيدي كنص فقط.")
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
            "pubg_id": pubg_id_text,  # يمكنك تعديل هذا السطر لإضافة معلومات إضافية مع الآيدي إن أردت
        }
        pending_pubg_orders.append(new_pubg_order)
        await update.message.reply_text(
            "تم تأكيد طلب شحن شدات ببجي وخصم المبلغ من رصيدك.\nسيتم إبلاغك عند شحن الشدات أو إلغائها."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن شدات في قسم الشدات المعلقه")
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
                "card_number": text,
            }
            pending_cards.append(new_card)
            await update.message.reply_text("تم استلام رقم الكارت بنجاح، سنقوم بالمراجعة قريباً.")
            await context.bot.send_message(chat_id=ADMIN_ID, text="هناك طلب شحن جديد في الكارتات المعلقة.")
        else:
            await update.message.reply_text("الرقم المدخل غير صحيح. تأكّد أنه مكوّن من 16 رقم.")
        return

    # باقي إجراءات إضافة وخصم الرصيد (admin_add_balance، admin_discount، وما إلى ذلك) تُستكمل بنفس النمط مع استخدام await
    # يمكنك استكمال باقي الفروع بنفس الأسلوب مع تحويل جميع استدعاءات context.bot.send_message أو update.message.reply_text إلى await

# ------------------------------------------------
# 9) الدالة الرئيسية لتشغيل البوت
# ------------------------------------------------
async def main() -> None:
    TOKEN = "8138615524:AAEZGgBRMSzLxxC7F6NquT4dbmk5vA-2w4M"  # استبدل هذا بتوكن البوت الخاص بك
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
