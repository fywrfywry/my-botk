import asyncio
import json
import logging
import sys
import uuid
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ==============================================================================
# 1. إعداد وتسجيل السجلات (Logging System)
# ==============================================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ZefameBot")

# ==============================================================================
# 2. الثوابت والإعدادات الرئيسية (Configuration Constants)
# ==============================================================================
BOT_TOKEN = "8837027411:AAEj-ZenZmuTNvkwD6ppoWx5mS-rDR9fjuA"
ADMIN_ID = 7352706784

DEFAULT_SERVICE_ID = "233"  # خدمة الإعجابات المجانية (Free Likes)

DIRECT_PROXY_URL = (
    "http://name8nvk3l-pool-res.mobile.corp-country-US-state-4736286"
    "-mode-query-tier-premium:SLRCvxnaZI5nIr0S@185.185.51.243:443"
)

GET_LINK, GET_LOOPS = range(2)


# ==============================================================================
# 3. كلاس التعامل مع سيرفر Zefame (Zefame Engine Core)
# ==============================================================================
class ZefameAutomatedBot:
    def __init__(self, service_id: str = DEFAULT_SERVICE_ID):
        self.service_id = str(service_id)
        self.session = requests.Session()
        self.setup_proxy_and_headers()

    def setup_proxy_and_headers(self):
        self.session.proxies = {
            "http": DIRECT_PROXY_URL,
            "https": DIRECT_PROXY_URL
        }
        self.session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Origin": "https://zefame.com",
            "Referer": "https://zefame.com/",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
            ),
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
        })

    def check_current_ip(self) -> str:
        try:
            response = self.session.get("https://api.ipify.org?format=json", timeout=12)
            if response.status_code == 200:
                return response.json().get("ip", "غير معروف")
            return "تعذر استخراج IP"
        except Exception as err:
            logger.error(f"خطأ أثناء فحص الـ IP عبر البروكسي: {err}")
            return "تعذر الاتصال بالبروكسي"

    def extract_video_id(self, tiktok_link: str):
        url_check = "https://api.zefame.com/api_free.php?lang=fr"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        payload = {
            "action": "checkVideoId",
            "link": tiktok_link
        }

        try:
            res = self.session.post(url_check, headers=headers, data=payload, timeout=15)
            if res.status_code != 200:
                return None, f"فشل الاتصال بالموقع (رمز {res.status_code})"

            res_json = res.json()
            video_id = None

            if isinstance(res_json, dict):
                data_obj = res_json.get("data", {})
                if isinstance(data_obj, dict):
                    video_id = data_obj.get("videoId") or data_obj.get("id")
                if not video_id:
                    video_id = (
                        res_json.get("videoId") 
                        or res_json.get("id") 
                        or res_json.get("video_id")
                    )

            if video_id:
                return str(video_id), "نجاح"
            return None, "لم يتم العثور على المعرف داخل استجابة السيرفر"

        except Exception as ex:
            logger.error(f"استثناء أثناء استخراج videoId: {ex}")
            return None, str(ex)

    def execute_service_request(self, video_id: str, device_id: str):
        url_service = "https://api.zefame.com/api_free.php"
        params = {
            "lang": "fr",
            "action": "check",
            "device": device_id,
            "service": self.service_id,
            "videoId": video_id,
        }

        try:
            res = self.session.get(url_service, params=params, timeout=15)
            if res.status_code == 200:
                try:
                    return True, res.json()
                except Exception:
                    return True, res.text
            else:
                return False, f"خطأ سيرفر: رمز الاستجابة {res.status_code}"

        except Exception as ex:
            logger.error(f"استثناء أثناء تنفيذ طلب الخدمة: {ex}")
            return False, str(ex)

    def run_single_process(self, tiktok_link: str):
        device_id = str(uuid.uuid4())
        ip_addr = self.check_current_ip()

        video_id, err_msg = self.extract_video_id(tiktok_link)
        if not video_id:
            return False, ip_addr, f"فشل استخراج الفيديو: {err_msg}"

        success, service_result = self.execute_service_request(video_id, device_id)
        return success, ip_addr, service_result


# ==============================================================================
# 4. دوال التعامل مع أوامر بوت التليجرام (Telegram Handlers)
# ==============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ عذراً، هذا البوت محمي وخاص بالمالك فقط.")
        return ConversationHandler.END

    welcome_text = (
        "أهلاً بك يا مالك البوت 🚀\n\n"
        "✨ **نظام زيادة إعجابات تيك توك التلقائي (Zefame Free Likes)**\n\n"
        "🔗 يرجى إرسال **رابط فيديو TikTok** المطلوب:"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    return GET_LINK


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return ConversationHandler.END

    link = update.message.text.strip()
    if "tiktok.com" not in link:
        await update.message.reply_text(
            "⚠️ **الرابط غير صالح!**\nيرجى إرسال رابط فيديو تيك توك صحيح يحتوي على tiktok.com:"
        )
        return GET_LINK

    context.user_data["tiktok_link"] = link
    await update.message.reply_text(
        "✅ **تم حفظ الرابط بنجاح.**\n\n"
        "🔢 أدخل الآن **عدد المحاولات المطلوبة** (مثال: 5):"
    )
    return GET_LOOPS


async def receive_loops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return ConversationHandler.END

    text_input = update.message.text.strip()
    try:
        loops = int(text_input)
        if loops <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح أكبر من الصفر:")
        return GET_LOOPS

    tiktok_link = context.user_data.get("tiktok_link")
    status_msg = await update.message.reply_text(
        f"🚀 **بدء العملية:** جاري إرسال ({loops}) محاولات عبر البروكسي السكني..."
    )

    bot_engine = ZefameAutomatedBot(service_id=DEFAULT_SERVICE_ID)

    for i in range(1, loops + 1):
        await status_msg.edit_text(
            f"🔄 **[المحاولة {i} من {loops}]**\n"
            f"جاري تبديل الـ IP وإرسال الطلب عبر البروكسي..."
        )

        success, ip_used, detail = bot_engine.run_single_process(tiktok_link)

        if success:
            if isinstance(detail, dict):
                formatted_response = json.dumps(detail, indent=2, ensure_ascii=False)
            else:
                formatted_response = str(detail)

            result_text = (
                f"✅ **العملية ({i}/{loops}) تمت بنجاح!**\n"
                f"🌐 **عنوان IP السكني:** `{ip_used}`\n\n"
                f"📥 **الرد المباشر من السيرفر:**\n"
                f"```json\n{formatted_response}\n```"
            )
        else:
            result_text = (
                f"❌ **العملية ({i}/{loops}) لم تكتمل**\n"
                f"🌐 **عنوان IP:** `{ip_used}`\n"
                f"⚠️ **السبب:** `{detail}`"
            )

        await update.message.reply_text(result_text, parse_mode="Markdown")

        if i < loops:
            await status_msg.edit_text(
                "⏳ **الانتظار 30 ثانية** لتمرير الدورة التالية وتدوير الـ IP..."
            )
            await asyncio.sleep(30)

    await update.message.reply_text(
        "✨ **اكتملت جميع المحاولات بنجاح!**\n"
        "للبدء في مهمة جديدة أرسل /start"
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 تم إلغاء العملية بنجاح.")
    return ConversationHandler.END


# ==============================================================================
# 5. تشغيل البوت وإدارة التطبيق (Application Main Engine)
# ==============================================================================
def main():
    logger.info("جاري بدء تشغيل بوت أتمتة Zefame...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            GET_LINK: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), receive_link)
            ],
            GET_LOOPS: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), receive_loops)
            ],
        },
        
