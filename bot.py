#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
بوت تلغرام متكامل (python-telegram-bot v13.x)
- إدارة المشرفين + خصومات للمشرف
- حماية آسياسيل (تكرار/سبام) مع حظر مؤقت وإلغاء تلقائي بعد المدة
- زر "الطلبات المعلّقة (الخدمات)" لاعتماد/رفض الطلبات وتنفيذ الـ API
- المتصدرين🎉: أعلى 10 إنفاقًا مع الجوائز (للمستخدم/المشرف في الرئيسية، وللمالك داخل لوحته)
- طرق شحن إضافية: نقاط سنتات / هلابي (نفس رسالة الدعم)
- إصلاح تشابك الحالات عند استخدام /start (تفريغ الحالات)
- إصلاح قسم "رفع سكور تيكتوك": أزرار قصيرة callback_data
- **إدارة الخدمات (جديد):**
  * إضافة خدمات جديدة ديناميكيًا بأي قسم + (اختياري) ربط API
  * تفعيل/إيقاف الخدمات (الثابتة/الديناميكية)
  * عرض كل الخدمات وحالاتها
- قراءة الإعدادات من متغيّرات البيئة (Heroku Config Vars) أو القيم الافتراضية
"""

import logging
import requests
import time
import os
from typing import Optional, Tuple, Dict, Any, List
from html import escape

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
ADMIN_ID = int(os.getenv("ADMIN_ID", "7655504656"))
TOKEN = os.getenv("TOKEN", "8138:dummy_token_change_me")
API_KEY = os.getenv("API_KEY", "25a9ceb07be0d8b2ba88e70dcbe92e06")
API_URL = os.getenv("API_URL", "https://kd1s.com/api/v2")
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "@z396r")

if not TOKEN or ":" not in TOKEN:
    logger.warning("⚠️ TOKEN غير مضبوط أو غير صالح. عدّل متغير البيئة TOKEN.")

# =========================
# تعريف الأقسام (ثابت)
# =========================
CATEGORIES = {
    "followers": "قسم المتابعين",
    "likes": "قسم اللايكات",
    "views": "قسم المشاهدات",
    "live_views": "قسم مشاهدات البث المباشر",
    "tiktok_score": "رفع سكور تيكتوك",
    "pubg": "قسم شحن شدات ببجي",
    "itunes": "قسم شراء رصيد ايتونز",
    "telegram": "خدمات التليجرام",
}

# =========================
# الخدمات الثابتة (كما كانت)
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

    # سكور تيكتوك (بدون "نقاط تحديات")
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

    "مشاهدات تيكتوك 1k": 0.10,
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

    # سكور تيكتوك
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
users_balance = {}
pending_orders = []
pending_cards = []
pending_pubg_orders = []
completed_orders = []
pending_itunes_orders = []
blocked_users = {}

# ===== حماية آسياسيل =====
CARD_DUP_LIMIT = int(os.getenv("CARD_DUP_LIMIT", "2"))
CARD_SPAM_COUNT = int(os.getenv("CARD_SPAM_COUNT", "5"))
CARD_SPAM_WINDOW_SECONDS = int(os.getenv("CARD_SPAM_WINDOW_SECONDS", "120"))
CARD_BAN_HOURS = int(os.getenv("CARD_BAN_HOURS", "2"))

card_submission_history = {}

def _ban_user_for_hours(user_id: int, hours: int, reason: str):
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
    if ss and not h: parts.append(f"{ss}ث")
    return " ".join(parts) or "قليل"

def _is_user_blocked_now(user_id: int) -> Optional[str]:
    if user_id == ADMIN_ID:
        return None
    info = blocked_users.get(user_id)
    if not info:
        return None
    if info is True:
        return "لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك."
    if isinstance(info, dict):
        until = info.get("until")
        reason = info.get("reason", "مخالفة سياسات الاستخدام.")
        if until and time.time() >= until:
            try:
                del blocked_users[user_id]
            except Exception:
                pass
            return None
        remain = int(until - time.time()) if until else 0
        return f"تم حظرك لمدة مؤقتة.\nالسبب: {reason}\nالمدة المتبقية: {_remaining_human(remain)}"
    return "لقد تم حضرك من استخدام البوت 🤣.\nانتظر حتى يتم الغاء حظرك."

def _record_and_check_card(user_id: int, digits: str) -> Optional[str]:
    now = time.time()
    hist = card_submission_history.setdefault(user_id, {"counts": {}, "times": []})
    prev = hist["counts"].get(digits, 0)
    hist["counts"][digits] = prev + 1
    hist["times"].append(now)
    cutoff = now - CARD_SPAM_WINDOW_SECONDS
    hist["times"] = [t for t in hist["times"] if t >= cutoff]
    if hist["counts"][digits] > CARD_DUP_LIMIT:
        return "إدخال نفس رقم كارت آسياسيل أكثر من مرتين."
    if len(hist["times"]) > CARD_SPAM_COUNT:
        return "إرسال عدد كبير من كروت آسياسيل خلال وقت قصير."
    return None

# =========================
# قاعدة البيانات Neon (PostgreSQL)
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
    logger.error("❌ DATABASE_URL غير مضبوط.")
    raise SystemExit(1)

try:
    _host = urlparse(DATABASE_URL).hostname or ""
    if "pooler" not in _host:
        logger.warning("⚠️ يُفضَّل استخدام Pooler endpoint.")
except Exception:
    pass

pg_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    max_idle=60,
    timeout=60,
    kwargs={
        "sslmode": "require",
        "connect_timeout": 10,
    },
)

def _pool_healthcheck():
    try:
        pg_pool.wait(timeout=30)
        with pg_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        logger.info("✅ DB OK.")
    except Exception as e:
        logger.exception("❌ DB error: %s", e)
        raise

def _exec(sql: str, params: tuple = (), fetch: str = ""):
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
        logger.exception("❌ OperationalError: %s", e)
        raise
    except Exception as e:
        logger.exception("❌ DB error: %s", e)
        raise

_pool_healthcheck()

# جداول المستخدمين/المشرفين
_exec("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY
)
""")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS username  TEXT")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance   REAL DEFAULT 0")
_exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_spent REAL DEFAULT 0")

