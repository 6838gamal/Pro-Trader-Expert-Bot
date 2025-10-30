# alert_page.py
import asyncio
import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --------------------------
# زر الرجوع للقائمة الرئيسية
# --------------------------
def alert_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="main_menu")]
    ])

# --------------------------
# قائمة الأزواج المراقبة
# --------------------------
WATCHED_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "TRXUSDT", "DOTUSDT"
]

# --------------------------
# صفحة التنبيهات
# --------------------------
async def show_alert_page(update, user_pages):
    user_id = getattr(update, "from_user", None)
    if user_id:
        user_pages[user_id.id] = "alert"

    # بدء المراقب مباشرة لكل مستخدم
    asyncio.create_task(monitor_alerts(update))

    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        await query.edit_message_text(
            "🚨 يتم الآن مراقبة الأزواج العشرة الكبرى بشكل مباشر.\n"
            "سيتم إرسال تنبيه عند حدوث تغير مفاجئ في السعر 📊",
            reply_markup=alert_keyboard()
        )
    elif hasattr(update, "message") and update.message:
        await update.message.reply_text(
            "🚨 يتم الآن مراقبة الأزواج العشرة الكبرى بشكل مباشر.\n"
            "سيتم إرسال تنبيه عند حدوث تغير مفاجئ في السعر 📊",
            reply_markup=alert_keyboard()
        )

# --------------------------
# وظيفة المراقبة الحية
# --------------------------
async def monitor_alerts(update):
    """مراقبة الأسعار الحية وإرسال تنبيهات عند التغير المفاجئ"""
    url = "https://api.binance.com/api/v3/ticker/price"
    last_prices = {}

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()

            # تحويل البيانات إلى قاموس سريع الوصول
            prices = {item["symbol"]: float(item["price"]) for item in data if item["symbol"] in WATCHED_PAIRS}

            for symbol, price in prices.items():
                if symbol in last_prices:
                    old_price = last_prices[symbol]
                    change = ((price - old_price) / old_price) * 100

                    # إذا التغير أكبر من ±1.5% خلال فترة قصيرة → تنبيه
                    if abs(change) >= 1.5:
                        msg = (
                            f"🚨 *تنبيه سعر مفاجئ!*\n"
                            f"الزوج: `{symbol}`\n"
                            f"السعر السابق: ${old_price:,.4f}\n"
                            f"السعر الحالي: ${price:,.4f}\n"
                            f"نسبة التغير: {change:.2f}%"
                        )
                        try:
                            if hasattr(update, "callback_query") and update.callback_query:
                                await update.callback_query.message.reply_text(msg, parse_mode="Markdown")
                            elif hasattr(update, "message") and update.message:
                                await update.message.reply_text(msg, parse_mode="Markdown")
                        except Exception:
                            pass

                last_prices[symbol] = price

            await asyncio.sleep(10)  # فحص كل 10 ثوانٍ

        except Exception as e:
            print(f"[Alert Monitor Error] {e}")
            await asyncio.sleep(15)
