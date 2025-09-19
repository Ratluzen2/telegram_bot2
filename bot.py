#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
بوت تلغرام متكامل (python-telegram-bot v13.x)
- إدارة المشرفين + خصومات للمشرف
- إصلاح شحن آسياسيل مع إشعار فوري للمالك + حماية (تكرار/سبام) مع حظر مؤقت
- زر "الطلبات المعلّقة (الخدمات)" لاعتماد/رفض الطلبات وتنفيذ الـ API
- المتصدرين🎉: عرض أعلى 10 إنفاقًا مع الجوائز (موجود للمستخدم/المشرف في الرئيسية، وللمالك داخل لوحته)
- طرق شحن إضافية: نقاط سنتات / هلابي (نفس رسالة الدعم)
- تفريغ الحالات تلقائيًا عند /start وأي زر رجوع لمنع التداخل
- إصلاح قسم "رفع سكور تيكتوك": أزرار قصيرة callback_data لتفادي حد 64 بايت
- قراءة الإعدادات من متغيّرات البيئة (Heroku Config Vars) أو القيم الافتراضية
- NEW: زر "طلباتي" للمستخدم والمشرف + تخزين كامل الطلبات/الكروت/الحظر/السجل في Neon DB
"""

import logging
import requests
import time
import os
from typing import Optional, List, Dict, Any
from html import escape
from datetime import datetime, timedelta, timezone

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
TOKEN = os.getenv("TOKEN", "8138615524:AAFr6m5Z4_gY0k7pdg7teD9nM8ReDC-KQKU")
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
    "رفع سكور بثك1k": {"service_id": 13125, "quantity_multiplier": 1000},
    "رفع سكور بثك2k": {"service_id": 13125, "quantity_multiplier": 2000},
    "رفع سكور بثك3k": {"service_id": 13125, "quantity_multiplier": 3000},
    "رفع سكور بثك10k": {"service_id": 13125, "quantity_multiplier": 10000},

    "أعضاء قنوات تلي 1k": {"service_id": 14021, "quantity_multiplier": 1000},
    "أعضاء قنوات تلي 2k": {"service_id": 14021, "quantity_multiplier": 2000},
    "أعضاء قنوات تلي 3k": {"service_id": 14021, "quantity_multiplier": 3000},
    "أعضاء قنوات تلي 4k": {"service_id": 14021, "quantity_multiplier": 4000},
    "أعضاء كروبات تلي 1k": {"service_id": 14022, "quantity_multiplier": 1000},
    "أعضاء كروبات تلي 2k": {"service_id": 14022, "quantity_multiplier": 2000},
    "أعضاء كروبات تلي 3k": {"service_id": 14022, "quantity_multiplier": 3000},
    "أعضاء كروبات تلي 4k": {"service_id": 14022, "quantity_multiplier": 4000},
}

# الأسعار الأساسية
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



# خدمات لودو
ludo_services = {
    "لودو 810 الماسة": 3,
    "لودو 2320 الماسة": 7,
    "لودو 5150 الماسة": 13,
    "لودو 13580 الماسة": 28,
    "لودو 68500 ذهب": 3,
    "لودو 223700 ذهب": 7,
    "لودو 1463320 ذهب": 13,
    "لودو 3666470 ذهب": 28,
}
# =========================
# المتغيرات والذاكرة (تظل موجودة لكن الاعتماد الآن على DB)
# =========================
users_balance = {}   # كاش اختياري — المصدر الحقيقي DB

# ===== ميزة الحماية =====
CARD_DUP_LIMIT = int(os.getenv("CARD_DUP_LIMIT", "2"))
CARD_SPAM_COUNT = int(os.getenv("CARD_SPAM_COUNT", "5"))
CARD_SPAM_WINDOW_SECONDS = int(os.getenv("CARD_SPAM_WINDOW_SECONDS", "120"))
CARD_BAN_HOURS = int(os.getenv("CARD_BAN_HOURS", "2"))

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
    logger.error("❌ DATABASE_URL غير مضبوط. عيّن رابط Neon (يفضّل pooler endpoint مع sslmode=require).")
    raise SystemExit(1)

try:
    _host = urlparse(DATABASE_URL).hostname or ""
    if "pooler" not in _host:
        logger.warning("⚠️ يُفضَّل استخدام Pooler endpoint من Neon لعدد اتصالات أقل وثبات أعلى.")
except Exception:
    pass

pg_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    max_idle=60,
    timeout=60,
    kwargs={"sslmode": "require", "connect_timeout": 10},
)

def _exec(sql: str, params: tuple = (), fetch: str = ""):
    """Execute a SQL statement safely with a one-time automatic retry.
    This fixes the issue where the first /start after a long idle period fails
    because the Postgres pool closed the idle connection. We refresh the pool and retry once.
    """
    global pg_pool
    for attempt in (1, 2):
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
        except Exception as e:
            if attempt == 1:
                try:
                    logger.warning("DB op failed (will refresh pool & retry once): %s", e)
                except Exception:
                    pass
                try:
                    try:
                        pg_pool.close()
                    except Exception:
                        pass
                    from psycopg_pool import ConnectionPool as _Pool
                    pg_pool = _Pool(
                        conninfo=DATABASE_URL,
                        min_size=1,
                        max_size=5,
                        max_idle=60,
                        timeout=60,
                        kwargs={"sslmode": "require", "connect_timeout": 10},
                    )
                except Exception:
                    pass
                try:
                    import time as _t; _t.sleep(0.2)
                except Exception:
                    pass
                continue
            raise


def _now():
    return datetime.now(timezone.utc)

# === إنشاء الجداول الأساسية ===
_exec("""CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    full_name TEXT,
    username  TEXT,
    balance   REAL DEFAULT 0,
    total_spent REAL DEFAULT 0
)""")

_exec("""CREATE TABLE IF NOT EXISTS moderators (
    user_id   BIGINT PRIMARY KEY,
    full_name TEXT,
    username  TEXT
)""")

# حظر المستخدمين
_exec("""CREATE TABLE IF NOT EXISTS blocked_users (
    user_id BIGINT PRIMARY KEY,
    until TIMESTAMPTZ,
    reason TEXT
)""")

# سجل محاولات كروت آسياسيل
_exec("""CREATE TABLE IF NOT EXISTS card_submissions (
    user_id BIGINT,
    digits TEXT,
    ts TIMESTAMPTZ DEFAULT NOW()
)""")
_exec("CREATE INDEX IF NOT EXISTS idx_card_sub_user_ts ON card_submissions(user_id, ts DESC)")

# كروت آسياسيل
_exec("""CREATE TABLE IF NOT EXISTS cards (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    full_name TEXT,
    username TEXT,
    card_number TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'pending',   -- pending/approved/rejected
    amount REAL
)""")
_exec("CREATE INDEX IF NOT EXISTS idx_cards_status ON cards(status)")

# جدول الطلبات العامة (سوشيال/تلغرام/ببجي/آيتونز)
_exec("""CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    full_name TEXT,
    username TEXT,
    category TEXT,               -- 'smm' | 'pubg' | 'itunes' | 'telegram'(ضمن smm) (للتوافق)
    service TEXT,
    price REAL,
    link TEXT,
    payload JSONB,
    status TEXT DEFAULT 'pending',  -- pending/completed/rejected/refunded/waiting
    api_order_number TEXT,
    api_service_number TEXT,
    refunded BOOLEAN DEFAULT FALSE,
    ordered_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
)""")
_exec("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, ordered_at DESC)")
_exec("CREATE INDEX IF NOT EXISTS idx_orders_status_cat ON orders(status, category)")

# === أكواد الخدمات (Overrides) + نظام الإحالة ===
# جدول overrides لتعيين service_id/quantity_multiplier مخصص لكل خدمة
_exec("""CREATE TABLE IF NOT EXISTS service_api_overrides (
    service_name TEXT PRIMARY KEY,
    service_id TEXT,
    quantity_multiplier INTEGER
)""")

# === أسعار الخدمات (Overrides) ===
_exec("""CREATE TABLE IF NOT EXISTS service_price_overrides (
    service_name TEXT PRIMARY KEY,
    price REAL
)""")

def db_get_price_override(service_name: str):
    row = _exec("SELECT price FROM service_price_overrides WHERE service_name=%s", (service_name,), "one")
    return None if not row else float(row[0])

def db_set_price_override(service_name: str, price: float):
    _exec("""INSERT INTO service_price_overrides (service_name, price)
             VALUES (%s,%s)
             ON CONFLICT(service_name) DO UPDATE SET price=EXCLUDED.price""",
          (service_name, float(price)))

def db_delete_price_override(service_name: str):
    _exec("DELETE FROM service_price_overrides WHERE service_name=%s", (service_name,))


def db_get_service_override(service_name: str):
    row = _exec("SELECT service_id, quantity_multiplier FROM service_api_overrides WHERE service_name=%s",
                (service_name,), "one")
    if not row:
        return None
    return {"service_id": row[0], "quantity_multiplier": row[1]}

def db_set_service_override(service_name: str, service_id: str, quantity_multiplier: int = None):
    qm = quantity_multiplier
    if qm is None:
        base = service_api_mapping.get(service_name) or {}
        qm = int(base.get("quantity_multiplier", 1000))
    _exec("""INSERT INTO service_api_overrides (service_name, service_id, quantity_multiplier)
             VALUES (%s,%s,%s)
             ON CONFLICT(service_name) DO UPDATE
             SET service_id=EXCLUDED.service_id, quantity_multiplier=EXCLUDED.quantity_multiplier""",
          (service_name, str(service_id), int(qm)))

def db_delete_service_override(service_name: str):
    _exec("DELETE FROM service_api_overrides WHERE service_name=%s", (service_name,))

# نظام الإحالة
REFERRAL_COMMISSION_USD = 0.10

_exec("""CREATE TABLE IF NOT EXISTS referrals (
    invitee_id BIGINT PRIMARY KEY,
    inviter_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    first_funding_at TIMESTAMPTZ,
    commission_paid BOOLEAN DEFAULT FALSE,
    commission_amount NUMERIC(10,2) DEFAULT 0.10
)""")
_exec("CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals(inviter_id)")

def db_set_referral_if_new(inviter_id: int, invitee_id: int):
    if not inviter_id or not invitee_id or inviter_id == invitee_id:
        return
    row = _exec("SELECT inviter_id FROM referrals WHERE invitee_id=%s", (invitee_id,), "one")
    if row:
        return
    _exec("INSERT INTO referrals (invitee_id, inviter_id, commission_amount) VALUES (%s,%s,%s)",
          (invitee_id, inviter_id, REFERRAL_COMMISSION_USD))

def db_get_referral_by_invitee(invitee_id: int):
    return _exec("SELECT inviter_id, commission_paid, commission_amount, first_funding_at FROM referrals WHERE invitee_id=%s",
                 (invitee_id,), "one")

def db_mark_first_funding_and_pay(invitee_id: int) -> int:
    row = db_get_referral_by_invitee(invitee_id)
    if not row:
        return 0
    inviter_id, commission_paid, commission_amount, _ = row
    if commission_paid:
        return 0
    _exec("UPDATE users SET balance = COALESCE(balance,0) + %s WHERE user_id=%s",
          (commission_amount, inviter_id))
    _exec("UPDATE referrals SET first_funding_at=NOW(), commission_paid=TRUE WHERE invitee_id=%s AND commission_paid=FALSE",
          (invitee_id,))
    try:
        sync_balance_from_db(inviter_id)
    except Exception as e:
        logger.error("sync inviter balance failed: %s", e)
    return inviter_id

def db_get_user_ref_stats(inviter_id: int):
    row = _exec("SELECT COUNT(*), SUM(CASE WHEN commission_paid THEN 1 ELSE 0 END), SUM(CASE WHEN NOT commission_paid THEN 1 ELSE 0 END), COALESCE(SUM(CASE WHEN commission_paid THEN commission_amount ELSE 0 END),0) FROM referrals WHERE inviter_id=%s", (inviter_id,), "one")
    total, paid, pending, total_earned = row or (0,0,0,0)
    invites = _exec("""SELECT r.invitee_id, u.full_name, u.username, r.commission_paid, r.created_at, r.first_funding_at
                       FROM referrals r LEFT JOIN users u ON r.invitee_id=u.user_id
                       WHERE r.inviter_id=%s ORDER BY r.created_at DESC LIMIT 10""", (inviter_id,), "all") or []
    return {"total": total or 0, "paid": paid or 0, "pending": pending or 0, "total_earned": float(total_earned or 0), "invites": invites}

def db_get_admin_ref_overview():
    row = _exec("SELECT COUNT(*), COALESCE(SUM(CASE WHEN commission_paid THEN commission_amount ELSE 0 END),0) FROM referrals", (), "one")
    total_refs, total_paid = row or (0,0)
    top = _exec("""SELECT r.inviter_id,
                           COALESCE(u.full_name, 'Unknown') AS full_name,
                           COALESCE(u.username, '') AS username,
                           COUNT(*) AS cnt,
                           SUM(CASE WHEN r.commission_paid THEN 1 ELSE 0 END) AS paid_cnt
                    FROM referrals r
                    LEFT JOIN users u ON u.user_id = r.inviter_id
                    GROUP BY r.inviter_id, u.full_name, u.username
                    ORDER BY cnt DESC
                    LIMIT 10""", (), "all") or []
    return {"total_refs": total_refs or 0, "total_paid": float(total_paid or 0), "top": top}



# =========================
# دوال DB: المستخدمين والرصيد
# =========================
def get_user_from_db(user_id: int):
    return _exec("SELECT user_id, full_name, username, balance, total_spent FROM users WHERE user_id=%s", (user_id,), "one")

def add_user_to_db(user_id: int, full_name: str, username: str):
    _exec("""INSERT INTO users (user_id, full_name, username)
             VALUES (%s,%s,%s)
             ON CONFLICT (user_id) DO UPDATE SET full_name=EXCLUDED.full_name, username=EXCLUDED.username""",
          (user_id, full_name or "Unknown", username or "NoUsername"))

def update_user_balance_in_db(user_id: int, balance: float):
    _exec("UPDATE users SET balance=%s WHERE user_id=%s", (balance, user_id))

def update_username_in_db(user_id: int, username: str):
    _exec("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))

def add_user_spent(user_id: int, amount: float):
    _exec("UPDATE users SET total_spent = COALESCE(total_spent,0) + %s WHERE user_id=%s", (amount, user_id))

def reduce_user_spent(user_id: int, amount: float):
    _exec("UPDATE users SET total_spent = GREATEST(COALESCE(total_spent,0) - %s, 0) WHERE user_id=%s", (amount, user_id))

def get_all_users():
    return _exec("SELECT user_id, full_name, username, balance, total_spent FROM users", fetch="all") or []

def get_users_with_balance_desc():
    return _exec("""SELECT user_id, full_name, username, balance, total_spent
                    FROM users WHERE balance > 0 ORDER BY balance DESC""", fetch="all") or []

def sync_balance_from_db(user_id: int):
    row = get_user_from_db(user_id)
    users_balance[user_id] = (row[3] if row else 0.0)

def sync_balance_to_db(user_id: int):
    bal = users_balance.get(user_id, 0.0)
    row = get_user_from_db(user_id)
    if row:
        update_user_balance_in_db(user_id, bal)
    else:
        add_user_to_db(user_id, "Unknown", "NoUsername")
        update_user_balance_in_db(user_id, bal)

# =========================
# دوال DB: المشرفون
# =========================
def _normalize_username(u: Optional[str]) -> Optional[str]:
    if not u: return None
    u = str(u).strip()
    return u[1:] if u.startswith("@") else u

def is_moderator(user_id: int) -> bool:
    row = _exec("SELECT 1 FROM moderators WHERE user_id=%s", (user_id,), "one")
    return row is not None

def add_moderator(user_id: int, full_name: str, username: str):
    username = _normalize_username(username) or "NoUsername"
    _exec("""INSERT INTO moderators (user_id, full_name, username)
             VALUES (%s,%s,%s)
             ON CONFLICT (user_id) DO UPDATE SET full_name=EXCLUDED.full_name, username=EXCLUDED.username""",
          (user_id, full_name or "Unknown", username))

def remove_moderator_by_identifier(identifier: str) -> bool:
    identifier = identifier.strip()
    if identifier.isdigit():
        rc = _exec("DELETE FROM moderators WHERE user_id=%s", (int(identifier),))
    else:
        uname = _normalize_username(identifier)
        rc = _exec("DELETE FROM moderators WHERE LOWER(username)=LOWER(%s)", (uname,))
    return (rc or 0) > 0

def list_moderators():
    return _exec("SELECT user_id, full_name, username FROM moderators ORDER BY user_id ASC", fetch="all") or []

# =========================
# دوال DB: الحظر و الحماية
# =========================
def _ban_user_for_hours(user_id: int, hours: int, reason: str):
    until = _now() + timedelta(hours=hours)
    _exec("""INSERT INTO blocked_users (user_id, until, reason)
             VALUES (%s,%s,%s)
             ON CONFLICT (user_id) DO UPDATE SET until=EXCLUDED.until, reason=EXCLUDED.reason""",
          (user_id, until, reason))

def _remaining_human(seconds: int) -> str:
    m = max(0, int(seconds))
    h = m // 3600; m %= 3600
    mm = m // 60; ss = m % 60
    parts = []
    if h: parts.append(f"{h}س")
    if mm: parts.append(f"{mm}د")
    if ss and not h: parts.append(f"{ss}ث")
    return " ".join(parts) or "قليل"

def _is_user_blocked_now(user_id: int) -> Optional[str]:
    if user_id == ADMIN_ID: return None
    row = _exec("SELECT until, reason FROM blocked_users WHERE user_id=%s", (user_id,), "one")
    if not row: return None
    until, reason = row
    if until and _now() >= until:
        _exec("DELETE FROM blocked_users WHERE user_id=%s", (user_id,))
        return None
    remain = int((until - _now()).total_seconds()) if until else 0
    reason = reason or "مخالفة سياسات الاستخدام."
    return f"تم حظرك لمدة مؤقتة.\nالسبب: {reason}\nالمدة المتبقية: {_remaining_human(remain)}"

def list_blocked_users():
    return _exec("SELECT user_id, until, reason FROM blocked_users ORDER BY until DESC", fetch="all") or []

def unblock_user(user_id: int):
    _exec("DELETE FROM blocked_users WHERE user_id=%s", (user_id,))

def _record_and_check_card(user_id: int, digits: str) -> Optional[str]:
    # سجل
    _exec("INSERT INTO card_submissions (user_id, digits, ts) VALUES (%s,%s,NOW())", (user_id, digits))
    # التكرار لنفس الرقم
    dup = _exec("""SELECT COUNT(*) FROM card_submissions WHERE user_id=%s AND digits=%s""", (user_id, digits), "one")[0]
    if dup > CARD_DUP_LIMIT:
        return "إدخال نفس رقم كارت آسياسيل أكثر من مرتين."
    # سبام خلال نافذة زمنية
    cnt = _exec("""SELECT COUNT(*) FROM card_submissions
                   WHERE user_id=%s AND ts >= NOW() - INTERVAL '%s seconds'""",
                (user_id, CARD_SPAM_WINDOW_SECONDS), "one")[0]
    if cnt > CARD_SPAM_COUNT:
        return "إرسال عدد كبير من كروت آسياسيل خلال وقت قصير."
    return None

# =========================
# دوال DB: الكروت
# =========================
def db_add_card(user_id:int, full_name:str, username:str, digits:str):
    _exec("""INSERT INTO cards (user_id, full_name, username, card_number, submitted_at, status)
             VALUES (%s,%s,%s,%s,NOW(),'pending')""", (user_id, full_name, username, digits))

def db_get_pending_cards():
    return _exec("""SELECT id, user_id, full_name, username, card_number, submitted_at
                    FROM cards WHERE status='pending' ORDER BY submitted_at ASC""", fetch="all") or []

def db_get_card(card_id:int):
    return _exec("""SELECT id, user_id, full_name, username, card_number, submitted_at, status, amount
                    FROM cards WHERE id=%s""", (card_id,), "one")

def db_approve_card(card_id:int, amount:float):
    _exec("UPDATE cards SET status='approved', amount=%s WHERE id=%s", (amount, card_id))

def db_reject_card(card_id:int):
    _exec("UPDATE cards SET status='rejected' WHERE id=%s", (card_id,))

# =========================
# دوال DB: الطلبات
# =========================
def db_add_order(user_id:int, full_name:str, username:str, category:str, service:str, price:float,
                 link:Optional[str], payload:Optional[dict]) -> int:
    row = _exec("""INSERT INTO orders (user_id, full_name, username, category, service, price, link, payload, status, ordered_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'pending',NOW())
                   RETURNING id""",
                 (user_id, full_name, username, category, service, price, link, psycopg.types.json.Json(payload) if payload else None),
                 "one")
    return int(row[0])

def db_get_pending_orders(category_filter:Optional[List[str]]=None):
    if category_filter:
        placeholders = ",".join(["%s"]*len(category_filter))
        return _exec(f"""SELECT id, user_id, full_name, username, category, service, price, link, ordered_at
                         FROM orders WHERE status='pending' AND category IN ({placeholders})
                         ORDER BY ordered_at ASC""", tuple(category_filter), "all") or []
    return _exec("""SELECT id, user_id, full_name, username, category, service, price, link, ordered_at
                    FROM orders WHERE status='pending' ORDER BY ordered_at ASC""", fetch="all") or []

def db_get_completed_api_orders():
    return _exec("""SELECT id, user_id, full_name, username, service, price, api_order_number
                    FROM orders
                    WHERE status='completed' AND api_order_number IS NOT NULL
                    ORDER BY completed_at DESC NULLS LAST, id DESC""", fetch="all") or []

def db_mark_order_completed_api(order_id:int, api_order:str, api_service:str):
    _exec("""UPDATE orders SET status='completed', api_order_number=%s, api_service_number=%s, completed_at=NOW()
             WHERE id=%s""", (api_order, api_service, order_id))

def db_mark_order_completed_manual(order_id:int):
    _exec("""UPDATE orders SET status='completed', completed_at=NOW() WHERE id=%s""", (order_id,))

def db_refund_order(order_id:int, user_id:int, amount:float):
    # استرجاع الرصيد وتعديل الطلب
    _exec("UPDATE users SET balance = COALESCE(balance,0) + %s WHERE user_id=%s", (amount, user_id))
    reduce_user_spent(user_id, amount)
    _exec("UPDATE orders SET status='refunded', refunded=TRUE WHERE id=%s", (order_id,))

def db_delete_order(order_id:int):
    _exec("DELETE FROM orders WHERE id=%s", (order_id,))

def db_get_user_orders(user_id:int, limit:int=10, offset:int=0):
    return _exec("""SELECT id, category, service, price, status, api_order_number, ordered_at, completed_at
                    FROM orders WHERE user_id=%s
                    ORDER BY ordered_at DESC
                    LIMIT %s OFFSET %s""", (user_id, limit, offset), "all") or []

def db_count_user_orders(user_id:int) -> int:
    return _exec("SELECT COUNT(*) FROM orders WHERE user_id=%s", (user_id,), "one")[0]

# =========================
# خصومات المشرفين
# =========================
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
# خصومات المشرفين (10% خصم ثابت على جميع الخدمات للمشرفين فقط)
# =========================
def get_effective_price(user_id: int, service_name: str, base_price: float, kind: str = "generic") -> float:
    try:
        bp = float(base_price)
        if is_moderator(user_id):
            return round(bp * 0.90, 2)
        return bp
    except Exception as e:
        logger.error("get_effective_price error: %s", e)
        return float(base_price)


# =========================
# دوال مساعدة: السعر الفعلي والعرض مع الخصم + تعيين كمية API
# =========================
def get_base_price(service_name: str, default_price: float) -> float:
    """يرجع سعر الأساس مع مراعاة أي override في قاعدة البيانات."""
    try:
        p = db_get_price_override(service_name)
        return float(p) if p is not None else float(default_price)
    except Exception:
        return float(default_price)

def get_display_price(user_id: int, service_name: str, default_price: float, kind: str="generic") -> float:
    """يُستخدم عند عرض الأزرار؛ يطبّق override ثم خصم المشرف (إن وُجد)."""
    base = get_base_price(service_name, default_price)
    return get_effective_price(user_id, service_name, base, kind)

def _get_default_service_id(service_name: str) -> str:
    base = service_api_mapping.get(service_name) or {}
    sid = base.get("service_id")
    return str(sid) if sid is not None else ""

def db_set_quantity_only(service_name: str, quantity_multiplier: int):
    """تحديث الكمية فقط مع الحفاظ على service_id الحالي إن وجد، أو الافتراضي."""
    ov = db_get_service_override(service_name) or {}
    sid = ov.get("service_id") or _get_default_service_id(service_name)
    if not sid:
        sid = _get_default_service_id(service_name)
    db_set_service_override(service_name, sid, int(quantity_multiplier))

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
            [InlineKeyboardButton("طلباتي", callback_data="my_orders")],
            [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
            [InlineKeyboardButton("الإحالة", callback_data="referral_panel")],
            [InlineKeyboardButton("لوحة تحكم المشرف", callback_data="moderator_menu")],
            [InlineKeyboardButton("المتصدرين🎉", callback_data="show_leaderboard")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الخدمات", callback_data="show_services")],
        [InlineKeyboardButton("طلباتي", callback_data="my_orders")],
        [InlineKeyboardButton("رصيدي", callback_data="show_balance")],
        [InlineKeyboardButton("الإحالة", callback_data="referral_panel")],
        [InlineKeyboardButton("المتصدرين🎉", callback_data="show_leaderboard")]
    ])

def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")],
        [InlineKeyboardButton("الطلبات المعلّقة (الخدمات)", callback_data="pending_smm_orders")],
        [InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")],
        [InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders")],
        [InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")],
        [InlineKeyboardButton("طلبات الارصدة المعلقة", callback_data="pending_mobile_orders")],
        [InlineKeyboardButton("طلبات لودو المعلقة", callback_data="pending_ludo_orders")],
        [InlineKeyboardButton("إضافة الرصيد", callback_data="admin_add_balance"), InlineKeyboardButton("خصم الرصيد", callback_data="admin_discount")],
        [InlineKeyboardButton("فحص رصيد API", callback_data="api_check_balance"), InlineKeyboardButton("فحص حالة طلب API", callback_data="api_order_status")],
        [InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count"), InlineKeyboardButton("رصيد المستخدمين", callback_data="admin_users_balance")],
        [InlineKeyboardButton("إدارة المشرفين", callback_data="manage_mods")],
        [InlineKeyboardButton("حضر المستخدم", callback_data="block_user"), InlineKeyboardButton("الغاء حظر المستخدم", callback_data="unblock_user")],
        [InlineKeyboardButton("اعلان البوت", callback_data="admin_announce")],
        [InlineKeyboardButton("أكواد خدمات API", callback_data="admin_service_codes")],
        [InlineKeyboardButton("نظام الإحالة", callback_data="admin_referrals")]
    ]
    buttons.append([InlineKeyboardButton("شرح الخصومات", callback_data="admin_discounts_info")])
    buttons.append([InlineKeyboardButton("المتصدرين🎉", callback_data="show_leaderboard")])
    return InlineKeyboardMarkup(buttons)



# =========================
# محرر أسعار وكميات الخدمات (لوحة المالك)
# =========================
def _ap_build_catalog():
    """يبني كتالوج الخدمات من القواميس الحالية (اسم التصنيف، اسم الخدمة، السعر الافتراضي)."""
    catalog = {
        "smm": list(services_dict.keys()),
        "pubg": list(pubg_services.keys()),
        "itunes": list(itunes_services.keys()),
        "telegram": list(telegram_services.keys()),
        "mobile": list(mobile_recharge_services.keys()),
        "ludo": list(ludo_services.keys())
    }
    return catalog

def _ap_show_categories(query):
    kb = [
        [InlineKeyboardButton("سوشيال (SMM)", callback_data="ap_cat_smm")],
        [InlineKeyboardButton("PUBG", callback_data="ap_cat_pubg")],
        [InlineKeyboardButton("iTunes", callback_data="ap_cat_itunes")],
        [InlineKeyboardButton("Telegram", callback_data="ap_cat_telegram")],
        [InlineKeyboardButton("Mobile رصيد", callback_data="ap_cat_mobile")],
        [InlineKeyboardButton("Ludo", callback_data="ap_cat_ludo")],
        [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
    ]
    query.edit_message_text("اختر القسم الذي تريد تعديل أسعاره/كمياته:", reply_markup=InlineKeyboardMarkup(kb))

def _ap_list_services(update: Update, context: CallbackContext, query, cat: str, page: int = 0, page_size: int = 10):
    catalog = _ap_build_catalog()
    items = catalog.get(cat, [])
    total = len(items)
    start = page * page_size
    end = min(total, start + page_size)
    if start >= total and total > 0:
        page = 0; start = 0; end = min(total, page_size)
    view = items[start:end]

    # خزّن الخريطة
    context.user_data["ap_map"] = items
    context.user_data["ap_cat"] = cat
    context.user_data["ap_page"] = page

    lines = [f"القسم: {cat} — الصفحة {page+1}/{(total-1)//page_size+1 if total else 1}", ""]
    for i, name in enumerate(view, start=start):
        # السعر الحالي
        default_price = (
            services_dict.get(name) if cat=="smm" else
            pubg_services.get(name) if cat=="pubg" else
            itunes_services.get(name) if cat=="itunes" else
            telegram_services.get(name) if cat=="telegram" else
            mobile_recharge_services.get(name) if cat=="mobile" else
            ludo_services.get(name) if cat=="ludo" else 0
        )
        base = get_base_price(name, default_price or 0)
        has_qty = (name in service_api_mapping)
        qty_txt = ""
        if has_qty:
            ov = db_get_service_override(name) or {}
            q = ov.get("quantity_multiplier") or (service_api_mapping.get(name) or {}).get("quantity_multiplier")
            qty_txt = f" | الكمية: {q}"
        lines.append(f"- #{i} • {name} • السعر: {base}${qty_txt}")

    buttons = []
    # أزرار الخدمات (كل زر يفتح صفحة الخدمة)
    for i, name in enumerate(view, start=start):
        buttons.append([InlineKeyboardButton(f"⚙️ تعديل #{i}", callback_data=f"ap_sel_{i}")])

    # تنقل
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"ap_page_{cat}_{max(0,page-1)}"))
    if end < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"ap_page_{cat}_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_edit_prices")])

    try:
        query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))

def _ap_show_service_actions(update: Update, context: CallbackContext, query, idx: int):
    items = context.user_data.get("ap_map") or []
    if idx < 0 or idx >= len(items):
        query.answer("خيار غير صالح.", show_alert=True); return
    name = items[idx]
    has_qty = (name in service_api_mapping)

    btns = [[InlineKeyboardButton("💲 تعديل السعر", callback_data=f"ap_setprice_{idx}")]]
    if has_qty:
        btns.append([InlineKeyboardButton("📦 تعديل الكمية", callback_data=f"ap_setqty_{idx}")])
    btns.append([InlineKeyboardButton("❌ حذف تعديل السعر", callback_data=f"ap_delprice_{idx}")])
    if has_qty:
        btns.append([InlineKeyboardButton("↩️ إعادة الكمية للافتراضي", callback_data=f"ap_delqty_{idx}")])
    btns.append([InlineKeyboardButton("رجوع", callback_data=f"ap_page_{context.user_data.get('ap_cat','smm')}_{context.user_data.get('ap_page',0)}")])
    query.edit_message_text(f"الخدمة:\n• {name}\nاختر الإجراء:", reply_markup=InlineKeyboardMarkup(btns))

# ======= خدمات شراء رصيد الهاتف (قسم جديد) =======
mobile_recharge_services = {
    "شراء رصيد 2دولار اثير": 2.0,
    "شراء رصيد 5دولار اثير": 5.0,
    "شراء رصيد 10دولار اثير": 10.0,
    "شراء رصيد 15دولار اثير": 15.0,
    "شراء رصيد 40دولار اثير": 40.0,
    "شراء رصيد 2دولار اسيا": 2.0,
    "شراء رصيد 5دولار اسيا": 5.0,
    "شراء رصيد 10دولار اسيا": 10.0,
    "شراء رصيد 15دولار اسيا": 15.0,
    "شراء رصيد 40دولار اسيا": 40.0,
    "شراء رصيد 2دولار كورك": 2.0,
    "شراء رصيد 5دولار كورك": 5.0,
    "شراء رصيد 10دولار كورك": 10.0,
    "شراء رصيد 15دولار كورك": 15.0,
    "شراء رصيد 40دولار كورك": 40.0,
}

def mobile_recharge_services_keyboard(user_id: int):
    buttons = []
    for service_name, base_price in mobile_recharge_services.items():
        eff = get_display_price(user_id, service_name, base_price, "mobile")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"mobile_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)


# ======== Helpers: تنسيق العرض وإزالة k ووضع الكمية بين قوسين ========
import re as _re

def _strip_k_digits(s: str) -> str:
    return s.replace("k", "").replace("K", "")

def _extract_qty_from_name(name: str) -> int:
    m = _re.search(r'(\d+)\s*k\b', name, flags=_re.IGNORECASE)
    if not m:
        m = _re.search(r'(\d+)k\b', name, flags=_re.IGNORECASE)
    if not m:
        m = _re.search(r'(\d+)k', name, flags=_re.IGNORECASE)
    if m:
        try: return int(m.group(1)) * 1000
        except: pass

    m = _re.search(r'(\d+)\s*شدة', name)
    if m:
        try: return int(m.group(1))
        except: pass

    m = _re.search(r'شراء\s*رصيد\s+(\d+)\s*ايتونز', name)
    if m:
        try: return int(m.group(1))
        except: pass

    m = _re.search(r'شراء\s*رصيد\s+(\d+)\s*دولار\s*(?:اثير|اسيا|كورك)', name)
    if m:
        try: return int(m.group(1))
        except: pass

    m = _re.search(r'لودو\s+(\d+)\s*(?:الماسة|ذهب)', name)
    if m:
        try: return int(m.group(1))
        except: pass

    m = _re.search(r'(\d+)\s*k', name, flags=_re.IGNORECASE)
    if m:
        try: return int(m.group(1)) * 1000
        except: pass

    m = _re.findall(r'(\d+)', name)
    if m:
        try: return int(m[-1])
        except: pass
    return None

def _remove_qty_fragment(name: str) -> str:
    patterns = [
        r'\s*\d+\s*k\b', r'\s*\d+k\b',
        r'\s*\d+\s*شدة',
        r'\s*\d+\s*ايتونز',
        r'\s*\d+\s*دولار\s*(?:اثير|اسيا|كورك)',
        r'\s*\d+\s*(?:الماسة|ذهب)',
        r'بثك\s*\d+\s*k\b',
    ]
    base = name
    for pat in patterns:
        base = _re.sub(pat + r'$', '', base, flags=_re.IGNORECASE).strip()
    return _strip_k_digits(base).strip()


def get_effective_quantity(service_name: str):
    """
    يرجع الكمية الفعلية المعرّفة للخدمة حسب الأولوية:
    1) override من جدول service_api_overrides (إن وجد).
    2) القيمة الافتراضية من service_api_mapping (إن وجدت).
    3) استخراج تقديري من الاسم (لغير API).
    4) None إذا لا يوجد.
    """
    try:
        ov = db_get_service_override(service_name) or {}
        q = ov.get("quantity_multiplier")
        if q:
            try:
                return int(q)
            except:
                pass
        base_map = service_api_mapping.get(service_name) or {}
        q = base_map.get("quantity_multiplier")
        if q:
            try:
                return int(q)
            except:
                pass
    except Exception as _e:
        # تجاهل ونكمل بالاستخراج من الاسم
        pass
    # خدمات لا تدعم API: نُقدّر من الاسم
    return _extract_qty_from_name(service_name)

def display_label_for_service(service_name: str, eff_price: float) -> str:
    qty = get_effective_quantity(service_name)
    qty_txt = f"{qty}" if (isinstance(qty, int) and qty > 0) else ""
    title = _remove_qty_fragment(service_name)
    lower = service_name
    if "شدة" in lower:
        return f"{_strip_k_digits(title)} ({qty_txt}) شدة - {eff_price}$"
    if "ايتونز" in lower:
        return f"شراء رصيد ({qty_txt}) ايتونز - {eff_price}$"
    if "دولار اثير" in lower:
        return f"شراء رصيد ({qty_txt}) دولار اثير - {eff_price}$"
    if "دولار اسيا" in lower or "دولار اسي" in lower:
        return f"شراء رصيد ({qty_txt}) دولار اسيا - {eff_price}$"
    if "دولار كورك" in lower:
        return f"شراء رصيد ({qty_txt}) دولار كورك - {eff_price}$"
    if "لودو" in lower and ("الماسة" in lower or "ذهب" in lower):
        tail = "الماسة" if "الماسة" in lower else "ذهب" if "ذهب" in lower else ""
        return f"لودو ({qty_txt}) {tail} - {eff_price}$"
    return f"{_strip_k_digits(title)} {eff_price}$ - ({qty_txt})"

def services_menu_keyboard_for(user_id: int):
    # نسخة مفلترة لإخفاء زر تعديل الأسعار والكميات عن غير المالك
    buttons = [
        [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")],
        [InlineKeyboardButton("قسم المتابعين", callback_data="show_followers")],
        [InlineKeyboardButton("قسم اللايكات", callback_data="show_likes")],
        [InlineKeyboardButton("قسم المشاهدات", callback_data="show_views")],
        [InlineKeyboardButton("قسم مشاهدات البث المباشر", callback_data="show_live_views")],
        [InlineKeyboardButton("قسم شحن شدات ببجي", callback_data="show_pubg")],
        [InlineKeyboardButton("رفع سكور تيكتوك", callback_data="show_tiktok_score")],
        [InlineKeyboardButton("قسم شراء رصيد ايتونز", callback_data="show_itunes_services")],
        [InlineKeyboardButton("قسم شراء رصيد الهاتف", callback_data="show_mobile_recharge")],
        [InlineKeyboardButton("خدمات التليجرام", callback_data="show_telegram_services")],
        [InlineKeyboardButton("خدمات لودو", callback_data="show_ludo_services")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    if user_id != ADMIN_ID:
        buttons = buttons[1:]  # إزالة زر التعديل
    return InlineKeyboardMarkup(buttons)
def services_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")],
        [InlineKeyboardButton("قسم المتابعين", callback_data="show_followers")],
        [InlineKeyboardButton("قسم اللايكات", callback_data="show_likes")],
        [InlineKeyboardButton("قسم المشاهدات", callback_data="show_views")],
        [InlineKeyboardButton("قسم مشاهدات البث المباشر", callback_data="show_live_views")],
        [InlineKeyboardButton("قسم شحن شدات ببجي", callback_data="show_pubg")],
        [InlineKeyboardButton("رفع سكور تيكتوك", callback_data="show_tiktok_score")],
        [InlineKeyboardButton("قسم شراء رصيد ايتونز", callback_data="show_itunes_services")],
        [InlineKeyboardButton("قسم شراء رصيد الهاتف", callback_data="show_mobile_recharge")],
        [InlineKeyboardButton("خدمات التليجرام", callback_data="show_telegram_services")],
        [InlineKeyboardButton("خدمات لودو", callback_data="show_ludo_services")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def tiktok_score_keyboard(user_id: int, context: CallbackContext):
    score_services = [(k, v) for k, v in services_dict.items() if ("رفع سكور" in k)]
    context.user_data["score_map"] = [name for name, _ in score_services]
    service_buttons = []
    for idx, (service_name, price) in enumerate(score_services):
        eff = get_display_price(user_id, service_name, price, "generic")
        service_buttons.append([InlineKeyboardButton(display_label_for_service(service_name, eff), callback_data=f"score_service_{idx}")])
    service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(service_buttons)

def itunes_services_keyboard(user_id: int):
    buttons = []
    for service_name, price in itunes_services.items():
        eff = get_display_price(user_id, service_name, price, "itunes")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"itunes_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)

def telegram_services_keyboard(user_id: int):
    buttons = []
    for service_name, price in telegram_services.items():
        eff = get_display_price(user_id, service_name, price, "telegram")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"telegram_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)


def ludo_services_keyboard(user_id: int):
    buttons = []
    for service_name, price in ludo_services.items():
        eff = get_display_price(user_id, service_name, price, "ludo")
        buttons.append([InlineKeyboardButton(f"{service_name} - {eff}$", callback_data=f"ludo_service_{service_name}")])
    buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
    return InlineKeyboardMarkup(buttons)


def clear_all_waiting_flags(context: CallbackContext):
    waiting_keys = ["waiting_for_card", "waiting_for_block", "waiting_for_add_balance_user_id",
        "waiting_for_add_balance_amount", "waiting_for_discount_user_id", "waiting_for_discount_amount",
        "waiting_for_broadcast", "waiting_for_api_order_status", "selected_service", "service_price",
        "selected_pubg_service", "pubg_service_price", "selected_ludo_service", "ludo_service_price", "card_to_approve", "card_to_approve_id", "waiting_for_amount",
        "selected_itunes_service", "itunes_service_price", "waiting_for_itunes_confirm",
        "waiting_for_itunes_code", "itunes_to_complete_id", "selected_mobile_service", "mobile_service_price", "waiting_for_mobile_confirm", "waiting_for_mobile_code", "mobile_to_complete_id",
        "selected_telegram_service", "telegram_service_price", "waiting_for_telegram_link",
        "waiting_for_new_mod", "waiting_for_remove_mod", "admin_target_id",
        "score_map",
        "my_orders_offset", "waiting_for_bulk_service_code", "__target_services__", "__groups__", "waiting_for_price_edit_service", "waiting_for_qty_edit_service", "ap_map", "ap_cat", "ap_page"]
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

# ======= أدوات التجميع + بوابة المالك + يوزرنيم البوت =======
def _normalize_ar_text(s: str) -> str:
    s = (s or "").lower()
    rep = {"أ":"ا","إ":"ا","آ":"ا","ى":"ي","ة":"ه","ؤ":"و","ئ":"ي"}
    for k,v in rep.items():
        s = s.replace(k, v)
    return s

_PLAT_KEYWORDS = {
    "tiktok": ["tiktok","تيك","تيكتوك","تك توك","تيك توك"],
    "instagram": ["instagram","انست","انستا","انستغرام","الانستا"],
    "youtube": ["youtube","يوتيوب"],
    "telegram": ["telegram","تليجرام","تلي","تليغرام"],
    "facebook": ["facebook","فيس","فيسبوك"],
    "x": ["x","تويتر","twitter","تويتر اكس"],
    "snapchat": ["snap","سناب","سناب شات"],
    "twitch": ["twitch","تويتش"],
}

_TYPE_KEYWORDS = {
    "مشاهدات بث": ["مشاهدات بث","مشاهدات البث","مشاهدة البث","بث مباشر","لايف","live","live views"],
    "أعضاء قنوات": ["اعضاء قنوات","اعضاء قناة","قناة","قنوات","channel members","channel"],
    "أعضاء كروبات": ["اعضاء كروبات","اعضاء كروب","كروب","كروبات","group members","group"],
    "مشاهدات": ["مشاهده","مشاهدات","view","views"],
    "متابعين": ["متابع","متابعين","followers","فولو"],
    "لايكات": ["لايك","لايكات","like","likes","اعجابات","اعجاب"],
    "تعليقات": ["تعليق","تعليقات","comments","كومنت"],
    "ساعات مشاهدة": ["ساعات","watch time","ساعات مشاهده"],
    "مشتركين": ["مشترك","مشتركين","subscribers","subs"],
    "رفع سكور": ["رفع سكور","سكور","score","boost score"],
}


EXCLUDE_GROUPS = {"رفع سكور instagram"}

def _detect_platform_and_type(service_name: str):
    n = _normalize_ar_text(service_name)
    plat = "أخرى"; typ = "أخرى"
    for p, keys in _PLAT_KEYWORDS.items():
        if any(k in n for k in keys): plat = p; break
    for t, keys in _TYPE_KEYWORDS.items():
        if any(k in n for k in keys): typ = t; break
    return plat, typ

def build_service_groups():
    groups = {}
    for name in service_api_mapping.keys():
        plat, typ = _detect_platform_and_type(name)
        if plat == "أخرى" and typ == "أخرى":
            key = "أخرى"
        elif typ == "أخرى":
            key = f"أخرى {plat}"
        elif plat == "أخرى":
            key = f"{typ}"
        else:
            key = f"{typ} {plat}"
        if key in EXCLUDE_GROUPS: continue
        groups.setdefault(key, []).append(name)
    ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return ordered

def _parse_service_code_only(s: str):
    s = (s or "").strip()
    import re as _re
    m = _re.search(r"\d+", s)
    if not m: return None
    return m.group(0)

def _admin_text_gate(update: Update, context: CallbackContext):

    if context.user_data.get("waiting_for_price_edit_service"):
        srv = context.user_data.get("waiting_for_price_edit_service")
        try:
            val = float((update.message.text or "").strip().replace(",", "."))
            if val <= 0:
                update.message.reply_text("السعر يجب أن يكون أكبر من 0. أرسل رقمًا صالحًا أو اضغط رجوع من لوحة الأسعار.")
                return True
            db_set_price_override(srv, val)
            context.user_data.pop("waiting_for_price_edit_service", None)
            update.message.reply_text(f"تم حفظ السعر الجديد لخدمة:\n• {srv}\nالسعر: {val}$",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_edit_prices")]]))
        except Exception as e:
            update.message.reply_text("تعذّر حفظ السعر. تأكد من إرسال رقم صحيح مثل 7.5")
        return True

    if context.user_data.get("waiting_for_qty_edit_service"):
        srv = context.user_data.get("waiting_for_qty_edit_service")
        txt = (update.message.text or "").strip()
        if not txt.isdigit():
            update.message.reply_text("أرسل رقمًا صحيحًا للكمية (عدد صحيح).")
            return True
        q = int(txt)
        if q <= 0:
            update.message.reply_text("الكمية يجب أن تكون رقمًا صحيحًا أكبر من صفر.")
            return True
        try:
            db_set_quantity_only(srv, q)
            context.user_data.pop("waiting_for_qty_edit_service", None)
            update.message.reply_text(f"تم تحديث الكمية (quantity_multiplier) لخدمة:\n• {srv}\nالكمية: {q}",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_edit_prices")]]))
        except Exception as e:
            update.message.reply_text("تعذّر حفظ الكمية. حاول مرة أخرى.")
        return True

    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return False
    if context.user_data.get("waiting_for_bulk_service_code"):
        target_services = context.user_data.get("__target_services__") or []
        sid = _parse_service_code_only(update.message.text or "")
        if not sid:
            update.message.reply_text("رجاءً أرسل رقم كود الـAPI فقط (مثال: 13912)."); return True
        count = 0
        for srv in target_services:
            try: db_set_service_override(srv, sid, None); count += 1
            except Exception as e: logger.error("bulk set override failed for %s: %s", srv, e)
        context.user_data.pop("waiting_for_bulk_service_code", None)
        context.user_data.pop("__target_services__", None)
        update.message.reply_text(f"تم تعيين الكود {sid} لعدد {count} خدمة داخل المجموعة ✅",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_service_codes")]]))
        return True
    return False

def _get_bot_username(context: CallbackContext) -> str:
    try:
        if getattr(context.bot, "username", None): return context.bot.username
        me = context.bot.get_me()
        if me and me.username:
            context.bot.username = me.username; return me.username
    except Exception as e: logger.error("get_me failed: %s", e)
    return "YourBot"


# =========================
def start(update: Update, context: CallbackContext):
    # حذف رسالة /start السابقة إن وجدت
    try:
        prev_id = context.user_data.get('last_start_menu_message_id')
        if prev_id:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prev_id)
            context.user_data['last_start_menu_message_id'] = None
    except Exception as _e:
        logger.debug('Could not delete previous start menu: %s', _e)
    user_id = update.effective_user.id
    clear_all_waiting_flags(context)

    # إحالة عبر رابط البدء
    try:
        _t = update.message.text or ""
        if _t.startswith("/start "):
            _payload = _t.split(" ", 1)[1].strip()
            if _payload.startswith("ref_"):
                _inv = int(_payload.replace("ref_", "").strip())
                if _inv and _inv != user_id:
                    existed = db_get_referral_by_invitee(user_id)
                    if not existed:
                        db_set_referral_if_new(_inv, user_id)
                        try:
                            context.bot.send_message(chat_id=_inv, text="👥 تمت إضافة إحالة جديدة عبر رابطك. سيتم دفع العمولة بعد أول شحن لصديقك.")
                        except Exception: pass
                        try:
                            context.bot.send_message(chat_id=user_id, text=f"تم ربط حسابك بالمُحيل (ID:{_inv}).")
                        except Exception: pass
    except Exception as e:
        logger.error("referral capture failed: %s", e)

    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        update.message.reply_text(ban_msg)
        return

    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    add_user_to_db(user_id, full_name, username)
    update_username_in_db(user_id, username)
    sync_balance_from_db(user_id)

    msg = update.message.reply_text("مرحباً بك في البوت!", reply_markup=main_menu_keyboard(user_id))
    context.user_data["last_start_menu_message_id"] = msg.message_id

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
# تنفيذ الطلب عبر API عند الموافقة (DB)
# =========================
def approve_order_process_db(order_id: int, context: CallbackContext, query):
    row = _exec("""SELECT id, user_id, full_name, username, category, service, price, link
                   FROM orders WHERE id=%s AND status='pending'""", (order_id,), "one")
    if not row:
        query.answer("الطلب غير موجود أو ليس معلقاً.", show_alert=True)
        return

    _, uid, fn, un, cat, service_name, price, link = row

    if service_name in service_api_mapping:
        mapping = service_api_mapping[service_name].copy()
        try:
            ov = db_get_service_override(service_name)
            if ov:
                if ov.get('service_id'): mapping['service_id'] = ov['service_id']
                if ov.get('quantity_multiplier'): mapping['quantity_multiplier'] = int(ov['quantity_multiplier'])
        except Exception as _e:
            logger.error('override read error for %s: %s', service_name, _e)
        params = {
            'key': API_KEY,
            'action': 'add',
            'service': mapping['service_id'],
            'link': link,
            'quantity': mapping['quantity_multiplier']
        }
        try:
            response = requests.post(API_URL, data=params, timeout=25)
            api_response = response.json()
        except Exception:
            api_response = {"error": "فشل استدعاء API"}

        if "order" in api_response:
            db_mark_order_completed_api(order_id, str(api_response["order"]), str(mapping["service_id"]))
            try:
                context.bot.send_message(chat_id=uid, text=f"تم استلام طلبك وسوف يتم تنفيذه قريباً\nرقم طلبك ({api_response['order']})")
            except Exception:
                pass
            query.edit_message_text("تم تنفيذ الطلب عبر API وإشعار المستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
        else:
            # استرجاع المبلغ للمستخدم
            _exec("UPDATE users SET balance = COALESCE(balance,0) + %s WHERE user_id=%s", (price, uid))
            reduce_user_spent(uid, price)
            _exec("UPDATE orders SET status='refunded', refunded=TRUE WHERE id=%s", (order_id,))
            try:
                context.bot.send_message(chat_id=uid, text="فشل تنفيذ الطلب عبر النظام الخارجي، تمت إعادة المبلغ لرصيدك.")
            except Exception:
                pass
            query.edit_message_text("فشل تنفيذ الطلب عبر API وتمت إعادة الرصيد للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
    else:
        db_mark_order_completed_manual(order_id)
        try:
            context.bot.send_message(chat_id=uid, text="تم إكمال طلبك بنجاح.")
        except Exception:
            pass
        query.edit_message_text("تم تأكيد الطلب وإشعار المستخدم.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))

# =========================
# أزرار (Callback)
# =========================
# ===== شرح خصومات المشرف (نص موحد) =====
def get_mod_discount_help_text() -> str:
    return (
        "💡 <b>خصومات المشرف:</b>\n"
        "• خصم ثابت <b>10٪</b> على جميع الخدمات داخل البوت.\n"
        "• يُطبَّق الخصم تلقائيًا عند <b>عرض الأسعار</b> و<b>خصم الرصيد</b> و<b>تسجيل الطلب</b>."
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # ======== محرر الأسعار والكميات (مالك) ========
    if data == "admin_edit_prices":
        if user_id != ADMIN_ID:
            query.edit_message_text("عذراً، هذه الصفحة للمالك فقط.")
            return
        _ap_show_categories(query); return

    if data.startswith("ap_page_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        parts = data.split("_", 2)[2].split("_")
        cat = parts[0]; page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        _ap_list_services(update, context, query, cat, page); return

    if data.startswith("ap_cat_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        cat = data.replace("ap_cat_", "")
        _ap_list_services(update, context, query, cat, 0); return

    if data.startswith("ap_sel_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        try:
            idx = int(data.replace("ap_sel_", ""))
        except Exception:
            query.answer("خيار غير صالح.", show_alert=True); return
        _ap_show_service_actions(update, context, query, idx); return

    if data.startswith("ap_setprice_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        idx = int(data.replace("ap_setprice_", ""))
        items = context.user_data.get("ap_map") or []
        if idx < 0 or idx >= len(items):
            query.answer("خيار غير صالح.", show_alert=True); return
        srv = items[idx]
        context.user_data["waiting_for_price_edit_service"] = srv
        query.edit_message_text(f"أرسل السعر الجديد بالدولار لخدمة:\n• {srv}\nمثال: 7.5",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=f"ap_sel_{idx}")]]))
        return

    if data.startswith("ap_setqty_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        idx = int(data.replace("ap_setqty_", ""))
        items = context.user_data.get("ap_map") or []
        if idx < 0 or idx >= len(items):
            query.answer("خيار غير صالح.", show_alert=True); return
        srv = items[idx]
        if srv not in service_api_mapping:
            query.answer("هذه الخدمة لا تملك كمية قابلة للتعديل.", show_alert=True); return
        context.user_data["waiting_for_qty_edit_service"] = srv
        query.edit_message_text(f"أرسل الكمية الجديدة (عدد صحيح) لخدمة:\n• {srv}\nمثال: 5000",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=f"ap_sel_{idx}")]]))
        return

    if data.startswith("ap_delprice_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        idx = int(data.replace("ap_delprice_", ""))
        items = context.user_data.get("ap_map") or []
        if idx < 0 or idx >= len(items):
            query.answer("خيار غير صالح.", show_alert=True); return
        srv = items[idx]
        db_delete_price_override(srv)
        query.edit_message_text(f"تم حذف تعديل السعر والعودة للسعر الافتراضي.\n• {srv}",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=f"ap_sel_{idx}")]]))
        return

    if data.startswith("ap_delqty_"):
        if user_id != ADMIN_ID: 
            query.answer("غير مسموح.", show_alert=True); return
        idx = int(data.replace("ap_delqty_", ""))
        items = context.user_data.get("ap_map") or []
        if idx < 0 or idx >= len(items):
            query.answer("خيار غير صالح.", show_alert=True); return
        srv = items[idx]
        # إعادة الكمية للافتراصي (إما حذف السجل أو إعادة تعيينه)
        try:
            # نحافظ على service_id لو موجود
            base_q = (service_api_mapping.get(srv) or {}).get("quantity_multiplier", 1000)
            db_set_quantity_only(srv, base_q)
        except Exception:
            pass
        query.edit_message_text(f"تمت إعادة الكمية للافتراصي.\n• {srv}",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data=f"ap_sel_{idx}")]]))
        return


    # شرح الخصومات للمشرفين
    if data == "mod_discount_info" and is_moderator(user_id):
        try:
            query.edit_message_text(
                get_mod_discount_help_text(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="show_services")]])
            )
        except Exception:
            context.bot.send_message(chat_id=update.effective_chat.id, text=get_mod_discount_help_text(), parse_mode="HTML")
        return

    query.answer()

    clear_all_waiting_flags(context)

    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        query.answer(ban_msg, show_alert=True)
        return

    if data == "back_main":
        query.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu_keyboard(user_id))
        return
    # لوحة الإحالة للمستخدم
    if data == "referral_panel":
        uname = _get_bot_username(context)
        link = f"https://t.me/{uname}?start=ref_{user_id}"
        stats = db_get_user_ref_stats(user_id)
        lines = [
            "👥 نظام الإحالة\n",
            f"🔗 رابطك: {link}",
            f"📣 عدد المدعوين: {stats.get('total',0)}",
            f"💸 أرباح مدفوعة: {stats.get('paid',0)} شخص = {stats.get('total_earned',0):.2f}$",
            f"⏳ بانتظار الدفع: {stats.get('pending',0)}",
            "", "آخر المدعوين:"
        ]
        for it in stats.get("invites", []):
            iid, fn, un, paid, created_at, first_at = it
            tag = "✅" if paid else "⏳"
            uname2 = f"@{un}" if un and un != "NoUsername" else ""
            lines.append(f"- {fn} {uname2} — {tag}")
        buttons = [[InlineKeyboardButton("رجوع", callback_data="back_main")]]
        query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "show_services":
        query.edit_message_text("اختر القسم:", reply_markup=services_menu_keyboard_for(user_id))
        return

    # ======= المتصدرين🎉 =======
    if data == "show_leaderboard":
        top = _exec("""SELECT user_id, full_name, username, total_spent
                       FROM users ORDER BY total_spent DESC, user_id ASC LIMIT 10""", fetch="all") or []
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

    # ======= عرض الأقسام بأسعار =======
    if data == "show_followers":
        followers_services = {k: v for k, v in services_dict.items() if "متابعين" in k}
        service_buttons = []
        for name, price in followers_services.items():
            eff = get_display_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(display_label_for_service(name, eff), callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_likes":
        likes_services = {k: v for k, v in services_dict.items() if "لايكات" in k}
        service_buttons = []
        for name, price in likes_services.items():
            eff = get_display_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(display_label_for_service(name, eff), callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_views":
        views_services = {k: v for k, v in services_dict.items() if ("مشاهدات تيكتوك" in k or "مشاهدات انستغرام" in k)}
        service_buttons = []
        for name, price in views_services.items():
            eff = get_display_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(display_label_for_service(name, eff), callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_live_views":
        live_views_services = {k: v for k, v in services_dict.items() if "مشاهدات بث" in k}
        service_buttons = []
        for name, price in live_views_services.items():
            eff = get_display_price(user_id, name, price, "generic")
            service_buttons.append([InlineKeyboardButton(display_label_for_service(name, eff), callback_data=f"service_{name}")])
        service_buttons.append([InlineKeyboardButton("رجوع", callback_data="show_services")])
        query.edit_message_text("اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(service_buttons))
        return

    if data == "show_tiktok_score":
        query.edit_message_text("اختر خدمة رفع سكور تيكتوك المطلوبة:", reply_markup=tiktok_score_keyboard(user_id, context))
        return

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
        base_price = services_dict.get(service_name)
        base_price = get_base_price(service_name, base_price if base_price is not None else 0.0)
        if services_dict.get(service_name) is None:
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
                [InlineKeyboardButton("رجوع", callback_data="show_followers")]
            ]
            if user_id == ADMIN_ID:
                buttons.insert(0, [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")])
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        # تعليمات الإدخال
        message_text = (
            "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:\n"
            "🔴 ملاحظة: أرسل <b>الرابط</b> وليس اليوزرنيم!"
        )
        context.user_data["selected_service"] = service_name
        context.user_data["service_price"] = price
        query.edit_message_text(message_text, parse_mode="HTML")
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
        base_price = get_base_price(service_name, base_price if base_price is not None else 0.0)
        if services_dict.get(service_name) is None:
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
                [InlineKeyboardButton("رجوع", callback_data="show_followers")]
            ]
            if user_id == ADMIN_ID:
                buttons.insert(0, [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")])
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return

        # تعليمات خاصة لبعض الخدمات
        if "انستغرام" in service_name:
            message_text = (
                "الرجاء إرسال رابط الخدمة الخاص بك\n"
                "🔴 تنبيه:\n"
                "يرجى إطفاء زر 'تميز للمراجعة' داخل حسابك الانستغرام قبل ارسال رابط الخدمه لضمان إكمال طلبك!"
            )
        elif "رفع سكور بث" in service_name:
            message_text = "يرجى ارسال رابط البث المباشر الخاص بك على تيكتوك.\n🔴 تنبيه: أرسل <b>رابط البث</b> وليس اليوزرنيم."
        elif "تيكتوك" in service_name:
            message_text = "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:\n🔴 ملاحظة: أرسل <b>الرابط</b> وليس اليوزرنيم!"
        else:
            message_text = "الرجاء إرسال الرابط الخاص بالخدمة المطلوبة:"
        context.user_data["selected_service"] = service_name
        context.user_data["service_price"] = price
        query.edit_message_text(message_text, parse_mode="HTML")
        return

    
    # قسم خدمات لودو
    if data == "show_ludo_services":
        query.edit_message_text("اختر خدمة لودو المطلوبة:", reply_markup=ludo_services_keyboard(user_id))
        return

    # اختيار خدمة لودو
    if data.startswith("ludo_service_"):
        service_name = data[len("ludo_service_"):]
        base_price = ludo_services.get(service_name, 0)
        base_price = get_base_price(service_name, base_price)
        price = get_effective_price(user_id, service_name, base_price, "ludo")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            buttons = [
                [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                [InlineKeyboardButton("رجوع", callback_data="show_followers")]
            ]
            if user_id == ADMIN_ID:
                buttons.insert(0, [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")])
            query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        context.user_data["selected_ludo_service"] = service_name
        context.user_data["ludo_service_price"] = price
        query.edit_message_text("أرسل آيدي لودو الخاص بك (أرقام فقط).", parse_mode="HTML")
        return
# اختيار خدمة ببجي
    if data.startswith("pubg_service_"):
        name = data[len("pubg_service_"):]
        base_price = pubg_services.get(name, 0)
        base_price = get_base_price(name, base_price)
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
                [InlineKeyboardButton("رجوع", callback_data="show_followers")]
            ]
            if user_id == ADMIN_ID:
                buttons.insert(0, [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")])
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
        base_price = get_base_price(service_name, base_price)
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
                [InlineKeyboardButton("رجوع", callback_data="show_followers")]
            ]
            if user_id == ADMIN_ID:
                buttons.insert(0, [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")])
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
        base_price = get_base_price(service_name, base_price)
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
                [InlineKeyboardButton("رجوع", callback_data="show_followers")]
            ]
            if user_id == ADMIN_ID:
                buttons.insert(0, [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")])
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
        [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")],
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

    # زر طلباتي (صفحة قابلة للتنقل)
    if data == "my_orders" or data.startswith("my_orders_"):
        offset = 0
        if data == "my_orders":
            offset = 0
        elif data.startswith("my_orders_page_"):
            try:
                offset = int(data.split("_")[-1])
            except:
                offset = 0
        context.user_data["my_orders_offset", "waiting_for_bulk_service_code", "__target_services__", "__groups__"] = offset
        total = db_count_user_orders(user_id)
        orders = db_get_user_orders(user_id, limit=10, offset=offset)
        if not orders:
            kb = [[InlineKeyboardButton("رجوع", callback_data="back_main")]]
            query.edit_message_text("لا توجد طلبات بعد.", reply_markup=InlineKeyboardMarkup(kb))
            return
        lines = []
        for (oid, cat, service, price, status, api_no, at, ct) in orders:
            when = at.strftime("%Y-%m-%d %H:%M")
            end = f" | تمّ: {ct.strftime('%Y-%m-%d %H:%M')}" if ct else ""
            api_part = f" | رقم API: {api_no}" if api_no else ""
            cat_ara = {"smm":"سوشيال", "pubg":"ببجي", "itunes":"آيتونز", "telegram":"تليجرام"}.get(cat, cat or "-")
            lines.append(f"#{oid} • {cat_ara} • {service} • {price}$ • {status} • {when}{end}{api_part}")
        # أزرار تنقل
        nav = []
        if offset > 0:
            prev_off = max(0, offset-10)
            nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"my_orders_page_{prev_off}"))
        if offset + 10 < total:
            next_off = offset + 10
            nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"my_orders_page_{next_off}"))
        buttons = [nav] if nav else []
        buttons.append([InlineKeyboardButton("رجوع", callback_data="back_main")])
        query.edit_message_text("سجل طلباتك:\n\n" + "\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))
        return

    # شحن عبر آسياسيل
    if data == "charge_asiacell":
        context.user_data["waiting_for_card"] = True
        query.edit_message_text("أرسل رقم الكارت المكون من 14 أو 16 رقم (يمكنك لصقه كما هو):")
        return

    # شحن عبر طرق أخرى
    if data in ("charge_superkey", "charge_zaincash", "charge_usdt", "charge_cent_points", "charge_helabi"):
        msg = f"لإتمام عملية الشحن تواصل مع الدعم الفني عبر الضغط هنا👈🏻 {SUPPORT_CONTACT}"
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="back_main")]]))
        return

    # ========== لوحة المالك ==========
    if data == "admin_menu":
        if user_id == ADMIN_ID:
            query.edit_message_text("لوحة تحكم المالك:", reply_markup=admin_menu_keyboard())
        else:
            query.edit_message_text("عذراً، أنت لست المالك.")
        return

    if user_id == ADMIN_ID:
        # ======= محرر أكواد الخدمات (API) =======
        if data == "admin_service_codes":
            pairs = build_service_groups()
            if not pairs:
                query.edit_message_text("لا توجد خدمات معرّفة حالياً.")
                return
            kb = []; names = []; display = ["🛠️ اختر مجموعة لتعديل كود الـAPI لها (أرسل رقمًا واحدًا فقط):\n"]
            for idx, (gname, services) in enumerate(pairs):
                names.append((gname, services))
                display.append(f"{idx+1}) {gname} — {len(services)} خدمة")
                kb.append([InlineKeyboardButton(f"تعديل: {gname}", callback_data=f"edit_group_{idx}")])
            kb.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            context.user_data["__groups__"] = names
            query.edit_message_text("\n".join(display), reply_markup=InlineKeyboardMarkup(kb))
            return

        if data.startswith("edit_group_"):
            try:
                idx = int(data.split("_")[-1])
            except Exception:
                query.answer("خطأ في الفهرس.", show_alert=True); return
            groups = context.user_data.get("__groups__") or build_service_groups()
            if idx < 0 or idx >= len(groups):
                query.answer("العنصر غير موجود.", show_alert=True); return
            gname, services = groups[idx]
            context.user_data["__target_services__"] = services
            context.user_data["waiting_for_bulk_service_code"] = True
            txt = (f"📝 تعديل كود الـAPI للمجموعة: {gname}\n"
                   f"عدد الخدمات: {len(services)}\n\n"
                   f"أرسل الآن <b>رقم كود الـAPI</b> فقط (مثال: <code>13912</code>)، وسيتم تعيينه لكل الخدمات في هذه المجموعة.")
            query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_service_codes")]]), parse_mode="HTML")
            return

        # ======= لوحة إحالات المالك =======
        if data == "admin_referrals":
            ov = db_get_admin_ref_overview()
            lines = ["📊 لوحة الإحالات (إدارة)\n",
                     f"إجمالي الإحالات: {ov.get('total_refs',0)}",
                     f"إجمالي العمولات المدفوعة: {ov.get('total_paid',0):.2f}$", "", "أفضل 10 مُحيلين:"]
            for row in ov.get("top", []):
                inviter_id_i, full_name_i, username_i, cnt_i, paid_cnt_i = row
                uname = f"@{username_i}" if username_i else "—"
                lines.append(f'- <a href="tg://user?id:{inviter_id_i}">{full_name_i}</a> | {uname} | ID:{inviter_id_i} — دعا {cnt_i} مستخدم (مدفوعة: {paid_cnt_i})')
            query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]), parse_mode="HTML")
            return
        # طلبات الخدمات المعلّقة (سوشيال/تلي)
        if data == "pending_smm_orders":
            pend = db_get_pending_orders(category_filter=["smm"])
            if not pend:
                query.edit_message_text("لا توجد طلبات خدمات معلّقة حالياً.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            else:
                text_msg = "الطلبات المعلّقة (الخدمات):\n\n"
                kb = []
                for (oid, uid, fn, un, cat, service, price, link, ts) in pend:
                    text_msg += (f"{oid}) {fn} (@{un})\n"
                                 f"   الخدمة: {service} | السعر: {price}$\n"
                                 f"   الرابط: {link}\n\n")
                    kb.append([
                        InlineKeyboardButton(f"✅ تنفيذ #{oid}", callback_data=f"approve_smm_id_{oid}"),
                        InlineKeyboardButton(f"❌ رفض #{oid}", callback_data=f"reject_smm_id_{oid}")
                    ])
                kb.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(kb))
            return

        if data.startswith("approve_smm_id_"):
            try:
                order_id = int(data.split("_")[-1])
            except Exception:
                query.answer("رقم طلب غير صالح.", show_alert=True)
                return
            approve_order_process_db(order_id, context, query)
            return

        if data.startswith("reject_smm_id_"):
            try:
                order_id = int(data.split("_")[-1])
            except Exception:
                query.answer("تعذر إيجاد الطلب.", show_alert=True)
                return
            row = _exec("""SELECT user_id, price FROM orders WHERE id=%s AND status='pending'""", (order_id,), "one")
            if not row:
                query.answer("الطلب غير موجود.", show_alert=True)
                return
            uid, amount = row
            db_refund_order(order_id, uid, float(amount))
            try:
                context.bot.send_message(chat_id=uid, text="تم إلغاء طلبك وإعادة المبلغ إلى رصيدك.")
            except Exception:
                pass
            query.edit_message_text("تم رفض الطلب وإرجاع الرصيد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_smm_orders")]]))
            return

        if data == "block_user":
            query.edit_message_text("أرسل اليوزرنيم أو الآيدي للمستخدم الذي تريد حضره:")
            context.user_data["waiting_for_block"] = True
            return

        if data == "unblock_user":
            bl = list_blocked_users()
            if not bl:
                query.edit_message_text("لا يوجد مستخدمين محظورين.")
            else:
                text = "قائمة المستخدمين المحظورين:\n"
                keyboard = []
                for (uid, until, rsn) in bl:
                    userrow = get_user_from_db(uid)
                    user_display = f"{userrow[1]} (@{userrow[2]})" if userrow else f"User {uid}"
                    text += f"{user_display} (ID: {uid}) — حتى: {until}\n"
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
            unblock_user(target_id)
            try:
                context.bot.send_message(chat_id=target_id, text="✅ تم إلغاء حظرك. يمكنك استخدام البوت الآن.")
            except Exception:
                pass
            query.edit_message_text("تم إلغاء حظر المستخدم بنجاح.")
            return

        if data == "admin_add_balance":
            query.edit_message_text("أرسل الآن آيدي المستخدم الذي تريد إضافة الرصيد له:")
            context.user_data["waiting_for_add_balance_user_id"] = True
            return
        if data == "admin_discount":
            query.edit_message_text("أرسل الآن آيدي المستخدم (رقم) أو اليوزر @username لبدء خصم الرصيد:")
            context.user_data["waiting_for_discount_user_id"] = True
            return

        if data == "admin_discounts_info":
            try:
                query.edit_message_text(
                    get_mod_discount_help_text(),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]])
                )
            except Exception:
                context.bot.send_message(chat_id=update.effective_chat.id, text=get_mod_discount_help_text(), parse_mode="HTML")
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
            rows = db_get_completed_api_orders()
            if not rows:
                query.edit_message_text("لا توجد طلبات تم تنفيذها عبر API.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
                return
            keyboard = []
            text_msg = "الطلبات المكتملة عبر API:\n\n"
            for (oid, uid, fn, un, service, price, api_no) in rows:
                text_msg += f"- #{oid} | {fn} | {service} | {price}$ | رقم الطلب: {api_no}\n"
                keyboard.append([
                    InlineKeyboardButton("اشعار المستخدم", callback_data=f"notify_order_{oid}"),
                    InlineKeyboardButton("ارجاع الرصيد", callback_data=f"refund_order_{oid}"),
                    InlineKeyboardButton("🗑️ حذف الطلب", callback_data=f"delete_order_{oid}")
                ])
            keyboard.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith("notify_order_"):
            try:
                oid = int(data.split("_")[-1])
            except:
                query.answer("خطأ في رقم الطلب", show_alert=True); return
            row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
            if not row:
                query.answer("طلب غير موجود", show_alert=True); return
            try:
                context.bot.send_message(chat_id=row[0], text="تم تنفيذ طلبك بنجاح")
            except Exception as e:
                logger.error("notify err: %s", e)
            query.answer("تم إرسال إشعار للمستخدم", show_alert=True)
            return

        if data.startswith("refund_order_"):
            try:
                oid = int(data.split("_")[-1])
            except:
                query.edit_message_text("طلب غير موجود."); return
            row = _exec("SELECT user_id, price, status, refunded FROM orders WHERE id=%s", (oid,), "one")
            if not row:
                query.edit_message_text("طلب غير موجود."); return
            uid, amount, status, refunded = row
            if refunded:
                query.answer("تم ارجاع الرصيد مسبقاً.", show_alert=True); return
            db_refund_order(oid, uid, float(amount))
            try:
                context.bot.send_message(chat_id=uid, text=f"تم استعادة رصيدك المخصوم ({amount}$)")
            except Exception:
                pass
            query.edit_message_text("تمت العملية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            return

        if data.startswith("delete_order_"):
            try:
                oid = int(data.split("_")[-1])
            except:
                query.answer("تعذر حذف هذا الطلب.", show_alert=True); return
            db_delete_order(oid)
            query.data = "review_orders"
            button_handler(update, context)
            return

        # إدارة كروت الشحن
        if data == "pending_cards":
            rows = db_get_pending_cards()
            if not rows:
                query.edit_message_text("لا توجد كروت معلقة حالياً.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            else:
                text_msg = "الكروت المعلقة:\n"
                buttons = []
                for (cid, uid, fn, un, card_number, submitted_at) in rows:
                    text_msg += f"#{cid}) @{un} - كارت معلق\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الكارت #{cid}", callback_data=f"process_card_{cid}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return

        if data.startswith("process_card_"):
            cid = int(data.split("_")[-1])
            card = db_get_card(cid)
            if not card:
                query.edit_message_text("الكارت غير موجود."); return
            _, uid, fn, un, number, ts, status, amount = card
            text_msg = (
                f"تفاصيل الكارت #{cid}:\n"
                f"- المعرف: {uid}\n- الاسم: {fn}\n- يوزر: @{un}\n"
                f"- رقم الكارت: اضغط زر (إظهار الرقم) أدناه.\n\nاختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("إظهار الرقم", callback_data=f"show_card_{cid}")],
                [InlineKeyboardButton("قبول الكارت", callback_data=f"approve_card_{cid}"),
                 InlineKeyboardButton("رفض الكارت", callback_data=f"reject_card_{cid}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_cards")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        if data.startswith("show_card_"):
            cid = int(data.split("_")[-1])
            card = db_get_card(cid)
            if not card:
                query.message.reply_text("الكارت غير موجود."); return
            number = card[4]
            query.message.reply_text(text=f"رقم الكارت:\n`{number}`\n(اضغط مطولاً للنسخ)", parse_mode="Markdown")
            return

        if data.startswith("approve_card_"):
            cid = int(data.split("_")[-1])
            # اطلب المبلغ
            query.edit_message_text("أرسل الآن المبلغ المراد شحنه للمستخدم (بالدولار):",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]))
            context.user_data["card_to_approve_id"] = cid
            context.user_data["waiting_for_amount"] = True
            return

        if data.startswith("reject_card_"):
            cid = int(data.split("_")[-1])
            card = db_get_card(cid)
            if card:
                db_reject_card(cid)
                try:
                    context.bot.send_message(chat_id=card[1], text="تم رفض الشحن لأن رقم الكارت غير صحيح.")
                except Exception:
                    pass
            query.edit_message_text("تم رفض الكارت بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_cards")]]))
            return

        # طلبات ببجي
        if data == "pending_pubg_orders":
            pend = _exec("""SELECT id, user_id, full_name, username, service, price,
                                   COALESCE(payload->>'pubg_id','') AS pubg_id
                            FROM orders
                            WHERE status='pending' AND category='pubg'
                            ORDER BY ordered_at ASC""", fetch="all") or []
            if not pend:
                query.edit_message_text("لا توجد طلبات شدات ببجي معلقة حالياً.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            else:
                text_msg = "طلبات شدات ببجي المعلقة:\n"
                buttons = []
                for (oid, uid, fn, un, service, price, pubg_id) in pend:
                    text_msg += f"#{oid}) @{un} - الخدمة: {service}, الآيدي: {pubg_id}\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الطلب #{oid}", callback_data=f"process_pubg_order_{oid}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return

        if data.startswith("process_pubg_order_"):
            oid = int(data.split("_")[-1])
            row = _exec("""SELECT id, user_id, full_name, username, service, price, payload
                           FROM orders WHERE id=%s""", (oid,), "one")
            if not row:
                query.edit_message_text("الطلب غير موجود."); return
            _, uid, fn, un, service, price, payload = row
            pubg_id = (payload or {}).get("pubg_id") if isinstance(payload, dict) else None
            text_msg = (
                f"تفاصيل طلب شحن شدات ببجي #{oid}:\n"
                f"- المعرف: {uid}\n- الاسم: {fn}\n- يوزر: @{un}\n"
                f"- الخدمة: {service}\n- السعر: {price}$\n- الآيدي: {pubg_id}\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("تم شحن الشدات", callback_data=f"approve_pubg_order_{oid}"),
                 InlineKeyboardButton("تم الغاء شحن الشدات", callback_data=f"reject_pubg_order_{oid}")],
                [InlineKeyboardButton("انتظار المستخدم", callback_data=f"user_wait_pubg_order_{oid}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        if data.startswith("approve_pubg_order_"):
            oid = int(data.split("_")[-1])
            _exec("UPDATE orders SET status='completed', completed_at=NOW() WHERE id=%s", (oid,))
            row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
            if row:
                try: context.bot.send_message(chat_id=row[0], text="تم شحن شدات ببجي بنجاح.")
                except Exception: pass
            query.edit_message_text("تم شحن شدات ببجي وإشعار المستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]))
            return

        if data.startswith("reject_pubg_order_"):
            oid = int(data.split("_")[-1])
            row = _exec("SELECT user_id, price FROM orders WHERE id=%s", (oid,), "one")
            if row:
                db_refund_order(oid, row[0], float(row[1]))
                try: context.bot.send_message(chat_id=row[0], text="تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ إلى حسابك.")
                except Exception: pass
            query.edit_message_text("تم إلغاء طلب شحن شدات ببجي وإعادة المبلغ للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]))
            return

        if data.startswith("user_wait_pubg_order_"):
            oid = int(data.split("_")[-1])
            row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
            if row:
                try: context.bot.send_message(chat_id=row[0], text="سوف يتم تنفيذ طلبك قريبا")
                except Exception: pass
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_pubg_orders")]]))
            return

        if data == "api_check_balance":
            api_check_balance(update, context); return

        if data == "api_order_status":
            query.edit_message_text("أدخل رقم الطلب للتحقق من حالته عبر API:")
            context.user_data["waiting_for_api_order_status"] = True
            return

        # طلبات لودو
        if data == "pending_ludo_orders":
            pend = _exec("""SELECT id, user_id, full_name, username, service, price,
                                   COALESCE(payload->>'ludo_id','') AS ludo_id
                            FROM orders
                            WHERE status='pending' AND category='ludo'
                            ORDER BY ordered_at ASC""", fetch="all") or []
            if not pend:
                query.edit_message_text("لا توجد طلبات لودو معلقة حالياً.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            else:
                text_msg = "طلبات لودو المعلقة:\n"
                buttons = []
                for (oid, uid, fn, un, service, price, ludo_id) in pend:
                    user_line = f"{fn} (@{un})" if un else f"{fn}"
                    text_msg += f"#{oid}) {user_line} - الخدمة: {service}, الآيدي: {ludo_id}\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الطلب #{oid}", callback_data=f"process_ludo_order_{oid}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return

        if data.startswith("process_ludo_order_"):
            oid = int(data.split("_")[-1])
            row = _exec("""SELECT id, user_id, full_name, username, service, price, payload
                           FROM orders WHERE id=%s""", (oid,), "one")
            if not row:
                query.edit_message_text("الطلب غير موجود."); return
            _, uid, fn, un, service, price, payload = row
            ludo_id = (payload or {}).get("ludo_id") if isinstance(payload, dict) else None
            text_msg = (
                f"تفاصيل طلب لودو #{oid}:\n"
                f"- المعرف: {uid}\n- الاسم: {fn}\n- يوزر: @{un}\n"
                f"- الخدمة: {service}\n- السعر: {price}$\n- آيدي لودو: {ludo_id}\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("تم تنفيذ لودو", callback_data=f"approve_ludo_order_{oid}")],
                [InlineKeyboardButton("رفض الطلب", callback_data=f"reject_ludo_order_{oid}")],
                [InlineKeyboardButton("انتظار المستخدم", callback_data=f"user_wait_ludo_order_{oid}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_ludo_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        if data.startswith("approve_ludo_order_"):
            oid = int(data.split("_")[-1])
            _exec("UPDATE orders SET status='completed', completed_at=NOW() WHERE id=%s", (oid,))
            row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
            if row:
                try: context.bot.send_message(chat_id=row[0], text="تم تنفيذ طلب لودو بنجاح.")
                except Exception: pass
            query.edit_message_text("تم تنفيذ طلب لودو وإشعار المستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_ludo_orders")]]))
            return

        if data.startswith("reject_ludo_order_"):
            oid = int(data.split("_")[-1])
            row = _exec("SELECT user_id, price FROM orders WHERE id=%s", (oid,), "one")
            if row:
                db_refund_order(oid, row[0], float(row[1]))
                try: context.bot.send_message(chat_id=row[0], text="تم إلغاء طلب لودو وإعادة المبلغ إلى حسابك.")
                except Exception: pass
            query.edit_message_text("تم إلغاء طلب لودو وإعادة المبلغ للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_ludo_orders")]]))
            return

        if data.startswith("user_wait_ludo_order_"):
            oid = int(data.split("_")[-1])
            row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
            if row:
                try: context.bot.send_message(chat_id=row[0], text="سوف يتم تنفيذ طلبك لودو قريبًا.")
                except Exception: pass
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_ludo_orders")]]))
            return
    
        # طلبات ايتونز
        if data == "pending_itunes_orders":
            pend = _exec("""SELECT id, user_id, full_name, username, service, price
                            FROM orders WHERE status='pending' AND category='itunes'
                            ORDER BY ordered_at ASC""", fetch="all") or []
            if not pend:
                query.edit_message_text("لا توجد طلبات شحن ايتونز معلقة حالياً.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
            else:
                text_msg = "طلبات شحن الايتونز المعلقة:\n"
                buttons = []
                for (oid, uid, fn, un, service, price) in pend:
                    text_msg += f"#{oid}) @{un} - {service} بسعر {price}$\n"
                    buttons.append([InlineKeyboardButton(f"معالجة الطلب #{oid}", callback_data=f"process_itunes_{oid}")])
                buttons.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
                query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
            return

        if data.startswith("process_itunes_"):
            oid = int(data.split("_")[-1])
            row = _exec("""SELECT id, user_id, full_name, username, service, price
                           FROM orders WHERE id=%s""", (oid,), "one")
            if not row:
                query.edit_message_text("طلب غير موجود."); return
            _, uid, fn, un, service, price = row
            text_msg = (
                f"تفاصيل طلب شحن ايتونز #{oid}:\n"
                f"- المعرف: {uid}\n- الاسم: {fn}\n- يوزر: @{un}\n"
                f"- الخدمة: {service}\n- السعر: {price}$\n\n"
                "اختر الإجراء:"
            )
            btns = [
                [InlineKeyboardButton("انتظار المستخدم", callback_data=f"itunes_wait_{oid}")],
                [InlineKeyboardButton("اكمال الطلب", callback_data=f"itunes_complete_{oid}")],
                [InlineKeyboardButton("الغاء الطلب", callback_data=f"itunes_cancel_{oid}")],
                [InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]
            ]
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
            return

        if data.startswith("itunes_wait_"):
            oid = int(data.split("_")[-1])
            row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
            if row:
                try: context.bot.send_message(chat_id=row[0], text="سوف يتم ارسال كود الهدايا قريبا")
                except Exception: pass
            query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]))
            return

        if data.startswith("itunes_complete_"):
            oid = int(data.split("_")[-1])
            query.edit_message_text("أرسل الآن كود الهدايا الايتونز:",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]))
            context.user_data["itunes_to_complete_id"] = oid
            context.user_data["waiting_for_itunes_code"] = True
            return

        if data.startswith("itunes_cancel_"):
            oid = int(data.split("_")[-1])
            row = _exec("SELECT user_id, price FROM orders WHERE id=%s", (oid,), "one")
            if row:
                db_refund_order(oid, row[0], float(row[1]))
                try: context.bot.send_message(chat_id=row[0], text="تم إلغاء طلب شحن الايتونز وإعادة المبلغ لرصيدك.")
                except Exception: pass
            query.edit_message_text("تم إلغاء طلب شحن الايتونز وإعادة المبلغ للمستخدم.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_itunes_orders")]]))
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
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط."); return
        pend_counts = _exec("""SELECT
                                (SELECT COUNT(*) FROM orders WHERE status='pending' AND category='smm') AS smm,
                                (SELECT COUNT(*) FROM orders WHERE status='pending' AND category='pubg') AS pubg,
                                (SELECT COUNT(*) FROM cards  WHERE status='pending') AS cards,
                                (SELECT COUNT(*) FROM orders WHERE status='pending' AND category='itunes') AS itunes
                               """, fetch="one")
        smm, pubg_cnt, cards_cnt, itunes_cnt = pend_counts
        total = (smm or 0)+(pubg_cnt or 0)+(cards_cnt or 0)+(itunes_cnt or 0)
        txt = ( "📮 الطلبات المعلقة:\n"
                f"- إجمالي المعلّقة: {total}\n"
                f"- العادية: {smm}\n"
                f"- شدات ببجي: {pubg_cnt}\n"
                f"- كروت الشحن: {cards_cnt}\n"
                f"- الايتونز: {itunes_cnt}\n\n"
                "يمكنك إشعار المالك الآن لمراجعتها." )
        kb = [[InlineKeyboardButton("🔔 إشعار المالك بالمراجعة", callback_data="mod_ping_owner")],
              [InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]
        query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "mod_ping_owner":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط."); return
        cnt = _exec("SELECT COUNT(*) FROM orders WHERE status='pending'", fetch="one")[0]
        try:
            context.bot.send_message(chat_id=ADMIN_ID,
                text=("🔔 إشعار من أحد المشرفين لمراجعة الطلبات المعلقة.\n"
                      f"المشرف: {update.effective_user.full_name} (@{update.effective_user.username or 'NoUsername'})\n"
                      f"إجمالي المعلّقة الآن: {cnt}"))
            query.edit_message_text("تم إشعار المالك. شكراً لك.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]))
        except Exception as e:
            logger.error("mod_ping_owner error: %s", e)
            query.edit_message_text("تعذر إشعار المالك حالياً.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]))
        return

    if data == "mod_stats":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط."); return
        completed = _exec("SELECT COUNT(*) FROM orders WHERE status='completed'", fetch="one")[0]
        ongoing = _exec("SELECT COUNT(*) FROM orders WHERE status='completed' AND refunded=FALSE", fetch="one")[0]
        pending_total = _exec("SELECT COUNT(*) FROM orders WHERE status='pending'", fetch="one")[0]
        canceled_est = _exec("SELECT COUNT(*) FROM orders WHERE refunded=TRUE", fetch="one")[0]
        txt = ( "📊 إحصائيات الطلبات:\n"
                f"- مكتملة: {completed}\n"
                f"- جارية: {ongoing}\n"
                f"- معلّقة: {pending_total}\n"
                f"- ملغاة/مسترجعة: {canceled_est}" )
        query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moderator_menu")]]))
        return

    if data == "mod_discounts_info":
        if not is_moderator(user_id):
            query.edit_message_text("هذه الميزة مخصصة للمشرفين فقط."); return
        try:
            query.edit_message_text(
                get_mod_discount_help_text(),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moderator_menu")]])
            )
        except Exception:
            context.bot.send_message(chat_id=update.effective_chat.id, text=get_mod_discount_help_text(), parse_mode="HTML")
        return

# =========================
# استقبال الرسائل (Message)
# =========================
def handle_messages(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    ban_msg = _is_user_blocked_now(user_id)
    if ban_msg:
        update.message.reply_text(ban_msg); return

    # إدخال المالك لكود مجموعة الخدمات
    try:
        if _admin_text_gate(update, context):
            return
    except Exception as _e:
        logger.error("admin_text_gate error: %s", _e)

    full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    text = update.message.text or ""

    # تأكيد طلب رصيد الهاتف من المستخدم
    if context.user_data.get("waiting_for_mobile_confirm"):
        if text.strip() == "1":
            service_name = context.user_data.get("selected_mobile_service")
            price = float(context.user_data.get("mobile_service_price", 0))
            bal = users_balance.get(user_id, 0.0)
            if bal < price:
                update.message.reply_text("رصيدك غير كافٍ حالياً. قم بالشحن أولاً.")
                clear_all_waiting_flags(context); return
            users_balance[user_id] = round(bal - price, 2)
            sync_balance_to_db(user_id)
            add_user_spent(user_id, price)
            order_id = db_add_order(user_id, full_name, username, "mobile", service_name, price, None, {})
            try:
                context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(f"🆕 طلب رصيد هاتف:\n"
                          f"- المستخدم: {full_name} (@{username}) | ID: {user_id}\n"
                          f"- الخدمة: {service_name} | السعر: {price}$\n- رقم الطلب: #{order_id}"),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("طلبات الارصدة المعلقة", callback_data="pending_mobile_orders")]])
                )
            except Exception:
                pass
            update.message.reply_text("✅ تم استلام طلبك. سيتم إرسال رقم الكارت لك قريباً.", reply_markup=main_menu_keyboard(user_id))
        else:
            update.message.reply_text("تم إلغاء العملية.")
        clear_all_waiting_flags(context); return

    # المالك يرسل رقم الكارت لإكمال الطلب
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_mobile_code"):
        oid = context.user_data.get("mobile_to_complete_id")
        code = text.strip()
        row = _exec("SELECT user_id FROM orders WHERE id=%s AND category='mobile'", (oid,), "one")
        if row:
            try:
                context.bot.send_message(chat_id=row[0], text=f"🎁 رقم الكارت الخاص بك:\n{code}")
            except Exception as e:
                logger.error("Failed to send mobile code: %s", e)
            _exec("UPDATE orders SET status='completed', completed_at=NOW(), payload = COALESCE(payload,'{}'::jsonb) || %s::jsonb WHERE id=%s",
                  (psycopg.types.json.Json({"card_number": code}), oid))
            update.message.reply_text("تم إرسال رقم الكارت للمستخدم.")
        else:
            update.message.reply_text("طلب غير صالح.")
        clear_all_waiting_flags(context); return

    # --- أوضاع المالك ---
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_add_balance_user_id"):
        target_input = text.strip()
        try:
            target_id = int(target_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == (_normalize_username(target_input) or "").lower():
                    found_user = usr; break
            if not found_user:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات."); return
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
            update.message.reply_text("الرجاء إرسال مبلغ صالح."); return
        target_id = context.user_data.get("admin_target_id")
        _exec("UPDATE users SET balance = COALESCE(balance,0) + %s WHERE user_id=%s", (amount, target_id))
        sync_balance_from_db(target_id)
        update.message.reply_text(f"تم إضافة {amount}$ لآيدي {target_id}.")
        try:
            cur = _exec("SELECT COALESCE(balance,0) FROM users WHERE user_id=%s", (target_id,), "one")[0]
        except Exception:
            cur = None
        try:
            context.bot.send_message(chat_id=target_id, text=f"تم شحن رصيدك بمبلغ {amount}$ من قِبل المالك. رصيدك الحالي: {cur if cur is not None else '-'}$")
        except Exception:
            pass
        try:
            context.bot.send_message(chat_id=ADMIN_ID, text=f"✅ تمت إضافة {amount}$ لآيدي {target_id}. الرصيد الحالي: {cur if cur is not None else '-'}$")
        except Exception:
            pass

        # إحالة: أول شحن
        try:
            inviter_id = db_mark_first_funding_and_pay(target_id)
            if inviter_id:
                try: context.bot.send_message(chat_id=inviter_id, text=f"🎉 مبروك! حصلت على عمولة إحالة {REFERRAL_COMMISSION_USD}$ لأن صديقك قام بأول شحن.")
                except Exception: pass
                try: context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 دُفعت عمولة إحالة {REFERRAL_COMMISSION_USD}$ للمُحيل {inviter_id} بعد أول شحن للمحال {target_id}.")
                except Exception: pass
        except Exception as _e:
            logger.error("referral payout on admin add failed: %s", _e)
        clear_all_waiting_flags(context); return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_discount_user_id"):
        target_input = text.strip()
        try:
            target_id = int(target_input)
        except ValueError:
            found_user = None
            for usr in get_all_users():
                if usr[2] and usr[2].lower() == (_normalize_username(target_input) or "").lower():
                    found_user = usr; break
            if not found_user:
                update.message.reply_text("المستخدم غير موجود في قاعدة البيانات."); return
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
            update.message.reply_text("الرجاء إرسال مبلغ صالح."); return
        target_id = context.user_data.get("admin_target_id")
        curbal = _exec("SELECT COALESCE(balance,0) FROM users WHERE user_id=%s", (target_id,), "one")[0]
        if curbal < amount:
            update.message.reply_text("رصيد المستخدم أقل من مبلغ الخصم."); return
        _exec("UPDATE users SET balance=%s WHERE user_id=%s", (round(curbal - amount,2), target_id))
        sync_balance_from_db(target_id)
        update.message.reply_text(f"تم خصم {amount}$ من آيدي {target_id}. الرصيد الحالي: {round(curbal-amount,2)}$")
        try:
            cur = _exec("SELECT COALESCE(balance,0) FROM users WHERE user_id=%s", (target_id,), "one")[0]
        except Exception:
            cur = None
        try:
            context.bot.send_message(chat_id=target_id, text=f"تم خصم {amount}$ من رصيدك من قِبل المالك. رصيدك الحالي: {cur if cur is not None else '-'}$")
        except Exception:
            pass
        try:
            context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ تم خصم {amount}$ من آيدي {target_id}. الرصيد الحالي: {cur if cur is not None else '-'}$")
        except Exception:
            pass

        clear_all_waiting_flags(context); return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_block"):
        ident = text.strip()
        if ident.isdigit():
            _ban_user_for_hours(int(ident), CARD_BAN_HOURS, "حظر يدوي من المالك.")
            update.message.reply_text("تم حضر المستخدم.")
        else:
            uname = _normalize_username(ident)
            target = None
            for usr in get_all_users():
                if usr[2] and (_normalize_username(usr[2]) or "").lower() == (uname or "").lower():
                    target = usr[0]; break
            if target:
                _ban_user_for_hours(target, CARD_BAN_HOURS, "حظر يدوي من المالك.")
                update.message.reply_text("تم حضر المستخدم.")
            else:
                update.message.reply_text("لم يتم العثور على المستخدم.")
        clear_all_waiting_flags(context); return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_broadcast"):
        broadcast_ad(update, context)
        clear_all_waiting_flags(context); return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_api_order_status"):
        order_id = text.strip()
        params = {'key': API_KEY, 'action': 'status', 'order': order_id}
        try:
            response = requests.post(API_URL, data=params, timeout=20)
            js = response.json()
            update.message.reply_text(f"حالة الطلب {order_id}:\n{js}")
        except Exception:
            update.message.reply_text("فشل جلب الحالة من API.")
        clear_all_waiting_flags(context); return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_new_mod"):
        context.user_data["waiting_for_new_mod"] = False
        target_id = None; target_username = None; full_name_db = "Unknown"
        if text.isdigit():
            target_id = int(text)
            row = get_user_from_db(target_id)
            if row:
                full_name_db = row[1]; target_username = row[2] or "NoUsername"
        else:
            target_username = _normalize_username(text)
            row_match = None
            for usr in get_all_users():
                if usr[2] and (_normalize_username(usr[2]) or "").lower() == (target_username or "").lower():
                    row_match = usr; break
            if row_match:
                target_id = row_match[0]; full_name_db = row_match[1]
            else:
                update.message.reply_text("تعذر إيجاد المستخدم بهذا اليوزر. أرسل الآيدي الرقمي.")
                return
        add_moderator(target_id, full_name_db, target_username or "NoUsername")
        try: context.bot.send_message(chat_id=target_id, text="✅ تم ترقيتك إلى مشرف. أرسل /start لتظهر لك لوحة تحكم المشرف.")
        except Exception as e: logger.warning("Could not DM new moderator: %s", e)
        update.message.reply_text(f"تمت إضافة المشرف: {full_name_db} (@{target_username}) - ID: {target_id}")
        return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_remove_mod"):
        context.user_data["waiting_for_remove_mod"] = False
        ok = remove_moderator_by_identifier(text)
        update.message.reply_text("تم حذف المشرف بنجاح." if ok else "لم يتم العثور على المشرف المحدد.")
        return

    # ======== شحن آسياسيل (المستخدم) + حماية ========
    if context.user_data.get("waiting_for_card"):
        raw = text.strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) not in (14, 16):
            update.message.reply_text("❌ رقم الكارت غير صحيح. الرجاء إرسال رقم مكوّن من 14 أو 16 رقم.")
            return
        violation_reason = _record_and_check_card(user_id, digits)
        if violation_reason:
            _ban_user_for_hours(user_id, CARD_BAN_HOURS, violation_reason)
            update.message.reply_text(f"🚫 تم حظرك مؤقتًا لمدة {CARD_BAN_HOURS} ساعة.\nالسبب: {violation_reason}")
            clear_all_waiting_flags(context); return
        # خزّن الكارت
        db_add_card(user_id, full_name, username, digits)
        # إشعار المالك
        card_number_display = f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:]}" if len(digits)==16 else digits
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=("💳 تم استلام كارت آسياسيل جديد للمراجعة:\n"
                      f"- المستخدم: {full_name} (@{username})\n"
                      f"- ID: {user_id}\n"
                      f"- الكارت: {card_number_display}\n\n"
                      "اضغط الزر أدناه لعرض جميع الكروت المعلقة."),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الكارتات المعلقة", callback_data="pending_cards")]])
            )
        except Exception as e:
            logger.error("Failed to notify owner about new card: %s", e)
        update.message.reply_text("✅ تم إرسال رقم الكارت للمراجعة.\nسيقوم المالك بالتحقق والشحن إن أمكن.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context); return

    # ======== إدخال مبلغ الشحن عند موافقة المالك ========
    if user_id == ADMIN_ID and context.user_data.get("waiting_for_amount"):
        try:
            amount = float(text.strip())
        except ValueError:
            update.message.reply_text("الرجاء إرسال مبلغ صالح."); return
        cid = context.user_data.get("card_to_approve_id")
        card = db_get_card(cid) if cid else None
        if not card:
            update.message.reply_text("تعذر العثور على الكارت المحدد."); clear_all_waiting_flags(context); return
        target_id = card[1]
        _exec("UPDATE users SET balance = COALESCE(balance,0) + %s WHERE user_id=%s", (amount, target_id))
        sync_balance_from_db(target_id)
        db_approve_card(cid, amount)
        try:
            context.bot.send_message(chat_id=target_id, text=f"🎉 تم شحن رصيدك بقيمة {amount}$.")
        except Exception as e:
            logger.error("Failed to notify user about topup: %s", e)
        # إحالة: أول شحن عبر آسياسيل
        try:
            inviter_id = db_mark_first_funding_and_pay(target_id)
            if inviter_id:
                try: context.bot.send_message(chat_id=inviter_id, text=f"🎉 مبروك! حصلت على عمولة إحالة {REFERRAL_COMMISSION_USD}$ لأن صديقك شحن لأول مرة عبر آسياسيل.")
                except Exception: pass
                try: context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 دُفعت عمولة إحالة {REFERRAL_COMMISSION_USD}$ للمُحيل {inviter_id} بعد أول شحن (آسياسيل) للمحال {target_id}.")
                except Exception: pass
        except Exception as _e:
            logger.error("referral payout on Asiacell failed: %s", _e)
        update.message.reply_text(f"تم شحن رصيد المستخدم {card[2]} (@{card[3]}) بمبلغ {amount}$.")
        clear_all_waiting_flags(context); return

    # --- طلبات الخدمات (خصم رصيد + تسجيل صرف) ---
    if context.user_data.get("selected_service"):
        service_name = context.user_data.get("selected_service")
        price = float(context.user_data.get("service_price", 0))
        link = text.strip()
        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك لم يعد كافياً. حاول الشحن أولاً.")
            clear_all_waiting_flags(context); return
        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)
        add_user_spent(user_id, price)
        # خزّن الطلب
        order_id = db_add_order(user_id, full_name, username, "smm", service_name, price, link, None)
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(f"🆕 طلب خدمة جديد بانتظار المراجعة:\n"
                      f"- المستخدم: {full_name} (@{username}) | ID: {user_id}\n"
                      f"- الخدمة: {service_name} | السعر: {price}$\n"
                      f"- الرابط: {link}\n- رقم الطلب: #{order_id}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الطلبات المعلّقة (الخدمات)", callback_data="pending_smm_orders")]])
            )
        except Exception:
            pass
        update.message.reply_text("✅ تم استلام طلبك ووضعه في قائمة المراجعة.\nسيتم التنفيذ قريباً.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context); return

    if context.user_data.get("selected_pubg_service"):
        service_name = context.user_data.get("selected_pubg_service")
        price = float(context.user_data.get("pubg_service_price", 0))
        pubg_id = text.strip()
        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك لم يعد كافياً. حاول الشحن أولاً.")
            clear_all_waiting_flags(context); return
        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)
        add_user_spent(user_id, price)
        order_id = db_add_order(user_id, full_name, username, "pubg", service_name, price, None, {"pubg_id": pubg_id})
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(f"🆕 طلب شدّات ببجي:\n" f"- المستخدم: {full_name} (@{username}) | ID: {user_id}\n" f"- الخدمة: {service_name} | السعر: {price}$\n" f"- آيدي ببجي: {pubg_id}\n- رقم الطلب: #{order_id}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("طلبات شدات ببجي", callback_data="pending_pubg_orders")]])
            )
        except Exception:
            pass

        update.message.reply_text("✅ تم استلام طلب شحن شدات ببجي. سنقوم بالتنفيذ قريباً.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context); return

    if context.user_data.get("waiting_for_itunes_confirm"):
        if text.strip() == "1":
            service_name = context.user_data.get("selected_itunes_service")
            price = float(context.user_data.get("itunes_service_price", 0))
            bal = users_balance.get(user_id, 0.0)
            if bal < price:
                update.message.reply_text("رصيدك غير كافٍ حالياً. قم بالشحن أولاً.")
                clear_all_waiting_flags(context); return
            users_balance[user_id] = round(bal - price, 2)
            sync_balance_to_db(user_id)
            add_user_spent(user_id, price)
            order_id = db_add_order(user_id, full_name, username, "itunes", service_name, price, None, {})
            try:
                context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(f"🆕 طلب شحن آيتونز:\n" f"- المستخدم: {full_name} (@{username}) | ID: {user_id}\n" f"- الخدمة: {service_name} | السعر: {price}$\n- رقم الطلب: #{order_id}"),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("طلبات شحن الايتونز", callback_data="pending_itunes_orders")]])
                )
            except Exception:
                pass

            update.message.reply_text("✅ تم استلام طلب ايتونز. سيتم إرسال الكود لك قريباً.", reply_markup=main_menu_keyboard(user_id))
        else:
            update.message.reply_text("تم إلغاء العملية.")
        clear_all_waiting_flags(context); return

    if user_id == ADMIN_ID and context.user_data.get("waiting_for_itunes_code"):
        oid = context.user_data.get("itunes_to_complete_id")
        code = text.strip()
        row = _exec("SELECT user_id FROM orders WHERE id=%s AND category='itunes'", (oid,), "one")
        if row:
            try:
                context.bot.send_message(chat_id=row[0], text=f"🎁 كود ايتونز الخاص بك:\n{code}")
            except Exception as e:
                logger.error("Failed to send iTunes code: %s", e)
            _exec("UPDATE orders SET status='completed', completed_at=NOW(), payload = COALESCE(payload,'{}'::jsonb) || %s::jsonb WHERE id=%s",
                  (psycopg.types.json.Json({"code": code}), oid))
            update.message.reply_text("تم إرسال الكود للمستخدم.")
        else:
            update.message.reply_text("طلب غير صالح.")
        clear_all_waiting_flags(context); return


    # استقبال آيدي لودو بعد اختيار الخدمة
    if context.user_data.get("selected_ludo_service"):
        service_name = context.user_data.get("selected_ludo_service")
        price = float(context.user_data.get("ludo_service_price", 0))
        ludo_id = text.strip()
        if not ludo_id.isdigit():
            update.message.reply_text("أرسل آيدي لودو أرقام فقط، بدون مسافات.")
            return
        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك غير كافٍ حالياً.")
            clear_all_waiting_flags(context); return
        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)
        add_user_spent(user_id, price)
        db_add_order(user_id, full_name, username, "ludo", service_name, price, None, {"ludo_id": ludo_id})
        try:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(f"🆕 طلب لودو:\n- المستخدم: {full_name} (@{username}) | ID: {user_id}\n"
                      f"- الخدمة: {service_name} | السعر: {price}$\n- آيدي لودو: {ludo_id}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("طلبات لودو المعلّقة", callback_data="pending_ludo_orders")]])
            )
        except Exception:
            pass
        update.message.reply_text("✅ تم استلام طلب لودو. سنباشر التنفيذ قريباً.", reply_markup=main_menu_keyboard(user_id))
        clear_all_waiting_flags(context); return
    if context.user_data.get("waiting_for_telegram_link"):
        service_name = context.user_data.get("selected_telegram_service")
        price = float(context.user_data.get("telegram_service_price", 0))
        invite_link = text.strip()
        if "t.me/" not in invite_link:
            update.message.reply_text("الرجاء إرسال رابط دعوة صحيح مثل: https://t.me/+xxxxx"); return
        bal = users_balance.get(user_id, 0.0)
        if bal < price:
            update.message.reply_text("رصيدك غير كافٍ حالياً.")
            clear_all_waiting_flags(context); return
        users_balance[user_id] = round(bal - price, 2)
        sync_balance_to_db(user_id)
        add_user_spent(user_id, price)
        db_add_order(user_id, full_name, username, "smm", service_name, price, invite_link, {"type":"telegram"})
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
        clear_all_waiting_flags(context); return

    update.message.reply_text("اختر من القائمة:", reply_markup=main_menu_keyboard(user_id))

# =========================
# أوامر بسيطة
# =========================
def help_cmd(update: Update, context: CallbackContext):
    update.message.reply_text("أرسل /start لفتح القوائم.")

# =========================
# تشغيل البوت
# =========================

# ===== Handlers قسم شراء رصيد الهاتف (مستقل) =====
def mobile_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # فتح قسم شراء رصيد الهاتف
    if data == "show_mobile_recharge":
        try:
            query.edit_message_text("اختر خدمة رصيد الهاتف المطلوبة:", reply_markup=mobile_recharge_services_keyboard(user_id))
        except Exception:
            context.bot.send_message(chat_id=update.effective_chat.id, text="اختر خدمة رصيد الهاتف المطلوبة:", reply_markup=mobile_recharge_services_keyboard(user_id))
        return

    # اختيار خدمة رصيد الهاتف
    if data.startswith("mobile_service_"):
        service_name = data[len("mobile_service_"):]
        base_price = mobile_recharge_services.get(service_name, 0.0)
        base_price = get_base_price(service_name, base_price)
        price = get_effective_price(user_id, service_name, base_price, "mobile")
        current_balance = users_balance.get(user_id, 0.0)
        if current_balance < price:
            try:
                buttons = [
        [InlineKeyboardButton("تعديل الأسعار والكميات", callback_data="admin_edit_prices")],
                    [InlineKeyboardButton("شحن عبر اسياسيل", callback_data="charge_asiacell")],
                    [InlineKeyboardButton("شحن عبر سوبركي", callback_data="charge_superkey")],
                    [InlineKeyboardButton("شحن عبر زين كاش", callback_data="charge_zaincash")],
                    [InlineKeyboardButton("شحن عبر USDT", callback_data="charge_usdt")],
                    [InlineKeyboardButton("شحن عبر نقاط سنتات", callback_data="charge_cent_points")],
                    [InlineKeyboardButton("شحن عبر هلابي", callback_data="charge_helabi")],
                    [InlineKeyboardButton("رجوع", callback_data="show_mobile_recharge")]
                ]
                query.edit_message_text("رصيدك ليس كافياً.", reply_markup=InlineKeyboardMarkup(buttons))
            except Exception:
                context.bot.send_message(chat_id=update.effective_chat.id, text="رصيدك ليس كافياً.")
            return
        context.user_data["selected_mobile_service"] = service_name
        context.user_data["mobile_service_price"] = price
        try:
            query.edit_message_text(f"تم اختيار الخدمة: {service_name}\n\nارسل رقم 1 لتأكيد طلبك")
        except Exception:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"تم اختيار الخدمة: {service_name}\n\nارسل رقم 1 لتأكيد طلبك")
        context.user_data["waiting_for_mobile_confirm"] = True
        return

    # لوحة تحكم المالك: طلبات الارصدة المعلقة
    if data == "pending_mobile_orders" and user_id == ADMIN_ID:
        pend = db_get_pending_orders(category_filter=["mobile"])
        if not pend:
            query.edit_message_text("لا توجد طلبات رصيد هاتف معلّقة حالياً.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]))
        else:
            text_msg = "طلبات رصيد الهاتف المعلّقة:\n\n"
            kb = []
            for (oid, uid, fn, un, cat, service, price, link, ts) in pend:
                text_msg += (f"{oid}) {fn} (@{un})\n"
                             f"   الخدمة: {service} | السعر: {price}$\n\n")
                kb.append([InlineKeyboardButton(f"ادارة #{oid}", callback_data=f"process_mobile_{oid}")])
            kb.append([InlineKeyboardButton("رجوع", callback_data="admin_menu")])
            query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("process_mobile_") and user_id == ADMIN_ID:
        oid = int(data.split("_")[-1])
        row = _exec("""SELECT id, user_id, full_name, username, service, price
                       FROM orders WHERE id=%s""", (oid,), "one")
        if not row:
            query.edit_message_text("طلب غير موجود."); return
        _, uid, fn, un, service, price = row
        text_msg = (
            f"تفاصيل طلب رصيد هاتف #{oid}:\n"
            f"- المعرف: {uid}\n- الاسم: {fn}\n- يوزر: @{un}\n"
            f"- الخدمة: {service}\n- السعر: {price}$\n\n"
            "اختر الإجراء:"
        )
        btns = [
            [InlineKeyboardButton("انتظار المستخدم", callback_data=f"mobile_wait_{oid}")],
            [InlineKeyboardButton("اكمال الطلب", callback_data=f"mobile_complete_{oid}")],
            [InlineKeyboardButton("الغاء الطلب", callback_data=f"mobile_cancel_{oid}")],
            [InlineKeyboardButton("رجوع", callback_data="pending_mobile_orders")]
        ]
        query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(btns))
        return

    if data.startswith("mobile_wait_") and user_id == ADMIN_ID:
        oid = int(data.split("_")[-1])
        row = _exec("SELECT user_id FROM orders WHERE id=%s", (oid,), "one")
        if row:
            try: context.bot.send_message(chat_id=row[0], text="سيتم إرسال رقم الكارت لك قريباً.")
            except Exception: pass
        query.edit_message_text("تم إرسال إشعار الانتظار للمستخدم.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_mobile_orders")]]))
        return

    if data.startswith("mobile_complete_") and user_id == ADMIN_ID:
        oid = int(data.split("_")[-1])
        query.edit_message_text("أرسل الآن رقم الكارت للمستخدم:",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_mobile_orders")]]))
        context.user_data["mobile_to_complete_id"] = oid
        context.user_data["waiting_for_mobile_code"] = True
        return

    if data.startswith("mobile_cancel_") and user_id == ADMIN_ID:
        oid = int(data.split("_")[-1])
        row = _exec("SELECT user_id, price FROM orders WHERE id=%s", (oid,), "one")
        if row:
            db_refund_order(oid, row[0], float(row[1]))
            try: context.bot.send_message(chat_id=row[0], text="تم إلغاء طلب رصيد الهاتف وإعادة المبلغ لرصيدك.")
            except Exception: pass
        query.edit_message_text("تم إلغاء طلب رصيد الهاتف وإعادة المبلغ للمستخدم.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="pending_mobile_orders")]]))
        return

def main():
    # تأكد من اتصال الـ DB
    try:
        with pg_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح.")
    except Exception as e:
        logger.exception("❌ فشل الاتصال بقاعدة البيانات: %s", e)
        raise

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CallbackQueryHandler(mobile_button_handler, pattern=r"^(show_mobile_recharge|mobile_service_|pending_mobile_orders|process_mobile_|mobile_wait_|mobile_complete_|mobile_cancel_)"))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler((Filters.text | Filters.photo | Filters.video | Filters.voice) & ~Filters.command, handle_messages))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


# =========================
# خصومات المشرفين (جديد – خصم ثابت 10% للمشرفين فقط)
# =========================
def get_effective_price(user_id: int, service_name: str, base_price: float, kind: str = "generic") -> float:
    try:
        if is_moderator(user_id):
            return round(float(base_price) * 0.90, 2)
        return float(base_price)
    except Exception as e:
        logger.error("get_effective_price error: %s", e)
        return float(base_price)
