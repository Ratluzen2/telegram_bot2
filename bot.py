#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
بوت تلغرام متكامل (python-telegram-bot v13.x)
- إدارة المشرفين + خصومات للمشرف
- إصلاح شحن آسياسيل مع إشعار فوري للمالك
- زر "الطلبات المعلّقة (الخدمات)" لاعتماد/رفض الطلبات وتنفيذ الـ API
- قراءة الإعدادات من متغيّرات البيئة (Heroku Config Vars) أو القيم الافتراضية
"""

import logging
import requests
import time
import os
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)

# =========================
# إعدادات السجل (logging)
# =========================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("TG_BOT")

# =========================
# الإعدادات (Environment)
# =========================
ADMIN_ID = int(os.getenv("ADMIN_ID", "7655504656"))   # مثال: 7655504656
TOKEN = os.getenv("TOKEN", "8138615524:AAFr6m5Z4_gY0k7pdg7teD9nM8ReDC-KQKU")  # مثال: "123456:AA...."
API_KEY = os.getenv("API_KEY", "25a9ceb07be0d8b2ba88e70dcbe92e06")
API_URL = os.getenv("API_URL", "https://kd1s.com/api/v2")
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "@z396r")  # لدعم طرق الشحن الإضافية

if not TOKEN or ":" not in TOKEN:
    logger.warning("⚠️ TOKEN غير مضبوط أو غير صالح. عدّل متغير البيئة TOKEN.")

# =========================
# تعريف القواميس الخاصة بالخدمات
# =========================
service_api_mapping = {
    "متابعين تيكتوك 1k": {"service_id": 13912, "quantity_multiplier": 1000},
    "متابعين تيكتوك 2k": {"service_id": 13912, "quantity_multiplier": 2000},
    "متابعين تيكتوك 3k": {"service_id": 13912, "quantity_multiplier": 3000},
    "متابعين تيكتوك 4k": {"service_id": 13912, "quantity_multiplier": 4000},
    "مشاهدات تيكتوك 1k": {"service_id": 9447, "quantity_multiplier": 1000},
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

# الأسعار الأساسية (للمستخدمين العاديين)
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

# =========================
# المتغيرات والذاكرة
# =========================
users_balance = {}            # {user_id: balance}
pending_orders = []           # طلبات خدمات معلّقة (روابط)
pending_cards = []            # كروت شحن معلّقة
pending_pubg_orders = []      # طلبات ببجي معلّقة
completed_orders = []         # طلبات اكتملت (مع طابع زمني)
pending_itunes_orders = []    # طلبات ايتونز معلّقة
blocked_users = {}            # {user_id: True أو dict مع معلومات الحظر}

# ===== ميزة الحماية (إضافة جديدة فقط) =====
# إعدادات قابلة للتهيئة عبر البيئة
CARD_DUP_LIMIT = int(os.getenv("CARD_DUP_LIMIT", "2"))                 # يُحظر في المحاولة الثالثة لنفس الكارت
CARD_SPAM_COUNT = int(os.getenv("CARD_SPAM_COUNT", "5"))               # عدد الكروت الأقصى ضمن النافذة
CARD_SPAM_WINDOW_SECONDS = int(os.getenv("CARD_SPAM_WINDOW_SECONDS", "120"))  # نافذة الزمن بالثواني
CARD_BAN_HOURS = int(os.getenv("CARD_BAN_HOURS", "2"))                 # مدة الحظر بالساعات

# تخزين تاريخ محاولات الكروت لكل مستخدم
card_submission_history = {}  # {user_id: {"counts": {digits: count}, "times": [ts1, ts2, ...]}}

def _ban_user_for_hours(user_id: int, hours: int, reason: str):
    """حظر المستخدم لمدة محددة مع سبب."""
    until_ts = time.time() + hours * 3600
    blocked_users[user_id] = {"until": until_ts, "reason": reason}

def _remaining_human(seconds: int) -> str:
    m = max(0, int(seconds))
    h = m // 3600
    m %= 3600
    mm = m // 60
    ss = m % 60
    parts = []
    if h: parts.append(f"{h}س")
    if mm: parts.append(f"{mm}د")
    if ss and not h: parts.append(f"{ss}ث")  # نعرض الثواني فقط إذا مافي ساعات
    return " ".join(parts) or "قليل"

def _is_user_blocked_now(user_id: int) -> Optional[str]:
    """
    يعيد None إذا غير محظور، وإلا يعيد رسالة الحظر (ويفك الحظر تلقائياً إذا انتهت المدة).
    """
    if user_id == ADMIN_ID:
        return None
    info = blocked_users.get(user_id)
    if not info:
        return None
    # دعم القيمة القديمة True
    if info is True:
        return "لقد تم حضرك من استخدام البوت.\nانتظر حتى يتم الغاء حظرك."
    if isinstance(info, dict):
        until = info.get("until")
        reason = info.get("reason", "مخالفة سياسات الاستخدام.")
        if until and time.time() >= until:
            # فك الحظر تلقائياً بعد انتهاء المدة
            try:
                del blocked_users[user_id]
            except Exception:
                pass
            return None
        # مدة متبقية
        remain = int(until - time.time()) if until else 0
        return f"تم حظرك لمدة مؤقتة.\nالسبب: {reason}\nالمدة المتبقية: {_remaining_human(remain)}"
    return "لقد تم حضرك من استخدام البوت.\nانتظر حتى يتم الغاء حظرك."

def _record_and_check_card(user_id: int, digits: str) -> Optional[str]:
    """
    يسجل محاولة إدخال كارت ويعيد سبب الحظر لو وُجد، وإلا يعيد None.
    - يحظر عند تكرار نفس الكارت لأكثر من CARD_DUP_LIMIT مرة.
    - يحظر عند إرسال أكثر من CARD_SPAM_COUNT كروت خلال CARD_SPAM_WINDOW_SECONDS.
    """
    now = time.time()
    hist = card_submission_history.setdefault(user_id, {"counts": {}, "times": []})
    # عداد التكرار لنفس الكارت
    prev = hist["counts"].get(digits, 0)
    hist["counts"][digits] = prev + 1

    # طوابع زمنية لمحاولات الكروت
    hist["times"].append(now)
    cutoff = now - CARD_SPAM_WINDOW_SECONDS
    hist["times"] = [t for t in hist["times"] if t >= cutoff]

    # شرط التكرار
    if hist["counts"][digits] > CARD_DUP_LIMIT:
        return "إدخال نفس رقم كارت آسياسيل أكثر من مرتين."

    # شرط السبام ضمن النافذة
    if len(hist["times"]) > CARD_SPAM_COUNT:
        return "إرسال عدد كبير من كروت آسياسيل خلال وقت قصير."

    return None
# ===== نهاية ميزة الحماية =====

# =========================
# قاعدة البيانات Neon (PostgreSQL) عبر psycopg3
# =========================
import psycopg
from psycopg_pool import ConnectionPool
from urllib.parse import urlparse

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("NEON_DATABASE_URL")
    or os.getenv("DATABASE_URL_POOLER")
    or ""
)
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL غير مضبوط. عيّن رابط Neon (يفضّل pooler endpoint مع sslmode=require).")
    raise SystemExit(1)

# تحذير إن لم يكن endpoint الخاص بالـ pooler
try:
    _host = urlparse(DATABASE_URL).hostname or ""
    if "pooler" not in _host:
        logger.warning("⚠️ يُفضَّل استخدام Pooler endpoint من Neon لعدد اتصالات أقل وثبات أعلى.")
except Exception:
    pass

# Pool بإعدادات مهلة أوضح
pg_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,            # كافي للبوت
    max_idle=60,           # ثواني
    timeout=60,            # مهلة استعارة اتصال من الـ pool
    kwargs={
        "sslmode": "require",
        "connect_timeout": 10,  # مهلة إنشاء اتصال فعلي
    },
)

def _pool_healthcheck():
    """نتأكد أن الاتصال يعمل ونطبع السبب الحقيقي لو فشل."""
    try:
        pg_pool.wait(timeout=30)  # انتظر تهيئة الـ pool
        with pg_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح.")
    except Exception as e:
        logger.exception("❌ فشل الاتصال بقاعدة البيانات. تحقق من DATABASE_URL وNeon: %s", e)
        raise

def _exec(sql: str, params: tuple = (), fetch: str = ""):
    """تنفيذ الاستعلامات مع الالتزام. fetch: '' | 'one' | 'all'."""
    try:
        with pg_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch == "one":
                    row = cur.fetchone()
                    conn.commit()
                    return row
                if fetch == "all":
                    rows = cur.fetchall()
                    conn.commit()
                    return rows
                rc = cur.rowcount
                conn.commit()
                return rc
    except psycopg.OperationalError as e:
        logger.exception("❌ OperationalError من PostgreSQL: %s", e)
        raise
    except Exception as e:
        logger.exception("❌ DB error: %s", e)
        raise

# صحّة الاتصال قبل إنشاء الجداول
_pool_healthcheck()

# إنشاء الجداول (إن لم تكن موجودة) + الأعمدة المطلوبة
_exec("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY
)
""")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS username  TEXT")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance   REAL DEFAULT 0")