_exec("""
CREATE TABLE IF NOT EXISTS moderators (
    user_id   BIGINT PRIMARY KEY,
    full_name TEXT,
    username  TEXT
)
""")

# ===== جداول إدارة الخدمات (جديدة) =====
_exec("""
CREATE TABLE IF NOT EXISTS services_dynamic (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    api_service_id INTEGER,
    quantity_multiplier INTEGER,
    enabled BOOLEAN DEFAULT TRUE
)
""")

_exec("""
CREATE TABLE IF NOT EXISTS services_overrides (
    name TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE
)
""")

# =========================
# دوال DB: مستخدمين
# =========================
def get_user_from_db(user_id: int):
    return _exec(
        "SELECT user_id, full_name, username, balance, total_spent FROM users WHERE user_id=%s",
        (user_id,), fetch="one"
    )

def add_user_to_db(user_id: int, full_name: str, username: str):
    row = get_user_from_db(user_id)
    if not row:
        _exec(
            "INSERT INTO users (user_id, full_name, username, balance, total_spent) VALUES (%s, %s, %s, %s, %s)",
            (user_id, full_name, username, 0.0, 0.0)
        )

def update_user_balance_in_db(user_id: int, balance: float):
    _exec("UPDATE users SET balance=%s WHERE user_id=%s", (balance, user_id))

def update_username_in_db(user_id: int, username: str):
    _exec("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))

def add_user_spent(user_id: int, amount: float):
    _exec("UPDATE users SET total_spent = COALESCE(total_spent,0) + %s WHERE user_id=%s", (amount, user_id))

def reduce_user_spent(user_id: int, amount: float):
    _exec("""
        UPDATE users
        SET total_spent = GREATEST(COALESCE(total_spent,0) - %s, 0)
        WHERE user_id=%s
    """, (amount, user_id))

def get_all_users():
    return _exec("SELECT user_id, full_name, username, balance, total_spent FROM users", fetch="all") or []

def get_users_with_balance_desc():
    return _exec(
        "SELECT user_id, full_name, username, balance, total_spent FROM users WHERE balance > 0 ORDER BY balance DESC",
        fetch="all"
    ) or []

def get_top_spenders(limit: int = 10):
    return _exec(
        "SELECT user_id, full_name, username, total_spent FROM users ORDER BY total_spent DESC, user_id ASC LIMIT %s",
        (limit,), fetch="all"
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
# دوال DB: الخدمات
# =========================
def add_dynamic_service(name: str, price: float, category: str,
                        api_service_id: Optional[int], quantity_multiplier: Optional[int]) -> bool:
    try:
        _exec("""
            INSERT INTO services_dynamic (name, price, category, api_service_id, quantity_multiplier, enabled)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (name) DO UPDATE SET
                price=EXCLUDED.price,
                category=EXCLUDED.category,
                api_service_id=EXCLUDED.api_service_id,
                quantity_multiplier=EXCLUDED.quantity_multiplier,
                enabled=TRUE
        """, (name, price, category, api_service_id, quantity_multiplier))
        return True
    except Exception as e:
        logger.error("add_dynamic_service error: %s", e)
        return False

def list_dynamic_services(category: Optional[str] = None, only_enabled: bool = True):
    if category and only_enabled:
        return _exec("SELECT id, name, price, category, api_service_id, quantity_multiplier, enabled FROM services_dynamic WHERE category=%s AND enabled=TRUE ORDER BY name",
                     (category,), fetch="all") or []
    if category and not only_enabled:
        return _exec("SELECT id, name, price, category, api_service_id, quantity_multiplier, enabled FROM services_dynamic WHERE category=%s ORDER BY name",
                     (category,), fetch="all") or []
    if not category and only_enabled:
        return _exec("SELECT id, name, price, category, api_service_id, quantity_multiplier, enabled FROM services_dynamic WHERE enabled=TRUE ORDER BY category, name",
                     fetch="all") or []
    return _exec("SELECT id, name, price, category, api_service_id, quantity_multiplier, enabled FROM services_dynamic ORDER BY category, name",
                 fetch="all") or []

def get_dynamic_service_by_id(svc_id: int):
    return _exec("SELECT id, name, price, category, api_service_id, quantity_multiplier, enabled FROM services_dynamic WHERE id=%s",
                 (svc_id,), fetch="one")

def get_dynamic_service_by_name(name: str):
    return _exec("SELECT id, name, price, category, api_service_id, quantity_multiplier, enabled FROM services_dynamic WHERE name=%s",
                 (name,), fetch="one")

def set_dynamic_service_enabled(name: str, enabled: bool) -> bool:
    rc = _exec("UPDATE services_dynamic SET enabled=%s WHERE name=%s", (enabled, name))
    return (rc or 0) > 0

def is_static_service_enabled(name: str) -> bool:
    row = _exec("SELECT enabled FROM services_overrides WHERE name=%s", (name,), fetch="one")
    if not row:
        return True
    return bool(row[0])

def set_static_service_enabled(name: str, enabled: bool):
    _exec("""
        INSERT INTO services_overrides (name, enabled)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET enabled=EXCLUDED.enabled
    """, (name, enabled))

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
    try:
        if not is_moderator(user_id):
            return base_price
        if kind in ("itunes", "pubg") or ("ايتونز" in service_name or "ببجي" in service_name):
            return round(float(base_price) * 0.90, 2)
        in_80 = (
            ("متابعين" in service_name) or
            ("لايكات" in service_name) or
            ("مشاهدات بث" in service_name) or
            ("رفع سكور" in service_name) or
            (kind == "telegram")
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
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("لوحة تحكم المالك", callback_data="admin_menu")]
        ])
    if is_moderator(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("الخدمات", callback_data="show_services")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
            [InlineKeyboardButton("لوحة تحكم المشرف", callback_data="moderator_menu")],
            [InlineKeyboardButton("المتصدرين🎉", callback_data="show_leaderboard")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الخدمات", callback_data="show_services")],
        [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
        [InlineKeyboardButton("المتصدرين🎉", callback_data="show_leaderboard")]
    ])

def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("الطلبات المعلّقة (الخدمات)", callback_data="pending_smm_orders")],
        [InlineKeyboardButton("إدارة الخدمات", callback_data="services_admin")],
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
        [InlineKeyboardButton("المتصدرين🎉", callback_data="show_leaderboard")],
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

