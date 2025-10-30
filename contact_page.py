import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# =====================
# قائمة الرموز التعبيرية لكل منصة
# =====================
emoji_options = {
    "twitter": ["🐦", "🕊️", "🌬️"],
    "facebook": ["📘", "💙", "📖"],
    "whatsapp": ["📱", "💬", "📲"],
    "telegram": ["✈️", "📨", "🛩️"],
    "linkedin": ["💼", "📊", "🏢"],
    "youtube": ["📺", "🎬", "🍿"],
    "tiktok": ["🎵", "🎶", "🎤"],
    "instagram": ["📸", "🌟", "📷"],
    "x": ["🐦", "🪶", "🌐"]  # تويتر سابقًا X
}

def random_emoji(platform):
    return random.choice(emoji_options.get(platform, ["🌐"]))

# =====================
# إنشاء لوحة مفاتيح تفاعلية
# =====================
def build_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(f"{random_emoji('x')} X", url="https://x.com/alhwysh787472?s=09"),
            InlineKeyboardButton(f"{random_emoji('facebook')} فيسبوك", url="https://www.facebook.com/jmal.alhwysh.2025?mibextid=rS40aB7S9Ucbxw6v")
        ],
        [
            InlineKeyboardButton(f"{random_emoji('whatsapp')} واتساب", url="https://wa.me/774440982"),
            InlineKeyboardButton(f"{random_emoji('telegram')} تلجرام", url="https://t.me/Gamalalhwish")
        ],
        [
            InlineKeyboardButton(f"{random_emoji('linkedin')} لينكدإن", url="https://www.linkedin.com/in/gamal-alhwish"),
            InlineKeyboardButton(f"{random_emoji('youtube')} يوتيوب", url="https://youtube.com/@gamalabdualnasseralhwish?si=LUOCx4DVnSWShIJA")
        ],
        [
            InlineKeyboardButton(f"{random_emoji('tiktok')} تيكتوك", url="https://www.tiktok.com/@gamalalmaqtaryfor"),
            InlineKeyboardButton(f"{random_emoji('instagram')} إنستغرام", url="https://www.instagram.com/gamal_almaqtary_tech_services/")
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# =====================
# عرض صفحة التواصل
# =====================
async def show_contact_page(update, context=None):
    """
    تعرض صفحة التواصل مع التحديث التلقائي للرموز التعبيرية.
    تعمل سواء تم استدعاؤها من زر callback أو رسالة مباشرة.
    """
    text = (
        "🌐 تواصل معنا عبر جميع المنصات:\n\n"
        "اختر المنصة المفضلة لديك 👇\n\n"
        "💬 نحن دائمًا متواجدون للرد على استفساراتك!"
    )

    # التحقق من نوع التحديث
    if hasattr(update, "callback_query") and update.callback_query:
        query = update.callback_query
        message = await query.message.edit_text(text=text, reply_markup=build_keyboard())
    elif hasattr(update, "message") and update.message:
        message = await update.message.reply_text(text=text, reply_markup=build_keyboard())
    else:
        return

    # تحديث الأزرار تلقائيًا كل 5 ثوانٍ لزيادة الحيوية
    for _ in range(10):
        await asyncio.sleep(5)
        try:
            await message.edit_reply_markup(reply_markup=build_keyboard())
        except Exception:
            pass
