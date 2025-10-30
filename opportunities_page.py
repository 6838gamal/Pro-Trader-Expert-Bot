# opportunities_page.py
import datetime
import os
import pandas as pd
import ta
from binance.client import Client
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --------------------------
# إعداد Binance API
# --------------------------
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# --------------------------
# إعداد لوحة التحكم
# --------------------------
def opportunities_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="main_menu")]])

# --------------------------
# توليد الفرص الاحترافية
# --------------------------
def generate_opportunities(symbols):
    opportunities = []
    for symbol in symbols:
        try:
            # جلب بيانات الشموع اليومية
            klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1DAY, limit=30)
            df = pd.DataFrame(klines, columns=[
                'open_time','open','high','low','close','volume','close_time','qav',
                'num_trades','taker_base','taker_quote','ignore'
            ])
            df['close'] = df['close'].astype(float)

            # مؤشرات فنية
            df['MA20'] = df['close'].rolling(20).mean()
            df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

            last_price = df['close'].iloc[-1]
            ma20 = df['MA20'].iloc[-1]
            rsi = df['RSI'].iloc[-1]

            # قاعدة التوصية
            if last_price < ma20 and rsi < 30:
                action = "اشترِ الآن 🔥"
                entry = last_price
                target = round(entry * 1.05, 2)
                stop_loss = round(entry * 0.97, 2)
            elif last_price > ma20 and rsi > 70:
                action = "بيع الآن ⚡"
                entry = last_price
                target = round(entry * 0.95, 2)
                stop_loss = round(entry * 1.03, 2)
            else:
                action = "انتظار ⏳"
                entry = target = stop_loss = last_price

            opportunities.append(
                f"{symbol}:\n"
                f"السعر الحالي: {last_price:.2f}$\n"
                f"سعر الدخول: {entry:.2f}$\n"
                f"الهدف: {target:.2f}$\n"
                f"وقف الخسارة: {stop_loss:.2f}$\n"
                f"التوصية: {action}\n"
            )
        except Exception as e:
            opportunities.append(f"{symbol}: ⚠️ خطأ في جلب البيانات ({e})\n")
    return opportunities

# --------------------------
# الدالة الرئيسية لإظهار الفرص
# --------------------------
async def show_opportunities_page(update):
    """
    تعرض أفضل 5 فرص مع الأسعار، الهدف، وقف الخسارة، والتوصية.
    """
    top5_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
    top5 = generate_opportunities(top5_symbols)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    text = f"🔥 أفضل 5 فرص اليوم (تحديث: {now}):\n\n" + "\n".join(top5)

    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=opportunities_keyboard())
    elif hasattr(update, "message") and update.message:
        await update.message.reply_text(text, reply_markup=opportunities_keyboard())