def tiktok_score_keyboard(user_id: int, context: CallbackContext):
    # ثابتة + ديناميكية
    static_score = [(k, v) for k, v in services_dict.items() if ("رفع سكور" in k) and is_static_service_enabled(k)]
    dyn_score = list_dynamic_services("tiktok_score", only_enabled=True)
    score_services: List[Tuple[str, float]] = []
    for name, price in static_score:
        score_services.append((name, price))
    for (sid, name, price, _cat, _api, _qty, _en) in dyn_score:
        score_services.append((name, price))
    context.user_data["score_map"] = [name for name, _ in score_services]
    service_buttons = []
    for idx, (service_name, price) in enumerate(score_services):
        eff = get_effective_price(user_id, service_name, price, "generic")
        service_buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"score_service_{idx}")])
    service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(service_buttons)

def itunes_services_keyboard(user_id: int):
    buttons = []
    # ثابتة
    for service_name, price in itunes_services.items():
        if not is_static_service_enabled(service_name):
            continue
        eff = get_effective_price(user_id, service_name, price, "itunes")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"itunes_service_{service_name}")])
    # ديناميكية
    for (sid, name, price, _cat, _api, _qty, _en) in list_dynamic_services("itunes", only_enabled=True):
        eff = get_effective_price(user_id, name, price, "itunes")
        buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"dynsvc_{sid}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def telegram_services_keyboard(user_id: int):
    buttons = []
    for service_name, price in telegram_services.items():
        if not is_static_service_enabled(service_name):
            continue
        eff = get_effective_price(user_id, service_name, price, "telegram")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"telegram_service_{service_name}")])
    for (sid, name, price, _cat, _api, _qty, _en) in list_dynamic_services("telegram", only_enabled=True):
        eff = get_effective_price(user_id, name, price, "telegram")
        buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"dynsvc_{sid}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def clear_all_waiting_flags(context: CallbackContext):
    waiting_keys = [
        # قديمة
        "waiting_for_card", "waiting_for_block", "waiting_for_add_balance_user_id",
        "waiting_for_add_balance_amount", "waiting_for_discount_user_id", "waiting_for_discount_amount",
        "waiting_for_broadcast", "waiting_for_api_order_status", "selected_service", "service_price",
        "selected_pubg_service", "pubg_service_price", "card_to_approve", "card_to_approve_index", "waiting_for_amount",
        "selected_itunes_service", "itunes_service_price", "waiting_for_itunes_confirm",
        "waiting_for_itunes_code", "itunes_to_complete", "itunes_to_complete_index",
        "selected_telegram_service", "telegram_service_price", "waiting_for_telegram_link",
        "waiting_for_new_mod", "waiting_for_remove_mod", "admin_target_id", "score_map",
        # جديدة — إدارة الخدمات
        "svc_add_step", "svc_add_category", "svc_add_name", "svc_add_price",
        "svc_add_use_api", "svc_add_api_id", "svc_add_qty",
        "svc_toggle_wait_name"
    ]
    for key in waiting_keys:
        context.user_data.pop(key, None)

