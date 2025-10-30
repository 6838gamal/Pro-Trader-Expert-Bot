import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from gtts import gTTS
from datetime import datetime

# =====================
# متغيرات عالمية لإدارة المستخدمين
# =====================
user_pages = {}
active_chats = set()

# =====================
# إعداد Gemini API
# =====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# =====================
# لوحة مفاتيح الذكاء الاصطناعي
# =====================
def ai_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="main_menu")]])

# =====================
# مجلد لحفظ الأصوات حسب اليوم
# =====================
def get_audio_folder():
    base_folder = os.path.join(os.getcwd(), "Pro Trader Expert Bot", "AI_Audio")
    today_folder = os.path.join(base_folder, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(today_folder, exist_ok=True)
    return today_folder

# =====================
# عرض صفحة الذكاء الاصطناعي
# =====================
async def show_ai_page(update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, "message") and update.message:
        user_id = update.message.from_user.id
        await update.message.reply_text(
            "🤖 تم تفعيل *وضع الوكيل الذكي*.\n"
            "يمكنك الآن طرح أي سؤال عن التداول أو السوق.\n"
            "أرسل رسالتك هنا.",
            parse_mode="Markdown",
            reply_markup=ai_keyboard()
        )
    elif hasattr(update, "callback_query") and update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        await query.message.edit_text(
            "🤖 تم تفعيل *وضع الوكيل الذكي*.\n"
            "يمكنك الآن طرح أي سؤال عن التداول أو السوق.\n"
            "أرسل رسالتك هنا.",
            parse_mode="Markdown",
            reply_markup=ai_keyboard()
        )

    active_chats.add(user_id)
    user_pages[user_id] = "ai_chat"
    print(f"[DEBUG] المستخدم {user_id} دخل وضع AI")

# =====================
# التعامل مع رسائل الذكاء الاصطناعي
# =====================
async def handle_ai_message(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_pages.get(user_id) != "ai_chat":
        return

    user_text = update.message.text
    print(f"[DEBUG] المستخدم ({user_id}) أرسل: {user_text}")

    # التحقق من وجود مفتاح API
    if not GEMINI_API_KEY:
        await update.message.reply_text(
            "⚠️ لم يتم ضبط مفتاح Gemini API.\n"
            "تأكد من إعداد متغير البيئة GEMINI_API_KEY بشكل صحيح."
        )
        print("[ERROR] GEMINI_API_KEY غير موجود")
        return

    # استخدام نفس الرابط الذي نجح في curl
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    body = {"contents": [{"parts": [{"text": user_text}]}]}

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # استخراج الرد بشكل آمن
        candidates = data.get("candidates", [])
        if candidates:
            reply = (
                candidates[0].get("content", {})
                .get("parts", [{}])[0]
                .get("text", "لم أتمكن من توليد رد.")
            )
        else:
            reply = "لم أتمكن من توليد رد."

        print(f"[DEBUG] الرد المستلم من Gemini: {reply}")

    except requests.exceptions.HTTPError as http_err:
        reply = f"⚠️ خطأ HTTP: {http_err}"
        print(f"[ERROR] {reply}")
    except requests.exceptions.RequestException as req_err:
        reply = f"⚠️ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {req_err}"
        print(f"[ERROR] {reply}")

    # إرسال الرد النصي مع لوحة المفاتيح
    await update.message.reply_text(reply, reply_markup=ai_keyboard())

    # تحويل الرد إلى صوت
    try:
        tts = gTTS(reply, lang="ar")
        folder = get_audio_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = os.path.join(folder, f"reply_{user_id}_{timestamp}.mp3")
        tts.save(audio_path)
        await update.message.reply_audio(
            open(audio_path, "rb"),
            title="🎧 استمع للرد الصوتي",
            caption="🔊 هذا هو الرد الصوتي من الوكيل الذكي."
        )
    except Exception as e:
        print(f"[ERROR] فشل إنشاء الصوت: {e}")

# =====================
# التعامل مع زر الرجوع
# =====================
async def handle_ai_callback(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "main_menu":
        user_pages.pop(user_id, None)
        active_chats.discard(user_id)
        print(f"[DEBUG] المستخدم {user_id} خرج من وضع AI")
        await query.message.edit_text("🔙 تم الخروج من وضع الوكيل الذكي.")