_exec("""
CREATE TABLE IF NOT EXISTS moderators (
    user_id   BIGINT PRIMARY KEY,
    full_name TEXT,
    username  TEXT
)
""")

# =========================
# دوال DB والمستخدمين
# =========================
def get_user_from_db(user_id: int):
    return _exec(
        "SELECT user_id, full_name, username, balance FROM users WHERE user_id=%s",
        (user_id,),
        fetch="one"
    )

def add_user_to_db(user_id: int, full_name: str, username: str):
    row = get_user_from_db(user_id)
    if not row:
        _exec(
            "INSERT INTO users (user_id, full_name, username, balance) VALUES (%s, %s, %s, %s)",
            (user_id, full_name, username, 0.0)
        )

def update_user_balance_in_db(user_id: int, balance: float):
    _exec("UPDATE users SET balance=%s WHERE user_id=%s", (balance, user_id))

def update_username_in_db(user_id: int, username: str):
    _exec("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))

def get_all_users():
    return _exec(
        "SELECT user_id, full_name, username, balance FROM users",
        fetch="all"
    ) or []

def get_users_with_balance_desc():
    return _exec(
        "SELECT user_id, full_name, username, balance FROM users WHERE balance > 0 ORDER BY balance DESC",
        fetch="all"
    ) or []

def sync_balance_from_db(user_id: int):
    row = get_user_from_db(user_id)
    users_balance[user_id] = row[3] if row else users_balance.get(user_id, 0.0)

def sync_balance_to_db(user_id: int):
    bal = users_balance.get(user_id, 0.0)
    row = get_user_from_db(user_id)
    if row:
        update_user_balance_in_db(user_id, bal)
    else:
        add_user_to_db(user_id, "Unknown", "NoUsername")
        update_user_balance_in_db(user_id, bal)

# =========================
# أدوات المشرفين والخصومات
# =========================
def _normalize_username(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    u = str(u).strip()
    return u[1:] if u.startswith("@") else u

def is_moderator(user_id: int) -> bool:
    row = _exec("SELECT 1 FROM moderators WHERE user_id=%s", (user_id,), fetch="one")
    return row is not None

def add_moderator(user_id: int, full_name: str, username: str):
    username = _normalize_username(username) or "NoUsername"
    _exec(
        "INSERT INTO moderators (user_id, full_name, username) VALUES (%s, %s, %s) "
        "ON CONFLICT (user_id) DO UPDATE SET full_name=EXCLUDED.full_name, username=EXCLUDED.username",
        (user_id, full_name or "Unknown", username)
    )

def remove_moderator_by_identifier(identifier: str) -> bool:
    identifier = identifier.strip()
    if identifier.isdigit():
        rc = _exec("DELETE FROM moderators WHERE user_id=%s", (int(identifier),))
    else:
        uname = _normalize_username(identifier)
        rc = _exec("DELETE FROM moderators WHERE LOWER(username)=LOWER(%s)", (uname,))
    return (rc or 0) > 0

def list_moderators():
    return _exec(
        "SELECT user_id, full_name, username FROM moderators ORDER BY user_id ASC",
        fetch="all"
    ) or []

def get_effective_price(user_id: int, service_name: str, base_price: float, kind: str = "generic") -> float:
    """
    خصومات للمشرفين فقط:
    - المتابعين/المشاهدات المباشرة/اللايكات/رفع سكور/خدمات التليجرام ⇒ *0.8
    - ايتونز/ببجي ⇒ *0.9
    """
    try:
        if not is_moderator(user_id):
            return base_price

        if kind in ("itunes", "pubg") or ("ايتونز" in service_name or "ببجي" in service_name):
            return round(float(base_price) * 0.90, 2)

        in_80 = (
            "متابعين" in service_name or
            "لايكات" in service_name or
            "مشاهدات بث" in service_name or
            "رفع سكور" in service_name or
            "نقاط تحديات" in service_name or
            kind == "telegram"
        )
        if in_80:
            return round(float(base_price) * 0.80, 2)

        return base_price
    except Exception as e:
        logger.error("get_effective_price error: %s", e)
        return base_price

# =========================
# لوحات المفاتيح (Keyboards)
# =========================
def main_menu_keyboard(user_id: int):
    if user_id == ADMIN_ID:
        return InlineKeyboardMarkup([[InlineKeyboardButton("لوحة تحكم المالك", callback_data="admin_menu")]])
    if is_moderator(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
            [InlineKeyboardButton("لوحة تحكم المشرف", callback_data="moderator_menu")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الخدمات", callback_data="show_services")],
        [InlineKeyboardButton("رصيدي", callback_data="show_balance")]
    ])

def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("الطلبات المعلّقة (الخدمات)", callback_data="pending_smm_orders")],
        [InlineKeyboardButton("إدارة المشرفين", callback_data="manage_mods")],
        [InlineKeyboardButton("حضر المستخدم", callback_data="block_user"),
         InlineKeyboardButton("الغاء حظر المستخدم", callback_data="unblock_user")],
        [InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance"),
         InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")],
        [InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"),
         InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance")],
        [InlineKeyboardButton("مراجعة الطلبات (API مكتملة)", callback_data="review_orders"),
         InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders"),
         InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")],
        [InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")],
        [InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance"),
         InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status")],
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

def tiktok_score_keyboard(user_id: int):
    score_services = {k: v for k, v in services_dict.items() if ("رفع سكور" in k or "نقاط تحديات" in k)}
    service_buttons = []
    for service_name, price in score_services.items():
        eff = get_effective_price(user_id, service_name, price, "generic")
        service_buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"service_{service_name}")])
    service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(service_buttons)

def itunes_services_keyboard(user_id: int):
    buttons = []
    for service_name, price in itunes_services.items():
        eff = get_effective_price(user_id, service_name, price, "itunes")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"itunes_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def telegram_services_keyboard(user_id: int):
    buttons = []
    for service_name, price in telegram_services.items():
        eff = get_effective_price(user_id, service_name, price, "telegram")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"telegram_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def clear_all_waiting_flags(context: CallbackContext):
    waiting_keys = [
        "waiting_for_card", "waiting_for_block", "waiting_for_add_balance_user_id",
        "waiting_for_add_balance_amount", "waiting_for_discount_user_id", "waiting_for_discount_amount",
        "waiting_for_broadcast", "waiting_for_api_order_status", "selected_service", "service_price",
        "selected_pubg_service", "pubg_service_price", "card_to_approve", "card_to_approve_index", "waiting_for_amount",
        "selected_itunes_service", "itunes_service_price", "waiting_for_itunes_confirm",
        "waiting_for_itunes_code", "itunes_to_complete", "itunes_to_complete_index",
        "selected_telegram_service", "telegram_service_price", "waiting_for_telegram_link",
        "waiting_for_new_mod", "waiting_for_remove_mod", "admin_target_id"
    ]
    for key in waiting_keys:
        context.user_data.pop(key, None)

# =========================
# نظام الإعلان (يدعم وسائط)
# =========================
def broadcast_ad(update: Update, context: CallbackContext):
    announcement_prefix = "✨ إعلان من مالك البوت ✨\n\n"
    all_users = get_all_users()
    admin_reply = "تم إرسال الإعلان لجميع المستخدمين."

    try:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            new_caption = announcement_prefix + caption
            for usr in all_users:
                try:
                    context.bot.send_photo(chat_id=usr[0], photo=file_id, caption=new_caption)
                except Exception as e:
                    logger.error("Error sending photo to %s: %s", usr[0], e)
            update.message.reply_text(admin_reply)

        elif update.message.video:
            file_id = update.message.video.file_id
            caption = update.message.caption or ""
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
            update.message.reply_text("نوع الرسالة غير مدعوم في البث.")
    except Exception as e:
        logger.error("broadcast_ad error: %s", e)
        update.message.reply_text("تعذّر إرسال البث حالياً.")

# =========================
# دالة البداية (start)
# =========================
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # تحقق الحظر (مع الفك التلقائي عند الانتهاء)
    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        update.message.reply_text(ban_msg)
        return

    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    add_user_to_db(user_id, full_name, username)
    update_username_in_db(user_id, username)
    sync_balance_from_db(user_id)

    text = "مرحباً بك في البوت!"
    reply_markup = main_menu_keyboard(user_id)
    update.message.reply_text(text, reply_markup=reply_markup)

# =========================
# فحص رصيد API
# =========================
def api_check_balance(update: Update, context: CallbackContext):
    params = {'key': API_KEY, 'action': 'balance'}
    try:
        response = requests.post(API_URL, data=params, timeout=20)
        balance_info = response.json()
        if "balance" in balance_info:
            text_msg = f"رصيد حسابك في API: {balance_info['balance']}$"
        else:
            text_msg = f"حدث خطأ في جلب الرصيد من API: {balance_info.get('error', 'غير معروف')}"
    except Exception:
        text_msg = "فشل الاتصال بالـ API."

    if update.callback_query:
        btns = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
        update.callback_query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
    else:
        update.message.reply_text(text_msg)

# =========================
# تنفيذ الطلب عبر API عند الموافقة
# =========================
def approve_order_process(order_index: int, context: CallbackContext, query):
    try:
        order_info = pending_orders.pop(order_index)
    except IndexError:
        query.answer("الطلب غير موجود.", show_alert=True)
        return

    if order_info['service'] in service_api_mapping:
        mapping = service_api_mapping[order_info['service']]
        params = {
            'key': API_KEY,
            'action': 'add',
            'service': mapping['service_id'],
            'link': order_info['link'],
            'quantity': mapping['quantity_multiplier']
        }
        try:
            response = requests.post(API_URL, data=params, timeout=25)
            api_response = response.json()
        except Exception:
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
            query.edit_message_text("تم تنفيذ الطلب عبر API وإشعار المستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
        else:
            users_balance[order_info['user_id']] = users_balance.get(order_info['user_id'], 0.0) + order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
    else:
        order_info["order_number"] = "N/A"
        order_info["service_number"] = "N/A"
        order_info["refunded"] = False
        order_info["completed_at"] = time.time()
        completed_orders.append(order_info)
        context.bot.send_message(chat_id=order_info['user_id'], text="تم إكمال طلبك بنجاح.")
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))

# =========================
# أزرار (Callback) الهاندلر
# =========================
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    clear_all_waiting_flags(context)

    # تحقق الحظر (مع الفك التلقائي عند الانتهاء)
    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        query.answer(ban_msg, show_alert=True)
        return

    if data == "back_main":
        query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return

    if data == "show_services":
        query.edit_message_text("اختر القسم:", reply_markup=services_menu_keyboard())
        return

    # ======= عرض الأقسام بأسعار (مع خصومات المشرف إن وُجد) =======
    if data == "show_followers":
        followers_services = {k: v for k, v in services_dict.items() if "متابعين" in k}
        service_buttons = []
        for name, price in followers_services.items():
            eff = get_effective_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_likes":
        likes_services = {k: v for k, v in services_dict.items() if "لايكات" in k}
        service_buttons = []
        for name, price in likes_services.items():
            eff = get_effective_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_views":
        views_services = {k: v for k, v in services_dict.items() if "مشاهدات تيكتوك" in k أو "مشاهدات انستغرام" in k}
        service_buttons = []
        for name, price in views_services.items():
            eff = get_effective_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_live_views":
        # ✅ إصلاح: استخدام in بدل "في"
        live_views_services = {k: v for k, v in services_dict.items() if "مشاهدات بث" in k}
        service_buttons = []
        for name, price in live_views_services.items():
            eff = get_effective_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_tiktok_score":
        query.edit_message_text("اختر خدمة رفع سكور تيكتوك المطلوبة:", reply_markup=tiktok_score_keyboard(user_id))
        return

    if data == "show_itunes_services":
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=itunes_services_keyboard(user_id))
        return

    if data == "show_telegram_services":
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=telegram_services_keyboard(user_id))
        return

    if data == "show_pubg":
        service_buttons = []
        for name, base_price in pubg_services.items():
            eff = get_effective_price(user_id, name, base_price, "pubg")
            service_buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"pubg_service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر خدمة شحن شدات ببجي:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    # اختيار خدمة عامة
    if data.startswith("service_"):
        service_name = data[len("service_"):]
        base_price = services_dict.get(service_name)
        if base_price is None:
            query.edit_message_text("الخدمة غير موجودة.")
            return
        price = get_effective_price(user_id, service_name, base_price, "generic")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
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
        elif "رفع سكور بث" in service_name:
            message_text = (
                "يرجى ارسال رابط البث الخاص بك\n"
                "🔴تنبيه: يرجى ارسال رابط البث وليس اليوزرنيم!!"
            )
        elif "تيكتوك" in service_name:
            message_text = (
                "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:\n"
                "🔴ملاحظة: ارسل الرابط وليس اليوزرنيم!"
            )
        else:
            message_text = "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:"

        context.user_data["selected_service"] = service_name
        context.user_data["service_price"] = price
        query.edit_message_text(message_text)
        return

    # اختيار خدمة ببجي
    if data.startswith("pubg_service_"):
        name = data[len("pubg_service_"):]
        base_price = pubg_services.get(name, 0)
        price = get_effective_price(user_id, name, base_price, "pubg")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("رجوع", callback_data="show_pubg")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_pubg_service"] = name
        context.user_data["pubg_service_price"] = price
        query.edit_message_text("ارسل الايدي الخاص بك:")
        return

    # اختيار خدمة ايتونز
    if data.startswith("itunes_service_"):
        service_name = data[len("itunes_service_"):]
        base_price = itunes_services.get(service_name, 0)
        price = get_effective_price(user_id, service_name, base_price, "itunes")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("رجوع", callback_data="show_itunes_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_itunes_service"] = service_name
        context.user_data["itunes_service_price"] = price
        query.edit_message_text(f"تم اختيار الخدمة: {service_name}\n\nارسل رقم 1 لتأكيد طلبك")
        context.user_data["waiting_for_itunes_confirm"] = True
        return

    # اختيار خدمة تلغرام
    if data.startswith("telegram_service_"):
        service_name = data[len("telegram_service_"):]
        base_price = telegram_services.get(service_name, 0)
        price = get_effective_price(user_id, service_name, base_price, "telegram")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
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

    # عرض الرصيد
    if data == "show_balance":
        balance = users_balance.get(user_id, 0.0)
        buttons = [
            [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
            [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
            [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
            [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
            [InlineKeyboardButton("رجوع", callback_data="back_main")]
        ]
        query.edit_message_text(f"رصيدك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # شحن عبر آسياسيل (المنطق الأصلي)
    if data == "charge_asiacell":
        context.user_data["waiting_for_card"] = True
        query.edit_message_text("أرسل رقم الكارت المكون من 14 أو 16 رقم (يمكنك لصقه كما هو):")
        return

    # شحن عبر طرق أخرى (سوبركي / زين كاش / USDT): رسالة توجّه للدعم
    if data in ("charge_superkey", "charge_zaincash", "charge_usdt"):
        msg = f"لإتمام عملية الشحن تواصل مع الدعم الفني عبر الضغط هنا👈🏻 {SUPPORT_CONTACT}"
        query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="back_main")]])
        )
        return

    # ========== لوحة المالك ==========
    if data == "admin_menu":
        if user_id == ADMIN_ID:
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return

    if user_id == ADMIN_ID:
        # قائمة الطلبات المعلّقة (الخدمات)
        if data == "pending_smm_orders":
            if not pending_orders:
                query.edit_message_text(
                    "لا توجد طلبات خدمات معلّقة حالياً.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]])
                )
            else:
                text_msg = "الطلبات المعلّقة (الخدمات):\n\n"
                kb = []
                for idx, o in enumerate(pending_orders):
                    text_msg += (f"{idx+1}) {o['full_name']} (@{o['username']})\n"
                                 f"   الخدمة: {o['service']} | السعر: {o['price']}$\n"
                                 f"   الرابط: {o['link']}\n\n")
                    kb.append([
                        InlineKeyboardButton(f"✅ تنفيذ {idx+1}", callback_data=f"approve_smm_{idx}"),
                        InlineKeyboardButton(f"❌ رفض {idx+1}", callback_data=f"reject_smm_{idx}")
                    ])
                kb.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(kb))
            return

        if data.startswith("approve_smm_"):
            try:
                order_index = int(data.split("_")[-1])
            except Exception:
                query.answer("رقم طلب غير صالح.", show_alert=True)
                return
            approve_order_process(order_index, context, query)
            return

        if data.startswith("reject_smm_"):
            try:
                order_index = int(data.split("_")[-1])
                order_info = pending_orders.pop(order_index)
            except Exception:
                query.answer("تعذر إيجاد الطلب.", show_alert=True)
                return
            users_balance[order_info['user_id']] = users_balance.get(order_info['user_id'], 0.0) + float(order_info['price'])
            sync_balance_to_db(order_info['user_id'])
            try:
                context.bot.send_message(chat_id=order_info['user_id'], text="تم إلغاء طلبك وإعادة المبلغ إلى رصيدك.")
            except Exception:
                pass
            query.edit_message_text("تم رفض الطلب وإرجاع الرصيد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_smm_orders")]]))
            return

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
                for uid in list(blocked_users.keys()):
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
            text_msg = f"عدد المستخدمين: {len(users)}\n\n"
            for i, usr in enumerate(users, start=1):
                text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, أيدي: {usr[0]}\n"
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            return

        if data == "admin_users_balance":
            users = get_users_with_balance_desc()
            if not users:
                text_msg = "لا يوجد مستخدمون لديهم رصيد > 0."
            else:
                text_msg = "مستخدمو البوت (رصيد > 0) - ترتيب تنازلي:\n\n"
                for i, usr in enumerate(users, start=1):
                    text_msg += f"{i}) الاسم: {usr[1]}, يوزر: @{usr[2]}, الرصيد: {usr[3]}$, أيدي: {usr[0]}\n"
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            return

        # الطلبات المكتملة عبر API
        if data == "review_orders":
            filtered = [(i, o) for i, o in enumerate(completed_orders) if o.get("order_number", "N/A") != "N/A"]
            if not filtered:
                query.edit_message_text("لا توجد طلبات تم تنفيذها عبر API.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
                return
            keyboard = []
            text_msg = ""
            for orig_idx, order in filtered:
                text_msg += f"- الاسم: {order['full_name']}، الخدمة: {order['service']}، السعر: {order['price']}$، رقم الطلب: {order.get('order_number', 'N/A')}\n\n"
                keyboard.append([InlineKeyboardButton("اشعار المستخدم", callback_data=f"notify_order_{orig_idx}")])
                keyboard.append([InlineKeyboardButton("ارجاع الرصيد", callback_data=f"refund_order_{orig_idx}")])
            keyboard.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith("notify_order_"):
            try:
                order_index = int(data.split("_")[-1])
                order = completed_orders[order_index]
            except Exception:
                query.answer("خطأ في بيانات الطلب", show_alert=True)
                return
            context.bot.send_message(chat_id=order['user_id'], text="تم تنفيذ طلبك بنجاح")
            query.answer("تم إرسال إشعار للمستخدم", show_alert=True)
            return

        if data.startswith("refund_order_"):
            try:
                order_index = int(data.split("_")[-1])
                order = completed_orders[order_index]
            except Exception:
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
            query.edit_message_text("تمت العملية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            return

        # إدارة كروت الشحن
        if data == "pending_cards":
            if not pending_cards:
                query.edit_message_text("لا توجد كروت معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
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
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        if data.startswith("show_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            query.message.reply_text(text=f"رقم الكارت:\n`{card_info['card_number']}`\n(اضغط مطولاً للنسخ)", parse_mode="Markdown")
            return

        if data.startswith("approve_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards[card_index]
            query.edit_message_text("أرسل الآن المبلغ المراد شحنه للمستخدم (بالدولار):",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]))
            context.user_data["card_to_approve"] = card_info
            context.user_data["card_to_approve_index"] = card_index
            context.user_data["waiting_for_amount"] = True
            return

        if data.startswith("reject_card_"):
            card_index = int(data.split("_")[-1])
            card_info = pending_cards.pop(card_index)
            context.bot.send_message(chat_id=card_info["user_id"], text="تم رفض الشحن لأن رقم الكارت غير صحيح.")
            query.edit_message_text("تم رفض الكارت بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]))
            return

        # طلبات ببجي
        if data == "pending_pubg_orders":
            if not pending_pubg_orders:
                query.edit_message_text("لا توجد طلبات شدات ببجي معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
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
            query.edit_message_text("تم شحن شدات ببجي وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]))
            return

        if data.startswith("reject_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders.pop(order_index)
            users_balance[order_info['user_id']] += order_info['price']
            sync_balance_to_db(order_info['user_id'])
            context.bot.send_message(chat_id=order_info['user_id'], text="تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ إلى حسابك.")
            query.edit_message_text("تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ للمستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]))
            return

        if data.startswith("user_wait_pubg_order_"):
            order_index = int(data.split("_")[-1])
            order_info = pending_pubg_orders[order_index]
            context.bot.send_message(chat_id=order_info['user_id'], text="سوف يتم تنفيذ طلبك قريبا")
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]))
            return

        if data == "api_check_balance":
            api_check_balance(update, context)
            return

        if data == "api_order_status":
            query.edit_message_text("أدخل رقم الطلب للتحقق من حالته عبر API:")
            context.user_data["waiting_for_api_order_status"] = True
            return

        # طلبات ايتونز
        if data == "pending_itunes_orders":
            if not pending_itunes_orders:
                query.edit_message_text("لا توجد طلبات شحن ايتونز معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
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
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]))
            return

        if data.startswith("itunes_complete_"):
            itunes_index = int(data.split("_")[-1])
            itunes_order = pending_itunes_orders[itunes_index]
            query.edit_message_text("أرسل الآن كود الهدايا الايتونز:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]))
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
            query.edit_message_text("تم إلغاء طلب شحن الايتونز وإعادة المبلغ للمستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]))
            return

        # إدارة المشرفين
        if data == "manage_mods":
            query.edit_message_text("إدارة المشرفين:", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_mod")],
                [InlineKeyboardButton("➖ حذف مشرف", callback_data="remove_mod")],
                [InlineKeyboardButton("👥 عرض المشرفين", callback_data="list_mods")],
                [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
            ]))
            return

        if data == "add_mod":
            query.edit_message_text("أرسل الآن آيدي المستخدم أو يوزر @username لإضافته كمشرف:")
            context.user_data["waiting_for_new_mod"] = True
            return

        if data == "remove_mod":
            query.edit_message_text("أرسل الآن آيدي المستخدم أو يوزر @username لحذفه من المشرفين:")
            context.user_data["waiting_for_remove_mod"] = True
            return

        if data == "list_mods":
            mods = list_moderators()
            if not mods:
                query.edit_message_text("لا يوجد مشرفون حالياً.", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_mod")],
                    [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
                ]))
                return
            txt = f"👥 عدد المشرفين: {len(mods)}\n\n"
            for i, (mid, fn, un) in enumerate(mods, start=1):
                txt += f"{i}) {fn} (@{un}) - ID: {mid}\n"
            query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="manage_mods")]]))
            return

    # ========== لوحة المشرف ==========
    if data == "moderator_menu":
        if is_moderator(user_id):
            query.edit_message_text("لوحة تحكم المشرف:", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("مراجعة الطلبات المعلقة", callback_data="mod_review_pending")],
                [InlineKeyboardButton("إحصائيات الطلبات", callback_data="mod_stats")],
                [InlineKeyboardButton("شرح الخصومات", callback_data="mod_discounts_info")],
                [InlineKeyboardButton("رجوع", callback_data="back_main")],
            ]))
        else:
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط.")
        return

    if data == "mod_review_pending":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط.")
            return
        pend = len(pending_orders) + len(pending_pubg_orders) + len(pending_cards) + len(pending_itunes_orders)
        txt = (
            "📮 الطلبات المعلقة:\n"
            f"- إجمالي المعلّقة: {pend}\n"
            f"- العادية: {len(pending_orders)}\n"
            f"- شدات ببجي: {len(pending_pubg_orders)}\n"
            f"- كروت الشحن: {len(pending_cards)}\n"
            f"- الايتونز: {len(pending_itunes_orders)}\n\n"
            "يمكنك إشعار المالك الآن لمراجعتها."
        )
        kb = [[InlineKeyboardButton("🔔 إشعار المالك بالمراجعة", callback_data="mod_ping_owner")],
              [InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]
        query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "mod_ping_owner":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط.")
            return
        pend = len(pending_orders) + len(pending_pubg_orders) + len(pending_cards) + len(pending_itunes_orders)
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔔 إشعار من أحد المشرفين لمراجعة الطلبات المعلقة.\n"
                    f"المشرف: {update.effective_user.full_name} (@{update.effective_user.username or 'NoUsername'})\n"
                    f"إجمالي المعلّقة الآن: {pend}\n"
                    f"- العادية: {len(pending_orders)}, ببجي: {len(pending_pubg_orders)}, الكروت: {len(pending_cards)}, الايتونز: {len(pending_itunes_orders)}"
                )
            )
            query.edit_message_text("تم إشعار المالك. شكراً لك.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع", callback_data="moderator_menu")]
            ]))
        except Exception as e:
            logger.error("mod_ping_owner error: %s", e)
            query.edit_message_text("تعذر إشعار المالك حالياً.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع", callback_data="moderator_menu")]
            ]))
        return

    if data == "mod_stats":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط.")
            return
        completed = len(completed_orders)
        ongoing = sum(1 for o in completed_orders if o.get("order_number", "N/A") != "N/A" and not o.get("refunded"))
        pending_total = len(pending_orders) + len(pending_pubg_orders) + len(pending_cards) + len(pending_itunes_orders)
        canceled_est = sum(1 for o in completed_orders if o.get("refunded"))
        txt = (
            "📊 إحصائيات الطلبات:\n"
            f"- مكتملة: {completed}\n"
            f"- جارية: {ongoing}\n"
            f"- معلّقة: {pending_total}\n"
            f"- ملغاة/مسترجعة: {canceled_est}"
        )
        query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]))
        return

    if data == "mod_discounts_info":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط.")
            return
        txt = (
            "💡 خصومات المشرف:\n"
            "• المتابعين/اللايكات/مشاهدات البث/رفع سكور تيكتوك/خدمات التليجرام ⇒ ×0.8\n"
            "• شراء رصيد ايتونز/شدات ببجي ⇒ ×0.9\n"
            "تُطبق الخصومات تلقائياً عند عرض الأسعار والخصم من الرصيد، ولا تؤثر على أسعار المستخدمين العاديين."
        )
        query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]))
        return