# =========================
# نظام الإعلان
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
    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        update.message.reply_text(ban_msg)
        return
    clear_all_waiting_flags(context)
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
# أدوات مساعدة: دمج خدمات ثابتة/ديناميكية لكل قسم
# =========================
def _dynamic_kind_from_category(category: str) -> str:
    if category == "itunes":
        return "itunes"
    if category == "pubg":
        return "pubg"
    if category == "telegram":
        return "telegram"
    return "generic"

def _add_static_buttons_if_enabled(buttons: List[List[InlineKeyboardButton]], items: List[Tuple[str, float]], user_id: int, kind: str, prefix: str = "service_"):
    for name, price in items:
        if not is_static_service_enabled(name):
            continue
        eff = get_effective_price(user_id, name, price, kind)
        buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"{prefix}{name}")])

def _add_dynamic_buttons(buttons: List[List[InlineKeyboardButton]], category: str, user_id: int, kind: str):
    for (sid, name, price, _cat, _api, _qty, _en) in list_dynamic_services(category, only_enabled=True):
        eff = get_effective_price(user_id, name, price, kind)
        buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"dynsvc_{sid}")])

# =========================
# تنفيذ الطلب عبر API عند الموافقة
# =========================
def approve_order_process(order_index: int, context: CallbackContext, query):
    try:
        order_info = pending_orders.pop(order_index)
    except IndexError:
        query.answer("الطلب غير موجود.", show_alert=True)
        return

    api_sid = order_info.get("api_service_id")
    api_qty = order_info.get("api_quantity")

    if api_sid:
        params = {
            'key': API_KEY,
            'action': 'add',
            'service': api_sid,
            'link': order_info['link'],
            'quantity': api_qty or 1000
        }
        try:
            response = requests.post(API_URL, data=params, timeout=25)
            api_response = response.json()
        except Exception:
            api_response = {"error": "فشل استدعاء API"}

        if "order" in api_response:
            order_info["order_number"] = api_response["order"]
            order_info["service_number"] = api_sid
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
            reduce_user_spent(order_info['user_id'], order_info['price'])
            context.bot.send_message(chat_id=order_info['user_id'], text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
        return

    # إن لم يوجد api_service_id — ارجع للخريطة الثابتة إن وجدت
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
            reduce_user_spent(order_info['user_id'], order_info['price'])
            context.bot.send_message(chat_id=order_info['user_id'], text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
    else:
        # خدمة داخلية
        order_info["order_number"] = "N/A"
        order_info["service_number"] = "N/A"
        order_info["refunded"] = False
        order_info["completed_at"] = time.time()
        completed_orders.append(order_info)
        context.bot.send_message(chat_id=order_info['user_id'], text="تم إكمال طلبك بنجاح.")
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))

