import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# =====================
# تحميل متغيرات البيئة
# =====================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# =====================
# استدعاء صفحات البوت
# =====================
from price_live_tracker import show_price_page, show_price_symbol
from ai_page import show_ai_page, handle_ai_message
from alert_page import show_alert_page
from opportunities_page import show_opportunities_page
from contact_page import show_contact_page

# =====================
# إدارة بيانات المستخدمين
# =====================
user_pages = {}
user_price_history = {}  # لتخزين آخر رمز تم اختياره لكل مستخدم

# =====================
# لوحة رئيسية
# =====================
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 متابعة الأسعار", callback_data="price_menu")],
        [InlineKeyboardButton("📈 الفرص اليومية", callback_data="opportunities")],
        [InlineKeyboardButton("🚨 التنبيهات", callback_data="alert_menu")],
        [InlineKeyboardButton("🤖 التحدث مع الوكيل الذكي", callback_data="ai_chat")],
        [InlineKeyboardButton("👨‍💻 تواصل مع المطور", callback_data="contact")],
    ])

# =====================
# زر العودة للقائمة الرئيسية
# =====================
def back_to_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="main_menu")]
    ])

# =====================
# مساعد ذكي لإرسال الرد حسب نوع التحديث
# =====================
async def send_page(update_or_query, text, reply_markup=None):
    query = getattr(update_or_query, "callback_query", None)
    if query is not None:  # جاء من زر
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif hasattr(update_or_query, "message") and update_or_query.message is not None:  # جاء من أمر
        await update_or_query.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        print("⚠️ لا يوجد message أو callback_query صالح في هذا التحديث!")

# =====================
# أوامر البوت
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_pages[update.message.from_user.id] = "main"
    await send_page(
        update,
        "مرحبًا بك في 🤖 *Pro Trader Expert Bot*!\nاختر أحد الخيارات:",
        main_keyboard()
    )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_price_page(update, user_pages)

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_ai_page(update, context)

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_alert_page(update, user_pages)

async def opportunities_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_opportunities_page(update)

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_contact_page(update)

# =====================
# التوجيه عند الضغط على الأزرار
# =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    data = query.data

    if data == "main_menu":
        await send_page(update, "مرحبًا بك في 🤖 *Pro Trader Expert Bot*!\nاختر أحد الخيارات:", main_keyboard())
    elif data == "price_menu":
        await price_command(update, context)
    elif data.startswith("price_"):
        symbol = data.split("_")[1]
        user_id = query.from_user.id
        if user_id not in user_price_history:
            user_price_history[user_id] = {}
        user_price_history[user_id]["last_symbol"] = symbol
        await show_price_symbol(query, context.bot, symbol, user_price_history)
    elif data == "refresh_price":
        user_id = query.from_user.id
        last_symbol = user_price_history.get(user_id, {}).get("last_symbol")
        if last_symbol:
            await show_price_symbol(query, context.bot, last_symbol, user_price_history)
        else:
            from price_live_tracker import price_keyboard
            await query.edit_message_text(
                "لم يتم اختيار عملة بعد. اختر عملة أولاً.",
                reply_markup=price_keyboard()
            )
    elif data == "ai_chat":
        await ai_command(update, context)
    elif data == "alert_menu":
        await alert_command(update, context)
    elif data == "opportunities":
        await opportunities_command(update, context)
    elif data == "contact":
        await contact_command(update, context)

# =====================
# التعامل مع رسائل الذكاء الاصطناعي
# =====================
async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_ai_message(update, context)

# =====================
# تشغيل البوت
# =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("opportunities", opportunities_command))
    app.add_handler(CommandHandler("contact", contact_command))

    # أزرار
    app.add_handler(CallbackQueryHandler(button_callback))

    # رسائل الذكاء الاصطناعي
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler))

    print("🚀 Pro Trader Expert Bot is now running...")
    app.run_polling()

if __name__ == "__main__":
    main()