# =========================
# استقبال الرسائل (Message)
# =========================
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # تحقق الحظر (مع الفك التلقائي عند الانتهاء)
    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        update.message.reply_text(ban_msg)
        return

    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    text = update.message.text or ""

    # --- أوضاع المالك ---
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_add_balance_user_id"):
        target_input = text.strip()
        try:
            target_id = int(target_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == (_normalize_username(target_input) or "").lower():
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
            amount = float(text.strip())
        except ValueError:
            update.message.reply_text("الرجاء إرسال مبلغ صالح.")
            return
        target_id = context.user_data.get("admin_target_id")
        users_balance[target_id] = users_balance.get(target_id, 0.0) + amount
        sync_balance_to_db(target_id)
        update.message.reply_text(f"تم إضافة {amount}$ لآيدي {target_id}.")
        clear_all_waiting_flags(context)
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_discount_user_id"):
        target_input = text.strip()
        try:
            target_id = int(target_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == (_normalize_username(target_input) or "").lower():
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
            amount = float(text.strip())
        except ValueError:
            update.message.reply_text("الرجاء إرسال مبلغ صالح.")
            return
        target_id = context.user_data.get("admin_target_id")
        current = users_balance.get(target_id, 0.0)
        if current < amount:
            update.message.reply_text("رصيد المستخدم أقل من مبلغ الخصم.")
            return
        users_balance[target_id] = round(current - amount, 2)
        sync_balance_to_db(target_id)
        update.message.reply_text(f"تم خصم {amount}$ من آيدي {target_id}. الرصيد الحالي: {users_balance[target_id]}$")
        clear_all_waiting_flags(context)
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_block"):
        ident = text.strip()
        if ident.isdigit():
            blocked_users[int(ident)] = {"until": time.time() + CARD_BAN_HOURS * 3600, "reason": "حظر يدوي من المالك."}
            update.message.reply_text("تم حضر المستخدم.")
        else:
            uname = _normalize_username(ident)
            target = None
            for usr in get_all_users():
                if usr[2] and (_normalize_username(usr[2]) or "").lower() == (uname or "").lower():
                    target = usr[0]
                    break
            if target:
                blocked_users[target] = {"until": time.time() + CARD_BAN_HOURS * 3600, "reason": "حظر يدوي من المالك."}
                update.message.reply_text("تم حضر المستخدم.")
            else:
                update.message.reply_text("لم يتم العثور على المستخدم.")
        clear_all_waiting_flags(context)
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_broadcast"):
        broadcast_ad(update, context)
        clear_all_waiting_flags(context)
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_api_order_status"):
        order_id = text.strip()
        params = {'key': API_KEY, 'action': 'status', 'order': order_id}
        try:
            response = requests.post(API_URL, data=params, timeout=20)
            js = response.json()
            update.message.reply_text(f"حالة الطلب {order_id}:\n{js}")
        except Exception:
            update.message.reply_text("فشل جلب الحالة من API.")
        clear_all_waiting_flags(context)
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_new_mod"):
        context.user_data["waiting_for_new_mod"] = False
        target_id = None
        target_username = None
        full_name_db = "Unknown"

        if text.isdigit():
            target_id = int(text)
            row = get_user_from_db(target_id)
            if row:
                full_name_db = row[1]
                target_username = row[2] or "NoUsername"
        else:
            target_username = _normalize_username(text)
            row_match = None
            for usr in get_all_users():
                if usr[2] and (_normalize_username(usr[2]) or "").lower() == (target_username or "").lower():
                    row_match = usr
                    break
            if row_match:
                target_id = row_match[0]
                full_name_db = row_match[1]
            else:
                update.message.reply_text("تعذر إيجاد المستخدم بهذا اليوزر في قاعدة البيانات. أرسل الآيدي الرقمي للمستخدم.")
                return

        add_moderator(target_id, full_name_db, target_username or "NoUsername")
        try:
            context.bot.send_message(chat_id=target_id, text="✅ تم ترقيتك إلى مشرف. أرسل /start لتظهر لك لوحة تحكم المشرف.")
        except Exception as e:
            logger.warning("Could not DM new moderator: %s", e)
        update.message.reply_text(f"تمت إضافة المشرف: {full_name_db} (@{target_username}) - ID: {target_id}")
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_remove_mod"):
        context.user_data["waiting_for_remove_mod"] = False
        ok = remove_moderator_by_identifier(text)
        if ok:
            update.message.reply_text("تم حذف المشرف بنجاح.")
        else:
            update.message.reply_text("لم يتم العثور على المشرف المحدد.")
        return

    # ======== منطق الشحن عبر آسياسيل (المستخدم) + إشعار المالك فورًا ========
    if context.user_data.get("waiting_for_card"):
        raw = text.strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) not in (14, 16):
            update.message.reply_text("❌ رقم الكارت غير صحيح. الرجاء إرسال رقم مكوّن من 14 أو 16 رقم.")
            return

        # --- ميزة الحماية: كشف التكرار/السبام وحظر لمدة ساعتين عند المخالفة ---
        violation_reason = _record_and_check_card(user_id, digits)
        if violation_reason:
            _ban_user_for_hours(user_id, CARD_BAN_HOURS, violation_reason)
            update.message.reply_text(
                f"🚫 تم حظرك مؤقتًا لمدة {CARD_BAN_HOURS} ساعة.\nالسبب: {violation_reason}"
            )
            clear_all_waiting_flags(context)
            return
        # -----------------------------------------------------------------------

        card_number_display = f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:]}" if len(digits) == 16 else digits

        pending_cards.append({
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "card_number": digits,
            "submitted_at": time.time()
        })

        # إشعار المالك فورًا مع زر يفتح قائمة الكروت المعلقة
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "💳 تم استلام كارت آسياسيل جديد للمراجعة:\n"
                    f"- المستخدم: {full_name} (@{username})\n"
                    f"- ID: {user_id}\n"
                    f"- الكارت: {card_number_display}\n\n"
                    "اضغط الزر أدناه لعرض جميع الكروت المعلقة."
                ),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")]])
            )
        except Exception as e:
            logger.error("Failed to notify owner about new card: %s", e)

        update.message.reply_text("✅ تم إرسال رقم الكارت للمراجعة.\nسيقوم المالك بالتحقق والشحن إن أمكن.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context)
        return

    # ======== إدخال مبلغ الشحن عند موافقة المالك ========
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_amount"):
        try:
            amount = float(text.strip())
        except ValueError:
            update.message.reply_text("الرجاء إرسال مبلغ صالح.")
            return

        card_info = context.user_data.get("card_to_approve")
        card_index = context.user_data.get("card_to_approve_index")

        if card_info is None or card_index is None or not (0 <= card_index < len(pending_cards)):
            update.message.reply_text("تعذر العثور على الكارت المحدد.")
            clear_all_waiting_flags(context)
            return

        target_id = card_info["user_id"]
        users_balance[target_id] = users_balance.get(target_id, 0.0) + amount
        sync_balance_to_db(target_id)

        # إزالة الكارت من القائمة
        try:
            pending_cards.pop(card_index)
        except Exception:
            pass

        # إشعار المستخدم
        try:
            context.bot.send_message(chat_id=target_id, text=f"🎉 تم شحن رصيدك بقيمة {amount}$.")
        except Exception as e:
            logger.error("Failed to notify user about topup: %s", e)

        update.message.reply_text(f"تم شحن رصيد المستخدم {card_info['full_name']} (@{card_info['username']}) بمبلغ {amount}$.")
        clear_all_waiting_flags(context)
        return

    # --- أوضاع المستخدم/المشرف (طلبات الخدمات) ---
    if context.user_data.get("selected_service"):
        service_name = context.user_data.get("selected_service")
        price = float(context.user_data.get("service_price", 0))
        link = text.strip()

        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك لم يعد كافياً. حاول الشحن أولاً.")
            clear_all_waiting_flags(context)
            return
        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)

        pending_orders.append({
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "link": link,
            "ordered_at": time.time()
        })

        # إشعار المالك بوجود طلب خدمة جديد
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(f"🆕 طلب خدمة جديد بانتظار المراجعة:\n"
                      f"- المستخدم: {full_name} (@{username}) | ID: {user_id}\n"
                      f"- الخدمة: {service_name} | السعر: {price}$\n"
                      f"- الرابط: {link}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الطلبات المعلّقة (الخدمات)", callback_data="pending_smm_orders")]])
            )
        except Exception:
            pass

        update.message.reply_text("✅ تم استلام طلبك ووضعه في قائمة المراجعة.\nسيتم التنفيذ قريباً.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context)
        return

    if context.user_data.get("selected_pubg_service"):
        service_name = context.user_data.get("selected_pubg_service")
        price = float(context.user_data.get("pubg_service_price", 0))
        pubg_id = text.strip()

        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك لم يعد كافياً. حاول الشحن أولاً.")
            clear_all_waiting_flags(context)
            return
        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)

        pending_pubg_orders.append({
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "pubg_id": pubg_id,
            "ordered_at": time.time()
        })

        update.message.reply_text("✅ تم استلام طلب شحن شدات ببجي. سنقوم بالتنفيذ قريباً.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context)
        return

    if context.user_data.get("waiting_for_itunes_confirm"):
        if text.strip() == "1":
            service_name = context.user_data.get("selected_itunes_service")
            price = float(context.user_data.get("itunes_service_price", 0))

            bal = users_balance.get(user_id, 0.0)
            if bal < price:
                update.message.reply_text("رصيدك غير كافٍ حالياً. قم بالشحن أولاً.")
                clear_all_waiting_flags(context)
                return
            users_balance[user_id] = round(bal - price, 2)
            sync_balance_to_db(user_id)

            pending_itunes_orders.append({
                "user_id": user_id,
                "full_name": full_name,
                "username": username,
                "service": service_name,
                "price": price,
                "ordered_at": time.time()
            })

            update.message.reply_text("✅ تم استلام طلب ايتونز. سيتم إرسال الكود لك قريباً.", reply_markup=main_menu_keyboard(user_id))
        else:
            update.message.reply_text("تم إلغاء العملية.")
        clear_all_waiting_flags(context)
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_itunes_code"):
        itunes_order = context.user_data.get("itunes_to_complete")
        idx = context.user_data.get("itunes_to_complete_index")
        code = text.strip()
        if itunes_order is not None and isinstance(idx, int) and 0 <= idx < len(pending_itunes_orders):
            try:
                context.bot.send_message(chat_id=itunes_order['user_id'], text=f"🎁 كود ايتونز الخاص بك:\n{code}")
            except Exception as e:
                logger.error("Failed to send iTunes code: %s", e)
            try:
                pending_itunes_orders.pop(idx)
            except Exception:
                pass
            update.message.reply_text("تم إرسال الكود للمستخدم.")
        else:
            update.message.reply_text("طلب غير صالح.")
        clear_all_waiting_flags(context)
        return

    if context.user_data.get("waiting_for_telegram_link"):
        service_name = context.user_data.get("selected_telegram_service")
        price = float(context.user_data.get("telegram_service_price", 0))
        invite_link = text.strip()

        if "t.me/" not in invite_link:
            update.message.reply_text("الرجاء إرسال رابط دعوة صحيح مثل: https://t.me/+xxxxx")
            return

        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك غير كافٍ حالياً.")
            clear_all_waiting_flags(context)
            return

        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)

        pending_orders.append({
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "link": invite_link,
            "ordered_at": time.time()
        })

        # إشعار المالك
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(f"🆕 طلب خدمة تلغرام:\n- المستخدم: {full_name} (@{username}) | ID: {user_id}\n"
                      f"- الخدمة: {service_name} | السعر: {price}$\n- الرابط: {invite_link}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الطلبات المعلّقة (الخدمات)", callback_data="pending_smm_orders")]])
            )
        except Exception:
            pass

        update.message.reply_text("✅ تم استلام طلب خدمة التليجرام. سنباشر التنفيذ قريباً.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context)
        return

    update.message.reply_text("اختر من القائمة:", reply_markup=main_menu_keyboard(user_id))

# =========================
# أوامر بسيطة
# =========================
def help_cmd(update: Update, context: CallbackContext):
    update.message.reply_text("أرسل /start لفتح القوائم.")

# =========================
# تشغيل البوت
# =========================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # أوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))

    # أزرار
    dp.add_handler(CallbackQueryHandler(button_handler))

    # رسائل (نص + وسائط) — للبث والإدخالات المختلفة
    dp.add_handler(MessageHandler((Filters.text | Filters.photo | Filters.video | Filters.voice) & ~Filters.command, handle_messages))

    # بدء التشغيل
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