# =========================
# أزرار (Callback)
# =========================
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    clear_all_waiting_flags(context)

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

    # ======= المتصدرين🎉 =======
    if data == "show_leaderboard":
        top = get_top_spenders(10)
        header = (
            "<b>🥇 المتصدرون في الشراء داخل البوت</b>\n\n"
            "يحصل <b>أول 3 متصدرين</b> على جوائز تُضاف تلقائيًا خلال أسبوع:\n"
            "• المركز الأول: 10$ 💰\n"
            "• المركز الثاني: 5$ 💸\n"
            "• المركز الثالث: 3$ 🎁\n\n"
        )
        if not top:
            text_msg = header + "لا توجد عمليات شراء بعد. كن أنت الأول وابدأ بتجميع الصدارة!"
        else:
            lines = []
            for i, (uid, fn, un, spent) in enumerate(top, start=1):
                name = escape(fn or "مستخدم")
                usertag = f"@{un}" if un else ""
                lines.append(f"{i}. {name} {escape(usertag)} — إجمالي الصرف: {round(spent or 0, 2)}$")
            text_msg = header + "\n".join(lines)
        kb = [[InlineKeyboardButton("رجوع", callback_data="back_main")]]
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return

    # ======= الأقسام =======
    if data == "show_followers":
        buttons = []
        static_items = [(k, v) for k, v in services_dict.items() if "متابعين" in k]
        _add_static_buttons_if_enabled(buttons, static_items, user_id, "generic")
        _add_dynamic_buttons(buttons, "followers", user_id, "generic")
        buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "show_likes":
        buttons = []
        static_items = [(k, v) for k, v in services_dict.items() if "لايكات" in k]
        _add_static_buttons_if_enabled(buttons, static_items, user_id, "generic")
        _add_dynamic_buttons(buttons, "likes", user_id, "generic")
        buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "show_views":
        buttons = []
        static_items = [(k, v) for k, v in services_dict.items() if ("مشاهدات تيكتوك" in k or "مشاهدات انستغرام" in k)]
        _add_static_buttons_if_enabled(buttons, static_items, user_id, "generic")
        _add_dynamic_buttons(buttons, "views", user_id, "generic")
        buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "show_live_views":
        buttons = []
        static_items = [(k, v) for k, v in services_dict.items() if "مشاهدات بث" in k]
        _add_static_buttons_if_enabled(buttons, static_items, user_id, "generic")
        _add_dynamic_buttons(buttons, "live_views", user_id, "generic")
        buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "show_tiktok_score":
        query.edit_message_text("اختر خدمة رفع سكور تيكتوك المطلوبة:", reply_markup=tiktok_score_keyboard(user_id, context))
        return

    if data == "show_itunes_services":
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=itunes_services_keyboard(user_id))
        return

    if data == "show_telegram_services":
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=telegram_services_keyboard(user_id))
        return

    if data == "show_pubg":
        buttons = []
        # ثابتة
        for name, base_price in pubg_services.items():
            if not is_static_service_enabled(name):
                continue
            eff = get_effective_price(user_id, name, base_price, "pubg")
            buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"pubg_service_{name}")])
        # ديناميكية
        for (sid, name, price, _cat, _api, _qty, _en) in list_dynamic_services("pubg", only_enabled=True):
            eff = get_effective_price(user_id, name, price, "pubg")
            buttons.append([InlineKeyboardButton(f"{name} - {eff}$", callback_data=f"dynsvc_{sid}")])
        buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر خدمة شحن شدات ببجي:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # ===== أزرار السكور القصيرة (ثابت+ديناميكي) =====
    if data.startswith("score_service_"):
        try:
            idx = int(data.split("_")[-1])
        except Exception:
            query.edit_message_text("حدث خطأ في اختيار الخدمة.")
            return
        names = context.user_data.get("score_map") or [k for k in services_dict.keys() if ("رفع سكور" in k)]
        if idx < 0 or idx >= len(names):
            query.edit_message_text("الخدمة غير موجودة.")
            return
        service_name = names[idx]
        # ديناميكي أم ثابت؟
        dyn = get_dynamic_service_by_name(service_name)
        if dyn:
            _id, _name, price, category, api_id, qty, enabled = dyn
            price_eff = get_effective_price(user_id, service_name, price, "generic")
            current_balance = users_balance.get(user_id, 0.0)
            if current_balance < price_eff:
                buttons = [
                    [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                    [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                    [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                    [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                    [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                    [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                    [InlineKeyboardButton("رجوع", callback_data="show_tiktok_score")]
                ]
                query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
                return
            context.user_data["selected_service"] = service_name
            context.user_data["service_price"] = price_eff
            # خزّن API للديناميكي
            if api_id:
                context.user_data["selected_dynamic_api"] = {"api_service_id": api_id, "api_quantity": qty or 1000}
            message_text = (
                "يرجى ارسال رابط البث المباشر الخاص بك على تيكتوك.\n"
                "🔴 تنبيه: أرسل <b>رابط البث</b> وليس اليوزرنيم."
            )
            query.edit_message_text(message_text, parse_mode="HTML")
            return

        # ثابت
        base_price = services_dict.get(service_name)
        if base_price is None or not is_static_service_enabled(service_name):
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
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                [InlineKeyboardButton("رجوع", callback_data="show_tiktok_score")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_service"] = service_name
        context.user_data["service_price"] = price
        message_text = (
            "يرجى ارسال رابط البث المباشر الخاص بك على تيكتوك.\n"
            "🔴 تنبيه: أرسل <b>رابط البث</b> وليس اليوزرنيم."
        )
        query.edit_message_text(message_text, parse_mode="HTML")
        return

    # ===== اختيار خدمة ديناميكية عامة =====
    if data.startswith("dynsvc_"):
        try:
            svc_id = int(data.split("_")[-1])
        except Exception:
            query.edit_message_text("خدمة غير صالحة.")
            return
        dyn = get_dynamic_service_by_id(svc_id)
        if not dyn:
            query.edit_message_text("الخدمة غير موجودة.")
            return
        _id, name, price, category, api_id, qty, enabled = dyn
        kind = _dynamic_kind_from_category(category)
        price_eff = get_effective_price(user_id, name, price, kind)
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price_eff:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                [InlineKeyboardButton("رجوع", callback_data="show_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return

        # مسارات حسب القسم
        if category == "telegram":
            context.user_data["selected_telegram_service"] = name
            context.user_data["telegram_service_price"] = price_eff
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

        if category == "itunes":
            context.user_data["selected_itunes_service"] = name
            context.user_data["itunes_service_price"] = price_eff
            context.user_data["waiting_for_itunes_confirm"] = True
            query.edit_message_text(f"تم اختيار الخدمة: {name}\n\nارسل رقم 1 لتأكيد طلبك")
            return

        if category == "pubg":
            context.user_data["selected_pubg_service"] = name
            context.user_data["pubg_service_price"] = price_eff
            query.edit_message_text("ارسل الايدي الخاص بك:")
            return

        # باقي الأقسام = رابط
        context.user_data["selected_service"] = name
        context.user_data["service_price"] = price_eff
        if api_id:
            context.user_data["selected_dynamic_api"] = {"api_service_id": api_id, "api_quantity": qty or 1000}
        # رسائل مخصصة
        if category == "tiktok_score":
            msg = (
                "يرجى ارسال رابط البث المباشر الخاص بك على تيكتوك.\n"
                "🔴 تنبيه: أرسل <b>رابط البث</b> وليس اليوزرنيم."
            )
        elif "انستغرام" in name:
            msg = (
                "الرجاء إرسال رابط الخدمة الخاص بك\n"
                "🔴 تنبيه:\n"
                "يرجى إطفاء زر 'تميز للمراجعة' داخل حسابك الانستغرام قبل ارسال رابط الخدمه لضمان إكمال طلبك!"
            )
        elif "تيكتوك" in name:
            msg = (
                "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:\n"
                "🔴 ملاحظة: أرسل <b>الرابط</b> وليس اليوزرنيم!"
            )
        else:
            msg = "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:"
        query.edit_message_text(msg, parse_mode="HTML")
        return

    # ===== اختيار خدمة ثابتة عامة =====
    if data.startswith("service_"):
        service_name = data[len("service_"):]
        base_price = services_dict.get(service_name)
        if base_price is None or not is_static_service_enabled(service_name):
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
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
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
                "يرجى ارسال رابط البث المباشر الخاص بك على تيكتوك.\n"
                "🔴 تنبيه: أرسل <b>رابط البث</b> وليس اليوزرنيم."
            )
        elif "تيكتوك" in service_name:
            message_text = (
                "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:\n"
                "🔴 ملاحظة: أرسل <b>الرابط</b> وليس اليوزرنيم!"
            )
        else:
            message_text = "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:"

        context.user_data["selected_service"] = service_name
        context.user_data["service_price"] = price
        query.edit_message_text(message_text, parse_mode="HTML")
        return

    # ===== اختيار خدمة ببجي ثابتة =====
    if data.startswith("pubg_service_"):
        name = data[len("pubg_service_"):]
        base_price = pubg_services.get(name, 0)
        if not is_static_service_enabled(name):
            query.edit_message_text("الخدمة غير مفعلة حالياً.")
            return
        price = get_effective_price(user_id, name, base_price, "pubg")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                [InlineKeyboardButton("رجوع", callback_data="show_pubg")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_pubg_service"] = name
        context.user_data["pubg_service_price"] = price
        query.edit_message_text("ارسل الايدي الخاص بك:")
        return

    # ===== اختيار خدمة ايتونز ثابتة =====
    if data.startswith("itunes_service_"):
        service_name = data[len("itunes_service_"):]
        base_price = itunes_services.get(service_name, 0)
        if not is_static_service_enabled(service_name):
            query.edit_message_text("الخدمة غير مفعلة حالياً.")
            return
        price = get_effective_price(user_id, service_name, base_price, "itunes")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                [InlineKeyboardButton("رجوع", callback_data="show_itunes_services")]
            ]
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_itunes_service"] = service_name
        context.user_data["itunes_service_price"] = price
        query.edit_message_text(f"تم اختيار الخدمة: {service_name}\n\nارسل رقم 1 لتأكيد طلبك")
        context.user_data["waiting_for_itunes_confirm"] = True
        return

    # ===== اختيار خدمة تلغرام ثابتة =====
    if data.startswith("telegram_service_"):
        service_name = data[len("telegram_service_"):]
        base_price = telegram_services.get(service_name, 0)
        if not is_static_service_enabled(service_name):
            query.edit_message_text("الخدمة غير مفعلة حالياً.")
            return
        price = get_effective_price(user_id, service_name, base_price, "telegram")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
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

    # ===== الرصيد وطرق الشحن =====
    if data == "show_balance":
        balance = users_balance.get(user_id, 0.0)
        buttons = [
            [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
            [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
            [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
            [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
            [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
            [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
            [InlineKeyboardButton("رجوع", callback_data="back_main")]
        ]
        query.edit_message_text(f"رصيدك الحالي: {balance}$", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "charge_asiacell":
        context.user_data["waiting_for_card"] = True
        query.edit_message_text("أرسل رقم الكارت المكون من 14 أو 16 رقم (يمكنك لصقه كما هو):")
        return

    if data in ("charge_superkey", "charge_zaincash", "charge_usdt", "charge_cent_points", "charge_helabi"):
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

    # ------- إدارة الخدمات (مالك) -------
    if user_id == ADMIN_ID and data == "services_admin":
        kb = [
            [InlineKeyboardButton("➕ إضافة خدمة جديدة", callback_data="svc_add")],
            [InlineKeyboardButton("🔁 تفعيل/إيقاف خدمة", callback_data="svc_toggle")],
            [InlineKeyboardButton("📄 عرض كل الخدمات", callback_data="svc_list")],
            [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
        ]
        query.edit_message_text("إدارة الخدمات:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if user_id == ADMIN_ID and data == "svc_add":
        # اختيار القسم
        kb = []
        row = []
        for key, label in CATEGORIES.items():
            row.append(InlineKeyboardButton(label, callback_data=f"svc_add_cat_{key}"))
            if len(row) == 2:
                kb.append(row); row = []
        if row: kb.append(row)
        kb.append([InlineKeyboardButton("رجوع", callback_data="services_admin")])
        query.edit_message_text("اختر قسم الخدمة الجديدة:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if user_id == ADMIN_ID and data.startswith("svc_add_cat_"):
        cat = data.split("_", 3)[-1]
        if cat not in CATEGORIES:
            query.edit_message_text("قسم غير صالح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
            return
        context.user_data["svc_add_category"] = cat
        context.user_data["svc_add_step"] = "name"
        query.edit_message_text(f"أدخل اسم الخدمة الجديدة ضمن ({CATEGORIES[cat]}):")
        return

    if user_id == ADMIN_ID and data == "svc_toggle":
        context.user_data["svc_toggle_wait_name"] = True
        query.edit_message_text(
            "أرسل اسم الخدمة لإيقافها/تفعيلها.\n"
            "• إذا كانت ديناميكية: سيتم قلب حالتها.\n"
            "• إذا كانت ثابتة: سيتم تفعيل/إيقاف عبر overrides.\n\n"
            "ملاحظة: الاسم يجب أن يطابق المعروض في الأزرار بالضبط."
        )
        return

    if user_id == ADMIN_ID and data == "svc_list":
        # ثابتة
        lines = ["📄 <b>الخدمات الثابتة</b>:"]
        def _st(name, price):
            state = "✅" if is_static_service_enabled(name) else "⛔️"
            lines.append(f"{state} {escape(name)} — {price}$")
        for k, v in sorted(services_dict.items()):
            _st(k, v)
        for k, v in sorted(pubg_services.items()):
            _st(k, v)
        for k, v in sorted(itunes_services.items()):
            _st(k, v)
        for k, v in sorted(telegram_services.items()):
            _st(k, v)
        # ديناميكية
        lines.append("\n🧩 <b>الخدمات الديناميكية</b>:")
        dyns = list_dynamic_services(None, only_enabled=False)
        if not dyns:
            lines.append("لا توجد خدمات ديناميكية بعد.")
        else:
            for (sid, name, price, cat, api, qty, en) in dyns:
                badge = "✅" if en else "⛔️"
                api_txt = f"API:{api}×{qty}" if api else "بدون API"
                lines.append(f"{badge} #{sid} — {escape(name)} — {price}$ — {CATEGORIES.get(cat, cat)} — {api_txt}")
        kb = [[InlineKeyboardButton("رجوع", callback_data="services_admin")]]
        query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
        return

    # ------- بقية لوحة المالك (كما كانت) -------
    if user_id == ADMIN_ID:
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
            reduce_user_spent(order_info['user_id'], float(order_info['price']))
            try:
                context.bot.send_message(chat_id=order_info['user_id'], text="تم إلغاء طلبك وإعادة المبلغ إلى رصيدك.")
            except Exception:
                pass
            query.edit_message_text("تم رفض الطلب وإرجاع الرصيد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_smm_orders")]]))
            return

    # ================= إدارة المشرفين/الإحصائيات ... (نفس السابق) =================
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
    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        update.message.reply_text(ban_msg)
        return

    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    text = update.message.text or ""

    # --- أوضاع المالك: إدارة الخدمات (الدردشة) ---
    if user_id == ADMIN_ID and context.user_data.get("svc_add_step") == "name":
        if not text.strip():
            update.message.reply_text("الاسم لا يمكن أن يكون فارغاً. أعد الإرسال:")
            return
        context.user_data["svc_add_name"] = text.strip()
        context.user_data["svc_add_step"] = "price"
        update.message.reply_text("أدخل السعر بالدولار (عدد):")
        return

    if user_id == ADMIN_ID and context.user_data.get("svc_add_step") == "price":
        try:
            price = float(text.strip())
        except ValueError:
            update.message.reply_text("الرجاء إرسال سعر صالح.")
            return
        context.user_data["svc_add_price"] = price
        context.user_data["svc_add_step"] = "use_api"
        kb = [[InlineKeyboardButton("نعم، استخدم API", callback_data="svc_add_api_yes")],
              [InlineKeyboardButton("لا، بدون API", callback_data="svc_add_api_no")]]
        update.message.reply_text("هل تريد ربط هذه الخدمة بـ API خارجي؟", reply_markup=InlineKeyboardMarkup(kb))
        return

    if user_id == ADMIN_ID and context.user_data.get("svc_toggle_wait_name"):
        name = text.strip()
        # جرّب الديناميكي
        dyn = get_dynamic_service_by_name(name)
        if dyn:
            _id, _name, _price, _cat, _api, _qty, en = dyn
            set_dynamic_service_enabled(name, not en)
            state = "تم تفعيل الخدمة." if not en else "تم إيقاف الخدمة."
            update.message.reply_text(state, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
            clear_all_waiting_flags(context)
            return
        # ثابت
        new_state = not is_static_service_enabled(name)
        set_static_service_enabled(name, new_state)
        state = "تم تفعيل الخدمة (ثابتة)." if new_state else "تم إيقاف الخدمة (ثابتة)."
        update.message.reply_text(state, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
        clear_all_waiting_flags(context)
        return

    # --- أوضاع المالك القديمة (إضافة/خصم/حظر/بث/حالة API) ---
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
                update.message.reply_text("تعذر إيجاد المستخدم بهذا اليوزر. أرسل الآيدي الرقمي.")
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

    # ======== آسياسيل + الحماية ========
    if context.user_data.get("waiting_for_card"):
        raw = text.strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) not in (14, 16):
            update.message.reply_text("❌ رقم الكارت غير صحيح. الرجاء إرسال رقم مكوّن من 14 أو 16 رقم.")
            return
        violation_reason = _record_and_check_card(user_id, digits)
        if violation_reason:
            _ban_user_for_hours(user_id, CARD_BAN_HOURS, violation_reason)
            update.message.reply_text(
                f"🚫 تم حظرك مؤقتًا لمدة {CARD_BAN_HOURS} ساعة.\nالسبب: {violation_reason}"
            )
            clear_all_waiting_flags(context)
            return
        card_number_display = f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:]}" if len(digits) == 16 else digits
        pending_cards.append({
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "card_number": digits,
            "submitted_at": time.time()
        })
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

    # ======== إدخال مبلغ الشحن (المالك) ========
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
        try:
            pending_cards.pop(card_index)
        except Exception:
            pass
        try:
            context.bot.send_message(chat_id=target_id, text=f"🎉 تم شحن رصيدك بقيمة {amount}$.")
        except Exception as e:
            logger.error("Failed to notify user about topup: %s", e)
        update.message.reply_text(f"تم شحن رصيد المستخدم {card_info['full_name']} (@{card_info['username']}) بمبلغ {amount}$.")
        clear_all_waiting_flags(context)
        return

    # --- طلبات الخدمات (خصم رصيد + تسجيل صرف) ---
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
        add_user_spent(user_id, price)
        order = {
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "link": link,
            "ordered_at": time.time()
        }
        # إن كان ديناميكي مرتبط بـ API
        dyn_api = context.user_data.get("selected_dynamic_api")
        if dyn_api:
            order["api_service_id"] = dyn_api.get("api_service_id")
            order["api_quantity"] = dyn_api.get("api_quantity")
        pending_orders.append(order)
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
        add_user_spent(user_id, price)
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
            add_user_spent(user_id, price)
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
        add_user_spent(user_id, price)
        pending_orders.append({
            "user_id": user_id,
            "full_name": full_name,
            "username": username,
            "service": service_name,
            "price": price,
            "link": invite_link,
            "ordered_at": time.time()
        })
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
# خطوات زر إضافة خدمة — جزء الكولباك
# =========================
def _svc_add_flow_callback(update: Update, context: CallbackContext, data: str):
    query = update.callback_query
    # بعد اختيار استخدام API أم لا
    if data == "svc_add_api_yes":
        context.user_data["svc_add_use_api"] = True
        context.user_data["svc_add_step"] = "api_id"
        query.edit_message_text("أرسل الآن رقم service_id الخاص بالـ API (عدد صحيح):")
        return True
    if data == "svc_add_api_no":
        context.user_data["svc_add_use_api"] = False
        # حفظ الخدمة فورًا
        name = context.user_data.get("svc_add_name")
        price = context.user_data.get("svc_add_price")
        category = context.user_data.get("svc_add_category")
        ok = add_dynamic_service(name, float(price), category, None, None)
        if ok:
            query.edit_message_text("✅ تم إضافة الخدمة بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
        else:
            query.edit_message_text("❌ تعذّر إضافة الخدمة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
        clear_all_waiting_flags(context)
        return True
    return False

def _svc_add_flow_message(update: Update, context: CallbackContext):
    # استلام api_id أو qty
    if context.user_data.get("svc_add_step") == "api_id":
        txt = update.message.text.strip()
        if not txt.isdigit():
            update.message.reply_text("الرجاء إرسال رقم صحيح لـ service_id.")
            return True
        context.user_data["svc_add_api_id"] = int(txt)
        context.user_data["svc_add_step"] = "qty"
        update.message.reply_text("أرسل الآن quantity_multiplier (عدد صحيح، مثل 1000):")
        return True
    if context.user_data.get("svc_add_step") == "qty":
        txt = update.message.text.strip()
        if not txt.isdigit():
            update.message.reply_text("الرجاء إرسال quantity_multiplier كعدد صحيح.")
            return True
        context.user_data["svc_add_qty"] = int(txt)
        # حفظ
        name = context.user_data.get("svc_add_name")
        price = context.user_data.get("svc_add_price")
        category = context.user_data.get("svc_add_category")
        api_id = context.user_data.get("svc_add_api_id")
        qty = context.user_data.get("svc_add_qty")
        ok = add_dynamic_service(name, float(price), category, api_id, qty)
        if ok:
            update.message.reply_text("✅ تم إضافة الخدمة (مرتبطة بـ API).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
        else:
            update.message.reply_text("❌ تعذّر إضافة الخدمة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="services_admin")]]))
        clear_all_waiting_flags(context)
        return True
    return False

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
    def _callback_router(update: Update, context: CallbackContext):
        data = update.callback_query.data
        # مسار إضافة خدمة (أسئلة نعم/لا)
        if update.effective_user.id == ADMIN_ID:
            if _svc_add_flow_callback(update, context, data):
                return
        button_handler(update, context)

    dp.add_handler(CallbackQueryHandler(_callback_router))

    # رسائل (نص + وسائط)
    def _message_router(update: Update, context: CallbackContext):
        # مسار إضافة خدمة (رسائل نصية)
        if update.effective_user.id == ADMIN_ID:
            if _svc_add_flow_message(update, context):
                return
        handle_messages(update, context)

    dp.add_handler(MessageHandler((Filters.text | Filters.photo | Filters.video | Filters.voice) & ~Filters.command, _message_router))

    # بدء التشغيل
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
