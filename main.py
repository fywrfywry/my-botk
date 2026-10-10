import asyncio
import json
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

# بيانات البروكسي السكني الخاص بك
PROXY_URL = "http://name8nvk3l-pool-res.mobile.corp-country-US-state-4736286-mode-query-tier-premium:SLRCvxnaZI5nIr0S@185.185.51.243:443"

# التوكن والأيدي الخاص بك
BOT_TOKEN = "8837027411:AAEj-ZenZmuTNvkwD6ppoWx5mS-rDR9fjuA"
ADMIN_ID = 7352706784  # ايدي حسابك للحماية

# حالات المحادثة
GET_LINK, GET_LOOPS = range(2)


class ZefameAutomatedBot:

  def __init__(self, service_id: str = "232"):
    self.service_id = str(service_id)
    self.session = requests.Session()
    self.session.proxies = {"http": PROXY_URL, "https": PROXY_URL}
    self.session.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Origin": "https://zefame.com",
        "Referer": "https://zefame.com/",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like"
            " Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
        ),
        "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
    })

  def check_current_ip(self):
    try:
      res = self.session.get("https://api.ipify.org?format=json", timeout=10)
      return res.json().get("ip")
    except Exception:
      return "تعذر الفحص"

  def run_single_process(self, tiktok_link: str):
    self.device_id = str(uuid.uuid4())
    ip_addr = self.check_current_ip()

    url_check = "https://api.zefame.com/api_free.php?lang=fr"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = {"action": "checkVideoId", "link": tiktok_link}

    try:
      response_check = self.session.post(
          url_check, headers=headers, data=data, timeout=15
      )
      if response_check.status_code != 200:
        return False, ip_addr, "فشل الاتصال بموقع zefame"

      res_json = response_check.json()
      video_id = None
      if isinstance(res_json, dict):
        if "data" in res_json and isinstance(res_json["data"], dict):
          video_id = res_json["data"].get("videoId") or res_json["data"].get(
              "id"
          )
        if not video_id:
          video_id = (
              res_json.get("videoId")
              or res_json.get("id")
              or res_json.get("video_id")
          )

      if not video_id:
        return False, ip_addr, "لم يتم استخراج videoId"

      url_service = "https://api.zefame.com/api_free.php"
      params = {
          "lang": "fr",
          "action": "check",
          "device": self.device_id,
          "service": self.service_id,
          "videoId": str(video_id),
      }

      response_service = self.session.get(url_service, params=params, timeout=15)
      if response_service.status_code == 200:
        try:
          return True, ip_addr, response_service.json()
        except Exception:
          return True, ip_addr, response_service.text
      else:
        return False, ip_addr, f"رمز الحالة: {response_service.status_code}"

    except Exception as e:
      return False, ip_addr, str(e)


# --- دوال محادثة البوت التفاعلية ---


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    await update.message.reply_text(
        "❌ عذراً، هذا البوت خاص ومحمي ولا يمكنك استخدامه."
    )
    return ConversationHandler.END

  await update.message.reply_text(
      "أهلاً بك يا مالك البوت 🚀\n\n🔗 أرسل **رابط فيديو TikTok** المراد زيادة"
      " المشاركات له:"
  )
  return GET_LINK


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return ConversationHandler.END

  link = update.message.text.strip()
  if "tiktok.com" not in link:
    await update.message.reply_text(
        "⚠️ الرابط غير صحيح. يرجى إرسال رابط تيك توك صالح:"
    )
    return GET_LINK

  context.user_data["tiktok_link"] = link
  await update.message.reply_text(
      "✅ تم حفظ الرابط بنجاح.\n\n🔢 الآن أرسل **عدد مرات التكرار المطلوبة**"
      " (مثلاً: 5):"
  )
  return GET_LOOPS


async def receive_loops(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return ConversationHandler.END

  text_loops = update.message.text.strip()
  try:
    loops = int(text_loops)
    if loops <= 0:
      raise ValueError()
  except ValueError:
    await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح أكبر من الصفر:")
    return GET_LOOPS

  tiktok_link = context.user_data.get("tiktok_link")
  status_msg = await update.message.reply_text(
      f"🚀 جاري البدء بتنفيذ ({loops}) محاولات..."
  )

  bot_engine = ZefameAutomatedBot(service_id="232")

  for i in range(1, loops + 1):
    await status_msg.edit_text(
        f"🔄 **[العملية {i}/{loops}]**\nجاري إرسال الطلب عبر البروكسي السكني..."
    )

    success, ip_used, detail = bot_engine.run_single_process(tiktok_link)

    if success:
      if isinstance(detail, dict):
        formatted_response = json.dumps(detail, indent=2, ensure_ascii=False)
      else:
        formatted_response = str(detail)

      result_text = (
          f"✅ **العملية ({i}/{loops}) نجحت!**\n"
          f"🌐 **الـ IP المستخدم:** `{ip_used}`\n\n"
          f"📥 **الرد الحقيقي من السيرفر:**\n```json\n{formatted_response}\n```"
      )
    else:
      result_text = (
          f"❌ **العملية ({i}/{loops}) فشلت**\n"
          f"🌐 **الـ IP:** `{ip_used}`\n"
          f"⚠️ **السبب:** `{detail}`"
      )

    await update.message.reply_text(result_text, parse_mode="Markdown")

    if i < loops:
      await status_msg.edit_text(
          "⏳ الانتظار 30 ثانية لتحديث الـ IP السكني والدورة التالية..."
      )
      await asyncio.sleep(30)

  await update.message.reply_text(
      "✨ **اكتملت جميع العمليات بنجاح تام!**\nللبدء من جديد أرسل /start"
  )
  return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("تم إلغاء العملية.")
  return ConversationHandler.END


if __name__ == "__main__":
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
      fallbacks=[CommandHandler("cancel", cancel)],
  )

  app.add_handler(conv_handler)

  print("🤖 بوت التليجرام التفاعلي يعمل الآن...")
  app.run_polling()
