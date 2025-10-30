# price_live_tracker.py
import os
import asyncio
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# =====================
# إعداد Binance API من متغيرات البيئة
# =====================
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")
BASE_URL = "https://api.binance.com"

# =====================
# جلب أبرز 10 أزواج USDT حسب حجم التداول
# =====================
def top_10_pairs():
    try:
        url = f"{BASE_URL}/api/v3/ticker/24hr"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        usdt_pairs = [d for d in data if d["symbol"].endswith("USDT")]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True)
        top10 = [d["symbol"] for d in sorted_pairs[:10]]
        return top10
    except Exception as e:
        print(f"Error fetching top pairs: {e}")
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
                "XRPUSDT", "DOGEUSDT", "LTCUSDT", "DOTUSDT", "AVAXUSDT"]

# =====================
# لوحة اختيار العملات
# =====================
def price_keyboard(top_pairs=None):
    if top_pairs is None:
        top_pairs = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]

    keyboard = []
    for i in range(0, len(top_pairs), 2):
        row = []
        for j in range(i, min(i + 2, len(top_pairs))):
            row.append(InlineKeyboardButton(top_pairs[j], callback_data=f"price_{top_pairs[j]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 تحديث السعر", callback_data="refresh_price"),
                     InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

# =====================
# جلب السعر من Binance
# =====================
def fetch_price(symbol: str) -> float:
    try:
        url = f"{BASE_URL}/api/v3/ticker/price"
        headers = {"X-MBX-APIKEY": API_KEY} if API_KEY else {}
        params = {"symbol": symbol.upper()}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return float(data["price"])
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

# =====================
# إنشاء مخطط ASCII صغير
# =====================
def ascii_chart(prices: list) -> str:
    if not prices:
        return "(لا توجد بيانات للمخطط)"
    max_price = max(prices)
    min_price = min(prices)
    chart = ""
    for p in prices:
        length = int(((p - min_price) / (max_price - min_price + 1e-8)) * 20)
        chart += "█" * length + f" {p:.5f}$\n"
    return chart

# =====================
# عرض صفحة اختيار العملة
# =====================
async def show_price_page(update, user_pages):
    user_id = getattr(update, "from_user", None)
    if user_id:
        user_pages[user_id.id] = "price"

    top_pairs = top_10_pairs()
    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        await query.edit_message_text(
            "💰 اختر العملة لعرض السعر والمخطط (Top 10 أزواج):",
            reply_markup=price_keyboard(top_pairs)
        )
    elif hasattr(update, "message") and update.message:
        await update.message.reply_text(
            "💰 اختر العملة لعرض السعر والمخطط (Top 10 أزواج):",
            reply_markup=price_keyboard(top_pairs)
        )

# =====================
# التحديث التلقائي للأسعار
# =====================
async def live_price_tracker(bot, chat_id, symbol, user_price_history, interval=30):
    if chat_id not in user_price_history:
        user_price_history[chat_id] = {}
    if symbol not in user_price_history[chat_id]:
        user_price_history[chat_id][symbol] = []

    while True:
        price = fetch_price(symbol)
        if price is not None:
            history = user_price_history[chat_id][symbol]
            trend = ""
            if history:
                last_price = history[-1]
                if price > last_price:
                    trend = "🔺 صعود"
                elif price < last_price:
                    trend = "🔻 هبوط"
                else:
                    trend = "➡️ ثابت"
            history.append(price)
            if len(history) > 10:
                history.pop(0)
            price_str = f"{price:.5f}$"
            chart_text = ascii_chart(history)

            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=user_price_history[chat_id].get("message_id", None),
                    text=f"💰 سعر {symbol} الحالي: {price_str} {trend}\n\n{chart_text}",
                    reply_markup=price_keyboard(top_10_pairs())
                )
            except Exception as e:
                print(f"Error updating message: {e}")

            if "message_id" not in user_price_history[chat_id]:
                user_price_history[chat_id]["message_id"] = None
        await asyncio.sleep(interval)

# =====================
# عرض سعر عملة محددة
# =====================
async def show_price_symbol(update, bot, symbol: str, user_price_history: dict):
    chat_id = update.from_user.id
    if chat_id not in user_price_history:
        user_price_history[chat_id] = {}
    if symbol not in user_price_history[chat_id]:
        user_price_history[chat_id][symbol] = []

    price = fetch_price(symbol)
    price_str = f"{price:.5f}$" if price else "⚠️ خطأ في جلب السعر"
    chart_text = ascii_chart(user_price_history[chat_id][symbol])

    query = getattr(update, "callback_query", None)
    if query:
        msg = await query.edit_message_text(
            f"💰 سعر {symbol} الحالي: {price_str}\n\n{chart_text}",
            reply_markup=price_keyboard(top_10_pairs())
        )
        user_price_history[chat_id]["message_id"] = msg.message_id
    elif hasattr(update, "message") and update.message:
        msg = await update.message.reply_text(
            f"💰 سعر {symbol} الحالي: {price_str}\n\n{chart_text}",
            reply_markup=price_keyboard(top_10_pairs())
        )
        user_price_history[chat_id]["message_id"] = msg.message_id

    # بدء Live Tracker تلقائي لكل مستخدم
    asyncio.create_task(live_price_tracker(bot, chat_id, symbol, user_price_history))
